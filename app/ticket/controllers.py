from flask import request, render_template, url_for, redirect, jsonify, flash, g, send_from_directory
from app import app, db
import datetime
import os

from app.models import Site
from app.models.users import User
from flask_user import current_user
from app.ticket.models import FlicketTicket, FlicketStatus, FlicketPost, FlicketSubscription, FlicketPriority, FlicketCategory, FlicketDepartment, FlicketHistory, FlicketUploads, TicketComponent, TicketResolution

from app.models.ITP import Project

from app.ticket.forms.flicket_forms import SearchEmailForm, CreateTicketForm, ReplyForm, CategoryForm, DepartmentForm, EditTicketForm, EditReplyForm
from app.ticket.forms.search import SearchTicketForm
from app.ticket.forms.forms_main import ConfirmPassword

from app.ticket.scripts.flicket_functions import add_action, block_quoter
from app.ticket.scripts.email import FlicketMail
from app.ticket.scripts.flicket_upload import UploadAttachment
from app.ticket.scripts.jinja2_functions import display_post_box

from app.controllers import check_valid_site

app.jinja_env.globals.update(display_post_box=display_post_box)


#creating a ticket
@app.route('/site/<siteid>/ticket/create', methods=['GET', 'POST'])
@app.route('/site/all/ticket/create', methods=['GET', 'POST'])
def ticket_create(siteid=None, projectname=None, component=None, priority=None, category=None):

    form = CreateTicketForm(title=request.args.get('ticket_description'),
                            priority=request.args.get('priority'))

    if form.validate_on_submit():

        # this is a new post so ticket status is 'open'
        ticket_status = FlicketStatus.query.filter_by(status='Open').first()
        ticket_priority = FlicketPriority.query.filter_by(id=int(form.priority.data)).first()
        ticket_category = FlicketCategory.query.filter_by(id=int(form.category.data)).first()
        ticket_component = TicketComponent.query.filter_by(id=request.form['Component']).first()

        if request.form['date_due'] != " " and request.form['date_due'] != None:
            date_due = request.form['date_due']
        else:
            date_due=None
        siteid = request.form['siteid']

        site = Site.query.filter_by(id=siteid).one()
        app.logger.info('new ticket for ' + siteid)
        app.logger.info('new ticket for ' + str(site.id))

        project_id = request.form['project']
        print(project_id)
        if project_id != "":
            project = Project.query.filter_by(id=project_id).first()
            project_id = project.id
        else:
            project_id = None
        print(project_id)

        files = request.files.getlist("file")
        upload_attachments = UploadAttachment(files)
        if upload_attachments.are_attachements():
            upload_attachments.upload_files()

        app.logger.info(str(site.name) + ' ' + str(site.id))
        # submit ticket data to database
        new_ticket = FlicketTicket(
            ticket_name=form.title.data,
            date_added=datetime.datetime.now(),
            user=current_user,
            current_status=ticket_status,
            description=form.content.data,
            ticket_priority=ticket_priority,
            category=ticket_category,
            component=ticket_component,
            site_id=site.id,
            project_id=project_id,
            date_due=date_due
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

    print(request.args.get('site_id'))

    if siteid != None:
        site = Site.query.filter_by(id=siteid).first()
        sites = None
        if projectname != None:
            project = Project.query.filter_by(name=projectname).first()
        else:
            project = None
        projects = Project.query.filter_by(site_id=site.id).all()
    else:
        if current_user.has_role('admin'):
            sites = Site.query.all()
        else:
            sites = current_user.sites
        site = None
        project = None
        #Needs to be removed once ticket model has been updated
        projects = Project.query.all()


    components = TicketComponent.query.all()

    print(request.referrer.split('/')[-1])

    return render_template(
        'flicket/flicket_create.html',
        title='Create Ticket',
        form=form,
        sites=sites,
        site=site,
        project=project,
        projects=projects,
        components=components
    )

@app.route('/site/<siteid>/ticket/<ticket_id>/view', methods=['GET', 'POST'])
@app.route('/site/all/ticket/<ticket_id>/view', methods=['GET', 'POST'])
def ticket_view(ticket_id, siteid=None, page=1):
    # is ticket number legitimate
    ticket = FlicketTicket.query.filter_by(id=ticket_id).first()
    site =  Site.query.filter_by(id=ticket.site_id).one()
    resolutions = TicketResolution.query.all()

    print(request.referrer.split('/')[-2])
    print(siteid)
    if request.referrer.split('/')[-2] == 'all':
        site_all = True
    else:
        site_all = False

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

        flash('You have replied to ticket {}: {}.'.format(ticket.id_zfill, ticket.ticket_name), category="success")

        # if the reply has been submitted for closure.
        if form.submit_close.data:

            return redirect(url_for('change_status', ticket_id=ticket.id, status='Closed'))

        return redirect(url_for('ticket_view', ticket_id=ticket_id))

    # if reply is blank but has been submitted for closure.
    if form.submit_close.data:

        return redirect(url_for('change_status', ticket_id=ticket.id, status='Closed'))

    # get post id and populate contents for auto quoting
    if post_rid:
        query = FlicketPost.query.filter_by(id=post_rid).first()
        reply_contents = "{} wrote on {}\r\n\r\n{}".format(query.user.name, query.date_added, query.content)
        form.content.data = block_quoter(reply_contents)
    if ticket_rid:
        reply_contents = "{} {} wrote on {}\r\n\r\n{}".format(ticket.user.first_name, ticket.user.last_name, ticket.date_added, ticket.description)
        form.content.data = block_quoter(reply_contents)

    replies = replies.paginate(page, app.config['POSTS_PER_PAGE'])

    return render_template(
        'flicket/flicket_view.html',
        title='View Ticket',
        ticket=ticket,
        form=form,
        site=site,
        site_all=site_all,
        replies=replies,
        page=page,
        resolutions=resolutions
    )

@app.route('/site/all/ticket/uploads/<filename>')
def view_ticket_uploads(filename):
    path = os.path.join(os.getcwd(), app.config['TICKET_UPLOAD_FOLDER'])
    return send_from_directory(path, filename)

@app.route('/site/all/tickets', methods=['GET', 'POST'])
@app.route('/site/<siteid>/tickets', methods=['GET', 'POST'])
def tickets(siteid=None):

    access_allowed = check_valid_site(siteid)
    PER_PAGE = 5
    if request.args.get('page') == None:
        page = 1
    else:
        page = int(request.args.get('page'))

    if siteid != None and access_allowed:
        site = Site.query.filter_by(id=siteid).first()
        tickets = FlicketTicket.query.filter_by(site_id=site.id).order_by(FlicketTicket.date_added.desc()).paginate(page, PER_PAGE, False)
    elif current_user.has_role('admin'):
        site = None
        tickets = FlicketTicket.query.order_by(FlicketTicket.date_added.desc()).paginate(page, PER_PAGE, False)
    else:
        tickets = []
        #get all the tickets for a particular user
        tickets = FlicketTicket.query.filter(FlicketTicket.site_id.in_([user_site.id for user_site in current_user.sites]))
        tickets = tickets.order_by(FlicketTicket.date_added.desc()).paginate(page, PER_PAGE, False)
        site = None

    print(tickets)

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

    number_results = len(tickets.items)
    all_status = FlicketStatus.query.all()
    all_priority = FlicketPriority.query.all()
    all_category = FlicketCategory.query.all()

    return render_template('flicket/flicket_tickets.html',
                           title='Tickets',
                           form=form,
                           tickets=tickets,
                           page=page,
                           number_results=number_results,
                           status=status,
                           department=department,
                           category=category,
                           user_id=user_id,
                           site=site,
                           all_status=all_status,
                           all_priority=all_priority,
                           all_category=all_category
                           )

@app.route('/_filter_tickets', methods=['GET', 'POST'])
def filter_tickets():

    PER_PAGE = 5
    if request.args.get('page') == None:
        page = 1
    else:
        page = int(request.args.get('page'))

    siteid = request.args.get('site')

    access_allowed = check_valid_site(siteid)

    if id != None and access_allowed:
        site = Site.query.filter_by(id=siteid).first()
        tickets = FlicketTicket.query.filter_by(site_id=site.id)
    elif current_user.has_role('admin'):
        tickets = FlicketTicket.query
    else:
        tickets = []
        #get all the tickets for a particular user
        for user_site in current_user.sites:
            tickets += FlicketTicket.query.filter_by(site_id=user_site.id)
        site = None

    name = request.args.get('name', None)
    if name == "":
        tickets = tickets
    else:
        tickets = tickets.filter(FlicketTicket.ticket_name.contains(name))
    priority = request.args.get('priority', None)
    if priority == "all":
        tickets = tickets
    else:
        priority = FlicketPriority.query.filter_by(priority=priority).first()
        tickets = tickets.filter_by(ticket_priority_id=priority.id)
    category = request.args.get('category', None)
    if category == "all":
        tickets = tickets
    else:
        category = FlicketCategory.query.filter_by(category=category).first()
        tickets = tickets.filter_by(category_id=category.id)
    status = request.args.get('status', None)
    if status == "all":
        tickets = tickets
    else:
        status = FlicketStatus.query.filter_by(status=status).first()
        tickets = tickets.filter_by(status_id=status.id)
    tickets = tickets.order_by(FlicketTicket.date_added.desc()).paginate(page, PER_PAGE, False)
    previous_page = tickets.has_prev
    next_page = tickets.has_next
    pages = tickets.pages
    print(page)
    print(pages)
    return jsonify({"results":render_template('flicket/ticket_table_template.html', tickets=tickets),
                    "page": page,
                    "next": next_page,
                    "previous": previous_page,
                    "pages": pages})

# edit ticket
@app.route('/site/<siteid>/ticket/<ticket_id>/edit', methods=['GET', 'POST'])
@app.route('/site/all/ticket/<ticket_id>/edit', methods=['GET', 'POST'])
def edit_ticket(ticket_id, siteid=None):
    form = EditTicketForm(ticket_id=ticket_id)

    ticket = FlicketTicket.query.filter_by(id=ticket_id).first()

    if not ticket:
        flash('Could not find ticket.', category='warning')
        return redirect(url_for('tickets'))

    siteid = siteid

    site =  Site.query.filter_by(id=ticket.site_id).one()

    if ticket.project_id != None:
        project = Project.query.filter_by(id=ticket.project_id).first()
    else:
        project=None

    if site != None:
        projects = Project.query.filter_by(site_id=site.id).all()
    else:
        projects=None
    app.logger.info(site.name)
    site_list = Site.query.all()

    if ticket.current_status.status == 'Closed':
        flash('Cannot edit closed ticket.', category='warning')
        return redirect(url_for('ticket_view', ticket_id=ticket.id))

    if ticket.current_status == None:
        ticket_status = FlicketStatus.query.filter_by(status='Open').first()
        ticket.current_status = ticket_status
        db.session.commit()

    # check user is authorised to edit ticket. Currently, only admin or author can do this.
    not_authorised = True
    if ticket.user == current_user or current_user.has_role('admin') or ticket.assigned == current_user:
        not_authorised = False

    if not_authorised:
        flash('You are not authorised to edit this ticket.', category='warning')
        return redirect(url_for('ticket_view', ticket_id=ticket_id))

    if form.validate_on_submit():

        ticket.component = TicketComponent.query.filter_by(id=request.form['Component']).first()
        if request.form['date_due'] != " " and request.form['date_due'] != None:
            ticket.date_due = request.form['date_due']
        site = Site.query.filter_by(name=request.form['sitename']).one()
        ticket.site_id = site.id
        project = Project.query.filter_by(id=request.form['project']).first()
        ticket.project_id = project.id

        db.session.commit()

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

    components = TicketComponent.query.all()

    app.logger.info('edit ticket for site ' + site.name)
    return render_template(
        'flicket/flicket_edittopic.html',
        title='Edit Ticket',
        form=form,
        site=site,
        sites=site_list,
        siteid=siteid,
        project=project,
        projects=projects,
        components=components,
        ticket=ticket
    )


# edit post
@app.route('/site/all/post/<post_id>/edit', methods=['GET', 'POST'])
def edit_post(post_id):

    form = EditReplyForm(post_id=post_id)

    post = FlicketPost.query.filter_by(id=post_id).first()

    if not post:
        flash('Could not find post.', category='warning')
        return redirect(url_for('flicket_main'))

    # check to see if topic is closed. ticket can't be edited once it's closed.
    if post.ticket.current_status.status =="Closed":
        return redirect(url_for('ticket_view', ticket_id=post.ticket.id))

    # check user is authorised to edit post. Only author or admin can do this.
    not_authorised = True
    if post.user == current_user or current_user.has_role('admin'):
        not_authorised = False
    if not_authorised:
        flash('You are not authorised to edit this post.', category='warning')
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
@app.route('/site/all/ticket/<ticket_id>/delete', methods=['GET', 'POST'])
def delete_ticket(ticket_id):
    # check is user is authorised to delete tickets. Currently, only admins can delete tickets.
    if not current_user.has_role('admin'):
        flash('You are not authorised to delete tickets.', category='warning')
        return redirect(url_for('ticket_view', ticket_id=ticket_id))

    ticket = FlicketTicket.query.filter_by(id=ticket_id).first()

    if request.method == "POST":

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

    return render_template('flicket/flicket_delete.html',
                           ticket=ticket,
                           title='Delete Ticket')


# delete post
@app.route('/site/all/ticket/<ticket_id>/post/<post_id>/delete', methods=['GET', 'POST'])
def delete_post(ticket_id, post_id):
    # check user is authorised to delete posts. Only admin can do this.
    if not current_user.has_role('admin'):
        flash('You are not authorised to delete posts', category='warning')

    ticket = FlicketTicket.query.filter_by(id=ticket_id).first()
    post = FlicketPost.query.filter_by(id=post_id).first()

    if request.method == "POST":

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
        flash('post deleted', category='success')
        return redirect(url_for('ticket_view', ticket_id=ticket.id))

    return render_template('flicket/flicket_deletepost.html',
                           post=post,
                           title='Flicket - Delete post')


# delete category
@app.route('/site/all/category/<category_id>/delete', methods=['GET', 'POST'])
def delete_category(category_id=False):
    if category_id:

        # check user is authorised to delete categories. Only admin can do this.
        if not current_user.has_role('admin'):
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
        if not current_user.has_role('admin'):
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
    # form = SearchEmailForm()

    ticket = FlicketTicket.query.filter_by(id=ticket_id).first()
    users = User.query.order_by(User.last_name).all()

    if ticket.current_status == None:
        ticket_status = FlicketStatus.query.filter_by(status='Open').first()
        ticket.current_status = ticket_status
        db.session.commit()

    if ticket.current_status.status == 'Closed':
        flash("Can't assign a closed ticket.")
        return redirect(url_for('ticket_view', ticket_id=ticket_id))

    if request.method == 'POST':
    # if form.validate_on_submit():
        user_id = request.form['user']
        user = User.query.filter_by(id=user_id).first()

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
        app.logger.info('user id: ' + str(user_id))
        if user is not None:
            app.logger.info(user.first_name)

        # subscribe to the ticket
        if not ticket.is_subscribed(user):
            subscribe = FlicketSubscription(
                ticket=ticket,
                user=user
            )
            db.session.add(subscribe)

        db.session.commit()

        # send email to state ticket has been assigned.
        # f_mail = FlicketMail()
        # f_mail.assign_ticket(ticket)

        flash('You reassigned ticket:{}'.format(ticket.id))
        return redirect(url_for('ticket_view', ticket_id=ticket.id))

    return render_template("flicket/flicket_assign.html", title="Assign Ticket", ticket=ticket, users=users)

# view for self claim a ticket
@app.route('/ticket/<ticket_id>/claim', methods=['GET', 'POST'])
def ticket_claim(ticket_id=False):

    if ticket_id:
        # claim ticket
        ticket = FlicketTicket.query.filter_by(id=ticket_id).first()

        if ticket.current_status.status == 'Closed':
            flash('Ticket is closed.', category='warning')
            return redirect(url_for('ticket_view', ticket_id=ticket.id))

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

        if ticket.current_status.status == 'Closed':
            flash('Ticket is closed.', category='warning')
            return redirect(url_for('ticket_view', ticket_id=ticket.id))

        # is ticket assigned.
        if not ticket.assigned:
            flash('Ticket has not been assigned')
            return redirect(url_for('ticket_view', ticket_id=ticket_id))

        # check ticket is owned by user or user is admin
        if (ticket.assigned.id != current_user.id) and (not current_user.has_role('admin')):
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
@app.route('/ticket/<ticket_id>/Close/update', methods=['GET', 'POST'])
def close_status(ticket_id):
    ticket = FlicketTicket.query.filter_by(id=ticket_id).first()
    new_status = FlicketStatus.query.filter_by(status="Closed").first()

    print(request.referrer.split('/')[-4])

    # Check to see if user is authorised to close ticket.
    edit = False
    if ticket.user == current_user:
        edit = True
    if ticket.assigned == current_user:
        edit = True
    if current_user.has_role('admin'):
        edit = True

    if not edit:
        flash('Only the person to which the ticket has been assigned, creator or Admin can close this ticket.',
              category='warning')
        return redirect(url_for('ticket_view', ticket_id=ticket.id))

    # Check to see if the ticket is already closed.
    if ticket.current_status.status == 'Closed':
        flash('Ticket is already closed.', category='warning')
        return redirect(url_for('ticket_view', ticket_id=ticket.id))

    f_mail = FlicketMail()
    f_mail.close_ticket(ticket)

    # add action record
    add_action(action='close', ticket=ticket)

    resolution = TicketResolution.query.filter_by(id=request.form['resolution']).first()

    ticket.current_status = new_status
    ticket.resolution = resolution
    ticket.resolved_by = current_user
    ticket.date_resolved = datetime.datetime.now()
    db.session.commit()

    flash('Ticket {} closed.'.format(str(ticket_id).zfill(5)), category='success')

    return redirect(url_for('ticket_view', ticket_id=ticket.id))

@app.route('/ticket/<ticket_id>/Open/update', methods=['GET', 'POST'])
def open_status(ticket_id):

    ticket = FlicketTicket.query.filter_by(id=ticket_id).first()
    new_status = FlicketStatus.query.filter_by(status="Open").first()

    # Check to see if user is authorised to close ticket.
    edit = False
    if ticket.user == current_user:
        edit = True
    if ticket.assigned == current_user:
        edit = True
    if current_user.has_role('admin'):
        edit = True

    if not edit:
        flash('Only the person to which the ticket has been assigned, creator or Admin can open this ticket.',
              category='warning')
        return redirect(url_for('ticket_view', ticket_id=ticket.id))

    f_mail = FlicketMail()
    f_mail.reopen_ticket(ticket)

    # add action record
    add_action(action='reopen', ticket=ticket)

    ticket.current_status = new_status
    ticket.resolution = None
    ticket.resolved_by = None
    ticket.date_resolved = None
    db.session.commit()

    flash('Ticket {} reopened.'.format(str(ticket_id).zfill(5)), category='success')

    return redirect(url_for('ticket_view', ticket_id=ticket.id))

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
