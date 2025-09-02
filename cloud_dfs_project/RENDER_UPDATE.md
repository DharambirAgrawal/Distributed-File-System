# Render Manual Configuration Update

If you're using manual deployment on Render (not the render.yaml), you need to update the Start Command in your Render dashboard:

## Steps to Update Render Dashboard:

1. **Go to your Render dashboard**
2. **Click on your web service**
3. **Go to Settings**
4. **Find "Start Command" section**
5. **Update the command to:**
   ```
   gunicorn run:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
   ```
6. **Click "Save Changes"**
7. **Redeploy your service**

## Alternative Commands (any of these should work):

- `gunicorn run:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120` (Recommended)
- `gunicorn wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
- `python run.py` (For development only)

## Environment Variables to Set:

Required:
- `SECRET_KEY`: Generate a secure random string

Optional:
- `DATABASE_URL`: Auto-provided if you add a PostgreSQL database
- `FLASK_ENV`: production (default)
- `STORAGE_PATH`: /opt/render/project/src/storage (default)
- `BACKUP_PATH`: /opt/render/project/src/backup_cloud (default)
- `ENABLE_CLOUD_BACKUP`: false (default for free tier)

## If Using Blueprint (render.yaml):

The render.yaml file is already updated. Just redeploy from your repository.

## Troubleshooting:

If you still get the error, try:
1. Clear build cache in Render
2. Redeploy from scratch
3. Check that the latest code is pushed to your main branch
4. Verify the Start Command is correctly set
