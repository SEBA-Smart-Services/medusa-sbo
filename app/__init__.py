from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler

# set up Flask
app = Flask(__name__)
app.config.from_object('config')

# set up database
db = SQLAlchemy(app)

# set up database connection registry
from app.models import SessionRegistry
registry = SessionRegistry()

# set up scheduler
scheduler = APScheduler()
scheduler.init_app(app)

# THIS MUST BE MOVED, ALONG WITH  mapping.py TO OUTSIDE OF THE PRODUCTION APP
# re-map all algorithms, as these may have been edited
# from app.mapping import map_all
# map_all()
