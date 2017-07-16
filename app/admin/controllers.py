from app import app, db
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_user import current_user
from app.models import Asset, Site, AssetPoint, AssetType, Algorithm, FunctionalDescriptor, FunctionalDescriptorCategory, PointType, InbuildingsAsset, Result, EmailTemplate, Email, User, Role, Alarm, LoggedEntity, LogTimeValue
from app.weather.models import Weather
from app.models.ITP import Deliverable_type, Location, Check_generic

# configuration of views for Admin page
# some columns (eg results) are excluded, since it tries to load and display >10,000 entries and crashes the page
# default sort column is needed on views that have enough entries to use pagination

admin = Admin(app)

# view that requires the current user to be authenticated as admin
# all views should be subclasses of this
class ProtectedView(ModelView):
    def is_accessible(self):
        return current_user.has_role('admin')

class FunctionalDescriptorView(ProtectedView):
    pass

class AssetView(ProtectedView):
	form_excluded_columns = ['results']

class AssetPointView(ProtectedView):
    column_filters = (Asset.name, PointType.name)
    column_searchable_list = ('name', Asset.name)
    column_default_sort = ('asset_id')
    form_excluded_columns = ['results']

class PointTypeView(ProtectedView):
    form_excluded_columns = ['algorithms']

# lock the algorithm models from being edited - these are automatically generated from the code
class AlgorithmView(ProtectedView):
    form_excluded_columns = ['results']
    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = True
    column_details_list = ['name', 'descr', 'point_types', 'functions']

class InbuildingsAssetView(ProtectedView):
    column_default_sort = 'id'

class ResultView(ProtectedView):
    column_default_sort = ('id', True)

class SiteView(ProtectedView):
    form_excluded_columns = ['issue_history']

class AssetTypeView(ProtectedView):
    pass

class EmailTemplateView(ProtectedView):
    pass

class EmailView(ProtectedView):
    pass

class UserView(ProtectedView):
    pass

class RoleView(ProtectedView):
    pass

class AlarmView(ProtectedView):
     column_display_pk = True

class LoggedEntityView(ProtectedView):
     column_display_pk = True

class LogTimeValueView(ProtectedView):
     column_display_pk = True

class DeliverableTypeView(ProtectedView):
    column_display_pk = True

class LocationView(ProtectedView):
    column_display_pk = True

class CheckGenericView(ProtectedView):
    column_display_pk = True

# attach the model views to the admin page
admin.add_view(SiteView(Site, db.session))
admin.add_view(AssetTypeView(AssetType, db.session))
admin.add_view(FunctionalDescriptorView(FunctionalDescriptor, db.session))
admin.add_view(AssetView(Asset, db.session))
admin.add_view(AssetPointView(AssetPoint, db.session))
admin.add_view(PointTypeView(PointType, db.session))
admin.add_view(AlgorithmView(Algorithm, db.session))
admin.add_view(ResultView(Result, db.session))
admin.add_view(InbuildingsAssetView(InbuildingsAsset, db.session))
admin.add_view(EmailTemplateView(EmailTemplate, db.session))
admin.add_view(EmailView(Email, db.session))
admin.add_view(UserView(User, db.session))
admin.add_view(RoleView(Role, db.session))
admin.add_view(ProtectedView(Weather, db.session))
admin.add_view(ProtectedView(FunctionalDescriptorCategory, db.session))
admin.add_view(AlarmView(Alarm, db.session))
admin.add_view(LoggedEntityView(LoggedEntity, db.session))
admin.add_view(LogTimeValueView(LogTimeValue, db.session))
admin.add_view(DeliverableTypeView(Deliverable_type, db.session))
admin.add_view(LocationView(Location, db.session))
admin.add_view(CheckGenericView(Check_generic, db.session))
