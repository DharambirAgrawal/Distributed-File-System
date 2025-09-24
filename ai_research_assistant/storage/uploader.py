import os

from werkzeug.utils import secure_filename

from db.database import get_db_cursor, coerce_datetime
from utils.file_utils import (
    ensure_user_directory,
    extract_text_from_file,
    format_file_size,
    get_page_count_from_bytes,
    get_user_upload_dir,
)

class FileUploader:
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg', 'gif'}
    MAX_FILE_SIZE_MB = float(os.getenv('MAX_UPLOAD_SIZE_MB', '10'))
    MAX_PAGE_COUNT = int(os.getenv('MAX_UPLOAD_PAGE_LIMIT', '50'))
    
    @staticmethod
    def allowed_file(filename):
        """Check if file extension is allowed"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in FileUploader.ALLOWED_EXTENSIONS

    @classmethod
    def _max_file_size_bytes(cls) -> int:
        return int(cls.MAX_FILE_SIZE_MB * 1024 * 1024)

    @classmethod
    def _validate_upload_limits(cls, file, extension: str):
        """Validate file size and page limits before saving."""
        file.stream.seek(0, os.SEEK_END)
        size_bytes = file.stream.tell()
        file.stream.seek(0)

        if size_bytes > cls._max_file_size_bytes():
            max_size_readable = format_file_size(cls._max_file_size_bytes())
            actual_size_readable = format_file_size(size_bytes)
            return False, f"File exceeds the maximum allowed size of {max_size_readable}. Uploaded file size: {actual_size_readable}."

        page_check_extensions = {'pdf', 'doc', 'docx'}
        if extension in page_check_extensions:
            file_bytes = file.read()
            file.stream.seek(0)
            try:
                page_count = get_page_count_from_bytes(file_bytes, extension)
            except ValueError as exc:
                return False, str(exc)

            if page_count > cls.MAX_PAGE_COUNT:
                return False, (
                    f"Document has {page_count} pages which exceeds the limit of {cls.MAX_PAGE_COUNT} pages."
                )

        return True, None
    
    @staticmethod
    def upload_file(user_id, file):
        """Upload a file for a user"""
        try:
            if not file or file.filename == '':
                return False, "No file selected"
            
            if not FileUploader.allowed_file(file.filename):
                return False, "File type not allowed"
            
            # Secure the filename
            filename = secure_filename(file.filename)
            extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

            ok, message = FileUploader._validate_upload_limits(file, extension)
            if not ok:
                return False, message
            
            # Ensure user directory exists
            user_dir = get_user_upload_dir(user_id)
            ensure_user_directory(user_dir)
            
            # Create unique filename if file already exists
            file_path = os.path.join(user_dir, filename)
            counter = 1
            base_name, extension = os.path.splitext(filename)
            while os.path.exists(file_path):
                filename = f"{base_name}_{counter}{extension}"
                file_path = os.path.join(user_dir, filename)
                counter += 1
            
            # Save file
            file.save(file_path)
            
            # Extract text content from the file
            full_text_content = extract_text_from_file(file_path)
            
            # Save metadata to database with full text content
            with get_db_cursor() as cursor:
                cursor.execute(
                    "INSERT INTO documents (user_id, file_name, storage_path, full_text_content) VALUES (%s, %s, %s, %s) RETURNING id",
                    (user_id, filename, file_path, full_text_content)
                )
                document_id = cursor.fetchone()['id']
                
            return True, document_id
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def get_user_files(user_id):
        """Get all files for a user"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute("""
                    SELECT d.id, d.file_name, d.storage_path, d.summary, d.created_at
                    FROM documents d
                    WHERE d.user_id = %s
                    ORDER BY d.created_at DESC
                """, (user_id,))

                documents = []
                for row in cursor.fetchall() or []:
                    record = dict(row)
                    record['created_at'] = coerce_datetime(record.get('created_at'))
                    cursor.execute(
                        "SELECT tag FROM tags WHERE document_id = %s ORDER BY id",
                        (record['id'],)
                    )
                    tag_rows = cursor.fetchall() or []
                    record['tags'] = [tag_row['tag'] for tag_row in tag_rows if tag_row.get('tag') is not None]
                    documents.append(record)

                return documents
        except Exception as e:
            print(f"Error getting user files: {e}")
            return []
    
    @staticmethod
    def delete_file(user_id, document_id):
        """Delete a file and its metadata"""
        try:
            with get_db_cursor() as cursor:
                # Get file path
                cursor.execute(
                    "SELECT storage_path FROM documents WHERE id = %s AND user_id = %s",
                    (document_id, user_id)
                )
                result = cursor.fetchone()
                
                if not result:
                    return False, "File not found"
                
                file_path = result['storage_path']
                
                # Delete file from filesystem
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                # Delete from database (cascade will handle tags)
                cursor.execute(
                    "DELETE FROM documents WHERE id = %s AND user_id = %s",
                    (document_id, user_id)
                )
                
                return True, "File deleted successfully"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def add_tag(document_id, tag_name, user_id):
        """Add a tag to a document"""
        try:
            with get_db_cursor() as cursor:
                # Verify document belongs to user
                cursor.execute(
                    "SELECT id FROM documents WHERE id = %s AND user_id = %s",
                    (document_id, user_id)
                )
                if not cursor.fetchone():
                    return False, "Document not found"
                
                # Check if tag already exists for this document
                cursor.execute(
                    "SELECT id FROM tags WHERE document_id = %s AND tag = %s",
                    (document_id, tag_name)
                )
                if cursor.fetchone():
                    return False, "Tag already exists for this document"
                
                # Add tag
                cursor.execute(
                    "INSERT INTO tags (document_id, tag) VALUES (%s, %s)",
                    (document_id, tag_name)
                )
                return True, "Tag added successfully"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def remove_tag(document_id, tag_name, user_id):
        """Remove a tag from a document"""
        try:
            with get_db_cursor() as cursor:
                # Verify document belongs to user and remove tag
                cursor.execute("""
                    DELETE FROM tags 
                    WHERE document_id = %s AND tag = %s 
                    AND document_id IN (SELECT id FROM documents WHERE user_id = %s)
                """, (document_id, tag_name, user_id))
                
                if cursor.rowcount > 0:
                    return True, "Tag removed successfully"
                return False, "Tag not found"
        except Exception as e:
            return False, str(e)