from app.extensions import db
from datetime import datetime
import uuid

class Email(db.Model):
    __tablename__ = 'emails'
    
    email_id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.tenant_id', ondelete='CASCADE'), nullable=False)
    post_id = db.Column(db.String(36), db.ForeignKey('posts.post_id', ondelete='CASCADE'), nullable=False)
    profile_id = db.Column(db.String(36), db.ForeignKey('profiles.profile_id'))
    subject = db.Column(db.String(500), nullable=False)
    body = db.Column(db.Text, nullable=False)
    recipients = db.Column(db.Text)
    status = db.Column(db.String(50), default='draft')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)