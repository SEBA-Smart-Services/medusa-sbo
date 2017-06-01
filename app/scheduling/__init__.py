from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
import app

# set up scheduler
# blocking scheduler if it has its own process
# background scheduler if it's running in the same process as flask
scheduler = BlockingScheduler()
backgroundscheduler = BackgroundScheduler()

# load jobs
jobs = app.app.config.get('JOBS')
for job_scheduler in [scheduler, backgroundscheduler]:
    for job in jobs:
        # convert the job function from string to an object
        # TODO: CURRENTLY USES EVAL. THIS IS VERY RISKY. SHOULD CHANGE
        # also, because we are configuring two schedulers we operate twice on the same object
        # therefore check if it has already been 'evaled' before evaling
        if isinstance(job['func'], str):
            job['func'] = eval(job['func'])

        # add the job by directly passing in the kwargs
        job_scheduler.add_job(**job)
