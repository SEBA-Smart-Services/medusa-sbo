from app import app, db
from app.models import Site, AssetType, AssetSubtype, LoggedEntity, Asset, ComponentType, AssetComponent
from flask import request, render_template, url_for, redirect, flash
from openpyxl import load_workbook

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

# process an asset addition via upload
@app.route('/site/<sitename>/add/_upload', methods=['POST'])
def add_asset_upload(sitename):

    # check if file was uploaded
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('add_asset_input', sitename=sitename))
    file = request.files['file']
    if file.filename =='':
        flash('No file selected')
        return redirect(url_for('add_asset_input', sitename=sitename))

    # check if file is correct type
    if not (file and ('.' in file.filename) and (file.filename.rsplit('.',1)[1].lower() in ['xlsx','xlsm'])):
        flash('File must be xlsx/xlsm')
        return redirect(url_for('add_asset_input', sitename=sitename))

    wb = load_workbook(file)
    ws = wb.worksheets[0]
    

    site = Site.query.filter_by(name=sitename).one()

    return redirect(url_for('asset_list', sitename=sitename))

