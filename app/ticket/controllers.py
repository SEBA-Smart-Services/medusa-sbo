from flask import request, render_template, url_for, redirect, jsonify, flash, g
from app import app, db
import datetime

from app.models import Site
from app.models.users import User
from app.ticket.models import FlicketTicket, FlicketStatus, FlicketSubscription, FlicketPriority, FlicketCategory

from app.ticket.forms.flicket_forms import SearchEmailForm, CreateTicketForm

from app.ticket.scripts.flicket_functions import add_action
from app.ticket.scripts.email import FlicketMail
from app.ticket.scripts.flicket_upload import UploadAttachment

#creating a ticket
@app.route('/ticket/create', methods=['GET', 'POST'])
def ticket_create():
    form = CreateTicketForm()

    if form.validate_on_submit():

        # this is a new post so ticket status is 'open'
        ticket_status = FlicketStatus.query.filter_by(status='open').first()
        ticket_priority = FlicketPriority.query.filter_by(id=int(form.priority.data)).first()
        ticket_category = FlicketCategory.query.filter_by(id=int(form.category.data)).first()

        files = request.files.getlist("file")
        upload_attachments = UploadAttachment(files)
        if upload_attachments.are_attachements():
            upload_attachments.upload_files()


        # submit ticket data to database
        new_ticket = FlicketTicket(ticket_name=form.title.data,
                                   date_added=datetime.datetime.now(),
                                   user=g.user,
                                   current_status=ticket_status,
                                   description=form.content.data,
                                   ticket_priority=ticket_priority,
                                   category=ticket_category
                                   )
        db.session.add(new_ticket)

        # add attachments to the dataabase.
        upload_attachments.populate_db(new_ticket)
        # subscribe user to ticket
        subscribe = FlicketSubscription(user=g.user, ticket=new_ticket)
        db.session.add(subscribe)

        # commit changes to the database
        db.session.commit()

        flash('New Ticket created.', category='success')

        return redirect(url_for('flicket_bp.ticket_view', ticket_id=new_ticket.id))

    return render_template('flicket_create.html',
                           title='Flicket - Create Ticket',
                           form=form)


#assigning a ticket
# @app.route('/ticket/assign', methods=['GET', 'POST'])
# def ticket_assign(ticket_id=False):
#     form = SearchEmailForm()
#     ticket = FlicketTicket.query.filter_by(id=ticket_id).first()
#
#     if ticket.current_status.status == 'Closed':
#         flash("Can't assign a closed ticket.")
#         return redirect(url_for('flicket_bp.ticket_view', ticket_id=ticket_id))
#
#     if form.validate_on_submit():
#
#         user = FlicketUser.query.filter_by(email=form.email.data).first()
#
#         if ticket.assigned == user:
#             flash('User is already assigned to ticket silly')
#             return redirect(url_for('flicket_bp.ticket_view', ticket_id=ticket.id ))
#
#         # set status to in work
#         status = FlicketStatus.query.filter_by(status='In Work').first()
#         # assign ticket
#         ticket.assigned = user
#         ticket.current_status = status
#
#         # add action record
#         add_action(action='assign', ticket=ticket, recipient=user)
#
#         # subscribe to the ticket
#         if not ticket.is_subscribed(user):
#             subscribe = FlicketSubscription(
#                 ticket=ticket,
#                 user=user
#             )
#             db.session.add(subscribe)
#
#         db.session.commit()
#
#         # send email to state ticket has been assigned.
#         f_mail = FlicketMail()
#         f_mail.assign_ticket(ticket)
#
#         flash('You reassigned ticket:{}'.format(ticket.id))
#         return redirect(url_for('flicket_bp.ticket_view', ticket_id=ticket.id))
#
#     return render_template("flicket_assign.html", title="Assign Ticket", form=form, ticket=ticket)
