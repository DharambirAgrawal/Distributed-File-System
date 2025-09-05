import os
import uuid
import hashlib
from typing import List, BinaryIO

class FileChunker:
    """Handles file chunking and reconstruction operations"""
    
    def __init__(self, chunk_size: int = 1024 * 1024):
        self.chunk_size = chunk_size
    
    def chunk_file(self, file_obj: BinaryIO, filename: str) -> tuple:
        """
        Split a file into chunks and return chunk information
        
        Args:
            file_obj: File object to chunk
            filename: Original filename
            
        Returns:
            tuple: (chunk_names, total_size, checksum)
        """
        chunk_names = []
        total_size = 0
        hasher = hashlib.sha256()
        
        # Reset file pointer to beginning
        file_obj.seek(0)
        
        chunk_index = 0
        while True:
            chunk_data = file_obj.read(self.chunk_size)
            if not chunk_data:
                break
            
            # Generate unique chunk name
            chunk_name = f"{uuid.uuid4().hex}_{chunk_index}.chunk"
            chunk_names.append(chunk_name)
            
            # Update hash and size
            hasher.update(chunk_data)
            total_size += len(chunk_data)
            chunk_index += 1
        
        checksum = hasher.hexdigest()
        return chunk_names, total_size, checksum
    
    def reconstruct_file(self, chunk_names: List[str], storage_path: str) -> bytes:
        """
        Reconstruct a file from its chunks
        
        Args:
            chunk_names: List of chunk filenames
            storage_path: Path where chunks are stored
            
        Returns:
            bytes: Reconstructed file data
        """
        reconstructed_data = b''
        
        for chunk_name in chunk_names:
            chunk_path = os.path.join(storage_path, chunk_name)
            if not os.path.exists(chunk_path):
                raise FileNotFoundError(f"Chunk {chunk_name} not found")
            
            with open(chunk_path, 'rb') as chunk_file:
                reconstructed_data += chunk_file.read()
        
        return reconstructed_data
    
    def verify_chunks(self, chunk_names: List[str], storage_path: str) -> List[str]:
        """
        Verify which chunks are missing from local storage
        
        Args:
            chunk_names: List of chunk filenames to verify
            storage_path: Path where chunks should be stored
            
        Returns:
            List[str]: List of missing chunk names
        """
        missing_chunks = []
        
        for chunk_name in chunk_names:
            chunk_path = os.path.join(storage_path, chunk_name)
            if not os.path.exists(chunk_path):
                missing_chunks.append(chunk_name)
        
        return missing_chunks
