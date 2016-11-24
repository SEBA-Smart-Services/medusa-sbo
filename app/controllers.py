from app import app, db
from app.models import Asset, Site, AssetComponent, AssetType, Algorithm, AssetHealth, AssetSubtype, ComponentType, Result, SubtypeComponent, LoggedEntity, LogTimeValue
from app.algorithms import check_asset
from flask import json, request, render_template, url_for, redirect, jsonify


###################################
## endpoints
###################################

@app.route('/')
def main():
    return redirect(url_for('asset_list', sitename='TestSite'))

# set homepage for the site
@app.route('/site/<string:sitename>')
def homepage(sitename):
    return redirect(url_for('asset_list', sitename=sitename))

# list assets on the site
@app.route('/site/<string:sitename>/assets')
def asset_list(sitename):
    site = Site.query.filter_by(name=sitename).one()
    return render_template('assets.html', assets=site.assets, site=site)

# list unresolved issues on the site
@app.route('/site/<string:sitename>/unresolved')
def unresolved_list(sitename):
    site = Site.query.filter_by(name=sitename).one()
    results = Result.query.filter_by(unresolved=True).all()
    return render_template('unresolved.html', results=results, site=site)

# page to add an asset to the site
@app.route('/site/<string:sitename>/add')
def add_asset_input(sitename):
    site = Site.query.filter_by(name=sitename).one()
    asset_types = AssetType.query.all()
    return render_template('add.html', site=site, asset_types=asset_types)

# return list of subtypes through AJAX
@app.route('/site/<string:sitename>/add/_subtype')
def return_subtypes(sitename):
    asset_type_name = request.args.get('type', '')
    asset_type = AssetType.query.filter_by(name=asset_type_name).one()
    subtypes = AssetSubtype.query.filter_by(type=asset_type)
    subtype_names = [subtype.name for subtype in subtypes]
    return jsonify(subtype_names)

# return list of loggedentities through AJAX
@app.route('/site/<string:sitename>/add/_loggedentity')
def return_loggedentities(sitename):
    site = Site.query.filter_by(name=sitename).one()

    # select database
    LoggedEntity.__table__.info['bind_key'] = site.db_name

    logs = LoggedEntity.query.filter_by(type='trend.ETLog').all()
    log_paths = [log.path for log in logs]
    return jsonify(log_paths)

# return list of components through AJAX
@app.route('/site/<string:sitename>/add/_component')
def return_components(sitename):
    asset_type_name = request.args.get('type', '')
    asset_type = AssetType.query.filter_by(name=asset_type_name).one()
    subtype_name = request.args.get('subtype', '')
    subtype = AssetSubtype.query.filter_by(name=subtype_name, type=asset_type).one()
    components = subtype.components
    component_names = [component.type.name for component in components]
    return jsonify(component_names)

# return list of algorithms to exclude through AJAX
@app.route('/site/<string:sitename>/add/_exclusion')
def return_exclusions(sitename):
    asset_type_name = request.args.get('type', '')
    asset_type = AssetType.query.filter_by(name=asset_type_name).one()
    subtype_name = request.args.get('subtype', '')
    subtype = AssetSubtype.query.filter_by(name=subtype_name, type=asset_type).one()
    algorithms = subtype.algorithms
    algorithm_names = [algorithm.descr for algorithm in algorithms]
    return jsonify(algorithm_names)

# process an asset addition
@app.route('/site/<string:sitename>/add/_submit', methods=['POST'])
def add_asset_submit(sitename):
    site = Site.query.filter_by(name=sitename).one()
    type = AssetType.query.filter_by(name=request.form['type']).one()
    subtype = AssetSubtype.query.filter_by(name=request.form['subtype'], type=type).one()
    asset = Asset(subtype=subtype, name=request.form['name'], location=request.form['location'], group=request.form['group'], site=site, health=0)
    db.session.add(asset)

    # select database
    LoggedEntity.__table__.info['bind_key'] = site.db_name

    # @@ need a better system of reading in values than string-matching component1 and log1
    # generate components
    for i in range(1, len(subtype.components) + 1):
        component_type_name = request.form.get('component' + str(i))
        if not component_type_name is None:
            component_type = ComponentType.query.filter_by(name=component_type_name).one()
            component = AssetComponent(type=component_type, asset=asset)
            log_path = request.form.get('log' + str(i))
            if not log_path is None:
                log = LoggedEntity.query.filter_by(path=log_path).one()
                component.loggedentity_id = log.id
            db.session.add(component)

    # set excluded algorithms
    exclusion_list = request.form.getlist('exclusion')
    for algorithm_descr in exclusion_list:
        exclusion = Algorithm.query.filter_by(descr=algorithm_descr).one()
        asset.exclusions.append(exclusion)

    db.session.commit()
    return redirect(url_for('asset_list', sitename=sitename))

# show results for a single asset
@app.route('/site/<string:sitename>/results/<string:assetname>')
def result_list(sitename, assetname):
    site = Site.query.filter_by(name=sitename).one()
    asset = Asset.query.filter_by(name=assetname, site=site).one()
    recent_results = Result.query.filter_by(asset=asset, recent=True).all()
    unresolved_results = Result.query.filter_by(asset=asset, unresolved=True).all()
    return render_template('results.html', asset=asset, site=site, recent_results=recent_results, unresolved_results=unresolved_results)