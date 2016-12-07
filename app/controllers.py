from app import app, db
from app.models import Asset, Site, AssetComponent, AssetType, Algorithm, AssetSubtype, ComponentType, Result, SubtypeComponent, LoggedEntity, LogTimeValue
from app.algorithms import check_asset
from flask import json, request, render_template, url_for, redirect, jsonify

###################################
## main pages
###################################

@app.route('/')
def main():
    return redirect(url_for('asset_list', sitename='TestSite'))

# set homepage for the site
@app.route('/site/<sitename>')
def homepage(sitename):
    return redirect(url_for('asset_list', sitename=sitename))

# list assets on the site
@app.route('/site/<sitename>/assets')
def asset_list(sitename):
    site = Site.query.filter_by(name=sitename).one()
    return render_template('assets.html', assets=site.assets, site=site)

# list unresolved issues on the site
@app.route('/site/<sitename>/unresolved')
def unresolved_list(sitename):
    site = Site.query.filter_by(name=sitename).one()
    results = Result.query.filter(Result.status_id > 1, Result.status_id < 5).all()
    return render_template('unresolved.html', results=results, site=site)

# show results for a single asset
@app.route('/site/<sitename>/results/<assetname>')
def result_list(sitename, assetname):
    site = Site.query.filter_by(name=sitename).one()
    asset = Asset.query.filter_by(name=assetname, site=site).one()
    recent_results = Result.query.filter_by(asset=asset, recent=True).all()
    unresolved_results = Result.query.filter(Result.asset==asset, Result.status_id > 1, Result.status_id < 5).all()
    return render_template('results.html', asset=asset, site=site, recent_results=recent_results, unresolved_results=unresolved_results)


###################################
## add asset
###################################

# page to add an asset to the site
@app.route('/site/<sitename>/add_asset')
def add_asset_input(sitename):
    site = Site.query.filter_by(name=sitename).one()
    asset_types = AssetType.query.all()
    return render_template('add_asset.html', site=site, asset_types=asset_types)

# return list of subtypes through AJAX
@app.route('/site/<sitename>/add/_subtype')
def return_subtypes(sitename):
    subtypes = AssetSubtype.query.filter(AssetSubtype.type.has(name=request.args['type']))
    subtype_names = [subtype.name for subtype in subtypes]
    return jsonify(subtype_names)

# return list of loggedentities through AJAX
@app.route('/site/<sitename>/add/_loggedentity')
def return_loggedentities(sitename):
    site = Site.query.filter_by(name=sitename).one()

    # select database
    LoggedEntity.__table__.info['bind_key'] = site.db_name

    logs = LoggedEntity.query.filter_by(type='trend.ETLog').all()
    log_paths = [log.path for log in logs]
    return jsonify(log_paths)

# return list of components through AJAX
@app.route('/site/<sitename>/add/_component')
def return_components(sitename):
    subtype = AssetSubtype.query.filter_by(name=request.args['subtype']).one()
    component_names = [component.type.name for component in subtype.components]
    return jsonify(component_names)

# return list of algorithms to exclude through AJAX
@app.route('/site/<sitename>/add/_exclusion')
def return_exclusions(sitename):
    subtype = AssetSubtype.query.filter_by(name=request.args['subtype']).one()
    algorithm_names = [algorithm.descr for algorithm in subtype.algorithms]
    return jsonify(algorithm_names)

# process an asset addition
@app.route('/site/<sitename>/add/_submit', methods=['POST'])
def add_asset_submit(sitename):

    # create asset with 0 health
    site = Site.query.filter_by(name=sitename).one()
    subtype = AssetSubtype.query.filter_by(name=request.form['subtype']).one()
    asset = Asset(subtype=subtype, name=request.form['name'], location=request.form['location'], group=request.form['group'], priority=request.form['priority'], site=site, health=0)
    db.session.add(asset)

    # select database
    LoggedEntity.__table__.info['bind_key'] = site.db_name

    # @@ need a better system of reading in values than string-matching component1 and log1
    # generate components
    for i in range(1, len(subtype.components) + 1):
        component_type_name = request.form.get('component' + str(i))
        component_type = ComponentType.query.filter_by(name=component_type_name).one()
        component = AssetComponent(type=component_type, asset=asset, name=component_type_name)
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


###################################
## edit asset
###################################

# page to edit an asset on the site
@app.route('/site/<sitename>/edit/<assetname>')
def edit_asset(sitename, assetname):
    site = Site.query.filter_by(name=sitename).one()
    asset = Asset.query.filter(Asset.name == assetname, Asset.site.has(name=sitename)).one()

    # set available logs
    LoggedEntity.__table__.info['bind_key'] = site.db_name
    logs = LoggedEntity.query.filter_by(type='trend.ETLog').all()

    return render_template('edit.html', site=site, asset=asset, logs=logs)

# process an asset edit
@app.route('/site/<sitename>/edit/<assetname>/_submit', methods=['POST'])
def edit_asset_submit(sitename, assetname):
    asset = Asset.query.filter(Asset.name == assetname, Asset.site.has(name=sitename)).one()

    # set asset attributes
    asset.name = request.form['name']
    asset.location = request.form['location']
    asset.group = request.form['group']
    asset.priority = request.form['priority']
    
    # select database
    LoggedEntity.__table__.info['bind_key'] = asset.site.db_name

    # @@ need a better system of reading in values than string-matching component1 and log1
    # assign log ids to components
    for i in range(1, len(asset.components) + 1):
        component_type_name = request.form.get('component' + str(i))
        component_type = ComponentType.query.filter_by(name=component_type_name).one()
        component = AssetComponent.query.filter_by(type=component_type, asset=asset).one()
        log_path = request.form.get('log' + str(i))
        if not log_path is None:
            log = LoggedEntity.query.filter_by(path=log_path).one()
            component.loggedentity_id = log.id

    # set excluded algorithms
    asset.exclusions.clear()
    exclusion_list = request.form.getlist('exclusion')
    for algorithm_descr in exclusion_list:
        exclusion = Algorithm.query.filter_by(descr=algorithm_descr).one()
        asset.exclusions.append(exclusion)

    db.session.commit()
    return redirect(url_for('asset_list', sitename=sitename))


###################################
## delete asset
###################################

# delete asset
@app.route('/site/<sitename>/delete/<assetname>')
def delete_asset(sitename, assetname):
    asset = Asset.query.filter(Asset.name == assetname, Asset.site.has(name=sitename)).one()
    db.session.delete(asset)
    db.session.commit()
    return redirect(url_for('asset_list', sitename=sitename))


###################################
## add subtype
###################################

# page to add an asset subtype to the site
@app.route('/site/<sitename>/add_subtype')
def add_subtype(sitename):
    site = Site.query.filter_by(name=sitename).one()
    asset_types = AssetType.query.all()
    component_type_list = ComponentType.query.all()
    return render_template('add_subtype.html', site=site, asset_types=asset_types, component_type_list=component_type_list)

# process an asset addition
@app.route('/site/<sitename>/add_subtype/_submit', methods=['POST'])
def add_subtype_submit(sitename):

    # create subtype
    type = AssetType.query.filter_by(name=request.form['type']).one()
    subtype = AssetSubtype(type=type, name=request.form['name'])
    db.session.add(subtype)

    # generate components
    for component_type_name in request.form.getlist('component'):
        component_type = ComponentType.query.filter_by(name=component_type_name).one()
        component = SubtypeComponent(type=component_type, subtype=subtype, name=component_type_name)
        db.session.add(component)

    db.session.commit()
    return redirect(url_for('asset_list', sitename=sitename))