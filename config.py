binds = {
    'sbo':      'mssql+pyodbc://admin:password@MedusaTest\SQLEXPRESS/StruxureWareReportsDB?driver=SQL+Server+Native+Client+10.0',
    'medusa':   'mssql+pyodbc://admin:password@MedusaTest\SQLEXPRESS/Medusa?driver=SQL+Server+Native+Client+10.0'
}
SQLALCHEMY_BINDS = binds
SECRET_KEY = 'random string'
SQLALCHEMY_TRACK_MODIFICATIONS = False
JSON_AS_ASCII = True
TEMPLATES_AUTO_RELOAD = True

JOBS = [
    {
        'id': 'runchecks',
        'func': 'app.algorithms:check_all',
        'trigger': 'interval',
        'minutes': 15,
        'misfire_grace_time': 10
    },
    # {
    #     'id': 'inbuildings_assets',
    #     'func': 'app.inbuildings.controllers:inbuildings_all_sites',
    #     'trigger': 'interval',
    #     'hours': 24,
    #     'misfire_grace_time': 10
    # },
    {
    	'id': 'record_issues',
    	'func': 'app.scheduled:record_issues',
    	'trigger': 'interval',
    	'minutes': 15,
    	'misfire_grace_time': 10
    }
    # {
    #     'id': 'get_weather',
    #     'func': 'app.weather.controllers:get_weather',
    #     'trigger': 'interval',
    #     'minutes': 30,
    #     'misfire_grace_time': 10
    # }
]

SCHEDULER_VIEWS_ENABLED = True