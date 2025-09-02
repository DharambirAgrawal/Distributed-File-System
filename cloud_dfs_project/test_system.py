#!/usr/bin/env python3
"""
Test script for Cloud Distributed File System
This script tests the API endpoints and basic functionality
"""

import requests
import json
import os
import tempfile
import time

# Configuration
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api"

def create_test_file(size_mb=1):
    """Create a test file with random data"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.test') as f:
        # Write some test data
        test_data = b"This is a test file for the DFS system. " * (1024 * size_mb // 40)
        f.write(test_data)
        return f.name

def test_upload_file():
    """Test file upload"""
    print("🔄 Testing file upload...")
    
    test_file = create_test_file(2)  # 2MB test file
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': ('test_file.txt', f, 'text/plain')}
            response = requests.post(f"{API_BASE}/files", files=files)
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Upload successful! File ID: {data['file_id']}")
            return data['file_id']
        else:
            print(f"❌ Upload failed: {response.text}")
            return None
    
    finally:
        os.unlink(test_file)

def test_list_files():
    """Test file listing"""
    print("🔄 Testing file listing...")
    
    response = requests.get(f"{API_BASE}/files")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ List successful! Found {len(data['files'])} files")
        return data['files']
    else:
        print(f"❌ List failed: {response.text}")
        return []

def test_download_file(file_id):
    """Test file download"""
    print(f"🔄 Testing file download for ID {file_id}...")
    
    response = requests.get(f"{API_BASE}/files/{file_id}")
    
    if response.status_code == 200:
        print(f"✅ Download successful! File size: {len(response.content)} bytes")
        return True
    else:
        print(f"❌ Download failed: {response.text}")
        return False

def test_sync_file(file_id):
    """Test cloud sync"""
    print(f"🔄 Testing cloud sync for ID {file_id}...")
    
    response = requests.post(f"{API_BASE}/files/{file_id}/sync")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Sync successful! {data['message']}")
        return True
    else:
        print(f"❌ Sync failed: {response.text}")
        return False

def test_storage_usage():
    """Test storage usage endpoint"""
    print("🔄 Testing storage usage...")
    
    response = requests.get(f"{API_BASE}/storage/usage")
    
    if response.status_code == 200:
        data = response.json()
        usage = data['usage']
        print(f"✅ Storage usage retrieved!")
        print(f"   Total size: {usage['total_size_mb']} MB")
        print(f"   Chunk count: {usage['chunk_count']}")
        print(f"   Cloud enabled: {usage['cloud_enabled']}")
        return True
    else:
        print(f"❌ Storage usage failed: {response.text}")
        return False

def test_web_interface():
    """Test web interface availability"""
    print("🔄 Testing web interface...")
    
    response = requests.get(BASE_URL)
    
    if response.status_code == 200:
        print("✅ Web interface is accessible!")
        return True
    else:
        print(f"❌ Web interface failed: {response.text}")
        return False

def wait_for_service(max_retries=30):
    """Wait for the service to be available"""
    print("⏳ Waiting for service to be available...")
    
    for i in range(max_retries):
        try:
            response = requests.get(BASE_URL, timeout=5)
            if response.status_code == 200:
                print("✅ Service is ready!")
                return True
        except requests.ConnectionError:
            pass
        
        print(f"   Attempt {i+1}/{max_retries}...")
        time.sleep(2)
    
    print("❌ Service did not become available in time")
    return False

def main():
    """Run all tests"""
    print("🚀 Starting Cloud DFS System Tests")
    print("=" * 50)
    
    # Wait for service
    if not wait_for_service():
        return
    
    # Test web interface
    test_web_interface()
    print()
    
    # Test storage usage
    test_storage_usage()
    print()
    
    # Test file upload
    file_id = test_upload_file()
    print()
    
    if file_id:
        # Test file listing
        files = test_list_files()
        print()
        
        # Test file download
        test_download_file(file_id)
        print()
        
        # Test cloud sync (might fail if cloud not configured)
        test_sync_file(file_id)
        print()
    
    print("=" * 50)
    print("🎉 Tests completed!")
    print()
    print("💡 Next steps:")
    print(f"   - Visit {BASE_URL} to use the web interface")
    print(f"   - Try uploading files through the UI")
    print(f"   - Check the API documentation at {BASE_URL}")
    
    if not os.environ.get('ENABLE_CLOUD_BACKUP') == 'true':
        print(f"   - Configure Google Cloud Storage for cloud backup")

if __name__ == "__main__":
    main()
