from flask import Flask, request, flash, url_for, redirect, render_template, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Resource, fields, marshal, marshal_with, Api, reqparse
from distutils.util import strtobool
from flask_apscheduler import APScheduler

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
scheduler = APScheduler()
scheduler.init_app(app)