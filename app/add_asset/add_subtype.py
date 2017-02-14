from app import app, db
from app.models import Site, AssetType, AssetSubtype, ComponentType, SubtypeComponent
from flask import request, render_template, url_for, redirect

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