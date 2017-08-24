from flask import request, render_template, url_for, redirect, jsonify, flash, g
from app import app, db
import datetime

from app.models import Site
from app.models.users import User
from app.ticket.models import FlicketTicket, FlicketStatus, FlicketPost, FlicketSubscription, FlicketPriority, FlicketCategory

from app.ticket.forms.flicket_forms import SearchEmailForm, CreateTicketForm, ReplyForm

from app.ticket.scripts.flicket_functions import add_action, block_quoter
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

        return redirect(url_for('ticket_view', ticket_id=new_ticket.id))


    print('testing')
    print(form)
    return render_template('flicket/flicket_create.html',
                           title='Create Ticket',
                           form=form)

def ticket_view(ticket_id, page=1):
    # is ticket number legitimate
    ticket = FlicketTicket.query.filter_by(id=ticket_id).first()

    if not ticket:
        flash('Cannot find ticket: "{}"'.format(ticket_id), category='warning')
        return redirect(url_for('flicket_bp.tickets'))

    # find all replies to ticket.
    replies = FlicketPost.query.filter_by(ticket_id=ticket_id).order_by(FlicketPost.date_added.asc())

    # get reply id's
    post_rid = request.args.get('post_rid')
    ticket_rid = request.args.get('ticket_rid')

    form = ReplyForm()

    # add reply post
    if form.validate_on_submit():

        # upload file if user has selected one and the file is in accepted list of
        files = request.files.getlist("file")
        upload_attachments = UploadAttachment(files)
        if upload_attachments.are_attachements():
            upload_attachments.upload_files()

        new_reply = FlicketPost(
            ticket=ticket,
            user=g.user,
            date_added=datetime.datetime.now(),
            content=form.content.data
        )
        db.session.add(new_reply)

        # add files to database.
        upload_attachments.populate_db(new_reply)

        # change ticket status to open if closed.
        if ticket.current_status.status.lower() == 'closed':
            ticket_open = FlicketStatus.query.filter_by(status='Open').first()
            ticket.current_status = ticket_open

        # subscribe to the ticket
        if not ticket.is_subscribed(g.user):
            subscribe = FlicketSubscription(
                ticket=ticket,
                user=g.user
            )
            db.session.add(subscribe)

        db.session.commit()

        # send email notification
        mail = FlicketMail()
        mail.reply_ticket(ticket=ticket, reply=new_reply)

        flash('You have replied to ticket {}: {}.'.format(ticket.id_zfill, ticket.title), category="success")

        # if the reply has been submitted for closure.
        if form.submit_close.data:

            return redirect(url_for('flicket_bp.change_status', ticket_id=ticket.id, status='Closed'))

        return redirect(url_for('ticket_view', ticket_id=ticket_id))

    # get post id and populate contents for auto quoting
    if post_rid:
        query = FlicketPost.query.filter_by(id=post_rid).first()
        reply_contents = "{} wrote on {}\r\n\r\n{}".format(query.user.name, query.date_added, query.content)
        form.content.data = block_quoter(reply_contents)
    if ticket_rid:
        reply_contents = "{} wrote on {}\r\n\r\n{}".format(ticket.user.name, ticket.date_added, ticket.content)
        form.content.data = block_quoter(reply_contents)

    replies = replies.paginate(page, app.config['posts_per_page'])

    return render_template('flicket/flicket_view.html',
                           title='View Ticket',
                           ticket=ticket,
                           form=form,
                           replies=replies,
                           page=page)

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
