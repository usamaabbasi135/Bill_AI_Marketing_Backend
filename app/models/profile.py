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
    status = db.Column(db.String(50), nullable=False, default='url_only')
    email = db.Column(db.String(255))
    phone = db.Column(db.String(50))
    company = db.Column(db.String(255))
    job_title = db.Column(db.String(255))
    location = db.Column(db.String(255))
    industry = db.Column(db.String(255))
    scraped_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)