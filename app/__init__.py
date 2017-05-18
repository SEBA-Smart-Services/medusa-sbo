from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import boto3, os

# set up Flask
app = Flask(__name__)

# download and load config from s3
# if debug mode is running, downloading the file will cause a change which causes a
# second restart of debug mode. prevent this, except in the case where config.py is missing entirely
# and needs to be downloaded for the first time
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not os.path.exists('config.py'):
    s3 = boto3.resource('s3')
    s3.meta.client.download_file('medusa-sebbqld', 'config/config.py', 'config.py')

# choos which part of the config file to load
server_type = os.getenv('MEDUSA_CONFIGURATION', 'development')
config = {
    "development": "config.DevelopmentConfig",
    "production": "config.ProductionConfig"
}

app.config.from_object(config[server_type])

# set up database
db = SQLAlchemy(app)

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

# packages
from app import models, add, admin, cmms, weather, algorithms, reports, scheduling
# modules
from app import controllers
