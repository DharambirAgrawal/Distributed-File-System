import os
import shutil
import json
from typing import List, Optional

class CloudStorage:
    """Handles local backup storage operations to simulate cloud storage"""
    
    def __init__(self, backup_path: str, user_id: Optional[str] = None):
        self.backup_path = backup_path
        self.user_id = user_id or "default"
        
        # Create user-specific backup directory
        self.user_backup_path = os.path.join(backup_path, f"user_{self.user_id}")
        self.files_path = os.path.join(self.user_backup_path, "files")
        self.chunks_path = os.path.join(self.user_backup_path, "chunks")
        self.metadata_path = os.path.join(self.user_backup_path, "metadata")
        
        # Ensure backup directories exist
        os.makedirs(self.files_path, exist_ok=True)
        os.makedirs(self.chunks_path, exist_ok=True)
        os.makedirs(self.metadata_path, exist_ok=True)
        
        self.enabled = True
    
    def is_enabled(self) -> bool:
        """Check if local backup storage is properly configured and enabled"""
        return self.enabled and os.path.exists(self.backup_path)
    
    def upload_file(self, file_data: bytes, filename: str, metadata: dict = None) -> Optional[str]:
        """
        Upload a complete file to local backup storage
        
        Args:
            file_data: File data as bytes
            filename: Name for the file in backup storage
            metadata: Optional metadata dictionary
            
        Returns:
            str: Local backup URL if successful, None otherwise
        """
        if not self.is_enabled():
            return None
        
        try:
            file_path = os.path.join(self.files_path, filename)
            
            # Write file data
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            # Save metadata if provided
            if metadata:
                metadata_file = os.path.join(self.metadata_path, f"{filename}.json")
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
            
            return f"local://{self.user_backup_path}/files/{filename}"
            
        except Exception as e:
            print(f"Error uploading file to local backup: {e}")
            return None
    
    def download_file(self, filename: str) -> Optional[bytes]:
        """
        Download a file from local backup storage
        
        Args:
            filename: Name of the file in backup storage
            
        Returns:
            bytes: File data if successful, None otherwise
        """
        if not self.is_enabled():
            return None
        
        try:
            file_path = os.path.join(self.files_path, filename)
            
            if not os.path.exists(file_path):
                return None
            
            with open(file_path, 'rb') as f:
                return f.read()
            
        except Exception as e:
            print(f"Error downloading file from local backup: {e}")
            return None
    
    def upload_chunks(self, chunk_names: List[str], local_storage_path: str, file_id: str) -> bool:
        """
        Upload individual chunks to local backup storage
        
        Args:
            chunk_names: List of chunk names to upload
            local_storage_path: Path where chunks are stored locally
            file_id: Unique identifier for the file
            
        Returns:
            bool: True if all chunks uploaded successfully
        """
        if not self.is_enabled():
            return False
        
        try:
            # Create file-specific chunk directory
            file_chunks_path = os.path.join(self.chunks_path, file_id)
            os.makedirs(file_chunks_path, exist_ok=True)
            
            for chunk_name in chunk_names:
                local_chunk_path = os.path.join(local_storage_path, chunk_name)
                
                if not os.path.exists(local_chunk_path):
                    continue
                
                backup_chunk_path = os.path.join(file_chunks_path, chunk_name)
                shutil.copy2(local_chunk_path, backup_chunk_path)
            
            return True
            
        except Exception as e:
            print(f"Error uploading chunks to local backup: {e}")
            return False
    
    def download_chunks(self, chunk_names: List[str], local_storage_path: str, file_id: str) -> List[str]:
        """
        Download missing chunks from local backup storage
        
        Args:
            chunk_names: List of chunk names to download
            local_storage_path: Path where chunks should be stored locally
            file_id: Unique identifier for the file
            
        Returns:
            List[str]: List of successfully downloaded chunk names
        """
        if not self.is_enabled():
            return []
        
        downloaded_chunks = []
        
        try:
            file_chunks_path = os.path.join(self.chunks_path, file_id)
            
            if not os.path.exists(file_chunks_path):
                return downloaded_chunks
            
            for chunk_name in chunk_names:
                backup_chunk_path = os.path.join(file_chunks_path, chunk_name)
                
                if not os.path.exists(backup_chunk_path):
                    continue
                
                local_chunk_path = os.path.join(local_storage_path, chunk_name)
                shutil.copy2(backup_chunk_path, local_chunk_path)
                downloaded_chunks.append(chunk_name)
            
            return downloaded_chunks
            
        except Exception as e:
            print(f"Error downloading chunks from local backup: {e}")
            return downloaded_chunks
    
    def delete_file(self, filename: str) -> bool:
        """
        Delete a file from local backup storage
        
        Args:
            filename: Name of the file to delete
            
        Returns:
            bool: True if successful
        """
        if not self.is_enabled():
            return False
        
        try:
            file_path = os.path.join(self.files_path, filename)
            metadata_file = os.path.join(self.metadata_path, f"{filename}.json")
            
            if os.path.exists(file_path):
                os.remove(file_path)
            
            if os.path.exists(metadata_file):
                os.remove(metadata_file)
            
            return True
            
        except Exception as e:
            print(f"Error deleting file from local backup: {e}")
            return False
    
    def delete_chunks(self, chunk_names: List[str], file_id: str) -> bool:
        """
        Delete chunks from local backup storage
        
        Args:
            chunk_names: List of chunk names to delete
            file_id: Unique identifier for the file
            
        Returns:
            bool: True if successful
        """
        if not self.is_enabled():
            return False
        
        try:
            file_chunks_path = os.path.join(self.chunks_path, file_id)
            
            if os.path.exists(file_chunks_path):
                shutil.rmtree(file_chunks_path)
            
            return True
            
        except Exception as e:
            print(f"Error deleting chunks from local backup: {e}")
            return False
    
    def list_files(self) -> List[str]:
        """
        List all files in local backup storage
        
        Returns:
            List[str]: List of file names
        """
        if not self.is_enabled():
            return []
        
        try:
            if not os.path.exists(self.files_path):
                return []
            
            return [f for f in os.listdir(self.files_path) 
                   if os.path.isfile(os.path.join(self.files_path, f))]
            
        except Exception as e:
            print(f"Error listing files from local backup: {e}")
            return []
    
    def get_backup_usage(self) -> dict:
        """
        Get backup storage usage statistics
        
        Returns:
            dict: Backup usage information
        """
        total_size = 0
        file_count = 0
        chunk_count = 0
        
        try:
            # Count files
            if os.path.exists(self.files_path):
                for filename in os.listdir(self.files_path):
                    file_path = os.path.join(self.files_path, filename)
                    if os.path.isfile(file_path):
                        total_size += os.path.getsize(file_path)
                        file_count += 1
            
            # Count chunks
            if os.path.exists(self.chunks_path):
                for file_dir in os.listdir(self.chunks_path):
                    file_chunks_path = os.path.join(self.chunks_path, file_dir)
                    if os.path.isdir(file_chunks_path):
                        for chunk_file in os.listdir(file_chunks_path):
                            chunk_path = os.path.join(file_chunks_path, chunk_file)
                            if os.path.isfile(chunk_path):
                                total_size += os.path.getsize(chunk_path)
                                chunk_count += 1
        
        except Exception as e:
            print(f"Error calculating backup usage: {e}")
        
        return {
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'file_count': file_count,
            'chunk_count': chunk_count,
            'user_id': self.user_id
        }
