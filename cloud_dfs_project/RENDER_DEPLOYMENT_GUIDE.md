# 🚀 Render Deployment Guide

This guide shows how to deploy your Distributed File System to Render using Docker.

## Prerequisites

1. ✅ Docker containers are working locally (test with `./docker-test.sh prod`)
2. ✅ Code is pushed to GitHub repository
3. ✅ Render account created

## Render Configuration

### 1. Web Service Configuration

Create a new **Web Service** in Render with these settings:

**Basic Settings:**
- **Name**: `distributed-file-system`
- **Environment**: `Docker`
- **Region**: Choose closest to your users
- **Branch**: `main` (or your deployment branch)
- **Root Directory**: `cloud_dfs_project`

**Docker Settings:**
- **Dockerfile Path**: `./Dockerfile`
- **Docker Command**: Leave empty (uses CMD from Dockerfile)

### 2. Environment Variables

Set these environment variables in Render:

```bash
# Database (Render PostgreSQL)
DATABASE_URL=<Your Render PostgreSQL URL>

# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=false
SECRET_KEY=<Generate a strong secret key>

# Storage Paths
STORAGE_PATH=/app/storage
BACKUP_PATH=/app/backup_cloud
UPLOAD_FOLDER=/app/uploads

# File System Settings
CHUNK_SIZE=1048576
ENABLE_CLOUD_BACKUP=false

# Port (Render automatically sets this)
PORT=$PORT
```

### 3. PostgreSQL Database

1. Create a **PostgreSQL** service in Render
2. Copy the **Internal Database URL** 
3. Set it as the `DATABASE_URL` environment variable
4. The database will be automatically initialized using `init-db.sql`

### 4. Health Check

Render will automatically use the health check defined in your Dockerfile:
- Endpoint: `/health`
- Expected response: `{"service":"Distributed File System","status":"healthy",...}`

## Deployment Steps

### Step 1: Prepare Repository
```bash
# Ensure your code is committed and pushed
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### Step 2: Create Render Services

1. **Create PostgreSQL Database:**
   - Go to Render Dashboard
   - Click "New +"
   - Select "PostgreSQL"
   - Choose a name (e.g., `dfs-database`)
   - Select region and plan
   - Note the Internal Database URL

2. **Create Web Service:**
   - Click "New +"
   - Select "Web Service"
   - Connect your GitHub repository
   - Configure as described above

### Step 3: Environment Variables

In your Web Service settings, add all the environment variables listed above.

**Important Environment Variables:**
```bash
DATABASE_URL=postgresql://username:password@hostname:port/database_name
SECRET_KEY=your-super-secret-key-here-make-it-long-and-random
FLASK_ENV=production
```

### Step 4: Deploy

1. Click "Create Web Service"
2. Render will automatically:
   - Build your Docker image
   - Deploy the container
   - Set up health checks
   - Provide a public URL

## Render Deployment Files

Your repository already includes these Render-specific files:

- **`render.yaml`**: Infrastructure as Code configuration
- **`Dockerfile`**: Production-ready container definition
- **`init-db.sql`**: Database initialization script

## Testing Your Deployment

Once deployed, test these endpoints:

```bash
# Health check
curl https://your-app-name.onrender.com/health

# Main application
curl https://your-app-name.onrender.com/
```

## Monitoring and Logs

### View Logs
- Go to your Web Service in Render Dashboard
- Click "Logs" tab
- Monitor application startup and requests

### Metrics
- Render provides built-in metrics
- Monitor CPU, Memory, and Response times
- Set up alerts for downtime

## Troubleshooting

### Common Issues:

1. **Build Failures:**
   - Check Dockerfile syntax
   - Ensure all requirements are in `requirements.txt`
   - Verify root directory is set to `cloud_dfs_project`

2. **Database Connection Issues:**
   - Verify `DATABASE_URL` is correctly set
   - Check PostgreSQL service is running
   - Ensure database credentials are correct

3. **Application Not Starting:**
   - Check environment variables
   - Review application logs
   - Verify health check endpoint responds

4. **Port Issues:**
   - Don't hardcode port 5000
   - Use `PORT` environment variable
   - Render automatically assigns ports

### Debug Commands:
```bash
# Local testing (should match Render environment)
docker build -t dfs-test .
docker run -p 5000:5000 --env-file .env dfs-test

# Check logs locally
docker-compose logs web -f
```

## Performance Optimization

### For Production:

1. **Resource Allocation:**
   - Start with Render's starter plan
   - Monitor usage and upgrade if needed
   - Consider upgrading PostgreSQL for better performance

2. **Docker Optimizations:**
   - Multi-stage builds (already implemented)
   - Minimal base image (python:3.11-slim)
   - Non-root user for security

3. **Application Optimizations:**
   - Gunicorn with multiple workers
   - Health checks for reliability
   - Proper error handling

## Security Considerations

✅ **Already Implemented:**
- Non-root Docker user
- Environment variable for secrets
- Production-ready Flask settings
- Health check endpoints

🔧 **Additional Recommendations:**
- Use Render's secret management
- Enable HTTPS (automatic with Render)
- Set up monitoring and alerts
- Regular security updates

## Cost Optimization

- **Starter Plan**: Good for testing and low traffic
- **Standard Plan**: Better performance, custom domains
- **PostgreSQL**: Start with shared, upgrade to dedicated if needed

## Next Steps After Deployment

1. ✅ Test all functionality
2. ✅ Set up monitoring
3. ✅ Configure custom domain (optional)
4. ✅ Set up CI/CD for automatic deployments
5. ✅ Monitor logs and performance

---

## Quick Deployment Checklist

- [ ] PostgreSQL service created in Render
- [ ] Database URL noted
- [ ] Web service configured
- [ ] Environment variables set
- [ ] Repository connected
- [ ] Deployment successful
- [ ] Health check passing
- [ ] Application accessible
- [ ] File upload/download working
- [ ] User authentication working

**Your app will be available at:** `https://your-service-name.onrender.com`
