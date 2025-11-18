"""
Celery worker entry point
Run with: celery -A celery_worker.celery worker --loglevel=info
"""
from app import create_app
from app.extensions import celery

# Create app to initialize Celery
app = create_app()

# Import tasks so Celery can discover them
from app.tasks import ai_analyzer  # noqa: F401

# Make celery available at module level for celery command
celery_app = celery

