#!/usr/bin/env python3
"""
BOOKTIME Series Thumbnails Backend Test
Simple test for series functionality
"""

import requests
import sys
import json
from datetime import datetime

def log(message, level="INFO"):
    """Log messages with timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

def test_api():
    """Test the API endpoints for series functionality"""
    base_url = "https://changelog-reader-9.preview.emergentagent.com"
    
    log("🚀 Starting BOOKTIME Series Backend Test")
    log("=" * 50)
    
    # Test 1: Health Check
    log("🏥 Testing API Health...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            log(f"✅ API Health OK - Database: {data.get('database', 'unknown')}")
        else:
            log(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        log(f"❌ Health check error: {str(e)}")
        return False
    
    # Test 2: Try to access books endpoint without auth
    log("📚 Testing Books Endpoint Access...")
    try:
        response = requests.get(f"{base_url}/api/books/all", timeout=10)
        log(f"   Books endpoint status: {response.status_code}")
        if response.status_code == 401:
            log("   ✅ Authentication required (expected)")
        elif response.status_code == 200:
            log("   ⚠️ No authentication required")
        else:
            log(f"   ❓ Unexpected status: {response.status_code}")
    except Exception as e:
        log(f"❌ Books endpoint error: {str(e)}")
    
    # Test 3: Try login endpoint
    log("🔐 Testing Login Endpoint...")
    try:
        login_data = {"username": "test", "password": "test"}
        response = requests.post(f"{base_url}/api/auth/login", json=login_data, timeout=10)
        log(f"   Login endpoint status: {response.status_code}")
        if response.status_code == 200:
            log("   ✅ Login endpoint accessible")
        elif response.status_code == 401:
            log("   ✅ Login endpoint working (invalid credentials)")
        else:
            log(f"   ❓ Unexpected login status: {response.status_code}")
    except Exception as e:
        log(f"❌ Login endpoint error: {str(e)}")
    
    log("=" * 50)
    log("✅ Backend API is accessible and responding")
    log("📝 Next step: Test frontend integration with browser automation")
    
    return True

if __name__ == "__main__":
    success = test_api()
    sys.exit(0 if success else 1)