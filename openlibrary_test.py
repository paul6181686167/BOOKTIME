import requests
import unittest
import json
import sys
from datetime import datetime

class OpenLibraryIntegrationTest(unittest.TestCase):
    """Test suite for the Open Library integration in Booktime API"""

    def setUp(self):
        """Setup for each test"""
        # Get the backend URL from environment or use default
        import os
        self.backend_url = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
        self.api_url = f"{self.backend_url}/api"
        
        # Book IDs to be cleaned up after tests
        self.book_ids_to_delete = []
        
        print(f"🚀 Testing Open Library integration with backend URL: {self.backend_url}")

    def tearDown(self):
        """Clean up after each test"""
        # Delete any books created during testing
        for book_id in self.book_ids_to_delete:
            try:
                requests.delete(f"{self.api_url}/books/{book_id}")
                print(f"Cleaned up book with ID: {book_id}")
            except Exception as e:
                print(f"Error cleaning up book {book_id}: {str(e)}")

    def test_openlibrary_search_endpoint(self):
        """Test the Open Library search endpoint"""
        # Test with a valid query
        query = "dune"
        response = requests.get(f"{self.api_url}/openlibrary/search", params={"q": query, "limit": 5})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check response structure
        self.assertIn("total", data)
        self.assertIn("books", data)
        self.assertIsInstance(data["books"], list)
        
        # Should have results for "dune"
        self.assertGreater(data["total"], 0)
        self.assertGreater(len(data["books"]), 0)
        
        # Check book structure
        if data["books"]:
            book = data["books"][0]
            required_fields = ["title", "author", "ol_key", "category"]
            for field in required_fields:
                self.assertIn(field, book)
                
        print(f"✅ Open Library search endpoint working, found {data['total']} results for 'dune'")
        
        # Test with empty query (should fail)
        response = requests.get(f"{self.api_url}/openlibrary/search", params={"q": "", "limit": 5})
        self.assertEqual(response.status_code, 400)
        print("✅ Open Library search with empty query returns 400 as expected")
        
        # Test with nonexistent query
        query = "xyznonexistentbooktitle123456789"
        response = requests.get(f"{self.api_url}/openlibrary/search", params={"q": query, "limit": 5})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total"], 0)
        self.assertEqual(len(data["books"]), 0)
        print("✅ Open Library search with nonexistent query returns empty results as expected")

    def test_openlibrary_import_endpoint(self):
        """Test importing a book from Open Library"""
        # First search for a book to get its OL key
        query = "tolkien"
        response = requests.get(f"{self.api_url}/openlibrary/search", params={"q": query, "limit": 5})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        if not data["books"]:
            self.fail("No books found to test import")
            
        # Get the first book's OL key
        book_to_import = data["books"][0]
        ol_key = book_to_import["ol_key"]
        
        # Import the book
        response = requests.post(
            f"{self.api_url}/openlibrary/import", 
            json={"ol_key": ol_key, "category": "roman"}
        )
        self.assertEqual(response.status_code, 200)
        imported_book = response.json()
        
        # Add to cleanup list
        self.book_ids_to_delete.append(imported_book["_id"])
        
        # Verify the imported book
        self.assertEqual(imported_book["title"], book_to_import["title"])
        self.assertEqual(imported_book["author"], book_to_import["author"])
        self.assertEqual(imported_book["status"], "to_read")
        
        print(f"✅ Successfully imported book: {imported_book['title']} by {imported_book['author']}")
        
        # Try to import the same book again (should fail with 409)
        response = requests.post(
            f"{self.api_url}/openlibrary/import", 
            json={"ol_key": ol_key, "category": "roman"}
        )
        self.assertEqual(response.status_code, 409)
        print("✅ Importing duplicate book returns 409 as expected")
        
        # Try to import with invalid OL key
        response = requests.post(
            f"{self.api_url}/openlibrary/import", 
            json={"ol_key": "/works/invalid_key", "category": "roman"}
        )
        self.assertEqual(response.status_code, 404)
        print("✅ Importing with invalid OL key returns 404 as expected")

    def test_openlibrary_category_mapping(self):
        """Test that Open Library categories are correctly mapped"""
        # Search for books in different categories
        categories_to_test = {
            "manga": "manga",
            "graphic novel": "bd",
            "comic": "bd",
            "fiction": "roman"
        }
        
        for search_term, expected_category in categories_to_test.items():
            response = requests.get(
                f"{self.api_url}/openlibrary/search", 
                params={"q": search_term, "limit": 5}
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            if data["books"]:
                # Check if at least one book has the expected category
                categories = [book["category"] for book in data["books"]]
                self.assertIn(expected_category, categories, 
                             f"Expected at least one book with category '{expected_category}' for search '{search_term}'")
                print(f"✅ Category mapping works for '{search_term}' -> '{expected_category}'")

    def test_openlibrary_data_enrichment(self):
        """Test that imported books have enriched data"""
        # Search for a book with rich metadata
        query = "harry potter"
        response = requests.get(f"{self.api_url}/openlibrary/search", params={"q": query, "limit": 5})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        if not data["books"]:
            self.fail("No books found to test data enrichment")
            
        # Find a book with cover and other metadata
        book_to_import = None
        for book in data["books"]:
            if book.get("cover_url") and book.get("total_pages") and book.get("publication_year"):
                book_to_import = book
                break
                
        if not book_to_import:
            book_to_import = data["books"][0]  # Fallback to first book
            
        # Import the book
        ol_key = book_to_import["ol_key"]
        response = requests.post(
            f"{self.api_url}/openlibrary/import", 
            json={"ol_key": ol_key, "category": "roman"}
        )
        self.assertEqual(response.status_code, 200)
        imported_book = response.json()
        
        # Add to cleanup list
        self.book_ids_to_delete.append(imported_book["_id"])
        
        # Check for enriched data
        enriched_fields = [
            "cover_url", "total_pages", "isbn", "publication_year", 
            "publisher", "genre", "original_language"
        ]
        
        enriched_count = sum(1 for field in enriched_fields if imported_book.get(field))
        self.assertGreater(enriched_count, 2, "Imported book should have at least 3 enriched fields")
        
        print(f"✅ Imported book has {enriched_count} enriched fields")
        for field in enriched_fields:
            if imported_book.get(field):
                print(f"   - {field}: {imported_book[field]}")

if __name__ == "__main__":
    unittest.main(verbosity=2)