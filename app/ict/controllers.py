from flask import request, render_template, url_for, redirect, jsonify
from app import app, db
from app.models import Site
from app.ict.models import ITasset
from app.ict.salt_client import SaltAPI
import datetime
# list IT assets on the site
@app.route('/site/<sitename>/it-assets',  methods=['GET', 'POST'])
def ict_asset_list(sitename):
    site = Site.query.filter_by(name=sitename).one()
    itassets=site.it_assets
    return render_template('it-assets.html', site=site, ict_assets=itassets)


@app.route('/site/<sitename>/assets/_rescan-minion-data',  methods=['GET', 'POST'])
def update_minion_data(sitename):
    site = Site.query.filter_by(name=sitename).one()
    itassets=site.it_assets

    api = SaltAPI()
    api.login()
    for ITasset in itassets:
        #first check if minion is online.
        onlinestatus = api.is_minion_reachable(ITasset.minion_name)
        ITasset.online = onlinestatus
        now = datetime.datetime.now()
        ITasset.last_checked = now.strftime('%Y-%m-%d %H:%M:%S')
        #only get grains if minion is online
        if onlinestatus == True:
            data = api.get_minion_grains(ITasset.minion_name)
            ipaddress = data["ipv4"][0] #  the grain returns the ip address in a list. maybe it can send multiple addresses?
            operatingsystem = data["osfullname"]
            ITasset.ip_address=ipaddress
            ITasset.operating_system=operatingsystem
    api.logout()
    db.session.commit()
    return redirect(url_for('asset_list', sitename=site.name))
