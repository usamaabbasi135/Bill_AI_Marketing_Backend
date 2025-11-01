from app.extensions import db
from datetime import datetime
import uuid

class Tenant(db.Model):
    __tablename__ = 'tenants'
    
    tenant_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_name = db.Column(db.String(255), nullable=False)
    plan = db.Column(db.String(50), default='free')
    status = db.Column(db.String(50), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    users = db.relationship('User', backref='tenant', cascade='all, delete-orphan')
    companies = db.relationship('Company', backref='tenant', cascade='all, delete-orphan')