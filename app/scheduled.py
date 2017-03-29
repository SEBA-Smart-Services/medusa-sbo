from app.models import IssueHistory, IssueHistoryTimestamp, Site, AssetComponent, LoggedEntity
from app import db, registry, app
import datetime

# make a record of the quantity of issues at each site
def record_issues():
	timestamp = IssueHistoryTimestamp(timestamp=datetime.datetime.now())
	for site in Site.query.all():
		issues = site.get_unresolved()
		site_history = IssueHistory(issues=len(issues), site=site, timestamp=timestamp)
		timestamp.issues.append(site_history)
		db.session.add(timestamp)
		db.session.commit()

# link medusa assets to webreports logs. XML file must have been imported first
def register_components():
    for component in AssetComponent.query.filter(AssetComponent.loggedentity_path != '').all():
        session = registry.get(component.asset.site.db_name)
        if not session is None:
            loggedentity = session.query(LoggedEntity).filter_by(path=component.loggedentity_path).first()
            if not loggedentity is None:
                component.loggedentity_id = loggedentity.id
                component.loggedentity_path = ''
                print("{} - {} log registered".format(component.asset.name, component.name))
            db.session.commit()