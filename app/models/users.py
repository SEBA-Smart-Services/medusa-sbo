from app import db
from app.models.ITP import ITC_check_map, Deliverable_ITC_map
# from app.ticket.models import FlicketTicket
from flask_security import UserMixin, RoleMixin


# Define the User data model. Make sure to add the flask_user.UserMixin !!
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)

    # User authentication information (required for Flask-User)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, server_default='')
    password_active = db.Column(db.Boolean())
    password_change_date = db.Column(db.DateTime())

    company = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)

    active = db.Column(db.Boolean(), nullable=False, server_default='0')
    authenticated = db.Column(db.Boolean, default=False)
    last_login_at = db.Column(db.DateTime())
    current_login_at = db.Column(db.DateTime())
    last_login_ip = db.Column(db.String(100))
    current_login_ip = db.Column(db.String(100))
    login_count = db.Column(db.Integer)
    confirmed_at = db.Column(db.DateTime())

    # Relationships
    roles = db.relationship('Role', secondary='users_roles',
                            backref=db.backref('users', lazy='dynamic'))
    sites = db.relationship('Site', secondary='users_sites',
                            backref=db.backref('users', lazy='dynamic'))
    Deliverable_ITC = db.relationship('Deliverable_check_map', backref='user')

    ######################
    # commented out until issue #8 resolved_by_id
    # https://github.com/SEBA-Smart-Services/medusa-sbo/issues/8

    ticket_start_id = db.relationship('FlicketTicket',

                        primaryjoin="User.id == FlicketTicket.started_id")
    ticket_assigned_id = db.relationship('FlicketTicket',
                         primaryjoin="User.id == FlicketTicket.assigned_id")
    ticket_resolve_id = db.relationship('FlicketTicket',

                        primaryjoin="User.id == FlicketTicket.resolved_by_id")
    ticket_modified_id = db.relationship('FlicketTicket',
                        primaryjoin="User.id == FlicketTicket.modified_id")

    def __repr__(self):
        return self.email

    # def is_active(self):
    #     return True
    #
    # def get_id(self):
    #     print(self.id)
    #     return self.email
    #
    # def is_authenticated(self):
    #     return self.authenticated
    #
    # def is_anonymous(self):
    #     return False

# Define the Role data model
class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), nullable=False, server_default=u'', unique=True)  # for @roles_accepted()
    label = db.Column(db.Unicode(255), server_default=u'')  # for display purposes

    def __repr__(self):
        return self.name


# Define the UserRoles association model
class UsersRoles(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('role.id', ondelete='CASCADE'))

# association between users and sites
class UsersSites(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
    site_id = db.Column(db.Integer(), db.ForeignKey('site.ID', ondelete='CASCADE'))
