from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_name=None):
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.environ.get('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))
    
    # Create storage directories
    storage_path = app.config['STORAGE_PATH']
    if not os.path.exists(storage_path):
        os.makedirs(storage_path)
    
    upload_path = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)
    
    # Create backup directory
    backup_path = app.config.get('BACKUP_PATH', 'backup_cloud')
    if not os.path.exists(backup_path):
        os.makedirs(backup_path)
    
    # Register blueprints
    from app.routes import main, api
    from app.auth import auth
    app.register_blueprint(main)
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(auth, url_prefix='/auth')
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
