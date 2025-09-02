from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config
import os

db = SQLAlchemy()

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.environ.get('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    # Create storage directory
    storage_path = app.config['STORAGE_PATH']
    if not os.path.exists(storage_path):
        os.makedirs(storage_path)
    
    upload_path = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
    
    # Register blueprints
    from app.routes import main, api
    app.register_blueprint(main)
    app.register_blueprint(api, url_prefix='/api')
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
