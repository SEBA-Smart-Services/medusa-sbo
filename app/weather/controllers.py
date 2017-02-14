from app import app
from CoolProp.HumidAirProp import HAPropsSI
from flask import render_template
from pyowm import OWM
from app.weather.models import Weather

# get weather info from OpenWeatherMap via API
def get_weather():
	# get weather info
	API_key = '810702d017860accf696debebee47df5'
	city_id = 2174003
	owm = OWM(API_key)
	weather_live = owm.weather_at_id(city_id).get_weather()

	# store in cache
	weather_cache = Weather()
	weather_cache.temperature = weather.get_temperature(unit='celsius')['temp']
	weather_cache.humidity = weather.get_humidity() / 100

	print('Weather recorded as {}C {}%').format(weather_cache.temperature, weather_cache.humidity*100)

# show weather page
@app.route('/site/all/weather')
def weather_page():
	
	weather = Weather.query.filter_by(location='Brisbane').one()
	outside_t = weather.temperature
	outside_r = weather.humidity
	supply_t = 16
	supply_r = 0.5
	return_t = 26
	return_r = 0.5

	# calculate enthalpies
	supply_h = HAPropsSI('H','T',273.15+supply_t,'P',101325,'R',supply_r)
	outside_h = HAPropsSI('H','T',273.15+outside_t,'P',101325,'R',outside_r)
	return_h = HAPropsSI('H','T',273.15+return_t,'P',101325,'R',return_r)

	# is economy mode available
	economy = outside_h < return_h

	# calculate power savings
	if economy == True:
		if outside_h < supply_h:
			savings = 100
		else:
			savings = 100 - (outside_h - supply_h) / (return_h - supply_h) * 100
	else:
		savings = 0

	return render_template('weather.html', economy=economy, savings=savings, allsites=True)