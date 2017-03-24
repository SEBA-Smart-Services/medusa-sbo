from app.models import LogTimeValue, Result, Asset, AssetComponent
from app import db, app, registry
import datetime, time, pandas, random, numpy, scipy
from scipy.fftpack import fft

# class used to select data
class DataGrab():

    def __init__(self, session, asset):
        self.session = session
        self.asset = asset

    def latest_qty(self, component_name, quantity):
        component = AssetComponent.query.filter_by(name=component_name).one()
        value_list = self.session.query(LogTimeValue).filter_by(parent_id=component.loggedentity_id).order_by(LogTimeValue.datetimestamp.desc()).limit(quantity).all()
        return self.to_series(value_list)

    def latest_time(self, component_name, timedelta):
        component = AssetComponent.query.filter_by(name=component_name).one()
        value_list = self.session.query(LogTimeValue).filter(LogTimeValue.parent_id == component.loggedentity_id, LogTimeValue.datetimestamp >= datetime.datetime.now()-timedelta).all()
        return self.to_series(value_list)

    def time_range(self, component_name, timedelta_start, timedelta_finish):
        component = AssetComponent.query.filter_by(name=component_name).one()
        value_list = self.session.query(LogTimeValue).filter(LogTimeValue.parent_id == component.loggedentity_id, LogTimeValue.datetimestamp >= datetime.datetime.now()-timedelta_start, \
            LogTimeValue.datetimestamp <= datetime.datetime.now()-timedelta_finish).all()
        return self.to_series(value_list)

    def to_series(self, logtimevalue_list):
        timestamps = [entry.datetimestamp for entry in logtimevalue_list]
        values = [entry.float_value for entry in logtimevalue_list]
        series = pandas.Series(values, index=timestamps)
        return series

###################################
## algorithm checks
###################################

# apply all the algorithms against a single asset
def check_asset(asset):

    # get database session for this asset
    session = registry.get(asset.site.db_name)
    datagrab = DataGrab(session, asset)

    # clear 'most recent' status on previous results
    for result in Result.query.filter_by(asset=asset, recent=True):
        result.recent = False

    algorithms_run = 0
    algorithms_passed = 0
    t = time.time()

    for algorithm in set(asset.subtype.algorithms) - set(asset.exclusions):
        #data = {}
        component_list = []

        # find all the component types belonging to this asset which are being checked by this algorithm
        for component in asset.components:
            if component.type in algorithm.component_types:
                # set the database that the trend log resides in print(logtimevalue.table.info(bindkey))
                #LogTimeValue.__table__.info['bind_key'] = asset.site.db_name
                # add the trend log to a dictionary of data
                # currently only selects the newest 1000 entries
                #values = DataGrab.latest_qty(component, 1000)
                #data[component.type.name] = values
                component_list.append(component)

        # call each algorithm which is mapped to the asset
        [result, passed] = algorithm.run(datagrab)

        # save result to result table
        save_result(asset, algorithm, result, passed, component_list)

        algorithms_run += 1
        algorithms_passed += passed

    # save results to asset health table
    asset.health = algorithms_passed/algorithms_run
    session.commit()
    print('Ran checks on {}, took {}'.format(asset.name,time.time()-t))

@app.route('/check')
# run algorithms on all assets
def check_all():
    for asset in Asset.query.all():
        for result in Result.query.filter(Result.asset==asset, Result.status_id not in [1,5]).all():
            result.status_id = 1
        check_asset(asset)
    return 'done'
    
# dummy class used to access all the algorithm checks
# 'components_required' specifies which components each algorithm will request data for
class AlgorithmClass():
    pass
    
# check if room air temp is higher than setpoint while heating is on
class airtemp_heating_check(AlgorithmClass):
    components_required = ['Room Air Temp', 'Heater Enable', 'Room Air Temp Setpoint']
    name = "Air temp higher than setpoint while heating on"
    format = "{:.1%}"

    def run(data):
        heating = data.latest_time('Heater Enable', datetime.timedelta(hours=24))
        room_temp = data.latest_time('Room Air Temp', datetime.timedelta(hours=24))
        room_setpoint = data.latest_time('Room Air Temp Setpoint', datetime.timedelta(hours=24))

        heating_seconds = heating.resample('1S').ffill()
        room_temp_seconds = room_temp.resample('1S').ffill()
        room_setpoint_seconds = room_setpoint.resample('1S').ffill()

        all_data = pandas.concat([heating_seconds,room_temp_seconds,room_setpoint_seconds], axis=1)
        seconds_in_error = len(numpy.where((all_data[1] < all_data[2]) & (all_data[0] == 1))[0])

        result = seconds_in_error/86400
        passed = result < 0.05
        return [result, passed]

# check if heating and cooling are simultaneously on
class simult_heatcool_check(AlgorithmClass):
    components_required = ['Heater Enable', 'Chilled Water Valve Enable']
    name = "Simultaneous heating and cooling"
    format = "{:.1%}"

    def run(data):
        heating = data.latest_time('Heater Enable', datetime.timedelta(hours=24))
        cooling = data.latest_time('Chilled Water Valve Enable', datetime.timedelta(hours=24))

        heating_seconds = heating.resample('1S').ffill()
        cooling_seconds = cooling.resample('1S').ffill()

        status = heating_seconds + cooling_seconds
        heating_and_cooling = status[status == 2]
        seconds_heating_and_cooling = len(heating_and_cooling)
        result = seconds_heating_and_cooling/86400
        passed = result == 0
        return [result, passed]

# check if zone fan is on while zone is unoccupied
class fan_unoccupied_check(AlgorithmClass):
    components_required = ['Room Occupancy', 'Fan Enable']
    name = "Zone fan on while unoccupied"
    format = "{:.1%}"

    def run(data):    
        occupancy = data.latest_time('Room Occupancy', datetime.timedelta(hours=24))
        enable = data.latest_time('Fan Enable', datetime.timedelta(hours=24))

        occupancy_seconds = occupancy.resample('1S').ffill()
        enable_seconds = enable.resample('1S').ffill()

        status = enable_seconds - occupancy_seconds
        occupied_while_off = status[status == 1]
        seconds_occupied_while_off = len(occupied_while_off)
        result = seconds_occupied_while_off/86400
        passed = result < 0.05
        return [result, passed]

# check if zone is occupied and AHU is off
class ahu_occupied_check(AlgorithmClass):
    components_required = ['Room Occupancy', 'Fan Enable']
    name = "Zone occupied, AHU off"
    format = "{:.1%}"

    def run(data):

        occupancy = data.latest_time('Room Occupancy', datetime.timedelta(hours=24))
        enable = data.latest_time('Fan Enable', datetime.timedelta(hours=24))

        occupancy_seconds = occupancy.resample('1S').ffill()
        enable_seconds = enable.resample('1S').ffill()

        status = enable_seconds - occupancy_seconds
        occupied_while_off = status[status == -1]
        seconds_occupied_while_off = len(occupied_while_off)
        result = seconds_occupied_while_off/86400
        passed = result < 0.05
        return [result, passed]

# check if chilled water valve actuator is hunting
class chw_hunting_check(AlgorithmClass):
    components_required = ['Chilled Water Valve']
    name = "Chilled water valve actuator hunting"
    format = "bool"

    def run(data):
        # using units of minutes in this algorithm
        # only check for oscilations with a period of less than 60 minutes
        min_period = 1/60
        freq_sums = {}
        
        for hours in range(24, 0, -1):
            valve = data.time_range('Chilled Water Valve', datetime.timedelta(hours=hours), datetime.timedelta(hours=hours-1))
            # FFT needs evenly spaced samples to work. Resample to 1 minute rather than 1 second because computationally expensive - gives max resolution of 1 oscillation per 2 minutes
            # up (interpolate) and downsample (first) since the sample rate is unknown and variable
            valve_mins = valve.resample('1Min').first().interpolate(method='quadratic')

            N = len(valve_mins)
            x_fft = numpy.linspace(0, 1, N)
            valve_fft = fft(valve_mins)

            i = numpy.argmax(x_fft > min_period)
            # we only care about oscillations faster than our min period. Also only take half the range since the FFT is mirrored, avoid doubling up
            sum_range = valve_fft[i:int(N/2)]

            # metric to judge overall instability, sum of frequency components
            freq_sums[hours] = sum(numpy.abs(sum_range))

        # this is the tuning parameter
        freq_cutoff = 100

        result = max(freq_sums) > freq_cutoff
        passed = not result

        return [result, passed]

# check the run hours
class run_hours_check(AlgorithmClass):
    components_required = ['Fan Enable', 'Run Hours Maintenance Setpoint']
    name = "Run hours exceeded limit"
    format = "{:.1f}h"

    def run(data):

        enable = data.latest_time('Fan Enable', datetime.timedelta(hours=24),)
        setpoint = data.latest_qty('Run Hours Maintenance Setpoint', 1)

        seconds_active = enable.resample('1S').ffill().sum()

        result = seconds_active/3600
        passed = seconds_active < setpoint[0]
        return [result, passed]

# dummy test fuction
class testfunc(AlgorithmClass):
    components_required = []
    name = "Test"
    format = "bool"

    def run(data):
        #print("Test!")
        result = True
        passed = True
        return [result, passed]

# save the check results
def save_result(asset, algorithm, value, passed, component_list):
    result = Result(timestamp=datetime.datetime.now(), asset_id=asset.id, algorithm_id=algorithm.id, value=value, passed=passed, status_id=int(not passed)+1, components=component_list, recent=True)
    db.session.add(result)
    db.session.commit()