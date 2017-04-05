from app.models import IssueHistory, IssueHistoryTimestamp, Site, AssetPoint, LoggedEntity
from app import db, registry
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

# link medusa assets to webreports logs. XML file must have been imported first for this to work
def register_points():
    for point in AssetPoint.query.filter(AssetPoint.loggedentity_path != '').all():
        session = registry.get(point.asset.site.db_key)
        if not session is None:
            # search to see if the XML generated file exists in the WebReports server
            loggedentity = session.query(LoggedEntity).filter_by(path=point.loggedentity_path).first()
            if not loggedentity is None:
                point.loggedentity_id = loggedentity.id
                point.loggedentity_path = ''
                print("{} - {} log registered".format(point.asset.name, point.name))
            db.session.commit()
            db.session.close()
            session.close()
