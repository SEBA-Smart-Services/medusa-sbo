from . import tasks
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler

# set up scheduler
scheduler = BlockingScheduler()
backgroundscheduler = BackgroundScheduler()

# load jobs
from . import config
