from flask import Flask, request, flash, url_for, redirect, render_template, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, fields, marshal, marshal_with, Api, reqparse
from distutils.util import strtobool
from flask_apscheduler import APScheduler

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
db.create_all(bind='medusa')

from app.models import SessionRegistry
registry = SessionRegistry()

scheduler = APScheduler()
scheduler.init_app(app)

from app.mapping import map_all
map_all()