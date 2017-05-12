from app import app, db
from CoolProp.HumidAirProp import HAPropsSI
from flask import render_template
from pyowm import OWM
from app.weather.models import Weather
from flask_user import roles_required
import pyowm

# get weather info from OpenWeatherMap via API
def get_weather():

	# get cache object
	weather_cache = Weather.query.filter_by(location='Brisbane').first()

	# if doesn't exist, then create
	if weather_cache is None:
		weather_cache = Weather(location='Brisbane', temperature=24, humidity=0.5)
		db.session.add(weather_cache)
		db.session.commit()

	try:
		# get weather info
		API_key = '810702d017860accf696debebee47df5'
		city_id = 2174003
		owm = OWM(API_key)
		weather_live = owm.weather_at_id(city_id).get_weather()
		temperature = weather_live.get_temperature(unit='celsius')['temp']
		humidity = weather_live.get_humidity() / 100
	except pyowm.exceptions.api_call_error.APICallError:
		# can't connect, so abort
		# TODO: don't abort, but instead display '-' for weather related stats on the UI
		return

	# store in cache
	weather_cache.temperature = temperature
	weather_cache.humidity = humidity
	db.session.commit()

	print('Weather recorded as {}C {}%'.format(weather_cache.temperature, weather_cache.humidity*100))

# show weather page
@app.route('/site/all/weather')
@roles_required('performance_centre')
def weather_page():

	# grab weather from cache
	weather = Weather.query.filter_by(location='Brisbane').first()

	if weather is None:
		get_weather()
		weather = Weather.query.filter_by(location='Brisbane').first()

	outside_t = weather.temperature
	outside_r = weather.humidity

	# calculate savings from setpoint offset
	setpoint = 24
	min_offset = -1
	min_temp = 19
	max_offset = 1
	max_temp = 29
	savings_per_degree = 7.5	# taken from gov website, need a better system for calculating savings

	offset = (outside_t - min_temp) / (max_temp - min_temp) * (max_offset - min_offset) + min_offset

	# bound offset
	offset = max(min_offset, min(max_offset, offset))

	savings = abs(offset * savings_per_degree)


	# calculate savings from economy cycle
	# estimates taken from 'typical' system. Should be improved upon later / in winter
	setpoint = setpoint + offset
	supply_t = setpoint - 6
	supply_r = 0.5
	return_t = setpoint + 1.5
	return_r = 0.6

	# calculate enthalpies
	supply_h = HAPropsSI('H', 'T', 273.15+supply_t, 'P', 101325, 'R', supply_r)
	outside_h = HAPropsSI('H', 'T', 273.15+outside_t, 'P', 101325, 'R', outside_r)
	return_h = HAPropsSI('H', 'T', 273.15+return_t, 'P', 101325, 'R', return_r)

	# is economy mode available. economy mode does not apply if we are in heating mode
	economy = (outside_h < return_h) and (outside_h > supply_h)

	# calculate power savings
	if economy == True:
		savings = savings + 100 - (outside_h - supply_h) / (return_h - supply_h) * 100

	return render_template('weather.html', offset=offset, economy=economy, savings=savings, allsites=True)
