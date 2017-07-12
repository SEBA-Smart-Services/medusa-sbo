from app import db
from app.models.users import User

################################
#Project models
################################
class Project(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    #description = db.Column(db.String(500))
    site_id = db.Column(db.Integer(), db.ForeignKey('site.ID', ondelete='CASCADE'))
    ITP = db.relationship('ITP',
        backref = 'project')

    #def __init__(self, name, description, site_id):
    #    self.name = name
        #self.description = description
    #    self.site_id = site_id

class Location(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), unique=True)
    deliverable = db.relationship('Deliverable',
        backref = 'location')

class ITP(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    project_id = db.Column(db.Integer(), db.ForeignKey('project.id', ondelete='CASCADE'))
    deliverable = db.relationship('Deliverable',
        backref = 'ITP')

    #def __init__(self, name, project_id):
    #    self.name = name
    #    self.project_id = project_id

################################
#Section for models on Deliverables
################################
class Deliverable_type(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), unique=True)
    deliverable = db.relationship('Deliverable',
        backref = 'type')

class Deliverable(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    deliverable_type_id = db.Column(db.Integer(), db.ForeignKey('deliverable_type.id', ondelete='CASCADE'))
    location_id = db.Column(db.Integer(), db.ForeignKey('location.id', ondelete='CASCADE'))
    ITP_id = db.Column(db.Integer(), db.ForeignKey('ITP.id', ondelete='CASCADE'))

###############################
#Section on ITCs
###############################
# many-many mapping table defining checks in an ITC
class ITC_check_map(db.Model):
    __tablename__ = "ITC_check_map"
    id = db.Column(db.Integer(), primary_key=True)
    check_generic = db.Column(db.Integer(), db.ForeignKey('Check_generic.id'))
    ITC_id = db.Column(db.Integer(), db.ForeignKey('ITC.id'))
    is_done = db.Column(db.Boolean(), default=False)
    completion_datetime = db.Column(db.DateTime())
    completion_by_user_id = db.Column(db.Integer(), db.ForeignKey('user.id'))
    comments = db.Column(db.String(500))

#ITC_check_map = db.Table('ITC_check_map',
#    db.Column('ID', db.Integer, primary_key=True),
#    db.Column('check_generic_id', db.Integer, db.ForeignKey('Check_generic.id')),
#    db.Column('ITC_id', db.Integer, db.ForeignKey('ITC.id')),
#    db.Column('is_done', db.Boolean, default=False),
#    db.Column('completion_datetime', db.DateTime),
#    db.Column('completion_by_user_id', db.Integer, db.ForeignKey('user.id')),
#    db.Column('comments', db.String(500))
#)

class Check_generic(db.Model):
    __tablename__ = 'Check_generic'
    id = db.Column(db.Integer(), primary_key=True)
    check_description = db.Column(db.String(500))
    ITC_check_map = db.relationship('ITC_check_map',
        backref = 'check')


class ITC(db.Model):
    __tablename__ = 'ITC'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    deliverable_id = db.Column(db.Integer(), db.ForeignKey('deliverable.id', ondelete='CASCADE'))
    ITC_check_map = db.relationship('ITC_check_map',
        backref='ITC')
    comment = db.Column(db.String(500))
