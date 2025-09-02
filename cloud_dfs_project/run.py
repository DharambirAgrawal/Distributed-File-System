#!/usr/bin/env python3
"""
Main application entry point for both development and production
Compatible with both 'app:app' and 'wsgi:application' gunicorn commands
"""

import os
import sys

# Set production environment if not already set
if not os.environ.get('FLASK_ENV'):
    os.environ['FLASK_ENV'] = 'production'

try:
    from app import create_app
    
    # Create Flask application instance
    app = create_app()
    
    # For WSGI compatibility
    application = app
    
    print(f"✅ Flask application loaded successfully")
    print(f"📊 Environment: {os.environ.get('FLASK_ENV', 'unknown')}")
    print(f"🌐 Debug mode: {app.debug}")
    
except Exception as e:
    print(f"❌ Failed to create Flask application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

if __name__ == '__main__':
    # Development server
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    
    print("🚀 Starting Cloud Distributed File System...")
    print(f"💾 Storage path: {app.config['STORAGE_PATH']}")
    print(f"📦 Chunk size: {app.config['CHUNK_SIZE']} bytes")
    print(f"☁️  Cloud backup: {app.config['ENABLE_CLOUD_BACKUP']}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug_mode,
        threaded=True
    )
