"""
Celery tasks package.

Import directly from modules when needed:
  from app.tasks.ai_analyzer import analyze_post
  from app.tasks.scraper import scrape_company_posts
"""

__all__ = []

# Try to import tasks that may exist
try:
    from app.tasks.ai_analyzer import analyze_post
    __all__.append('analyze_post')
except ImportError:
    pass

try:
    from app.tasks.scraper import scrape_company_posts
    __all__.append('scrape_company_posts')
except ImportError:
    pass

try:
    from app.tasks.email_tasks import generate_campaign_emails_task
    __all__.append('generate_campaign_emails_task')
except ImportError:
    pass

