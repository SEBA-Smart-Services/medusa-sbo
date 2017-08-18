from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os, ast, configparser
from flask_mail import Mail

# set up Flask
app = Flask(__name__)

# set config
app.config.from_envvar('MEDUSA_DEVELOPMENT_SETTINGS')

# initialise database models
db = SQLAlchemy(app)

# initialise Flask-Mail
mail = Mail(app)

from flask_security import Security, SQLAlchemyUserDatastore
from app.models.users import User, Role

#######################################################
# NEED TO MIGRATE THIS TO CFG FILE AND RMEOVE FROM CODE
# app.config['SECURITY_POST_CHANGE_VIEW'] = '/'
# app.config['SECURITY_POST_RESET_VIEW'] = '/'
# app.config['SECURITY_POST_CONFIRM_VIEW'] = 'security.change_password'
# app.config['USER_CHANGE_PASSWORD_URL'] = '/change'
######################################################

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# set up database connection registry
from app.models import SessionRegistry
registry = SessionRegistry()

# set up event handler
from app.event_handler import EventHandler
event = EventHandler()

# Setup Flask-User to handle user account related forms
from flask_user import UserManager, SQLAlchemyAdapter
from app.models import User
db_adapter = SQLAlchemyAdapter(db, User)  # Setup the SQLAlchemy DB Adapter
user_manager = UserManager(db_adapter, app)  # Init Flask-User and bind to app

# set up bugsnag
import bugsnag
from bugsnag.flask import handle_exceptions
bugsnag.configure(
  api_key = app.config['BUGSNAG_API_KEY'],
  project_root = app.config['PROJECT_ROOT'],
  notify_release_stages = app.config['NOTIFY_RELEASE_STAGES'],
  release_stage = app.config['RELEASE_STAGE']
)
handle_exceptions(app)

# import the remaining. in particular, all views and models must be imported, as well as anything with a decorator
# packages
from app import models, add, admin, cmms, weather, algorithms, reports, scheduling
# modules
from app import controllers
