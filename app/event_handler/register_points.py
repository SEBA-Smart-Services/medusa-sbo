from app.models import AssetPoint, LoggedEntity
from app import db, registry
from base64 import b64encode

# link medusa assets to webreports logs. XML file must have been imported and bound first for this to work
def register_points():
    for point in AssetPoint.query.filter(AssetPoint.loggedentity_id == None).all():
        # get the session to the remote webreports database
        session = registry.get(point.asset.site.db_key)
        if not session is None:
            # match based on a base64 encoded identifier, which is added to the description field of the trend log when generating the xml
            identifier = 'DONOTMODIFY:' + str(b64encode('{}.{}.{}'.format(point.asset.site.id, point.asset.id, point.id).encode('ascii')).decode('ascii'))
            # search to see if the XML generated file exists in the WebReports server
            loggedentity = session.query(LoggedEntity).filter_by(descr=identifier).first()
            if not loggedentity is None:
                # record the id number of the log
                point.loggedentity_id = loggedentity.id
                print("{} - {} log registered".format(point.asset.name, point.name))
            db.session.commit()
            session.close()
    db.session.close()
