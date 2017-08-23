from flask import request, render_template, url_for, redirect, jsonify
from app import app, db
from app.models import Site
from app.sitedataagent.forms import SiteAgentConfigForm
from app.sitedataagent.models import SiteDataUploader
from app.sitedataagent.aws_utils import AwsIamManager

# site config page
@app.route('/site/<sitename>/config/sitedataagent', methods=['GET','POST'])
def site_data_agent(sitename):
    # no POST of data to this url, handled by jquery to endpoint below.
    site = Site.query.filter_by(name=sitename).one()

    form = SiteAgentConfigForm()
    ##
    access_key = {
        "is_enabled": False,
        "access_key_id": None,
        "secret_access_key": None
    }

    uploader_exists = db.session.query(db.exists().where(SiteDataUploader.site_id==site.id)).one()[0]
    if uploader_exists:
        uploader = SiteDataUploader.query.filter_by(site_id=site.id).one()
        access_key["is_enabled"] = uploader.enabled
        access_key["access_key_id"] = uploader.aws_access_key_id
        access_key["secret_access_key"] = uploader.aws_secret_access_key
    else:
        uploader = None
    # try:
    #     uploader = SiteDataUploader.query.filter_by(site_id=site.id).one()
    # except Exception as e:
    #     uploader = None

    # temporary!!!, replace with model to db!
    # access_key = {
    #     "is_enabled": "not working yet",
    #     "access_key_id": "not working yet 123",
    #     "secret_access_key": "not working yet 456"
    # }
    if request.method == 'GET':
        # return (str(site) + str(uploader))
        return render_template('site_settings/site_data_agent.html', site=site, access_key=access_key)

@app.route('/_generate_access_keys/<int:site_id>')
def generate_access_keys(site_id):
    # create IAM object from AWS utils
    iam = AwsIamManager(site_id)

    # get enabled state of site data agent from client over ajax
    is_enabled_ajax = request.args.get('isChecked', 0, type=int)
    # jquery ajax var isChecked sends int 0 as False and int 1 as True
    if is_enabled_ajax == 0:
        is_enabled = False
    else:
        is_enabled = True

    ########
    # SECURITY: need to protect this endpoint with a pre-generated token
    ########
    # delete IAM user and access keys before generating a new set
    resp = iam.delete_access_key()
    resp = iam.delete_user()

    # check if site data agent is enabled
    if is_enabled:
        resp = iam.create_user()
        resp = iam.create_access_key()
        access_key_id = iam.access_key_id
        secret_access_key = iam.secret_access_key
    else:
        access_key_id = None
        secret_access_key = None

    # get record from sitedatauploader table or instantiate a new one if none
    # check if record for site exists in sitedatauploader table
    uploader_exists = db.session.query(db.exists().where(SiteDataUploader.site_id==site_id)).one()[0]
    if uploader_exists:
        uploader = SiteDataUploader.query.filter_by(site_id=site_id).one()
    else:
        # if doesnt exist already, create record
        uploader = SiteDataUploader()
        uploader.site_id = site_id
        uploader.aws_username = iam.aws_s3_uploader_iam_username
        db.session.add(uploader)

    uploader.enabled = is_enabled
    uploader.aws_username = iam.aws_s3_uploader_iam_username
    uploader.aws_access_key_id = access_key_id
    uploader.aws_secret_access_key = secret_access_key

    db.session.commit()

    return jsonify(
        accessKeyId=access_key_id,
        secretAccessKey=secret_access_key,
        isEnabled=str(is_enabled)
    )
