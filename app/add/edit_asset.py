from app import app, db, registry
from app.models import Site, Asset, LoggedEntity, ComponentType, AssetComponent
from flask import request, render_template, url_for, redirect

# page to edit an asset on the site
@app.route('/site/<sitename>/edit/<assetname>')
def edit_asset(sitename, assetname):
    site = Site.query.filter_by(name=sitename).one()
    asset = Asset.query.filter(Asset.name == assetname, Asset.site.has(name=sitename)).one()

    # get database session for this site
    session = registry.get(site.db_name)

    # set available logs
    if not session is None:
        logs = session.query(LoggedEntity).filter_by(type='trend.ETLog').all()
    else:
        logs = []

    return render_template('edit_asset.html', site=site, asset=asset, logs=logs)

# process an asset edit
@app.route('/site/<sitename>/edit/<assetname>/_submit', methods=['POST'])
def edit_asset_submit(sitename, assetname):
    asset = Asset.query.filter(Asset.name == assetname, Asset.site.has(name=sitename)).one()

    # set asset attributes
    asset.name = request.form['name']
    asset.location = request.form['location']
    asset.group = request.form['group']
    asset.priority = request.form['priority']
    
    # get database session for this site
    session = registry.get(site.db_name)

    # @@ need a better system of reading in values than string-matching component1 and log1
    # assign log ids to components
    for i in range(1, len(asset.components) + 1):
        component_type_name = request.form.get('component' + str(i))
        component_type = ComponentType.query.filter_by(name=component_type_name).one()
        component = AssetComponent.query.filter_by(type=component_type, asset=asset).one()
        log_path = request.form.get('log' + str(i))
        if not log_path and not session is None:
            log = LoggedEntity.query.filter_by(path=log_path).one()
            component.loggedentity_id = log.id

    # set process functions
    asset.functions.clear()
    function_list = request.form.getlist('function')
    for function_name in function_list:
        function = AssetFunction.query.filter_by(name=function_name).one()
        asset.functions.append(function)

    # set excluded algorithms
    asset.exclusions.clear()
    exclusion_list = request.form.getlist('exclusion')
    for algorithm_descr in exclusion_list:
        exclusion = Algorithm.query.filter_by(descr=algorithm_descr).one()
        asset.exclusions.append(exclusion)

    db.session.commit()
    return redirect(url_for('asset_list', sitename=sitename))

# delete asset
@app.route('/site/<sitename>/delete/<assetname>')
def delete_asset(sitename, assetname):
    asset = Asset.query.filter(Asset.name == assetname, Asset.site.has(name=sitename)).one()
    db.session.delete(asset)
    db.session.commit()
    return redirect(url_for('asset_list', sitename=sitename))
