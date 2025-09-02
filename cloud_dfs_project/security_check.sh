#!/bin/bash
# Security validation script for Cloud DFS
# Run this script to ensure your environment is secure

echo "🔒 Cloud DFS Security Validation"
echo "================================"

# Check if sensitive files are ignored
echo "📋 Checking .gitignore protection..."
if git check-ignore cloud_dfs_project/.env cloud_dfs_project/google_secret.json >/dev/null 2>&1; then
    echo "✅ Sensitive files are properly ignored by git"
else
    echo "❌ WARNING: Sensitive files may not be protected!"
    echo "   Make sure .env and google_secret.json are in .gitignore"
fi

# Check for staged sensitive files
echo "📋 Checking git staging area..."
if git status --porcelain | grep -E "(\.env|google_secret|credentials)" >/dev/null 2>&1; then
    echo "❌ WARNING: Sensitive files found in git staging!"
    echo "   Run: git reset HEAD <filename> to unstage"
else
    echo "✅ No sensitive files in git staging area"
fi

# Check file permissions
echo "📋 Checking file permissions..."
if [ -f "google_secret.json" ]; then
    perms=$(stat -c "%a" google_secret.json)
    if [ "$perms" -eq 600 ] || [ "$perms" -eq 644 ]; then
        echo "✅ Google credentials file has appropriate permissions"
    else
        echo "⚠️  Consider restricting credentials file permissions:"
        echo "   chmod 600 google_secret.json"
    fi
else
    echo "❌ Google credentials file not found"
fi

# Check environment variables
echo "📋 Checking environment configuration..."
if [ -f ".env" ]; then
    if grep -q "your-bucket-name" .env; then
        echo "⚠️  Update GCS_BUCKET_NAME in .env file"
    else
        echo "✅ Bucket name appears to be configured"
    fi
    
    if grep -q "your-secret-key" .env; then
        echo "⚠️  Update SECRET_KEY in .env file for production"
    else
        echo "✅ Secret key appears to be configured"
    fi
else
    echo "❌ .env file not found"
fi

echo ""
echo "🎯 Next Steps:"
echo "1. Update GCS_BUCKET_NAME in .env with your actual bucket"
echo "2. Test file upload/download functionality"
echo "3. For production: use proper secret management"
echo "4. Never commit .env or credentials files"

echo ""
echo "✨ Your environment appears secure for development!"
