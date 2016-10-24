from flask import Flask, request, flash, url_for, redirect, render_template, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, fields, marshal, marshal_with, Api, reqparse
from distutils.util import strtobool
import flask
import uuid, base64
import requests

app = Flask(__name__)
binds = {
    'sbo':      'mssql+pyodbc://admin:password@127.0.0.1\SQLEXPRESS/StruxureWareReportsDB?driver=SQL+Server+Native+Client+10.0',
    'medusa':   'mssql+pyodbc://admin:password@127.0.0.1\SQLEXPRESS/Medusa?driver=SQL+Server+Native+Client+10.0'
}
app.config['SQLALCHEMY_BINDS'] = binds
app.config['SECRET_KEY'] = 'random string'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = True
db = SQLAlchemy(app)
api = Api(app)

##
## class definitions
##

# table with trend log values
class LogTimeValues(db.Model):
    __bind_key__ = 'sbo'
    __tablename__ = 'tbLogTimeValues'
    datetimestamp = db.Column('DateTimeStamp',db.DateTime)
    seqno = db.Column('SeqNo',db.BigInteger,primary_key=True)
    float_value = db.Column('FloatVALUE',db.Float)
    parent_id = db.Column('ParentID',db.Integer,primary_key=True)
    odometer_value = db.Column('OdometerValue',db.Float)

# table with list of trend logs
class LoggedEntities(db.Model):
    __bind_key__ = 'sbo'
    __tablename__ = 'tbLoggedEntities'
    entity_id = db.Column('ID',db.Integer,primary_key=True)
    guid = db.Column('GUID',db.String(50))
    path = db.Column('Path',db.String(1024))
    descr = db.Column('Descr',db.String(512))
    disabled = db.Column('Disabled',db.Boolean)
    last_mod = db.Column('LastMod',db.DateTime)
    version = db.Column('Version',db.Integer)
    entity_type = db.Column('Type',db.String(80))
    log_point = db.Column('LogPoint',db.String(1024))
    unit_prefix = db.Column('UNITPREFIX',db.String(512))
    unit = db.Column('Unit',db.String(512))
    base_value = db.Column('BaseValue',db.Float)
    meter_startpoint = db.Column('MeterStartPoint',db.Float)
    last_read_value = db.Column('LastReadValue',db.Float)

# asset list
class Assets(db.Model):
    __bind_key__ = 'medusa'
    eid = db.Column('EID',db.Integer,primary_key=True)
    name = db.Column('Name',db.String(512))
    location = db.Column('Location',db.String(512))
    group = db.Column('Group',db.String(512))

    def __init__(self,eid,name,group,location):
        self.eid = eid
        self.name = name
        self.location = location
        self.group = group
        

##
## app.route functions
##

# return a value from a trendlog	
@app.route('/<string:logname>/<int:seqno>')
def sql_test(name,seqno):
    trendlog_entity = LoggedEntities.query.filter(LoggedEntities.path.like('%' + logname)).first()
    trend_value = LogTimeValues.query.filter_by(parent_id == trendlog_entity.entity_id, seqno == seqno).first().float_value
    return str(trend_value)

# check comms with inbuildings server
@app.route('/inbuildings')
def inbuildings_test():
    # setup request parameters
    key = '0P8q1M8x8k1K4m7t8H2g5E1d8d5A4h3e1h2d9J3U3R7h2V9q9L6R6x8n9W4l3K9o6F1e8e6N7g4w7d1B2T1C6K9u6H9I4Y9b6J3m3z5I7q7b1e2q8p1z2R9K5I1f3P1I1o6f9u7v9b1Z2s4h8D1B8o9C7N5y5Y9N8I2T5i3W9o5e9c3F5K4j2u2y9k9r4j1Y9E1w4f6s6'
    message = 'Comms Test'
    mode = 'raisenewjob'
    test = 'yes'
    equip_id = '0'
    priority_id = '7'
    data = {'key':key, 'mode': mode, 'test': test, 'eid': equip_id, 'pid': priority_id, 'body': message}

    # send request
    try:
        resp = inbuildings_request(data)
    except requests.exceptions.ConnectionError:
        return "No Comms"
    else:
        return "Comms OK"

# run checks
@app.route('/check/AHU/4')
def airtemp_heating_check():
    return str(True)

@app.route('/check/AHU/8')
def simult_heatcool_check():
    return str(True)

@app.route('/check/AHU/13')
def fan_unoccupied_check():
    return str(True)

@app.route('/check/AHU/14')
def ahu_occupied_check():
    return str(False)

@app.route('/check/AHU/16')
def chw_hunting_check():
    return str(False)

@app.route('/check/AHU/19')
def run_hours_check():
    return str(False)


##
##  non app.route functions
##

# generic inbuildings request
def inbuildings_request(data):
    # setup request parameters
    url = 'https://inbuildings.info/ingenius/rest/sbo.php'
    headers = {'content-type': 'application/x-www-urlencoded'}
    resp = requests.post(url, data = data, headers = headers)
    # parse server response into readable type
    resp_parsed = resp.json()
    return resp_parsed

# inbuildings asset request
def inbuildings_asset_request():
    # setup request parameters
    key = '0P8q1M8x8k1K4m7t8H2g5E1d8d5A4h3e1h2d9J3U3R7h2V9q9L6R6x8n9W4l3K9o6F1e8e6N7g4w7d1B2T1C6K9u6H9I4Y9b6J3m3z5I7q7b1e2q8p1z2R9K5I1f3P1I1o6f9u7v9b1Z2s4h8D1B8o9C7N5y5Y9N8I2T5i3W9o5e9c3F5K4j2u2y9k9r4j1Y9E1w4f6s6'
    mode = "equipmentlist"
    data = {'key':key, 'mode': mode}
    resp = inbuildings_request(data)
    
    for asset in resp:
        if Assets.query.filter_by(eid=asset['eid']).first() is None:
            db_asset = Assets(asset['eid'],asset['name'],asset['location'],asset['group'])
        else:
            db_asset = Assets.query.filter_by(eid=asset['eid']).first()
            db_asset.name = asset['name']
            db_asset.location = asset['location']
            db_asset.group = asset['group']
        db.session.add(db_asset)
        
    db.session.commit()

if __name__ == '__main__':
    db.create_all(bind='medusa')
    app.run(debug=True)
