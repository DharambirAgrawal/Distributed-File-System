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
    
    # Create storage directories safely with proper error handling
    def create_dir_safely(path, name):
        """Create directory safely with error handling and fallbacks"""
        # Make path absolute and resolve any issues
        try:
            # Convert relative paths
            if path.startswith('./'):
                path = os.path.join(os.getcwd(), path[2:])
            elif not os.path.isabs(path):
                path = os.path.join(os.getcwd(), path)
            
            # Create directory
            os.makedirs(path, mode=0o755, exist_ok=True)
            print(f"✅ Created {name} directory: {path}")
            return path
            
        except PermissionError as e:
            print(f"⚠️  Permission denied creating {name} directory: {path}")
            # Use current directory as fallback
            fallback_path = os.path.join(os.getcwd(), os.path.basename(path))
            try:
                os.makedirs(fallback_path, mode=0o755, exist_ok=True)
                print(f"✅ Using fallback {name} directory: {fallback_path}")
                return fallback_path
            except Exception as e2:
                print(f"❌ Fallback also failed: {e2}")
                # Final fallback - use temp directory structure
                import tempfile
                temp_base = tempfile.gettempdir()
                final_path = os.path.join(temp_base, 'dfs_app', os.path.basename(path))
                os.makedirs(final_path, mode=0o755, exist_ok=True)
                print(f"✅ Using temp {name} directory: {final_path}")
                return final_path
                
        except Exception as e:
            print(f"❌ Error creating {name} directory {path}: {e}")
            # Final emergency fallback
            emergency_path = os.path.join('.', f'emergency_{os.path.basename(path)}')
            os.makedirs(emergency_path, mode=0o755, exist_ok=True)
            print(f"🚨 Emergency fallback {name} directory: {emergency_path}")
            return emergency_path
    
    # Create directories with fallbacks
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
