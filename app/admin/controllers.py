from app import app, db
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from app.models import Asset, Site, AssetComponent, AssetType, Algorithm, AssetSubtype, ComponentType, InbuildingsAsset, Result, SubtypeComponent, LoggedEntity, LogTimeValue

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
    form_excluded_columns = ['results']

class ComponentTypeView(ModelView):
	form_excluded_columns = ['algorithms']

class AlgorithmView(ModelView):
	form_excluded_columns = ['results']

class InbuildingsAssetView(ModelView):
	column_default_sort = 'id'

class ResultView(ModelView):
	column_default_sort = ('id', True)

admin.add_view(ModelView(Site, db.session))
admin.add_view(ModelView(AssetType, db.session))
admin.add_view(AssetSubtypeView(AssetSubtype, db.session))
admin.add_view(SubtypeComponentView(SubtypeComponent, db.session))
admin.add_view(AssetView(Asset, db.session))
admin.add_view(AssetComponentView(AssetComponent, db.session))
admin.add_view(ComponentTypeView(ComponentType, db.session))
admin.add_view(AlgorithmView(Algorithm, db.session))
admin.add_view(ResultView(Result, db.session))
admin.add_view(InbuildingsAssetView(InbuildingsAsset, db.session))