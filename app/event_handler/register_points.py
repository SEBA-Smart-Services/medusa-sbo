from app.models import AssetPoint, LoggedEntity
from app import db, registry
from base64 import b64encode

# link medusa assets to webreports logs. XML file must have been imported and bound first for this to work
def register_points():
    for point in AssetPoint.query.filter(AssetPoint.loggedentity_id == None).all():
        session = registry.get(point.asset.site.db_key)
        if not session is None:
            identifier = 'DONOTMODIFY:' + str(b64encode('{}.{}.{}'.format(point.asset.site.id, point.asset.id, point.id).encode('ascii')).decode('ascii'))
            # search to see if the XML generated file exists in the WebReports server
            loggedentity = session.query(LoggedEntity).filter_by(descr=identifier).first()
            if not loggedentity is None:
                point.loggedentity_id = loggedentity.id
                print("{} - {} log registered".format(point.asset.name, point.name))
            db.session.commit()
            session.close()
    db.session.close()
