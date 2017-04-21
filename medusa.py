# from init file
from app import app
from app.scheduled import backgroundscheduler
import os

# prevents scheduler from running twice - flask uses 2 instances in debug mode
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
	backgroundscheduler.start()

# run app. Host 0.0.0.0 allows any incoming ip adresses to access the server
app.run(threaded=True, debug=True, host='0.0.0.0')
