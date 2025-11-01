from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

"""
Flask Extensions - Initialized here, configured in app/__init__.py

Why separate file?
- Avoids circular imports
- Extensions need to be created before app, but configured after
- Makes testing easier (can mock extensions)
"""
# Database ORM - Converts Python classes to SQL tables
# Usage: from app.extensions import db


db = SQLAlchemy()

# JWT Authentication - Handles login tokens
# Usage: from app.extensions import jwt

jwt = JWTManager()