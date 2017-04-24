from app import db
from app.models import AssetType, PointType, Asset, Site, AssetPoint, InbuildingsConfig

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
	'Fan Enable',
	'CHW Valve'
]
# a list of dummy sites for testing
site_names = [
	'TestSite1',
	'TestSite2'
]

test_asset_name = 'Test AHU'

# TO DO: this should be grabbed from a config file instead!
db_bind_name = 'medusa'

# regenerate all tables in the database, based on models
db.drop_all(bind=db_bind_name)
db.create_all(bind=db_bind_name)

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

from mapping import map_all
map_all()

db.session.close()
