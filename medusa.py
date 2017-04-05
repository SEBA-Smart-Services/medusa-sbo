# from init file
from app import app, db, scheduler
# packages
from app import add, admin, cmms, weather, algorithms
# modules
from app import models, mapping, controllers

import os

# generate any tables in the database that are missing, based on models
db.create_all(bind='medusa')

# prevents scheduler from running twice - flask uses 2 instances in debug mode
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
	scheduler.start()

# run app. Host 0.0.0.0 allows any incoming ip adresses to access the server
app.run(threaded=True, debug=True, host='0.0.0.0')