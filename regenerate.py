from app import db
from app.models import AssetType, PointType, Asset, Site, AssetPoint

# regenerate all tables in the database, based on models
db.drop_all(bind='medusa')
db.create_all(bind='medusa')

# add some initial data
for sitename in ['TestSite1', 'TestSite2']:
    site = Site(name=sitename)
    db.session.add(site)

for typename in ['AHU', 'Chiller']:
    asset_type = AssetType(name=typename)
    db.session.add(asset_type)

for pointname in ['Fan Enable', 'CHW Valve']:
    point_type = PointType(name=pointname)
    db.session.add(point_type)

site = Site.query.filter_by(name='TestSite1').one()
asset_type = AssetType.query.filter_by(name='AHU').one()
asset = Asset(name='Test AHU', site=site, type=asset_type, health=0, priority=1, notes='')
point1_type = PointType.query.filter_by(name='Fan Enable').one()
point2_type = PointType.query.filter_by(name='CHW Valve').one()
point1 = AssetPoint(name='Fan Enable', type=point1_type, asset=asset)
point2 = AssetPoint(name='CHW Valve', type=point2_type, asset=asset)
asset.points.append(point1)
asset.points.append(point2)
db.session.add(asset)

db.session.commit()
db.session.close()
