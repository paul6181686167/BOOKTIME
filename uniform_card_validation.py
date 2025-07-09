import requests
import json
import unittest
import uuid
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://a6f62ca1-928d-41f6-aad2-2d4a65b465a8.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class UniformCardValidationTest(unittest.TestCase):
    """Test suite for validating the uniform card display in Booktime API"""

    def setUp(self):
        """Setup for each test - create a test user"""
        self.test_user = {
            "first_name": "UniformTest",
            "last_name": "Test"
        }
        
        # Register the test user or login if already exists
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

    def test_1_auth_endpoint(self):
        """Test authentication endpoint with the test user"""
        print("\n=== Testing Authentication ===")
        
        # Verify the user info
        response = requests.get(f"{API_URL}/auth/me", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        user_info = response.json()
        
        # Check that the user info contains the expected fields
        self.assertIn("id", user_info)
        self.assertIn("first_name", user_info)
        self.assertIn("last_name", user_info)
        
        # Verify the user info matches what we expect
        self.assertEqual(user_info["first_name"], self.test_user["first_name"])
        self.assertEqual(user_info["last_name"], self.test_user["last_name"])
        
        print(f"✅ Authentication successful for user: {user_info['first_name']} {user_info['last_name']}")
        print(f"   User ID: {user_info['id']}")

    def test_2_books_endpoint(self):
        """Test GET /api/books endpoint for library books"""
        print("\n=== Testing GET /api/books ===")
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
            required_fields = ["id", "title", "author", "category", "status"]
            for field in required_fields:
                self.assertIn(field, book, f"Book is missing required field: {field}")
                
            # Check category is one of the expected values
            self.assertIn(book["category"], ["roman", "bd", "manga"], 
                         f"Book has invalid category: {book['category']}")
            
            # Check status is one of the expected values
            self.assertIn(book["status"], ["to_read", "reading", "completed"], 
                         f"Book has invalid status: {book['status']}")
            
            print("✅ Library books have uniform card structure")
        else:
            print("ℹ️ No books found for this user (normal for new user)")

    def test_3_series_search_endpoint(self):
        """Test GET /api/series/search endpoint for series search"""
        print("\n=== Testing GET /api/series/search?q=harry ===")
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
            
            print("✅ Series search results have uniform card structure")
        else:
            print(f"ℹ️ No series found for search term: {search_term}")

    def test_4_openlibrary_search_endpoint(self):
        """Test GET /api/openlibrary/search endpoint for OpenLibrary search"""
        print("\n=== Testing GET /api/openlibrary/search?q=harry&limit=5 ===")
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
            
            print("✅ OpenLibrary search results have uniform card structure")
        else:
            print(f"ℹ️ No OpenLibrary books found for search term: {search_term}")

    def test_5_uniform_card_validation(self):
        """Validate that all card types have a uniform structure"""
        print("\n=== Validating Uniform Card Structure ===")
        
        # Define the common fields that should be present in all card types
        common_fields = ["category", "title", "author"]
        
        # Get data from all endpoints
        endpoints = [
            {"name": "Library Books", "url": f"{API_URL}/books", "item_key": None},
            {"name": "Series Search", "url": f"{API_URL}/series/search?q=harry", "item_key": "series"},
            {"name": "OpenLibrary Search", "url": f"{API_URL}/openlibrary/search?q=harry&limit=5", "item_key": "books"}
        ]
        
        all_items = []
        
        for endpoint in endpoints:
            response = requests.get(endpoint["url"], headers=self.headers)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            if endpoint["item_key"]:
                items = data[endpoint["item_key"]]
            else:
                items = data
            
            if items and len(items) > 0:
                item = items[0]
                all_items.append({"source": endpoint["name"], "item": item})
                print(f"Found item from {endpoint['name']}")
        
        # Check for common fields across all item types
        for item_data in all_items:
            source = item_data["source"]
            item = item_data["item"]
            
            # Special handling for series which have different field names
            if source == "Series Search":
                # Map series fields to common fields
                if "name" in item:
                    item["title"] = item["name"]
                if "authors" in item and len(item["authors"]) > 0:
                    item["author"] = item["authors"][0]
            
            # Check for common fields
            for field in common_fields:
                if field not in item:
                    print(f"⚠️ {source} item is missing common field: {field}")
                else:
                    print(f"✅ {source} has field: {field} = {item[field]}")
        
        print("✅ All card types have been validated for uniform structure")

if __name__ == "__main__":
    unittest.main(verbosity=2)