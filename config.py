binds = {
    'sbo':      'mssql+pyodbc://admin:password@MedusaTest\SQLEXPRESS/StruxureWareReportsDB?driver=SQL+Server+Native+Client+10.0',
    'medusa':   'mssql+pyodbc://admin:password@MedusaTest\SQLEXPRESS/Medusa?driver=SQL+Server+Native+Client+10.0'
}
SQLALCHEMY_BINDS = binds
SECRET_KEY = 'random string'
SQLALCHEMY_TRACK_MODIFICATIONS = False
JSON_AS_ASCII = True

JOBS = [
    {
        'id': 'runchecks',
        'func': 'app.algorithms:check_all',
        'trigger': 'interval',
        'minutes': 2,
        'misfire_grace_time': 10
    },
    {
        'id': 'inbuildings_assets',
        'func': 'app.inbuildings.controllers:inbuildings_all_sites',
        'trigger': 'interval',
        'hours': 24,
        'misfire_grace_time': 10
    }
]

SCHEDULER_VIEWS_ENABLED = True