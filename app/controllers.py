from app import app, db, registry, user_datastore, security
from app.models import (
    Alarm,
    Asset,
    AssetPoint,
    AssetType,
    Algorithm,
    Email,
    FunctionalDescriptor,
    IssueHistory,
    IssueHistoryTimestamp,
    InbuildingsConfig,
    LoggedEntity,
    LogTimeValue,
    PointType,
    Result,
    Site
)
from app.models import Alarm
from app.models.ITP import Project, ITP, Deliverable, Location, Deliverable_type, ITC, ITC_check_map, Check_generic, Deliverable_ITC_map, Deliverable_check_map, ITC_group, Secondary_location
from app.models.users import User
from app.ticket.models import FlicketTicket, FlicketStatus
from app.forms import SiteConfigForm, AddSiteForm
from flask import json, request, render_template, url_for, redirect, jsonify, flash, make_response, g
from flask_user import current_user
from statistics import mean
import datetime, time
from flask_wtf import Form
from wtforms import TextField, PasswordField, validators
from werkzeug.security import check_password_hash
from flask_security.utils import encrypt_password
from flask_paginate import Pagination

# enforce login required for all pages
@app.before_request
def check_valid_login():
    login_valid = current_user.is_authenticated

    print(request.endpoint)

    if (request.endpoint and
        # not required for login page or static content
        request.endpoint != 'security.login' and
        request.endpoint != 'static' and
        #Flask security pages for accounts do not require logins
        request.endpoint != 'security.forgot_password' and
        request.endpoint != 'security.reset_password' and
        request.endpoint != 'security.send_confirmation' and
        request.endpoint != 'security.confirm_email' and
        request.endpoint != 'security.change_password' and
        not login_valid and
        # check if it's allowed to be public, see public_endpoint decorator
        not getattr(app.view_functions[request.endpoint], 'is_public', False    )) :
        # redirect to login page if they are not authenticated
        return redirect(url_for('security.login'))

def check_valid_site(siteid=None):
    print(siteid)
    site = Site.query.filter_by(id=siteid).first()
    print('checking valid site')
    print(site)
    if site != None:
        if current_user.has_role('admin'):
            print('User is valid')
            return True
        if site not in current_user.sites:
            flash('Not authorised to access this site')
            return False
        else:
            print('User is valid')
            return True
    else:
        print('User is not valid')
        return False

# decorator to make pages not require login
def public_endpoint(function):
    function.is_public = True
    return function


###################################
## main pages for all sites
###################################
# default path
@app.route('/')
def main():
    return redirect(url_for('dashboard_all'))

# show overview dashboard. has aggregated info for all the sites that are attached to the currently logged in user
@app.route('/site/all/dashboard')
def dashboard_all():
    if current_user.has_role('admin'):
        sites = Site.query.all()
    else:
        sites = current_user.sites

    PER_PAGE = 6
    if request.args.get('page') == None:
        page = 1
    else:
        page = int(request.args.get('page'))

    tickets = FlicketTicket.query.all()
    # sqlalchemy can't do relationship filtering to see if an attribute is in a list of objects (e.g. to see if asset.site is in sites)
    # instead, we do the filtering on the ids (e.g. to see if asset.site.id is in the list of site ids)
    if len(sites) > 0:
        site_ids = [site.id for site in sites]
        # get only results that are active or unacknowledged
        # needs to be joined to the site table to do filtering on the site id
        results = Result.query.join(Result.asset).join(Asset.site).filter((Result.active == True) | (Result.acknowledged == False), Site.id.in_(site_ids)).order_by(Asset.priority.asc()).all()
        num_results = len(results)

        if num_results == 0:
            # there are no issues across any sites. Celebrate!
            top_priority = "-"
        else:
            top_priority = results[0].asset.priority

        # join to site table to allow filtering by site id
        if len(Asset.query.join(Asset.site).filter(Site.id.in_(site_ids)).all()) > 0:
            try:
                avg_health = mean([asset.health for asset in Asset.query.join(Asset.site).filter(Site.id.in_(site_ids)).all()])
            except TypeError:
                # one of the asset healths is Null, so set it to zero
                for asset in Asset.query.all():
                    if asset.health is None:
                        asset.health = 0
                db.session.commit()
                avg_health = mean([asset.health for asset in Asset.query.join(Asset.site).filter(Site.id.in_(site_ids)).all()])

        else:
            avg_health = 0

        # get alarms display data

        nalarms = "FAIL"
        # get database session for this site
        try:
            nalarms = get_alarms_per_week(db.session, nweeks=8)

        except Exception as e:
            message = "No data. " + str(e)

        # join to site table to allow filtering by site id
        low_health_assets = len(Asset.query.join(Asset.site).filter(Asset.health < 0.5, Site.id.in_(site_ids)).all())
    else:
        results = []
        num_results = 0
        top_priority = "-"
        avg_health = 0
        low_health_assets = []
        nalarms = []

    open_tickets = FlicketTicket.query.filter(FlicketTicket.current_status.has(FlicketStatus.status == "Open"))
    ticket_num = len(open_tickets.all())
    open_tickets = open_tickets.order_by(FlicketTicket.date_added.desc()).paginate(page, PER_PAGE, False)
    # only send results[0:5], to display the top 5 priority issues in the list
    return render_template('dashboard.html', results=results[0:5], num_results=num_results, top_priority=top_priority, avg_health=avg_health, low_health_assets=low_health_assets, alarmcount=nalarms, tickets=open_tickets, ticket_num=ticket_num)

@app.route('/filter_open_tickets')
def filter_open_tickets():
    PER_PAGE = 6
    if request.args.get('page') == None:
        page = 1
    else:
        page = int(request.args.get('page'))

    siteid = request.args.get('siteid')
    if siteid != None:
        site = Site.query.filter_by(id=siteid).first()
    else:
        site = None
    print(site)

    open_tickets = FlicketTicket.query.filter(FlicketTicket.current_status.has(FlicketStatus.status == "Open"))
    if site != None:
        open_tickets = open_tickets.filter_by(site_id=site.id)
    open_tickets = open_tickets.order_by(FlicketTicket.date_added.desc()).paginate(page, PER_PAGE, False)

    pages = open_tickets.pages

    return jsonify({"results":render_template('flicket/open_ticket_table_template.html', tickets=open_tickets),
                    "page": page,
                    "pages": pages})

# list all sites that are attached to the logged in user
@app.route('/site/all/sites')
def site_list():
    issues = {}
    priority = {}
    if "admin" in current_user.roles:
        sites = Site.query.all()
    else:
        sites = current_user.sites

    for site in sites:
        issues[site.name] = len(site.get_unresolved())
        if not site.get_unresolved_by_priority():
            # there are no issues at this site
            top_priority = "-"
        else:
            top_priority = site.get_unresolved_by_priority()[0].asset.priority
        priority[site.name] = top_priority
    return render_template('sites.html', sites=sites, issues=issues, priority=priority)

# @app.route('/site_filter')
# def site_filter():
#     issues = {}
#     priority = {}
#     if "admin" in current_user.roles:
#         sites = Site.query.all()
#     else:
#         sites = current_user.sites
#
#     for site in sites:
#         issues[site.name] = len(site.get_unresolved())
#         if not site.get_unresolved_by_priority():
#             # there are no issues at this site
#             top_priority = "-"
#         else:
#             top_priority = site.get_unresolved_by_priority()[0].asset.priority
#         priority[site.name] = top_priority
#
#     return jsonify({"results":render_template('/site_table_template.html', sites=sites),
#                     "page": page})

# list all unresolved issues for the sites attached to the logged in user
@app.route('/site/all/issues')
def unresolved_list_all():
    sites = current_user.sites
    results = []
    for site in sites:
        results.extend(site.get_unresolved())
    return render_template('issues.html', results=results)

# handle update from acknowledging/editing notes of issues for all issues
@app.route('/site/all/issues/_submit', methods=['POST'])
def unresolved_issues_submit_all():
    sites = current_user.sites
    results = []
    for site in sites:
        results.extend(site.get_unresolved())

    # unacknowledge all results and set notes field
    for result in results:
        result.acknowledged = False
        result.notes = request.form['notes-' + str(result.id)]

    # re-acknowledge results as per input
    for result_id in request.form.getlist('acknowledge'):
        result = Result.query.filter_by(id=result_id).one()
        result.acknowledged = True

    db.session.commit()

    return redirect(url_for('unresolved_list_all'))

# display chart of unresolved issues over time
@app.route('/site/all/issue-chart')
def unresolved_chart():
    sites = current_user.sites
    history = IssueHistoryTimestamp.query.filter(IssueHistoryTimestamp.timestamp > datetime.datetime.now()-datetime.timedelta(hours=24)).all()

    # generate array to be converted into chart
    # currently just builds a string character by character, can probably be done better
    # header row, contains the x axis label followed by the name of each site
    array = "[['Time',"
    for site in sites:
        array += "'" + site.name + "',"
    array += "],"
    # data rows. each row starts with a timestamp, followed by the issue counts for each site at that time
    for timestamp in history:
        array += "[new Date(" + str(date_to_millis(timestamp.timestamp)) + "),"
        for site in sites:
            # if issues were not recorded for a site at a particular timestamp, use a value of 0
            issues_temp = 0
            for issues in timestamp.issues:
                if (site == issues.site):
                    issues_temp = issues.issues
            array += str(issues_temp) + ","
        array += "],"
    array += "]"

    return render_template('issue_chart.html', sites=sites, array=array, history=history)

# conversion tool for adding entries to the issue chart
# necessary to match python date format to javascript date format
@app.template_filter('date_to_millis')
def date_to_millis(d):
    """Converts a datetime object to the number of milliseconds since the unix epoch."""
    return int(time.mktime(d.timetuple())) * 1000

# handle creation of a new site
@app.route('/site/all/add_site', methods=['GET', 'POST'])
def add_site():

    form = AddSiteForm()

    if request.method == 'GET':
        return render_template('add_site.html', form=form)

    elif request.method == 'POST':
        # if form has errors, return the page (errors will display)
        if not form.validate_on_submit():
            return render_template('add_site.html', form=form)

        site = Site(name=form.name.data)
        # generate cmms config object for the new site (currently only inbuildings)
        site.inbuildings_config = InbuildingsConfig(enabled=False, key="")

        # convert port input to a string
        # if blank it will be recorded as 'None', so manually set empty string
        if form.db_port.data is None:
            form.db_port.data = ""
        form.db_port.data = str(form.db_port.data)

        # update webreports database settings
        form.populate_obj(site)
        site.generate_key()

        if Site.query.filter_by(name=site.name).first() is None:
            db.session.add(site)
            db.session.commit()
            return redirect(url_for('add_asset', sitename=site.name))
        else:
            error = "Facility name " + site.name + " already exists!"
            return render_template('add_site.html', form=form, error=error)

###################################
## main pages for single site
###################################

# set homepage for the site
@app.route('/site/<sitename>')
def homepage(sitename):

    return redirect(url_for('dashboard_site', sitename=sitename))

# show site overview dashboard
@app.route('/site/<sitename>/dashboard')
def dashboard_site(sitename):
    PER_PAGE = 6
    if request.args.get('page') == None:
        page = 1
    else:
        page = int(request.args.get('page'))

    site = Site.query.filter_by(name=sitename).first()
    # only show the top 5 issues by priority in the list
    results = site.get_unresolved_by_priority()[0:4]
    num_results = len(site.get_unresolved())
    tickets = FlicketTicket.query.filter_by(
        site_id = site.id
    ).all()

    if not site.get_unresolved_by_priority():
        # no issues at this site
        top_priority = "-"
    else:
        top_priority = site.get_unresolved_by_priority()[0].asset.priority

    if len(site.assets) > 0:
        try:
            avg_health = mean([asset.health for asset in site.assets])
        except TypeError:
            # one of the asset healths is Null, so fix and set to 0
            for asset in site.assets:
                if asset.health is None:
                    asset.health = 0
            db.session.commit()
            avg_health = mean([asset.health for asset in site.assets])
    else:
        avg_health = 0

    # count the number of assets with <50% health
    low_health_assets = len(Asset.query.filter(Asset.site == site, Asset.health < 0.5).all())

    # get alarms display data
    site = Site.query.filter_by(name=sitename).one()
    nalarms = "FAIL"
    # get database session for this site
    try:
        # NEED TO FILTER THIS BY SITE ID!
        alarms = db.session.query(Alarm).limit(20).all()
        alarm_names = [alarm.AlarmText for alarm in alarms]
        nalarms = get_alarms_per_week(db.session, nweeks=8)

    except Exception as e:
        message = "Site not connected." + str(site.name) + '\n' + str(e)

    open_tickets = FlicketTicket.query.filter(
        (FlicketTicket.current_status.has(FlicketStatus.status == "Open")) &
        (FlicketTicket.site_id == site.id)
    )
    ticket_num = len(open_tickets.all())
    open_tickets = open_tickets.order_by(FlicketTicket.date_added.desc()).paginate(page, PER_PAGE, False)

    return render_template(
        'dashboard.html',
        results=results,
        num_results=num_results,
        top_priority=top_priority,
        avg_health=avg_health,
        low_health_assets=low_health_assets,
        site=site,
        alarmcount=nalarms,
        tickets=open_tickets,
        ticket_num=ticket_num
    )

# list assets on the site
@app.route('/site/<sitename>/assets',  methods=['GET', 'POST'])
def asset_list(sitename):
    site = Site.query.filter_by(name=sitename).one()
    asset_types = AssetType.query.all()
    asset_quantity = {}
    for asset_type in asset_types:
        asset_quantity[asset_type.name] = len(Asset.query.filter_by(site=site, type=asset_type).all())
    itassets=site.it_assets
    return render_template('assets.html', assets=site.assets, asset_quantity=asset_quantity, asset_types=asset_types, site=site, ict_assets=itassets)

# list unresolved issues on the site
@app.route('/site/<sitename>/issues')
def unresolved_list(sitename):
    site = Site.query.filter_by(name=sitename).one()
    results = site.get_unresolved()
    return render_template('issues.html', results=results, site=site)

# handle update from acknowledging/editing notes of issues for a site
@app.route('/site/<sitename>/issues/_submit', methods=['POST'])
def unresolved_issues_submit(sitename):
    site = Site.query.filter_by(name=sitename).one()
    results = site.get_unresolved()

    # unacknowledge all results and set notes field
    for result in results:
        result.acknowledged = False
        result.notes = request.form['notes-' + str(result.id)]

    # re-acknowledge results as per input
    for result_id in request.form.getlist('acknowledge'):
        result = Result.query.filter_by(id=result_id).one()
        result.acknowledged = True

    db.session.commit()

    return redirect(url_for('unresolved_list', sitename=sitename))

# show details for a single asset
@app.route('/site/<sitename>/details/<asset_id>')
def asset_details(sitename, asset_id):
    site = Site.query.filter_by(name=sitename).one()
    asset = Asset.query.filter_by(id=asset_id).one()
    recent_results = Result.query.filter_by(asset=asset, recent=True).all()
    unresolved_results = Result.query.filter(Result.asset==asset, (Result.active == True) | (Result.acknowledged == False)).all()
    algorithms = set(asset.algorithms) - set(asset.exclusions)
    return render_template('asset_details.html', asset=asset, site=site, recent_results=recent_results, unresolved_results=unresolved_results, algorithms=algorithms)

# handle update from acknowledging/editing notes of issues for a single asset
@app.route('/site/<sitename>/results/<asset_id>/_submit', methods=['POST'])
def asset_issues_submit(sitename, asset_id):
    asset = Asset.query.filter_by(id=asset_id).one()
    unresolved_results = Result.query.filter(Result.asset==asset, (Result.active == True) | (Result.acknowledged == False)).all()

    # unacknowledge all results and set notes field
    for result in unresolved_results:
        result.acknowledged = False
        result.notes = request.form['notes-' + str(result.id)]

    # re-acknowledge results as per input
    for result_id in request.form.getlist('acknowledge'):
        result = Result.query.filter_by(id=result_id).one()
        result.acknowledged = True

    db.session.commit()

    return redirect(url_for('asset_details', sitename=sitename, asset_id=asset_id))

# site config page
@app.route('/site/<sitename>/config', methods=['GET','POST'])
def site_config(sitename):
    site = Site.query.filter_by(name=sitename).one()

    #################################
    # There appears to be some orphan sites without InbuildingsConfig relationships
    # not sure how/when??
    # this page breaks for these sites'
    # this try/except statement prevents this
    try:
        inbuildings_config = InbuildingsConfig.query.filter_by(site=site).one()
    except:
        inbuildings_config = None

    ib = InbuildingsConfig.query.limit(10).all()
    all_sites = Site.query.limit(10).all()
    print(ib)
    for s in ib:
        print('IB site id', s.site_id)
    for s in all_sites:
        print('site', s.name, s.id, s.inbuildings_config)

    if request.method == 'POST':
        form = SiteConfigForm()

        # if form has errors, return the page (errors will display)
        if not form.validate_on_submit():
            return render_template('site_config.html', inbuildings_config=inbuildings_config, site=site, form=form)

        # convert port input to a string
        if form.db_port.data is None:
            form.db_port.data = ""
        form.db_port.data = str(form.db_port.data)

        # update webreports database settings
        form.populate_obj(site)
        site.generate_key()

        # update inbuildings settings
        #################################
        # There appears to be some orphan sites without InbuildingsConfig relationships
        # not sure how/when??
        # this page breaks for these sites'
        # this if statement prevents this
        if inbuildings_config is not None:
            inbuildings_config.enabled = form.inbuildings_enabled.data
            inbuildings_config.key = form.inbuildings_key.data

        # update emails
        emails = []
        # remove whitespace and separate out emails from csv
        email_strings = set(form.email_list.data.replace(" ", "").split(','))
        for email_string in email_strings:
            if email_string != '':
                emails.append(Email(address=email_string))
        site.emails = emails

        db.session.commit()
        return redirect(url_for('homepage', sitename=sitename))

    elif request.method == 'GET':
        # prefill form with information from site object
        form = SiteConfigForm(obj=site)

        #################################
        # There appears to be some orphan sites without InbuildingsConfig relationships
        # not sure how/when??
        # this page breaks for these sites'
        # this if statement prevents this
        if inbuildings_config is None:
            form.inbuildings_enabled.data = False # inbuildings_config.enabled
            form.inbuildings_key.data = ''# inbuildings_config.key
        else:
            form.inbuildings_enabled.data = inbuildings_config.enabled
            form.inbuildings_key.data = inbuildings_config.key
        # turn emails into csv
        form.email_list.data = ','.join([email.address for email in site.emails])
        return render_template('site_config.html', site=site, form=form)


# TESTING ALARMS CG

def get_alarms_per_week(session, nweeks=4):
    """
    get all alarm records per week from today until nweeks

    return a list:
    [
        [dt1, nalarms1],
        [dt2, nalarms2],
        ...
    ]

    TODO:
    - move this to "alarms functions and algos module"
    - migrate to a class for handling alarm lists
    - allow more flexibility to include unacknowledged etc

    """
    end_date = datetime.date.today()
    series = []
    for i in range(nweeks):
        start_date = end_date - datetime.timedelta(days=7)
        # count number of alarms in range
        nalarms = db.session.query(Alarm).filter(
            Alarm.DateTimeStamp > start_date,
            Alarm.DateTimeStamp <= end_date
        ).count()
        series.append([start_date.strftime("%-d-%b"), nalarms])
        # get the next earliest week next loop
        end_date = start_date
    # reverse order
    series.reverse()
    # number of alarms
    return series

####################### View all projects for user #############################

@app.route('/projects')
def all_projects():

    PER_PAGE = 5
    if request.args.get('page') == None:
        page = 1
    else:
        page = int(request.args.get('page'))

    if current_user.has_role('admin'):
        sites = Site.query.all()
    else:
        sites = current_user.sites

    projects = Project.query.filter(Project.site_id.in_([site.id for site in sites]))
    projects = projects.order_by(Project.name.asc()).paginate(page, PER_PAGE, False)

    users = User.query.all()

    return render_template('projects.html', projects=projects, users=users, sites=sites)

@app.route('/_filter_projects', methods=['GET', 'POST'])
def filter_project():

    PER_PAGE = 5
    if request.args.get('page') == None:
        page = 1
    else:
        page = int(request.args.get('page'))

    if current_user.has_role('admin'):
        sites = Site.query.all()
    else:
        sites = current_user.sites

    projects = Project.query.filter(Project.site_id.in_([site.id for site in sites]))

    name = request.args.get('name', None)
    if name == "":
        projects = projects
    else:
        projects = projects.filter(Project.name.contains(name))

    project_number = request.args.get('project_number', None)
    if project_number == "":
        projects = projects
    else:
        projects = projects.filter(Project.job_number.contains(project_number))

    site = request.args.get('site', None)
    if site == "all":
        projects = projects
    else:
        site = Site.query.filter_by(name=site).first()
        projects = projects.filter_by(site_id=site.id)

    assigned = request.args.get('assigned', None)
    if assigned == "all":
        projects = projects
    else:
        assigned = User.query.filter_by(id=assigned).first()
        projects = projects.filter_by(assigned_to_id=assigned.id)

    projects = projects.order_by(Project.name.asc()).paginate(page, PER_PAGE, False)

    pages = projects.pages

    return jsonify({"results":render_template('project_table_template.html', projects=projects),
                    "page": page,
                    "pages": pages})

################################################################################
########################## controllers for ITP routes###########################
################################################################################

##################### Project navigation controllers ###########################

#Route for all Projects for a given site
@app.route('/site/<siteid>/projects')
def site_projects_list(siteid):
    if not check_valid_site(siteid):
        return redirect(url_for('dashboard_all'))

    site = Site.query.filter_by(id=siteid).first()
    site_projects = Project.query.filter_by(site_id = site.id).all()

    projects = []
    for i in site_projects:
        projects.append(i)

    return render_template('project/site_projects_list.html', site=site, projects=projects)

#Route for individual Project for a given Site
@app.route('/site/<siteid>/projects/<projectid>')
def site_project(siteid, projectid):
    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid, site_id=site.id).first()
    project_ITP = ITP.query.filter_by(project_id=project.id).first()

    if project_ITP != None:
        deliverables = Deliverable.query.filter_by(ITP_id=project_ITP.id).all()

        total = 0
        completed = 0
        in_progress = 0
        not_applicable = 0
        not_started = 0
        totals = []
        ITC_complete = 0
        ITC_in_progress = 0
        ITC_not_applicable = 0
        ITC_not_started = 0
        total_ITC = 0
        for deliverable in deliverables:
            ITCs = Deliverable_ITC_map.query.filter_by(deliverable_id=deliverable.id).all()
            for ITC in ITCs:
                total_ITC += 1
                if ITC.status == "Completed":
                    ITC_complete += 1
                elif ITC.status == "In Progress":
                    ITC_in_progress += 1
                elif ITC.status == "Not Applicable":
                    ITC_not_applicable += 1
                else:
                    ITC_not_started += 1

                checks = Deliverable_check_map.query.filter_by(deliverable_ITC_map_id=ITC.id).all()
                for check in checks:
                    total += 1
                    if check.status == "Completed":
                        completed += 1
                    elif check.status == "In Progress":
                        in_progress += 1
                    elif check.status == "Not Applicable":
                        not_applicable += 1
                    else:
                        not_started += 1
        if total != 0:
            percents = [(completed/total)*100,(in_progress/total)*100,(not_applicable/total)*100,(not_started/total)*100]
            totals = [totals, completed, in_progress, not_applicable, not_started]
            ITC_totals = [total_ITC, ITC_complete, ITC_in_progress, ITC_not_applicable, ITC_not_started]
        else:
            percents = [0,0,0,0]
            totals = [0,0,0,0,0]
            ITC_totals = [0,0,0,0,0]
    else:
        percents = [0,0,0,0]
        totals = [0,0,0,0,0]
        ITC_totals = [0,0,0,0,0]

    return render_template('project/site_project.html', site=site, project=project, ITP=project_ITP, percents=percents, totals=ITC_totals)

#Route for creating a new Project for a given Site
#add in __init__ to schema so the variables can just be passed to the new Project
#including site_id
@app.route('/site/<siteid>/projects/new', methods=['POST','GET'])
def site_project_new(siteid):
    site = Site.query.filter_by(id=siteid).first()
    users = User.query.all()

    if request.method == 'POST':
        if request.form['project_name'] == None or request.form['project_name'] == "":
            error = "Project name missing!"
            return render_template('project/site_project_new.html', site=site, users=users, error=error)
        elif request.form['job_number'] == None or request.form['job_number'] == "":
            error = "Job Number is missing!"
            return render_template('project/site_project_new.html', site=site, users=users, error=error)
        elif Project.query.filter_by(site_id=site.id, name=request.form['project_name']).first() == None:
            if Project.query.filter_by(job_number=request.form['job_number']).first() != None:
                error =  "Project job number " + request.form['job_number'] + " already exists."
                return render_template('project/site_project_new.html', site=site, users=users, error=error)
            else:
                new_site = Project(request.form['project_name'], request.form['job_number'], request.form['project_description'], site.id)
                if request.form['assigned_to'] != "":
                    assigned_to = User.query.filter_by(id=request.form['assigned_to']).first()
                    new_site.assigned_to_id = assigned_to.id
                db.session.add(new_site)
                db.session.commit()
                return redirect(url_for('site_projects_list', siteid=site.id))
        else:
            error =  site.name + " already has a project named " + request.form['project_name'] + "!"
            return render_template('project/site_project_new.html', site=site, users=users, error=error)
    else:
        return render_template('project/site_project_new.html', site=site, users=users)

#Route for editing a current project
@app.route('/site/<siteid>/projects/<projectid>/edit', methods=['POST','GET'])
def site_project_edit(siteid, projectid):
    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid, site_id=site.id).first()
    users = User.query.all()

    referrer = request.referrer.split('/')[-1].strip('?')
    print(project.start_date)

    if request.method == 'POST':
        if Project.query.filter_by(site_id=site.id, name=request.form['project_name']).first() == None or Project.query.filter_by(site_id=site.id, name=request.form['project_name']).first().id == project.id:
            project_name = request.form['project_name']
            if (project_name != "" and project_name != project.name):
                project.name = project_name
            description = request.form['project_description']
            if (description != "" and request.form['project_description'] != project.description):
                project.description = request.form['project_description']
            job_number = request.form['job_number']
            if Project.query.filter_by(job_number=job_number).first() != None and Project.query.filter_by(job_number=job_number).first().id != project.id:
                error =  "Project job number " + request.form['job_number'] + " already exists."
                return render_template('project/site_project_edit.html', site=site, project=project, users=users, error=error, referrer=referrer)
            if (job_number != "" and job_number != project.job_number):
                project.job_number = request.form['job_number']
            start_date = request.form['start_date']
            if (start_date != "" and start_date != project.start_date):
                project.start_date = start_date
            assigned_to = request.form['assigned_to']
            if (assigned_to != "" and assigned_to != project.assigned_to_id):
                project.assigned_to_id = assigned_to
            db.session.commit()
            if referrer == "projects":
                return redirect(url_for('site_projects_list', siteid=site.id))
            else:
                return redirect(url_for('site_project', siteid=site.id, projectid=project.id))
        else:
            error =  site.name + " already has a project named " + request.form['project_name'] + "!"
            return render_template('project/site_project_edit.html', site=site, project=project, users=users, error=error, referrer=referrer)
    else:
        return render_template('project/site_project_edit.html', site=site, project=project, users=users, referrer=referrer)

#Route for deleting a current project
@app.route('/site/<siteid>/projects/<projectid>/delete', methods=['POST','GET'])
def site_project_delete(siteid, projectid):
    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid, site_id=site.id).first()

    if request.method == 'POST':
        db.session.delete(project)
        db.session.commit()
        return redirect(url_for('site_projects_list', siteid=site.id))
    else:
        return render_template('project/site_project_delete.html', site=site, project=project)

############################ ITP navigation controllers ########################


#Route for details on ITP for project
@app.route('/site/<siteid>/projects/<projectid>/ITP/<ITPid>')
def site_project_ITP(siteid, projectid, ITPid):
    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid, site_id=site.id).first()
    project_ITP = ITP.query.filter_by(id=ITPid, project_id=project.id).first()
    deliverables = Deliverable.query.filter_by(ITP_id=project_ITP.id)

    all_ITCs = []
    total = 0
    completed = 0
    in_progress = 0
    not_applicable = 0
    not_started = 0
    totals = []
    ITC_complete = 0
    ITC_in_progress = 0
    ITC_not_applicable = 0
    ITC_not_started = 0
    total_ITC = 0
    for deliverable in deliverables.all():
        deliver_total = 0
        deliver_completed = 0
        ITCs = Deliverable_ITC_map.query.filter_by(deliverable_id=deliverable.id).all()
        all_ITCs += ITCs
        for ITC in ITCs:
            total_ITC += 1
            if ITC.status == "Completed":
                ITC_complete += 1
            elif ITC.status == "In Progress":
                ITC_in_progress += 1
            elif ITC.status == "Not Applicable":
                ITC_not_applicable += 1
            else:
                ITC_not_started += 1

            checks = Deliverable_check_map.query.filter_by(deliverable_ITC_map_id=ITC.id).all()
            for check in checks:
                total += 1
                deliver_total += 1
                if check.status == "Completed":
                    completed += 1
                    deliver_completed += 1
                elif check.status == "In Progress":
                    in_progress += 1
                elif check.status == "Not Applicable":
                    not_applicable += 1
                else:
                    not_started += 1

        if deliver_total == 0:
            deliverable.percentage_complete = 0
        else:
            deliverable.percentage_complete = deliver_completed/deliver_total*100
        db.session.commit()

        if deliverable.percentage_complete > 0 and deliverable.percentage_complete < 100:
            deliverable.status = "In Progress"
        elif deliverable.percentage_complete == 100:
            deliverable.status = "Completed"
        else:
            deliverable.status = "Not Started"
    if total != 0:
        percents = [(completed/total)*100,(in_progress/total)*100,(not_applicable/total)*100,(not_started/total)*100]
        totals = [total_ITC, ITC_complete, ITC_in_progress, ITC_not_applicable, ITC_not_started]
    else:
        percents = [0,0,0,0]
        totals = [0,0,0,0]

    completion_date = "-"
    if percents[0] == 100:
        completion_date = checks[0].completion_datetime
        for check in checks:
            if check.completion_datetime < completion_date:
                completion_date = check.completion_datetime

    PER_PAGE = 4
    if request.args.get('page') == None:
        page = 1
    else:
        page = int(request.args.get('page'))

    deliverables_list = deliverables.order_by(Deliverable.name.asc()).paginate(page, PER_PAGE, False)
    ITCs = Deliverable_ITC_map.query.filter(Deliverable_ITC_map.deliverable_id.in_([deliverable.id for deliverable in deliverables]))
    ITCs = ITCs.order_by(Deliverable_ITC_map.deliverable_id.desc()).paginate(page, PER_PAGE, False)

    return render_template('ITP/project_ITP.html', site=site, project=project, ITP=project_ITP,
            deliverables=deliverables, completion_date=completion_date, ITCs=ITCs,
            percents=percents, totals=totals, deliverables_list=deliverables_list)

@app.route('/_filter_deliverables_list')
def filter_deliverables_list():
    siteid = request.args.get('siteid')
    projectid = request.args.get('projectid')
    ITPid = request.args.get('ITPid')
    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid, site_id=site.id).first()
    project_ITP = ITP.query.filter_by(id=ITPid, project_id=project.id).first()
    deliverables = Deliverable.query.filter_by(ITP_id=project_ITP.id)

    PER_PAGE = 4
    if request.args.get('page') == None:
        page = 1
    else:
        page = int(request.args.get('page'))

    deliverables_list = deliverables.order_by(Deliverable.name.asc()).paginate(page, PER_PAGE, False)

    pages = deliverables_list.pages

    return jsonify({"results":render_template('deliverable/deliverable_table_template.html',
                    deliverables_list=deliverables_list,
                    site=site,
                    project=project,
                    ITP=project_ITP),
                    "page": page,
                    "pages": pages,})

@app.route('/_filter_ITCs_list')
def filter_ITCs_list():
    siteid = request.args.get('siteid')
    projectid = request.args.get('projectid')
    ITPid = request.args.get('ITPid')

    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid, site_id=site.id).first()
    project_ITP = ITP.query.filter_by(id=ITPid, project_id=project.id).first()
    deliverables = Deliverable.query.filter_by(ITP_id=project_ITP.id).all()

    ITCs = Deliverable_ITC_map.query.filter(Deliverable_ITC_map.deliverable_id.in_([deliverable.id for deliverable in deliverables]))

    PER_PAGE = 4
    if request.args.get('page') == None:
        page = 1
    else:
        page = int(request.args.get('page'))

    ITCs = ITCs.order_by(Deliverable_ITC_map.deliverable_id.asc()).paginate(page, PER_PAGE, False)

    pages = ITCs.pages

    return jsonify({"results":render_template('specific_ITC/ITCs_table_template.html',
                    site=site,
                    project=project,
                    ITP=project_ITP,
                    ITCs=ITCs),
                    "page": page,
                    "pages": pages,})

#Route for creating new ITP
@app.route('/site/<siteid>/projects/<projectid>/ITP/new', methods=['POST','GET'])
def site_project_ITP_new(siteid, projectid):
    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid, site_id=site.id).first()

    if request.method == 'POST':
        if request.form['ITP_name'] == None or request.form['ITP_name'] == "":
            error = "ITP name missing!"
            return render_template('ITP/project_ITP_new.html', site=site, project=project, error=error)
        elif ITP.query.filter_by(project_id=project.id, name=request.form['ITP_name']).first() == None:
            new_ITP = ITP(request.form['ITP_name'], project.id, request.form['ITP_status'])
            db.session.add(new_ITP)
            db.session.commit()
            return redirect(url_for('site_project_ITP', siteid=site.id, projectid=project.id, ITPid=new_ITP.id))
        else:
            error = "ITP " + request.form['ITP_name'] + " already exists"
            return render_template('ITP/project_ITP_new.html', site=site, project=project, error=error)
    else:
        return render_template('ITP/project_ITP_new.html', site=site, project=project)

#Route for editing a current ITP
@app.route('/site/<siteid>/projects/<projectid>/ITP/<ITPid>/edit', methods=['POST','GET'])
def site_project_ITP_edit(siteid, projectid, ITPid):
    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid, site_id=site.id).first()
    project_ITP = ITP.query.filter_by(id=ITPid, project_id=project.id).first()

    if request.method == 'POST':
        if ITP.query.filter_by(project_id=project.id, name=request.form['ITP_name']).first() == None or ITP.query.filter_by(project_id=project.id, name=request.form['ITP_name']).first().id == project_ITP.id:
            ITP_name = request.form['ITP_name']
            if (ITP_name != "" and ITP_name != project_ITP.name):
                project_ITP.name = ITP_name
            description = request.form['ITP_description']
            #if (description != "" and request.form['project_description'] == project.description):
            #    description = request.form['project_description']
            db.session.commit()
            return redirect(url_for('site_project_ITP', siteid=site.id, projectid=project.id, ITPid=project_ITP.id))
        else:
            error =  project.name + " already has a ITP named " + request.form['ITP_name'] + "!"
            return render_template('ITP/project_ITP_edit.html', site=site, project=project, ITP=project_ITP, error=error)
    else:
        return render_template('ITP/project_ITP_edit.html', site=site, project=project, ITP=project_ITP)

#Route for deleting a current ITP
@app.route('/site/<siteid>/projects/<projectid>/ITP/<ITPid>/delete', methods=['POST','GET'])
def site_project_ITP_delete(siteid, projectid, ITPid):
    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid, site_id=site.id).first()
    project_ITP = ITP.query.filter_by(id=ITPid, project_id=project.id).first()

    if request.method == 'POST':
        db.session.delete(project_ITP)
        db.session.commit()
        return redirect(url_for('site_project', siteid=site.id, projectid=project.id))
    else:
        return render_template('ITP/project_ITP_delete.html', site=site, project=project, ITP=project_ITP)


###################### deliverable navigation controllers ######################
#maybe have section for new deliverable type and location creation?
#regex search for names (case insensitive) if not found add to list

#Route for deliverable list
@app.route('/site/<siteid>/projects/<projectid>/ITP/<ITPid>/deliverable')
def site_project_ITP_deliverable_list(siteid, projectid, ITPid):
    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid, site_id=site.id).first()
    project_ITP = ITP.query.filter_by(id=ITPid, project_id=project.id).first()
    deliverables = Deliverable.query.filter_by(ITP_id=project_ITP.id)

    for deliverable in deliverables.all():
        total = 0
        completed = 0
        ITCs = Deliverable_ITC_map.query.filter_by(deliverable_id=deliverable.id).all()
        for ITC in ITCs:
            checks = Deliverable_check_map.query.filter_by(deliverable_ITC_map_id=ITC.id).all()
            for check in checks:
                total += 1
                if check.is_done == True:
                    completed += 1
        if total != 0:
            percent = (completed/total)*100
        else:
            percent = 0
        deliverable.percentage_complete = percent

        if percent > 0 and percent < 100:
            deliverable.status = "In Progress"
        elif percent == 100:
            deliverable.status = "Completed"
        else:
            deliverable.status = "Not Started"
        db.session.commit()

    PER_PAGE = 4
    if request.args.get('page') == None:
        page = 1
    else:
        page = int(request.args.get('page'))

    deliverables_list = deliverables.order_by(Deliverable.name.asc()).paginate(page, PER_PAGE, False)
    all_types = Deliverable_type.query.all()
    all_status = ['Completed', 'In Progress', 'Not started', 'Not Applicable']

    return render_template('deliverable/ITP_deliverable_list.html',
                    site=site,
                    project=project,
                    ITP=project_ITP,
                    deliverables=deliverables,
                    deliverables_list=deliverables_list,
                    all_types=all_types,
                    all_status=all_status)

@app.route('/_filter_deliverable_list_extended', methods=['GET', 'POST'])
def filter_deliverable_list_extended():
    siteid = request.args.get('siteid')
    projectid = request.args.get('projectid')
    ITPid = request.args.get('ITPid')

    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid, site_id=site.id).first()
    project_ITP = ITP.query.filter_by(id=ITPid, project_id=project.id).first()
    deliverables_list = Deliverable.query.filter_by(ITP_id=project_ITP.id)

    PER_PAGE = 4
    if request.args.get('page') == None:
        page = 1
    else:
        page = int(request.args.get('page'))

    siteid = request.args.get('site')

    name = request.args.get('name', None)
    if name == "":
        deliverables_list = deliverables_list
    else:
        deliverables_list = deliverables_list.filter(Deliverable.name.contains(name))
    deliver_type = request.args.get('type', None)
    if deliver_type == "all":
        deliverables_list = deliverables_list
    else:
        deliver_type = Deliverable_type.query.filter_by(name=deliver_type).first()
        deliverables_list = deliverables_list.filter_by(deliverable_type_id=deliver_type.id)
    status = request.args.get('status', None)
    if status == "all":
        deliverables_list = deliverables_list
    else:
        deliverables_list = deliverables_list.filter_by(status=status)

    deliverables_list = deliverables_list.order_by(Deliverable.name.asc()).paginate(page, PER_PAGE, False)
    previous_page = deliverables_list.has_prev
    next_page = deliverables_list.has_next
    pages = deliverables_list.pages
    print(page)
    print(pages)
    return jsonify({"results":render_template('deliverable/deliverables_list_table_template.html',
                    deliverables_list=deliverables_list,
                    site=site,
                    project=project,
                    ITP=project_ITP),
                    "page": page,
                    "next": next_page,
                    "previous": previous_page,
                    "pages": pages})

#Route for deliverable
@app.route('/site/<siteid>/projects/<projectid>/ITP/<ITPid>/deliverable/<deliverableid>')
def site_project_ITP_deliverable(siteid, projectid, ITPid, deliverableid):
    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid, site_id=site.id).first()
    project_ITP = ITP.query.filter_by(id=ITPid, project_id=project.id).first()
    deliverable_current = Deliverable.query.filter_by(id=deliverableid, ITP_id=project_ITP.id).first()
    ITP_ITCs = Deliverable_ITC_map.query.filter_by(deliverable_id=deliverable_current.id).all()
    deliverables = Deliverable.query.filter_by(ITP_id=project_ITP.id).all()

    total = 0
    completed = 0
    in_progress = 0
    not_applicable = 0
    not_started = 0
    totals = []
    ITC_complete = 0
    ITC_in_progress = 0
    ITC_not_applicable = 0
    ITC_not_started = 0
    total_ITC = 0
    ITCs = Deliverable_ITC_map.query.filter_by(deliverable_id=deliverable_current.id).all()
    for ITC in ITCs:
        total_ITC += 1
        if ITC.status == "Completed":
            ITC_complete += 1
        elif ITC.status == "In Progress":
            ITC_in_progress += 1
        elif ITC.status == "Not Applicable":
            ITC_not_applicable += 1
        else:
            ITC_not_started += 1

        checks = Deliverable_check_map.query.filter_by(deliverable_ITC_map_id=ITC.id).all()
        for check in checks:
            total += 1
            if check.status == "Completed":
                completed += 1
            elif check.status == "In Progress":
                in_progress += 1
            elif check.status == "Not Applicable":
                not_applicable += 1
            else:
                not_started += 1
    if total != 0:
        percents = [(completed/total)*100,(in_progress/total)*100,(not_applicable/total)*100,(not_started/total)*100]
        totals = [total_ITC, ITC_complete, ITC_in_progress, ITC_not_applicable, ITC_not_started]
    else:
        percents = [0,0,0,0]
        totals = [0,0,0,0]
    deliverable_current.percentage_complete = percents[0]
    if (deliverable_current.percentage_complete == 100 and deliverable_current.completion_date == None):
        print("Now complete")
        deliverable_current.completion_date = datetime.datetime.now()
    else:
        print("Not complete")
        deliverable_current.completion_date = " "
    db.session.commit()

    return render_template('deliverable/ITP_deliverable.html', site=site, project=project, ITP=project_ITP, deliverable=deliverable_current, ITCs=ITP_ITCs, percents=percents, totals=totals)

#Route for new deliverable
@app.route('/site/<siteid>/projects/<projectid>/ITP/<ITPid>/deliverable/new', methods=['POST','GET'])
def site_project_ITP_deliverable_new(siteid, projectid, ITPid):
    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid, site_id=site.id).first()
    project_ITP = ITP.query.filter_by(id=ITPid, project_id=project.id).first()
    deliverable_types = Deliverable_type.query.all()
    locations = Location.query.filter_by(site_id=site.id).all()
    users = User.query.all()

    if request.method == 'POST':
        if request.form['deliverable_name'] == None or request.form['deliverable_name'] == "":
            error = "Deliverable name is missing!"
            return render_template('deliverable/ITP_deliverable_new.html', site=site, project=project, ITP=project_ITP, types=deliverable_types, locations=locations, error=error)
        elif request.form['deliverable_type'] == None or request.form['deliverable_type'] == "":
            error = "Deliverable type is missing!"
            return render_template('deliverable/ITP_deliverable_new.html', site=site, project=project, ITP=project_ITP, types=deliverable_types, locations=locations, error=error)
        elif request.form['deliverable_location'] == None or request.form['deliverable_location'] == "":
            error = "Deliverable location is missing!"
            return render_template('deliverable/ITP_deliverable_new.html', site=site, project=project, ITP=project_ITP, types=deliverable_types, locations=locations, error=error)
        elif Deliverable.query.filter_by(name=request.form['deliverable_name'], ITP_id=project_ITP.id).first() == None:
            location_id = Location.query.filter_by(name=request.form['deliverable_location']).first()
            secondary_location_id = Secondary_location.query.filter_by(name=request.form['secondary_location']).first()
            deliverable_type = Deliverable_type.query.filter_by(name=request.form['deliverable_type']).first()
            deliverable = Deliverable(request.form['deliverable_name'], request.form['deliverable_description'], deliverable_type.id, location_id.id, project_ITP.id)
            db.session.add(deliverable)
            if secondary_location_id != None:
                deliverable.secondary_location_id = secondary_location_id.id
            db.session.commit()
            deliverable = Deliverable.query.filter_by(name=request.form['deliverable_name'], ITP_id=project_ITP.id).first()
            ITCs = ITC.query.filter_by(deliverable_type_id=deliverable_type.id).all()
            deliverable.start_date = datetime.datetime.now()
            for itc in ITCs:
                deliver_itc = Deliverable_ITC_map(deliverable.id, itc.id)
                db.session.add(deliver_itc)
                db.session.commit()

            deliver_itcs = Deliverable_ITC_map.query.filter_by(deliverable_id=deliverable.id).all()
            for deliver_itc in deliver_itcs:
                ITC_checks = ITC_check_map.query.filter_by(ITC_id=deliver_itc.ITC_id).all()
                for ITC_check in ITC_checks:
                    deliver_check = Deliverable_check_map(deliver_itc.id, ITC_check.id)
                    db.session.add(deliver_check)
                    db.session.commit()

            return redirect(url_for('site_project_ITP_deliverable_list', siteid=site.id, projectid=project.id, ITPid= project_ITP.id))
        else:
            error = "Deliverable " + request.form['deliverable_name'] + " already exists!"
            return render_template('deliverable/ITP_deliverable_new.html', site=site, project=project, ITP=project_ITP, types=deliverable_types, locations=locations, error=error, users=users)
    else:
        return render_template('deliverable/ITP_deliverable_new.html', site=site, project=project, ITP=project_ITP, types=deliverable_types, locations=locations, users=users)

@app.route('/_get_secondary', methods=['POST','GET'])
def get_secondary_location():
    secondary_locations = Secondary_location.query

    location = request.args.get('location')
    print(location)
    if location == "":
        secondary_locations = secondary_locations
    else:
        location = Location.query.filter_by(name=location).first()
        secondary_locations = secondary_locations.filter(Secondary_location.location_id.contains(location.id)).all()

    return jsonify({"results":render_template('secondary_location_template.html', secondary_locations=secondary_locations)})


#Route for editing a current deliverable
@app.route('/site/<siteid>/projects/<projectid>/ITP/<ITPid>/deliverable/<deliverableid>/edit', methods=['POST','GET'])
def site_project_ITP_deliverable_edit(siteid, projectid, ITPid, deliverableid):
    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid, site_id=site.id).first()
    project_ITP = ITP.query.filter_by(id=ITPid, project_id=project.id).first()
    deliverable = Deliverable.query.filter_by(id=deliverableid, ITP_id=project_ITP.id).first()
    deliverable_types = Deliverable_type.query.all()
    locations = Location.query.filter_by(site_id=site.id).all()
    users = User.query.all()
    secondary_locations = Secondary_location.query.filter(deliverable.id == deliverable.id).all()

    referrer = request.referrer.split('/')[-1].strip('?')

    if request.method == 'POST':
        if Deliverable.query.filter_by(name=request.form['deliverable_name'], ITP_id=project_ITP.id).first() == None or Deliverable.query.filter_by(name=request.form['deliverable_name'], ITP_id=project_ITP.id).first().id == deliverable.id:
            deliverable_name = request.form['deliverable_name']
            if (deliverable_name != "" and deliverable_name != deliverable.name):
                deliverable.name = deliverable_name
            deliverable_number = request.form['deliverable_number']
            if (deliverable_number != "" and deliverable_number != deliverable.component_number):
                deliverable.component_number = deliverable_number
            description = request.form['deliverable_description']
            if (description != "" and description != deliverable.description):
                deliverable.description = description
            start_date = request.form['start_date']
            if (start_date != "" and start_date != deliverable.start_date):
                deliverable.start_date = start_date
            assigned_to = request.form['assigned_to']
            if (assigned_to != "" and assigned_to != deliverable.assigned_to):
                deliverable.assigned_to = assigned_to
            secondary_location_id = Secondary_location.query.filter_by(name=request.form['secondary_location']).first()
            if secondary_location_id != None:
                deliverable.secondary_location_id = secondary_location_id.id
            db.session.commit()
            if referrer == 'deliverable':
                return redirect(url_for('site_project_ITP_deliverable_list', siteid=site.id, projectid=project.id, ITPid=project_ITP.id))
            else:
                return redirect(url_for('site_project_ITP_deliverable', siteid=site.id, projectid=project.id, ITPid=project_ITP.id, deliverableid=deliverable.id))
        else:
            error = "Deliverable " + request.form['deliverable_name'] + " already exists!"
            return render_template('deliverable/ITP_deliverable_edit.html', site=site, project=project, ITP=project_ITP, types=deliverable_types,
                        secondary_locations=secondary_locations, locations=locations, deliverable=deliverable, users=users, error=error, referrer=referrer)
    else:
        return render_template('deliverable/ITP_deliverable_edit.html', site=site, project=project, ITP=project_ITP, types=deliverable_types,
                        secondary_locations=secondary_locations, locations=locations, deliverable=deliverable, users=users, referrer=referrer)

#Route for deleting a current deliverable
@app.route('/site/<siteid>/projects/<projectid>/ITP/<ITPid>/deliverable/<deliverableid>/delete', methods=['POST','GET'])
def site_project_ITP_deliverable_delete(siteid, projectid, ITPid, deliverableid):
    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid, site_id=site.id).first()
    project_ITP = ITP.query.filter_by(id=ITPid, project_id=project.id).first()
    deliverable = Deliverable.query.filter_by(id=deliverableid, ITP_id=project_ITP.id).first()

    if request.method == 'POST':
        db.session.delete(deliverable)
        db.session.commit()
        return redirect(url_for('site_project_ITP_deliverable_list', siteid=site.id, projectid=project.id, ITPid=project_ITP.id))
    else:
        return render_template('deliverable/ITP_deliverable_delete.html', site=site, project=project, ITP=project_ITP, deliverable=deliverable)


############################ ITC navigation controllers ########################


#Route for ITC list for given a deliverable
@app.route('/site/<siteid>/projects/<projectid>/ITP/<ITPid>/deliverable/<deliverableid>/ITC')
def site_project_ITP_deliverable_ITC_list(siteid, projectid, ITPid, deliverableid):
    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid, site_id=site.id).first()
    project_ITP = ITP.query.filter_by(project_id=project.id, id=ITPid).first()
    deliverable = Deliverable.query.filter_by(ITP_id=project_ITP.id, id=deliverableid).first()
    ITP_ITCs = Deliverable_ITC_map.query.filter_by(deliverable_id=deliverable.id).all()
    ITC_groups = ITC_group.query.all()

    groups = []

    for ITC in ITP_ITCs:
        total = 0
        completed = 0
        checks = Deliverable_check_map.query.filter_by(deliverable_ITC_map_id=ITC.id).all()
        for check in checks:
            total += 1
            if check.is_done == True:
                completed += 1
        if total != 0:
            percent = (completed/total)*100
        else:
            percent = 0
        ITC.percentage_complete = percent

        if percent == 100:
            ITC.status = "Completed"
        elif (percent != 100 and ITC.status == "Completed"):
            ITC.status = "In Progress"
        db.session.commit()

        if ITC.ITC.group in ITC_groups:
            groups.append(ITC.ITC.group)

    return render_template('specific_ITC/ITC_list.html', site=site, project=project, ITP=project_ITP, deliverable=deliverable, ITCs=ITP_ITCs, groups=groups)

#Route for editing a current ITC
@app.route('/site/<siteid>/projects/<projectid>/ITP/<ITPid>/deliverable/<deliverableid>/ITC/<ITCid>/edit', methods=['POST','GET'])
def site_project_ITP_deliverable_ITC_edit(siteid, projectid, ITPid, deliverableid, ITCid):
    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid, site_id=site.id).first()
    project_ITP = ITP.query.filter_by(project_id=project.id, id=ITPid).first()
    deliverable = Deliverable.query.filter_by(ITP_id=project_ITP.id, id=deliverableid).first()
    ITP_ITC = Deliverable_ITC_map.query.filter_by(id=ITCid).first()
    deliverable_types = Deliverable_type.query.all()

    if request.method == 'POST':
        ITC_name = request.form['ITC_name']
        if (ITC_name != "" and ITC_name != ITP_ITC.name):
            ITP_ITC.name = ITC_name
        ITC_status = request.form['ITC_status']
        if (ITC_status != "" and ITC_status != ITP_ITC.status):
            ITP_ITC.status = ITC_status
        ITC_comment = request.form['ITC_comment']
        if (ITC_comment != "" and ITC_comment != ITP_ITC.comment):
            ITP_ITC.comment = ITC_comment
        db.session.commit()
        return redirect(url_for('site_project_ITP_deliverable_ITC_list', siteid=site.id, projectid=project.id, ITPid=project_ITP.id, deliverableid=deliverable.id))
    else:
        return render_template('specific_ITC/ITC_edit.html', site=site, project=project, ITP=project_ITP, deliverable=deliverable, ITC=ITP_ITC)

#Route for deleting a current ITC
@app.route('/site/<siteid>/projects/<projectid>/ITP/<ITPid>/deliverable/<deliverableid>/ITC/<ITCid>/delete', methods=['POST','GET'])
def site_project_ITP_deliverable_ITC_delete(siteid, projectid, ITPid, deliverableid, ITCid):
    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid).first()
    project_ITP = ITP.query.filter_by(project_id=project.id, id=ITPid).first()
    deliverable = Deliverable.query.filter_by(ITP_id=project_ITP.id, id=deliverableid).first()
    ITP_ITC = Deliverable_ITC_map.query.filter_by(id=ITCid).first()

    if request.method == 'POST':
        db.session.delete(ITP_ITC)
        db.session.commit()
        return redirect(url_for('site_project_ITP_deliverable_ITC_list', siteid=site.id, projectid=project.id, ITPid=project_ITP.id, deliverableid=deliverable.id))
    else:
        return render_template('specific_ITC/ITC_delete.html', site=site, project=project, ITP=project_ITP, deliverable=deliverable, ITC=ITP_ITC)

#Route for adding a check
@app.route('/site/<siteid>/projects/<projectid>/ITP/<ITPid>/deliverable/<deliverableid>/ITC/add', methods=['POST','GET'])
def site_project_ITP_deliverable_ITC_add(siteid, projectid, ITPid, deliverableid):
    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid, site_id=site.id).first()
    project_ITP = ITP.query.filter_by(id=ITPid, project_id=project.id).first()
    deliverable = Deliverable.query.filter_by(id=deliverableid, ITP_id=project_ITP.id).first()
    ITCs = ITC.query.all()

    if request.method == 'POST':
        itc = ITC.query.filter_by(id=request.form['ITC']).first()
        deliver_itc = Deliverable_ITC_map(deliverable.id, itc.id)
        db.session.add(deliver_itc)
        db.session.commit()
        return redirect(url_for('site_project_ITP_deliverable_ITC_list', siteid=site.id, projectid=project.id, deliverableid=deliverable.id, ITPid=project_ITP.id))
    else:
        return render_template('ITC_add.html', site=site, project=project, ITP=project_ITP, deliverable=deliverable, ITCs=ITCs)

#Route for updating check completion
@app.route('/site/<siteid>/projects/<projectid>/ITP/<ITPid>/deliverable/<deliverableid>/ITC/<ITCid>/check/change', methods=['POST'])
def site_project_ITP_deliverable_ITC_change(siteid, projectid, ITPid, deliverableid, ITCid):
    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid, site_id=site.id).first()
    project_ITP = ITP.query.filter_by(id=ITPid, project_id=project.id).first()
    deliverable = Deliverable.query.filter_by(id=deliverableid, ITP_id=project_ITP.id).first()
    deliver_ITC = Deliverable_ITC_map.query.filter_by(deliverable_id=deliverable.id, id=ITCid).first()
    user = current_user
    checked = request.form.getlist('check_box')
    completed_checks = Deliverable_check_map.query.filter_by(is_done=True, deliverable_ITC_map_id=deliver_ITC.id).all()
    checks = Deliverable_check_map.query.filter_by(deliverable_ITC_map_id=deliver_ITC.id).all()

    print("getting comments")
    print(request.form['deliverable_comments'] == "")
    comments = request.form['deliverable_comments']

    if comments != deliver_ITC.comments:
        deliver_ITC.comments = comments
        db.session.commit()

    #Change form status to done
    for checkid in checked:
        check = Deliverable_check_map.query.filter_by(id=checkid).first()
        print(check.ITC_check.check)
        if check.is_done != True:
            check.completion_datetime = datetime.datetime.now()
            check.completion_by_user_id = User.query.filter_by(id=user.id).first().id
            check.is_done = True
            check.status = "Completed"
            db.session.commit()

    #Change unticked status to false
    for completed_check in completed_checks:
        if str(completed_check.id) not in checked:
            completed_check.completion_datetime = None
            completed_check.completion_by_user_id = None
            completed_check.is_done = False
            completed_check.status = "In Progress"
            db.session.commit()

    return redirect(url_for('ITC_testing', siteid=site.id, projectid=project.id, ITPid=project_ITP.id, deliverableid=deliverable.id, ITCid=ITCid))

################################################################################
###################### Specific ITC check list items ###########################
################################################################################

#Dynamically generate checks based on current ITCs
@app.route('/site/<siteid>/projects/<projectid>/ITP/<ITPid>/deliverable/<deliverableid>/ITC/<ITCid>/starttest')
def start_ITC_testing(siteid, projectid, ITPid, deliverableid, ITCid):
    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid, site_id=site.id).first()
    project_ITP = ITP.query.filter_by(id=ITPid, project_id=project.id).first()
    deliverable = Deliverable.query.filter_by(id=deliverableid, ITP_id=project_ITP.id).first()
    deliver_ITC = Deliverable_ITC_map.query.filter_by(deliverable_id=deliverable.id, id=ITCid).first()
    ITC_checks = ITC_check_map.query.filter_by(ITC_id=deliver_ITC.ITC_id).all()
    deliver_checks = Deliverable_check_map.query.filter_by(deliverable_ITC_map_id=deliver_ITC.id).all()

    for check in deliver_checks:
        db.session.delete(check)
        db.session.commit()

    for ITC_check in ITC_checks:
        deliver_check = Deliverable_check_map(deliver_ITC.id, ITC_check.id)
        db.session.add(deliver_check)
        db.session.commit()

    deliver_ITC.status = "In Progress"
    db.session.commit()

    return redirect(url_for('ITC_testing', siteid=site.id, projectid=project.id, ITPid=project_ITP.id, deliverableid=deliverable.id, ITCid=ITCid))

#Route for looking at all current checks for an ITC
@app.route('/site/<siteid>/projects/<projectid>/ITP/<ITPid>/deliverable/<deliverableid>/ITC/<ITCid>/checks')
def ITC_testing(siteid, projectid, ITPid, deliverableid, ITCid):
    #When a generic_ITC is deleted the link will remain until the page is refreshed therefore we add this in to "refresh" the page
    try:
        site = Site.query.filter_by(id=siteid).first()
        project = Project.query.filter_by(id=projectid, site_id=site.id).first()
        project_ITP = ITP.query.filter_by(id=ITPid, project_id=project.id).first()
        deliverable = Deliverable.query.filter_by(id=deliverableid, ITP_id=project_ITP.id).first()
        deliver_ITC = Deliverable_ITC_map.query.filter_by(deliverable_id=deliverable.id, id=ITCid).first()
        deliverable_checks = Deliverable_check_map.query.filter_by(deliverable_ITC_map_id=deliver_ITC.id).all()
    except AttributeError:
        return redirect(url_for('site_project_ITP_deliverable_ITC_list', siteid=site.id, projectid=project.id, ITPid=project_ITP.id, deliverableid=deliverable.id))

    total = 0
    completed = 0
    for check in deliverable_checks:
        total += 1
        if check.is_done == True:
            completed += 1
    if total == 0:
        percentage_complete = 0
    else:
        percentage_complete = (completed/total)*100

    deliver_ITC.percentage_complete = percentage_complete

    if percentage_complete == 100:
        deliver_ITC.status = "Completed"
    elif (percentage_complete > 0 and percentage_complete < 100):
        deliver_ITC.status = "In Progress"
    db.session.commit()

    print(deliver_ITC.comments)

    return render_template('specific_ITC/ITC.html', site=site, project=project, ITP=project_ITP, deliverable=deliverable, ITC=deliver_ITC, checks=deliverable_checks, ITCid=ITCid, percentage_complete=percentage_complete)

#Route for editing a check
@app.route('/site/<siteid>/projects/<projectid>/ITP/<ITPid>/deliverable/<deliverableid>/ITC/<ITCid>/checks/<checkid>/edit', methods=['POST','GET'])
def site_project_ITP_deliverable_ITC_check_edit(siteid, projectid, ITPid, deliverableid, ITCid, checkid):
    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid, site_id=site.id).first()
    project_ITP = ITP.query.filter_by(id=ITPid, project_id=project.id).first()
    deliverable = Deliverable.query.filter_by(id=deliverableid, ITP_id=project_ITP.id).first()
    ITP_ITC = Deliverable_ITC_map.query.filter_by(id=ITCid).first()
    check = Deliverable_check_map.query.filter_by(id=checkid).first()

    if request.method == 'POST':
        comments = request.form['check_comment']
        if (comments != "" and comments == check.comments):
            check.comments = comments
        # check_generic = request.form['check_generic']
        # if (check_generic != "" and check_generic != check.check_generic):
        #     check.check_generic = check_generic
        check_status = request.form['check_status']
        if (check_status != "" and check_status != check.status and check.is_done != True):
            check.status = check_status
            if (request.form['check_status'] == "Completed"):
                check.is_done = True
        db.session.commit()
        return redirect(url_for('ITC_testing', siteid=site.id, projectid=project.id, deliverableid=deliverable.id, ITPid=project_ITP.id, ITCid=ITP_ITC.id))
    else:
        return render_template('specific_ITC/ITC_check_edit.html', site=site, project=project, ITP=project_ITP, deliverable=deliverable, ITC=ITP_ITC, check=check)

#Route for deleting a check
@app.route('/site/<siteid>/projects/<projectid>/ITP/<ITPid>/deliverable/<deliverableid>/ITC/<ITCid>/checks/<checkid>/delete', methods=['POST','GET'])
def site_project_ITP_deliverable_ITC_check_delete(siteid, projectid, ITPid, deliverableid, ITCid, checkid):
    site = Site.query.filter_by(id=siteid).first()
    project = Project.query.filter_by(id=projectid, site_id=site.id).first()
    project_ITP = ITP.query.filter_by(id=ITPid, project_id=project.id).first()
    deliverable = Deliverable.query.filter_by(id=deliverableid, ITP_id=project_ITP.id).first()
    ITP_ITC = Deliverable_ITC_map.query.filter_by(id=ITCid).first()
    check = Deliverable_check_map.query.filter_by(id=checkid).first()

    if request.method == 'POST':
        db.session.delete(check)
        db.session.commit()
        return redirect(url_for('ITC_testing', siteid=site.id, projectid=project.id, deliverableid=deliverable.id, ITPid=project_ITP.id, ITCid=ITP_ITC.id))
    else:
        return render_template('specific_ITC/ITC_check_delete.html', site=site, project=project, ITP=project_ITP, deliverable=deliverable, ITC=ITP_ITC, check=check)


################################################################################
############################ Generic ITC creation ##############################
################################################################################

#Route for Generic Component Creation and Editing
@app.route('/generic')
def general_items_list():
    return render_template('general_items_list.html')

#Route to view a generic ITC
@app.route('/generic/ITC/<ITCid>')
def ITC_general(ITCid):
    general_ITC = ITC.query.filter_by(id=ITCid).first()
    checks = ITC_check_map.query.filter_by(ITC_id=general_ITC.id).all()

    return render_template('generic_ITC/ITC_check_general.html', ITC=general_ITC, checks=checks)

#Route for new ITC
@app.route('/generic/ITC/new', methods=['POST','GET'])
def ITC_general_new():
    deliverable_types = Deliverable_type.query.all()
    ITC_groups = ITC_group.query.all()

    redirect_url = None
    if request.referrer.split('/')[-3].strip('?') == 'deliverable':
        redirect_url = request.referrer

    if request.method == 'POST':
        if request.form['ITC_name'] == "" or request.form['ITC_name'] == None:
            error = "ITC name missing!"
            return render_template('generic_ITC/ITC_new.html', deliverables=deliverable_types, ITC_groups=ITC_groups, error=error)
        if ITC.query.filter_by(name=request.form['ITC_name']).first() == None:
            deliverable_type = Deliverable_type.query.filter_by(id=request.form['deliverable_type']).first()
            new_ITC = ITC(request.form['ITC_name'], deliverable_type.id)
            db.session.add(new_ITC)
            new_ITC.description = request.form['ITC_description']
            group = ITC_group.query.filter_by(id=request.form['ITC_general_group']).first()
            if (group != ""):
                new_ITC.group = group
            db.session.commit()
            if request.args.get('redirect_url') == None:
                return redirect(url_for('ITC_general_list'))
            else:
                return redirect(redirect_url)
        else:
            error = "ITC " + request.form['ITC_name'] + " already exists!"
            return render_template('generic_ITC/ITC_new.html', deliverables=deliverable_types, ITC_groups=ITC_groups, error=error, redirect_url=redirect_url)
    else:
        return render_template('generic_ITC/ITC_new.html', deliverables=deliverable_types, ITC_groups=ITC_groups, redirect_url=redirect_url)

#Route for viewing all general ITC
@app.route('/generic/ITC', methods=['POST','GET'])
def ITC_general_list():

    PER_PAGE = 5
    if request.args.get('page') == None:
        page = 1
    else:
        page = int(request.args.get('page'))

    deliverable_types = Deliverable_type.query.all()
    ITCs = ITC.query.order_by(ITC.name.desc()).paginate(page, PER_PAGE, False)

    return render_template('generic_ITC/ITC_general.html', ITCs=ITCs, deliverable_types=deliverable_types)

@app.route('/_filter_generic_ITCs', methods=['POST','GET'])
def ITC_generic_filter():

    PER_PAGE = 5
    if request.args.get('page') == None:
        page = 1
    else:
        page = int(request.args.get('page'))

    ITCs = ITC.query

    name = request.args.get('name')
    if name == "":
        ITCs = ITCs
    else:
        ITCs = ITCs.filter(ITC.name.contains(name))

    deliverable_type = request.args.get('deliverable_type')
    if deliverable_type == "all":
        ITCs = ITCs
    else:
        deliverable_type = Deliverable_type.query.filter_by(id=deliverable_type).first()
        ITCs = ITCs.filter_by(deliverable_type_id=deliverable_type.id)

    ITCs = ITCs.order_by(ITC.name.desc()).paginate(page, PER_PAGE, False)

    print(ITCs.items)

    return jsonify({"results":render_template('generic_ITC/ITC_general_table.html', ITCs=ITCs),
                    "page": page})

#Delete generic check
@app.route('/generic/ITC/<ITCid>/delete', methods=['POST','GET'])
def ITC_general_delete(ITCid):
    ITC_generic = ITC.query.filter_by(id=ITCid).first()
    ITC_specifics = Deliverable_ITC_map.query.filter_by(ITC_id=ITC_generic.id).all()

    if request.method == 'POST':
        db.session.delete(ITC_generic)
        for ITC_specific in ITC_specifics:
            db.session.delete(ITC_specific)
        db.session.commit()
        return redirect(url_for('ITC_general_list'))
    else:
        return render_template('generic_ITC/ITC_general_delete.html', ITC=ITC_generic)

#Edit generic check
@app.route('/generic/ITC/<ITCid>/edit', methods=['POST','GET'])
def ITC_general_edit(ITCid):
    ITC_generic = ITC.query.filter_by(id=ITCid).first()
    ITC_groups = ITC_group.query.all()

    if request.method == 'POST':
        name = request.form['ITC_general_name']
        if (name != "" and name != ITC_generic.name):
            ITC_generic.name = name
        # deliverable_type_id = Deliverable_type.query.filter_by(name=request.form['ITC_general_deliverable_type']).first()
        # if (deliverable_type_id != ITC_generic.deliverable_type_id):
        #     ITC_generic.deliverable_type_id = deliverable_type_id
        group = ITC_group.query.filter_by(id=request.form['ITC_general_group']).first()
        if (group != "" and group != ITC_generic.group):
            ITC_generic.group = group
        db.session.commit()
        return redirect(url_for('ITC_general_list'))
    else:
        return render_template('generic_ITC/ITC_general_edit.html', ITC=ITC_generic, ITC_groups=ITC_groups)


################ Check creation and editing for generic ITC ####################

#Route for new check
@app.route('/generic/ITC/<ITCid>/check/new', methods=['POST','GET'])
def ITC_check_general_new(ITCid):
    ITP_ITC = ITC.query.filter_by(id=ITCid).first()
    checks_generic = Check_generic.query.all()

    if request.method == 'POST':
        if request.form['check_generic'] != "":
            check_generic = Check_generic.query.filter_by(id=request.form['check_generic']).first()
        check = ITC_check_map(check_generic.id, ITP_ITC.id)
        check.is_done = False
        db.session.add(check)
        db.session.commit()
        return redirect(url_for('ITC_general', ITCid=ITP_ITC.id))
    else:
        return render_template('generic_ITC_check/ITC_check_new.html', ITC=ITP_ITC, checks=checks_generic)

#Route for editing a generic check
@app.route('/generic/ITC/<ITCid>/check/<checkid>/edit', methods=['POST', 'GET'])
def ITC_check_general_edit(ITCid, checkid):
    ITP_ITC = ITC.query.filter_by(id=ITCid).first()
    check = ITC_check_map.query.filter_by(id=checkid).first()

    if request.method == 'POST':
        description = request.form['check_description']
        if (description != "" and description != check.check.check_description):
            #see if the check already exists
            old_check = Check_generic.query.filter_by(check_description=description).first()
            if old_check == None:
                new_check = Check_generic(description)
                db.session.add(new_check)
                db.session.commit()
                check.check_generic = new_check.id
                db.session.commit()
            else:
                check.check_generic = old_check.id
                db.session.commit()
        return redirect(url_for('ITC_general', ITCid=ITP_ITC.id))
    else:
        return render_template('generic_ITC_check/generic_ITC_check_edit.html', ITC=ITP_ITC, check=check)

#Route for deleting a generic check for an ITC template
@app.route('/generic/ITC/<ITCid>/check/<checkid>/delete', methods=['POST', 'GET'])
def ITC_check_general_delete(ITCid, checkid):
    ITP_ITC = ITC.query.filter_by(id=ITCid).first()
    check = ITC_check_map.query.filter_by(id=checkid).first()
    specific_checks = Deliverable_check_map.query.filter_by(ITC_check_id=check.id).all()
    print(specific_checks)

    if request.method == 'POST':
        db.session.delete(check)
        for specific_check in specific_checks:
            db.session.delete(specific_check)
        db.session.commit()
        return redirect(url_for('ITC_general', ITCid=ITP_ITC.id))
    else:
        return render_template('generic_ITC_check/generic_ITC_check_delete.html', ITC=ITP_ITC, check=check)

##################### Generic check creation and editing #######################

#Route for new generic check
@app.route('/generic/check/new', methods=['POST', 'GET'])
def generic_check_new():
    if request.method == "POST":
        if request.form['check_description'] == "" or request.form['check_description'] == None:
            error = "Check description missing"
            return render_template('generic_check/generic_check_new.html', error=error)
        if Check_generic.query.filter_by(check_description=request.form['check_description']).first() == None:
            check = Check_generic(request.form['check_description'])
            db.session.add(check)
            db.session.commit()
            return redirect(url_for('generic_check_list'))
        else:
            error = "Check " + request.form['check_description'] + " already exists!"
            return render_template('generic_check/generic_check_new.html', error=error)
    else:
        return render_template('generic_check/generic_check_new.html')

#Route for viewing all generic checks
@app.route('/generic/check')
def generic_check_list():

    PER_PAGE = 5
    if request.args.get('page') == None:
        page = 1
    else:
        print(request.args.get('page'))
        page = int(request.args.get('page'))

    checks = Check_generic.query.order_by(Check_generic.id.asc()).paginate(page, PER_PAGE, False)

    return render_template('generic_check/generic_check_list.html', checks=checks)

#Route for paginating checks
@app.route('/_filter_checks', methods=['GET', 'POST'])
def filter_checks():
    print(request.args.get('description', None))
    print(request.args.get('page', None))

    PER_PAGE = 5
    if request.args.get('page') == None:
        page = 1
    else:
        page = int(request.args.get('page'))

    description = request.args.get('description', None)
    if description == None:
        checks = Check_generic.query
    else:
        checks = Check_generic.query.filter(Check_generic.check_description.contains(description))

    checks = checks.order_by(Check_generic.id.asc()).paginate(page, PER_PAGE, False)
    previous_page = checks.has_prev
    next_page = checks.has_next
    pages = checks.pages

    return jsonify({"results":render_template('generic_check/generic_check_table_template.html', checks=checks),
                    "page": page,
                    "next": next_page,
                    "previous": previous_page,
                    "pages": pages})


#Route for editing generic checks
@app.route('/generic/check/<checkid>/edit', methods=['POST', 'GET'])
def generic_check_edit(checkid):
    check = Check_generic.query.filter_by(id=checkid).first()

    if request.method == "POST":
        check_description = request.form['check_description']
        if (check_description != "" and check_description != check.check_description):
            #see if check already exists, if not create a new check
            old_check = Check_generic.query.filter_by(check_description=check_description).first()
            if old_check == None:
                new_check = Check_generic(check_description)
                db.session.add(new_check)
                db.session.commit()
            else:
                flash('Check already exists')
        return redirect(url_for('generic_check_list'))
    else:
        return render_template('generic_check/generic_check_edit.html', check=check)

#Route for deleting generic check
@app.route('/generic/check/<checkid>/delete', methods=['POST', 'GET'])
def generic_check_delete(checkid):
    check = Check_generic.query.filter_by(id=checkid).first()
    ITC_checks = ITC_check_map.query.filter_by(check_generic=check.id).all()
    print(ITC_checks)

    if request.method == "POST":
        db.session.delete(check)
        for ITC_check in ITC_checks:
            db.session.delete(ITC_check)
        db.session.commit()
        return redirect(url_for('generic_check_list'))
    else:
        return render_template('generic_check/generic_check_delete.html', check=check)





#
