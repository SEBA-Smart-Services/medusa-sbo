from app import app

if __name__ == "__main__":

    if app.config['USE_UWSGI'] == False:
        from app.scheduled import backgroundscheduler
        import os
        # prevents scheduler from running twice - flask uses 2 instances in debug mode
        if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        	backgroundscheduler.start()

    threaded = not app.config['USE_UWSGI']
    app.run(threaded=threaded, debug=app.config['USE_DEBUG'], host='0.0.0.0')
