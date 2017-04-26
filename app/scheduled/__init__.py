from . import tasks
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler

# set up scheduler
scheduler = BlockingScheduler()
backgroundscheduler = BackgroundScheduler()

# load jobs
from config import add_jobs
add_jobs([scheduler, backgroundscheduler])
