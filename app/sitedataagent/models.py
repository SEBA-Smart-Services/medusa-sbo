from app import db
from app.models import Base


class SiteDataUploader(Base):
    __tablename__ = 'site_data_uploader'

    enabled = db.Column(db.Boolean)
    aws_username = db.Column(db.String(100), nullable=False, unique=True)
    aws_access_key_id = db.Column(db.String(100))
    aws_secret_access_key = db.Column(db.String(100))
    site_id = db.Column(db.Integer, db.ForeignKey('site.ID'))
    site = db.relationship("Site", back_populates="site_data_uploader")

    def __init__(self):
        pass

    def __repr__(self):
        return '<SiteDataUploader %r>' % self.aws_username
