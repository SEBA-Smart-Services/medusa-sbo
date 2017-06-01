from app.scheduling import scheduler

# standalone process to be called as an uWSGI mule
# runs all the background tasks not tied to the web interface

if __name__ == "__main__":
    scheduler.start()
