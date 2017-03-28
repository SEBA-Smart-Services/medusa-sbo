binds = {
    #'sbo':      'mssql+pyodbc://admin:password@MedusaTest\SQLEXPRESS/StruxureWareReportsDB?driver=SQL+Server+Native+Client+10.0',
    'medusa':   'mssql+pyodbc://admin:password@192.168.1.10\SQLEXPRESS/Medusa?driver=SQL+Server+Native+Client+10.0'
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
    },
    # {
    #     'id': 'inbuildings_assets',
    #     'func': 'app.inbuildings.controllers:inbuildings_all_sites',
    #     'trigger': 'interval',
    #     'hours': 24,
    # },
    {
    	'id': 'record_issues',
    	'func': 'app.scheduled:record_issues',
    	'trigger': 'interval',
    	'minutes': 15,
    },
    {
        'id': 'register_components',
        'func': 'app.scheduled:register_components',
        'trigger': 'interval',
        'minutes': 1,
    },
    # {
    #     'id': 'get_weather',
    #     'func': 'app.weather.controllers:get_weather',
    #     'trigger': 'interval',
    #     'minutes': 30,
    # },
]

SCHEDULER_VIEWS_ENABLED = True