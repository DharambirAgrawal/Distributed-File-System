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
    
    # Create storage directories safely
    def create_dir_safely(path, name):
        """Create directory safely with error handling"""
        try:
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
                print(f"✅ Created {name} directory: {path}")
        except PermissionError:
            print(f"⚠️  Permission denied creating {name} directory: {path}")
            # Try to use a fallback path in current directory
            fallback_path = f"./{os.path.basename(path)}"
            try:
                os.makedirs(fallback_path, exist_ok=True)
                print(f"✅ Using fallback {name} directory: {fallback_path}")
                return fallback_path
            except Exception as e:
                print(f"❌ Failed to create fallback directory: {e}")
                return path
        except Exception as e:
            print(f"❌ Error creating {name} directory {path}: {e}")
        return path
    
    storage_path = create_dir_safely(app.config['STORAGE_PATH'], 'storage')
    app.config['STORAGE_PATH'] = storage_path
    
    upload_path = create_dir_safely(app.config['UPLOAD_FOLDER'], 'upload')
    app.config['UPLOAD_FOLDER'] = upload_path
    
    backup_path = create_dir_safely(app.config.get('BACKUP_PATH', './backup_cloud'), 'backup')
    app.config['BACKUP_PATH'] = backup_path
    
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
