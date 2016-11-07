from app.models import Function, Asset
from app.checks import FunctionClass
from app import app, db

###################################
## mapping functions
###################################

# find all defined functions and add them to the database
def generate_functions():
    # functions are subclasses of FunctionClass
    for function in FunctionClass.__subclasses__():
        function_db = Function.query.filter_by(name=function.__name__).all()

        # if the function doesn't exist in the database, create it
        if function_db == None:
            function_db = Function(descr=function.descr, name=function.__name__)
            db.session.add(function_db)

    db.session.commit()
    return "done"

# generate the entire mapping tables for functions-components and functions-assets
def map_functions():
    for function in Function.query.all():
        function.map()
    db.session.commit()

# generate the entire mapping table for functions-assets
def map_assets():
    for asset in Asset.query.all():
        asset.map()
    db.session.commit()

