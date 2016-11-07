from app import app, db
from app.models import LoggedEntity, LogTimeValue, Asset, Component, ComponentType
from app.checks import check_asset
from app.mapping import generate_functions, map_functions, map_assets
from app.inbuildings import inbuildings_asset_request
from flask import request

###################################
## endpoint functions
###################################

# return a value from a trendlog	
@app.route('/<string:logname>/<int:seqno>')
def sql_test(logname,seqno):
    # search for the trendlog based on it's name
    # danger here if two trendlogs are named the same thing
    trendlog_entity = LoggedEntity.query.filter(LoggedEntity.path.like('%' + logname)).first()
    trend_value = LogTimeValue.query.filter_by(parent_id = trendlog_entity.id, seqno = seqno).first().float_value
    return str(trend_value)

# map functions in database
@app.route('/map')
def map_all():
    generate_functions()
    map_functions()
    return "Done"

# trigger check and get results for pre-selected asset
@app.route('/check/test')
def testcheck():
    # delete existing results table
    db.session.query(Result).delete()
    asset = Asset.query.filter_by(id=2).first()
    check_asset(asset)
    result = get_results(asset.name)
    return result

# get check results for an asset as a string
@app.route('/check/<string:asset_name>')
def get_results(asset_name):
    asset = Asset.query.filter_by(name=asset_name).first()
    result = asset.health.summary
    return result

# update components belonging to an asset
@app.route('/update', methods=['POST'])
def update():
    asset = Asset.query.filter_by(name=request.values['asset']).one()

    # delete existing components
    asset.components.clear()

    # get components from POST data
    component_list = request.values.to_dict(flat=False)
    component_list.pop('asset')

    # add components to database
    for component_type_name in component_list.keys():
        component_type = ComponentType.query.filter_by(name=component_type_name).one()
        trendlog_name = component_list[component_type_name][0]
        trendlog = LoggedEntity.query.filter(LoggedEntity.path.like('%' + trendlog_name)).one()
        new_component = Component(asset=asset, type=component_type, loggedentity_id=trendlog.id)
        asset.components.append(new_component)

    # redo asset mapping
    asset.map_all()

    db.session.commit()
    return "Done"

# grab assets from inbuildings
@app.route('/assets')
def get_assets():
    inbuildings_asset_request()
    return "Done"