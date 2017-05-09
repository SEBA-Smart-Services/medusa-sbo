from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# set up Flask
app = Flask(__name__)
app.config.from_object('config')

# set up database
db = SQLAlchemy(app)

# set up database connection registry
from app.models import SessionRegistry
registry = SessionRegistry()

# set up event handler
from app.event_handler import EventHandler
event = EventHandler()

# packages
from app import models, add, admin, cmms, weather, algorithms, scheduling, reports
# modules
from app import controllers
