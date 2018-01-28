from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os, ast, configparser
from flask_mail import Mail
from celery import Celery

# set up Flask
app = Flask(__name__)

# set config
app.config.from_envvar('MEDUSA_DEVELOPMENT_SETTINGS')
#app.config.from_envvar('MEDUSA_PRODUCTION_SETTINGS')

# initialise database models
db = SQLAlchemy(app)

# initialise Flask-Mail
mail = Mail(app)

from flask_security import Security, SQLAlchemyUserDatastore
from app.models.users import User, Role

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

#prompting
from flask_script import Manager
manager = Manager(app)

# setup Celery asynchronus methods
#celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
#celery.conf.update(app.config)
celery = Celery(app.name, backend=app.config['CELERY_BROKER_URL'], broker='amqp://localhost')

from app import controllers

# each component of the application should be packaged into a standalone package
# consider refactoring as Flask Blueprints
from app.sitedataagent import controllers, models
from app.ict import controllers
from app.ticket import controllers, models
from app.alarms import controllers
from app.hvac_assets import controllers

# import the remaining. in particular, all views and models must be imported, as well as anything with a decorator
# packages
from app import models, admin, cmms, weather, algorithms, reports, scheduling

from app.scheduled.tasks import register_points

app.logger.info('registering points...')
#register_points()
