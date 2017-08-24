from app import app, db
from app.models import Site

@app.route('/_pointdata/<int:asset_point_id>')
def get_pointdata(asset_point_id):
    """
    returns asset point log samples
    """

    return jsonify(
        testKey="penis"
    )
