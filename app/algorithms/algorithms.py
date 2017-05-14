from app.models import LogTimeValue, Result, Asset, AssetPoint
from app import db, app, registry, event
import datetime
import time
import pandas
import numpy
import random
from scipy.fftpack import fft


# class used to select data
class DataGrab():

    def __init__(self, session, asset):
        self.session = session
        self.asset = asset

    # grab a fixed number of samples
    def latest_qty(self, point_name, quantity):
        point = AssetPoint.query.filter(AssetPoint.type.has(name=point_name), AssetPoint.asset==self.asset).one()
        value_list = self.session.query(LogTimeValue).filter_by(parent_id=point.loggedentity_id).order_by(LogTimeValue.datetimestamp.desc()).limit(quantity).all()
        return self.to_series(value_list)

    # grab a time-based range of samples, ending at now
    def latest_time(self, point_name, timedelta):
        point = AssetPoint.query.filter(AssetPoint.type.has(name=point_name), AssetPoint.asset==self.asset).one()
        value_list = self.session.query(LogTimeValue).filter(LogTimeValue.parent_id == point.loggedentity_id, LogTimeValue.datetimestamp >= datetime.datetime.now()-timedelta).all()
        return self.to_series(value_list)

    # grab a time-based range of samples, with defined start and end time
    def time_range(self, point_name, timedelta_start, timedelta_finish):
        point = AssetPoint.query.filter(AssetPoint.type.has(name=point_name), AssetPoint.asset==self.asset).one()
        value_list = self.session.query(LogTimeValue).filter(LogTimeValue.parent_id == point.loggedentity_id, LogTimeValue.datetimestamp >= datetime.datetime.now()-timedelta_start, \
            LogTimeValue.datetimestamp <= datetime.datetime.now()-timedelta_finish).all()
        return self.to_series(value_list)

    # convert samples to Pandas Series object
    def to_series(self, logtimevalue_list):
        timestamps = [entry.datetimestamp for entry in logtimevalue_list]
        values = [entry.float_value for entry in logtimevalue_list]

        # if list is empty, index is automatically assigned as Index rather than DatetimeIndex. So manually fix this
        if logtimevalue_list == []:
            timestamps = pandas.DatetimeIndex([])
        series = pandas.Series(values, index=timestamps)
        return series


###################################
# algorithm checks
###################################


# apply all the algorithms against a single asset
def check_asset(asset):

    # get database session for this asset
    session = registry.get(asset.site.db_key)

    if not session is None:
        datagrab = DataGrab(session, asset)

        # clear 'recent' status on previous results
        for result in Result.query.filter_by(asset=asset, recent=True):
            result.recent = False

        # get list of previously active results. result that are still active will be removed from this list
        # the remainder will be set to inactive
        previously_active = set(Result.query.filter_by(asset=asset, active=True).all())

        algorithms_run = 0
        algorithms_passed = 0
        t = time.time()

        for algorithm in set(asset.algorithms) - set(asset.exclusions):

            point_list = []

            # find all the point types belonging to this asset which are being checked by this algorithm
            for point in asset.points:
                if point.type in algorithm.point_types:
                    point_list.append(point)

            # call each algorithm which is mapped to the asset
            [result, passed] = algorithm.run(datagrab)

            # save result to result table
            result = save_result(asset, algorithm, result, passed, point_list)

            # call event handler on result
            event.handle_result(result)

            algorithms_run += 1
            algorithms_passed += passed

            # remove result from group to be set to inactive
            previously_active.discard(result)

        # set all remaining results to inactive
        for result in previously_active:
            result.active = False

        # save asset health. Currently computed as just the percentage of algorithms passed
        if algorithms_run > 0:
            sum_issue_health_impact=0
            for result in Result.query.filter_by(asset=asset, active=True):
                #asset health calculation is:
                #100-sum(issue_health_impact)
                #where issue_health_impact = issue_priority_weighting*result_value

                #create a weighting scale for the issues based on their priority
                #value from 0->1 i.e 0 to 100%
                #for now, issue priority 1=25%, 2=20%, 3=15%, 4=10%, 5=5%
                #ie an issue with a priority of 1 has a 25% impact on the asset health
                issue_priority_weighting = (25-((result.priority-1)*5))/100.00
                #define the impact an issue has to the asset health as:
                #issue weighting*result value (assume result value is percentage from 0-1)
                issue_health_impact = issue_priority_weighting*result.value

                #sum all of the issue health impacts together
                sum_issue_health_impact+=issue_health_impact

            #the health of the asset is 100% - the sum of the health impact of all of the issues

            print('Asset Health: {}'.format(asset.health))

        else:
            asset.health = 0
        db.session.commit()
        print('Ran checks on {} - {}, took {}'.format(asset.site.name, asset.name, time.time()-t))

        session.close()

    else:
        print('Could not connect to database for {} - {}'.format(asset.site.name, asset.name))


# run algorithms on all assets
def check_all():
    for asset in Asset.query.all():
        check_asset(asset)
    db.session.close()


# dummy class used to access all the algorithm checks
# 'points_required' specifies which points each algorithm will request data for
# 'functions_required' specifies the functional descriptors that the algorithm requires to operate
class AlgorithmClass():
    points_required = []
    functions_required = []


# check if room air temp is higher than setpoint while heating is on
class airtemp_heating_check(AlgorithmClass):
    points_required = ['Room Air Temp', 'Heater Enable', 'Room Air Temp Setpoint']
    name = "Air temp higher than setpoint while heating on"
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


# check if heating and cooling are simultaneously on
class simult_heatcool_check(AlgorithmClass):
    points_required = ['Heater Enable', 'Chilled Water Valve Enable']
    name = "Simultaneous heating and cooling"
    format = "{:.1%}"

    def run(data):
        # grab last 24 hours of data
        heating = data.latest_time('Heater Enable', datetime.timedelta(hours=24))
        cooling = data.latest_time('Chilled Water Valve Enable', datetime.timedelta(hours=24))

        # resample to 1s intervals
        heating_seconds = heating.resample('1S').ffill()
        cooling_seconds = cooling.resample('1S').ffill()

        # combine the dataseries. in the new one, 0 = no heating/cooling
        # 1 = heating or cooling, and 2 = both heating and cooling
        status = heating_seconds + cooling_seconds

        # grab only the entries where heating and cooling is occuring
        heating_and_cooling = status[status == 2]
        seconds_heating_and_cooling = len(heating_and_cooling)
        result = seconds_heating_and_cooling/86400
        passed = result == 0
        return [result, passed]


# check if zone fan is on while zone is unoccupied
class fan_unoccupied_check(AlgorithmClass):
    points_required = ['Room Occupancy', 'Fan Enable']
    name = "Zone fan on while unoccupied"
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
class ahu_occupied_check(AlgorithmClass):
    points_required = ['Room Occupancy', 'Fan Enable']
    name = "Zone occupied, AHU off"
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


# check if chilled water valve actuator is hunting.
# in this algorithm, we are checking the fourier transform for signs of an oscillating signal.
# the idea is that an unstable pid loop will show up as a magnitude in the high frequency range (e.g more than 1 oscillation per hour).
# we transform the data to the right format (i.e. interval data), perform a fft, ignore all the low frequency oscillations, then add up what's left.
# if the sum of the high frequencies is large, then there's some oscillation going on. use a tuning parameter to decide how large is 'too large'
class chw_hunting_check(AlgorithmClass):
    points_required = ['Chilled Water Valve 100%']
    name = "Chilled water valve actuator hunting"
    format = "bool"

    def run(data):
        # using units of minutes in this algorithm
        # only check for oscilations with a period of less than 60 minutes
        min_period = 1/60.0
        freq_sums = {}

        for hours in range(24, 1, -1):
            # grab an hour of data
            valve = data.time_range('Chilled Water Valve 100%', datetime.timedelta(hours=hours), datetime.timedelta(hours=hours-1))
            # FFT needs evenly spaced samples to work. Resample to 1 minute rather than 1 second because computationally expensive - gives max resolution of 1 oscillation per 2 minutes
            # up (interpolate) and downsample (first) since the sample rate is unknown and variable. assuming a COV trend here
            valve_mins = valve.resample('1Min').first().interpolate(method='quadratic')

            N = len(valve_mins)
            if N > 0:
                # perform fft
                x_fft = numpy.linspace(0, 1, N)
                valve_fft = fft(valve_mins)

                i = numpy.argmax(x_fft > min_period)
                # we only care about oscillations faster than our min period. Also only take half the range since the FFT is mirrored, avoid doubling up
                sum_range = valve_fft[i:int(N/2)]

                # metric to judge overall instability, sum of high frequencies
                freq_sums[hours] = sum(numpy.abs(sum_range))
            else:
                freq_sums[hours] = 0

        # this is the tuning parameter
        freq_cutoff = 100

        result = max(freq_sums) > freq_cutoff
        passed = not result

        return [result, passed]


# check the run hours
class run_hours_check(AlgorithmClass):
    points_required = ['Fan Enable', 'Run Hours Maintenance Setpoint']
    name = "Run hours exceeded limit"
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


# dummy test fuction
class testfunc(AlgorithmClass):
    points_required = []
    name = "Test"
    format = "{:.1%}"

    def run(data):
        result = 0.5
        passed = True
        return [result, passed]

# test functions for demo purposes
class testfunc2(AlgorithmClass):
    points_required = ['filter sp']
    name = "Chilled water valve actuator hunting temperature"
    format = "{:.1%}"

    def run(data):
        result = 1
        passed = random.random() > 0.25
        return [result, passed]

class testfunc3(AlgorithmClass):
    points_required = ['filter sp']
    name = "Slow room air temp response to conditioning"
    format = "{:.1%}"

    def run(data):
        result = 1
        passed = random.random() > 0.25
        return [result, passed]

class testfunc4(AlgorithmClass):
    points_required = ['filter sp']
    name = "Malfunctioning heating coil"
    format = "{:.1%}"

    def run(data):
        result = 0.75
        passed = random.random() > 0.25
        return [result, passed]

class testfunc5(AlgorithmClass):
    points_required = ['filter sp']
    name = "Simultaneous heating and cooling"
    format = "{:.1%}"

    def run(data):
        result = 0.8
        passed = random.random() > 0.25
        return [result, passed]


# save the check results
def save_result(asset, algorithm, value, passed, point_list):
    # find existing results that are active
    result = Result.query.filter(Result.asset_id==asset.id, Result.algorithm_id==algorithm.id, (Result.active==True) | (Result.acknowledged==False)).first()
    # note: do not change the acknowledged state, if the result already exists

    # or create a new one if none
    if result is None:
        result = Result(first_timestamp=datetime.datetime.now(), asset_id=asset.id, algorithm_id=algorithm.id, occurances=0, priority=asset.priority)
        result.acknowledged = passed
        db.session.add(result)

    result.recent_timestamp = datetime.datetime.now()
    result.value = value
    result.passed = passed
    result.active = not passed
    result.occurances += 1
    result.points = point_list
    result.recent = True
    db.session.commit()

    return result
