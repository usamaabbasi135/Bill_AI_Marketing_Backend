"""
Celery entry point for running worker commands.

Usage:
    celery -A celery_worker worker --loglevel=info --pool=solo
    celery -A celery_worker beat --loglevel=info
"""
# Import directly from module to avoid circular imports
import sys
import os

# Add project root to path if needed
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import directly from celery_app module (bypass __init__.py)
from app.tasks.celery_app import celery_app

# IMPORTANT: Import tasks so they're registered with Celery
# This ensures the @celery_app.task decorators are executed
from app.tasks import scraper  # noqa: F401
from app.tasks import ai_analyzer  # noqa: F401
from app.tasks import email_sender_tasks  # noqa: F401
from app.tasks import email_tasks  # noqa: F401

# This makes the celery_app available for command line
if __name__ == '__main__':
    celery_app.start()
