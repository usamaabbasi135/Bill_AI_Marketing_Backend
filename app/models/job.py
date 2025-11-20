from datetime import datetime

from app.extensions import db


class Job(db.Model):
    __tablename__ = 'jobs'

    job_id = db.Column(db.String(255), primary_key=True)
    tenant_id = db.Column(
        db.String(36),
        db.ForeignKey('tenants.tenant_id', ondelete='CASCADE'),
        nullable=False
    )
    task_name = db.Column(db.String(255))
    status = db.Column(db.String(50), default='pending', nullable=False)
    result = db.Column(db.JSON)
    error = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = db.relationship('Tenant', backref=db.backref('jobs', lazy=True))

