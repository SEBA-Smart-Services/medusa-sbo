from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import boto3, os

# set up Flask
app = Flask(__name__)

# download and load config from s3
# if debug mode is running, downloading the file will cause a change which causes a
# second restart of debug mode. prevent this
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    s3 = boto3.resource('s3')
    s3.meta.client.download_file('medusa-sebbqld', 'config/config.py', 'config.py')

# above code prevents config from being downloaded by debugger
# if config.py has been deleted, then debugger will need to download before startup (debug starts before main)
try:
    app.config.from_object('config')
except:
    s3 = boto3.resource('s3')
    s3.meta.client.download_file('medusa-sebbqld', 'config/config.py', 'config.py')
    app.config.from_object('config')

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
