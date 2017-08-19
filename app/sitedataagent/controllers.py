from flask import request, render_template, url_for, redirect, jsonify
from app import app
from app.models import Site
from app.sitedataagent.forms import SiteAgentConfigForm
from app.sitedataagent.aws_utils import AwsIamManager

# site config page
@app.route('/site/<sitename>/config/sitedataagent', methods=['GET','POST'])
def site_data_agent(sitename):

    site = Site.query.filter_by(name=sitename).one()

    form = SiteAgentConfigForm()

    if request.method == 'POST':

        if form.validate_on_submit():
            return redirect(url_for('site_data_agent', sitename=sitename, form=form))

        #
        # # if form has errors, return the page (errors will display)
        # if not form.validate_on_submit():
        #     return render_template('site_config.html', inbuildings_config=inbuildings_config, site=site, form=form)
        #
        # # convert port input to a string
        # if form.db_port.data is None:
        #     form.db_port.data = ""
        # form.db_port.data = str(form.db_port.data)
        #
        # # update webreports database settings
        # form.populate_obj(site)
        # site.generate_key()
        #
        # # update inbuildings settings
        # #################################
        # # There appears to be some orphan sites without InbuildingsConfig relationships
        # # not sure how/when??
        # # this page breaks for these sites'
        # # this if statement prevents this
        # if inbuildings_config is not None:
        #     inbuildings_config.enabled = form.inbuildings_enabled.data
        #     inbuildings_config.key = form.inbuildings_key.data
        #
        # # update emails
        # emails = []
        # # remove whitespace and separate out emails from csv
        # email_strings = set(form.email_list.data.replace(" ", "").split(','))
        # for email_string in email_strings:
        #     if email_string != '':
        #         emails.append(Email(address=email_string))
        # site.emails = emails
        #
        # db.session.commit()
        return 'little success ' + site.name# redirect(url_for('site_data_agent', sitename=sitename))

    elif request.method == 'GET':
        # # prefill form with information from site object
        # form = SiteConfigForm(obj=site)
        #
        # #################################
        # # There appears to be some orphan sites without InbuildingsConfig relationships
        # # not sure how/when??
        # # this page breaks for these sites'
        # # this if statement prevents this
        # if inbuildings_config is None:
        #     form.inbuildings_enabled.data = False # inbuildings_config.enabled
        #     form.inbuildings_key.data = ''# inbuildings_config.key
        # else:
        #     form.inbuildings_enabled.data = inbuildings_config.enabled
        #     form.inbuildings_key.data = inbuildings_config.key
        # # turn emails into csv
        # form.email_list.data = ','.join([email.address for email in site.emails])
        return render_template('site_settings/site_data_agent.html', site=site, form=form)


@app.route('/_generate_aws_access_keys/<int:site_id>')
def add_numbers(site_id):
    print(site_id)
    iam = AwsIamManager(site_id)
    resp = iam.delete_access_key()
    delete_resp = iam.delete_user()
    create_resp = iam.create_user()
    resp = iam.create_access_key()
    resp = iam.delete_access_key()
    delete_resp = iam.delete_user()
    return jsonify(
        accessKeyId=iam.access_key_id,
        secretAccessKey=iam.secret_access_key
    )
