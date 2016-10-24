from flask import Flask, request, flash, url_for, redirect, render_template, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, fields, marshal, marshal_with, Api, reqparse
from distutils.util import strtobool
import flask
import uuid, base64
import requests

app = Flask(__name__)
binds = {
    'sbo':  'mssql+pyodbc://admin:password@127.0.0.1\SQLEXPRESS/StruxureWareReportsDB?driver=SQL+Server+Native+Client+10.0'
}
app.config['SQLALCHEMY_BINDS'] = binds
app.config['SECRET_KEY'] = "random string"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = True
db = SQLAlchemy(app)
api = Api(app)

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

#return a value from a trendlog	
@app.route('/<string:logname>/<int:seqno>')
def sql_test(name,seqno):
    trendlog_entity = LoggedEntities.query.filter(LoggedEntities.path.like('%' + logname)).first()
    trend_value = LogTimeValues.query.filter_by(parent_id==trendlog_entity.entity_id, seqno==seqno).first().float_value
    return str(trend_value)

#check comms with inbuildings server
@app.route('/inbuildings')
def inbuildings_test():
    # setup request parameters
    key = "0P8q1M8x8k1K4m7t8H2g5E1d8d5A4h3e1h2d9J3U3R7h2V9q9L6R6x8n9W4l3K9o6F1e8e6N7g4w7d1B2T1C6K9u6H9I4Y9b6J3m3z5I7q7b1e2q8p1z2R9K5I1f3P1I1o6f9u7v9b1Z2s4h8D1B8o9C7N5y5Y9N8I2T5i3W9o5e9c3F5K4j2u2y9k9r4j1Y9E1w4f6s6"
    url = "https://inbuildings.info/ingenius/rest/sbo.php"
    headers = {'content-type': 'application/x-www-urlencoded'}
    message = "Comms Test"
    mode = "raisenewjob"

    # send request
    try:
        resp = requests.post(url, data = {'key':key, 'mode': mode, 'test': 'yes', 'eid': '0', 'pid': '7', 'body': message}, headers = headers)
        # parse server response into readable type
        resp_parsed = resp.json()
    except:
        return "No Comms"
    else:
        return "Comms OK"

if __name__ == '__main__':
    app.run(debug=True)
