from datetime import datetime
from app import db
import json

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
            'chunk_list': self.chunk_list
        }
    
    def __repr__(self):
        return f'<File {self.filename}>'
