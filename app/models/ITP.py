from app import db
import datetime
from sqlalchemy import UniqueConstraint

################################
#Project models
################################
class Project(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    job_number = db.Column(db.Integer(), nullable=False)
    assigned_to_id = db.Column(db.Integer(), db.ForeignKey('user.id'))
    description = db.Column(db.String(500))
    start_date = db.Column(db.DateTime())
    completion_date = db.Column(db.DateTime())
    site_id = db.Column(db.Integer(), db.ForeignKey('site.ID', ondelete='CASCADE'))
    ITP = db.relationship('ITP', backref = 'project')
    tickets = db.relationship('FlicketTicket', backref='project', lazy='dynamic')
    __table_args__ = (db.UniqueConstraint('site_id','name', name='_site_name_uc'),)

    def __init__(self, name, job_number, description, site_id):
        self.name = name
        self.job_number = job_number
        self.description = description
        self.site_id = site_id
        self.start_date = datetime.datetime.now()

    def __repr__(self):
        return self.name

class Location(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), unique=True)
    site_id = db.Column(db.Integer(), db.ForeignKey('site.ID'))
    secondary_location_id = db.Column(db.Integer(), db.ForeignKey('secondary_location.id'))
    deliverable = db.relationship('Deliverable',
        backref = 'location')

    def __repr__(self):
        return self.name

class Secondary_location(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), unique=True)
    location = db.relationship('Location',
        backref = 'secondary')
    deliverable = db.relationship('Deliverable',
        backref = 'secondary')

    def __repr__(self):
        return self.name

class ITP(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255), nullable=True)
    project_id = db.Column(db.Integer(), db.ForeignKey('project.id', ondelete='CASCADE'))
    deliverable = db.relationship('Deliverable',
        backref = 'ITP')
    status = db.Column(db.String(200))
    percentage_complete = db.Column(db.Integer())
    __table_args__ = (db.UniqueConstraint('project_id','name', name='_project_name_uc'),)

    def __init__(self, name, project_id, status):
        self.name = name
        self.project_id = project_id
        self.status = status
        self.percentage_complete = 0

    def __repr__(self):
        return self.name

################################
#Section for models on Deliverables
################################
class Deliverable_type(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), unique=True)
    deliverable = db.relationship('Deliverable',
        backref = 'type')
    ITC = db.relationship('ITC',
        backref = 'deliverable_type')

    def __repr__(self):
        return self.name

class Deliverable(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    description = db.Column(db.String(255))
    deliverable_type_id = db.Column(db.Integer(), db.ForeignKey('deliverable_type.id', ondelete='CASCADE'))
    location_id = db.Column(db.Integer(), db.ForeignKey('location.id', ondelete='CASCADE'))
    secondary_location_id = db.Column(db.Integer(), db.ForeignKey('secondary_location.id', ondelete='CASCADE'))
    ITP_id = db.Column(db.Integer(), db.ForeignKey('ITP.id', ondelete='CASCADE'))
    Deliverable_ITC_map = db.relationship('Deliverable_ITC_map',
        backref = 'deliverable')
    status = db.Column(db.String(200))
    percentage_complete = db.Column(db.Integer())
    component_number = db.Column(db.Integer())
    assigned_to = db.Column(db.String(255))
    start_date = db.Column(db.DateTime)
    completion_date = db.Column(db.DateTime())
    completed = db.Column(db.Boolean())
    __table_args__ = (db.UniqueConstraint('ITP_id','name', name='_ITP_name_uc'),)

    def __init__(self, name, description, deliverable_type_id, location_id, ITP_id):
        self.name = name
        self.description = description
        self.deliverable_type_id = deliverable_type_id
        self.location_id = location_id
        self.ITP_id = ITP_id
        self.status = "Not Started"
        self.percentage_complete = 0

    def __repr__(self):
        return self.name

###############################
#Section on Generic ITCs
###############################

class Check_generic(db.Model):
    __tablename__ = "Check_generic"
    id = db.Column(db.Integer(), primary_key=True)
    check_description = db.Column(db.String(500), unique=True)
    ITC_check_map = db.relationship('ITC_check_map',
        backref = 'check')

    def __init__(self, check_description):
        self.check_description = check_description

    def __repr__(self):
        return self.check_description

class ITC(db.Model):
    __tablename__ = "ITC"
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), unique=True)
    description = db.Column(db.String(255), nullable=True)
    ITC_check_map = db.relationship('ITC_check_map',
        backref='ITC')
    deliverable_type_id = db.Column(db.Integer(), db.ForeignKey('deliverable_type.id'))
    deliverable_ITC_map = db.relationship('Deliverable_ITC_map',
        backref='ITC')
    ITC_group_id = db.Column(db.Integer(), db.ForeignKey('ITC_group.id'))

    def __init__(self, name, deliverable_type_id):
        self.name = name
        self.deliverable_type_id = deliverable_type_id

    def __repr__(self):
        return self.name

class ITC_group(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), unique=True)
    ITC = db.relationship('ITC',
        backref = 'group')

    def __repr__(self):
        return self.name

###############################
#Section on mapping
###############################

# many-many mapping table defining checks in an generic ITC
class ITC_check_map(db.Model):
    __tablename__ = "ITC_check_map"
    id = db.Column(db.Integer(), primary_key=True)
    check_generic = db.Column(db.Integer(), db.ForeignKey('Check_generic.id'))
    ITC_id = db.Column(db.Integer(), db.ForeignKey('ITC.id'))
    deliverable_check_map = db.relationship('Deliverable_check_map',
        backref='ITC_check')

    def __init__(self, check_generic, ITC_id):
        self.check_generic = check_generic
        self.ITC_id = ITC_id

#many-many mapping table for defining a list of ITC to a deliverable
class Deliverable_ITC_map(db.Model):
    __tablename__ = "Deliverable_ITC_map"
    id = db.Column(db.Integer(), primary_key=True)
    comments = db.Column(db.String(255), nullable=True)
    deliverable_id = db.Column(db.Integer(), db.ForeignKey('deliverable.id', ondelete='CASCADE'))
    ITC_id = db.Column(db.Integer(), db.ForeignKey('ITC.id', ondelete='CASCADE'))
    deliverable_check_map = db.relationship('Deliverable_check_map',
        backref='deliver_ITC',
        primaryjoin="Deliverable_ITC_map.id == Deliverable_check_map.deliverable_ITC_map_id")
    status = db.Column(db.String(200))
    percentage_complete = db.Column(db.Integer())

    def __init__(self, deliverable_id, ITC_id):
        self.deliverable_id = deliverable_id
        self.ITC_id = ITC_id
        self.status = "Not Started"
        self.percentage_complete = 0

#many-many table for adding all checks specific to deliverable
class Deliverable_check_map(db.Model):
    __tablename__ = "Deliverable_check_map"
    id = db.Column(db.Integer(), primary_key=True)
    deliverable_ITC_map_id = db.Column(db.Integer(), db.ForeignKey('Deliverable_ITC_map.id'))
    ITC_check_id = db.Column(db.Integer(), db.ForeignKey('ITC_check_map.id'))
    is_done = db.Column(db.Boolean(), default=False)
    completion_datetime = db.Column(db.DateTime())
    completion_by_user_id = db.Column(db.Integer(), db.ForeignKey('user.id'))
    comments = db.Column(db.String(500))
    status = db.Column(db.String(200))

    def __init__(self, deliverable_ITC_map_id, ITC_check_id):
        self.deliverable_ITC_map_id = deliverable_ITC_map_id
        self.ITC_check_id = ITC_check_id
        self.status = "Not Started"
        self.is_done = False
