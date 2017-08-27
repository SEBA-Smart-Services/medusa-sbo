import pandas
import numpy
import datetime
from app.algorithms import Algorithm

# check if room air temp is higher than setpoint while heating is on
class ZoneTempHeatingCheck(Algorithm):

    name = "zone temperature high while unit is heating"
    description = "zone temperature high while unit is heating"

    points_required = [
        'Room Air Temp',
        'Heater Enable',
        'Room Air Temp Setpoint'
    ]
    format = "{:.1%}"

    def run(data):
        # grab last 24 hours of data
        heating = data.latest_time('Heater Enable', datetime.timedelta(hours=24))
        room_temp = data.latest_time('Room Air Temp', datetime.timedelta(hours=24))
        room_setpoint = data.latest_time('Room Air Temp Setpoint', datetime.timedelta(hours=24))

        # resample to 1s intervals
        heating_seconds = heating.resample('1S').ffill()
        room_temp_seconds = room_temp.resample('1S').ffill()
        room_setpoint_seconds = room_setpoint.resample('1S').ffill()

        # put all the data into a single dataseries, so that timestamps are shared
        all_data = pandas.concat([heating_seconds,room_temp_seconds,room_setpoint_seconds], axis=1)
        # count the seconds where room temp > setpoint and heating is on
        seconds_in_error = len(numpy.where((all_data[1] < all_data[2]) & (all_data[0] == 1))[0])

        result = seconds_in_error/86400
        passed = result < 0.05
        return [result, passed]
