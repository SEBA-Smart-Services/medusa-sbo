from app import db
from sqlalchemy import orm
import sys

###################################
## classes in report server database
###################################

# trend log values, stored in report server
class LogTimeValue(db.Model):
    __bind_key__ = 'sbo'
    __tablename__ = 'tbLogTimeValues'
    datetimestamp = db.Column('DateTimeStamp',db.DateTime)
    seqno = db.Column('SeqNo',db.BigInteger,primary_key=True)
    float_value = db.Column('FloatVALUE',db.Float)
    parent_id = db.Column('ParentID',db.Integer,primary_key=True)
    odometer_value = db.Column('OdometerValue',db.Float)

# list of trend logs, stored in report server
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

###################################
## classes in medusa database
###################################

# many-many mapping table between assets and functions
asset_func_mapping = db.Table('asset_func_mapping',
    db.Column('Asset_id', db.Integer, db.ForeignKey('asset.ID'), primary_key=True),
    db.Column('Function_id', db.Integer, db.ForeignKey('function.ID'), primary_key=True),
    info={'bind_key': 'medusa'}
)

# list of assets, based on inbuildings data
class Asset(db.Model):
    __bind_key__ = 'medusa'
    id = db.Column('ID',db.Integer,primary_key=True)
    inbuildings_id = db.Column('Inbuildings_id',db.Integer)
    name = db.Column('Name',db.String(512))
    location = db.Column('Location',db.String(512))
    group = db.Column('Group',db.String(512))
    type_id = db.Column('Type_id',db.Integer,db.ForeignKey('asset_type.ID'))
    functions = db.relationship('Function', secondary=asset_func_mapping, backref=db.backref('assets'))
    components = db.relationship('Component', backref='asset', cascade="save-update, merge, delete, delete-orphan")
    results = db.relationship('Result', backref='asset')
    health = db.relationship('AssetHealth', uselist=False, backref='asset')

    def get_component_types(self):
        return [component.type for component in self.components]

    # update the mapping between this asset and all functions
    def map_all(self):
        #delete the current mapping
        self.functions.clear()
        for function in Function.query.all():
            self.map_function(function)

    def map_function(self, function):
        # map this asset to a single function based on previously generated relationship between assets-components-component_types-functions
        passed = True
        # check the components required by function against the components the asset actually has
        for c in function.component_types:
            if not c in self.get_component_types():
                passed = False

        # if all are matching, add the relationship
        if passed == True:
            self.functions.append(function)

# asset types
class AssetType(db.Model):
    __bind_key__ = 'medusa'
    id = db.Column('ID',db.Integer,primary_key=True)
    name = db.Column('Name',db.String(512))
    assets = db.relationship('Asset', backref='type')

# components that each asset has - there may be multiple of the same type
class Component(db.Model):
    __bind_key__ = 'medusa'
    id = db.Column('ID',db.Integer,primary_key=True)
    asset_id = db.Column('Asset_id',db.Integer,db.ForeignKey('asset.ID'))
    type_id = db.Column('Type_id',db.Integer,db.ForeignKey('component_type.ID'))
    loggedentity_id = db.Column('LoggedEntity_id',db.Integer)

# component types
class ComponentType(db.Model):
    __bind_key__ = 'medusa'
    id = db.Column('ID',db.Integer,primary_key=True)
    name = db.Column('Name',db.String(512))
    components = db.relationship('Component', backref='type')

# many-many mapping table between functions and component types
func_comp_mapping = db.Table('func_comp_mapping',
    db.Column('Function_id', db.Integer, db.ForeignKey('function.ID'), primary_key=True),
    db.Column('Component_type_id', db.Integer, db.ForeignKey('component_type.ID'), primary_key=True),
    info={'bind_key': 'medusa'}
)

# functions. the 'name' field refers to the actual function classname in the code
class Function(db.Model):
    __bind_key__ = 'medusa'
    id = db.Column('ID',db.Integer,primary_key=True)
    name = db.Column('Name',db.String(512))
    descr = db.Column('Descr',db.String(512))
    component_types = db.relationship('ComponentType', secondary=func_comp_mapping, backref=db.backref('functions'))
    results = db.relationship('Result', backref='function')

    def __init__(self, name, descr, component_types, results):
        self.name = name
        self.descr = descr
        self.component_types = component_types
        self.results = results
        self.init_on_load()

    # this triggers when loading from the db
    @orm.reconstructor
    def init_on_load(self):
        # find the corresponding class in the code that matches the 'name' field
        self.function = getattr(sys.modules['app.checks'], self.name)

    # call the code from the actual function
    def run(self, *args, **kwargs):
        return function.run(*args, **kwargs)

    # update mappings to component types and assets
    def map(self):
        # update matching component types based on specified component_type attribute in .function
        self.component_types.clear()
        for component_type_reqd in self.function.components_required:
            type = ComponentType.query.filter_by(name=component_type_reqd).one()
            self.component_types.append(type)

        # update asset mappings
        self.assets.clear()
        for asset in Asset.query.all():
            asset.map_function(self)

# timestamped list containing the results of all functions ever applied to each asset
class Result(db.Model):
    __bind_key__ = 'medusa'
    id = db.Column('ID', db.Integer, primary_key=True)
    timestamp = db.Column('Timestamp', db.DateTime)
    asset_id = db.Column('Asset_id', db.Integer, db.ForeignKey('asset.ID'))
    function_id = db.Column('Function_id', db.Integer, db.ForeignKey('function.ID'))
    value = db.Column('Result', db.Float)
    passed = db.Column('Passed', db.Boolean)
    unresolved = db.Column('Unresolved', db.Boolean)

# health results of the latest checks performed against each asset
class AssetHealth(db.Model):
    __bind_key__ = 'medusa'
    asset_id = db.Column('Asset_id', db.Integer, db.ForeignKey('asset.ID'), primary_key=True)
    health = db.Column('Health', db.Float)
    summary = db.Column('Summary', db.String(4000))