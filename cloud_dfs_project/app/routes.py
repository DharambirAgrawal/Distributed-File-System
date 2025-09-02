from flask import Blueprint, render_template, request, jsonify, send_file, flash, redirect, url_for, current_app
from werkzeug.utils import secure_filename
from app import db
from app.models import File
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

def get_storage_instances():
    """Get storage instances with current app config"""
    storage_path = current_app.config['STORAGE_PATH']
    chunk_size = current_app.config['CHUNK_SIZE']
    
    local_storage = LocalStorage(storage_path)
    chunker = FileChunker(chunk_size)
    
    cloud_storage = None
    if current_app.config['ENABLE_CLOUD_BACKUP']:
        bucket_name = current_app.config['GCS_BUCKET_NAME']
        credentials_path = current_app.config['GOOGLE_APPLICATION_CREDENTIALS']
        if bucket_name:
            cloud_storage = CloudStorage(bucket_name, credentials_path)
    
    return local_storage, chunker, cloud_storage

# Web Interface Routes
@main.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@main.route('/upload')
def upload_page():
    """Upload page"""
    return render_template('upload.html')

@main.route('/files')
def files_page():
    """Files listing page"""
    files = File.query.order_by(File.upload_date.desc()).all()
    local_storage, _, _ = get_storage_instances()
    storage_usage = local_storage.get_storage_usage()
    
    return render_template('files.html', files=files, storage_usage=storage_usage)

@main.route('/upload', methods=['POST'])
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
def download_file_web(file_id):
    """Download file via web interface"""
    file_record = File.query.get_or_404(file_id)
    
    try:
        local_storage, chunker, cloud_storage = get_storage_instances()
        
        # Check for missing chunks and try to restore from cloud
        missing_chunks = chunker.verify_chunks(file_record.chunk_list, local_storage.storage_path)
        
        if missing_chunks and cloud_storage and cloud_storage.is_enabled():
            restored_chunks = cloud_storage.download_chunks(
                missing_chunks, local_storage.storage_path, str(file_record.id)
            )
            if restored_chunks:
                flash(f'Restored {len(restored_chunks)} chunks from cloud backup', 'info')
        
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
def sync_to_cloud(file_id):
    """Sync file to cloud storage"""
    file_record = File.query.get_or_404(file_id)
    
    try:
        local_storage, chunker, cloud_storage = get_storage_instances()
        
        if not cloud_storage or not cloud_storage.is_enabled():
            flash('Cloud storage is not configured', 'error')
            return redirect(url_for('main.files_page'))
        
        # Reconstruct file and upload to cloud
        file_data = chunker.reconstruct_file(file_record.chunk_list, local_storage.storage_path)
        
        cloud_url = cloud_storage.upload_file(
            file_data, 
            file_record.filename,
            metadata={
                'original_filename': file_record.original_filename,
                'upload_date': file_record.upload_date.isoformat(),
                'file_size': str(file_record.file_size)
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
            
            flash(f'File "{file_record.original_filename}" synced to cloud successfully!', 'success')
        else:
            flash('Failed to sync file to cloud', 'error')
    
    except Exception as e:
        flash(f'Sync failed: {str(e)}', 'error')
    
    return redirect(url_for('main.files_page'))

# API Routes
@api.route('/files', methods=['GET'])
def list_files():
    """API: List all files"""
    files = File.query.order_by(File.upload_date.desc()).all()
    return jsonify({
        'success': True,
        'files': [file.to_dict() for file in files]
    })

@api.route('/files', methods=['POST'])
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
def download_file_api(file_id):
    """API: Download a file"""
    file_record = File.query.get_or_404(file_id)
    
    try:
        local_storage, chunker, cloud_storage = get_storage_instances()
        
        # Check for missing chunks and try to restore from cloud
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
def sync_file_api(file_id):
    """API: Sync file to cloud storage"""
    file_record = File.query.get_or_404(file_id)
    
    try:
        local_storage, chunker, cloud_storage = get_storage_instances()
        
        if not cloud_storage or not cloud_storage.is_enabled():
            return jsonify({'success': False, 'message': 'Cloud storage not configured'}), 400
        
        # Reconstruct file and upload to cloud
        file_data = chunker.reconstruct_file(file_record.chunk_list, local_storage.storage_path)
        
        cloud_url = cloud_storage.upload_file(
            file_data, 
            file_record.filename,
            metadata={
                'original_filename': file_record.original_filename,
                'upload_date': file_record.upload_date.isoformat(),
                'file_size': str(file_record.file_size)
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
                'message': 'File synced to cloud successfully',
                'cloud_url': cloud_url
            })
        else:
            return jsonify({'success': False, 'message': 'Failed to sync to cloud'}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@api.route('/files/<int:file_id>', methods=['DELETE'])
def delete_file_api(file_id):
    """API: Delete a file"""
    file_record = File.query.get_or_404(file_id)
    
    try:
        local_storage, _, cloud_storage = get_storage_instances()
        
        # Delete local chunks
        local_storage.delete_chunks(file_record.chunk_list)
        
        # Delete from cloud if synced
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
def storage_usage_api():
    """API: Get storage usage statistics"""
    local_storage, _, cloud_storage = get_storage_instances()
    
    usage = local_storage.get_storage_usage()
    usage['cloud_enabled'] = cloud_storage.is_enabled() if cloud_storage else False
    
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
            chunk_list=chunk_names
        )
        
        db.session.add(file_record)
        db.session.commit()
        
        result = {
            'success': True,
            'message': 'File uploaded successfully',
            'file_id': file_record.id,
            'filename': original_filename,
            'size': file_size,
            'chunks': len(chunk_names)
        }
        
        # Auto-sync to cloud if enabled
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
                        'file_size': str(file_size)
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
                    
                    result['cloud_synced'] = True
                    result['cloud_url'] = cloud_url
            except Exception as e:
                print(f"Auto-sync to cloud failed: {e}")
                result['cloud_sync_error'] = str(e)
        
        return result
    
    except Exception as e:
        return {'success': False, 'message': str(e)}
