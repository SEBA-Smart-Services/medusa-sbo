from flask import request, render_template, url_for, redirect, jsonify
from app import app
from app.models import Site
from app.sitedataagent.forms import SiteAgentConfigForm
from app.sitedataagent.aws_utils import AwsIamManager

# site config page
@app.route('/site/<sitename>/config/sitedataagent', methods=['GET','POST'])
def site_data_agent(sitename):
    # no POST of data to this url, handled by jquery to endpoint below.
    site = Site.query.filter_by(name=sitename).one()

    form = SiteAgentConfigForm()
    ##
    # temporary!!!, replace with model to db!
    access_key = {
        "is_enabled": "not working yet",
        "access_key_id": "not working yet 123",
        "secret_access_key": "not working yet 456"
    }
    if request.method == 'GET':
        return render_template('site_settings/site_data_agent.html', site=site, access_key=access_key)

@app.route('/_generate_access_keys/<int:site_id>')
def generate_access_keys(site_id):
    # create IAM object from AWS utils
    iam = AwsIamManager(site_id)
    # get enabled state of site data agent from client over ajax
    is_enabled_ajax = request.args.get('isChecked', 0, type=int)
    ########
    # SECURITY: need to protect this endpoint with a pre-generated token
    ########
    resp = iam.delete_access_key()
    resp = iam.delete_user()
    if is_enabled_ajax == 0:
        is_enabled = False
        access_key_id = str(None)
        secret_access_key = str(None)
    else:
        is_enabled = True
        resp = iam.create_user()
        resp = iam.create_access_key()
        access_key_id = iam.access_key_id
        secret_access_key = iam.secret_access_key
        resp = iam.delete_access_key()
        delete_resp = iam.delete_user()

    return jsonify(
        accessKeyId=access_key_id,
        secretAccessKey=secret_access_key,
        isEnabled=str(is_enabled)
    )
