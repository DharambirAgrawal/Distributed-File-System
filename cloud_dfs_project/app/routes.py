from flask import Blueprint, render_template, request, jsonify, send_file, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import File, User
from app.storage.chunker import FileChunker
from app.storage.local_storage import LocalStorage
from app.storage.cloud_storage import CloudStorage
import os
import io
import uuid
from datetime import datetime

# Blueprint for web interface
main = Blueprint('main', __name__)

# Blueprint for REST API
api = Blueprint('api', __name__)

def get_user_storage_path(user_id):
    """Get user-specific storage path"""
    base_path = current_app.config['STORAGE_PATH']
    user_path = os.path.join(base_path, f"user_{user_id}")
    os.makedirs(user_path, exist_ok=True)
    return user_path

def get_storage_instances(user_id=None):
    """Get storage instances with current app config and user context"""
    if user_id is None and current_user.is_authenticated:
        user_id = current_user.id
    elif user_id is None:
        user_id = 'anonymous'
    
    # User-specific storage path
    storage_path = get_user_storage_path(user_id)
    chunk_size = current_app.config['CHUNK_SIZE']
    
    local_storage = LocalStorage(storage_path)
    chunker = FileChunker(chunk_size)
    
    cloud_storage = None
    if current_app.config['ENABLE_CLOUD_BACKUP']:
        backup_path = current_app.config['BACKUP_PATH']
        cloud_storage = CloudStorage(backup_path, str(user_id))
    
    return local_storage, chunker, cloud_storage

# Web Interface Routes
@main.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@main.route('/upload')
@login_required
def upload_page():
    """Upload page"""
    return render_template('upload.html')

@main.route('/files')
@login_required
def files_page():
    """Files listing page"""
    files = File.query.filter_by(user_id=current_user.id).order_by(File.upload_date.desc()).all()
    local_storage, _, cloud_storage = get_storage_instances()
    storage_usage = local_storage.get_storage_usage()
    
    # Get backup usage if available
    backup_usage = None
    if cloud_storage and cloud_storage.is_enabled():
        backup_usage = cloud_storage.get_backup_usage()
    
    return render_template('files.html', files=files, storage_usage=storage_usage, backup_usage=backup_usage)

@main.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """Handle file upload from web form"""
    if 'file' not in request.files:
        flash('No file selected', 'error')
        return redirect(url_for('main.upload_page'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected', 'error')
        return redirect(url_for('main.upload_page'))
    
    # Process file upload
    result = process_file_upload(file)
    
    if result['success']:
        flash(f'File "{file.filename}" uploaded successfully!', 'success')
    else:
        flash(f'Upload failed: {result["message"]}', 'error')
    
    return redirect(url_for('main.files_page'))

@main.route('/download/<int:file_id>')
@login_required
def download_file_web(file_id):
    """Download file via web interface"""
    file_record = File.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    
    try:
        local_storage, chunker, cloud_storage = get_storage_instances()
        
        # Check for missing chunks and try to restore from backup
        missing_chunks = chunker.verify_chunks(file_record.chunk_list, local_storage.storage_path)
        
        if missing_chunks and cloud_storage and cloud_storage.is_enabled():
            restored_chunks = cloud_storage.download_chunks(
                missing_chunks, local_storage.storage_path, str(file_record.id)
            )
            if restored_chunks:
                flash(f'Restored {len(restored_chunks)} chunks from backup', 'info')
        
        # Reconstruct file
        file_data = chunker.reconstruct_file(file_record.chunk_list, local_storage.storage_path)
        
        return send_file(
            io.BytesIO(file_data),
            as_attachment=True,
            download_name=file_record.original_filename,
            mimetype='application/octet-stream'
        )
    
    except Exception as e:
        flash(f'Download failed: {str(e)}', 'error')
        return redirect(url_for('main.files_page'))

@main.route('/sync/<int:file_id>')
@login_required
def sync_to_backup(file_id):
    """Sync file to backup storage"""
    file_record = File.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    
    try:
        local_storage, chunker, cloud_storage = get_storage_instances()
        
        if not cloud_storage or not cloud_storage.is_enabled():
            flash('Backup storage is not configured', 'error')
            return redirect(url_for('main.files_page'))
        
        # Reconstruct file and upload to backup
        file_data = chunker.reconstruct_file(file_record.chunk_list, local_storage.storage_path)
        
        cloud_url = cloud_storage.upload_file(
            file_data, 
            file_record.filename,
            metadata={
                'original_filename': file_record.original_filename,
                'upload_date': file_record.upload_date.isoformat(),
                'file_size': str(file_record.file_size),
                'user_id': str(current_user.id)
            }
        )
        
        if cloud_url:
            file_record.is_synced = True
            file_record.cloud_url = cloud_url
            db.session.commit()
            
            # Also upload chunks for redundancy
            cloud_storage.upload_chunks(
                file_record.chunk_list, local_storage.storage_path, str(file_record.id)
            )
            
            flash(f'File "{file_record.original_filename}" synced to backup successfully!', 'success')
        else:
            flash('Failed to sync file to backup', 'error')
    
    except Exception as e:
        flash(f'Sync failed: {str(e)}', 'error')
    
    return redirect(url_for('main.files_page'))

# API Routes
@api.route('/files', methods=['GET'])
@login_required
def list_files():
    """API: List all files for current user"""
    files = File.query.filter_by(user_id=current_user.id).order_by(File.upload_date.desc()).all()
    return jsonify({
        'success': True,
        'files': [file.to_dict() for file in files],
        'user_id': current_user.id
    })

@api.route('/files', methods=['POST'])
@login_required
def upload_file_api():
    """API: Upload a file"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400
    
    result = process_file_upload(file)
    
    if result['success']:
        return jsonify(result), 201
    else:
        return jsonify(result), 400

@api.route('/files/<int:file_id>', methods=['GET'])
@login_required
def download_file_api(file_id):
    """API: Download a file"""
    file_record = File.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    
    try:
        local_storage, chunker, cloud_storage = get_storage_instances()
        
        # Check for missing chunks and try to restore from backup
        missing_chunks = chunker.verify_chunks(file_record.chunk_list, local_storage.storage_path)
        
        if missing_chunks and cloud_storage and cloud_storage.is_enabled():
            cloud_storage.download_chunks(
                missing_chunks, local_storage.storage_path, str(file_record.id)
            )
        
        # Reconstruct file
        file_data = chunker.reconstruct_file(file_record.chunk_list, local_storage.storage_path)
        
        return send_file(
            io.BytesIO(file_data),
            as_attachment=True,
            download_name=file_record.original_filename,
            mimetype='application/octet-stream'
        )
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/files/<int:file_id>/sync', methods=['POST'])
@login_required
def sync_file_api(file_id):
    """API: Sync file to backup storage"""
    file_record = File.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    
    try:
        local_storage, chunker, cloud_storage = get_storage_instances()
        
        if not cloud_storage or not cloud_storage.is_enabled():
            return jsonify({'success': False, 'message': 'Backup storage not configured'}), 400
        
        # Reconstruct file and upload to backup
        file_data = chunker.reconstruct_file(file_record.chunk_list, local_storage.storage_path)
        
        cloud_url = cloud_storage.upload_file(
            file_data, 
            file_record.filename,
            metadata={
                'original_filename': file_record.original_filename,
                'upload_date': file_record.upload_date.isoformat(),
                'file_size': str(file_record.file_size),
                'user_id': str(current_user.id)
            }
        )
        
        if cloud_url:
            file_record.is_synced = True
            file_record.cloud_url = cloud_url
            db.session.commit()
            
            # Also upload chunks for redundancy
            cloud_storage.upload_chunks(
                file_record.chunk_list, local_storage.storage_path, str(file_record.id)
            )
            
            return jsonify({
                'success': True, 
                'message': 'File synced to backup successfully',
                'cloud_url': cloud_url
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to sync to backup'}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/files/<int:file_id>', methods=['DELETE'])
@login_required
def delete_file_api(file_id):
    """API: Delete a file"""
    file_record = File.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    
    try:
        local_storage, _, cloud_storage = get_storage_instances()
        
        # Delete local chunks
        local_storage.delete_chunks(file_record.chunk_list)
        
        # Delete from backup if synced
        if file_record.is_synced and cloud_storage and cloud_storage.is_enabled():
            cloud_storage.delete_file(file_record.filename)
            cloud_storage.delete_chunks(file_record.chunk_list, str(file_record.id))
        
        # Delete database record
        db.session.delete(file_record)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'File deleted successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/storage/usage', methods=['GET'])
@login_required
def storage_usage_api():
    """API: Get storage usage statistics"""
    local_storage, _, cloud_storage = get_storage_instances()
    
    usage = local_storage.get_storage_usage()
    usage['backup_enabled'] = cloud_storage.is_enabled() if cloud_storage else False
    usage['user_id'] = current_user.id
    
    if cloud_storage and cloud_storage.is_enabled():
        usage['backup_usage'] = cloud_storage.get_backup_usage()
    
    return jsonify({'success': True, 'usage': usage})

def process_file_upload(file):
    """Process file upload (shared by web and API routes)"""
    try:
        local_storage, chunker, cloud_storage = get_storage_instances()
        
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
        
        # Chunk the file
        chunk_names, file_size, checksum = chunker.chunk_file(file, original_filename)
        
        # Store chunks locally
        file.seek(0)  # Reset file pointer
        if not local_storage.store_chunks(file, chunk_names, chunker.chunk_size):
            return {'success': False, 'message': 'Failed to store file chunks'}
        
        # Create database record
        file_record = File(
            filename=unique_filename,
            original_filename=original_filename,
            file_size=file_size,
            chunk_count=len(chunk_names),
            chunk_size=chunker.chunk_size,
            checksum=checksum,
            chunk_list=chunk_names,
            user_id=current_user.id
        )
        
        db.session.add(file_record)
        db.session.commit()
        
        result = {
            'success': True,
            'message': 'File uploaded successfully',
            'file_id': file_record.id,
            'filename': original_filename,
            'size': file_size,
            'chunks': len(chunk_names),
            'user_id': current_user.id
        }
        
        # Auto-sync to backup if enabled
        if cloud_storage and cloud_storage.is_enabled():
            try:
                file.seek(0)
                file_data = file.read()
                cloud_url = cloud_storage.upload_file(
                    file_data, 
                    unique_filename,
                    metadata={
                        'original_filename': original_filename,
                        'upload_date': file_record.upload_date.isoformat(),
                        'file_size': str(file_size),
                        'user_id': str(current_user.id)
                    }
                )
                
                if cloud_url:
                    file_record.is_synced = True
                    file_record.cloud_url = cloud_url
                    db.session.commit()
                    
                    # Also upload chunks
                    cloud_storage.upload_chunks(
                        chunk_names, local_storage.storage_path, str(file_record.id)
                    )
                    
                    result['backup_synced'] = True
                    result['backup_url'] = cloud_url
            except Exception as e:
                print(f"Auto-sync to backup failed: {e}")
                result['backup_sync_error'] = str(e)
        
        return result
    
    except Exception as e:
        return {'success': False, 'message': str(e)}
