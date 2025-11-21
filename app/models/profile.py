from app.extensions import db
from datetime import datetime
import uuid

class Profile(db.Model):
    __tablename__ = 'profiles'
    
    profile_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.tenant_id', ondelete='CASCADE'), nullable=False)
    person_name = db.Column(db.String(255))
    headline = db.Column(db.Text)
    linkedin_url = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)