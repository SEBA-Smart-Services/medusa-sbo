from app.models import LogTimeValue, Result, Asset, AssetPoint
from app import db, app, event
import datetime
import time
import pandas
import numpy
import random
from scipy.fftpack import fft


# class used to select data from a webreports server and present it in a useful format for algorithms
# instances are specific to each asset
# functions require you to specify the name of the point type as a string - this can be improved, and will not work
# if there are multiple of the same type of point
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

    session = db.session

    # skip all checks if it can't connect
    if not session is None:
        datagrab = DataGrab(session, asset)

        # clear 'recent' status on previous results
        for result in Result.query.filter_by(asset=asset, recent=True):
            result.recent = False

        # get list of previously active results. result that are still active will be removed from this list as we go
        # the remainder will be set to inactive
        previously_active = set(Result.query.filter_by(asset=asset, active=True).all())

        algorithms_run = 0
        algorithms_passed = 0
        t = time.time()

        # run all algorithms that have not been excluded
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

        # if no algorithms are being run, mark as unhealthy
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
# these are used when mapping the algorithms to the assets
class AlgorithmClass():
    points_required = []
    functions_required = []

class Algorithm():
    points_required = []
    functions_required = []



# dummy test fuction
class testfunc(Algorithm):
    points_required = []
    name = "Test"
    format = "{:.1%}"

    def run(data):
        result = 0.5
        passed = True
        return [result, passed]

# test functions for demo purposes
class testfunc2(Algorithm):
    points_required = ['filter sp']
    name = "Chilled water valve actuator hunting temperature."
    format = "{:.1%}"

    def run(data):
        result = 1
        passed = random.random() > 0.25
        return [result, passed]

class testfunc3(Algorithm):
    points_required = ['filter sp']
    name = "Slow room air temp response to conditioning."
    format = "{:.1%}"

    def run(data):
        result = 1
        passed = random.random() > 0.25
        return [result, passed]

class testfunc4(Algorithm):
    points_required = ['filter sp']
    name = "Malfunctioning heating coil."
    format = "{:.1%}"

    def run(data):
        result = 0.75
        passed = random.random() > 0.25
        return [result, passed]

class testfunc5(Algorithm):
    points_required = ['filter sp']
    name = "Simultaneous heating and cooling."
    format = "{:.1%}"

    def run(data):
        result = 0.8
        passed = random.random() > 0.25
        return [result, passed]


# save the algorithm results
def save_result(asset, algorithm, value, passed, point_list):
    # find existing results that are active, or were active and are still unacknowledged
    result = Result.query.filter(Result.asset_id==asset.id, Result.algorithm_id==algorithm.id, (Result.active==True) | (Result.acknowledged==False)).first()
    # note: do not change the acknowledged state, if the result already exists

    # or create a new one if none
    if result is None:
        result = Result(first_timestamp=datetime.datetime.now(), asset_id=asset.id, algorithm_id=algorithm.id, occurances=0, priority=asset.priority)
        result.acknowledged = passed
        db.session.add(result)

    # update with details of the algorithm check
    result.recent_timestamp = datetime.datetime.now()
    result.value = value
    result.passed = passed
    result.active = not passed
    result.occurances += 1
    result.points = point_list
    result.recent = True
    db.session.commit()

    return result
