from app import app, db
from app.models import Asset, Site, AssetPoint, AssetType, Algorithm, FunctionalDescriptor, PointType, Result, LoggedEntity, LogTimeValue, IssueHistory, IssueHistoryTimestamp, CMMSInterface, CMMSConfig
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

# display chart of unresolved issues over time
@app.route('/site/all/issue-chart')
def unresolved_chart():
    sites = Site.query.all()
    history = IssueHistoryTimestamp.query.filter(IssueHistoryTimestamp.timestamp > datetime.datetime.now()-datetime.timedelta(hours=24)).all()
    return render_template('issue_chart.html', sites=sites, history=history, allsites=True)

# show map of all tech locations
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
    site = Site(name=request.form['name'], db_key=request.form['database_key'])
    for interface in CMMSInterface.query.all():
        cmms_config = CMMSConfig(interface=interface, enabled=False)
        site.cmms_configs.append(cmms_config)
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
        avg_health = mean([asset.health for asset in site.assets])
    else:
        avg_health = 0

    low_health_assets = len(Asset.query.filter(Asset.site == site, Asset.health < 0.5).all())
    return render_template('dashboard.html', results=results, num_results=num_results, top_priority=top_priority, avg_health=avg_health, low_health_assets=low_health_assets, site=site)

# list assets on the site
@app.route('/site/<sitename>/assets')
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

# show results for a single asset
@app.route('/site/<sitename>/results/<assetname>')
def result_list(sitename, assetname):
    site = Site.query.filter_by(name=sitename).one()
    asset = Asset.query.filter_by(name=assetname, site=site).one()
    recent_results = Result.query.filter_by(asset=asset, recent=True).all()
    unresolved_results = Result.query.filter(Result.asset==asset, Result.status_id > 1, Result.status_id < 5).all()
    return render_template('results.html', asset=asset, site=site, recent_results=recent_results, unresolved_results=unresolved_results)

# show CMMS integration page
@app.route('/site/<sitename>/CMMS')
def CMMS(sitename):
    site = Site.query.filter_by(name=sitename).one()
    inbuildings = CMMSInterface.query.filter_by(name='Inbuildings').one()
    astea = CMMSInterface.query.filter_by(name='Astea').one()
    inbuildings_config = CMMSConfig.query.filter_by(site=site, interface=inbuildings).one()
    astea_config = CMMSConfig.query.filter_by(site=site, interface=astea).one()
    return render_template('CMMS.html', inbuildings_config=inbuildings_config, astea_config=astea_config, site=site)

# update CMMS config for a site
@app.route('/site/<sitename>/CMMS/_submit', methods=['POST'])
def CMMS_submit(sitename):
    site = Site.query.filter_by(name=sitename).one()
    print(request.form)
    for interface in CMMSInterface.query.all():
        config = CMMSConfig.query.filter_by(site=site, interface=interface).one()
        config.enabled = request.form.get(interface.name, False)
        config.key = request.form.get(interface.name + '_key')
        print(config)
    db.session.commit()
    return redirect(url_for('homepage', sitename=sitename))