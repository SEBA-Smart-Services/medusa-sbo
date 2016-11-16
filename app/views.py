from app import admin, db
from flask_admin.contrib.sqla import ModelView
from app.models import Asset, Site, AssetComponent, AssetType, Algorithm, AssetHealth, AssetSubtype, ComponentType, InbuildingsAsset, Result, SubtypeComponent

class AssetComponentView(ModelView):
    column_filters = (Asset.name, ComponentType.name)
    column_searchable_list = ('name', Asset.name)

admin.add_view(ModelView(Site, db.session))
admin.add_view(ModelView(AssetType, db.session))
admin.add_view(ModelView(AssetSubtype, db.session))
admin.add_view(ModelView(SubtypeComponent, db.session))
admin.add_view(ModelView(Asset, db.session))
admin.add_view(AssetComponentView(AssetComponent, db.session))
admin.add_view(ModelView(ComponentType, db.session))
admin.add_view(ModelView(Algorithm, db.session))
admin.add_view(ModelView(Result, db.session))
admin.add_view(ModelView(AssetHealth, db.session))
admin.add_view(ModelView(InbuildingsAsset, db.session))

