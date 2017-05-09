from app.models import IssueHistory, IssueHistoryTimestamp, Site
from app import db
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
