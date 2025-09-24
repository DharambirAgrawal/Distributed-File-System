#!/usr/bin/env python3
"""
Test script for the AI Research Assistant application
"""

import requests
import sys
import os

# Test the application endpoints
BASE_URL = "http://localhost:5000"

def test_signup():
    """Test user signup functionality"""
    print("Testing user signup...")
    
    signup_data = {
        'username': 'testuser',
        'password': 'testpass123',
        'confirm_password': 'testpass123'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/signup", data=signup_data, allow_redirects=False)
        print(f"Signup response status: {response.status_code}")
        
        if response.status_code == 302:
            print("✅ Signup successful - redirected to login")
            return True
        else:
            print("❌ Signup failed")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to application. Make sure it's running on localhost:5000")
        return False

def test_login():
    """Test user login functionality"""
    print("\nTesting user login...")
    
    # First create a session
    session = requests.Session()
    
    login_data = {
        'username': 'testuser',
        'password': 'testpass123'
    }
    
    try:
        response = session.post(f"{BASE_URL}/login", data=login_data, allow_redirects=False)
        print(f"Login response status: {response.status_code}")
        
        if response.status_code == 302:
            print("✅ Login successful - redirected to dashboard")
            return True, session
        else:
            print("❌ Login failed")
            return False, None
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to application")
        return False, None

def test_dashboard_access(session):
    """Test dashboard access"""
    print("\nTesting dashboard access...")
    
    try:
        response = session.get(f"{BASE_URL}/dashboard")
        print(f"Dashboard response status: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Dashboard accessible")
            return True
        else:
            print("❌ Dashboard not accessible")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to application")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing AI Research Assistant Application")
    print("=" * 50)
    
    # Test signup
    signup_success = test_signup()
    
    if signup_success:
        # Test login
        login_success, session = test_login()
        
        if login_success and session:
            # Test dashboard
            dashboard_success = test_dashboard_access(session)
            
            if dashboard_success:
                print("\n🎉 All tests passed! Application is working correctly.")
            else:
                print("\n❌ Dashboard test failed")
        else:
            print("\n❌ Login test failed")
    else:
        print("\n❌ Signup test failed")
    
    print("\n📝 Manual testing suggestions:")
    print("1. Open http://localhost:5000 in your browser")
    print("2. Create a new account")
    print("3. Login with your credentials")
    print("4. Upload a test file")
    print("5. Add tags to your files")
    print("6. Test file deletion")

if __name__ == "__main__":
    main()