from app.administration import views
from app import app, models, checks, mapping, inbuildings, views

models.db.create_all(bind='medusa')
app.run(threaded=True, debug=True, host='0.0.0.0')