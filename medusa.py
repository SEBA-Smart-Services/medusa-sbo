from flask import Flask, request, flash, url_for, redirect, render_template, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, fields, marshal, marshal_with, Api, reqparse
from distutils.util import strtobool
import flask
import uuid, base64
import requests
import datetime
import sys

app = Flask(__name__)
binds = {
    'sbo':      'mssql+pyodbc://admin:password@MedusaTest\SQLEXPRESS/StruxureWareReportsDB?driver=SQL+Server+Native+Client+10.0',
    'medusa':   'mssql+pyodbc://admin:password@MedusaTest\SQLEXPRESS/Medusa?driver=SQL+Server+Native+Client+10.0'
}
app.config['SQLALCHEMY_BINDS'] = binds
app.config['SECRET_KEY'] = 'random string'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = True
db = SQLAlchemy(app)
api = Api(app)

###################################
## database classes
###################################

# trend log values
class LogTimeValue(db.Model):
    __bind_key__ = 'sbo'
    __tablename__ = 'tbLogTimeValues'
    datetimestamp = db.Column('DateTimeStamp',db.DateTime)
    seqno = db.Column('SeqNo',db.BigInteger,primary_key=True)
    float_value = db.Column('FloatVALUE',db.Float)
    parent_id = db.Column('ParentID',db.Integer,primary_key=True)
    odometer_value = db.Column('OdometerValue',db.Float)

# list of trend logs
class LoggedEntity(db.Model):
    __bind_key__ = 'sbo'
    __tablename__ = 'tbLoggedEntities'
    id = db.Column('ID',db.Integer,primary_key=True)
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

# asset-function mapping
asset_func_mapping = db.Table('asset_func_mapping',
    db.Column('Asset_id', db.Integer, db.ForeignKey('asset.EID'), primary_key=True),
    db.Column('Function_id', db.Integer, db.ForeignKey('function.ID'), primary_key=True),
    info={'bind_key': 'medusa'}
)

# asset list
class Asset(db.Model):
    __bind_key__ = 'medusa'
    id = db.Column('EID',db.Integer,primary_key=True)
    name = db.Column('Name',db.String(512))
    location = db.Column('Location',db.String(512))
    group = db.Column('Group',db.String(512))
    type_id = db.Column('Type_id',db.Integer,db.ForeignKey('asset_type.ID'))
    functions = db.relationship('Function', secondary=asset_func_mapping, backref=db.backref('assets'))
    components = db.relationship('Component', backref='asset', cascade="save-update, merge, delete, delete-orphan")
    results = db.relationship('Result', backref='asset')

    def __init__(self,id,name,group,location):
        self.id = id
        self.name = name
        self.location = location
        self.group = group

    def get_component_types(self):
        return [component.type for component in self.components]

# asset types
class AssetType(db.Model):
    __bind_key__ = 'medusa'
    id = db.Column('ID',db.Integer,primary_key=True)
    name = db.Column('Name',db.String(512))
    assets = db.relationship('Asset', backref='type')

# components
class Component(db.Model):
    __bind_key__ = 'medusa'
    id = db.Column('ID',db.Integer,primary_key=True)
    asset_id = db.Column('Asset_id',db.Integer,db.ForeignKey('asset.EID'))
    type_id = db.Column('Type_id',db.Integer,db.ForeignKey('component_type.ID'))
    loggedentity_id = db.Column('LoggedEntity_id',db.Integer)

# component types
class ComponentType(db.Model):
    __bind_key__ = 'medusa'
    id = db.Column('ID',db.Integer,primary_key=True)
    name = db.Column('Name',db.String(512))
    components = db.relationship('Component', backref='type')

# components-functions mapping
func_comp_mapping = db.Table('func_comp_mapping',
    db.Column('Function_id', db.Integer, db.ForeignKey('function.ID'), primary_key=True),
    db.Column('Component_type_id', db.Integer, db.ForeignKey('component_type.ID'), primary_key=True),
    info={'bind_key': 'medusa'}
)

# functions
class Function(db.Model):
    __bind_key__ = 'medusa'
    id = db.Column('ID',db.Integer,primary_key=True)
    name = db.Column('Name',db.String(512))
    descr = db.Column('Descr',db.String(512))
    component_types = db.relationship('ComponentType', secondary=func_comp_mapping, backref=db.backref('functions'))
    results = db.relationship('Result', backref='function')

    def run(self, *args, **kwargs):
        functionclass = getattr(sys.modules[__name__],self.name)
        return functionclass.run(*args, **kwargs)

# function results
class Result(db.Model):
    __bind_key__ = 'medusa'
    id = db.Column('ID', db.Integer, primary_key=True)
    timestamp = db.Column('Timestamp', db.DateTime)
    asset_id = db.Column('Asset_id', db.Integer, db.ForeignKey('asset.EID'))
    function_id = db.Column('Function_id', db.Integer, db.ForeignKey('function.ID'))
    value = db.Column('Result', db.Float)
    passed = db.Column('Passed', db.Boolean)

    
###################################
## endpoint functions
###################################

# return a value from a trendlog	
@app.route('/<string:logname>/<int:seqno>')
def sql_test(name,seqno):
    trendlog_entity = LoggedEntity.query.filter(LoggedEntity.path.like('%' + logname)).first()
    trend_value = LogTimeValue.query.filter_by(parent_id == trendlog_entity.entity_id, seqno == seqno).first().float_value
    return str(trend_value)

# map functions in database
@app.route('/map')
def map_all():
    generate_functions()
    map_functions_components()
    map_functions_assets()
    return "done"

# check with pre-filled info
@app.route('/check/test')
def testcheck():
    db.session.query(Result).delete()
    asset_name = Asset.query.filter_by(id=20440).first().name
    result = check(asset_name)
    return result

# run checks on an asset
@app.route('/check/<string:asset_name>')
def check(asset_name):
    asset = Asset.query.filter_by(name=asset_name).first()
    result = check_asset(asset)
    return result

# update components belonging to an asset
@app.route('/update', methods=['POST'])
def update():
    asset = Asset.query.filter_by(name=request.values['asset']).one()
    asset.components.clear()
    component_list = request.values.to_dict(flat=False)
    component_list.pop('asset')
    for component_type_name in component_list.keys():
        component_type = ComponentType.query.filter_by(name=component_type_name).one()
        trendlog_name = component_list[component_type_name][0]
        trendlog = LoggedEntity.query.filter(LoggedEntity.path.like('%' + trendlog_name)).one()
        new_component = Component(asset=asset, type=component_type, loggedentity_id=trendlog.id)
        asset.components.append(new_component)
    db.session.commit()
    return "Done"

###################################
## mapping functions
###################################

def generate_functions():
    for function in FunctionClass.__subclasses__():
        functionmodel = Function.query.filter_by(name=function.__name__).all()
        if functionmodel == None:
            functionmodel = Function(descr=function.descr, name=function.__name__)
            db.session.add(functionmodel)
    db.session.commit()
    return "done"

# must be done before map_functions_assets
def map_functions_components():
    db.session.execute(func_comp_mapping.delete())
    for function in FunctionClass.__subclasses__():
        functionmodel = Function.query.filter_by(name=function.__name__).one()
        for component_type_reqd in function.components_required:
            type = ComponentType.query.filter_by(name=component_type_reqd).one()
            functionmodel.component_types.append(type)
            
    db.session.commit()
    return "done"

def map_functions_assets():
    db.session.execute(asset_func_mapping.delete())
    for a in Asset.query.all():
        for f in Function.query.all():
            passed = True
            
            for c in f.component_types:
                if not c in a.get_component_types():
                    passed = False

            if passed == True:
                a.functions.append(f)
    db.session.commit()
    return "done"

###################################
## functional checks
###################################
    
def check_asset(asset):
    result_string = ""
    for function in asset.functions:
        data={}
        for component in asset.components:
            if component.type in function.component_types:
                value_list = LogTimeValue.query.filter_by(parent_id=component.loggedentity_id).order_by(LogTimeValue.datetimestamp.desc()).limit(1000).from_self().order_by(LogTimeValue.datetimestamp.asc()).all()
                data[component.type.name] = value_list
        [result,passed] = function.run(data)
        save_result(asset,function,result,passed)
        result_string += "{}: {},  Result = {}\n".format(function.descr,"Passed" if passed==True else "Failed",result)
    return result_string

class FunctionClass():
    pass
    
class airtemp_heating_check(FunctionClass):
    components_required = ['Room Air Temp Sensor','Room Air Temp Setpoint','Heating Coil']
    name = "Room air temp higher than setpoint while heating on"
    def run(data):
        result = 0.1
        healthy = False
        return [result,healthy]

class simult_heatcool_check(FunctionClass):
    components_required = ['Chilled Water Valve','Heating Coil']
    name = "Simultaneous heating and cooling"
    def run(data):
        totaltime = datetime.timedelta(0)
        result = datetime.timedelta(0)
        for i in range(1, len(data['Chilled Water Valve'])):
            
            current_time = data['Chilled Water Valve'][i].datetimestamp
            date_candidates = [value.datetimestamp for value in data['Heating Coil'] if value.datetimestamp < current_time]
            
            if len(date_candidates) > 0:
                current_time_matched = max(date_candidates)
                j = [value.datetimestamp for value in data['Heating Coil']].index(current_time_matched)
                timediff = data['Chilled Water Valve'][i].datetimestamp - data['Chilled Water Valve'][i-1].datetimestamp
                totaltime += timediff

                if data['Chilled Water Valve'][i].float_value > 0 and data['Heating Coil'][j].float_value > 0:
                    result += timediff
                    
        result = result/totaltime
        healthy = False
        return [result,healthy]

class fan_unoccupied_check(FunctionClass):
    components_required = ['Zone Fan','Zone Occupancy Sensor']
    name = "Zone fan on while unoccupied"
    def run(data):    
        result = 0
        healthy = True
        return [result,healthy]

class ahu_occupied_check(FunctionClass):
    components_required = ['Power Switch','Zone Occupancy Sensor']
    name = "Zone occupied, AHU off"
    def run(data):
        result = 0
        healthy = True
        return [result,healthy]

class chw_hunting_check(FunctionClass):
    components_required = ['Chilled Water Valve']
    name = "Chilled water valve actuator hunting"
    def run(data):
        result = False
        healthy = True
        return [result,healthy]

class run_hours_check(FunctionClass):
    components_required = ['Power Switch']
    name = "Run hours"
    def run(data):
        result = 0
        for i in range(1, len(data['Power Switch'])):
            timediff = data['Power Switch'][i].datetimestamp - data['Power Switch'][i-1].datetimestamp
            result += timediff.total_seconds() * data['Power Switch'][i].float_value
        result = result/3600
        healthy = False
        return [result,healthy]

class testfunc(FunctionClass):
    components_required = []
    name = "Test"
    def run(data):
        print("Test!")
        #print(data.keys())
        result = True
        healthy = True
        return [result,healthy]

# save the check results
def save_result(asset,function,value,passed):
    result = Result(timestamp=datetime.datetime.now(), asset_id=asset.id, function_id=function.id, value=value, passed=passed)
    db.session.add(result)
    db.session.commit()


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

# inbuildings asset request
def inbuildings_asset_request():
    # setup request parameters
    key = '0P8q1M8x8k1K4m7t8H2g5E1d8d5A4h3e1h2d9J3U3R7h2V9q9L6R6x8n9W4l3K9o6F1e8e6N7g4w7d1B2T1C6K9u6H9I4Y9b6J3m3z5I7q7b1e2q8p1z2R9K5I1f3P1I1o6f9u7v9b1Z2s4h8D1B8o9C7N5y5Y9N8I2T5i3W9o5e9c3F5K4j2u2y9k9r4j1Y9E1w4f6s6'
    mode = "equipmentlist"
    data = {'key':key, 'mode': mode}
    resp = inbuildings_request(data)

    #create or update
    for asset in resp:
        if Asset.query.filter_by(id=asset['eid']).first() is None:
            db_asset = Asset(asset['eid'],asset['name'],asset['location'],asset['group'])
            db.session.add(db_asset)
        else:
            db_asset = Asset.query.filter_by(id=asset['eid']).first()
            db_asset.name = asset['name']
            db_asset.location = asset['location']
            db_asset.group = asset['group']  
    db.session.commit()

if __name__ == '__main__':
    db.create_all(bind='medusa')
    app.run(debug=True,host='192.168.8.150')
