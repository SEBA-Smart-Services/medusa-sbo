import datetime
from app.algorithms import Algorithm

# check if zone fan is on while zone is unoccupied
class UnitRunZoneUnoccupied(Algorithm):

    name = "unit running while zones unoccupied"
    description = "unit running while zones unoccupied"

    points_required = [
        'Room Occupancy',
        'Fan Enable'
    ]
    format = "{:.1%}"

    def run(data):
        # grab last 24 hours of data
        occupancy = data.latest_time('Room Occupancy', datetime.timedelta(hours=24))
        enable = data.latest_time('Fan Enable', datetime.timedelta(hours=24))

        # resample to 1s intervals
        occupancy_seconds = occupancy.resample('1S').ffill()
        enable_seconds = enable.resample('1S').ffill()

        # combine into new dataseries, where -1 = occupied but not enabled
        # 0 = occupied and enabled, and 1 = enabled but not occupied
        status = enable_seconds - occupancy_seconds

        # grab only the entries with value 1
        occupied_while_off = status[status == 1]
        seconds_occupied_while_off = len(occupied_while_off)
        result = seconds_occupied_while_off/86400
        passed = result < 0.05

        return [result, passed]


# check if zone is occupied and AHU is off
class UnitOffZoneOccupied(Algorithm):

    name = "unit off while zone is occupied"
    description = "unit off while zone is occupied"

    points_required = [
        'Room Occupancy',
        'Fan Enable'
    ]
    format = "{:.1%}"

    def run(data):
        # grab last 24 hours of data
        occupancy = data.latest_time('Room Occupancy', datetime.timedelta(hours=24))
        enable = data.latest_time('Fan Enable', datetime.timedelta(hours=24))

        # resample to 1s intervals
        occupancy_seconds = occupancy.resample('1S').ffill()
        enable_seconds = enable.resample('1S').ffill()

        # combine into new dataseries, where -1 = occupied but not enabled
        # 0 = occupied and enabled, and 1 = enabled but not occupied
        status = enable_seconds - occupancy_seconds

        # grab only the entries with value -1
        occupied_while_off = status[status == -1]
        seconds_occupied_while_off = len(occupied_while_off)
        result = seconds_occupied_while_off/86400
        passed = result < 0.05

        return [result, passed]
