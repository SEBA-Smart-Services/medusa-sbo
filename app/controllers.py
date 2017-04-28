from app import app, db
from app.models import Asset, Site, AssetPoint, AssetType, Algorithm, FunctionalDescriptor, PointType, Result, LoggedEntity, LogTimeValue, IssueHistory, IssueHistoryTimestamp, InbuildingsConfig
from flask import json, request, render_template, url_for, redirect, jsonify, flash, make_response
from statistics import mean
import datetime, time

###################################
## main pages for all sites
###################################

# default path
@app.route('/')
def main():
    return redirect(url_for('homepage_all'))

# set homepage for overall view
@app.route('/site/all')
def homepage_all():
    return redirect(url_for('dashboard_all'))

# show overview dashboard
@app.route('/site/all/dashboard')
def dashboard_all():
    results = Result.get_unresolved_by_priority()[0:4]
    num_results = len(Result.get_unresolved())

    if not Result.get_unresolved_by_priority():
        # there are no issues across any sites. Celebrate!
        top_priority = "-"
    else:
        top_priority = Result.get_unresolved_by_priority()[0].asset.priority

    if len(Asset.query.all()) > 0:
        try:
            avg_health = mean([asset.health for asset in Asset.query.all()])
        except TypeError:
            # one of the asset healths is Null
            for asset in Asset.query.all():
                if asset.health is None:
                    asset.health = 0
            db.session.commit()
            avg_health = mean([asset.health for asset in Asset.query.all()])

    else:
        avg_health = 0

    low_health_assets = len(Asset.query.filter(Asset.health < 0.5).all())
    return render_template('dashboard.html', results=results, num_results=num_results, top_priority=top_priority, avg_health=avg_health, low_health_assets=low_health_assets, allsites=True)

# list all sites
@app.route('/site/all/sites')
def site_list():
    sites = Site.query.all()
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

# list all unresolved issues
@app.route('/site/all/unresolved')
def unresolved_list_all():
    results = Result.get_unresolved()
    return render_template('unresolved.html', results=results, allsites=True)

@app.route('/site/all/unresolved/_submit', methods=['POST'])
def unresolved_issues_submit_all():
    results = Result.get_unresolved()
    print(request.form['acknowledge'])
    #for result_id in request.form['acknowledge']

    return redirect(url_for('unresolved_list_all'))

# display chart of unresolved issues over time
@app.route('/site/all/issue-chart')
def unresolved_chart():
    sites = Site.query.all()
    history = IssueHistoryTimestamp.query.filter(IssueHistoryTimestamp.timestamp > datetime.datetime.now()-datetime.timedelta(hours=24)).all()

    # generate array to be converted into chart
    # header row
    array = "[['Time',"
    for site in sites:
        array += "'" + site.name + "',"
    array += "],"
    # data rows
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
    response.set_cookie('ARRAffinity', 'd5fb9e944f8abbefd6bc0a9a39c159ffc6fbb4084e000bed662582769266cb00', domain='.inbuildings.info')
    response.set_cookie('PHPSESSID', 'pudr7sj47olg948h1ollv8vrv7', domain='inbuildings.info')
    return response

# conversion tool for adding entries to the issue chart
@app.template_filter('date_to_millis')
def date_to_millis(d):
    """Converts a datetime object to the number of milliseconds since the unix epoch."""
    return int(time.mktime(d.timetuple())) * 1000

# page to add a site to the system
@app.route('/site/all/add_site')
def add_site():
    return render_template('add_site.html', allsites=True)

# handle creation of a new site
@app.route('/site/all/add_site/_submit', methods=['POST'])
def add_site_submit():
    site = Site(name=request.form['name'])
    site.inbuildings_config = InbuildingsConfig(enabled=False, key="")

    # set webreports database settings
    site.db_username = request.form.get('db_username')
    site.db_password = request.form.get('db_password')
    site.db_address = request.form.get('db_address')
    site.db_port = request.form.get('db_port')
    site.db_name = request.form.get('db_name')
    site.generate_key()

    db.session.add(site)
    db.session.commit()
    return redirect(url_for('site_list'))

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
            # one of the asset healths is Null
            for asset in site.assets:
                if asset.health is None:
                    asset.health = 0
            db.session.commit()
            avg_health = mean([asset.health for asset in site.assets])
    else:
        avg_health = 0

    low_health_assets = len(Asset.query.filter(Asset.site == site, Asset.health < 0.5).all())
    return render_template('dashboard.html', results=results, num_results=num_results, top_priority=top_priority, avg_health=avg_health, low_health_assets=low_health_assets, site=site)

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
@app.route('/site/<sitename>/unresolved')
def unresolved_list(sitename):
    site = Site.query.filter_by(name=sitename).one()
    results = site.get_unresolved()
    return render_template('unresolved.html', results=results, site=site)

# handle update from acknowledging/editing notes of issues for a site
@app.route('/site/<sitename>/unresolved/_submit', methods=['POST'])
def unresolved_issues_submit(sitename):
    site = Site.query.filter_by(name=sitename).one()
    results = site.get_unresolved()

    # unacknowledge all results and set notes field
    for result in results:
        result.acknowledged = False
        result.notes = request.form['notes-' + str(result.id)]

    # acknowledge results as per input
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

    # acknowledge results as per input
    for result_id in request.form.getlist('acknowledge'):
        result = Result.query.filter_by(id=result_id).one()
        result.acknowledged = True

    db.session.commit()

    return redirect(url_for('asset_details', sitename=sitename, asset_id=asset_id))

# show site config page
@app.route('/site/<sitename>/config')
def site_config(sitename):
    site = Site.query.filter_by(name=sitename).one()
    inbuildings_config = InbuildingsConfig.query.filter_by(site=site).one()
    return render_template('site_config.html', inbuildings_config=inbuildings_config, site=site)

# update config for a site
@app.route('/site/<sitename>/config/_submit', methods=['POST'])
def site_config_submit(sitename):
    site = Site.query.filter_by(name=sitename).one()

    # update webreports database settings
    site.db_username = request.form.get('db_username')
    site.db_password = request.form.get('db_password')
    site.db_address = request.form.get('db_address')
    site.db_port = request.form.get('db_port')
    site.db_name = request.form.get('db_name')
    site.generate_key()

    # update inbuildings settings
    inbuildings_config = InbuildingsConfig.query.filter_by(site=site).one()
    inbuildings_config.enabled = request.form.get('inbuildings', False)
    inbuildings_config.key = request.form.get('inbuildings_key')

    db.session.commit()
    return redirect(url_for('homepage', sitename=sitename))
