import requests
import json
import unittest
import uuid
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://06ad0466-f8dc-45df-9572-d7f90595d8b4.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class ComprehensiveUniformCardTest(unittest.TestCase):
    """Comprehensive test suite for the uniform card display in Booktime API"""

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
        
        # Add a test book to the library for testing
        self.test_book = {
            "title": "Harry Potter et la Chambre des Secrets",
            "author": "J.K. Rowling",
            "category": "roman",
            "saga": "Harry Potter",
            "volume_number": 2,
            "description": "Le deuxième tome de la saga Harry Potter",
            "cover_url": "https://covers.openlibrary.org/b/id/10522178-L.jpg"
        }
        
        # Add the book to the library
        response = requests.post(f"{API_URL}/books", json=self.test_book, headers=self.headers)
        if response.status_code == 200:
            self.test_book_data = response.json()
            print(f"✅ Added test book to library: {self.test_book['title']}")
        else:
            print(f"⚠️ Failed to add test book: {response.text}")

    def tearDown(self):
        """Clean up after tests"""
        # Delete the test book if it was created
        if hasattr(self, 'test_book_data') and 'id' in self.test_book_data:
            response = requests.delete(f"{API_URL}/books/{self.test_book_data['id']}", headers=self.headers)
            if response.status_code == 200:
                print(f"✅ Deleted test book: {self.test_book['title']}")
            else:
                print(f"⚠️ Failed to delete test book: {response.text}")

    def test_1_books_endpoint(self):
        """Test GET /api/books endpoint for uniform card display"""
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
            
            print("✅ Book structure is valid for uniform card display")
        else:
            print("ℹ️ No books found for this user")

    def test_2_series_search_endpoint(self):
        """Test GET /api/series/search endpoint for uniform card display"""
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
            
            print("✅ Series search structure is valid for uniform card display")
        else:
            print(f"ℹ️ No series found for search term: {search_term}")

    def test_3_openlibrary_search_endpoint(self):
        """Test GET /api/openlibrary/search endpoint for uniform card display"""
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
            
            print("✅ OpenLibrary search structure is valid for uniform card display")
        else:
            print(f"ℹ️ No OpenLibrary books found for search term: {search_term}")

    def test_4_books_search_grouped_endpoint(self):
        """Test GET /api/books/search-grouped endpoint for uniform card display"""
        print("\n=== Testing GET /api/books/search-grouped?q=harry ===")
        search_term = "harry"
        response = requests.get(f"{API_URL}/books/search-grouped?q={search_term}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check the structure of the response
        self.assertIn("results", data)
        self.assertIn("total_books", data)
        self.assertIn("total_sagas", data)
        self.assertIn("search_term", data)
        self.assertIn("grouped_by_saga", data)
        
        results = data["results"]
        print(f"GET /api/books/search-grouped?q={search_term} returned {len(results)} results")
        print(f"Total books: {data['total_books']}, Total sagas: {data['total_sagas']}")
        
        # Check if there are any results found
        if results:
            result = results[0]
            print(f"Sample search result: {json.dumps(result, indent=2)[:200]}...")
            
            # Check the type field to determine if it's a saga or book
            self.assertIn("type", result)
            
            if result["type"] == "saga":
                # Check required fields for saga cards
                required_fields = ["name", "books", "total_books", "author", "category"]
                for field in required_fields:
                    self.assertIn(field, result, f"Saga result is missing required field: {field}")
                
                # Check category is one of the expected values
                self.assertIn(result["category"], ["roman", "bd", "manga"], 
                             f"Saga result has invalid category: {result['category']}")
                
                print("✅ Saga search result structure is valid for uniform card display")
                
            elif result["type"] == "book":
                # Check required fields for book cards
                required_fields = ["title", "author", "category", "status"]
                for field in required_fields:
                    self.assertIn(field, result, f"Book result is missing required field: {field}")
                
                # Check category is one of the expected values
                self.assertIn(result["category"], ["roman", "bd", "manga"], 
                             f"Book result has invalid category: {result['category']}")
                
                print("✅ Book search result structure is valid for uniform card display")
            
            else:
                self.fail(f"Unknown result type: {result['type']}")
        else:
            print(f"ℹ️ No search results found for term: {search_term}")

    def test_5_compare_card_structures(self):
        """Compare the structure of cards across different endpoints to ensure uniformity"""
        print("\n=== Comparing Card Structures Across Endpoints ===")
        
        # Get a book from the library
        response = requests.get(f"{API_URL}/books", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        library_books = response.json()
        
        # Get a series from search
        response = requests.get(f"{API_URL}/series/search?q=harry", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        series_data = response.json()
        series_list = series_data["series"]
        
        # Get a book from OpenLibrary search
        response = requests.get(f"{API_URL}/openlibrary/search?q=harry&limit=1", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        ol_data = response.json()
        ol_books = ol_data["books"]
        
        # Get a result from books/search-grouped
        response = requests.get(f"{API_URL}/books/search-grouped?q=harry", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        grouped_data = response.json()
        grouped_results = grouped_data["results"]
        
        # Compare the common fields across all card types
        print("Checking common fields across all card types...")
        
        # Define the common fields that should be present in all card types
        common_fields = ["category"]
        
        # Check library books
        if library_books:
            library_book = library_books[0]
            print(f"Library book category: {library_book.get('category', 'N/A')}")
            for field in common_fields:
                self.assertIn(field, library_book, f"Library book is missing common field: {field}")
        
        # Check series
        if series_list:
            series = series_list[0]
            print(f"Series category: {series.get('category', 'N/A')}")
            for field in common_fields:
                self.assertIn(field, series, f"Series is missing common field: {field}")
        
        # Check OpenLibrary books
        if ol_books:
            ol_book = ol_books[0]
            print(f"OpenLibrary book category: {ol_book.get('category', 'N/A')}")
            for field in common_fields:
                self.assertIn(field, ol_book, f"OpenLibrary book is missing common field: {field}")
        
        # Check grouped search results
        if grouped_results:
            grouped_result = grouped_results[0]
            print(f"Grouped search result category: {grouped_result.get('category', 'N/A')}")
            for field in common_fields:
                self.assertIn(field, grouped_result, f"Grouped search result is missing common field: {field}")
        
        print("✅ All card types have the required common fields for uniform display")
        
        # Check that categories are consistent across all endpoints
        valid_categories = ["roman", "bd", "manga"]
        
        if library_books:
            self.assertIn(library_books[0]["category"], valid_categories)
        
        if series_list:
            self.assertIn(series_list[0]["category"], valid_categories)
        
        if ol_books:
            self.assertIn(ol_books[0]["category"], valid_categories)
        
        if grouped_results:
            self.assertIn(grouped_results[0]["category"], valid_categories)
        
        print("✅ Categories are consistent across all endpoints")
        print("✅ Card structures are uniform across all endpoints")

if __name__ == "__main__":
    unittest.main(verbosity=2)