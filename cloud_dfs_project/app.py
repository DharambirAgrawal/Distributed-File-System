#!/usr/bin/env python3
"""
Cloud Distributed File System (DFS) - Main Application Entry Point

This application demonstrates a distributed file system with:
- File chunking for distributed storage
- Local storage with PostgreSQL metadata
- Google Cloud Storage integration for backup
- REST API and web interface
- Fault tolerance with automatic chunk recovery
"""

from app import create_app
import os

# Set production environment if not already set
if not os.environ.get('FLASK_ENV'):
    os.environ['FLASK_ENV'] = 'production'

# Create Flask application instance for gunicorn
app = create_app()

if __name__ == '__main__':
    # Development server
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    
    print("🚀 Starting Cloud Distributed File System...")
    print(f"📊 Debug mode: {debug_mode}")
    print(f"🌐 Port: {port}")
    print(f"💾 Storage path: {app.config['STORAGE_PATH']}")
    print(f"📦 Chunk size: {app.config['CHUNK_SIZE']} bytes")
    print(f"☁️  Cloud backup: {app.config['ENABLE_CLOUD_BACKUP']}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode,
        threaded=True
    )
