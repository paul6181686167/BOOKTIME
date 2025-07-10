#!/usr/bin/env python3
"""
Investigation détaillée de l'endpoint GET /api/books
"""

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://2f8adca6-e967-4c31-a654-c73ff2215dca.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

def investigate_books_endpoint():
    """Investigate the books endpoint response format"""
    try:
        # First, register a test user
        test_user = {
            "first_name": "TestInvestigation",
            "last_name": "BooksEndpoint",
            "email": f"test_investigation_{datetime.now().strftime('%Y%m%d_%H%M%S')}@test.com"
        }
        
        register_response = requests.post(f"{API_BASE}/auth/register", json=test_user, timeout=10)
        
        if register_response.status_code == 200:
            register_data = register_response.json()
            token = register_data["access_token"]
            
            # Test the books endpoint
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{API_BASE}/books", headers=headers, timeout=10)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Type: {type(response.json())}")
            print(f"Response Content:")
            print(json.dumps(response.json(), indent=2))
            
            # Test with different parameters
            print("\n" + "="*50)
            print("Testing with view_mode parameter:")
            
            response_books = requests.get(f"{API_BASE}/books?view_mode=books", headers=headers, timeout=10)
            print(f"view_mode=books - Status: {response_books.status_code}, Type: {type(response_books.json())}")
            
            response_series = requests.get(f"{API_BASE}/books?view_mode=series", headers=headers, timeout=10)
            print(f"view_mode=series - Status: {response_series.status_code}, Type: {type(response_series.json())}")
            
        else:
            print(f"Failed to register user: {register_response.status_code}")
            
    except Exception as e:
        print(f"Exception: {str(e)}")

if __name__ == "__main__":
    investigate_books_endpoint()