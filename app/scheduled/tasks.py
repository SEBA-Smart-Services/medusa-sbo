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
def register_points():
    unmapped_points = AssetPoint.query.filter(AssetPoint.loggedentity_id == None).all()
    for point in unmapped_points:
        # session = registry.get(point.asset.site.db_key)
        # if not session is None:
        identifier = 'DONOTMODIFY:' + str(b64encode('{}.{}.{}'.format(point.asset.site.id, point.asset.id, point.id).encode('ascii')).decode('ascii'))
        # search to see if the XML generated file exists in the WebReports server
        loggedentity = LoggedEntity.query.filter_by(descr=identifier).first()
        if loggedentity is not None:
            point.loggedentity_id = loggedentity.id
            app.logger.info("{} - {} log registered".format(point.asset.name, point.name))
        db.session.commit()
    db.session.close()

def get_weather():
    app.weather.controllers.get_weather()

def check_all():
    app.algorithms.algorithms.check_all()

def inbuildings_request_all_sites():
    app.inbuildings.controllers.inbuildings_request_all_sites()
