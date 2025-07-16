#!/usr/bin/env python3
"""
BOOKTIME Mini-Fiches Feature Test Suite
Tests the new mini-fiches dropdown functionality
"""

import requests
import sys
import json
from datetime import datetime
import time

class BookTimeMiniFilesTester:
    def __init__(self, base_url="https://9db1f1c3-95d8-4bb0-bed7-aa3f0a4ecd38.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None

    def log(self, message):
        """Log with timestamp"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, response.text
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    self.log(f"   Error: {error_data}")
                except:
                    self.log(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test basic health endpoint"""
        success, response = self.run_test("Health Check", "GET", "health", 200)
        if success:
            self.log(f"✅ Backend is healthy: {response}")
        return success

    def test_auth_register_and_login(self):
        """Test user registration and login"""
        # First try to register a new user
        register_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": f"test_{int(time.time())}@example.com",
            "password": "TestPass123!"
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "api/auth/register",
            201,
            data=register_data
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response.get('user', {}).get('id')
            self.log(f"✅ Registered and logged in user with ID: {self.user_id}")
            return True
        
        # If registration fails, try login with existing Test User
        login_data = {
            "first_name": "Test",
            "last_name": "User"
        }
        
        success, response = self.run_test(
            "User Login Fallback",
            "POST",
            "api/auth/login",
            200,
            data=login_data
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response.get('user', {}).get('id')
            self.log(f"✅ Logged in existing user with ID: {self.user_id}")
            return True
        
        return False

    def test_series_popular(self):
        """Test getting popular series (needed for mini-fiches)"""
        success, response = self.run_test(
            "Get Popular Series",
            "GET",
            "api/series/popular?limit=10",
            200
        )
        
        if success and 'series' in response:
            series_count = len(response['series'])
            self.log(f"✅ Found {series_count} popular series")
            
            # Check if Harry Potter is in the list (needed for testing)
            harry_potter_found = any(
                'harry potter' in series.get('name', '').lower() 
                for series in response['series']
            )
            
            if harry_potter_found:
                self.log("✅ Harry Potter series found in popular series")
            else:
                self.log("⚠️  Harry Potter not found in popular series")
            
            return True
        return False

    def test_series_search_harry_potter(self):
        """Test searching for Harry Potter series"""
        success, response = self.run_test(
            "Search Harry Potter Series",
            "GET",
            "api/series/search?q=Harry Potter",
            200
        )
        
        if success and 'series' in response:
            series_count = len(response['series'])
            self.log(f"✅ Found {series_count} series matching 'Harry Potter'")
            
            if series_count > 0:
                first_series = response['series'][0]
                self.log(f"✅ First result: {first_series.get('name')} by {first_series.get('authors')}")
                return True
        return False

    def test_series_reading_preferences_empty(self):
        """Test getting reading preferences for a series (should be empty initially)"""
        series_name = "Harry Potter"
        
        success, response = self.run_test(
            "Get Reading Preferences - Empty",
            "GET",
            f"api/series/reading-preferences/{series_name}",
            200
        )
        
        if success and 'read_tomes' in response:
            read_tomes = response['read_tomes']
            self.log(f"✅ Reading preferences retrieved: {read_tomes}")
            return True
        return False

    def test_series_reading_preferences_save(self):
        """Test saving reading preferences for mini-fiches"""
        series_name = "Harry Potter"
        preferences_data = {
            "series_name": series_name,
            "read_tomes": [1, 2, 3]
        }
        
        success, response = self.run_test(
            "Save Reading Preferences",
            "POST",
            "api/series/reading-preferences",
            200,
            data=preferences_data
        )
        
        if success:
            self.log(f"✅ Reading preferences saved: {response}")
            return True
        return False

    def test_series_reading_preferences_retrieve(self):
        """Test retrieving saved reading preferences"""
        series_name = "Harry Potter"
        
        success, response = self.run_test(
            "Get Reading Preferences - With Data",
            "GET",
            f"api/series/reading-preferences/{series_name}",
            200
        )
        
        if success and 'read_tomes' in response:
            read_tomes = set(response['read_tomes'])
            expected_tomes = {1, 2, 3}
            
            if read_tomes == expected_tomes:
                self.log("✅ Reading preferences correctly saved and retrieved")
                return True
            else:
                self.log(f"❌ Reading preferences mismatch: got {read_tomes}, expected {expected_tomes}")
        return False

    def test_series_reading_preferences_update(self):
        """Test updating reading preferences"""
        series_name = "Harry Potter"
        update_data = {
            "read_tomes": [1, 2, 3, 4, 5]
        }
        
        success, response = self.run_test(
            "Update Reading Preferences",
            "PUT",
            f"api/series/reading-preferences/{series_name}",
            200,
            data=update_data
        )
        
        if success:
            self.log(f"✅ Reading preferences updated: {response}")
            
            # Verify the update
            success2, response2 = self.run_test(
                "Verify Updated Preferences",
                "GET",
                f"api/series/reading-preferences/{series_name}",
                200
            )
            
            if success2 and 'read_tomes' in response2:
                read_tomes = set(response2['read_tomes'])
                expected_tomes = {1, 2, 3, 4, 5}
                
                if read_tomes == expected_tomes:
                    self.log("✅ Reading preferences update verified")
                    return True
                else:
                    self.log(f"❌ Update verification failed: got {read_tomes}, expected {expected_tomes}")
        return False

    def test_books_create_for_series(self):
        """Test creating books for a series to test mini-fiches"""
        # Create a test book that belongs to Harry Potter series
        book_data = {
            "title": "Harry Potter à l'école des sorciers",
            "author": "J.K. Rowling",
            "category": "roman",
            "status": "to_read",
            "saga": "Harry Potter",
            "volume_number": 1,
            "description": "Premier tome de la série Harry Potter",
            "total_pages": 320,
            "publication_year": 1997
        }
        
        success, response = self.run_test(
            "Create Harry Potter Book",
            "POST",
            "api/books",
            201,
            data=book_data
        )
        
        if success and 'id' in response:
            book_id = response['id']
            self.log(f"✅ Created Harry Potter book with ID: {book_id}")
            
            # Store for cleanup
            self.created_book_id = book_id
            return True
        return False

    def test_books_search_grouped(self):
        """Test grouped search functionality for series"""
        success, response = self.run_test(
            "Search Books Grouped",
            "GET",
            "api/books/search-grouped?q=Harry Potter",
            200
        )
        
        if success and 'results' in response:
            results_count = len(response['results'])
            self.log(f"✅ Found {results_count} grouped results for 'Harry Potter'")
            
            # Check if we have series results
            series_results = [r for r in response['results'] if r.get('type') == 'series']
            book_results = [r for r in response['results'] if r.get('type') == 'book']
            
            self.log(f"✅ Series results: {len(series_results)}, Book results: {len(book_results)}")
            return True
        return False

    def cleanup_created_books(self):
        """Clean up any books created during testing"""
        if hasattr(self, 'created_book_id'):
            success, response = self.run_test(
                "Delete Test Book",
                "DELETE",
                f"api/books/{self.created_book_id}",
                200
            )
            if success:
                self.log("✅ Test book cleaned up")

    def run_all_tests(self):
        """Run all mini-fiches related tests"""
        self.log("🚀 Starting BOOKTIME Mini-Fiches Feature Tests...")
        self.log(f"🌐 Testing against: {self.base_url}")
        
        # Basic health check
        if not self.test_health_check():
            self.log("❌ Health check failed, stopping tests")
            return False
            
        # Authentication
        if not self.test_auth_register_and_login():
            self.log("❌ Authentication failed, stopping tests")
            return False
            
        # Test series functionality (needed for mini-fiches)
        test_methods = [
            self.test_series_popular,
            self.test_series_search_harry_potter,
            self.test_series_reading_preferences_empty,
            self.test_series_reading_preferences_save,
            self.test_series_reading_preferences_retrieve,
            self.test_series_reading_preferences_update,
            self.test_books_create_for_series,
            self.test_books_search_grouped
        ]
        
        for test_method in test_methods:
            try:
                if not test_method():
                    self.log(f"❌ {test_method.__name__} failed")
            except Exception as e:
                self.log(f"❌ {test_method.__name__} error: {str(e)}")
        
        # Cleanup
        self.cleanup_created_books()
        
        # Print final results
        self.log(f"\n📊 Mini-Fiches Test Results:")
        self.log(f"   Tests run: {self.tests_run}")
        self.log(f"   Tests passed: {self.tests_passed}")
        self.log(f"   Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            self.log("🎉 All mini-fiches tests passed!")
            return True
        else:
            self.log(f"⚠️  {self.tests_run - self.tests_passed} test(s) failed")
            return False

def main():
    """Main test runner"""
    tester = BookTimeMiniFilesTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())