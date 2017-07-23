from app import db

################################
#Project models
################################
class Project(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.String(500))
    site_id = db.Column(db.Integer(), db.ForeignKey('site.ID', ondelete='CASCADE'))
    ITP = db.relationship('ITP',
        backref = 'project')

    def __init__(self, name, description, site_id):
        self.name = name
        self.description = description
        self.site_id = site_id

    def __repr__(self):
        return self.name

class Location(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), unique=True)
    deliverable = db.relationship('Deliverable',
        backref = 'location')

    def __repr__(self):
        return self.name

class ITP(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    project_id = db.Column(db.Integer(), db.ForeignKey('project.id', ondelete='CASCADE'))
    deliverable = db.relationship('Deliverable',
        backref = 'ITP')
    status = db.Column(db.String(200))
    percentage_complete = db.Column(db.Integer())

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
    deliverable_type_id = db.Column(db.Integer(), db.ForeignKey('deliverable_type.id', ondelete='CASCADE'))
    location_id = db.Column(db.Integer(), db.ForeignKey('location.id', ondelete='CASCADE'))
    ITP_id = db.Column(db.Integer(), db.ForeignKey('ITP.id', ondelete='CASCADE'))
    Deliverable_ITC_map = db.relationship('Deliverable_ITC_map',
        backref = 'deliverable')

    def __init__(self, name, deliverable_type_id, location_id, ITP_id):
        self.name = name
        self.deliverable_type_id = deliverable_type_id
        self.location_id = location_id
        self.ITP_id = ITP_id

    def __repr__(self):
        return self.name

###############################
#Section on ITCs
###############################

class Check_generic(db.Model):
    __tablename__ = "Check_generic"
    id = db.Column(db.Integer(), primary_key=True)
    check_description = db.Column(db.String(500))
    ITC_check_map = db.relationship('ITC_check_map',
        backref = 'check')

    def __repr__(self):
        return self.check_description

class ITC(db.Model):
    __tablename__ = "ITC"
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255))
    ITC_check_map = db.relationship('ITC_check_map',
        backref='ITC')
    deliverable_type_id = db.Column(db.Integer(), db.ForeignKey('deliverable_type.id'))
    deliverable_ITC_map = db.relationship('Deliverable_ITC_map',
        backref='ITC')

    def __init__(self, name, deliverable_type_id):
        self.name = name
        self.deliverable_type_id = deliverable_type_id

    def __repr__(self):
        return self.name

###############################
#Section on mapping
###############################

# many-many mapping table defining checks in an ITC
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

class Deliverable_ITC_map(db.Model):
    __tablename__ = "Deliverable_ITC_map"
    id = db.Column(db.Integer(), primary_key=True)
    deliverable_id = db.Column(db.Integer(), db.ForeignKey('deliverable.id', ondelete='CASCADE'))
    ITC_id = db.Column(db.Integer(), db.ForeignKey('ITC.id', ondelete='CASCADE'))
    deliverable_check_map = db.relationship('Deliverable_check_map',
        backref='deliver_ITC',
        primaryjoin="Deliverable_ITC_map.id == Deliverable_check_map.deliverable_ITC_map_id")

    def __init__(self, deliverable_id, ITC_id):
        self.deliverable_id = deliverable_id
        self.ITC_id = ITC_id

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

    def __init__(self, deliverable_ITC_id, ITC_check_id):
        self.deliverable_ITC_id = deliverable_ITC_id
        self.ITC_check_id = ITC_check_id
        self.status = "Not Started"
