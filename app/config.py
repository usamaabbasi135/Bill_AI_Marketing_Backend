import os
from dotenv import load_dotenv

load_dotenv()

class Config:
     """
    Application Configuration
    
    All sensitive data (API keys, database URLs) comes from environment variables.
    This allows different configs for development vs production without code changes.
    
    Development: Uses .env file
    Production: AWS ECS sets environment variables
    """
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')