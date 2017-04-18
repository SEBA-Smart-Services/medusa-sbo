from app.models import IssueHistory, IssueHistoryTimestamp, Site, AssetPoint, LoggedEntity
from app import db, registry, app
from base64 import b64encode
import datetime

# make a record of the quantity of issues at each site. Used for graphing performance over time
def record_issues():
    timestamp = IssueHistoryTimestamp(timestamp=datetime.datetime.now())
    for site in Site.query.all():
        issues = site.get_unresolved()
        site_history = IssueHistory(issues=len(issues), site=site, timestamp=timestamp)
        timestamp.issues.append(site_history)
        db.session.add(timestamp)
        db.session.commit()
        db.session.close()

# link medusa assets to webreports logs. XML file must have been imported and bound first for this to work
@app.route('/register')
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
