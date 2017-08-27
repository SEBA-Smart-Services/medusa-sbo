#! usr/bin/python3
# -*- coding: utf-8 -*-
#
# Flicket - copyright Paul Bourne: evereux@gmail.com

from flask import render_template, url_for, flash
from flask_mail import Mail, Message

from app import app
from app.ticket.models import FlicketPost
from app.ticket.scripts.decorators import async
#from app.flicket_admin.models.flicket_config import FlicketConfig


class FlicketMail:
    """
    FlicketMail class to send emails.
    """

    def __init__(self):
        """
        Upon initialisation the mail configuration settings are retrieved from the database and
        self.mail is intialised.
        """

        #config = FlicketConfig.query.first()
        config = app.config
        print(config['MAIL_SERVER'])

        app.config.update(
            MAIL_SERVER=config['MAIL_SERVER'],
            MAIL_PORT=config['MAIL_PORT'],
            MAIL_USE_TLS=config['MAIL_USE_TLS'],
            MAIL_USE_SSL=config['MAIL_USE_SSL'],
            MAIL_DEBUG=config['MAIL_DEBUG'],
            MAIL_USERNAME=config['MAIL_USERNAME'],
            MAIL_PASSWORD=config['MAIL_PASSWORD'],
            MAIL_MAX_EMAILS=100,
            MAIL_SUPPRESS_SEND=False,
            MAIL_ASCII_ATTACHMENTS=None,
        )

        self.mail = Mail(app)
        self.mail.init_app(app)

        self.base_url = None

        self.sender = config['MAIL_FROM_EMAIL']

    def create_ticket(self, ticket):
        """"""
        # todo: send email to department heads
        pass

    def reply_ticket(self, ticket=None, reply=None):
        """
        :param ticket: ticket object
        :param reply: reply object
        :return:
        """
        recipients = ticket.get_subscriber_emails()
        title = 'Ticket #{} - {} has new replies.'.format(ticket.id_zfill, ticket.ticket_name)
        ticket_url = url_for('ticket_view', ticket_id=ticket.id)
        html_body = render_template('flicket/email_ticket_replies.html', title=title, number=ticket.id_zfill, ticket_url=ticket_url, ticket=ticket, reply=reply)

        self.send_email(title, self.sender, recipients, html_body)

    def assign_ticket(self, ticket):
        """
        :param ticket: ticket object
        :return:
        """

        recipients = ticket.get_subscriber_emails()
        title = 'Ticket #{} - {} has been assigned.'.format(ticket.id_zfill, ticket.ticket_name)
        ticket_url = url_for('ticket_view', ticket_id=ticket.id)
        html_body = render_template('flicket/email_ticket_assign.html', ticket=ticket, number=ticket.id_zfill,
                                    ticket_url=ticket_url)

        self.send_email(title, self.sender, recipients, html_body)

    def release_ticket(self, ticket):
        """
        :param ticket: ticket object
        :return:
        """

        recipients = ticket.get_subscriber_emails()
        title = 'Ticket #{} - {} has been released.'.format(ticket.id_zfill, ticket.ticket_name)
        ticket_url = url_for('ticket_view', ticket_id=ticket.id)
        html_body = render_template('flicket/email_ticket_release.html', ticket=ticket, number=ticket.id_zfill,
                                    ticket_url=ticket_url)

        self.send_email(title, self.sender, recipients, html_body)

    def close_ticket(self, ticket):
        """
        :param ticket: ticket object
        :return:
        """

        recipients = ticket.get_subscriber_emails()
        title = 'Ticket #{} - {} has been closed.'.format(ticket.id_zfill, ticket.ticket_name)
        ticket_url = url_for('ticket_view', ticket_id=ticket.id)
        html_body = render_template('flicket/email_ticket_close.html', ticket=ticket, ticket_url=ticket_url)

        self.send_email(title, self.sender, recipients, html_body)

    def reopen_ticket(self, ticket):
        """
        :param ticket: ticket object
        :return:
        """

        recipients = ticket.get_subscriber_emails()
        title = 'Ticket #{} - {} has been reopened.'.format(ticket.id_zfill, ticket.ticket_name)
        ticket_url = url_for('ticket_view', ticket_id=ticket.id)
        html_body = render_template('flicket/email_ticket_reopen.html', ticket=ticket, ticket_url=ticket_url)

        self.send_email(title, self.sender, recipients, html_body)


    @async
    def send_email(self, subject, sender, recipients, html_body):
        """
        Sends email via async thread.

        :param subject: string
        :param sender: string
        :param recipients: list()
        :param html_body: string
        :return: nowt
        """

        if not app.config['MAIL_SUPPRESS_SEND']:
            with app.app_context():
                message = Message(subject, sender=sender, recipients=recipients, html=html_body)
                self.mail.send(message)
