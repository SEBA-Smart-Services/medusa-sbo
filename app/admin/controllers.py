from app import app, db
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from app.models import Asset, Site, AssetComponent, AssetType, Algorithm, AssetSubtype, ComponentType, InbuildingsAsset, Result, SubtypeComponent, LoggedEntity, LogTimeValue, Status

# configuration of views for Admin page
# some columns (eg results) are excluded, since it tries to load and display >10,000 entries and crashes the page
# default sort column is needed on views that have enough entries to use pagination

admin = Admin(app)

class AssetSubtypeView(ModelView):
	form_excluded_columns = ['algorithms']

class SubtypeComponentView(ModelView):
	column_default_sort = 'subtype_id'

class AssetView(ModelView):
	form_excluded_columns = ['results']

class AssetComponentView(ModelView):
    column_filters = (Asset.name, ComponentType.name)
    column_searchable_list = ('name', Asset.name)
    column_default_sort = ('asset_id')
    form_excluded_columns = ['results']

class ComponentTypeView(ModelView):
	form_excluded_columns = ['algorithms']

class AlgorithmView(ModelView):
	form_excluded_columns = ['results']

class InbuildingsAssetView(ModelView):
	column_default_sort = 'id'

class ResultView(ModelView):
	column_default_sort = ('id', True)

class StatusView(ModelView):
	form_excluded_columns = ['results']

class SiteView(ModelView):
    form_excluded_columns = ['issue_history']

class AssetTypeView(ModelView):
    pass

admin.add_view(SiteView(Site, db.session))
admin.add_view(AssetTypeView(AssetType, db.session))
admin.add_view(AssetSubtypeView(AssetSubtype, db.session))
admin.add_view(SubtypeComponentView(SubtypeComponent, db.session))
admin.add_view(AssetView(Asset, db.session))
admin.add_view(AssetComponentView(AssetComponent, db.session))
admin.add_view(ComponentTypeView(ComponentType, db.session))
admin.add_view(AlgorithmView(Algorithm, db.session))
admin.add_view(ResultView(Result, db.session))
admin.add_view(InbuildingsAssetView(InbuildingsAsset, db.session))
admin.add_view(StatusView(Status, db.session))