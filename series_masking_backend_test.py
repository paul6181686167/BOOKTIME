#!/usr/bin/env python3
"""
BOOKTIME - Test du masquage des livres individuels appartenant à une série
Test backend spécifique pour vérifier que l'API retourne les bonnes données
pour permettre le masquage côté frontend.
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BACKEND_URL = "https://e9f1d2bf-e80d-4695-805f-09976ca1a870.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class SeriesMaskingAPITest:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.token = None
        self.test_user_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "test.user@booktime.com",
            "password": "TestPassword123!"
        }

    def log_test(self, name, success, message=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if message:
                print(f"   {message}")
        else:
            print(f"❌ {name}")
            if message:
                print(f"   {message}")

    def test_health_check(self):
        """Test API health"""
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=10)
            success = response.status_code == 200
            if success:
                data = response.json()
                message = f"Database: {data.get('database', 'unknown')}"
            else:
                message = f"Status: {response.status_code}"
            self.log_test("API Health Check", success, message)
            return success
        except Exception as e:
            self.log_test("API Health Check", False, f"Error: {str(e)}")
            return False

    def test_user_registration_and_login(self):
        """Test user registration and login"""
        try:
            # Try to register user (might already exist)
            response = requests.post(f"{API_URL}/auth/register", json=self.test_user_data)
            
            # Login regardless of registration result
            login_data = {
                "email": self.test_user_data["email"],
                "password": self.test_user_data["password"]
            }
            response = requests.post(f"{API_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                success = self.token is not None
                message = f"Token obtained: {'Yes' if self.token else 'No'}"
            else:
                success = False
                message = f"Login failed: {response.status_code}"
                
            self.log_test("User Login", success, message)
            return success
        except Exception as e:
            self.log_test("User Login", False, f"Error: {str(e)}")
            return False

    def get_headers(self):
        """Get headers with authentication"""
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        return headers

    def test_get_all_books(self):
        """Test retrieving all books to analyze series data"""
        try:
            response = requests.get(f"{API_URL}/books", headers=self.get_headers())
            success = response.status_code == 200
            
            if success:
                books = response.json()
                
                # Analyze books for series information
                series_books = []
                standalone_books = []
                
                for book in books:
                    if book.get('saga') and book.get('saga').strip():
                        series_books.append(book)
                    else:
                        standalone_books.append(book)
                
                # Group series books by saga
                series_groups = {}
                for book in series_books:
                    saga = book['saga']
                    if saga not in series_groups:
                        series_groups[saga] = []
                    series_groups[saga].append(book)
                
                message = f"Total: {len(books)} books, Series: {len(series_books)}, Standalone: {len(standalone_books)}, Series groups: {len(series_groups)}"
                
                # Store for later tests
                self.all_books = books
                self.series_books = series_books
                self.standalone_books = standalone_books
                self.series_groups = series_groups
                
                # Log series details
                print(f"   📚 Series found:")
                for saga, books_in_saga in series_groups.items():
                    print(f"     - {saga}: {len(books_in_saga)} books")
                    for book in books_in_saga:
                        print(f"       * {book.get('title', 'Unknown')} (Vol. {book.get('volume_number', '?')})")
                        
            else:
                message = f"Failed to get books: {response.status_code}"
                
            self.log_test("Get All Books", success, message)
            return success
        except Exception as e:
            self.log_test("Get All Books", False, f"Error: {str(e)}")
            return False

    def test_harry_potter_series_presence(self):
        """Test that Harry Potter series books are present"""
        try:
            if not hasattr(self, 'series_groups'):
                self.log_test("Harry Potter Series Check", False, "No series data available")
                return False
                
            harry_potter_books = self.series_groups.get('Harry Potter', [])
            success = len(harry_potter_books) > 0
            
            if success:
                message = f"Found {len(harry_potter_books)} Harry Potter books"
                print(f"   📚 Harry Potter books:")
                for book in harry_potter_books:
                    print(f"     - {book.get('title', 'Unknown')} (Vol. {book.get('volume_number', '?')}, Status: {book.get('status', 'unknown')})")
            else:
                message = "No Harry Potter books found"
                
            self.log_test("Harry Potter Series Check", success, message)
            return success
        except Exception as e:
            self.log_test("Harry Potter Series Check", False, f"Error: {str(e)}")
            return False

    def test_series_data_structure(self):
        """Test that series books have required fields for masking logic"""
        try:
            if not hasattr(self, 'series_books'):
                self.log_test("Series Data Structure", False, "No series data available")
                return False
                
            required_fields = ['saga', 'title', 'author', 'category', 'status']
            missing_fields = []
            
            for book in self.series_books:
                for field in required_fields:
                    if field not in book or not book[field]:
                        missing_fields.append(f"{book.get('title', 'Unknown')}: missing {field}")
            
            success = len(missing_fields) == 0
            
            if success:
                message = f"All {len(self.series_books)} series books have required fields"
            else:
                message = f"Missing fields found: {missing_fields[:5]}"  # Show first 5 issues
                
            self.log_test("Series Data Structure", success, message)
            return success
        except Exception as e:
            self.log_test("Series Data Structure", False, f"Error: {str(e)}")
            return False

    def test_standalone_books_structure(self):
        """Test that standalone books don't have saga field or have empty saga"""
        try:
            if not hasattr(self, 'standalone_books'):
                self.log_test("Standalone Books Structure", False, "No standalone data available")
                return False
                
            invalid_standalone = []
            
            for book in self.standalone_books:
                saga = book.get('saga', '')
                if saga and saga.strip():
                    invalid_standalone.append(f"{book.get('title', 'Unknown')}: has saga '{saga}'")
            
            success = len(invalid_standalone) == 0
            
            if success:
                message = f"All {len(self.standalone_books)} standalone books correctly have no saga"
            else:
                message = f"Invalid standalone books: {invalid_standalone[:3]}"
                
            self.log_test("Standalone Books Structure", success, message)
            return success
        except Exception as e:
            self.log_test("Standalone Books Structure", False, f"Error: {str(e)}")
            return False

    def test_book_filtering_by_category(self):
        """Test filtering books by category to ensure series masking works per category"""
        try:
            categories = ['roman', 'bd', 'manga']
            all_success = True
            
            for category in categories:
                response = requests.get(f"{API_URL}/books?category={category}", headers=self.get_headers())
                if response.status_code == 200:
                    books = response.json()
                    
                    # Count series vs standalone in this category
                    series_count = len([b for b in books if b.get('saga') and b.get('saga').strip()])
                    standalone_count = len([b for b in books if not b.get('saga') or not b.get('saga').strip()])
                    
                    print(f"   📚 {category.upper()}: {len(books)} total ({series_count} series, {standalone_count} standalone)")
                    
                    # Check for Harry Potter in roman category
                    if category == 'roman':
                        hp_books = [b for b in books if b.get('saga') == 'Harry Potter']
                        if hp_books:
                            print(f"     - Harry Potter books in roman: {len(hp_books)}")
                            for book in hp_books:
                                print(f"       * {book.get('title', 'Unknown')}")
                else:
                    all_success = False
                    print(f"   ❌ Failed to get {category} books: {response.status_code}")
            
            self.log_test("Book Filtering by Category", all_success, "Category filtering working")
            return all_success
        except Exception as e:
            self.log_test("Book Filtering by Category", False, f"Error: {str(e)}")
            return False

    def test_series_endpoint(self):
        """Test series-specific endpoints if available"""
        try:
            # Try to get series information
            response = requests.get(f"{API_URL}/series", headers=self.get_headers())
            
            if response.status_code == 200:
                series = response.json()
                message = f"Found {len(series)} series via /series endpoint"
                success = True
            elif response.status_code == 404:
                # Series endpoint might not exist, that's okay
                message = "Series endpoint not available (expected)"
                success = True
            else:
                message = f"Series endpoint error: {response.status_code}"
                success = False
                
            self.log_test("Series Endpoint", success, message)
            return success
        except Exception as e:
            self.log_test("Series Endpoint", False, f"Error: {str(e)}")
            return False

    def test_sagas_endpoint(self):
        """Test sagas endpoint for series information"""
        try:
            response = requests.get(f"{API_URL}/sagas", headers=self.get_headers())
            success = response.status_code == 200
            
            if success:
                sagas = response.json()
                message = f"Found {len(sagas)} sagas"
                
                # Look for Harry Potter saga
                hp_saga = next((s for s in sagas if s.get('name') == 'Harry Potter'), None)
                if hp_saga:
                    print(f"   📚 Harry Potter saga: {hp_saga.get('books_count', 0)} books")
                    
            else:
                message = f"Failed to get sagas: {response.status_code}"
                
            self.log_test("Sagas Endpoint", success, message)
            return success
        except Exception as e:
            self.log_test("Sagas Endpoint", False, f"Error: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all tests"""
        print("🔍 BOOKTIME - Test du masquage des livres de série (Backend)")
        print("=" * 60)
        
        # Core API tests
        if not self.test_health_check():
            print("❌ API not available, stopping tests")
            return False
            
        if not self.test_user_registration_and_login():
            print("❌ Authentication failed, stopping tests")
            return False
        
        # Data structure tests
        self.test_get_all_books()
        self.test_harry_potter_series_presence()
        self.test_series_data_structure()
        self.test_standalone_books_structure()
        self.test_book_filtering_by_category()
        
        # Series-specific endpoint tests
        self.test_series_endpoint()
        self.test_sagas_endpoint()
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 Tests completed: {self.tests_passed}/{self.tests_run} passed")
        
        if self.tests_passed == self.tests_run:
            print("✅ All backend tests passed - API ready for series masking")
        else:
            print("⚠️ Some backend tests failed - check API implementation")
            
        return self.tests_passed == self.tests_run

def main():
    tester = SeriesMaskingAPITest()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())