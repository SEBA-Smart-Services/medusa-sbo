from app.algorithms import Algorithm

# check if heating and cooling are simultaneously on
class SimultnsHeatCool(Algorithm):

    name = "simultaneous heating and cooling"
    description = "simultaneous heating and cooling"

    points_required = [
        'Heater Enable',
        'Chilled Water Valve Enable'
    ]
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
