#!/usr/bin/env python3
"""
Simple test script for the BOOKTIME API authentication endpoints
"""

import requests
import json

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://98c3b9a8-f97f-475f-862c-5125aa777726.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

def test_register():
    """Test user registration"""
    user_data = {
        "first_name": "John",
        "last_name": "Doe"
    }
    
    print(f"Testing registration with {user_data}")
    response = requests.post(f"{API_URL}/auth/register", json=user_data)
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return data.get("access_token")
    else:
        try:
            print(f"Error: {response.json()}")
        except:
            print(f"Error: {response.text}")
        return None

def test_login(first_name, last_name):
    """Test user login"""
    user_data = {
        "first_name": first_name,
        "last_name": last_name
    }
    
    print(f"\nTesting login with {user_data}")
    response = requests.post(f"{API_URL}/auth/login", json=user_data)
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        return data.get("access_token")
    else:
        try:
            print(f"Error: {response.json()}")
        except:
            print(f"Error: {response.text}")
        return None

def test_me(token):
    """Test getting current user info"""
    if not token:
        print("\nSkipping /me test - no token available")
        return
    
    print(f"\nTesting /me with token")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{API_URL}/auth/me", headers=headers)
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
    else:
        try:
            print(f"Error: {response.json()}")
        except:
            print(f"Error: {response.text}")

def main():
    """Run all tests"""
    # Test registration
    token = test_register()
    
    # Test login
    if not token:
        print("\nRegistration failed, trying login with default user")
        token = test_login("John", "Doe")
    else:
        print("\nRegistration successful, trying login with same user")
        token = test_login("John", "Doe")
    
    # Test /me
    test_me(token)

if __name__ == "__main__":
    main()