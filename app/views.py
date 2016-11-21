from app import app, db
from app.models import Asset, Site, AssetComponent, AssetType, Algorithm, AssetHealth, AssetSubtype, ComponentType, InbuildingsAsset, Result, SubtypeComponent, LoggedEntity, LogTimeValue
from app.checks import check_asset
from app.mapping import generate_algorithms, map_algorithms, map_asset_subtypes
from app.inbuildings import inbuildings_asset_request
from flask import json, request, render_template, url_for, redirect, jsonify


###################################
## endpoints
###################################

@app.route('/')
def main():
    return redirect(url_for('asset_list', sitename='TestSite'))

# set homepage for the site
@app.route('/<string:sitename>')
def homepage(sitename):
    return redirect(url_for('asset_list', sitename=sitename))

# list assets on the site
@app.route('/<string:sitename>/assets')
def asset_list(sitename):
    site = Site.query.filter_by(name=sitename).one()
    return render_template('assets.html', assets=site.assets, site=site)

# list unresolved issues on the site
@app.route('/<string:sitename>/unresolved')
def unresolved_list(sitename):
    site = Site.query.filter_by(name=sitename).one()
    results = Result.query.filter_by(unresolved=True).all()
    return render_template('unresolved.html', results=results, site=site)

# page to add an asset to the site
@app.route('/<string:sitename>/add')
def add_asset_input(sitename):
    site = Site.query.filter_by(name=sitename).one()
    asset_types = AssetType.query.all()
    return render_template('add.html', site=site, asset_types=asset_types)

# return list of subtypes through AJAX
@app.route('/<string:sitename>/add/_subtype')
def return_subtypes(sitename):
    asset_type_name = request.args.get('type', '')
    asset_type = AssetType.query.filter_by(name=asset_type_name).one()
    subtypes = AssetSubtype.query.filter_by(type=asset_type)
    subtype_names = [subtype.name for subtype in subtypes]
    return jsonify(subtype_names)

# return list of loggedentities through AJAX
@app.route('/<string:sitename>/add/_loggedentity')
def return_loggedentities(sitename):
    site = Site.query.filter_by(name=sitename).one()

    # select database
    LoggedEntity.__table__.info['bind_key'] = site.db_name

    logs = LoggedEntity.query.filter_by(type='trend.ETLog').all()
    log_paths = [log.path for log in logs]
    return jsonify(log_paths)

# return list of components through AJAX
@app.route('/<string:sitename>/add/_component')
def return_components(sitename):
    asset_type_name = request.args.get('type', '')
    asset_type = AssetType.query.filter_by(name=asset_type_name).one()
    subtype_name = request.args.get('subtype', '')
    subtype = AssetSubtype.query.filter_by(name=subtype_name, type=asset_type).one()
    components = subtype.components
    component_names = [component.type.name for component in components]
    return jsonify(component_names)

# return list of algorithms to exclude through AJAX
@app.route('/<string:sitename>/add/_exclusion')
def return_exclusions(sitename):
    asset_type_name = request.args.get('type', '')
    asset_type = AssetType.query.filter_by(name=asset_type_name).one()
    subtype_name = request.args.get('subtype', '')
    subtype = AssetSubtype.query.filter_by(name=subtype_name, type=asset_type).one()
    algorithms = subtype.algorithms
    algorithm_names = [algorithm.descr for algorithm in algorithms]
    return jsonify(algorithm_names)

# process an asset addition
@app.route('/<string:sitename>/add/_submit', methods=['POST'])
def add_asset_submit(sitename):
    site = Site.query.filter_by(name=sitename).one()
    type = AssetType.query.filter_by(name=request.form['type']).one()
    subtype = AssetSubtype.query.filter_by(name=request.form['subtype'], type=type).one()
    asset = Asset(subtype=subtype, name=request.form['name'], location=request.form['location'], group=request.form['group'], site=site, health=0)
    db.session.add(asset)

    print(request.form.getlist('component'))

    # select database
    LoggedEntity.__table__.info['bind_key'] = site.db_name

    # generate components
    component_list = request.form.getlist('component')
    for component_type_name in component_list:
        component_type = ComponentType.query.filter_by(name=component_type_name).one()
        component = AssetComponent(loggedentity_id=8, type=component_type, asset=asset)
        db.session.add(component)

    # set excluded algorithms
    exclusion_list = request.form.getlist('exclusion')
    for algorithm_descr in exclusion_list:
        exclusion = Algorithm.query.filter_by(descr=algorithm_descr).one()
        asset.exclusions.append(exclusion)

    # find corresponding logs
    log_list = request.form.getlist('log')
    for log_path in log_list:
        log = LoggedEntity.query.filter_by(path=log_path).one()

    #db.session.commit()
    return redirect(url_for('asset_list', sitename=sitename))

# show results for a single asset
@app.route('/<string:sitename>/results/<string:assetname>')
def result_list(sitename, assetname):
    site = Site.query.filter_by(name=sitename).one()
    asset = Asset.query.filter_by(name=assetname, site=site).one()
    recent_results = Result.query.filter_by(asset=asset, recent=True).all()
    unresolved_results = Result.query.filter_by(asset=asset, unresolved=True).all()
    return render_template('results.html', asset=asset, site=site, recent_results=recent_results, unresolved_results=unresolved_results)

# map algorithms in database
@app.route('/map')
def map_all():
    generate_algorithms()
    map_algorithms()
    return "Done"

# trigger check and get results for pre-selected asset
@app.route('/check/test')
def testcheck():
    # delete existing results table
    for result in Result.query.all():
        result.components.clear()
    Result.query.delete()
    asset = Asset.query.filter_by(id=1).first()
    check_asset(asset)
    return 'Done'

# update components belonging to an asset
@app.route('/update', methods=['POST'])
def update():
    asset = Asset.query.filter_by(name=request.values['asset']).one()

    # delete existing components
    asset.components.clear()

    # get components from POST data
    component_list = request.values.to_dict(flat=False)
    component_list.pop('asset')

    # select database
    LoggedEntity.__table__.info['bind_key'] = asset.site.db_name

    # add components to database
    for component_type_name in component_list.keys():
        component_type = ComponentType.query.filter_by(name=component_type_name).one()
        trendlog_name = component_list[component_type_name][0]
        trendlog = LoggedEntity.query.filter(LoggedEntity.path.like('%' + trendlog_name)).one()
        new_component = AssetComponent(asset=asset, type=component_type, loggedentity_id=trendlog.id)
        asset.components.append(new_component)

    db.session.commit()
    return "Done"

# grab assets from inbuildings
@app.route('/getassets')
def get_assets():
    site = Site.query.first()
    inbuildings_asset_request(site)
    return "Done"