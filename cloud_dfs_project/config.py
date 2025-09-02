import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database Configuration
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'postgresql://dfs_user:dfs_password@localhost:5432/dfs_db'
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Storage Configuration
    CHUNK_SIZE = int(os.environ.get('CHUNK_SIZE', 1024 * 1024))  # 1MB default
    STORAGE_PATH = os.environ.get('STORAGE_PATH') or 'storage'
    
    # Google Cloud Storage Configuration
    ENABLE_CLOUD_BACKUP = os.environ.get('ENABLE_CLOUD_BACKUP', 'false').lower() == 'true'
    GOOGLE_APPLICATION_CREDENTIALS = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    GCS_BUCKET_NAME = os.environ.get('GCS_BUCKET_NAME')
    
    # Upload Configuration
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB max file size
    UPLOAD_FOLDER = 'uploads'

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
