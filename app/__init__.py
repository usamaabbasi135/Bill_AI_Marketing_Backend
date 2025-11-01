from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from app.config import Config
from app.extensions import db, jwt

migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    
    # Import models
    from app.models import Tenant, User, Company, Post, Profile, Email, TenantSetting
    
    # Register blueprints
    from app.api import auth  # ← Add this
    app.register_blueprint(auth.bp, url_prefix='/api/auth')  # ← Add this
    
    @app.route('/api/health', methods=['GET'])
    def health():
        return jsonify({"status": "ok"}), 200
    
    return app