from celery import Celery
from dotenv import load_dotenv
import os
import sys
from pathlib import Path

# Load environment variables - use absolute path to .env file
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Also try loading from current directory
load_dotenv()

# Get Redis URL - prioritize environment variable
redis_url = os.getenv('REDIS_URL') or os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

# Ensure it's a Redis URL (not AMQP)
if not redis_url or not redis_url.startswith('redis://'):
    redis_url = 'redis://localhost:6379/0'

print(f"[CELERY CONFIG] Using broker: {redis_url}")  # Debug output
print(f"[CELERY CONFIG] REDIS_URL from env: {os.getenv('REDIS_URL')}")  # Debug

# Detect Windows and set appropriate pool
is_windows = sys.platform.startswith('win')
pool_type = 'solo' if is_windows else 'prefork'
print(f"[CELERY CONFIG] Using pool: {pool_type} (Windows: {is_windows})")  # Debug output

# Create Celery instance with Redis - SET BROKER IN CONSTRUCTOR
celery_app = Celery(
    'billy_ai',
    broker=redis_url,  # Set broker directly in constructor
    backend=redis_url  # Set backend directly in constructor
)

# Update configuration - ensure Redis transport
celery_app.conf.update(
    broker_url=redis_url,  # Explicitly set again
    result_backend=redis_url,  # Explicitly set again
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    broker_connection_retry_on_startup=True,
    worker_pool=pool_type,
    broker_transport='redis',  # Force Redis transport
    broker_transport_options={
        'visibility_timeout': 3600,
        'retry_policy': {
            'timeout': 5.0
        }
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks(['app.tasks'])

# Explicitly import tasks to ensure they're registered
# This is important because autodiscover might not work if __init__.py is empty
try:
    from app.tasks.scraper import scrape_company_posts, scrape_profiles  # noqa: F401
    print("[CELERY CONFIG] Task 'scrape_company_posts' imported and registered")
    print("[CELERY CONFIG] Task 'scrape_profiles' imported and registered")
except ImportError as e:
    print(f"[CELERY CONFIG] WARNING: Could not import scraper task: {e}")

# Final verification
print(f"[CELERY CONFIG] Final broker_url: {celery_app.conf.broker_url}")
print(f"[CELERY CONFIG] Final result_backend: {celery_app.conf.result_backend}")
print(f"[CELERY CONFIG] Registered tasks: {list(celery_app.tasks.keys())}")

