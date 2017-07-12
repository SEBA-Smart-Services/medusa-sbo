from app import app, db, registry
from app.models import Asset, Site, AssetPoint, AssetType, Algorithm, FunctionalDescriptor, PointType, Result, LoggedEntity, LogTimeValue, IssueHistory, IssueHistoryTimestamp, InbuildingsConfig, Email
from app.models import Alarm
from app.models.ITP import Project, ITP, Deliverable, Location, Deliverable_type
from app.forms import SiteConfigForm, AddSiteForm
from flask import json, request, render_template, url_for, redirect, jsonify, flash, make_response
from flask_user import current_user
from statistics import mean
import datetime, time


# enforce login required for all pages
@app.before_request
def check_valid_login():
    login_valid = current_user.is_authenticated

    if (request.endpoint and
        # not required for login page or static content
        request.endpoint != 'user.login' and
        request.endpoint != 'static' and
        not login_valid and
        # check if it's allowed to be public, see public_endpoint decorator
        not getattr(app.view_functions[request.endpoint], 'is_public', False    ) ) :
        # redirect to login page if they are not authenticated
        return redirect(url_for('user.login'))

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

# set homepage for overall view (Not sure why this is needed?)
#@app.route('/site/all')
#def homepage_all():
#    return redirect(url_for('dashboard_all'))

# show overview dashboard. has aggregated info for all the sites that are attached to the currently logged in user
@app.route('/site/all/dashboard')
def dashboard_all():
    sites = current_user.sites
    # sqlalchemy can't do relationship filtering to see if an attribute is in a list of objects (e.g. to see if asset.site is in sites)
    # instead, we do the filtering on the ids (e.g. to see if asset.site.id is in the list of site ids)
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
    # only send results[0:5], to display the top 5 priority issues in the list
    return render_template('dashboard.html', results=results[0:5], num_results=num_results, top_priority=top_priority, avg_health=avg_health, low_health_assets=low_health_assets, allsites=True, alarmcount=nalarms)

# list all sites that are attached to the logged in user
@app.route('/site/all/sites')
def site_list():
    sites = current_user.sites
    issues = {}
    priority = {}
    for site in sites:
        issues[site.name] = len(site.get_unresolved())
        if not site.get_unresolved_by_priority():
            # there are no issues at this site
            top_priority = "-"
        else:
            top_priority = site.get_unresolved_by_priority()[0].asset.priority
        priority[site.name] = top_priority
    return render_template('sites.html', sites=sites, issues=issues, priority=priority, allsites=True)

# list all unresolved issues for the sites attached to the logged in user
@app.route('/site/all/issues')
def unresolved_list_all():
    sites = current_user.sites
    results = []
    for site in sites:
        results.extend(site.get_unresolved())
    return render_template('issues.html', results=results, allsites=True)

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

    return render_template('issue_chart.html', sites=sites, array=array, history=history, allsites=True)

# show map of all tech locations
# NOTE: currently just set to iframe a blank google maps
@app.route('/site/all/map')
def map():
    # TODO: figure out how to auto sign into the inbuildings page. Attempt at cookies below doesn't work
    response = make_response(render_template('map.html', allsites=True))
    return response

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
        return render_template('add_site.html', form=form, allsites=True)

    elif request.method == 'POST':
        # if form has errors, return the page (errors will display)
        if not form.validate_on_submit():
            return render_template('add_site.html', form=form, allsites=True)

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

        db.session.add(site)
        db.session.commit()
        return redirect(url_for('add_asset', sitename=site.name))

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
        alarmcount=nalarms
    )

# list assets on the site
@app.route('/site/<sitename>/assets',  methods=['GET', 'POST'])
def asset_list(sitename):
    site = Site.query.filter_by(name=sitename).one()
    asset_types = AssetType.query.all()
    asset_quantity = {}
    for asset_type in asset_types:
        asset_quantity[asset_type.name] = len(Asset.query.filter_by(site=site, type=asset_type).all())
    return render_template('assets.html', assets=site.assets, asset_quantity=asset_quantity, asset_types=asset_types, site=site)

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
    inbuildings_config = InbuildingsConfig.query.filter_by(site=site).one()

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
	    rows=nalarms
    )


################################################################################
########################## controllers for ITP routes###########################
################################################################################

##################### Project navigation controllers ###########################

#Route for all Projects for a given site
#projects need to filter on site_id and then loop to create a list of projects to send to view
#in table maybe add a ITP tab to go straight to ITPs
@app.route('/site/<sitename>/projects')
def site_projects_list(sitename):
    site = Site.query.filter_by(name=sitename).one()
    #site_projects = Project.query.filter_by(site_id = site.id).all()
    projects = []
    for i in Project.query.all():
        projects.append(i)

    return render_template('site_projects_list.html', site=site, projects=projects)

#Route for individual Project for a given Site
@app.route('/site/<sitename>/projects/<projectname>')
def site_project(sitename, projectname):
    site = Site.query.filter_by(name=sitename).one()
    project = Project.query.filter_by(name=projectname).one()
    project_ITP = ITP.query.filter_by(project_id=project.id).one()
    return render_template('site_project.html', site=site, project=project, ITP=project_ITP)

#Route for creating a new Project for a given Site
#add in __init__ to schema so the variables can just be passed to the new Project
#including site_id
@app.route('/site/<sitename>/projects/new', methods=['POST','GET'])
def site_project_new(sitename):
    site = Site.query.filter_by(name=sitename).one()

    if request.method == 'POST':
        project_name = request.form['project_name']
        description = request.form['project_description']
        new_site = Project()
        new_site.name = project_name
        db.session.add(new_site)
        db.session.commit()
        return redirect(url_for('site_projects_list', sitename=site))
    else:
        return render_template('site_project_new.html', site=site)

#Route for editing a current project
@app.route('/site/<sitename>/projects/<projectname>/edit', methods=['POST','GET'])
def site_project_edit(sitename, projectname):
    site = Site.query.filter_by(name=sitename).one()
    project = Project.query.filter_by(name=projectname).one()

    if request.method == 'POST':
        project_name = request.form['project_name']
        if (project_name != "" and project_name != project.name):
            project.name = project_name
        description = request.form['project_description']
        #if (description != "" and request.form['project_description'] == project.description):
        #    description = request.form['project_description']
        db.session.commit()
        return redirect(url_for('site_projects_list', sitename=site))
    else:
        return render_template('site_project_edit.html', site=site, project=project)

#Route for deleting a current project
@app.route('/site/<sitename>/projects/<projectname>/delete', methods=['POST','GET'])
def site_project_delete(sitename, projectname):
    site = Site.query.filter_by(name=sitename).one()
    project = Project.query.filter_by(name=projectname).one()

    if request.method == 'POST':
        db.session.delete(project)
        db.session.commit()
        return redirect(url_for('site_projects_list', sitename=site))
    else:
        return render_template('site_project_delete.html', site=site, project=project)

############################ ITP navigation controllers ########################

#Route for ITP list
#filter project on site_id aswell to ensure there is no overlap
#@app.route('/site/<sitename>/projects/<projectname>/ITP')
#def site_project_ITP_list(sitename, projectname):
#    site = Site.query.filter_by(name=sitename).one()
#    project = Project.query.filter_by(name=projectname).one()
#    ITPs = ITP.query.filter_by(project_id=project.id).all()
#
#    return render_template('project_ITP_list.html', site=site, project=project, ITPs=ITPs)

#Route for details on ITP for project
@app.route('/site/<sitename>/projects/<projectname>/ITP/<ITPname>')
def site_project_ITP(sitename, projectname, ITPname):
    site = Site.query.filter_by(name=sitename).one()
    project = Project.query.filter_by(name=projectname).one()
    project_ITP = ITP.query.filter_by(name=ITPname).one()

    return render_template('project_ITP.html', site=site, project=project, ITP=project_ITP)

#Route for creating new ITP
@app.route('/site/<sitename>/projects/<projectname>/ITP/new', methods=['POST','GET'])
def site_project_ITP_new(sitename, projectname):
    site = Site.query.filter_by(name=sitename).one()
    project = Project.query.filter_by(name=projectname).one()

    if request.method == 'POST':
        ITP_name = request.form['ITP_name']
        new_ITP = ITP()
        new_ITP.name = ITP_name
        new_ITP.project_id = project.id
        db.session.add(new_ITP)
        db.session.commit()
        return redirect(url_for('site_project_ITP_list', sitename=site, projectname=project.name))
    else:
        return render_template('project_ITP_new.html', site=site, project=project)

#Route for editing a current ITP
@app.route('/site/<sitename>/projects/<projectname>/ITP/<ITPname>/edit', methods=['POST','GET'])
def site_project_ITP_edit(sitename, projectname, ITPname):
    site = Site.query.filter_by(name=sitename).one()
    project = Project.query.filter_by(name=projectname).one()
    project_ITP = ITP.query.filter_by(name=ITPname).one()

    if request.method == 'POST':
        ITP_name = request.form['ITP_name']
        if (ITP_name != "" and ITP_name != project_ITP.name):
            project_ITP.name = ITP_name
        description = request.form['ITP_description']
        #if (description != "" and request.form['project_description'] == project.description):
        #    description = request.form['project_description']
        db.session.commit()
        return redirect(url_for('site_project_ITP_list', sitename=site, projectname=project.name))
    else:
        return render_template('project_ITP_edit.html', site=site, project=project, ITP=project_ITP)

#Route for deleting a current ITP
@app.route('/site/<sitename>/projects/<projectname>/ITP/<ITPname>/delete', methods=['POST','GET'])
def site_project_ITP_delete(sitename, projectname, ITPname):
    site = Site.query.filter_by(name=sitename).one()
    project = Project.query.filter_by(name=projectname).one()
    project_ITP = ITP.query.filter_by(name=ITPname).one()

    if request.method == 'POST':
        db.session.delete(project_ITP)
        db.session.commit()
        return redirect(url_for('site_project_ITP_list', sitename=site, projectname=project.name))
    else:
        return render_template('project_ITP_delete.html', site=site, project=project, ITP=project_ITP)

################### deliverable type navigation controllers ####################

#Route for list of deliverable_types
#@app.route('/deliverable_type')
#def deliverable_type_list():
#    types = Deliverable_type.query.all()
#
#    return render_template('deliverable_type.html', types=types, allsites=True)

#Route for creating new deliverable_type
#@app.route('/deliverable_type/new', methods=['POST','GET'])
#def deliverable_type_new():
#    all_deliverable_types = Deliverable_type.query.all()

#    if request.method == 'POST':
#        type_name = request.form['type_name']
        #ensure deliverable doesnt already exsist

#        if len(Deliverable_type.query.filter_by(name=type_name).all()) == 0:
#            deliverable_type = Deliverable_type()
#            deliverable_type.name = type_name
#            db.session.add(deliverable_type)
#            db.session.commit()
#            return redirect(url_for('deliverable_type_list'))
        #could do DOM event to point out that it already exsists
#        return render_template('deliverable_type_new.html', allsites=True)
#    else:
#        return render_template('deliverable_type_new.html', allsites=True)

#Route for editing a current deliverable
#@app.route('/deliverable_type/<deliverabletypename>/edit', methods=['POST','GET'])
#def deliverable_type_edit(deliverabletypename):
#    deliverable_type = Deliverable_type.query.filter_by(name=deliverabletypename).one()

#    if request.method == 'POST':
#        deliverable_type_name = request.form['type_name']
#        if (deliverable_type_name != "" and deliverable_type_name != deliverable_type.name):
#            deliverable_type.name = deliverable_type_name
#        description = request.form['type_description']
        #if (description != "" and request.form['project_description'] == project.description):
        #    description = request.form['project_description']
#        db.session.commit()
#        return redirect(url_for('deliverable_type_list'))
#    else:
#        return render_template('deliverable_type_edit.html', deliverable_type=deliverable_type, allsites=True)

#Route for deleting a current deliverable
#@app.route('/deliverable_type/<deliverabletypename>/delete', methods=['POST','GET'])
#def deliverable_type_delete(deliverabletypename):
#    deliverable_type = Deliverable_type.query.filter_by(name=deliverabletypename).one()

#    if request.method == 'POST':
#        db.session.delete(deliverable_type)
#        db.session.commit()
#        return redirect(url_for('deliverable_type_list'))
#    else:
#        return render_template('deliverable_type_delete.html', deliverable_type=deliverable_type, allsites=True)



####################### location navigation controllers ########################

#Route for locations
#@app.route('/locations')
#def location_list():
#    locations = Location.query.all()
#    return render_template('location.html', locations=locations, allsites=True)

#Route for creating new locations
#@app.route('/locations/new', methods=['POST','GET'])
#def location_new():
#    all_locations = Location.query.all()

#    if request.method == 'POST':
#        location_name = request.form['location_name']

        #ensure location doesnt already exist
#        if len(Location.query.filter_by(name=location_name).all()) == 0:
#            location = Location()
#            location.name = location_name
#            db.session.add(location)
#            db.session.commit()
#            return redirect(url_for('location_list'))
        #could do DOM event to point out that it already exsists?
#        return render_template('location_new.html', allsites=True)
#    else:
#        return render_template('location_new.html', allsites=True)

#Route for editing current locations
#@app.route('/locations/<locationname>/edit', methods=['POST','GET'])
#def location_edit(locationname):
#    location = Location.query.filter_by(name=locationname).one()

#    if request.method == 'POST':
#        location_name = request.form['location_name']
#        if (location_name != "" and location_name != location.name):
#            location.name = location_name
#        description = request.form['location_description']
        #if (description != "" and request.form['project_description'] == project.description):
        #    description = request.form['project_description']
#        db.session.commit()
#        return redirect(url_for('location_list'))
#    else:
#        return render_template('location_edit.html', location=location, allsites=True)

#Route for editing current locations
#@app.route('/locations/<locationname>/delete', methods=['POST','GET'])
#def location_delete(locationname):
#    location = Location.query.filter_by(name=locationname).one()

#    if request.method == 'POST':
#        db.session.delete(location)
#        db.session.commit()
#        return redirect(url_for('location_list'))
#    else:
#        return render_template('location_delete.html', location=location, allsites=True)


###################### deliverable navigation controllers ######################
#maybe have section for new deliverable type and location creation?
#regex search for names (case insensitive) if not found add to list

#Route for deliverable list
@app.route('/site/<sitename>/projects/<projectname>/ITP/<ITPname>/deliverable')
def site_project_ITP_deliverable_list(sitename, projectname, ITPname):
    site = Site.query.filter_by(name=sitename).one()
    project = Project.query.filter_by(name=projectname).one()
    project_ITP = ITP.query.filter_by(name=ITPname).one()
    deliverables = Deliverable.query.filter_by(ITP_id=project_ITP.id).all()

    return render_template('ITP_deliverable_list.html', site=site, project=project, ITP=project_ITP, deliverables=deliverables)

#Route for deliverable
@app.route('/site/<sitename>/projects/<projectname>/ITP/<ITPname>/deliverable/<deliverablename>')
def site_project_ITP_deliverable(sitename, projectname, ITPname, deliverablename):
    site = Site.query.filter_by(name=sitename).one()
    project = Project.query.filter_by(name=projectname).one()
    project_ITP = ITP.query.filter_by(name=ITPname).one()
    deliverable = Deliverable.query.filter_by(name=deliverablename).one()

    return render_template('ITP_deliverable.html', site=site, project=project, ITP=project_ITP, deliverable=deliverable)

#Route for new deliverable
@app.route('/site/<sitename>/projects/<projectname>/ITP/<ITPname>/deliverable/new', methods=['POST','GET'])
def site_project_ITP_deliverable_new(sitename, projectname, ITPname):
    site = Site.query.filter_by(name=sitename).one()
    project = Project.query.filter_by(name=projectname).one()
    project_ITP = ITP.query.filter_by(name=ITPname).one()
    deliverable_types = Deliverable_type.query.all()
    locations = Location.query.all()

    print(locations)

    if request.method == 'POST':
        name = request.form['deliverable_name']
        location = request.form['deliverable_location']
        deliverable_type = request.form['deliverable_type']
        deliverable = Deliverable()
        deliverable.name = name
        deliverable.deliverable_type_id = Deliverable_type.query.filter_by(name=deliverable_type).one().id
        deliverable.location_id = Location.query.filter_by(name=location).one().id
        deliverable.ITP_id = project_ITP.id
        db.session.add(deliverable)
        db.session.commit()
        return redirect(url_for('site_project_ITP_deliverable_list', sitename=site, projectname=project.name, ITPname= project_ITP.name))
    else:
        return render_template('ITP_deliverable_new.html', site=site, project=project, ITP=project_ITP, types=deliverable_types, locations=locations)

#Route for editing a current ITP
@app.route('/site/<sitename>/projects/<projectname>/ITP/<ITPname>/deliverable/<deliverablename>/edit', methods=['POST','GET'])
def site_project_ITP_deliverable_edit(sitename, projectname, ITPname, deliverablename):
    site = Site.query.filter_by(name=sitename).one()
    project = Project.query.filter_by(name=projectname).one()
    project_ITP = ITP.query.filter_by(name=ITPname).one()
    deliverable = Deliverable_type.query.filter_by(name=deliverablename).one()
    deliverable_types = Deliverable_type.query.all()
    locations = Location.query.all()

    if request.method == 'POST':
        deliverable_name = request.form['deliverable_name']
        if (deliverable_name != "" and deliverable_name != deliverable.name):
            deliverable.name = deliverable_name
        description = request.form['deliverable_description']
        #if (description != "" and request.form['project_description'] == project.description):
        #    description = request.form['project_description']
        db.session.commit()
        return redirect(url_for('site_project_ITP_deliverable_list', sitename=site, projectname=projectname.name, ITPname=project_ITP.name))
    else:
        return render_template('ITP_deliverable_edit.html', site=site, project=project, ITP=project_ITP, types=deliverable_list, locations=locations, deliverable=deliverable)

#Route for deleting a current ITP
@app.route('/site/<sitename>/projects/<projectname>/ITP/<ITPname>/deliverable/<deliverablename>/delete', methods=['POST','GET'])
def site_project_ITP_deliverable_delete(sitename, projectname, ITPname, deliverablename):
    site = Site.query.filter_by(name=sitename).one()
    project = Project.query.filter_by(name=projectname).one()
    project_ITP = ITP.query.filter_by(name=ITPname).one()
    deliverable = Deliverable_type.query.filter_by(name=deliverablename).one()

    if request.method == 'POST':
        db.session.delete(deliverable)
        db.session.commit()
        return redirect(url_for('site_project_ITP_deliverable_list', sitename=site, projectname=project.name, ITPname=project_ITP.name))
    else:
        return render_template('ITP_deliverable_delete.html', site=site, project=project, ITP=project_ITP)

############################ ITC navigation controllers ########################


#Route for checks list
