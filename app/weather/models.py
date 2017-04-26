from app import db

# model to cache weather data
class Weather(db.Model):
    id = db.Column('ID', db.Integer, primary_key=True)
    location = db.Column('Location', db.String(512))
    temperature = db.Column('Temperature', db.Float)
    humidity = db.Column('Humidity', db.Float)
