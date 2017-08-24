from flask import request, render_template, url_for, redirect, jsonify
from app import app, db
from app.models import Site
from app.ict.models import ITasset
from app.ict.salt_client import SaltAPI

# list IT assets on the site
@app.route('/site/<sitename>/it-assets',  methods=['GET', 'POST'])
def ict_asset_list(sitename):
    site = Site.query.filter_by(name=sitename).one()
    itassets=site.it_assets
    return render_template('it-assets.html', site=site, ict_assets=itassets)


@app.route('/_reload_it_data/<int:site_id>')
def reload_it_data(site_id):
    return jsonify(
        test='returned'
    )

@app.route('/site/<sitename>/it-assets/_refresh',  methods=['GET', 'POST'])
def update_minion_data(sitename):
    site = Site.query.filter_by(name=sitename).one()
    itassets=site.it_assets

    api = SaltAPI()
    api.login()
    for ITasset in itassets:
        data = api.get_minion_grains(ITasset.minion_name)
        ipaddress = data["ipv4"][0] #  the grain returns the ip address in a list. maybe it can send multiple addresses?
        operatingsystem = data["osfullname"]
        onlinestatus = api.is_minion_reachable(ITasset.minion_name)
        ITasset.ip_address=ipaddress
        ITasset.operating_system=operatingsystem

    api.logout()
    db.session.commit()
    return redirect(url_for('ict_asset_list', sitename=site.name))
