from app import app, models, checks, mapping, inbuildings, endpoints

models.db.create_all(bind='medusa')
app.run(debug=True, host='0.0.0.0')