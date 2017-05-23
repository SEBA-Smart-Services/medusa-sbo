from app.models import Asset, InbuildingsAsset, Site
from app import db, app
import requests

###################################
##  inbuildings functions
###################################

# generic inbuildings request
def inbuildings_request(data):
    # setup request parameters
    url = 'https://inbuildings.info/ingenius/rest/sbo.php'
    headers = {'content-type': 'application/x-www-urlencoded'}
    resp = requests.post(url, data = data, headers = headers)
    # parse server response into readable type
    resp_parsed = resp.json()
    return resp_parsed

# check comms with inbuildings server
def inbuildings_comms_test():
    # setup request parameters
    key = Site.query.first().inbuildings_config.key
    message = 'Comms Test'
    mode = 'raisenewjob'
    test = 'yes'
    equip_id = '0'
    priority_id = '7'
    data = {'key': key, 'mode': mode, 'test': test, 'eid': equip_id, 'pid': priority_id, 'body': message}

    # send request
    try:
        inbuildings_request(data)
    except requests.exceptions.ConnectionError:
        return False
    else:
        return True

# inbuildings asset request
def inbuildings_asset_request(site):
    # setup request parameters
    key = site.inbuildings_config.key
    mode = "equipmentlist"
    data = {'key': key, 'mode': mode}

    # send request
    try:
        resp = inbuildings_request(data)
    except requests.exceptions.ConnectionError:
        # abort if no connection
        return

    previous_assets = InbuildingsAsset.query.filter_by(site_id=site.id).all()
    current_assets = []

    # either update existing record or create new record
    for asset in resp:
        db_asset = InbuildingsAsset.query.filter_by(id=asset['eid']).first()
        if db_asset is None:
            db_asset = InbuildingsAsset(id=asset['eid'], site=site)
            db.session.add(db_asset)
        db_asset.name = asset['name']
        db_asset.location = asset['location']
        db_asset.group = asset['group']
        current_assets.append(db_asset)

        # attempt to match to medusa assets based on name
        medusa_asset = Asset.query.filter_by(name=db_asset.name, site=site).first()
        if db_asset.asset is None and not medusa_asset is None:
            db_asset.asset = medusa_asset

    # delete non-existent assets
    for db_asset in set(previous_assets)-set(current_assets):
        db.session.delete(db_asset)

    db.session.commit()

# request assets for all sites
def request_all_sites():
    for site in Site.query.all():
        inbuildings_asset_request(site)

# raise a new job
def inbuildings_raise_job(asset, message, priority):
    # setup request parameters
    key = asset.site.inbuildings_config.key
    mode = "raisenewjob"
    # if an inbuildings asset is linked, use the eid from that
    if not asset.inbuildings is None:
        equip_id = str(asset.inbuildings.id)
    # otherwise stick the asset name in the message
    else:
        message = asset.name + ": " + message
        equip_id = ""
    priority_id = str(priority)
    data = {'key': key, 'mode': mode, 'eid': equip_id, 'pid': priority_id, 'body': message}

    # send request
    try:
        inbuildings_request(data)
    except requests.exceptions.ConnectionError:
        # abort if no connection
        return
