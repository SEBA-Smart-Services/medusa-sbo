from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Optional, InputRequired

# form for site config page
class SiteConfigForm(FlaskForm):
    db_username = StringField('Username', validators=[])
    db_password = StringField('Password', validators=[])
    db_address = StringField('Address', validators=[])
    db_port = IntegerField('Port', validators=[Optional()])
    db_name = StringField('Database Name', validators=[])
    email_trigger_priority = IntegerField('Send email notification at priority', validators=[])
    cmms_trigger_priority = IntegerField('Send work request at priority', validators=[])
    inbuildings_enabled = BooleanField('Enabled', validators=[])
    inbuildings_key = StringField('Key', validators=[])
    email_list = TextAreaField('Emails', validators=[])

# form for page to add a new site
class AddSiteForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    db_username = StringField('Username', validators=[])
    db_password = StringField('Password', validators=[])
    db_address = StringField('Address', validators=[])
    db_port = IntegerField('Port', validators=[Optional()])
    db_name = StringField('Database Name', validators=[])

# form for adding a new asset
class AddAssetForm(FlaskForm):
    type = StringField('Type', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    location = StringField('Location', validators=[])
    group = StringField('Group', validators=[])
    priority = IntegerField('Priority', validators=[])
    notes = TextAreaField('Notes', validators=[])

# form for editing an existing asset
# same as above, except the type cannot be changed
class EditAssetForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    location = StringField('Location', validators=[])
    group = StringField('Group', validators=[])
    priority = IntegerField('Priority', validators=[])
    notes = TextAreaField('Notes', validators=[])
