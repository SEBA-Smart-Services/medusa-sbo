from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Optional, InputRequired

# form for site config page
class AddITAssetForm(FlaskForm):
    site = StringField('Site', validators=[DataRequired()])
    device_type = StringField('Device Type', validators=[DataRequired()])
    device_number = StringField('Device Number', validators=[Optional()] )
    
