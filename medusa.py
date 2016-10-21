from flask import Flask, request, flash, url_for, redirect, render_template, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, fields, marshal, marshal_with, Api, reqparse
from distutils.util import strtobool
import flask
import uuid, base64

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

class LogTimeValues(db.Model):
    __bind_key__ = 'sbo'
    __tablename__ = 'tbLogTimeValues'
    datetimestamp = db.Column('DateTimeStamp',db.DateTime)
    seqno = db.Column('SeqNo',db.BigInteger,primary_key=True)
    floatvalue = db.Column('FloatVALUE',db.Float)
    parentid = db.Column('ParentID',db.Integer,primary_key=True)
    odometervalue = db.Column('OdometerValue',db.Float)

class LoggedEntities(db.Model):
    __bind_key__ = 'sbo'
    __tablename__ = 'tbLoggedEntities'
    entityid = db.Column('ID',db.Integer,primary_key=True)
    guid = db.Column('GUID',db.String(50))
    path = db.Column('Path',db.String(1024))
    descr = db.Column('Descr',db.String(512))
    disabled = db.Column('Disabled',db.Boolean)
    lastmod = db.Column('LastMod',db.DateTime)
    version = db.Column('Version',db.Integer)
    entitytype = db.Column('Type',db.String(80))
    logpoint = db.Column('LogPoint',db.String(1024))
    unitprefix = db.Column('UNITPREFIX',db.String(512))
    unit = db.Column('Unit',db.String(512))
    basevalue = db.Column('BaseValue',db.Float)
    meterstartpoint = db.Column('MeterStartPoint',db.Float)
    lastreadvalue = db.Column('LastReadValue',db.Float)
	
@app.route('/<string:name>/<int:seqno>')
def test(name,seqno):
    trendlogentity = LoggedEntities.query.filter(LoggedEntities.path.like('%'+name)).first()
    trendvalue = LogTimeValues.query.filter_by(parentid==trendlogentity.entityid, seqno==seqno).first().floatvalue
    return str(trendvalue)

if __name__ == '__main__':
    app.run(debug=True)
