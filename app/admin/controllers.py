from app import app, db
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from app.models import Asset, Site, AssetPoint, AssetType, Algorithm, FunctionalDescriptor, PointType, InbuildingsAsset, Result, EmailTemplate, Email

# configuration of views for Admin page
# some columns (eg results) are excluded, since it tries to load and display >10,000 entries and crashes the page
# default sort column is needed on views that have enough entries to use pagination

admin = Admin(app)

class FunctionalDescriptorView(ModelView):
    pass

class AssetView(ModelView):
	form_excluded_columns = ['results']

class AssetPointView(ModelView):
    column_filters = (Asset.name, PointType.name)
    column_searchable_list = ('name', Asset.name)
    column_default_sort = ('asset_id')
    form_excluded_columns = ['results']

class PointTypeView(ModelView):
    form_excluded_columns = ['algorithms']

class AlgorithmView(ModelView):
    form_excluded_columns = ['results']
    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = True
    column_details_list = ['name', 'descr', 'point_types', 'functions']

class InbuildingsAssetView(ModelView):
    column_default_sort = 'id'

class ResultView(ModelView):
    column_default_sort = ('id', True)

class SiteView(ModelView):
    form_excluded_columns = ['issue_history']

class AssetTypeView(ModelView):
    pass

class EmailTemplateView(ModelView):
    pass

class EmailView(ModelView):
    pass

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
