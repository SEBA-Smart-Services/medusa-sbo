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
config_name = os.getenv('MEDUSA_CONFIGURATION', 'default')
config = {
    "development": "config.DevelopmentConfig",
    "production": "config.ProductionConfig",
    "default": "config.DevelopmentConfig"
}

app.config.from_object(config[config_name])

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

# packages
from app import models, add, admin, cmms, weather, algorithms, reports, scheduling
# modules
from app import controllers
