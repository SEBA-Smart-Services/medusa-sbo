from app.models import LogTimeValue, Result, Asset
from app import db, app
import datetime, time, pandas

class DataGrab():

    @classmethod
    def latest_qty(cls, log_id, quantity):
        value_list = LogTimeValue.query.filter_by(parent_id=log_id).order_by(LogTimeValue.datetimestamp.desc()).limit(quantity).all()
        return cls.to_dataframe(value_list)

    @classmethod
    def latest_time(cls, log_id, time):
        value_list = LogTimeValue.query.filter(LogTimeValue.parent_id == log_id, LogTimeValue.datetimestamp >= time).all()
        return cls.to_dataframe(value_list)

    def to_dataframe(logtimevalue_list):
        timestamps = [entry.datetimestamp for entry in value_list]
        values = [entry.float_value for entry in value_list]
        dataframe = pandas.DataFrame(values, index=timestamps)
        return dataframe

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
                values = DataGrab.latest(component.loggedentity_id, 1000)
                data[component.type.name] = value_list
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
        totaltime = datetime.timedelta(0)
        result = datetime.timedelta(0)

        # for each air temp data point, find the nearest (timestamp less than or equal to) data point for setpoint and heater
        for i in range(1, len(data['Room Air Temp'])):
            
            current_time = data['Room Air Temp'][i].datetimestamp
            j = find_nearest_date(data['Room Air Temp Setpoint'], current_time)
            k = find_nearest_date(data['Heater Enable'], current_time)
            
            if not j is None and not k is None:
                # calculate duration of data sample, add to total time
                timediff = data['Room Air Temp'][i].datetimestamp - data['Room Air Temp'][i-1].datetimestamp
                totaltime += timediff

                # if room air temp > setpoint while heating is on, add duration to time sum
                if data['Room Air Temp'][i].float_value > data['Room Air Temp Setpoint'][j].float_value and data['Heater Enable'][k].float_value > 0:
                    result += timediff
            
        # find percent of time that the conditions were true
        result = result/totaltime
        passed = True if result < 0.2 else False
        return [result, passed]

# check if heating and cooling are simultaneously on
class simult_heatcool_check(AlgorithmClass):
    components_required = ['Heater Enable', 'Chilled Water Valve Enable']
    name = "Simultaneous heating and cooling"
    format = "{:.1%}"

    def run(self, data):
        totaltime = datetime.timedelta(0)
        result = datetime.timedelta(0)
        
        # for each chw data point, find the nearest (timestamp less than or equal to) data point for heater
        for i in range(1, len(data['Chilled Water Valve Enable'])):
            
            current_time = data['Chilled Water Valve Enable'][i].datetimestamp
            j = find_nearest_date(data['Heater Enable'], current_time)
            
            if not j is None:
                # calculate duration of data sample, add to total time
                timediff = data['Chilled Water Valve Enable'][i].datetimestamp - data['Chilled Water Valve Enable'][i-1].datetimestamp
                totaltime += timediff

                # if heating and cooling are both on, add duration to time sum
                if data['Chilled Water Valve Enable'][i].float_value > 0 and data['Heater Enable'][j].float_value > 0:
                    result += timediff
            
        # find percent of time that heating and cooling were simulaneously on
        result = result/totaltime
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
        timeon = 0

        # add up durations for each sample where fan was on
        for i in range(1, len(data['Fan Enable'])):
            timediff = data['Fan Enable'][i].datetimestamp - data['Fan Enable'][i-1].datetimestamp
            timeon += timediff.total_seconds() * data['Fan Enable'][i].float_value

        #convert to hours
        result = timeon/3600
        passed = True if result < data['Run Hours Maintenance Setpoint'][0].float_value else False
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