from app import cmms
from app.models import EmailTemplate
from .emailClient import EmailClient

class Notifier():

    def __init__(self):
        self.email_client = EmailClient('config.ini', 'medusa@sebbqld.com')

    def send_issue(self, issue):
        if issue.priority < issue.asset.site.email_trigger_priority:
            template = EmailTemplate.query.filter_by(name='Alert').one()
            data = {'asset':issue.asset.name, 'issue':issue.algorithm.descr, 'timestamp':issue.recent_timestamp}
            for email in issue.asset.site.emails:
                self.email_client.send_template(template, data, email.address)
        if issue.priority < issue.asset.site.cmms_trigger_priority:
            cmms.controllers.send()
