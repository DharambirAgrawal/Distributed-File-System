# Render Deployment Guide

This project is configured for deployment on Render. Follow these steps:

## Prerequisites
- GitHub account with this repository
- Render account (free tier available)

## Deployment Steps

### Option 1: Using render.yaml (Infrastructure as Code)
1. Fork/clone this repository to your GitHub account
2. Go to [render.com](https://render.com) and sign up/login
3. Click "New +" → "Blueprint"
4. Connect your GitHub repository
5. Select the repository and branch
6. Click "Apply" to deploy

### Option 2: Manual Setup
1. Go to [render.com](https://render.com) and sign up/login
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: distributed-file-system
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
   - **Plan**: Free (or choose paid for better performance)

### Database Setup
1. Create a PostgreSQL database on Render:
   - Click "New +" → "PostgreSQL"
   - Choose Free plan
   - Note the database URL provided

2. Add environment variables to your web service:
   - `DATABASE_URL`: [Your PostgreSQL connection string from Render]
   - `SECRET_KEY`: [Generate a secure random key]
   - `FLASK_ENV`: production
   - `ENABLE_CLOUD_BACKUP`: false (for now)

## Environment Variables
The following environment variables should be set in Render:

- `DATABASE_URL`: PostgreSQL connection string (auto-provided by Render DB)
- `SECRET_KEY`: Secure random string for session encryption
- `FLASK_ENV`: production
- `CHUNK_SIZE`: 1048576 (1MB, optional)
- `ENABLE_CLOUD_BACKUP`: false (disable cloud backup for free tier)

## Features Available After Deployment
- ✅ File upload and download
- ✅ File chunking and distributed storage
- ✅ User authentication
- ✅ Web interface
- ✅ REST API
- ✅ PostgreSQL database
- ⏸️ Cloud backup (disabled for free tier)

## Accessing Your Application
After deployment, Render will provide you with a URL like:
`https://your-app-name.onrender.com`

## Troubleshooting
- Check Render logs if deployment fails
- Ensure all environment variables are set
- Database migrations run automatically on startup
- Free tier may have cold starts (app sleeps after inactivity)

## Scaling
For production use, consider upgrading to:
- Paid Render plan for better performance
- Larger database instance
- Enable cloud backup features
