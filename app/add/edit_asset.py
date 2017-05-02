from app import app, db, registry
from app.models import Site, Asset, LoggedEntity, PointType, AssetPoint, FunctionalDescriptor, Algorithm
from flask import request, render_template, url_for, redirect

# page to edit an asset on the site
@app.route('/site/<sitename>/edit/<asset_id>')
def edit_asset(sitename, asset_id):
    site = Site.query.filter_by(name=sitename).one()
    asset = Asset.query.filter_by(id=asset_id).one()

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
@app.route('/site/<sitename>/edit/<asset_id>/_submit', methods=['POST'])
def edit_asset_submit(sitename, asset_id):
    asset = Asset.query.filter_by(id=asset_id).one()

    # set asset attributes
    asset.name = request.form['name']
    asset.location = request.form['location']
    asset.group = request.form['group']
    asset.priority = request.form['priority']
    asset.notes = request.form['notes']

    # get database session for this site
    session = registry.get(asset.site.db_key)

    # record previous points
    old_points = list(asset.points)

    # TODO: need a better system of reading in values than string-matching point1 and log1
    # if the point was here previously, it is an input with name prev_pointX and value point.id
    # if it is a new point, it is an input with name pointX and value pointType.name
    # update points
    # just guessing that an asset won't have more than 100 points. need a more elegant solution here
    for i in range(1, 100):
        # first check if the point was previously on there
        point_id = request.form.get('prev_point' + str(i))
        if not point_id is None:
            point_id = int(point_id)
            point = AssetPoint.query.filter_by(id=point_id).one()

            # mark the point as updated
            old_points.remove(point)

            # assign the log id to the point
            log_path = request.form.get('log' + str(i))
            if not log_path == '' and not session is None:
                log = session.query(LoggedEntity).filter_by(path=log_path).one()
                point.loggedentity_id = log.id

        # otherwise check if there is a new point
        else:
            point_type_name = request.form.get('point' + str(i))
            if not point_type_name is None:
                # create the point
                point_type = PointType.query.filter_by(name=point_type_name).one()
                point = AssetPoint(type=point_type, name=point_type_name)
                asset.points.append(point)

                # assign the log id to the point
                log_path = request.form.get('log' + str(i))
                if not log_path == '' and not session is None:
                    log = session.query(LoggedEntity).filter_by(path=log_path).one()
                    point.loggedentity_id = log.id

    # delete points that have been removed
    for point in old_points:
        db.session.delete(point)

    # set functional descriptor
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
    if not session is None:
        session.close()

    return redirect(url_for('asset_list', sitename=sitename))

# delete asset
# NOTE: asset name must not be blank or will error
@app.route('/site/<sitename>/delete/<asset_id>')
def delete_asset(sitename, asset_id):
    asset = Asset.query.filter_by(id=asset_id).one()
    db.session.delete(asset)
    db.session.commit()
    return redirect(url_for('asset_list', sitename=sitename))
