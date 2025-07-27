# app/__init__.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_mail import Mail
from celery import Celery

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
login_manager = LoginManager()
mail = Mail()
celery = Celery()

def create_app(config_class=None):
    app = Flask(__name__)
    
    # Load configuration
    if config_class is None:
        app.config.from_object('config.Config')
    else:
        app.config.from_object(config_class)
    
    # Configure CORS - must be before initializing other extensions
    from flask_cors import CORS
    CORS(app, 
         origins="http://localhost:5173",      # Your frontend origin
         supports_credentials=True,            # Essential for cookies
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         resources={r"/api/*": {"origins": "http://localhost:5173"}})
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # Set up login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    # Configure Celery
    celery.conf.update(app.config)
    
    # Register blueprints with debugging
    print("\n=== Registering Blueprints ===")
    
    # Auth Blueprint
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp)  # No url_prefix here since it's in the blueprint
    print(f"Registered 'auth' blueprint with URL prefix: {auth_bp.url_prefix}")
    
    # Main Blueprint
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)  # No url_prefix here
    print(f"Registered 'main' blueprint with URL prefix: {main_bp.url_prefix}")
    
    # Jobs Blueprint
    from app.jobs import bp as jobs_bp
    app.register_blueprint(jobs_bp)  # No url_prefix here
    print(f"Registered 'jobs' blueprint with URL prefix: {jobs_bp.url_prefix}")
    print("=== Blueprint Registration Complete ===\n")
    
    # Set up user loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.query.get(int(user_id))
    
    # Create upload directory if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Add a test route directly to the app
    @app.route('/test-route')
    def test_route():
        return 'Test route works!'
    
    # Debug information
    print("=== App Debug Info ===")
    print(f"Registered blueprints: {list(app.blueprints.keys())}")
    print(f"URL Map: {app.url_map}")
    print("=====================")
    
    return app