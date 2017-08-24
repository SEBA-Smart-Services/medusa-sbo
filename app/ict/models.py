from app import db
from app.models import Base


class ITasset(Base):
    __tablename__ = 'it_asset'
    id = db.Column(db.Integer(), primary_key=True)
    minion_name = db.Column(db.String(100), unique=True)
    ip_address = db.Column(db.String(100))
    operating_system = db.Column(db.String(100))
    platform = db.Column(db.String(100))
    site_id = db.Column(db.Integer, db.ForeignKey('site.ID'))

    def __init__(self):
        pass
