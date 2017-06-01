from app import app

# this section is only called if the file is run manually, and not via uWSGI
# useful for testing
if __name__ == "__main__":
    from app.scheduling import backgroundscheduler
    import os
    # prevents scheduler from running twice - flask uses 2 instances in debug mode
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        backgroundscheduler.start()

    app.run(threaded=True, debug=True, host='0.0.0.0')
