from app.models import InbuildingsAsset, Site
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
def inbuildings_test():
    # setup request parameters
    #key = '0P8q1M8x8k1K4m7t8H2g5E1d8d5A4h3e1h2d9J3U3R7h2V9q9L6R6x8n9W4l3K9o6F1e8e6N7g4w7d1B2T1C6K9u6H9I4Y9b6J3m3z5I7q7b1e2q8p1z2R9K5I1f3P1I1o6f9u7v9b1Z2s4h8D1B8o9C7N5y5Y9N8I2T5i3W9o5e9c3F5K4j2u2y9k9r4j1Y9E1w4f6s6'
    key = Site.query.first().inbuildings_key
    message = 'Comms Test'
    mode = 'raisenewjob'
    test = 'yes'
    equip_id = '0'
    priority_id = '7'
    data = {'key': key, 'mode': mode, 'test': test, 'eid': equip_id, 'pid': priority_id, 'body': message}

    # send request
    try:
        resp = inbuildings_request(data)
    except requests.exceptions.ConnectionError:
        return "No Comms"
    else:
        return "Comms OK"

# inbuildings asset request
def inbuildings_asset_request(site):
    # setup request parameters
    key = site.inbuildings_key
    mode = "equipmentlist"
    data = {'key': key, 'mode': mode}
    resp = inbuildings_request(data)

    # delete existing records for that site
    InbuildingsAsset.query.filter_by(site_id=site.id).delete()

    # create new asset records
    for asset in resp:
        db_asset = InbuildingsAsset(id=asset['eid'], name=asset['name'], location=asset['location'], group=asset['group'])
        db.session.add(db_asset)
    db.session.commit()