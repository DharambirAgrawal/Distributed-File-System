#!/bin/bash
set -e

echo "🚀 Starting Distributed File System deployment..."

# Create necessary directories
mkdir -p storage uploads backup_cloud

# Run database migrations if needed
if [ -f "migrate_db.py" ]; then
    echo "📊 Running database migrations..."
    python migrate_db.py
fi

echo "✅ Setup complete, starting application..."

# Start the application
exec gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
