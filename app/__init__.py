from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

from . import models
from .weather import models
db.create_all(bind='medusa')

from app.models import SessionRegistry
registry = SessionRegistry()

scheduler = APScheduler()
scheduler.init_app(app)

from app.mapping import map_all
map_all()