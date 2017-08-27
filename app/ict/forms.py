from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Optional, InputRequired

# form for adding IT asset
class AddITAssetForm(FlaskForm):
    site = StringField('Site', validators=[DataRequired()])
    device_type = StringField('Device Type', validators=[DataRequired()])
    device_number = StringField('Device Number', validators=[Optional()] )

# form for editing IT asset
class EditITAssetForm(FlaskForm):
    minion_name = StringField('IT Asset Name', validators=[DataRequired()])
    platform = StringField('Platform', validators=[Optional()])
    ip_address = StringField('IP Address', validators=[Optional()])
    operating_system = StringField('Operating System', validators=[Optional()])
