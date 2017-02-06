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
    type = db.Column('Type',db.String(80))
    log_point = db.Column('LogPoint',db.String(1024))
    unit_prefix = db.Column('UNITPREFIX',db.String(512))
    unit = db.Column('Unit',db.String(512))
    base_value = db.Column('BaseValue',db.Float)
    meter_startpoint = db.Column('MeterStartPoint',db.Float)
    last_read_value = db.Column('LastReadValue',db.Float)

###################################
## abstract models
###################################

# many-many mapping table between asset subtypes and the algorithms that apply to them
subtype_algo_mapping = db.Table('subtype_algo_mapping',
    db.Column('Subtype_id', db.Integer, db.ForeignKey('asset_subtype.ID'), primary_key=True),
    db.Column('Algorithm_id', db.Integer, db.ForeignKey('algorithm.ID'), primary_key=True),
    info={'bind_key': 'medusa'}
)

# many-many mapping table between algorithms and the component types they require
algo_comp_mapping = db.Table('algo_comp_mapping',
    db.Column('Algorithm_id', db.Integer, db.ForeignKey('algorithm.ID'), primary_key=True),
    db.Column('Component_type_id', db.Integer, db.ForeignKey('component_type.ID'), primary_key=True),
    info={'bind_key': 'medusa'}
)

# asset types
class AssetType(db.Model):
    __bind_key__ = 'medusa'
    id = db.Column('ID', db.Integer, primary_key=True)
    name = db.Column('Name', db.String(512))
    subtypes = db.relationship('AssetSubtype', backref='type')

    def __repr__(self):
        return self.name

# asset subtypes
class AssetSubtype(db.Model):
    __bind_key__ = 'medusa'
    id = db.Column('ID', db.Integer, primary_key=True)
    name = db.Column('Name', db.String(512))
    type_id = db.Column('Type_id', db.Integer, db.ForeignKey('asset_type.ID'))
    assets = db.relationship('Asset', backref='subtype')
    components = db.relationship('SubtypeComponent', backref='subtype', cascade='save-update, merge, delete, delete-orphan')
    algorithms = db.relationship('Algorithm', secondary=subtype_algo_mapping, backref='asset_subtypes')

    def get_component_types(self):
        return [component.type for component in self.components]

    # update the mapping between this subtype and all algorithms
    def map(self):
        #delete the current mapping
        self.algorithms.clear()
        for algorithms in Algorithm.query.all():
            self.map_algorithm(algorithm)

    def map_algorithm(self, algorithm):
        # map this asset subtype to a single algorithm based on previously generated relationship between subtype-components-component_types-algorithms
        passed = True
        # check the components required by algorithm against the components the asset subtype actually has
        for component in algorithm.component_types:
            if not component in self.get_component_types():
                passed = False

        # if all are matching, add the relationship
        if passed == True:
            self.algorithms.append(algorithm)

    def __repr__(self):
        return self.name

# components that each subtype has - there may be multiple of the same type
class SubtypeComponent(db.Model):
    __bind_key__ = 'medusa'
    id = db.Column('ID', db.Integer, primary_key=True)
    name = db.Column('Name', db.String(512))
    type_id = db.Column('Type_id', db.Integer, db.ForeignKey('component_type.ID'))
    subtype_id = db.Column('Subtype_id', db.Integer, db.ForeignKey('asset_subtype.ID'))

    def __repr__(self):
        if not self.name is None:
            return self.name
        else:
            return "Unnamed - {}".format(self.type.name)

# component types
class ComponentType(db.Model):
    __bind_key__ = 'medusa'
    id = db.Column('ID',db.Integer,primary_key=True)
    name = db.Column('Name',db.String(512))
    asset_components = db.relationship('AssetComponent', backref='type')
    subtype_components = db.relationship('SubtypeComponent', backref='type')

    def __repr__(self):
        return self.name

# algorithms. the 'name' field refers to the actual algorithm classname in the code
class Algorithm(db.Model):
    __bind_key__ = 'medusa'
    id = db.Column('ID', db.Integer, primary_key=True)
    name = db.Column('Name', db.String(512))
    descr = db.Column('Descr', db.String(512))
    component_types = db.relationship('ComponentType', secondary=algo_comp_mapping, backref=db.backref('algorithms'))
    results = db.relationship('Result', backref='algorithm')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.init_on_load()
        self.map()

    # this triggers when loading from the db
    @orm.reconstructor
    def init_on_load(self):
        # find the corresponding class in the code that matches the 'name' field
        self.algorithm = getattr(sys.modules['app.algorithms'], self.name)

    # call the code from the actual algorithm
    def run(self, *args, **kwargs):
        return self.algorithm.run(*args, **kwargs)

    # update mappings to component types and asset subtypes
    def map(self):
        # update matching component types based on specified component_type attribute in .algorithm
        self.component_types.clear()
        for component_type_reqd in self.algorithm.components_required:
            component_type = ComponentType.query.filter_by(name=component_type_reqd).one()
            self.component_types.append(component_type)

        # update asset subtype mappings
        self.asset_subtypes.clear()
        for asset_subtype in AssetSubtype.query.all():
            asset_subtype.map_algorithm(self)

    def __repr__(self):
        return self.name

# status of issue
class Status(db.Model):
    __bind_key__ = 'medusa'
    id = db.Column('ID', db.Integer, primary_key=True)
    descr = db.Column('Descr', db.String(512))
    results = db.relationship('Result', backref='status')

###################################
## real world models
###################################

# many-many mapping table defining algorithms that are excluded from operating on an assets
algo_exclusions = db.Table('algo_exclusions',
    db.Column('Asset_id', db.Integer, db.ForeignKey('asset.ID'), primary_key=True),
    db.Column('Algorithm_id', db.Integer, db.ForeignKey('algorithm.ID'), primary_key=True),
    info={'bind_key': 'medusa'}
)

# many-many mapping table defining which components were checked for each algorithm result
components_checked = db.Table('components_checked',
    db.Column('Result_id', db.Integer, db.ForeignKey('result.ID'), primary_key=True),
    db.Column('Component_id', db.Integer, db.ForeignKey('asset_component.ID'), primary_key=True),
    info={'bind_key': 'medusa'}
)

# list of customer sites
class Site(db.Model):
    __bind_key__ = 'medusa'
    id = db.Column('ID', db.Integer, primary_key=True)
    name = db.Column('Name', db.String(512))
    db_name = db.Column('DB_Name', db.String(512))
    inbuildings_key = db.Column('Inbuildings_key', db.String(512))
    assets = db.relationship('Asset', backref='site')
    inbuildings_assets = db.relationship('InbuildingsAsset', backref='site')
    issue_history = db.relationship('IssueHistory', backref='site')

    def __repr__(self):
        return self.name

    def get_unresolved(self):
        issues = Result.query.join(Result.asset).filter(Result.status_id > 1, Result.status_id < 5, Asset.site == self).all()
        return issues

    def get_unresolved_by_priority(self):
        issue = Result.query.join(Result.asset).filter(Result.status_id > 1, Result.status_id < 5, Asset.site == self).order_by(Asset.priority.asc()).all()
        return issue

# data pulled from inbuildings
class InbuildingsAsset(db.Model):
    __bind_key__ = 'medusa'
    id = db.Column('ID', db.Integer, primary_key=True)
    name = db.Column('Name', db.String(512))
    location = db.Column('Location', db.String(512))
    group = db.Column('Group', db.String(512))
    site_id = db.Column('Site_id', db.Integer, db.ForeignKey('site.ID'))
    asset_id = db.Column('Asset_id', db.Integer, db.ForeignKey('asset.ID'))

    def __repr__(self):
        return self.name

# list of assets
class Asset(db.Model):
    __bind_key__ = 'medusa'
    id = db.Column('ID', db.Integer, primary_key=True)
    name = db.Column('Name', db.String(512))
    location = db.Column('Location', db.String(512))
    group = db.Column('Group', db.String(512))
    health = db.Column('Health', db.Float)
    priority = db.Column('Priority', db.Integer)
    site_id = db.Column('Site_id', db.Integer, db.ForeignKey('site.ID'))
    subtype_id = db.Column('Subtype_id', db.Integer, db.ForeignKey('asset_subtype.ID'))
    components = db.relationship('AssetComponent', backref='asset', cascade='save-update, merge, delete, delete-orphan')
    results = db.relationship('Result', backref='asset', cascade='save-update, merge, delete, delete-orphan')
    inbuildings = db.relationship('InbuildingsAsset', backref='asset', uselist=False)
    exclusions = db.relationship('Algorithm', secondary=algo_exclusions, backref='exclusions')

    def get_component_types(self):
        return [component.type for component in self.components]

    def __repr__(self):
        return self.name

# components that each asset has - there may be multiple of the same type
class AssetComponent(db.Model):
    __bind_key__ = 'medusa'
    id = db.Column('ID', db.Integer, primary_key=True)
    name = db.Column('Name', db.String(512))
    asset_id = db.Column('Asset_id', db.Integer, db.ForeignKey('asset.ID'))
    type_id = db.Column('Type_id', db.Integer, db.ForeignKey('component_type.ID'))
    loggedentity_id = db.Column('LoggedEntity_id', db.Integer)

    def __repr__(self):
        if not self.name is None:
            return self.name
        else:
            return "Unnamed - {}".format(self.type.name)

# timestamped list containing the results of all algorithms ever applied to each asset
class Result(db.Model):
    __bind_key__ = 'medusa'
    id = db.Column('ID', db.Integer, primary_key=True)
    timestamp = db.Column('Timestamp', db.DateTime)
    asset_id = db.Column('Asset_id', db.Integer, db.ForeignKey('asset.ID'))
    algorithm_id = db.Column('Algorithm_id', db.Integer, db.ForeignKey('algorithm.ID'))
    value = db.Column('Result', db.Float)
    passed = db.Column('Passed', db.Boolean)
    recent = db.Column('Recent', db.Boolean)
    components = db.relationship('AssetComponent', secondary=components_checked, backref='results')
    status_id = db.Column('Status_id', db.Integer, db.ForeignKey('status.ID'))

    def __repr__(self):
        return str(self.timestamp)

    @classmethod
    def get_unresolved(cls):
        issues = cls.query.filter(cls.status_id > 1, cls.status_id < 5).all()
        return issues

    @classmethod
    def get_unresolved_by_priority(cls):
        issue = cls.query.join(cls.asset).filter(cls.status_id > 1, Result.status_id < 5).order_by(Asset.priority.asc()).all()
        return issue


###################################
## charting info
###################################

# timestamped list containing the results of all algorithms ever applied to each asset
class IssueHistoryTimestamp(db.Model):
    __bind_key__ = 'medusa'
    id = db.Column('ID', db.Integer, primary_key=True)
    timestamp = db.Column('Timestamp', db.DateTime)
    issues = db.relationship('IssueHistory', backref='timestamp')

# timestamped list containing the results of all algorithms ever applied to each asset
class IssueHistory(db.Model):
    __bind_key__ = 'medusa'
    id = db.Column('ID', db.Integer, primary_key=True)
    issues = db.Column('Issues', db.Integer)
    timestamp_id = db.Column('Timestamp_id', db.Integer, db.ForeignKey('issue_history_timestamp.ID'))
    site_id = db.Column('Site_id', db.Integer, db.ForeignKey('site.ID'))