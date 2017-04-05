from app import app, db, registry
from app.models import Site, Asset, LoggedEntity, PointType, AssetPoint, FunctionalDescriptor, Algorithm
from flask import request, render_template, url_for, redirect

# page to edit an asset on the site
@app.route('/site/<sitename>/edit/<assetname>')
def edit_asset(sitename, assetname):
    site = Site.query.filter_by(name=sitename).one()
    asset = Asset.query.filter(Asset.name == assetname, Asset.site.has(name=sitename)).one()

    # get database session for this site
    session = registry.get(site.db_key)

    # set available logs
    if not session is None:
        logs = session.query(LoggedEntity).filter_by(type='trend.ETLog').all()
        session.close()
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
    session = registry.get(asset.site.db_key)

    # @@ need a better system of reading in values than string-matching point1 and log1
    # assign log ids to points
    for i in range(1, len(asset.points) + 1):
        point_type_name = request.form.get('point' + str(i))
        point_type = PointType.query.filter_by(name=point_type_name).one()
        point = AssetPoint.query.filter_by(type=point_type, asset=asset).one()
        log_path = request.form.get('log' + str(i))
        if not log_path is None and not session is None:
            log = session.query(LoggedEntity).filter_by(path=log_path).one()
            point.loggedentity_id = log.id
            session.close()

    # set process functions
    asset.functions.clear()
    function_list = request.form.getlist('function')
    for function_name in function_list:
        function = FunctionalDescriptor.query.filter_by(name=function_name).one()
        asset.functions.append(function)

    # set excluded algorithms
    asset.exclusions.clear()
    inclusions = []
    included_list = request.form.getlist('algorithm')
    for algorithm_descr in included_list:
        inclusions.append(Algorithm.query.filter_by(descr=algorithm_descr).one())
    exclusions = set(Algorithm.query.all()) - set(inclusions)
    asset.exclusions.extend(exclusions)

    db.session.commit()

    return redirect(url_for('asset_list', sitename=sitename))

# delete asset
@app.route('/site/<sitename>/delete/<assetname>')
def delete_asset(sitename, assetname):
    asset = Asset.query.filter(Asset.name == assetname, Asset.site.has(name=sitename)).one()
    db.session.delete(asset)
    db.session.commit()
    return redirect(url_for('asset_list', sitename=sitename))
