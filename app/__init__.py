import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from app.config import Config
from app.extensions import db, jwt, celery

migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    
    # Initialize Celery (using environment variables directly, not from config)
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    celery.conf.update(
        broker_url=redis_url,
        result_backend=redis_url,
        accept_content=['json'],
        task_serializer='json',
        result_serializer='json',
        timezone='UTC',
    )
    
    # Make Celery aware of Flask app context
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    
    # Health check endpoint - register early so it's always available
    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({"status": "ok"}), 200
    
    # Import models
    from app.models import (
        Tenant,
        User,
        Company,
        Post,
        Profile,
        Email,
        TenantSetting,
        EmailTemplate,
        Campaign,
        CampaignProfile,
    )
    
    # Register blueprints
    from app.api import auth
    app.register_blueprint(auth.bp, url_prefix='/api/auth')
    from app.api import companies
    app.register_blueprint(companies.bp, url_prefix='/api/companies')
    from app.api import posts
    app.register_blueprint(posts.bp, url_prefix='/api/posts')

    # JWT error handlers for clearer responses
    @jwt.unauthorized_loader
    def jwt_missing_token(err):
        return jsonify({"error": "Unauthorized", "details": err}), 401

    @jwt.invalid_token_loader
    def jwt_invalid_token(err):
        return jsonify({"error": "Invalid token", "details": err}), 401

    @jwt.expired_token_loader
    def jwt_expired_token(header, payload):
        return jsonify({"error": "Token expired"}), 401
    
    return app