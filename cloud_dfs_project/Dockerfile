FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create storage directory
RUN mkdir -p /app/storage /app/uploads /app/backup_cloud && \
    chmod 755 /app/storage /app/uploads /app/backup_cloud

# Set environment variables
ENV PYTHONPATH=/app
ENV FLASK_APP=run.py
ENV PYTHONUNBUFFERED=1

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port (Render uses $PORT environment variable)
EXPOSE $PORT

# Health check using our health endpoint
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-5000}/health || exit 1

# Run the application
CMD gunicorn run:app --bind 0.0.0.0:${PORT:-5000} --workers 2 --timeout 120
