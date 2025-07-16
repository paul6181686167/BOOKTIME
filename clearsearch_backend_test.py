#!/usr/bin/env python3
"""
BOOKTIME ClearSearch Fix Validation Test
Focused test for the clearSearch functionality and series addition workflow
"""

import requests
import sys
import json
from datetime import datetime
import time

class ClearSearchValidationTest:
    def __init__(self):
        self.backend_url = "https://b16e2314-ae06-4775-b2d0-fc50a903187d.preview.emergentagent.com"
        self.token = None
        self.user_id = None
        self.test_timestamp = datetime.now().strftime('%H%M%S%f')
        self.test_user = {
            "first_name": "ClearSearch",
            "last_name": f"Test{self.test_timestamp}"
        }

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make HTTP request with proper headers"""
        url = f"{self.backend_url}/{endpoint.lstrip('/')}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=15)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=15)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=15)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=15)
            
            success = response.status_code == expected_status
            
            if success:
                self.log(f"✅ {method} {endpoint} - Status: {response.status_code}")
            else:
                self.log(f"❌ {method} {endpoint} - Expected {expected_status}, got {response.status_code}", "ERROR")
                if response.text:
                    self.log(f"Response: {response.text[:300]}", "ERROR")
            
            try:
                response_data = response.json() if response.text else {}
            except:
                response_data = {"raw_response": response.text}
            
            return success, response_data, response.status_code
            
        except Exception as e:
            self.log(f"❌ {method} {endpoint} - Exception: {str(e)}", "ERROR")
            return False, {"error": str(e)}, 0

    def test_health(self):
        """Test basic connectivity"""
        self.log("🔍 Testing backend health...")
        success, data, status = self.make_request('GET', '/health')
        return success

    def test_authentication(self):
        """Test user registration and authentication"""
        self.log("🔍 Testing authentication...")
        
        # Register new user
        success, data, status = self.make_request('POST', '/api/auth/register', self.test_user)
        
        if success and 'access_token' in data:
            self.token = data['access_token']
            self.user_id = data['user']['id']
            self.log(f"✅ Authenticated as: {self.test_user['first_name']} {self.test_user['last_name']}")
            
            # Test /me endpoint
            me_success, me_data, me_status = self.make_request('GET', '/api/auth/me')
            return success and me_success
        
        return False

    def test_series_endpoints(self):
        """Test series-related endpoints needed for clearSearch validation"""
        self.log("🔍 Testing series endpoints...")
        
        if not self.token:
            self.log("❌ No authentication token", "ERROR")
            return False
        
        # Test popular series
        success1, popular_data, _ = self.make_request('GET', '/api/series/popular')
        
        # Test series search
        success2, search_data, _ = self.make_request('GET', '/api/series/search?q=Harry Potter')
        
        # Test series library (should be empty initially)
        success3, library_data, _ = self.make_request('GET', '/api/series/library')
        
        # Test add series to library if we have popular series
        success4 = True
        if success1 and popular_data.get('series'):
            first_series = popular_data['series'][0]
            series_data = {
                "name": first_series['name'],
                "category": first_series['category'],
                "author": first_series.get('authors', ['Unknown'])[0],
                "description": first_series.get('description', ''),
                "total_volumes": first_series.get('volumes', 1),
                "status": "to_read"
            }
            
            success4, add_data, _ = self.make_request('POST', '/api/series/library', series_data)
            
            if success4:
                self.log(f"✅ Successfully added series: {first_series['name']}")
        
        return success1 and success2 and success3 and success4

    def test_openlibrary_search(self):
        """Test OpenLibrary search functionality"""
        self.log("🔍 Testing OpenLibrary search...")
        
        if not self.token:
            self.log("❌ No authentication token", "ERROR")
            return False
        
        success, data, _ = self.make_request('GET', '/api/openlibrary/search?q=Harry Potter&limit=5')
        
        if success and data.get('results'):
            self.log(f"✅ OpenLibrary search returned {len(data['results'])} results")
        
        return success

    def test_books_endpoints(self):
        """Test books endpoints"""
        self.log("🔍 Testing books endpoints...")
        
        if not self.token:
            self.log("❌ No authentication token", "ERROR")
            return False
        
        # Test get books
        success1, books_data, _ = self.make_request('GET', '/api/books')
        
        # Test create book
        test_book = {
            "title": f"ClearSearch Test Book {self.test_timestamp}",
            "author": "Test Author",
            "category": "roman",
            "status": "to_read",
            "description": "Test book for clearSearch validation"
        }
        
        success2, create_data, _ = self.make_request('POST', '/api/books', test_book)
        
        return success1 and success2

    def test_stats_endpoint(self):
        """Test statistics endpoint"""
        self.log("🔍 Testing stats endpoint...")
        
        if not self.token:
            self.log("❌ No authentication token", "ERROR")
            return False
        
        success, data, _ = self.make_request('GET', '/api/stats')
        return success

    def run_all_tests(self):
        """Run all validation tests"""
        self.log("🚀 Starting ClearSearch Fix Validation Tests")
        self.log(f"🎯 Backend URL: {self.backend_url}")
        self.log(f"🔑 Test User: {self.test_user['first_name']} {self.test_user['last_name']}")
        
        tests = [
            ("Backend Health", self.test_health),
            ("Authentication", self.test_authentication),
            ("Series Endpoints", self.test_series_endpoints),
            ("OpenLibrary Search", self.test_openlibrary_search),
            ("Books Endpoints", self.test_books_endpoints),
            ("Statistics", self.test_stats_endpoint),
        ]
        
        results = []
        for test_name, test_func in tests:
            self.log(f"\n📋 Running {test_name}...")
            try:
                result = test_func()
                results.append(result)
                if result:
                    self.log(f"✅ {test_name} - PASSED")
                else:
                    self.log(f"❌ {test_name} - FAILED", "ERROR")
            except Exception as e:
                self.log(f"❌ {test_name} - EXCEPTION: {str(e)}", "ERROR")
                results.append(False)
        
        # Summary
        passed = sum(results)
        total = len(results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        self.log(f"\n📊 Test Summary:")
        self.log(f"Tests passed: {passed}/{total}")
        self.log(f"Success rate: {success_rate:.1f}%")
        
        if passed == total:
            self.log("🎉 All backend tests PASSED! Ready for UI testing.")
            return True
        else:
            self.log("⚠️ Some backend tests FAILED. Check logs above.", "ERROR")
            return False

def main():
    print("=" * 60)
    print("BOOKTIME ClearSearch Fix Validation Test")
    print("=" * 60)
    
    tester = ClearSearchValidationTest()
    success = tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())