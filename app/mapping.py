from app.models import Algorithm, Asset
from app.algorithms import AlgorithmClass
from app import db, app

###################################
## mapping functions
###################################

# find all defined algorithms and add them to the database
def generate_algorithms():
    # algorithms are subclasses of AlgorithmClass
    for algorithm in AlgorithmClass.__subclasses__():
        algorithm_db = Algorithm.query.filter_by(name=algorithm.__name__).first()

        # if the algorithm doesn't exist in the database, create it
        if algorithm_db == None:
            algorithm_db = Algorithm(descr=algorithm.name, name=algorithm.__name__)
            db.session.add(algorithm_db)
            algorithm_db.map()

    db.session.commit()

# generate the entire mapping tables for algorithms-components and algorithms-asset subtypes
def map_algorithms():
    for algorithm in Algorithm.query.all():
        algorithm.map()
    db.session.commit()

# generate the entire mapping table for algorithms-asset subtypes
def map_asset_subtypes():
    for asset_subtype in AssetSubtype.query.all():
        asset_subtype.map()
    db.session.commit()

# route for manual triggering of mapping
@app.route('/map')
def map_all():
    generate_algorithms()
    map_algorithms()
    return "Done"