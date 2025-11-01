from app.extensions import db
from datetime import datetime
import uuid

class Company(db.Model):
    __tablename__ = 'companies'
    
    company_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.tenant_id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    linkedin_url = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    posts = db.relationship('Post', backref='company', cascade='all, delete-orphan')