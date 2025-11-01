from flask import Flask, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from app.config import Config
from app.extensions import db, jwt

# Flask-Migrate - Database migration management
migrate = Migrate()

def create_app(config_class=Config):
    """
    Application Factory Pattern
    
    Creates and configures the Flask application.
    Using factory pattern allows:
    - Multiple app instances (testing vs production)
    - Easier testing (create app with test config)
    - Cleaner code structure
    
    Args:
        config_class: Configuration class (default: Config from .env)
    
    Returns:
        Flask app instance
    
    Example:
        app = create_app()
        app.run()
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    
    # Import models
    from app.models import Tenant, User, Company, Post, Profile, Email, TenantSetting

    # Health check endpoint - Used by AWS load balancer to check if app is running

    @app.route('/api/health', methods=['GET'])
    def health():

        """
        Health Check Endpoint
        
        Returns 200 if app is running.
        AWS load balancer calls this every 30 seconds.
        
        Returns:
            JSON: {"status": "ok"}
        """
        
        return jsonify({"status": "ok"}), 200
    
    return app