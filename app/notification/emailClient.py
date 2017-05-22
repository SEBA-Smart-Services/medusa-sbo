from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.encoders import encode_base64
from string import Template
from app import app
import mimetypes
import smtplib
import os.path

class EmailClient(object):

    def __init__(self, sender):
        # initial settings
        self.set_host(app.config['EMAIL_HOST'], app.config['EMAIL_PORT'])
        self.set_auth(app.config['EMAIL_USERNAME'], app.config['EMAIL_PASSWORD'])
        self.set_sender(sender)

    def set_host(self, host, port):
        self.host = host
        self.port = port

    def set_auth(self, username, password):
        self.username = username
        self.password = password

    def set_sender(self, sender):
        self.sender = sender

    def set_recipients(self, recipients):
        """
        set MIME-friendly email recipients
        'recipients' is either:
         - a single email address as string
         - a list of email addresses as list
        """
        if isinstance(recipients, str):
            self.recipients = recipients
        elif isinstance(recipients, list):
            COMMASPACE = ', '
            self.recipients = COMMASPACE.join(recipients)
        else:
            raise TypeError("recipients must be string or list of strings, " + str(type(recipients)) + " was given")

    def write_message(self, body="", subject="", attachment_paths=[]):
        """
        create an email message using MIME

        body: Main text of email. Plain text for now.
        subject: subject line of email
        attachment_paths: list of fully qualified paths of files to be attached
        """
        msg = MIMEMultipart()
        body = MIMEText(body)
        msg.attach(body)
        msg['Subject'] = subject
        msg['From'] = self.sender
        msg['To'] = self.recipients
        for file_path in attachment_paths:
            #try and guess the file type
            ctype, encoding = mimetypes.guess_type(file_path)
            #if the type can't guessed then send it as binary type
            if ctype is None or encoding is not None:
              ctype = 'application/octet-stream'
            maintype, subtype = ctype.split('/', 1)
            try:
                with open(file_path, 'rb') as f:
                  part = MIMEBase(maintype, subtype)
                  part.set_payload(f.read())
                  encode_base64(part)
                  part.add_header('Content-Disposition', 'attachment', filename=os.path.basename(file_path))
                  msg.attach(part)
            except IOError:
                 print ("error: Can't open the file %s")%file_path

        self.message = msg

    def sendmail(self):
        server = smtplib.SMTP(self.host, self.port)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(self.username, self.password)
        text = self.message.as_string()
        server.sendmail(self.sender, self.recipients, text)
        server.quit()

    def send_template(self, template, data, address, attachment_paths=[]):
        self.set_recipients(address)
        body = Template(template.body).substitute(data)
        self.write_message(body, template.subject, attachment_paths)
        self.sendmail()
