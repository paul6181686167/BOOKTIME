import requests
import json
import unittest
import uuid
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://ec99213f-6641-4612-9dca-73f723ce0ab7.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class UniformCardTest(unittest.TestCase):
    """Test suite for the uniform card display in Booktime API"""

    def setUp(self):
        """Setup for each test - create a test user"""
        self.test_user = {
            "first_name": "UniformTest",
            "last_name": "Test"
        }
        
        # Register the test user
        response = requests.post(f"{API_URL}/auth/register", json=self.test_user)
        if response.status_code == 200:
            self.auth_data = response.json()
            self.token = self.auth_data["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
            print(f"✅ Created test user: {self.test_user['first_name']} {self.test_user['last_name']}")
        else:
            # Try to login if registration fails (user might already exist)
            response = requests.post(f"{API_URL}/auth/login", json=self.test_user)
            if response.status_code == 200:
                self.auth_data = response.json()
                self.token = self.auth_data["access_token"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
                print(f"✅ Logged in as existing user: {self.test_user['first_name']} {self.test_user['last_name']}")
            else:
                self.fail(f"Failed to create or login as test user: {response.text}")

    def test_books_endpoint(self):
        """Test GET /api/books endpoint for uniform card display"""
        response = requests.get(f"{API_URL}/books", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        books = response.json()
        
        print(f"GET /api/books returned {len(books)} books")
        
        # Check if the response is a list
        self.assertIsInstance(books, list)
        
        # If there are books, check the structure of the first book
        if books:
            book = books[0]
            print(f"Sample book: {json.dumps(book, indent=2)[:200]}...")
            
            # Check required fields for uniform card display
            required_fields = ["id", "title", "author", "category", "status", "cover_url"]
            for field in required_fields:
                self.assertIn(field, book, f"Book is missing required field: {field}")
                
            # Check category is one of the expected values
            self.assertIn(book["category"], ["roman", "bd", "manga"], 
                         f"Book has invalid category: {book['category']}")
            
            # Check status is one of the expected values
            self.assertIn(book["status"], ["to_read", "reading", "completed"], 
                         f"Book has invalid status: {book['status']}")
            
            print("✅ Book structure is valid for uniform card display")
        else:
            print("ℹ️ No books found for this user (normal for new user)")

    def test_series_search_endpoint(self):
        """Test GET /api/series/search endpoint for uniform card display"""
        search_term = "harry"
        response = requests.get(f"{API_URL}/series/search?q={search_term}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check the structure of the response
        self.assertIn("series", data)
        self.assertIn("total", data)
        self.assertIn("search_term", data)
        
        series_list = data["series"]
        print(f"GET /api/series/search?q={search_term} returned {len(series_list)} series")
        
        # Check if there are any series found
        if series_list:
            series = series_list[0]
            print(f"Sample series: {json.dumps(series, indent=2)[:200]}...")
            
            # Check required fields for uniform card display
            required_fields = ["name", "category", "authors", "isSeriesCard"]
            for field in required_fields:
                self.assertIn(field, series, f"Series is missing required field: {field}")
                
            # Check category is one of the expected values
            self.assertIn(series["category"], ["roman", "bd", "manga"], 
                         f"Series has invalid category: {series['category']}")
            
            # Check search-specific fields
            self.assertIn("search_score", series)
            self.assertIn("match_reasons", series)
            
            print("✅ Series search structure is valid for uniform card display")
        else:
            print(f"ℹ️ No series found for search term: {search_term}")

    def test_openlibrary_search_endpoint(self):
        """Test GET /api/openlibrary/search endpoint for uniform card display"""
        search_term = "harry"
        limit = 5
        response = requests.get(f"{API_URL}/openlibrary/search?q={search_term}&limit={limit}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check the structure of the response
        self.assertIn("books", data)
        self.assertIn("total_found", data)
        
        books = data["books"]
        print(f"GET /api/openlibrary/search?q={search_term}&limit={limit} returned {len(books)} books out of {data['total_found']} total")
        
        # Check if there are any books found
        if books:
            book = books[0]
            print(f"Sample OpenLibrary book: {json.dumps(book, indent=2)[:200]}...")
            
            # Check required fields for uniform card display
            required_fields = ["title", "author", "category", "cover_url", "ol_key"]
            for field in required_fields:
                self.assertIn(field, book, f"OpenLibrary book is missing required field: {field}")
                
            # Check category is one of the expected values
            self.assertIn(book["category"], ["roman", "bd", "manga"], 
                         f"OpenLibrary book has invalid category: {book['category']}")
            
            print("✅ OpenLibrary search structure is valid for uniform card display")
        else:
            print(f"ℹ️ No OpenLibrary books found for search term: {search_term}")

if __name__ == "__main__":
    unittest.main(verbosity=2)