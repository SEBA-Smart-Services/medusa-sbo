from flask import request, render_template, url_for, redirect, jsonify
from app import app, db
from app.models import Site
from app.ict.models import ITasset
from app.ict.salt_client import SaltAPI
import datetime
from app.ict.forms import AddITAssetForm, EditITAssetForm
from flask_wtf import Form
from wtforms import TextField, PasswordField, validators

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

@app.route('/site/<sitename>/add_it_asset',  methods=['GET', 'POST'])
def add_itasset(sitename):
    site = Site.query.filter_by(name=sitename).one()
    form = AddITAssetForm()
    error = ""
    if request.method == 'GET':
        return render_template('add_it_asset.html', form=form, site=site, error=error)
    # process a submitted form
    elif request.method == 'POST':
        # if form has errors, return the page (errors will display)
        if not form.validate_on_submit():
            return render_template('add_it_asset.html', form=form, site=site, error=error)

        #get the data from the form
        minion_site_name=form.site.data
        minion_device_type=form.device_type.data
        minion_device_number=form.device_number.data

        #concatenate the data into a minion name
        minion_name=minion_site_name+"-"+minion_device_type
        if minion_device_number!="": #this was an optional field so might be empty
           minion_name=minion_name+"-"+minion_device_number

        #check if a minion with this name already exists in the database
        if ITasset.query.filter_by(minion_name=minion_name).count():
            #a minion with this name already exists which is illegal
            error="An asset with this name already exists"
            return render_template('add_it_asset.html', form=form, site=site, error=error)

        #create new it_asset object in the db
        it_asset=ITasset()
        it_asset.minion_name=minion_name
        it_asset.site_id=site.id
        db.session.add(it_asset)
        db.session.commit()
    #success go to it asset details
    return redirect(url_for('itasset_details', sitename=site.name, minion_id=it_asset.id))

@app.route('/site/<sitename>/delete_itasset/<minion_id>')
def delete_itasset(sitename, minion_id):
    itasset = ITasset.query.filter_by(id=minion_id).one()
    db.session.delete(itasset)
    db.session.commit()
    return redirect(url_for('asset_list', sitename=sitename))

@app.route('/site/<sitename>/itasset_details/<minion_id>')
def itasset_details(sitename, minion_id):
    error=""
    site = Site.query.filter_by(name=sitename).one()
    itasset = ITasset.query.filter_by(id=minion_id).one()
    return render_template('it_asset_details.html', ITasset=itasset, site=site)

@app.route('/site/<sitename>/rescan_itasset/<minion_id>',  methods=['GET', 'POST'])
def update_one_minion_data(sitename, minion_id):
    itasset=ITasset.query.filter_by(id=minion_id).one()
    api = SaltAPI()
    api.login()
    error=""
    #first check if minion is online.
    onlinestatus = api.is_minion_reachable(itasset.minion_name)
    itasset.online = onlinestatus
    now = datetime.datetime.now()
    itasset.last_checked = now.strftime('%Y-%m-%d %H:%M:%S')
    #only get grains if minion is online
    if onlinestatus == True:
        data = api.get_minion_grains(itasset.minion_name)
        ipaddress = data["ipv4"][0] #  the grain returns the ip address in a list. maybe it can send multiple addresses?
        operatingsystem = data["osfullname"]
        itasset.ip_address=ipaddress
        itasset.operating_system=operatingsystem
    api.logout()
    db.session.commit()
    return redirect(url_for('itasset_details', sitename=sitename, minion_id=itasset.id))


# page to edit an it asset on the site
@app.route('/site/<sitename>/itasset_edit/<minion_id>', methods=['GET', 'POST'])
def edit_itasset(sitename, minion_id):
    site = Site.query.filter_by(name=sitename).one()
    itasset = ITasset.query.filter_by(id=minion_id).one()
    error=""
    if request.method == 'GET':
        # prepopulate form from asset attributes
        form = EditITAssetForm(obj=itasset)
        return render_template('edit_it_asset.html', site=site, ITasset=itasset, form=form, error=error)

    elif request.method == 'POST':
        form = EditITAssetForm()

        # if form has errors, return the page (errors will display)
        if not form.validate_on_submit():
            return render_template('edit_it_asset.html', site=site, ITasset=itasset, form=form, error=error)

        minion_name=form.minion_name.data


        # set itasset attributes based on form
        form.populate_obj(itasset)
        #concatenate the data into a minion name

        db.session.commit()

        #redirect to scan the minion with updated details
        #end of the scan will redirect back to the minion details page
        return redirect(url_for('update_one_minion_data', sitename=sitename, minion_id=itasset.id))

@app.route('/site/<sitename>/itasset_acceptkey/<minion_id>', methods=['GET', 'POST'])
def acceptkey_itasset(sitename, minion_id):
    site = Site.query.filter_by(name=sitename).one()
    itasset = ITasset.query.filter_by(id=minion_id).one()
    error=""
    api=SaltAPI()
    api.login()
    accepted_minions, unaccepted_minions = api.get_salt_minion_keys()

    if itasset.minion_name in accepted_minions:
        #if the minion key has already been accepted in the salt master:
        error = "IT asset is alread connected to the cloud"
        itasset.minion_key_accepted=True
        db.session.commit()
        return redirect(url_for('itasset_details', sitename=sitename, minion_id=itasset.id))
    elif itasset.minion_name in unaccepted_minions:
        #if the minion key is unaccepted in the salt master, it needs to be accepted:
        ret = api.accept_salt_minion_key(itasset.minion_name)
        if ret == False:
            #if minion key fails to accept
            error = "IT asset failed connect to the cloud"
            itasset.minion_key_accepted=False
            db.session.commit()
            return redirect(url_for('itasset_details', sitename=sitename, minion_id=itasset.id))
        elif ret == True:
            # if minion key successfully accepts
            error = "IT asset successfully connected to the cloud"
            itasset.minion_key_accepted=True
            db.session.commit()
            return redirect(url_for('itasset_details', sitename=sitename, minion_id=itasset.id))
    else:
    #else, if the minion key isnt in the salt master:
        error = "IT asset failed connect to the cloud"
        itasset.minion_key_accepted=False
        db.session.commit()
        return redirect(url_for('itasset_details', sitename=sitename, minion_id=itasset.id))
