from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import os
from dotenv import load_dotenv
import sys
from datetime import datetime

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Import our modules
from user.auth import UserAuth
from storage.uploader import FileUploader
from db.database import init_database, get_db_cursor, coerce_datetime
from search.algorithms import searcher
from share.share_link import ShareService
from share.decrypt import ShareAccessManager

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')

# Initialize database on startup
try:
    init_database()
except Exception as e:
    print(f"Failed to initialize database: {e}")

@app.route('/')
def index():
    """Home page - redirect to dashboard if logged in, otherwise to login"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        success, result = UserAuth.authenticate_user(username, password)
        
        if success:
            session['user_id'] = result
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(result, 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup page"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validation
        if len(username) < 3 or len(username) > 50:
            flash('Username must be between 3 and 50 characters', 'error')
            return render_template('signup.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long', 'error')
            return render_template('signup.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')
        
        success, result = UserAuth.create_user(username, password)
        
        if success:
            flash('Account created successfully! Please login.', 'success')
            return redirect(url_for('login'))
        else:
            flash(result, 'error')
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    """User dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = UserAuth.get_user_by_id(session['user_id'])
    files = FileUploader.get_user_files(session['user_id'])

    share_records = ShareService.get_user_shares(session['user_id'])
    recent_passwords = session.pop('recent_shares', {}) if 'recent_shares' in session else {}

    shares_by_document = {}
    for share in share_records:
        share_id_key = str(share['id'])
        if recent_passwords and share_id_key in recent_passwords:
            share['plain_password'] = recent_passwords[share_id_key]
        shares_by_document.setdefault(share['document_id'], []).append(share)

    for file_record in files:
        file_record['shares'] = shares_by_document.get(file_record['id'], [])

    share_base_url = request.host_url.rstrip('/')

    return render_template('dashboard.html', user=user, files=files, share_base_url=share_base_url)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """File upload page"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        success, result = FileUploader.upload_file(session['user_id'], file)
        
        if success:
            flash('File uploaded successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(result, 'error')
    
    return render_template('upload.html')

@app.route('/delete_file/<int:document_id>')
def delete_file(document_id):
    """Delete a file"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    success, message = FileUploader.delete_file(session['user_id'], document_id)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('dashboard'))


@app.route('/create_share/<int:document_id>', methods=['POST'])
def create_share(document_id):
    """Generate a secure share link for a document."""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    password = (request.form.get('share_password') or '').strip()
    max_downloads_raw = (request.form.get('max_downloads') or '').strip()
    expires_at_raw = (request.form.get('expires_at') or '').strip()

    max_downloads = None
    if max_downloads_raw:
        try:
            max_downloads = int(max_downloads_raw)
            if max_downloads <= 0:
                raise ValueError
        except ValueError:
            flash('Max downloads must be a positive integer.', 'error')
            return redirect(url_for('dashboard'))

    expires_at = None
    if expires_at_raw:
        try:
            expires_at = datetime.fromisoformat(expires_at_raw)
        except ValueError:
            flash('Invalid expiration date provided.', 'error')
            return redirect(url_for('dashboard'))

    try:
        share = ShareService.create_share(
            user_id=session['user_id'],
            document_id=document_id,
            password=password,
            max_downloads=max_downloads,
            expires_at=expires_at,
        )
    except ValueError as exc:
        flash(str(exc), 'error')
        return redirect(url_for('dashboard'))
    except Exception as exc:
        flash(f'Failed to create share link: {exc}', 'error')
        return redirect(url_for('dashboard'))

    recent = session.get('recent_shares', {})
    recent[str(share['id'])] = password
    session['recent_shares'] = recent

    flash('Secure share link created successfully.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/revoke/<int:share_id>', methods=['POST'])
def revoke_share(share_id):
    """Allow the owner to revoke an existing share."""
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if ShareService.revoke_share(user_id=session['user_id'], share_id=share_id):
        flash('Share link revoked.', 'success')
    else:
        flash('Unable to revoke share. It may not exist or belong to you.', 'error')

    return redirect(url_for('dashboard'))

@app.route('/add_tag/<int:document_id>', methods=['POST'])
def add_tag(document_id):
    """Add a tag to a document"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    tag_name = request.form.get('tag', '').strip()
    
    if not tag_name:
        flash('Tag cannot be empty', 'error')
        return redirect(url_for('dashboard'))
    
    success, message = FileUploader.add_tag(document_id, tag_name, session['user_id'])
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/remove_tag/<int:document_id>/<tag>')
def remove_tag(document_id, tag):
    """Remove a tag from a document"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    success, message = FileUploader.remove_tag(document_id, tag, session['user_id'])
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/search', methods=['GET', 'POST'])
def search():
    """Search documents"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        algorithm = request.form.get('algorithm', 'bfs')
        
        if not query:
            flash('Please enter a search query', 'error')
            return render_template('search.html')
        
        try:
            import time
            start_time = time.time()
            
            results = searcher.search(session['user_id'], query, algorithm, limit=50)
            
            execution_time = int((time.time() - start_time) * 1000)  # in milliseconds
            
            return render_template('search.html', 
                                 query=query, 
                                 algorithm=algorithm,
                                 results=[r.to_dict() for r in results],
                                 execution_time=execution_time)
        except Exception as e:
            flash(f'Search error: {str(e)}', 'error')
            return render_template('search.html')
    
    return render_template('search.html')

@app.route('/view_document/<int:document_id>')
def view_document(document_id):
    """View a specific document"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        with get_db_cursor() as cursor:
            cursor.execute(
                """
                SELECT d.id, d.file_name, d.summary, d.full_text_content, d.created_at
                FROM documents d
                WHERE d.id = %s AND d.user_id = %s
                """,
                (document_id, session['user_id'])
            )

            document_row = cursor.fetchone()

            if not document_row:
                flash('Document not found', 'error')
                return redirect(url_for('dashboard'))

            document = dict(document_row)
            document['created_at'] = coerce_datetime(document.get('created_at'))

            cursor.execute(
                "SELECT tag FROM tags WHERE document_id = %s ORDER BY id",
                (document_id,)
            )
            tag_rows = cursor.fetchall() or []
            document['tags'] = [row['tag'] for row in tag_rows if row.get('tag') is not None]

            return render_template('view_document.html', document=document)
            
    except Exception as e:
        flash(f'Error loading document: {str(e)}', 'error')
        return redirect(url_for('dashboard'))


def _redact_share_payload(share):
    if not share:
        return None
    sanitized = dict(share)
    sanitized.pop('password_hash', None)
    sanitized.pop('storage_path', None)
    sanitized.pop('owner_id', None)
    return sanitized


@app.route('/share/<token>', methods=['GET', 'POST'])
def shared_file(token):
    """Handle password-protected shared file access."""
    authorized = False
    error_message = None
    share = ShareService.get_share_by_token(token)

    ok, message = ShareAccessManager.validate_share_state(share)
    if not ok and request.method == 'GET':
        return render_template('error.html', message=message), 403

    if request.method == 'POST':
        password = (request.form.get('password') or '').strip()
        authorized, share, error_message = ShareAccessManager.authorize_with_password(token, password)
        if authorized:
            authorized_tokens = set(session.get('authorized_share_tokens', []))
            authorized_tokens.add(token)
            session['authorized_share_tokens'] = list(authorized_tokens)
        else:
            share = share or ShareService.get_share_by_token(token)

        if not authorized and error_message and error_message not in {'Incorrect password. Please try again.'}:
            # Fatal state (revoked, expired, etc.)
            return render_template('error.html', message=error_message), 403

    sanitized_share = _redact_share_payload(share)
    return render_template(
        'share.html',
        token=token,
        authorized=authorized,
        share=sanitized_share,
        error=error_message,
    )


@app.route('/share/<token>/download')
def download_shared_file(token):
    """Allow downloading a shared file after successful password validation."""
    authorized_tokens = set(session.get('authorized_share_tokens', []))
    if token not in authorized_tokens:
        share = ShareService.get_share_by_token(token)
        sanitized_share = _redact_share_payload(share)
        return render_template(
            'share.html',
            token=token,
            authorized=False,
            share=sanitized_share,
            error='Please enter the password before downloading.',
        ), 401

    ok, share, message = ShareAccessManager.authorize_without_password(token)
    if not ok:
        return render_template('error.html', message=message), 403

    success, updated_share, download_message = ShareAccessManager.register_download(share)
    if not success:
        sanitized_share = _redact_share_payload(updated_share or share)
        return render_template(
            'share.html',
            token=token,
            authorized=True,
            share=sanitized_share,
            error=download_message,
        ), 403

    storage_path = updated_share['storage_path']
    if not os.path.exists(storage_path):
        return render_template('error.html', message='The requested file is no longer available.'), 410

    return send_file(storage_path, as_attachment=True, download_name=updated_share['file_name'])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)