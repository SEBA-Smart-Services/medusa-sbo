from flask import request, render_template, url_for, redirect, jsonify
from app import app, db
from app.models import Site
from app.ict.models import ITasset

# list IT assets on the site
@app.route('/site/<sitename>/it-assets',  methods=['GET', 'POST'])
def ict_asset_list(sitename):
    site = Site.query.filter_by(name=sitename).one()
    #ict assets currently stored in Assets model. change to new model
    #ict_asset_type=AssetType.query.filter_by(name='ICT').one()
    #assets=Asset.query.filter_by(site=site, type=ict_asset_type).all()
    itassets=site.it_assets
    return render_template('it-assets.html', site=site, ict_assets=itassets)


@app.route('/_reload_it_data/<int:site_id>')
def reload_it_data(site_id):
    return jsonify(
        test='returned'
    )
