"""
WSGI entry point for production deployment
"""

import os
import sys

# Set production environment
os.environ.setdefault('FLASK_ENV', 'production')

try:
    from app import create_app
    
    # Create the Flask application
    application = create_app()
    
    # For compatibility with different WSGI servers
    app = application
    
    print(f"✅ Flask application created successfully")
    print(f"📊 Environment: {os.environ.get('FLASK_ENV', 'unknown')}")
    print(f"💾 Storage path: {application.config.get('STORAGE_PATH', 'unknown')}")
    
except Exception as e:
    print(f"❌ Failed to create Flask application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

if __name__ == "__main__":
    application.run()
