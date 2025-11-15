import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    # Database - Render provides this as DATABASE_URL
    # Default to local development database if not set
    DATABASE_URL = os.getenv('DATABASE_URL') or 'postgresql://dev:dev123@localhost:5432/billy_ai'
    
    # Fix for Render's postgres:// vs postgresql://
    if DATABASE_URL.startswith('postgres://'):
        DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Security keys - use defaults for local development, override in production
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production-12345')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret-key-change-in-production-12345')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)