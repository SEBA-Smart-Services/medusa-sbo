from app.models import LogTimeValue, AssetHealth, Result
from app import db
import datetime

###################################
## algorithm checks
###################################

# perform all the checks against a single asset
def check_asset(asset):
    summary_string = ""
    tests_string = ""
    results_string = ""
    passed_string = ""

    # clear 'most recent' status on previous results
    for result in Result.query.filter_by(asset=asset, recent=True):
        result.recent = False

    for algorithm in set(asset.subtype.algorithms) - set(asset.exclusions):
        data={}
        component_list = []

        # find all the component types belonging to this asset which are being checked by this algorithm
        for component in asset.components:
            if component.type in algorithm.component_types:
                # set the database that the trend log resides in
                LogTimeValue.__table__.info['bind_key'] = asset.site.db_name
                # add the trend log to a dictionary of data
                # currently only selects the newest 1000 entries
                value_list = LogTimeValue.query.filter_by(parent_id=component.loggedentity_id).order_by(LogTimeValue.datetimestamp.desc()).limit(1000).from_self().order_by(LogTimeValue.datetimestamp.asc()).all()
                data[component.type.name] = value_list
                component_list.append(component)

        # call each algorithm which is mapped to the asset
        [result, passed] = algorithm.run(data)

        # save result to result table
        save_result(asset, algorithm, result, passed, component_list)

        # save results in a string to pass back to SBO
        summary_string += "{}: {},  Result = {}\n".format(algorithm.descr,"Passed" if passed==True else "Failed",result)
        tests_string += "{}\n".format(algorithm.descr)
        passed_string += "{}\n".format("Passed" if passed==True else "Failed")
        results_string += "{}\n".format(result)


    # save results to asset health table
    health = 0.5
    health_db = AssetHealth(asset_id=asset.id, health=health, summary=summary_string, tests=tests_string, results=results_string, passed=passed_string)
    db.session.merge(health_db)
    db.session.commit()
    
# dummy class used to access all the algorithm checks
# 'components_required' specifies which components each algorithm will request data for
class AlgorithmClass():
    pass
    
# check if room air temp is higher than setpoint while heating is on
class airtemp_heating_check(AlgorithmClass):
    components_required = ['Room Air Temp', 'Heater Enable', 'Room Air Temp Setpoint']
    name = "Room air temp higher than setpoint while heating on"
    def run(data):
        result = 0.1
        passed = False
        return [result, passed]

# check if heating and cooling are simultaneously on
class simult_heatcool_check(AlgorithmClass):
    components_required = ['Heater Enable', 'Chilled Water Valve Enable']
    name = "Simultaneous heating and cooling"
    def run(data):
        totaltime = datetime.timedelta(0)
        result = datetime.timedelta(0)

        # for each chw data point, find the nearest (timestamp less than or equal to) data point for heater
        for i in range(1, len(data['Chilled Water Valve Enable'])):
            
            current_time = data['Chilled Water Valve Enable'][i].datetimestamp
            date_candidates = [value.datetimestamp for value in data['Heater Enable'] if value.datetimestamp < current_time]
            
            if len(date_candidates) > 0:
                current_time_matched = max(date_candidates)
                j = [value.datetimestamp for value in data['Heater Enable']].index(current_time_matched)

                # calculate duration of data sample, add to total time
                timediff = data['Chilled Water Valve Enable'][i].datetimestamp - data['Chilled Water Valve Enable'][i-1].datetimestamp
                totaltime += timediff

                # if heating and cooling are both on, add duration to time sum
                if data['Chilled Water Valve Enable'][i].float_value > 0 and data['Heater Enable'][j].float_value > 0:
                    result += timediff
        
        # find percent of time that heating and cooling were simulaneously on
        result = result/totaltime
        passed = True if result < 0.5 else False
        return [result, passed]

# check if zone fan is on while zone is unoccupied
class fan_unoccupied_check(AlgorithmClass):
    components_required = ['Room Occupancy', 'Fan Enable']
    name = "Zone fan on while unoccupied"
    def run(data):    
        result = 0
        passed = True
        return [result, passed]

# check if zone is occupied and AHU is off
class ahu_occupied_check(AlgorithmClass):
    components_required = ['Room Occupancy', 'Fan Enable']
    name = "Zone occupied, AHU off"
    def run(data):
        result = 0
        passed = True
        return [result, passed]

# check if chilled water valve actuator is hunting
class chw_hunting_check(AlgorithmClass):
    components_required = ['Chilled Water Valve', 'Supply Air Temp']
    name = "Chilled water valve actuator hunting"
    def run(data):
        result = False
        passed = True
        return [result, passed]

# check the run hours
class run_hours_check(AlgorithmClass):
    components_required = ['Fan Enable', 'Run Hours Maintenance Setpoint']
    name = "Run hours"
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
    def run(data):
        print("Test!")
        #print(data.keys())
        result = True
        passed = True
        return [result, passed]

# save the check results
def save_result(asset, algorithm, value, passed, component_list):
    result = Result(timestamp=datetime.datetime.now(), asset_id=asset.id, algorithm_id=algorithm.id, value=value, passed=passed, unresolved=not passed, components=component_list, recent=True)
    db.session.add(result)
    db.session.commit()