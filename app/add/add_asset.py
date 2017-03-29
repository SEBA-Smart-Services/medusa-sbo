from app import app, db, registry
from app.models import Site, AssetType, AssetSubtype, LoggedEntity, Asset, ComponentType, AssetComponent, SubtypeComponent
from flask import request, render_template, url_for, redirect, flash, send_file, make_response, jsonify
from openpyxl import load_workbook, Workbook
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter
from openpyxl.writer.excel import save_virtual_workbook
from io import BytesIO
from xml.etree.ElementTree import ElementTree, Element, SubElement

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

    # get database session for this site
    session = registry.get(site.db_name)

    if not session is None:
        logs = session.query(LoggedEntity).filter_by(type='trend.ETLog').all()
        log_paths = [log.path for log in logs]
    else:
        log_paths = []
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

    # get database session for this site
    session = registry.get(site.db_name)

    if not session is None:

        # create asset with 0 health
        site = Site.query.filter_by(name=sitename).one()
        subtype = AssetSubtype.query.filter_by(name=request.form['subtype']).one()
        asset = Asset(subtype=subtype, name=request.form['name'], location=request.form['location'], group=request.form['group'], priority=request.form['priority'], site=site, health=0)
        db.session.add(asset)
    
        # @@ need a better system of reading in values than string-matching component1 and log1
        # generate components
        for i in range(1, len(subtype.components) + 1):
            component_type_name = request.form.get('component' + str(i))
            component_type = ComponentType.query.filter_by(name=component_type_name).one()
            component = AssetComponent(type=component_type, asset=asset, name=component_type_name)
            log_path = request.form.get('log' + str(i))
            print(log_path)
            if not log_path is None:
                log = session.query(LoggedEntity).filter_by(path=log_path).one()
                component.loggedentity_id = log.id
            db.session.add(component)

        # set excluded algorithms
        exclusion_list = request.form.getlist('exclusion')
        for algorithm_descr in exclusion_list:
            exclusion = Algorithm.query.filter_by(descr=algorithm_descr).one()
            asset.exclusions.append(exclusion)

        db.session.commit()

    return redirect(url_for('asset_list', sitename=sitename))

# generate a downloadable Excel template for uploading assets
@app.route('/site/<sitename>/add/_download')
def add_asset_download(sitename):

    wb = Workbook()
    ws_input = wb.worksheets[0]

    # generate input page
    ws_input.title = "Input"
    ws_input['A1'] = "Name"
    ws_input['B1'] = "Location"
    ws_input['C1'] = "Group"
    ws_input['D1'] = "Type"
    ws_input['E1'] = "Subtype"
    ws_input['F1'] = "Priority"

    # generate page with all the options (for data validation)
    ws_options = wb.create_sheet("Options")
    x = 1
    for asset_type in AssetType.query.all():
        ws_options.cell(column=x, row=1).value = asset_type.name
        y = 2
        for subtype in asset_type.subtypes:
            ws_options.cell(column=x, row=y).value = subtype.name
            y += 1
        x += 1
        wb.create_named_range(asset_type.name, ws_options, "${}$2:${}${}".format(get_column_letter(x-1), get_column_letter(x-1), y-1))
    cols = len(tuple(ws_options.columns))
    wb.create_named_range("Types", ws_options, '$A$1:${}$1'.format(get_column_letter(cols)))

    # apply data validation to input page
    type_dv = DataValidation(type='list', formula1='Types', allow_blank=True)
    subtype_dv = DataValidation(type='list', formula1='INDIRECT(INDIRECT(ADDRESS(ROW(), COLUMN()-1)))', allow_blank=True)
    priority_dv = DataValidation(type='whole', operator='between', formula1=0, formula2=9)
    ws_input.add_data_validation(type_dv)
    ws_input.add_data_validation(subtype_dv)
    ws_input.add_data_validation(priority_dv)
    type_dv.ranges.append('D2:D1000')
    subtype_dv.ranges.append('E2:E1000')
    priority_dv.ranges.append('F2:F1000')

    # save file
    out = BytesIO(save_virtual_workbook(wb))

    # prevent browser from caching the download
    response = make_response(send_file(out, attachment_filename='Template.xlsx', as_attachment=True))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

# process an asset addition via upload
@app.route('/site/<sitename>/add/_upload', methods=['POST'])
def add_asset_upload(sitename):

    site = Site.query.filter_by(name=sitename).one()

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

    # generate asset for each non-blank row in the worksheet
    asset_list = []
    for row in tuple(ws.rows)[1:]:
        if not row[0].value is None and not row[3].value is None and not row[4].value is None and not row[5].value is None:
            name = row[0].value
            location = row[1].value
            if location is None:
                location = ""
            group = row[2].value
            if group is None:
                group = ""
            type_name = row[3].value
            subtype_name = row[4].value
            priority = row[5].value
            asset_type = AssetType.query.filter_by(name=type_name).one()
            subtype = AssetSubtype.query.filter_by(name=subtype_name, type=asset_type).one()
            asset = Asset(name=name, location=location, group=group, subtype=subtype, priority=priority, site=site, health=0)

            db.session.add(asset)
            asset_list.append(asset)

    # generate components
    for subtype_component in subtype.components:
        component = AssetComponent(type=subtype_component.type, asset=asset, name=subtype_component.type.name)

        # set destination folder
        component.loggedentity_path = "/Server 1/Medusa/Trends/{}/{} Extended".format(asset.name, component.name)

        db.session.add(component)

    db.session.commit()

    # generate xml import to SBO
    object_set = Element('ObjectSet')
    object_set.attrib = {'ExportMode':'Standard', 'Version':'1.8.1.87', 'Note':'TypesFirst'}
    exported_objects = SubElement(object_set, 'ExportedObjects')
    for asset in asset_list:
        oi_folder = SubElement(exported_objects, 'OI')
        oi_folder.attrib = {'NAME':asset.name, 'TYPE':'system.base.Folder'}
        for component in asset.components:
            oi_trend = SubElement(oi_folder, 'OI')
            oi_trend.attrib = {'NAME':'{} Extended'.format(component.name), 'TYPE':'trend.ETLog'}
            pi = SubElement(oi_trend, 'PI')
            pi.attrib = {'Name':'IncludeInReports', 'Value':'1'}

    # save file
    out = BytesIO()
    tree = ElementTree(object_set)
    tree.write(out, encoding='utf-8', xml_declaration=True)
    out.seek(0)

    # prevent browser from caching the download
    response = make_response(send_file(out, attachment_filename='Import.xml', as_attachment=True))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response