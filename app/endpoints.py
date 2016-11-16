from app import app, db
from app.models import LoggedEntity, LogTimeValue, Asset, AssetComponent, ComponentType, Result, Site
from app.checks import check_asset
from app.mapping import generate_algorithms, map_algorithms, map_asset_subtypes
from app.inbuildings import inbuildings_asset_request
from flask import request, render_template

###################################
## endpoint functions
###################################

@app.route('/<string:sitename>/assets')
def asset_list(sitename):
    site = Site.query.filter_by(name=sitename).one()
    return render_template('assets.html', assets=site.assets, site=site)

@app.route('/<string:sitename>/results')
def result_list(sitename):
    site = Site.query.filter_by(name=sitename).one()
    results = Result.query.all()
    return render_template('results.html', results=results, site=site)

# map algorithms in database
@app.route('/map')
def map_all():
    generate_algorithms()
    map_algorithms()
    return "Done"

# trigger check and get results for pre-selected asset
@app.route('/check/test')
def testcheck():
    # delete existing results table
    for result in Result.query.all():
        result.components.clear()
    Result.query.delete()
    asset = Asset.query.filter_by(id=1).first()
    check_asset(asset)
    result = get_results(asset.name)
    return result

# get check results for an asset as a string
@app.route('/check/<string:asset_name>')
def get_results(asset_name):
    asset = Asset.query.filter_by(name=asset_name).first()
    result = asset.health.summary
    return result

@app.route('/check/<string:asset_name>/tests')
def get_results_tests(asset_name):
    asset = Asset.query.filter_by(name=asset_name).first()
    result = asset.health.tests
    return result

@app.route('/check/<string:asset_name>/results')
def get_results_results(asset_name):
    asset = Asset.query.filter_by(name=asset_name).first()
    result = asset.health.results
    return result

@app.route('/check/<string:asset_name>/passed')
def get_results_passed(asset_name):
    asset = Asset.query.filter_by(name=asset_name).first()
    result = asset.health.passed
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

    # select database
    LoggedEntity.__table__.info['bind_key'] = asset.site.db_name

    # add components to database
    for component_type_name in component_list.keys():
        component_type = ComponentType.query.filter_by(name=component_type_name).one()
        trendlog_name = component_list[component_type_name][0]
        trendlog = LoggedEntity.query.filter(LoggedEntity.path.like('%' + trendlog_name)).one()
        new_component = AssetComponent(asset=asset, type=component_type, loggedentity_id=trendlog.id)
        asset.components.append(new_component)

    db.session.commit()
    return "Done"

# grab assets from inbuildings
@app.route('/getassets')
def get_assets():
    site = Site.query.first()
    inbuildings_asset_request(site)
    return "Done"

# provide result for a comms check
@app.route('/comms')
def comms():
    return "OK"

@app.route('/test')
def test():
    return "Test"