from flask import request, render_template, url_for, redirect, jsonify, flash, g
from app import app, db
import datetime

from app.models import Site
from app.models.users import User
from flask_user import current_user
from app.ticket.models import FlicketTicket, FlicketStatus, FlicketPost, FlicketSubscription, FlicketPriority, FlicketCategory, FlicketDepartment, FlicketHistory

from app.ticket.forms.flicket_forms import SearchEmailForm, CreateTicketForm, ReplyForm, CategoryForm, DepartmentForm, EditTicketForm
from app.ticket.forms.search import SearchTicketForm

from app.ticket.scripts.flicket_functions import add_action, block_quoter
from app.ticket.scripts.email import FlicketMail
from app.ticket.scripts.flicket_upload import UploadAttachment


# view users
@app.route('/ticket/main', methods=['GET', 'POST'])
def index():

    """ View showing flicket main page. We use this to display some statistics."""
    s_closed = 'Closed'
    s_open = 'Open'
    s_wip = 'In Work'

    days = 7
    # converts days into datetime object
    days_obj = datetime.datetime.now() - datetime.timedelta(days=days)

    # initialise base query
    query = FlicketTicket.query
    total = FlicketTicket.query.count()
    total_days = query.filter(FlicketTicket.date_added > days_obj).count()

    # get list of statuses
    statuses = [({'id': s.id, 'status': s.status}, {}) for s in FlicketStatus.query.order_by(FlicketStatus.status).all()]
    # find number of tickets for each status
    for s in statuses:
        ticket_num = query.filter(FlicketTicket.current_status.has(FlicketStatus.id == s[0]['id'])).count()
        s[1]['ticket_num'] = ticket_num

    # get list of departments
    departments = [({'id': d.id, 'department': d.department}, []) for d in FlicketDepartment.query.all()]

    # department_filter = FlicketDepartment.query.filter_by(department=department).first()
    # tickets = tickets.filter(FlicketTicket.category.has(FlicketCategory.department == department_filter))

    # find number of tickets for each department based on status
    for d in departments:
        for s in statuses:
            department_filter = query.filter(FlicketTicket.category.has(FlicketCategory.department_id == d[0]['id']))
            ticket_num = department_filter.filter(FlicketTicket.current_status.has(FlicketStatus.id == s[0]['id'])).count()
            d[1].append(({'status': s[0]['status']}, {'total_num': ticket_num}))

    return render_template('flicket/flicket_index.html',
                           total=total,
                           total_days=total_days,
                           days=days,
                           statuses=statuses,
                           departments=departments)


#creating a ticket
@app.route('/ticket/create', methods=['GET', 'POST'])
def ticket_create():
    form = CreateTicketForm()

    if form.validate_on_submit():

        # this is a new post so ticket status is 'open'
        ticket_status = FlicketStatus.query.filter_by(status='Open').first()
        ticket_priority = FlicketPriority.query.filter_by(id=int(form.priority.data)).first()
        ticket_category = FlicketCategory.query.filter_by(id=int(form.category.data)).first()

        files = request.files.getlist("file")
        upload_attachments = UploadAttachment(files)
        if upload_attachments.are_attachements():
            upload_attachments.upload_files()


        # submit ticket data to database
        new_ticket = FlicketTicket(ticket_name=form.title.data,
                                   date_added=datetime.datetime.now(),
                                   user=current_user,
                                   current_status=ticket_status,
                                   description=form.content.data,
                                   ticket_priority=ticket_priority,
                                   category=ticket_category
                                   )
        db.session.add(new_ticket)

        # add attachments to the dataabase.
        upload_attachments.populate_db(new_ticket)
        # subscribe user to ticket
        subscribe = FlicketSubscription(user=current_user, ticket=new_ticket)
        db.session.add(subscribe)

        # commit changes to the database
        db.session.commit()

        flash('New Ticket created.', category='success')

        return redirect(url_for('ticket_view', ticket_id=new_ticket.id))


    return render_template('flicket/flicket_create.html',
                           title='Create Ticket',
                           form=form)

@app.route('/ticket/<ticket_id>/view')
def ticket_view(ticket_id, page=1):
    # is ticket number legitimate
    ticket = FlicketTicket.query.filter_by(id=ticket_id).first()

    if not ticket:
        flash('Cannot find ticket: "{}"'.format(ticket_id), category='warning')
        return redirect(url_for('tickets'))

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
            user=current_user,
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
        if not ticket.is_subscribed(current_user):
            subscribe = FlicketSubscription(
                ticket=ticket,
                user=current_user
            )
            db.session.add(subscribe)

        db.session.commit()

        # send email notification
        mail = FlicketMail()
        mail.reply_ticket(ticket=ticket, reply=new_reply)

        flash('You have replied to ticket {}: {}.'.format(ticket.id_zfill, ticket.title), category="success")

        # if the reply has been submitted for closure.
        if form.submit_close.data:

            return redirect(url_for('change_status', ticket_id=ticket.id, status='Closed'))

        print(ticket.subscribers)
        return redirect(url_for('ticket_view', ticket_id=ticket_id))

    # get post id and populate contents for auto quoting
    if post_rid:
        query = FlicketPost.query.filter_by(id=post_rid).first()
        reply_contents = "{} wrote on {}\r\n\r\n{}".format(query.user.name, query.date_added, query.content)
        form.content.data = block_quoter(reply_contents)
    if ticket_rid:
        reply_contents = "{} wrote on {}\r\n\r\n{}".format(ticket.user.name, ticket.date_added, ticket.content)
        form.content.data = block_quoter(reply_contents)

    app.config['posts_per_page'] = 10
    replies = replies.paginate(page, app.config['posts_per_page'])

    return render_template('flicket/flicket_view.html',
                           title='View Ticket',
                           ticket=ticket,
                           form=form,
                           replies=replies,
                           page=page)

@app.route('/tickets', methods=['GET', 'POST'])
def tickets(page=1):

    form = SearchTicketForm()

    # get request arguments from the url
    status = request.args.get('status')
    department = request.args.get('department')
    category = request.args.get('category')
    content = request.args.get('content')
    user_id = request.args.get('user_id')

    if form.validate_on_submit():

        department = ''
        category = ''
        status = ''

        user = User.query.filter_by(email=form.email.data).first()
        if user:
            user_id = user.id

        # convert form inputs to it's table title
        if form.department.data:
            department = FlicketDepartment.query.filter_by(id=form.department.data).first().department
        if form.category.data:
            category = FlicketCategory.query.filter_by(id=form.category.data).first().category
        if form.status.data:
            status = FlicketStatus.query.filter_by(id=form.status.data).first().status

        return redirect(url_for('tickets',
                                content=form.content.data,
                                page=page,
                                department=department,
                                category=category,
                                status=status,
                                user_id=user_id,
                                ))

    # todo: get data from api

    tickets = FlicketTicket.query
    if status:
        tickets = tickets.filter(FlicketTicket.current_status.has(FlicketStatus.status == status))
        form.status.data = FlicketStatus.query.filter_by(status=status).first().id
    if category:
        tickets = tickets.filter(FlicketTicket.category.has(FlicketCategory.category == category))
        form.category.data = FlicketCategory.query.filter_by(category=category).first().id
    if department:
        department_filter = FlicketDepartment.query.filter_by(department=department).first()
        tickets = tickets.filter(FlicketTicket.category.has(FlicketCategory.department == department_filter))
        form.department.data = department_filter.id
    if user_id:
        tickets = tickets.filter_by(assigned_id=int(user_id))

    if content:
        # search the titles
        form.content.data = content

        f1 = FlicketTicket.title.ilike('%' + content + '%')
        f2 = FlicketTicket.content.ilike('%' + content + '%')
        f3 = FlicketTicket.posts.any(FlicketPost.content.ilike('%' + content + '%'))
        tickets = tickets.filter(f1 | f2 | f3)

    tickets = tickets.order_by(FlicketTicket.id.desc())
    number_results = tickets.count()

    # tickets = tickets.paginate(page, app.config['posts_per_page'])

    return render_template('flicket/flicket_tickets.html',
                           title='Tickets',
                           form=form,
                           tickets=tickets,
                           page=page,
                           number_results=number_results,
                           status=status,
                           department=department,
                           category=category,
                           user_id=user_id
                           )

# edit ticket
@app.route('/ticket/<ticket_id>/edit', methods=['GET', 'POST'])
def edit_ticket(ticket_id):
    form = EditTicketForm(ticket_id=ticket_id)

    ticket = FlicketTicket.query.filter_by(id=ticket_id).first()

    if ticket.current_status == None:
        ticket_status = FlicketStatus.query.filter_by(status='Open').first()
        ticket.current_status = ticket_status
        db.session.commit()

    if not ticket:
        flash('Could not find ticket.', category='warning')
        return redirect(url_for('flicket_main'))

    # check to see if topic is closed. ticket can't be edited once it's closed.
    if ticket.current_status.status == "Closed":
        return redirect(url_for('ticket_view', ticket_id=ticket.id))

    # check user is authorised to edit ticket. Currently, only admin or author can do this.
    not_authorised = True
    if ticket.user == current_user or current_user.is_admin:
        not_authorised = False

    if not_authorised:
        flash('You are not authorised to edit this ticket.', category='warning')
        return redirect(url_for('ticket_view', ticket_id=ticket_id))

    if form.validate_on_submit():

        # before we make any changes store the original post content in the history table if it has changed.
        if ticket.modified_id:
            history_id = ticket.modified_id
        else:
            history_id = ticket.started_id
        if ticket.description != form.content.data:
            history = FlicketHistory(
                original_content = ticket.description,
                topic=ticket,
                date_modified = datetime.datetime.now(),
                user_id = history_id
            )
            db.session.add(history)


        # loop through the selected uploads for deletion.
        if len(form.uploads.data) > 0:
            for i in form.uploads.data:
                # get the upload document information from the database.
                query = FlicketUploads.query.filter_by(id=i).first()
                # define the full uploaded filename
                the_file = os.path.join(app.config['ticket_upload_folder'], query.filename)

                if os.path.isfile(the_file):
                    # delete the file from the folder
                    os.remove(the_file)

                db.session.delete(query)

        ticket_status = FlicketStatus.query.filter_by(status='open').first()
        ticket_priority = FlicketPriority.query.filter_by(id=int(form.priority.data)).first()
        ticket_category = FlicketCategory.query.filter_by(id=int(form.category.data)).first()

        ticket.description = form.content.data
        ticket.ticket_name = form.title.data
        ticket.modified = current_user
        ticket.date_modified = datetime.datetime.now()
        ticket.current_status = ticket_status
        ticket.ticket_priority = ticket_priority
        ticket.category = ticket_category

        files = request.files.getlist("file")
        upload_attachments = UploadAttachment(files)
        if upload_attachments.are_attachements():
            upload_attachments.upload_files()

        # add files to database.
        upload_attachments.populate_db(ticket)

        db.session.commit()
        flash('Ticket successfully edited.', category='success')
        return redirect(url_for('ticket_view', ticket_id=ticket_id))

    form.content.data = ticket.description
    form.priority.data = ticket.ticket_priority_id
    form.title.data = ticket.ticket_name
    form.category.data = ticket.category_id

    return render_template('flicket/flicket_edittopic.html',
                           title='Edit Ticket',
                           form=form)


# edit post
@app.route('/post/<post_id>/edit', methods=['GET', 'POST'])
def edit_post(post_id):

    form = EditReplyForm(post_id=post_id)

    post = FlicketPost.query.filter_by(id=post_id).first()

    if not post:
        flash('Could not find post.', category='warning')
        return redirect(url_for('flicket_main'))

    # check to see if topic is closed. ticket can't be edited once it's closed.
    if is_ticket_closed(post.ticket.current_status.status):
        return redirect(url_for('ticket_view', ticket_id=post.ticket.id))

    # check user is authorised to edit post. Only author or admin can do this.
    not_authorised = True
    if post.user == current_user or current_user.is_admin:
        not_authorised = False
    if not_authorised:
        flash('You are not authorised to edit this ticket.', category='warning')
        return redirect(url_for('ticket_view', ticket_id=post.ticket_id))

    if form.validate_on_submit():

        # before we make any changes store the original post content in the history table if it has changed.
        if post.modified_id:
            history_id = post.modified_id
        else:
            history_id = post.user_id
        if post.content != form.content.data:
            history = FlicketHistory(
                original_content = post.content,
                post=post,
                date_modified = datetime.datetime.now(),
                user_id = history_id
            )
            db.session.add(history)

        # loop through the selected uploads for deletion.
        if len(form.uploads.data) > 0:
            for i in form.uploads.data:
                # get the upload document information from the database.
                query = FlicketUploads.query.filter_by(id=i).first()
                # define the full uploaded filename
                the_file = os.path.join(app.config['ticket_upload_folder'], query.filename)

                if os.path.isfile(the_file):
                    # delete the file from the folder
                    os.remove(the_file)

                db.session.delete(query)


        post.content = form.content.data
        post.modified = current_user
        post.date_modified = datetime.datetime.now()

        files = request.files.getlist("file")
        upload_attachments = UploadAttachment(files)
        if upload_attachments.are_attachements():
            upload_attachments.upload_files()

        # add files to database.
        upload_attachments.populate_db(post)

        db.session.commit()
        flash('Post successfully edited.', category='success')

        return redirect(url_for('ticket_view', ticket_id=post.ticket_id))

    form.content.data = post.content

    return render_template('flicket/flicket_editpost.html',
                           title='Edit Post',
                           form=form)

# delete ticket
@app.route('/ticket/<ticket_id>/delete', methods=['GET', 'POST'])
def delete_ticket(ticket_id):
    # check is user is authorised to delete tickets. Currently, only admins can delete tickets.
    if not current_user.has_role('admin'):
        flash('You are not authorised to delete tickets.', category='warning')
        return redirect(url_for('ticket_view', ticket_id=ticket_id))

    form = ConfirmPassword()

    ticket = FlicketTicket.query.filter_by(id=ticket_id).first()

    if form.validate_on_submit():

        # delete images from database and folder
        images = FlicketUploads.query.filter_by(topic_id=ticket_id)
        for i in images:
            # delete files
            os.remove(os.path.join(os.getcwd(), app.config['ticket_upload_folder'] + '/' + i.file_name))
            # remove from database
            db.session.delete(i)

        db.session.delete(ticket)
        # commit changes
        db.session.commit()
        flash('ticket deleted', category='success')
        return redirect(url_for('tickets'))

    return render_template('flicket/flicket_deletetopic.html',
                           form=form,
                           ticket=ticket,
                           title='Delete Ticket')


# delete post
@app.route('/post/<post_id>/delete', methods=['GET', 'POST'])
def delete_post(post_id):
    # check user is authorised to delete posts. Only admin can do this.
    if not current_user.is_admin:
        flash('You are not authorised to delete posts', category='warning')

    form = ConfirmPassword()

    post = FlicketPost.query.filter_by(id=post_id).first()

    if form.validate_on_submit():

        # delete images from database and folder
        images = FlicketUploads.query.filter_by(posts_id=post_id)
        for i in images:
            # delete files
            os.remove(os.path.join(os.getcwd(), app.config['ticket_upload_folder'] + '/' + i.file_name))
            # remove from database
            db.session.delete(i)

        db.session.delete(post)
        # commit changes
        db.session.commit()
        flash('ticket deleted', category='success')
        return redirect(url_for('tickets'))

    return render_template('flicket/flicket_deletepost.html',
                           form=form,
                           post=post,
                           title='Flicket - Delete post')


# delete category
@app.route('/category/<category_id>/delete', methods=['GET', 'POST'])
def delete_category(category_id=False):
    if category_id:

        # check user is authorised to delete categories. Only admin can do this.
        if not current_user.is_admin:
            flash('You are not authorised to delete categories.', category='warning')

        form = ConfirmPassword()

        categories = FlicketTicket.query.filter_by(category_id=category_id)
        category = FlicketCategory.query.filter_by(id=category_id).first()

        # stop the deletion of categories assigned to tickets.
        if categories.count() > 0:
            flash('Category is linked to posts. Category can not be deleted unless link is removed.', category="danger")
            return redirect(url_for('departments'))

        if form.validate_on_submit():
            # delete category from database
            category = FlicketCategory.query.filter_by(id=category_id).first()

            db.session.delete(category)
            # commit changes
            db.session.commit()
            flash('Category deleted', category='success')
            return redirect(url_for('departments'))

        notification = "You are trying to delete category <span class=\"label label-default\">{}</span> that belongs to department <span class=\"label label-default\">{}</span>.".format(
            category.category, category.department.department)

        return render_template('flicket/flicket_delete.html',
                               form=form,
                               notification=notification,
                               title='Flicket - Delete')


# delete department
@app.route('/department/<department_id>/delete', methods=['GET', 'POST'])
def delete_department(department_id=False):
    if department_id:

        # check user is authorised to delete departments. Only admin can do this.
        if not current_user.is_admin:
            flash('You are not authorised to delete departments.', category='warning')

        form = ConfirmPassword()

        #
        departments = FlicketCategory.query.filter_by(department_id=department_id)
        department = FlicketDepartment.query.filter_by(id=department_id).first()

        # we can't delete any departments associated with categories.
        if departments.count() > 0:
            flash(
                'Department has categories linked to it. Department can not be deleted unless the categories are removed.',
                category="danger")
            return redirect(url_for('departments'))

        if form.validate_on_submit():
            # delete category from database
            department = FlicketDepartment.query.filter_by(id=department_id).first()

            db.session.delete(department)
            # commit changes
            db.session.commit()
            flash('Department {} deleted.'.format(department.department), category='success')
            return redirect(url_for('departments'))

        notification = "You are trying to delete department <span class=\"label label-default\">{}</span>.".format(
            department.department)

        return render_template('flicket_delete.html',
                               form=form,
                               notification=notification,
                               title='Flicket - Delete')

#assigning a ticket
@app.route('/ticket/<ticket_id>/assign', methods=['GET', 'POST'])
def ticket_assign(ticket_id=False):
    form = SearchEmailForm()
    ticket = FlicketTicket.query.filter_by(id=ticket_id).first()

    if ticket.current_status == None:
        ticket_status = FlicketStatus.query.filter_by(status='Open').first()
        ticket.current_status = ticket_status
        db.session.commit()

    if ticket.current_status.status == 'Closed':
        flash("Can't assign a closed ticket.")
        return redirect(url_for('ticket_view', ticket_id=ticket_id))

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        if ticket.assigned == user:
            flash('User is already assigned to ticket')
            return redirect(url_for('ticket_view', ticket_id=ticket.id ))

        # set status to in work
        status = FlicketStatus.query.filter_by(status='In Work').first()
        # assign ticket
        ticket.assigned = user
        ticket.current_status = status

        # add action record
        add_action(action='assign', ticket=ticket, recipient=user)

        # subscribe to the ticket
        if not ticket.is_subscribed(user):
            subscribe = FlicketSubscription(
                ticket=ticket,
                user=user
            )
            db.session.add(subscribe)

        db.session.commit()

        # send email to state ticket has been assigned.
        f_mail = FlicketMail()
        f_mail.assign_ticket(ticket)

        flash('You reassigned ticket:{}'.format(ticket.id))
        return redirect(url_for('ticket_view', ticket_id=ticket.id))

    return render_template("flicket/flicket_assign.html", title="Assign Ticket", form=form, ticket=ticket)

# view for self claim a ticket
@app.route('/ticket/<ticket_id>/claim', methods=['GET', 'POST'])
def ticket_claim(ticket_id=False):
    if ticket_id:
        # claim ticket
        ticket = FlicketTicket.query.filter_by(id=ticket_id).first()

        # set status to in work
        status = FlicketStatus.query.filter_by(status='In Work').first()
        ticket.assigned = current_user
        ticket.current_status = status
        db.session.commit()

        # add action record
        add_action(action='claim', ticket=ticket)

        # send email notifications
        f_mail = FlicketMail()
        f_mail.assign_ticket(ticket=ticket)

        flash('You claimed ticket:{}'.format(ticket.id))
        return redirect(url_for('ticket_view', ticket_id=ticket.id))

    return redirect(url_for('tickets'))

# view to release a ticket user has been assigned.
@app.route('/ticket/<ticket_id>/release', methods=['GET', 'POST'])
def release(ticket_id=False):
    if ticket_id:

        ticket = FlicketTicket.query.filter_by(id=ticket_id).first()

        # is ticket assigned.
        if not ticket.assigned:
            flash('Ticket has not been assigned')
            return redirect(url_for('ticket_view', ticket_id=ticket_id))

        # check ticket is owned by user or user is admin
        if (ticket.assigned.id != current_user.id) and (not current_user.is_admin):
            flash('You can not release a ticket you are not working on.')
            return redirect(url_for('ticket_view', ticket_id=ticket_id))

        # set status to open
        status = FlicketStatus.query.filter_by(status='Open').first()
        ticket.current_status = status
        ticket.assigned = None
        db.session.commit()

        # add action record
        add_action(action='release', ticket=ticket)


        # send email to state ticket has been released.
        f_mail = FlicketMail()
        f_mail.release_ticket(ticket)

        flash('You released ticket: {}'.format(ticket.id))
        return redirect(url_for('ticket_view', ticket_id=ticket.id))

    return redirect(url_for('tickets'))

# view to subscribe user to a ticket.
@app.route('/ticket/<ticket_id>/subscribe', methods=['GET', 'POST'])
def subscribe_ticket(ticket_id=None):

    if ticket_id:

        ticket = FlicketTicket.query.filter_by(id=ticket_id).one()

        if not ticket.is_subscribed(current_user):
            # subscribe user to ticket
            subscribe = FlicketSubscription(user=current_user, ticket=ticket)
            db.session.add(subscribe)
            db.session.commit()
            flash('You have been subscribed to this ticket.')

        else:

            flash('You are already subscribed to this ticket')

        return redirect(url_for('ticket_view', ticket_id=ticket_id))


# view to unsubscribe user from a ticket.
@app.route('/ticekt/<ticket_id>/unsubscribe', methods=['GET', 'POST'])
def unsubscribe_ticket(ticket_id=None):

    if ticket_id:

        ticket = FlicketTicket.query.filter_by(id=ticket_id).one()

        if ticket.is_subscribed(current_user):

            subscription = FlicketSubscription.query.filter_by(user=current_user, ticket=ticket).one()
            # unsubscribe user to ticket
            db.session.delete(subscription)
            db.session.commit()
            flash('You have been unsubscribed from this ticket.')

        else:

            flash('You are already subscribed from this ticket')

        return redirect(url_for('ticket_view', ticket_id=ticket_id))

# close ticket
@app.route('/ticket/<ticket_id>/<status>/update', methods=['GET', 'POST'])
def change_status(ticket_id, status):

    ticket = FlicketTicket.query.filter_by(id=ticket_id).first()
    closed = FlicketStatus.query.filter_by(status=status).first()

    # Check to see if user is authorised to close ticket.
    edit = False
    if ticket.user == current_user:
        edit = True
    if ticket.assigned == current_user:
        edit = True
    if current_user.is_admin:
        edit = True

    if not edit:
        flash('Only the person to which the ticket has been assigned, creator or Admin can close this ticket.',
              category='warning')
        return redirect(url_for('ticket_view', ticket_id=ticket_id))

    # Check to see if the ticket is already closed.
    if ticket.current_status.status == 'Closed':
        flash('Ticket is already closed.', category='warning')
        return redirect(url_for('ticket_view', ticket_id=ticket.id))

    f_mail = FlicketMail()
    f_mail.close_ticket(ticket)

    # add action record
    add_action(action='close', ticket=ticket)

    ticket.current_status = closed
    ticket.assigned_id = None
    db.session.commit()


    flash('Ticket {} closed.'.format(str(ticket_id).zfill(5)), category='success')

    return redirect(url_for('tickets'))

#
@app.route('/categories/<department_id>', methods=['GET', 'POST'])
def categories(department_id=False):
    form = CategoryForm()
    categories = FlicketCategory.query.filter_by(department_id=department_id)
    department = FlicketDepartment.query.filter_by(id=department_id).first()

    form.department_id.data = department_id

    if form.validate_on_submit():
        add_category = FlicketCategory(category=form.category.data, department=department)
        db.session.add(add_category)
        db.session.commit()
        flash('New category {} added.'.format(form.category.data))
        return redirect(url_for('categories', department_id=department_id))

    return render_template('flicket/flicket_categories.html',
                           title='Categories',
                           form=form,
                           categories=categories,
                           department=department)

@app.route('/category/<category_id>/edit', methods=['GET', 'POST'])
def category_edit(category_id=False):
    if category_id:

        form = CategoryForm()
        category = FlicketCategory.query.filter_by(id=category_id).first()
        form.department_id.data = category.department_id

        if form.validate_on_submit():
            category.category = form.category.data
            db.session.commit()
            flash('Category {} edited.'.format(form.category.data))
            return redirect(url_for('departments'))

        form.category.data = category.category

        return render_template('flicket/flicket_category_edit.html',
                               title='Edit Category',
                               form=form,
                               category=category,
                               department=category.department.department
                               )

    return redirect(url_for('departments'))

# create ticket
@app.route('/departments', methods=['GET', 'POST'])
def departments(page=1):

    form = DepartmentForm()

    query = FlicketDepartment.query

    if form.validate_on_submit():
        add_department = FlicketDepartment(department=form.department.data)
        db.session.add(add_department)
        db.session.commit()
        flash('New department {} added.'.format(form.department.data))
        return redirect(url_for('departments'))

    return render_template('flicket/flicket_departments.html',
                           title='Flicket - Departments',
                           form=form,
                           page=page,
                           departments=_departments)


@app.route('/department/<department_id>/edit', methods=['GET', 'POST'])
def department_edit(department_id=False):
    if department_id:

        form = DepartmentForm()
        query = FlicketDepartment.query.filter_by(id=department_id).first()

        if form.validate_on_submit():
            query.department = form.department.data
            db.session.commit()
            flash('Depart {} edited.'.format(form.department.data))
            return redirect(url_for('departments'))

        form.department.data = query.department

        return render_template('flicket/flicket_department_edit.html',
                               title='Flicket - Edit Department',
                               form=form,
                               department=query
                               )

    return redirect(url_for('departments'))

############################### Other things?? #################################

@app.route('/ticket/topic/<topic_id>/history', methods=['GET', 'POST'])
def flicket_history_topic(topic_id):

    history = FlicketHistory.query.filter_by(topic_id=topic_id).all()
    ticket = FlicketTicket.query.filter_by(id=topic_id).first()

    return render_template(
        'flicket/flicket_history.html',
        title='Flicket - History',
        history=history,
        ticket=ticket)

@app.route('/post/<post_id>/history', methods=['GET', 'POST'])
def flicket_history_post(post_id):

    history = FlicketHistory.query.filter_by(post_id=post_id).all()

    # get the ticket object so we can generate a url to link back to topic.
    post = FlicketPost.query.filter_by(id=post_id).first()
    ticket = FlicketTicket.query.filter_by(id=post.ticket_id).first()

    return render_template(
        'flicket/flicket_history.html',
        title='History',
        history=history,
        ticket=ticket)
