from app import cmms
from app.models import EmailTemplate
from .emailClient import EmailClient
from app.cmms.controllers import CMMS
from smtplib import SMTPRecipientsRefused, SMTPDataError
import os

#create pathway to config
mydir = os.path.dirname(os.path.abspath(__file__))
#new_path = os.path.join(mydir, '..', '..', 'config.txt')

import configparser
config = configparser.ConfigParser()
#config.read(new_path)
config.read('/var/lib/medusa/medusa-development.ini')
notify_email = config.get("configurations","notify_email")

class Notifier():

    def __init__(self):
        self.email_client = EmailClient(notify_email)
        self.cmms = CMMS()

    def issue_notify(self, issue):
        # send email if meets email priority
        if issue.priority < issue.asset.site.email_trigger_priority:
            self.send_mail_issue(issue)
        # send CMMS work request if meets WO priority
        if issue.priority < issue.asset.site.cmms_trigger_priority:
            self.send_WO(issue)

    def send_mail_issue(self, issue):
        # send email notification
        template = EmailTemplate.query.filter_by(name='Alert').one()
        data = {'asset':issue.asset.name, 'issue':issue.algorithm.descr, 'timestamp':issue.recent_timestamp}
        for email in issue.asset.site.emails:
            self.email_client.send_template(template, data, email.address)

    def send_WO(self, issue):
        # send WO through CMMS
        if issue.asset.site.inbuildings_config.enabled:
            self.cmms.raise_job_inbuildings(issue)

    # send report to all emails for a site
    def send_mail_report(self, report, site):
        # grab template
        template = EmailTemplate.query.filter_by(name='Report').one()
        data = {'site':site.name}

        # save report to temporary storage
        report_path = 'report.pdf'
        file = open(report_path, 'wb+')
        file.write(report)
        file.close()

        # send report to emails
        for email in site.emails:
            try:
                self.email_client.send_template(template, data, email.address, [report_path])
            except (SMTPRecipientsRefused, SMTPDataError):
                print('Could not send email to {}'.format(email.address))

        # delete local report
        os.remove(report_path)
