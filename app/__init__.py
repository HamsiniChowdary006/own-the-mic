from flask import Flask
from flask_cors import CORS
from config import get_config, Config
from app.extensions import db, migrate, jwt, talisman
from app.utils.logging import init_logging

def create_app(config_class=None):
    if config_class is None:
        config_class = get_config()
        
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 1. Validate environment configuration
    config_class.validate()
    
    # 2. Setup standard logging
    init_logging(app)
    
    # 3. Enable CORS
    CORS(app)
    
    # 4. Content Security Policy for Google Authentication and CSS resources
    csp = {
        'default-src': [
            '\'self\'',
            'https://fonts.googleapis.com',
            'https://fonts.gstatic.com',
            'https://accounts.google.com'
        ],
        'script-src': [
            '\'self\'',
            '\'unsafe-inline\'',
            '\'unsafe-eval\'',
            'https://accounts.google.com/gsi/client',
            'https://apis.google.com'
        ],
        'style-src': [
            '\'self\'',
            '\'unsafe-inline\'',
            'https://fonts.googleapis.com',
            'https://accounts.google.com'
        ],
        'frame-src': [
            '\'self\'',
            'https://accounts.google.com'
        ],
        'connect-src': [
            '\'self\'',
            'https://accounts.google.com',
            'https://*.supabase.co'
        ],
        'img-src': [
            '\'self\'',
            'data:',
            'https://lh3.googleusercontent.com',
            'https://*.googleusercontent.com'
        ]
    }
    
    # Only force HTTPS in production config
    is_prod = getattr(config_class, 'ENV', 'development') == 'production'
    talisman.init_app(app, content_security_policy=csp, force_https=is_prod)
    
    # 5. Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    # 6. Register Blueprints
    from app.routes.main import main_bp
    app.register_blueprint(main_bp)
    
    from app.routes.api import api_bp
    app.register_blueprint(api_bp)
    
    from app.auth.routes import auth_bp
    app.register_blueprint(auth_bp)
    
    app.logger.info("Flask Application initialized successfully in %s mode.", getattr(config_class, 'ENV', 'development'))
    
    return app
