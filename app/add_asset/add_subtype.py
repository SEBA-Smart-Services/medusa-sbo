from app import app, db
from app.models import AssetType, AssetSubtype, ComponentType, SubtypeComponent
from flask import request, render_template, url_for, redirect

# page to add an asset subtype to the site
@app.route('/site/all/add_subtype')
def add_subtype():
    asset_types = AssetType.query.all()
    component_type_list = ComponentType.query.all()
    return render_template('add_subtype.html', asset_types=asset_types, component_type_list=component_type_list, allsites=True)

# process an subtype addition
@app.route('/site/all/add_subtype/_submit', methods=['POST'])
def add_subtype_submit():

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
    return redirect(url_for('homepage_all'))