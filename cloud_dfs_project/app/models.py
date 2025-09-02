from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db
import json

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship to files
    files = db.relationship('File', backref='owner', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert user object to dictionary (excluding sensitive data)"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active,
            'file_count': len(self.files)
        }
    
    def __repr__(self):
        return f'<User {self.username}>'

class File(db.Model):
    __tablename__ = 'files'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.BigInteger, nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    chunk_count = db.Column(db.Integer, nullable=False)
    chunk_size = db.Column(db.Integer, nullable=False)
    is_synced = db.Column(db.Boolean, default=False)
    cloud_url = db.Column(db.String(500), nullable=True)
    checksum = db.Column(db.String(64), nullable=True)
    _chunk_list = db.Column(db.Text, nullable=False)  # JSON string of chunk names
    
    # Foreign key to user
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    @property
    def chunk_list(self):
        """Get chunk list as Python list"""
        return json.loads(self._chunk_list) if self._chunk_list else []
    
    @chunk_list.setter
    def chunk_list(self, value):
        """Set chunk list from Python list"""
        self._chunk_list = json.dumps(value) if value else '[]'
    
    def to_dict(self):
        """Convert file object to dictionary"""
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'upload_date': self.upload_date.isoformat(),
            'chunk_count': self.chunk_count,
            'chunk_size': self.chunk_size,
            'is_synced': self.is_synced,
            'cloud_url': self.cloud_url,
            'checksum': self.checksum,
            'chunk_list': self.chunk_list,
            'user_id': self.user_id
        }
    
    def __repr__(self):
        return f'<File {self.filename}>'
