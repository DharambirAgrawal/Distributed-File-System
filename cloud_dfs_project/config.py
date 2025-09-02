import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database Configuration
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///dfs_dev.db'
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Storage Configuration
    CHUNK_SIZE = int(os.environ.get('CHUNK_SIZE', 1024 * 1024))  # 1MB default
    STORAGE_PATH = os.environ.get('STORAGE_PATH') or 'storage'
    
    # Local Backup Configuration (replaces Google Cloud Storage)
    ENABLE_CLOUD_BACKUP = os.environ.get('ENABLE_CLOUD_BACKUP', 'true').lower() == 'true'
    BACKUP_PATH = os.environ.get('BACKUP_PATH') or 'backup_cloud'
    
    # Upload Configuration
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file size
    UPLOAD_FOLDER = 'uploads'
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    # For production, use environment variables
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(24).hex()
    # Render provides DATABASE_URL for PostgreSQL
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL:
        # Handle postgres:// vs postgresql:// URL schemes
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # Fallback to SQLite for development/testing
        SQLALCHEMY_DATABASE_URI = 'sqlite:///dfs_prod.db'
    
    # Ensure paths work in production
    STORAGE_PATH = os.environ.get('STORAGE_PATH') or '/opt/render/project/src/storage'
    BACKUP_PATH = os.environ.get('BACKUP_PATH') or '/opt/render/project/src/backup_cloud'
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or '/opt/render/project/src/uploads'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
