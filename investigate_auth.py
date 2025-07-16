#!/usr/bin/env python3
"""
Investigation détaillée de l'authentification
"""

import requests
import json
from datetime import datetime

# Configuration
BACKEND_URL = "https://637d4469-7291-4b2a-87d6-f5863d434c99.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

def investigate_auth():
    """Investigate authentication issues"""
    try:
        # Test d'inscription
        test_user = {
            "first_name": "TestAuth",
            "last_name": "Investigation",
            "email": f"test_auth_{datetime.now().strftime('%Y%m%d_%H%M%S')}@test.com"
        }
        
        print("Testing registration with:")
        print(json.dumps(test_user, indent=2))
        
        register_response = requests.post(f"{API_BASE}/auth/register", json=test_user, timeout=10)
        
        print(f"\nRegistration Response:")
        print(f"Status Code: {register_response.status_code}")
        print(f"Headers: {dict(register_response.headers)}")
        
        try:
            response_data = register_response.json()
            print(f"Response Body: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Response Text: {register_response.text}")
        
        # Try with minimal data
        print("\n" + "="*50)
        print("Trying with minimal data (first_name + last_name only):")
        
        minimal_user = {
            "first_name": "TestMinimal",
            "last_name": "User"
        }
        
        minimal_response = requests.post(f"{API_BASE}/auth/register", json=minimal_user, timeout=10)
        print(f"Minimal Registration Status: {minimal_response.status_code}")
        
        try:
            minimal_data = minimal_response.json()
            print(f"Minimal Response: {json.dumps(minimal_data, indent=2)}")
        except:
            print(f"Minimal Response Text: {minimal_response.text}")
            
    except Exception as e:
        print(f"Exception: {str(e)}")

if __name__ == "__main__":
    investigate_auth()