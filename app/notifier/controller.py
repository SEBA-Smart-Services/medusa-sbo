from app import cmms, email
from app.models import EmailTemplate

class Notifier():

    def send_issue(issue):
        if issue.priority > issue.site.email_trigger_priority:
            template = EmailTemplate.query.filter_by(name='Alert').one()
            data = {'asset':issue.asset.name, 'issue':issue.algorithm.descr, 'timestamp':issue.current_timestamp}
            for address in issue.site.emails:
                email.send(template, data, address)
        if issue.priority > issue.site.cmms_trigger_priority:
            cmms.send()
