import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    # Database - Render provides this as DATABASE_URL
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    # Fix for Render's postgres:// vs postgresql://
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # Celery Configuration - support both REDIS_URL and CELERY_BROKER_URL
    redis_url = os.getenv('REDIS_URL') or os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_BROKER_URL = redis_url
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', redis_url)
    
    # Apify Configuration
    APIFY_API_TOKEN = os.getenv('APIFY_API_TOKEN')
    APIFY_ACTOR_ID = os.getenv('APIFY_ACTOR_ID', 'apimaestro/linkedin-company-posts')
    APIFY_PROFILE_ACTOR_ID = os.getenv('APIFY_PROFILE_ACTOR_ID', 'apify/unlimited-leads-linkedin')  # For profile scraping
