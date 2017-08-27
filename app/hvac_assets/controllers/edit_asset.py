from app import app, db
from app.models import Site, Asset, AssetType, LoggedEntity, PointType, AssetPoint, FunctionalDescriptor, Algorithm
from app.forms import EditAssetForm
from flask import request, render_template, url_for, redirect

# page to edit an asset on the site
@app.route('/site/<sitename>/edit/<asset_id>', methods=['GET', 'POST'])
def edit_asset(sitename, asset_id):

    site = Site.query.filter_by(name=sitename).one()
    asset = Asset.query.filter_by(id=asset_id).one()
    asset_types = AssetType.query.all()

    if request.method == 'GET':
        # prepopulate form from asset attributes
        form = EditAssetForm(obj=asset)

        # get database session for this site
        # session = registry.get(site.db_key)

        # grab logs from remote webreports database
        # if not session is None:
        #     logs = session.query(LoggedEntity).filter_by(type='trend.ETLog').all()
        #     session.close()
        # else:
        #     logs = []
        logs = []

        return render_template('edit_asset.html', site=site, asset_types=asset_types, asset=asset, logs=logs, form=form)

    elif request.method == 'POST':
        form = EditAssetForm()

        # if form has errors, return the page (errors will display)
        if not form.validate_on_submit():
            # get database session for this site
            # session = registry.get(site.db_key)

            # grab logs from remote webreports database
            # if not session is None:
            #     logs = session.query(LoggedEntity).filter_by(type='trend.ETLog').all()
            #     session.close()
            # else:
            #     logs = []
            logs = []

            return render_template('edit_asset.html', site=site, asset=asset, logs=logs, form=form)

        # set asset attributes based on form
        form.populate_obj(asset)

        # get database session for this site
        session = db.session

        # record previous points. points that still exist will be removed from this list as we go along
        old_points = list(asset.points)

        # read in points and their corresponding logs in the same manner as in add_asset
        # one difference, is that we have to preserve previous points
        # if the point was here previously, it is an input with name prev_pointX and value point.id
        # if it is a new point, it is an input with name pointX and value pointType.name
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

        # delete points that no longer exist
        for point in old_points:
            db.session.delete(point)

        # set functional descriptor
        asset.functions.clear()
        function_list = request.form.getlist('function')
        for function_name in function_list:
            function = FunctionalDescriptor.query.filter_by(name=function_name).one()
            asset.functions.append(function)

        # set excluded algorithms
        # the database operates via excluding algorithms
        # however the form only sends through algorithms that are ticked (i.e. included)
        # therefore subtract the inclusions from the total set of algorithms to get the exclusions
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
