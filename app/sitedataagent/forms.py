from flask_wtf import FlaskForm
from wtforms import BooleanField

# form for site config page
class SiteAgentConfigForm(FlaskForm):
    enabled = BooleanField('enabled', validators=[])
