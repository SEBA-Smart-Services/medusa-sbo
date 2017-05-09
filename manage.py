#!/usr/bin/env python
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

from app import app, db, user_manager
from app.models import AssetType, PointType, Asset, Site, AssetPoint, InbuildingsConfig, Algorithm, User, Role
from app.algorithms.algorithms import AlgorithmClass

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)

# some asset types
asset_types =  [
    'AHU-CV',
    'AHU-VV',
    'FCU',
    'AC-DX',
    'pump',
    'ventilation fan'
]
# some point types
point_types = [
    'zone air temp sensor',
    'return air damper cmd',
    'supply air fan run cmd',
    'zone air temp sp',
    'supply air fan run status',
    'return air temp sensor',
    'return air humidity sensor',
    'return air co2 sensor',
    'chilled water valve',
    'outside air damper cmd',
    'filter',
    'supply air fan status',
    'filter sp',
    'supply air temp sp',
    'supply air temp sensor',
    'supply air fan speed cmd'
]
# a list of dummy sites for testing
site_names = [
    'TestSite1',
    'TestSite2'
]

roles = [
    'admin'
]

test_asset_name = 'Test AHU'
admin_user = 'sebb'
admin_pw = 'Schn3!d3r1'
test_user = 'testuser'
test_pw = 'Schn3!d3r1'


@manager.command
def regenerate():

    # ensure session is closed
    db.session.close()

    # regenerate all tables in the database, based on models
    db.drop_all()
    db.create_all()

    # add some initial data
    for sitename in site_names:
        site = Site(name=sitename)
        site.inbuildings_config = InbuildingsConfig(enabled=False, key="")
        db.session.add(site)

    for typename in asset_types:
        asset_type = AssetType(name=typename)
        db.session.add(asset_type)

    for pointname in point_types:
        point_type = PointType(name=pointname)
        db.session.add(point_type)

    site = Site.query.filter_by(name=site_names[0]).one()
    asset_type = AssetType.query.filter_by(name=asset_types[0]).one()
    asset = Asset(name=test_asset_name, site=site, type=asset_type, health=0, priority=1, notes='')

    # add one of each point type to dummy unit
    for pointtype in point_types:
        point = PointType.query.filter_by(name=pointtype).one()
        asset_point = AssetPoint(name=pointtype, type=point, asset=asset)
        asset.points.append(asset_point)

    # add and commit to db
    db.session.add(asset)
    db.session.commit()

    # map assets to algorithms
    map_all()

    # generate users
    admin = User(username=admin_user, password=user_manager.hash_password(admin_pw), active=True)
    test = User(username=test_user, password=user_manager.hash_password(test_pw), active=True)
    db.session.add(admin)
    db.session.add(test)

    # generate roles
    for role_name in roles:
        role = Role(name=role_name, label=role_name)
        admin.roles.append(role)

    db.session.commit()
    db.session.close()

@manager.command
def reset_admin():
    admin = User.query.filter_by(username=admin_user)
    admin.password = user_manager.hash_password(admin_pw)
    admin.roles = Role.query.all()
    admin.active = True
    db.session.commit()
    db.session.close()

# find all defined algorithms and add them to the database
def generate_algorithms():
    # algorithms are subclasses of AlgorithmClass
    for algorithm in AlgorithmClass.__subclasses__():
        algorithm_db = Algorithm.query.filter_by(name=algorithm.__name__).first()

        # if the algorithm doesn't exist in the database, create it
        if algorithm_db == None:
            algorithm_db = Algorithm(descr=algorithm.name, name=algorithm.__name__)
            db.session.add(algorithm_db)

        # else update it
        else:
            algorithm_db.descr = algorithm.name

        algorithm_db.map()

    db.session.commit()

# generate the entire mapping tables for algorithms-points and algorithms-assets
def map_algorithms():
    for algorithm in Algorithm.query.all():
        algorithm.map()
    db.session.commit()

# generate the entire mapping table for algorithms-assets
def map_assets():
    for asset in Asset.query.all():
        asset.map()
    db.session.commit()

# map all algorithms
@manager.command
def map_all():
    generate_algorithms()
    map_algorithms()
    db.session.close()

@manager.command
def create():

    db.create_all()

    for sitename in site_names:
        site = Site(name=sitename)
        site.inbuildings_config = InbuildingsConfig(enabled=False, key="")
        db.session.add(site)

    for typename in asset_types:
        asset_type = AssetType(name=typename)
        db.session.add(asset_type)

    for pointname in point_types:
        point_type = PointType(name=pointname)
        db.session.add(point_type)

    site = Site.query.filter_by(name=site_names[0]).one()
    asset_type = AssetType.query.filter_by(name=asset_types[0]).one()
    asset = Asset(name=test_asset_name, site=site, type=asset_type, health=0, priority=1, notes='')

    # add one of each point type to dummy unit
    for pointtype in point_types:
        point = PointType.query.filter_by(name=pointtype).one()
        asset_point = AssetPoint(name=pointtype, type=point, asset=asset)
        asset.points.append(asset_point)

    db.session.add(asset)
    db.session.commit()
    db.session.close()


if __name__ == '__main__':
    manager.run()
