#!/usr/bin/env python3
"""
Minimal test script for the BOOKTIME API
"""

import requests

# Get the backend URL from the frontend .env file
BACKEND_URL = "http://localhost:8001"

def test_root():
    """Test the root endpoint"""
    print(f"Testing root endpoint: {BACKEND_URL}")
    response = requests.get(BACKEND_URL)
    print(f"Status code: {response.status_code}")
    
    if response.status_code == 200:
        print(f"Response: {response.json()}")
    else:
        try:
            print(f"Error: {response.json()}")
        except:
            print(f"Error: {response.text}")

if __name__ == "__main__":
    test_root()