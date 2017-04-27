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

# packages
from app import add, admin, cmms, weather, algorithms, scheduled
# modules
from app import models, controllers
