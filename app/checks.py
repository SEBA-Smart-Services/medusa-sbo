from app.models import LogTimeValue, AssetHealth, Result
import datetime

###################################
## functional checks
###################################

# perform all the checks against a single asset
def check_asset(asset):
    result_string = ""

    # find all the component types belonging to this asset which are being checked
    for function in asset.functions:
        data={}
        for component in asset.components:
            if component.type in function.component_types:

                # add the trend log to a dictionary of data
                # currently only selects the newest 1000 entries
                value_list = LogTimeValue.query.filter_by(parent_id=component.loggedentity_id).order_by(LogTimeValue.datetimestamp.desc()).limit(1000).from_self().order_by(LogTimeValue.datetimestamp.asc()).all()
                data[component.type.name] = value_list

        # call each function which is mapped to the asset
        [result,passed] = function.run(data)
        save_result(asset,function,result,passed)

        # save results in a string to pass back to SBO
        result_string += "{}: {},  Result = {}\n".format(function.descr,"Passed" if passed==True else "Failed",result)

    # save results to asset health table
    health = 0.5
    health_db = AssetHealth(asset_id=asset.id, health=health, summary=result_string)
    db.session.merge(health_db)
    db.session.commit()
    
# dummy class used to access all the functional checks
# components_required specifies which components each function will request data for
class FunctionClass():
    pass
    
# check if room air temp is higher than setpoint while heating is on
class airtemp_heating_check(FunctionClass):
    components_required = ['Room Air Temp Sensor','Room Air Temp Setpoint','Heating Coil']
    name = "Room air temp higher than setpoint while heating on"
    def run(data):
        result = 0.1
        healthy = False
        return [result,healthy]

# check if heating and cooling are simultaneously on
class simult_heatcool_check(FunctionClass):
    components_required = ['Chilled Water Valve','Heating Coil']
    name = "Simultaneous heating and cooling"
    def run(data):
        totaltime = datetime.timedelta(0)
        result = datetime.timedelta(0)

        # for each chw data point, find the nearest (timestamp less than or equal to) data point for heating coil
        for i in range(1, len(data['Chilled Water Valve'])):
            
            current_time = data['Chilled Water Valve'][i].datetimestamp
            date_candidates = [value.datetimestamp for value in data['Heating Coil'] if value.datetimestamp < current_time]
            
            if len(date_candidates) > 0:
                current_time_matched = max(date_candidates)
                j = [value.datetimestamp for value in data['Heating Coil']].index(current_time_matched)

                # calculate duration of data sample, add to total time
                timediff = data['Chilled Water Valve'][i].datetimestamp - data['Chilled Water Valve'][i-1].datetimestamp
                totaltime += timediff

                # if heating and cooling are both on, add duration to time sum
                if data['Chilled Water Valve'][i].float_value > 0 and data['Heating Coil'][j].float_value > 0:
                    result += timediff
        
        # find percent of time that heating and cooling were simulaneously on
        result = result/totaltime
        healthy = True if result < 0.5 else False
        return [result,healthy]

# check if zone fan is on while zone is unoccupied
class fan_unoccupied_check(FunctionClass):
    components_required = ['Zone Fan','Zone Occupancy Sensor']
    name = "Zone fan on while unoccupied"
    def run(data):    
        result = 0
        healthy = True
        return [result,healthy]

# check if zone is occupied and AHU is off
class ahu_occupied_check(FunctionClass):
    components_required = ['Power Switch','Zone Occupancy Sensor']
    name = "Zone occupied, AHU off"
    def run(data):
        result = 0
        healthy = True
        return [result,healthy]

# check if chilled water valve actuator is hunting
class chw_hunting_check(FunctionClass):
    components_required = ['Chilled Water Valve']
    name = "Chilled water valve actuator hunting"
    def run(data):
        result = False
        healthy = True
        return [result,healthy]

# check the run hours
class run_hours_check(FunctionClass):
    components_required = ['Power Switch']
    name = "Run hours"
    def run(data):
        result = 0

        # add up durations for each sample where power was on
        for i in range(1, len(data['Power Switch'])):
            timediff = data['Power Switch'][i].datetimestamp - data['Power Switch'][i-1].datetimestamp
            result += timediff.total_seconds() * data['Power Switch'][i].float_value

        #convert to hours
        result = result/3600
        healthy = False
        return [result,healthy]

# dummy test fuction
class testfunc(FunctionClass):
    components_required = []
    name = "Test"
    def run(data):
        print("Test!")
        #print(data.keys())
        result = True
        healthy = True
        return [result,healthy]

# save the check results
def save_result(asset,function,value,passed):
    result = Result(timestamp=datetime.datetime.now(), asset_id=asset.id, function_id=function.id, value=value, passed=passed, unresolved=not passed)
    db.session.add(result)
    db.session.commit()