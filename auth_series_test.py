#!/usr/bin/env python3
"""
Test script for BookTime API authentication and series endpoints
"""

import requests
import json
import time
import uuid
import sys

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://2edc0e99-0260-4be3-89a3-942129c74df3.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class BookTimeAPITester:
    def __init__(self):
        self.token = None
        self.user = None
        self.tests_run = 0
        self.tests_passed = 0
        self.book_ids_to_delete = []

    def run_test(self, name, method, endpoint, expected_status, data=None, auth=False, params=None):
        """Run a single API test"""
        url = f"{API_URL}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if auth and self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error details: {error_data}")
                except:
                    print(f"Response text: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_register(self, first_name, last_name):
        """Test user registration"""
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data={"first_name": first_name, "last_name": last_name}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user = response['user']
            print(f"User registered: {self.user['first_name']} {self.user['last_name']}")
            print(f"Token received: {self.token[:10]}...")
            return True
        return False

    def test_login(self, first_name, last_name):
        """Test user login"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data={"first_name": first_name, "last_name": last_name}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user = response['user']
            print(f"User logged in: {self.user['first_name']} {self.user['last_name']}")
            print(f"Token received: {self.token[:10]}...")
            return True
        return False

    def test_get_me(self):
        """Test get current user endpoint"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "auth/me",
            200,
            auth=True
        )
        if success:
            print(f"Current user: {response['first_name']} {response['last_name']}")
        return success

    def test_get_popular_series(self, category=None, limit=None):
        """Test getting popular series"""
        params = {}
        if category:
            params['category'] = category
        if limit:
            params['limit'] = limit
            
        success, response = self.run_test(
            f"Get Popular Series{' (category=' + category + ')' if category else ''}{' (limit=' + str(limit) + ')' if limit else ''}",
            "GET",
            "series/popular",
            200,
            auth=True,
            params=params
        )
        if success:
            print(f"Found {len(response['series'])} popular series")
            if category:
                for series in response['series']:
                    if series['category'] != category:
                        print(f"❌ Series {series['name']} has category {series['category']}, expected {category}")
                        return False
            if limit:
                if len(response['series']) > limit:
                    print(f"❌ Found {len(response['series'])} series, expected at most {limit}")
                    return False
        return success

    def test_search_series(self, query, category=None, limit=None):
        """Test searching for series"""
        params = {'q': query}
        if category:
            params['category'] = category
        if limit:
            params['limit'] = limit
            
        success, response = self.run_test(
            f"Search Series '{query}'",
            "GET",
            "series/search",
            200,
            auth=True,
            params=params
        )
        if success:
            print(f"Found {len(response['series'])} series matching '{query}'")
        return success

    def test_detect_series(self, title, author=None):
        """Test detecting series from a book title"""
        params = {'title': title}
        if author:
            params['author'] = author
            
        success, response = self.run_test(
            f"Detect Series for '{title}'",
            "GET",
            "series/detect",
            200,
            auth=True,
            params=params
        )
        if success:
            print(f"Found {len(response['detected_series'])} potential series matches")
            if response['detected_series']:
                top_match = response['detected_series'][0]
                print(f"Top match: {top_match['series']['name']} (confidence: {top_match['confidence']})")
                print(f"Match reasons: {top_match['match_reasons']}")
        return success

    def test_search_grouped(self, query):
        """Test searching with saga grouping"""
        params = {'q': query}
            
        success, response = self.run_test(
            f"Search Grouped '{query}'",
            "GET",
            "books/search-grouped",
            200,
            auth=True,
            params=params
        )
        if success:
            print(f"Found {response['total_books']} books in {response['total_sagas']} sagas matching '{query}'")
        return success

    def test_get_books(self):
        """Test getting all books"""
        success, response = self.run_test(
            "Get All Books",
            "GET",
            "books",
            200,
            auth=True
        )
        if success:
            print(f"Found {len(response)} books")
        return success

    def test_get_stats(self):
        """Test getting statistics"""
        success, response = self.run_test(
            "Get Statistics",
            "GET",
            "stats",
            200,
            auth=True
        )
        if success:
            print(f"Total books: {response['total_books']}")
            print(f"Categories: Roman: {response['categories']['roman']}, BD: {response['categories']['bd']}, Manga: {response['categories']['manga']}")
        return success

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting BookTime API Tests")
        
        # Generate unique test user
        timestamp = int(time.time())
        test_first_name = f"Test{timestamp}"
        test_last_name = f"User{timestamp}"
        
        # Test authentication endpoints
        print("\n=== Authentication Tests ===")
        if not self.test_register(test_first_name, test_last_name):
            print("❌ Registration failed, stopping tests")
            return False
            
        if not self.test_get_me():
            print("❌ Get current user failed, stopping tests")
            return False
            
        # Clear token and test login
        self.token = None
        if not self.test_login(test_first_name, test_last_name):
            print("❌ Login failed, stopping tests")
            return False
            
        # Test series endpoints
        print("\n=== Series Tests ===")
        if not self.test_get_popular_series():
            print("❌ Get popular series failed")
            
        if not self.test_get_popular_series(category="roman"):
            print("❌ Get popular series with category filter failed")
            
        if not self.test_get_popular_series(limit=3):
            print("❌ Get popular series with limit failed")
            
        if not self.test_search_series("Harry Potter"):
            print("❌ Search series failed")
            
        if not self.test_detect_series("Harry Potter et la Chambre des Secrets", "J.K. Rowling"):
            print("❌ Detect series (Harry Potter) failed")
            
        if not self.test_detect_series("One Piece Tome 42", "Eiichiro Oda"):
            print("❌ Detect series (One Piece) failed")
            
        if not self.test_detect_series("Astérix et Obélix: Mission Cléopâtre", "René Goscinny"):
            print("❌ Detect series (Astérix) failed")
            
        # Test search grouped endpoint
        print("\n=== Search Grouped Tests ===")
        if not self.test_search_grouped("Harry Potter"):
            print("❌ Search grouped failed")
            
        # Test basic endpoints
        print("\n=== Basic Endpoints Tests ===")
        if not self.test_get_books():
            print("❌ Get books failed")
            
        if not self.test_get_stats():
            print("❌ Get stats failed")
            
        # Print results
        print(f"\n📊 Tests passed: {self.tests_passed}/{self.tests_run}")
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = BookTimeAPITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)