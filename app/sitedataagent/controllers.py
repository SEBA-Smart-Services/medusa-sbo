import os, shutil
import zipfile
import random
import string
from io import BytesIO
from flask import request, render_template, url_for, redirect, jsonify, send_file, make_response
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

    if request.method == 'GET':
        # return (str(site) + str(uploader))
        return render_template('site_settings/site_data_agent.html', site=site, access_key=access_key)

@app.route('/_generate_access_keys/<int:site_id>')
def generate_access_keys(site_id):
    """
    generates AWS user and access key for site data agent, writes to DB,
    returns values to client via jquery
    """
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


@app.route('/_download_dataagent_config/<int:site_id>')
def download_dataagent_config(site_id):
    """
    downloads site data agent config files as zip
    """

    DATA_AGENT_TEMPLATE = app.config["DATA_AGENT_TEMPLATE"]
    CHIMERA_TEMPLATE = app.config["CHIMERA_TEMPLATE"]
    TEMP_STORAGE = "/tmp"

    class ConfigGenerator(object):

        def __init__(self):
            pass

        def random_word(self, length):
            # randomly generate dir name to prevent multiple concurrent config downloads conflicting
            return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(length))

        def get_template_placeholder(self, key, o="{{ ", c=" }}"):
            return str(o) + str(key) + str(c)

        def replace_placeholder(self, data, key, value):
            new_data = data
            new_data = new_data.replace(self.get_template_placeholder(key), str(value))
            new_data = new_data.replace(self.get_template_placeholder(key, o="{{", c="}}"), str(value))
            return new_data

        def generate_config(self, f, placeholders=None):
            """
            template config files have placeholders in the format:
                setting_1: {{ PLACEHOLDER_1 }}
            this function loops through config file, f, and replaces
            placeholders with 'placeholders' dict, in the format:
                {
                    "PLACEHOLDER_1": "new placeholder value 1",
                    "PLACEHOLDER_2": "new placeholder value 2"
                }
            """
            # prepare config contents for Windows newline
            with open(f, "r", newline='\r\n') as infile:
                template = infile.read()

            if placeholders is not None:
                for key, value in placeholders.items():
                    template = self.replace_placeholder(template, key, value)

            return template

        def mk_temp_dir(self, dirname_length=8):
            self.temp_dirname = self.random_word(dirname_length)
            self.temp_dir_abs = TEMP_STORAGE + os.sep + self.temp_dirname
            app.logger.info('making temporary config storage directory ' + str(self.temp_dir_abs))
            os.makedirs(self.temp_dir_abs)

        def rm_temp_dir(self):
            app.logger.info('removing temporary config storage directory ' + str(self.temp_dir_abs))
            shutil.rmtree(self.temp_dir_abs)

        def write_config_to_temp(self, filename, config):
            f = os.path.join(self.temp_dir_abs, filename)
            with open(f, 'w', newline='\r\n') as outfile:
                app.logger.info('writing config to temporary storage ' + str(f))
                outfile.write(config)

        def get_config_filename(self, template_file):
            return os.path.basename(template_file)

        def make_config_from_template(self, template_file, config_dict):
            config = self.generate_config(template_file, placeholders=config_dict)
            filename = self.get_config_filename(template_file)
            self.write_config_to_temp(filename, config)

        def make_config_zip2(self, template_files, config_dict):
            """
            USING TEMP STORAGE
            write config files from templates to randomly named dir in storage:
                /tmp/vzw2p222/config_filename1.ini
                /tmp/vzw2p222/config_filename2.ini
            package into zip file in memory and return as memory stream
            """
            self.mk_temp_dir()
            for template_file in template_files:
                self.make_config_from_template(template_file, config_dict)
            memory_file = BytesIO()
            with zipfile.ZipFile(memory_file, 'w') as zf:
                config_files = [os.path.join(self.temp_dir_abs, f) for f in os.listdir(self.temp_dir_abs)]
                for f in config_files:
                    app.logger.info(f)
                    data = zipfile.ZipInfo(os.path.basename(f))
                    data.compress_type = zipfile.ZIP_DEFLATED
                    with open(f, "r", newline='\r\n') as file:
                        file_content = file.read()
                    zf.writestr(data, file_content)
            self.rm_temp_dir
            memory_file.seek(0)
            return memory_file

        def make_config_zip(self, template_files, config_dict):
            """
            NO STORAGE REQUIRED
            write config files to memory
            package files into zip file in memory and return as memory stream
            """
            memory_file = BytesIO()
            with zipfile.ZipFile(memory_file, 'w') as zf:
                for f in config_files:
                    app.logger.info(f)
                    data = zipfile.ZipInfo(os.path.basename(f))
                    data.compress_type = zipfile.ZIP_DEFLATED
                    config = self.generate_config(f, placeholders=config_dict)
                    zf.writestr(data, config)
            # self.rm_temp_dir
            memory_file.seek(0)
            return memory_file

    try:
        uploader = SiteDataUploader.query.filter_by(site_id=site_id).one()
    except:
        uploader = SiteDataUploader()

    config_settings = {
        "AWS_S3_SITEDATA_BUCKET": app.config["AWS_S3_SITEDATA_BUCKET"],
        "AWS_S3_SITEDATA_PATH": app.config["AWS_S3_SITEDATA_PATH"],
        "AWS_S3_REGION": app.config["AWS_S3_REGION"],
        "AWS_ACCESS_KEY_ID": uploader.aws_access_key_id,
        "AWS_SECRET_ACCESS_KEY": uploader.aws_secret_access_key,
        "SMTP_SENDER": '@'.join((uploader.aws_username, app.config["MAIL_DEFAULT_SENDER"].split('@')[1])),
        "SMTP_RECIPIENTS": app.config["ADMIN_EMAIL"],
        "SMTP_HOST": app.config["MAIL_SERVER"],
        "SMTP_PORT": app.config["MAIL_PORT"],
        "SMTP_USERNAME": "",
        "SMTP_PASSWORD": "",
        "SITE_ID": site_id
    }

    # generate config as zip file in memory
    config_files = [
        CHIMERA_TEMPLATE,
        DATA_AGENT_TEMPLATE
    ]
    config_generator = ConfigGenerator()
    out = config_generator.make_config_zip(config_files, config_settings)

    # send the file to client
    response = make_response(send_file(out, attachment_filename='config.zip', as_attachment=True))
    # prevent browser from caching the download
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'

    return response
