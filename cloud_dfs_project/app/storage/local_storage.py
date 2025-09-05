import os
import shutil
from typing import List, BinaryIO

class LocalStorage:
    """Handles local file storage operations for chunks"""
    
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        
        # Ensure storage directory exists
        if not os.path.exists(storage_path):
            os.makedirs(storage_path)
    
    def store_chunks(self, file_obj: BinaryIO, chunk_names: List[str], chunk_size: int) -> bool:
        """
        Store file chunks to local storage
        
        Args:
            file_obj: File object to read from
            chunk_names: List of chunk names to use
            chunk_size: Size of each chunk
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Reset file pointer
            file_obj.seek(0)
            
            for chunk_name in chunk_names:
                chunk_path = os.path.join(self.storage_path, chunk_name)
                chunk_data = file_obj.read(chunk_size)
                
                if not chunk_data:
                    break
                
                with open(chunk_path, 'wb') as chunk_file:
                    chunk_file.write(chunk_data)
            
            return True
        except Exception as e:
            print(f"Error storing chunks: {e}")
            return False
    
    def retrieve_chunk(self, chunk_name: str) -> bytes:
        """
        Retrieve a specific chunk from local storage
        
        Args:
            chunk_name: Name of the chunk to retrieve
            
        Returns:
            bytes: Chunk data
        """
        chunk_path = os.path.join(self.storage_path, chunk_name)
        
        if not os.path.exists(chunk_path):
            raise FileNotFoundError(f"Chunk {chunk_name} not found")
        
        with open(chunk_path, 'rb') as chunk_file:
            return chunk_file.read()
    
    def delete_chunks(self, chunk_names: List[str]) -> bool:
        """
        Delete chunks from local storage
        
        Args:
            chunk_names: List of chunk names to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            for chunk_name in chunk_names:
                chunk_path = os.path.join(self.storage_path, chunk_name)
                if os.path.exists(chunk_path):
                    os.remove(chunk_path)
            return True
        except Exception as e:
            print(f"Error deleting chunks: {e}")
            return False
    
    def chunk_exists(self, chunk_name: str) -> bool:
        """
        Check if a chunk exists in local storage
        
        Args:
            chunk_name: Name of the chunk to check
            
        Returns:
            bool: True if chunk exists, False otherwise
        """
        chunk_path = os.path.join(self.storage_path, chunk_name)
        return os.path.exists(chunk_path)
    
    def get_storage_usage(self) -> dict:
        """
        Get storage usage statistics
        
        Returns:
            dict: Storage usage information
        """
        total_size = 0
        file_count = 0
        
        for filename in os.listdir(self.storage_path):
            file_path = os.path.join(self.storage_path, filename)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)
                file_count += 1
        
        return {
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'chunk_count': file_count
        }
