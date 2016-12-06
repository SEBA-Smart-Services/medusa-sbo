from app.models import LogTimeValue, Result, Asset
from app import db, app
import datetime, time, pandas, random

class DataGrab():

    @classmethod
    def latest_qty(cls, component, quantity):
        value_list = LogTimeValue.query.filter_by(parent_id=component.loggedentity_id).order_by(LogTimeValue.datetimestamp.desc()).limit(quantity).all()
        return cls.to_series(value_list)

    @classmethod
    def latest_time(cls, component, time):
        value_list = LogTimeValue.query.filter(LogTimeValue.parent_id == component.loggedentity_id, LogTimeValue.datetimestamp >= time).all()
        return cls.to_series(value_list)

    def to_series(logtimevalue_list):
        timestamps = [entry.datetimestamp for entry in logtimevalue_list]
        values = [entry.float_value for entry in logtimevalue_list]
        series = pandas.Series(values, index=timestamps)
        return series

###################################
## algorithm checks
###################################

# apply all the algorithms against a single asset
def check_asset(asset):
    summary_string = ""
    tests_string = ""
    results_string = ""
    passed_string = ""

    # clear 'most recent' status on previous results
    for result in Result.query.filter_by(asset=asset, recent=True):
        result.recent = False

    algorithms_run = 0
    algorithms_passed = 0
    t=time.time()

    for algorithm in set(asset.subtype.algorithms) - set(asset.exclusions):
        data={}
        component_list = []

        # find all the component types belonging to this asset which are being checked by this algorithm
        for component in asset.components:
            if component.type in algorithm.component_types:
                # set the database that the trend log resides in print(logtimevalue.table.info(bindkey))
                LogTimeValue.__table__.info['bind_key'] = asset.site.db_name
                # add the trend log to a dictionary of data
                # currently only selects the newest 1000 entries
                values = DataGrab.latest_qty(component, 1000)
                data[component.type.name] = values
                component_list.append(component)

        # call each algorithm which is mapped to the asset
        [result, passed] = algorithm.run(data)

        # save result to result table
        save_result(asset, algorithm, result, passed, component_list)

        algorithms_run += 1
        algorithms_passed += passed

    # save results to asset health table
    asset.health = algorithms_passed/algorithms_run
    db.session.commit()
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
    format = "{:.1%}"
    def run(data):
        result = random.random()
        passed = True if result < 0.2 else False
        return [result, passed]

# check if heating and cooling are simultaneously on
class simult_heatcool_check(AlgorithmClass):
    components_required = ['Heater Enable', 'Chilled Water Valve Enable']
    name = "Simultaneous heating and cooling"
    format = "{:.1%}"

    def run(data):
        result = random.random()
        passed = True if result < 0.2 else False
        return [result, passed]

# check if zone fan is on while zone is unoccupied
class fan_unoccupied_check(AlgorithmClass):
    components_required = ['Room Occupancy', 'Fan Enable']
    name = "Zone fan on while unoccupied"
    format = "{:.1%}"
    def run(data):    
        result = 0
        passed = True
        return [result, passed]

# check if zone is occupied and AHU is off
class ahu_occupied_check(AlgorithmClass):
    components_required = ['Room Occupancy', 'Fan Enable']
    name = "Zone occupied, AHU off"
    format = "{:.1%}"
    def run(data):
        result = 0
        passed = True
        return [result, passed]

# check if chilled water valve actuator is hunting
class chw_hunting_check(AlgorithmClass):
    components_required = ['Chilled Water Valve', 'Supply Air Temp']
    name = "Chilled water valve actuator hunting"
    format = "bool"
    def run(data):
        result = False
        passed = True
        return [result, passed]

# check the run hours
class run_hours_check(AlgorithmClass):
    components_required = ['Fan Enable', 'Run Hours Maintenance Setpoint']
    name = "Run hours"
    format = "{:.1f}h"
    def run(data):
        # timeon = 0

        # # add up durations for each sample where fan was on
        # for i in range(1, len(data['Fan Enable'])):
        #     timediff = data['Fan Enable'][i].datetimestamp - data['Fan Enable'][i-1].datetimestamp
        #     timeon += timediff.total_seconds() * data['Fan Enable'][i].float_value

        # #convert to hours
        # result = timeon/3600
        # passed = True if result < data['Run Hours Maintenance Setpoint'][0].float_value else False
        result = random.random()
        passed = True if result < 0.5 else False
        return [result, passed]

# dummy test fuction
class testfunc(AlgorithmClass):
    components_required = []
    name = "Test"
    format = "bool"
    def run(data):
        #print("Test!")
        #print(data.keys())
        result = True
        passed = True
        return [result, passed]

# save the check results
def save_result(asset, algorithm, value, passed, component_list):
    result = Result(timestamp=datetime.datetime.now(), asset_id=asset.id, algorithm_id=algorithm.id, value=value, passed=passed, status_id=int(not passed)+1, components=component_list, recent=True)
    db.session.add(result)
    db.session.commit()

# find the index of the nearest less than or equal to timestamp in a log
def find_nearest_date(data, timestamp):
    date_candidates = [value.datetimestamp for value in data if value.datetimestamp <= timestamp]
    if len(date_candidates) > 0:
        current_time_matched = max(date_candidates)
        index = date_candidates.index(current_time_matched)
    return index