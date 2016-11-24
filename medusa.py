from app.admin import controllers
from app.inbuildings import controllers
from app import app, db, scheduler, models, algorithms, mapping, controllers

db.create_all(bind='medusa')
# prevents scheduler from running twice - flask uses 2 instances in debug mode
if not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
	scheduler.start()
app.run(threaded=True, debug=True, host='0.0.0.0')