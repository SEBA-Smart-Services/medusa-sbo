from app import app, db, registry, user_datastore, security
from app.models import Asset, Site, AssetPoint, AssetType, Algorithm, FunctionalDescriptor, PointType, Result, LoggedEntity, LogTimeValue, IssueHistory, IssueHistoryTimestamp, InbuildingsConfig, Email
from app.models import Alarm
from app.models.ITP import Project, ITP, Deliverable, Location, Deliverable_type, ITC, ITC_check_map, Check_generic, Deliverable_ITC_map, Deliverable_check_map
from app.models.users import User
from app.forms import SiteConfigForm, AddSiteForm
from flask import json, request, render_template, url_for, redirect, jsonify, flash, make_response
from flask_user import current_user
from statistics import mean
import datetime, time
from flask_wtf import Form
from wtforms import TextField, PasswordField, validators
from werkzeug.security import check_password_hash
from flask_security.utils import encrypt_password

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
    sites = current_user.sites
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
    # only send results[0:5], to display the top 5 priority issues in the list
    return render_template('dashboard.html', results=results[0:5], num_results=num_results, top_priority=top_priority, avg_health=avg_health, low_health_assets=low_health_assets, alarmcount=nalarms)

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
    site = Site.query.filter_by(name=sitename).one()
    # only show the top 5 issues by priority in the list
    results = site.get_unresolved_by_priority()[0:4]
    num_results = len(site.get_unresolved())

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

    return render_template(
        'dashboard.html',
        results=results,
        num_results=num_results,
        top_priority=top_priority,
        avg_health=avg_health,
        low_health_assets=low_health_assets,
        site=site,
        alarmcount=nalarms,

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

# return table of alarms
@app.route('/site/<sitename>/alarms')
def return_alarms(sitename):

    site = Site.query.filter_by(name=sitename).one()

    message = "squirrel"
    alarm_names = []
    nalarms = "FAIL"
    # get database session for this site
    try:
        alarms = db.session.query(Alarm).limit(20).all()
        alarm_names = [alarm.AlarmText for alarm in alarms]
        nalarms = get_alarms_per_week(db.session, nweeks=8)

    except Exception as e:
        message = "Site not connected." + str(site.name) + '\n' + str(e)


    return render_template(
        'alarms.html',
        site=site,
        message=message,
        alarms=alarm_names,
        nalarms=nalarms,
	    rows=nalarms,

    )


####################### View all projects for user #############################

@app.route('/projects')
def all_projects():
    all_projects = []
    for site in current_user.sites:
        print(site.id)
        projects = Project.query.filter_by(site_id=site.id).all()
        all_projects = all_projects + projects

    print(all_projects)

    return render_template('projects.html', projects=all_projects)


################################################################################
########################## controllers for ITP routes###########################
################################################################################

##################### Project navigation controllers ###########################

#Route for all Projects for a given site
@app.route('/site/<sitename>/projects')
def site_projects_list(sitename):
    site = Site.query.filter_by(name=sitename).first()
    site_projects = Project.query.filter_by(site_id = site.id).all()

    projects = []
    for i in site_projects:
        projects.append(i)

    return render_template('project/site_projects_list.html', site=site, projects=projects)

#Route for individual Project for a given Site
@app.route('/site/<sitename>/projects/<projectname>')
def site_project(sitename, projectname):
    site = Site.query.filter_by(name=sitename).first()
    project = Project.query.filter_by(name=projectname).first()
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
            totals = [total_ITC, ITC_complete, ITC_in_progress, ITC_not_applicable, ITC_not_started]
        else:
            percents = [0,0,0,0]
            totals = [0,0,0,0]
    else:
        percents = [0,0,0,0]
        totals = [0,0,0,0]

    return render_template('project/site_project.html', site=site, project=project, ITP=project_ITP, percents=percents, totals=totals)

#Route for creating a new Project for a given Site
#add in __init__ to schema so the variables can just be passed to the new Project
#including site_id
@app.route('/site/<sitename>/projects/new', methods=['POST','GET'])
def site_project_new(sitename):
    site = Site.query.filter_by(name=sitename).first()
    users = User.query.all()
    print(users)

    if request.method == 'POST':
        new_site = Project(request.form['project_name'], request.form['job_number'], request.form['project_description'], site.id)
        new_site.assigned_to = request.form['assigned_to']
        db.session.add(new_site)
        db.session.commit()
        return redirect(url_for('site_projects_list', sitename=site))
    else:
        return render_template('project/site_project_new.html', site=site, users=users)

#Route for editing a current project
@app.route('/site/<sitename>/projects/<projectname>/edit', methods=['POST','GET'])
def site_project_edit(sitename, projectname):
    site = Site.query.filter_by(name=sitename).first()
    project = Project.query.filter_by(name=projectname).first()
    users = User.query.all()

    if request.method == 'POST':
        project_name = request.form['project_name']
        if (project_name != "" and project_name != project.name):
            project.name = project_name
        description = request.form['project_description']
        if (description != "" and request.form['project_description'] != project.description):
            project.description = request.form['project_description']
        job_number = request.form['job_number']
        if (job_number != "" and request.form['job_number'] != project.job_number):
            project.job_number = request.form['job_number']
        start_date = request.form['start_date']
        if (start_date != "" and request.form['start_date'] != project.start_date):
            project.start_date = request.form['start_date']
        assigned_to = request.form['assigned_to']
        if (assigned_to != "" and request.form['assigned_to'] != project.assigned_to):
            project.assigned_to = request.form['assigned_to']
        db.session.commit()
        return redirect(url_for('site_projects_list', sitename=site))
    else:
        return render_template('project/site_project_edit.html', site=site, project=project, users=users)

#Route for deleting a current project
@app.route('/site/<sitename>/projects/<projectname>/delete', methods=['POST','GET'])
def site_project_delete(sitename, projectname):
    site = Site.query.filter_by(name=sitename).first()
    project = Project.query.filter_by(name=projectname).first()

    if request.method == 'POST':
        db.session.delete(project)
        db.session.commit()
        return redirect(url_for('site_projects_list', sitename=site))
    else:
        return render_template('project/site_project_delete.html', site=site, project=project)

############################ ITP navigation controllers ########################


#Route for details on ITP for project
@app.route('/site/<sitename>/projects/<projectname>/ITP/<ITPname>')
def site_project_ITP(sitename, projectname, ITPname):
    site = Site.query.filter_by(name=sitename).first()
    project = Project.query.filter_by(name=projectname).first()
    project_ITP = ITP.query.filter_by(name=ITPname).first()
    deliverables = Deliverable.query.filter_by(ITP_id=project_ITP.id).all()

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
    for deliverable in deliverables:
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

    if deliverable.percentage_complete > 0 and deliverable.percentage_complete < 100:
        deliverable.status = "In Progress"
    elif deliverable.percentage_complete == 100:
        delvierable.status = "Completed"
    else:
        deliverable.status = "Not Started"

    completion_date = "-"
    if percents[0] == 100:
        completion_date = checks[0].completion_datetime
        for check in checks:
            if check.completion_datetime < completion_date:
                completion_date = check.completion_datetime

    return render_template('ITP/project_ITP.html', site=site, project=project, ITP=project_ITP, deliverables=deliverables, completion_date=completion_date, ITCs=all_ITCs, percents=percents, totals=totals)

#Route for creating new ITP
@app.route('/site/<sitename>/projects/<projectname>/ITP/new', methods=['POST','GET'])
def site_project_ITP_new(sitename, projectname):
    site = Site.query.filter_by(name=sitename).first()
    project = Project.query.filter_by(name=projectname).first()

    if request.method == 'POST':
        new_ITP = ITP(request.form['ITP_name'], project.id, request.form['ITP_status'])
        db.session.add(new_ITP)
        db.session.commit()
        return redirect(url_for('site_project_ITP', sitename=site, projectname=project.name, ITPname=new_ITP))
    else:
        return render_template('ITP/project_ITP_new.html', site=site, project=project)

#Route for editing a current ITP
@app.route('/site/<sitename>/projects/<projectname>/ITP/<ITPname>/edit', methods=['POST','GET'])
def site_project_ITP_edit(sitename, projectname, ITPname):
    site = Site.query.filter_by(name=sitename).first()
    project = Project.query.filter_by(name=projectname).first()
    project_ITP = ITP.query.filter_by(name=ITPname).first()

    if request.method == 'POST':
        ITP_name = request.form['ITP_name']
        if (ITP_name != "" and ITP_name != project_ITP.name):
            project_ITP.name = ITP_name
        description = request.form['ITP_description']
        #if (description != "" and request.form['project_description'] == project.description):
        #    description = request.form['project_description']
        db.session.commit()
        return redirect(url_for('site_project_ITP', sitename=site, projectname=project.name, ITPname=project_ITP))
    else:
        return render_template('ITP/project_ITP_edit.html', site=site, project=project, ITP=project_ITP)

#Route for deleting a current ITP
@app.route('/site/<sitename>/projects/<projectname>/ITP/<ITPname>/delete', methods=['POST','GET'])
def site_project_ITP_delete(sitename, projectname, ITPname):
    site = Site.query.filter_by(name=sitename).first()
    project = Project.query.filter_by(name=projectname).first()
    project_ITP = ITP.query.filter_by(name=ITPname).first()

    if request.method == 'POST':
        db.session.delete(project_ITP)
        db.session.commit()
        return redirect(url_for('site_project', sitename=site, projectname=project.name))
    else:
        return render_template('ITP/project_ITP_delete.html', site=site, project=project, ITP=project_ITP)


###################### deliverable navigation controllers ######################
#maybe have section for new deliverable type and location creation?
#regex search for names (case insensitive) if not found add to list

#Route for deliverable list
@app.route('/site/<sitename>/projects/<projectname>/ITP/<ITPname>/deliverable')
def site_project_ITP_deliverable_list(sitename, projectname, ITPname):
    site = Site.query.filter_by(name=sitename).first()
    project = Project.query.filter_by(name=projectname).first()
    project_ITP = ITP.query.filter_by(name=ITPname).first()
    deliverables = Deliverable.query.filter_by(ITP_id=project_ITP.id).all()

    for deliverable in deliverables:
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
            delvierable.status = "Completed"
        else:
            deliverable.status = "Not Started"
        db.session.commit()

    return render_template('deliverable/ITP_deliverable_list.html', site=site, project=project, ITP=project_ITP, deliverables=deliverables)

#Route for deliverable
@app.route('/site/<sitename>/projects/<projectname>/ITP/<ITPname>/deliverable/<deliverablename>')
def site_project_ITP_deliverable(sitename, projectname, ITPname, deliverablename):
    site = Site.query.filter_by(name=sitename).first()
    project = Project.query.filter_by(name=projectname).first()
    project_ITP = ITP.query.filter_by(name=ITPname).first()
    deliverable_current = Deliverable.query.filter_by(name=deliverablename).first()
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
    print(deliverable_current.percentage_complete)
    print(deliverable_current.completion_date)
    if (deliverable_current.percentage_complete == 100 and deliverable_current.completion_date == None):
        print("now complete")
        deliverable_current.completion_date = datetime.datetime.now()
    else:
        print("Not complete")
        deliverable_current.completion_date = " "
    db.session.commit()

    return render_template('deliverable/ITP_deliverable.html', site=site, project=project, ITP=project_ITP, deliverable=deliverable_current, ITCs=ITP_ITCs, percents=percents, totals=totals)

#Route for new deliverable
@app.route('/site/<sitename>/projects/<projectname>/ITP/<ITPname>/deliverable/new', methods=['POST','GET'])
def site_project_ITP_deliverable_new(sitename, projectname, ITPname):
    site = Site.query.filter_by(name=sitename).first()
    project = Project.query.filter_by(name=projectname).first()
    project_ITP = ITP.query.filter_by(name=ITPname).first()
    deliverable_types = Deliverable_type.query.all()
    locations = Location.query.all()

    if request.method == 'POST':
        location_id = Location.query.filter_by(name=request.form['deliverable_location']).first()
        deliverable_type = Deliverable_type.query.filter_by(name=request.form['deliverable_type']).first()
        deliverable = Deliverable(request.form['deliverable_name'], deliverable_type.id, location_id.id, project_ITP.id)
        db.session.add(deliverable)
        db.session.commit()
        deliverable = Deliverable.query.filter_by(name=request.form['deliverable_name']).first()
        ITCs = ITC.query.filter_by(deliverable_type_id=deliverable_type.id).all()
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

        return redirect(url_for('site_project_ITP_deliverable_list', sitename=site, projectname=project.name, ITPname= project_ITP.name))
    else:
        return render_template('deliverable/ITP_deliverable_new.html', site=site, project=project, ITP=project_ITP, types=deliverable_types, locations=locations)

#Route for editing a current deliverable
@app.route('/site/<sitename>/projects/<projectname>/ITP/<ITPname>/deliverable/<deliverablename>/edit', methods=['POST','GET'])
def site_project_ITP_deliverable_edit(sitename, projectname, ITPname, deliverablename):
    site = Site.query.filter_by(name=sitename).first()
    project = Project.query.filter_by(name=projectname).first()
    project_ITP = ITP.query.filter_by(name=ITPname).first()
    deliverable = Deliverable.query.filter_by(name=deliverablename).first()
    deliverable_types = Deliverable_type.query.all()
    locations = Location.query.all()
    users = User.query.all()

    if request.method == 'POST':
        deliverable_name = request.form['deliverable_name']
        if (deliverable_name != "" and deliverable_name != deliverable.name):
            deliverable.name = deliverable_name
        deliverable_number = request.form['deliverable_number']
        if (deliverable_number != "" and deliverable_number != deliverable.component_number):
            deliverable.component_number = deliverable_number
        # description = request.form['deliverable_description']
        # if (description != "" and description != deliverable.description):
        #     deliverable.description = description
        start_date = request.form['start_date']
        if (start_date != "" and start_date != deliverable.start_date):
            deliverable.start_date = start_date
        assigned_to = request.form['assigned_to']
        if (assigned_to != "" and assigned_to != deliverable.assigned_to):
            deliverable.assigned_to = assigned_to
        db.session.commit()
        return redirect(url_for('site_project_ITP_deliverable_list', sitename=site, projectname=project.name, ITPname=project_ITP.name))
    else:
        return render_template('deliverable/ITP_deliverable_edit.html', site=site, project=project, ITP=project_ITP, types=deliverable_types, locations=locations, deliverable=deliverable, users=users)

#Route for deleting a current deliverable
@app.route('/site/<sitename>/projects/<projectname>/ITP/<ITPname>/deliverable/<deliverablename>/delete', methods=['POST','GET'])
def site_project_ITP_deliverable_delete(sitename, projectname, ITPname, deliverablename):
    site = Site.query.filter_by(name=sitename).first()
    project = Project.query.filter_by(name=projectname).first()
    project_ITP = ITP.query.filter_by(name=ITPname).first()
    deliverable = Deliverable.query.filter_by(name=deliverablename).first()

    if request.method == 'POST':
        db.session.delete(deliverable)
        db.session.commit()
        return redirect(url_for('site_project_ITP_deliverable_list', sitename=site, projectname=project.name, ITPname=project_ITP.name))
    else:
        return render_template('deliverable/ITP_deliverable_delete.html', site=site, project=project, ITP=project_ITP, deliverable=deliverable)


#Route for adding a check
# @app.route('/site/<sitename>/projects/<projectname>/ITP/<ITPname>/deliverable/<deliverablename>/ITC/add', methods=['POST','GET'])
# def site_project_ITP_deliverable_ITC_check_new(sitename, projectname, ITPname, deliverablename, ITCname, checkid):
#     site = Site.query.filter_by(name=sitename).first()
#     project = Project.query.filter_by(name=projectname).first()
#     project_ITP = ITP.query.filter_by(name=ITPname).first()
#     deliverable = Deliverable.query.filter_by(name=deliverablename).first()
#     ITP_ITC = ITC.query.filter_by(name=ITCname).first()
#     check = ITC_check_map.query.filter_by(ITC_id=ITP_ITC.id).first()
#
#     if request.method == 'POST':
#         comments = request.form['check_comment']
#         if (comments != "" and comments == check.comments):
#             check.comments = comments
#         check_generic = request.form['check_generic']
#         if (check_generic != "" and check_generic != check.check_generic):
#             check.check_generic = check_generic
#         check_status = request.form['check_status']
#         if (check_status != "" and check_status != check.status and check.is_done != True):
#             check.status = check_status
#         db.session.commit()
#         return redirect(url_for('ITC_testing', sitename=site, projectname=project.name, deliverablename=deliverable.name, ITPname=project_ITP.name, ITCid=ITP_ITC.id))
#     else:
#         return render_template('ITC_check_edit.html', site=site, project=project, ITP=project_ITP, deliverable=deliverable, ITC=ITP_ITC, check=check)

############################ ITC navigation controllers ########################


#Route for ITC list for given a deliverable
@app.route('/site/<sitename>/projects/<projectname>/ITP/<ITPname>/deliverable/<deliverablename>/ITC')
def site_project_ITP_deliverable_ITC_list(sitename, projectname, ITPname, deliverablename):
    site = Site.query.filter_by(name=sitename).first()
    project = Project.query.filter_by(name=projectname).first()
    project_ITP = ITP.query.filter_by(project_id=project.id, name=ITPname).first()
    deliverable = Deliverable.query.filter_by(ITP_id=project_ITP.id, name=deliverablename).first()
    ITP_ITCs = Deliverable_ITC_map.query.filter_by(deliverable_id=deliverable.id).all()

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

    return render_template('specific_ITC/ITC_list.html', site=site, project=project, ITP=project_ITP, deliverable=deliverable, ITCs=ITP_ITCs)

#Route for editing a current ITC
@app.route('/site/<sitename>/projects/<projectname>/ITP/<ITPname>/deliverable/<deliverablename>/ITC/<ITCid>/edit', methods=['POST','GET'])
def site_project_ITP_deliverable_ITC_edit(sitename, projectname, ITPname, deliverablename, ITCid):
    site = Site.query.filter_by(name=sitename).first()
    project = Project.query.filter_by(name=projectname).first()
    project_ITP = ITP.query.filter_by(project_id=project.id, name=ITPname).first()
    deliverable = Deliverable.query.filter_by(ITP_id=project_ITP.id, name=deliverablename).first()
    ITP_ITC = Deliverable_ITC_map.query.filter_by(deliverable_id=deliverable.id).first()
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
        return redirect(url_for('site_project_ITP_deliverable_ITC_list', sitename=site, projectname=project.name, ITPname=project_ITP.name, deliverablename=deliverable.name))
    else:
        return render_template('specific_ITC/ITC_edit.html', site=site, project=project, ITP=project_ITP, deliverable=deliverable, ITC=ITP_ITC)

#Route for deleting a current ITC
@app.route('/site/<sitename>/projects/<projectname>/ITP/<ITPname>/deliverable/<deliverablename>/ITC/<ITCid>/delete', methods=['POST','GET'])
def site_project_ITP_deliverable_ITC_delete(sitename, projectname, ITPname, deliverablename, ITCid):
    site = Site.query.filter_by(name=sitename).first()
    project = Project.query.filter_by(name=projectname).first()
    project_ITP = ITP.query.filter_by(project_id=project.id, name=ITPname).first()
    deliverable = Deliverable.query.filter_by(ITP_id=project_ITP.id, name=deliverablename).first()
    ITP_ITC = Deliverable_ITC_map.query.filter_by(deliverable_id=deliverable.id).first()

    if request.method == 'POST':
        db.session.delete(ITP_ITC)
        db.session.commit()
        return redirect(url_for('site_project_ITP_deliverable_ITC_list', sitename=site, projectname=project.name, ITPname=project_ITP.name, deliverablename=deliverable.name))
    else:
        return render_template('specific_ITC/ITC_delete.html', site=site, project=project, ITP=project_ITP, deliverable=deliverable, ITC=ITP_ITC)

#Route for updating check completion
@app.route('/site/<sitename>/projects/<projectname>/ITP/<ITPname>/deliverable/<deliverablename>/ITC/<ITCid>/check/change', methods=['POST'])
def site_project_ITP_deliverable_ITC_change(sitename, projectname, ITPname, deliverablename, ITCid):
    site = Site.query.filter_by(name=sitename).first()
    project = Project.query.filter_by(name=projectname).first()
    project_ITP = ITP.query.filter_by(name=ITPname).first()
    deliverable = Deliverable.query.filter_by(name=deliverablename).first()
    deliver_ITC = Deliverable_ITC_map.query.filter_by(deliverable_id=deliverable.id).first()
    user = current_user
    checked = request.form.getlist('check_box')
    completed_checks = Deliverable_check_map.query.filter_by(is_done=True, deliverable_ITC_map_id=deliver_ITC.id).all()
    checks = Deliverable_check_map.query.filter_by(deliverable_ITC_map_id=deliver_ITC.id).all()

    #Change form status to done
    for checkid in checked:
        check = Deliverable_check_map.query.filter_by(id=checkid).first()
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

    return redirect(url_for('ITC_testing', sitename=site, projectname=project.name, ITPname=project_ITP.name, deliverablename=deliverable.name, ITCid=ITCid))

################################################################################
###################### Specific ITC check list items ###########################
################################################################################

#Dynamically generate checks based on current ITCs
@app.route('/site/<sitename>/projects/<projectname>/ITP/<ITPname>/deliverable/<deliverablename>/ITC/<ITCid>/starttest')
def start_ITC_testing(sitename, projectname, ITPname, deliverablename, ITCid):
    site = Site.query.filter_by(name=sitename).first()
    project = Project.query.filter_by(name=projectname).first()
    project_ITP = ITP.query.filter_by(name=ITPname).first()
    deliverable = Deliverable.query.filter_by(name=deliverablename).first()
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

    return redirect(url_for('ITC_testing', sitename=site, projectname=project.name, ITPname=project_ITP.name, deliverablename=deliverable.name, ITCid=ITCid))

#Route for looking at all current checks for an ITC
@app.route('/site/<sitename>/projects/<projectname>/ITP/<ITPname>/deliverable/<deliverablename>/ITC/<ITCid>/checks')
def ITC_testing(sitename, projectname, ITPname, deliverablename, ITCid):
    site = Site.query.filter_by(name=sitename).first()
    project = Project.query.filter_by(name=projectname).first()
    project_ITP = ITP.query.filter_by(name=ITPname).first()
    deliverable = Deliverable.query.filter_by(name=deliverablename).first()
    deliver_ITC = Deliverable_ITC_map.query.filter_by(deliverable_id=deliverable.id, id=ITCid).first()
    deliverable_checks = Deliverable_check_map.query.filter_by(deliverable_ITC_map_id=deliver_ITC.id).all()

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

    if percentage_complete == 100:
        deliver_ITC.status = "Completed"
    elif (percentage_complete > 0 and percentage_complete < 100):
        deliver_ITC.status = "Completed"
    db.session.commit()

    return render_template('specific_ITC/ITC.html', site=site, project=project, ITP=project_ITP, deliverable=deliverable, ITC=deliver_ITC, checks=deliverable_checks, ITCid=ITCid, percentage_complete=percentage_complete)

#Route for editing a check
@app.route('/site/<sitename>/projects/<projectname>/ITP/<ITPname>/deliverable/<deliverablename>/ITC/<ITCid>/checks/<checkid>/edit', methods=['POST','GET'])
def site_project_ITP_deliverable_ITC_check_edit(sitename, projectname, ITPname, deliverablename, ITCid, checkid):
    site = Site.query.filter_by(name=sitename).first()
    project = Project.query.filter_by(name=projectname).first()
    project_ITP = ITP.query.filter_by(name=ITPname).first()
    deliverable = Deliverable.query.filter_by(name=deliverablename).first()
    ITP_ITC = Deliverable_ITC_map.query.filter_by(id=ITCid).first()
    check = ITC_check_map.query.filter_by(ITC_id=ITP_ITC.id).first()

    if request.method == 'POST':
        comments = request.form['check_comment']
        if (comments != "" and comments == check.comments):
            check.comments = comments
        check_generic = request.form['check_generic']
        if (check_generic != "" and check_generic != check.check_generic):
            check.check_generic = check_generic
        check_status = request.form['check_status']
        if (check_status != "" and check_status != check.status and check.is_done != True):
            check.status = check_status
        db.session.commit()
        return redirect(url_for('ITC_testing', sitename=site, projectname=project.name, deliverablename=deliverable.name, ITPname=project_ITP.name, ITCid=ITP_ITC.id))
    else:
        return render_template('specific_ITC/ITC_check_edit.html', site=site, project=project, ITP=project_ITP, deliverable=deliverable, ITC=ITP_ITC, check=check)

#Route for deleting a check
@app.route('/site/<sitename>/projects/<projectname>/ITP/<ITPname>/deliverable/<deliverablename>/ITC/<ITCid>/checks/<checkid>/delete', methods=['POST','GET'])
def site_project_ITP_deliverable_ITC_check_delete(sitename, projectname, ITPname, deliverablename, ITCid, checkid):
    site = Site.query.filter_by(name=sitename).first()
    project = Project.query.filter_by(name=projectname).first()
    project_ITP = ITP.query.filter_by(name=ITPname).first()
    deliverable = Deliverable.query.filter_by(name=deliverablename).first()
    ITP_ITC = Deliverable_ITC_map.query.filter_by(id=ITCid).first()
    check = Deliverable_check_map.query.filter_by(id=checkid).first()

    if request.method == 'POST':
        db.session.delete(check)
        db.session.commit()
        return redirect(url_for('ITC_testing', sitename=site, projectname=project.name, deliverablename=deliverable.name, ITPname=project_ITP.name, ITCid=ITP_ITC.id))
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

    if request.method == 'POST':
        deliverable_type = Deliverable_type.query.filter_by(name=request.form['deliverable_type']).first()
        new_ITC = ITC(request.form['ITC_name'], deliverable_type.id)
        db.session.add(new_ITC)
        db.session.commit()
        return redirect(url_for('ITC_general_list'))
    else:
        return render_template('generic_ITC/ITC_new.html', deliverables=deliverable_types)

#Route for viewing all general ITC
@app.route('/generic/ITC', methods=['POST','GET'])
def ITC_general_list():
    ITCs = ITC.query.all()

    return render_template('generic_ITC/ITC_general.html', ITCs=ITCs)

#Delete generic check
@app.route('/generic/ITC/<ITCid>/delete', methods=['POST','GET'])
def ITC_general_delete(ITCid):
    ITC_generic = ITC.query.filter_by(id=ITCid).first()

    if request.method == 'POST':
        db.session.delete(ITC_generic)
        db.session.commit()
        return redirect(url_for('ITC_general_list'))
    else:
        return render_template('generic_ITC/ITC_general_delete.html', ITC=ITC_generic)

#Edit generic check
@app.route('/generic/ITC/<ITCid>/edit', methods=['POST','GET'])
def ITC_general_edit(ITCid):
    ITC_generic = ITC.query.filter_by(id=ITCid).first()

    if request.method == 'POST':
        name = request.form['ITC_general_name']
        if (name != "" and name == ITC_generic.name):
            ITC_generic.name = name
        deliverable_type_id = Deliverable_type.query.filter_by(name=request.form['ITC_general_deliverable_type']).first()
        if (deliverable_type_id != ITC_generic.delvierable_type_id):
            ITC_generic.delvierable_type_id = deliverable_type_id
        db.session.delete(ITC_generic)
        db.session.commit()
        return redirect(url_for('ITC_general_list'))
    else:
        return render_template('generic_ITC/ITC_general_edit.html', ITC=ITC_generic)


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

#Route for deleting a generic check
@app.route('/generic/ITC/<ITCid>/check/<checkid>/delete', methods=['POST', 'GET'])
def ITC_check_general_delete(ITCid, checkid):
    ITP_ITC = ITC.query.filter_by(id=ITCid).first()
    check = ITC_check_map.query.filter_by(id=checkid).first()

    if request.method == 'POST':
        db.session.delete(check)
        db.session.commit()
        return redirect(url_for('ITC_general', ITCid=ITP_ITC.id))
    else:
        return render_template('generic_ITC_check/generic_ITC_check_delete.html', ITC=ITP_ITC, check=check)

################ Check creation and editing for generic ITC ####################

#Route for new generic check
@app.route('/generic/check/new', methods=['POST', 'GET'])
def generic_check_new():
    if request.method == "POST":
        check = Check_generic(request.form['check_description'])
        db.session.add(check)
        db.session.commit()
        return redirect(url_for('generic_check_list'))
    else:
        return render_template('generic_check/generic_check_new.html')

#Route for viewing all generic checks
@app.route('/generic/check')
def generic_check_list():
    checks = Check_generic.query.all()

    return render_template('generic_check/generic_check_list.html', checks=checks)

#Route for editing generic checks
@app.route('/generic/check/<checkid>/edit', methods=['POST', 'GET'])
def generic_check_edit(checkid):
    check = Check_generic.query.filter_by(id=checkid).first()

    if request.method == "POST":
        check_description = request.form['check_description']
        if (check_description != "" and check_description != check.check_description):
            check.check_description = check_description
        db.session.commit()
        return redirect(url_for('generic_check_list'))
    else:
        return render_template('generic_check/generic_check_edit.html', check=check)

#Route for deleting generic check
@app.route('/generic/check/<checkid>/delete', methods=['POST', 'GET'])
def generic_check_delete(checkid):
    check = Check_generic.query.filter_by(id=checkid).first()

    if request.method == "POST":
        db.session.delete(check)
        db.session.commit()
        return redirect(url_for('generic_check_list'))
    else:
        return render_template('generic_check/generic_check_delete.html', check=check)





#
