from flask import jsonify
from app import app, db
from app.models import AssetPoint, LoggedEntity, LogTimeValue
from app.hvac_assets.utils import LogSampleFetcher

@app.route('/_pointdata/<int:asset_point_id>')
def get_pointdata(asset_point_id):
    """
    returns asset point log samples
    """
    data_fetcher = LogSampleFetcher(asset_point_id)
    samples = data_fetcher.range(as_list=True)

    app.logger.info(str(samples))
    
    return jsonify(
        testKey="penis",
        samples=samples
    )
