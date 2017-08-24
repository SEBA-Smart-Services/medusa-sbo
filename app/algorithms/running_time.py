import datetime
from app.algorithms import Algorithm

# check the run hours
class RunningTime(Algorithm):

    name = "unit running time exceeds scheduled maintenance limit"
    description = "unit running time exceeds scheduled maintenance limit"

    points_required = [
        'Fan Enable',
        'Run Hours Maintenance Setpoint'
    ]
    format = "{:.1f}h"

    def run(data):
        # grab last 24 hours of data
        enable = data.latest_time('Fan Enable', datetime.timedelta(hours=24),)
        setpoint = data.latest_qty('Run Hours Maintenance Setpoint', 1)

        # resample to 1s intervals
        seconds_active = enable.resample('1S').ffill().sum()

        result = seconds_active / 3600
        passed = seconds_active < setpoint[0]
        
        return [result, passed]
