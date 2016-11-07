binds = {
    'sbo':      'mssql+pyodbc://admin:password@MedusaTest\SQLEXPRESS/StruxureWareReportsDB?driver=SQL+Server+Native+Client+10.0',
    'medusa':   'mssql+pyodbc://admin:password@MedusaTest\SQLEXPRESS/Medusa?driver=SQL+Server+Native+Client+10.0'
}
SQLALCHEMY_BINDS = binds
SECRET_KEY = 'random string'
SQLALCHEMY_TRACK_MODIFICATIONS = False
JSON_AS_ASCII = True