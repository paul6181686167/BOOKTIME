import requests
import unittest
import json
import uuid
from datetime import datetime

class OpenLibraryEndpointsTest(unittest.TestCase):
    """Comprehensive test suite for the Open Library endpoints in Booktime API"""

    def setUp(self):
        """Setup for each test"""
        # Get the backend URL from environment or use default
        import os
        self.backend_url = os.environ.get("REACT_APP_BACKEND_URL", "http://localhost:8001")
        self.api_url = f"{self.backend_url}/api"
        
        # Book IDs to be cleaned up after tests
        self.book_ids_to_delete = []
        
        # Test book for enrichment
        self.test_book_data = {
            "title": "Harry Potter and the Philosopher's Stone",
            "author": "J.K. Rowling",
            "category": "roman",
            "description": "The first book in the Harry Potter series"
        }
        
        print(f"🚀 Testing Open Library endpoints with backend URL: {self.backend_url}")

    def tearDown(self):
        """Clean up after each test"""
        # Delete any books created during testing
        for book_id in self.book_ids_to_delete:
            try:
                requests.delete(f"{self.api_url}/books/{book_id}")
                print(f"Cleaned up book with ID: {book_id}")
            except Exception as e:
                print(f"Error cleaning up book {book_id}: {str(e)}")

    def test_01_search_with_different_queries(self):
        """Test searching for books with different queries"""
        queries = ["Harry Potter", "Astérix", "One Piece", "Le Seigneur des Anneaux"]
        
        for query in queries:
            response = requests.get(f"{self.api_url}/openlibrary/search", params={"q": query})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check response structure
            self.assertIn("total", data)
            self.assertIn("books", data)
            
            # Should have results
            self.assertGreater(data["total"], 0, f"Should find results for '{query}'")
            self.assertGreater(len(data["books"]), 0, f"Should return books for '{query}'")
            
            # Check book structure and mapping
            for book in data["books"]:
                required_fields = ["title", "author", "category", "ol_key", "description"]
                for field in required_fields:
                    self.assertIn(field, book)
                
                # Category should be one of the valid categories
                self.assertIn(book["category"], ["roman", "bd", "manga"])
                
                # Check for optional fields that should be mapped
                optional_fields = ["cover_url", "total_pages", "isbn", "publication_year", 
                                  "publisher", "genre", "original_language"]
                mapped_fields = [field for field in optional_fields if book.get(field)]
                
                # Print the first book's details for verification
                if data["books"].index(book) == 0:
                    print(f"\n✅ Search for '{query}' returned {len(data['books'])} books")
                    print(f"   First result: {book['title']} by {book['author']}")
                    print(f"   Category: {book['category']}")
                    print(f"   Mapped fields: {', '.join(mapped_fields)}")
    
    def test_02_search_with_different_limits(self):
        """Test searching with different limit parameters"""
        limits = [5, 10, 20]
        query = "Harry Potter"
        
        for limit in limits:
            response = requests.get(f"{self.api_url}/openlibrary/search", params={"q": query, "limit": limit})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Check that we got at most 'limit' results
            self.assertLessEqual(len(data["books"]), limit, f"Should return at most {limit} books")
            
            print(f"✅ Search with limit={limit} returned {len(data['books'])} books")
    
    def test_03_search_error_cases(self):
        """Test error cases for the search endpoint"""
        # Empty query
        response = requests.get(f"{self.api_url}/openlibrary/search", params={"q": ""})
        self.assertIn(response.status_code, [400, 422])
        print("✅ Empty query returns error status code as expected")
        
        # Missing query parameter
        response = requests.get(f"{self.api_url}/openlibrary/search")
        self.assertEqual(response.status_code, 400)
        print("✅ Missing query parameter returns 400 as expected")
        
        # Invalid limit (negative)
        response = requests.get(f"{self.api_url}/openlibrary/search", params={"q": "Harry Potter", "limit": -1})
        # This might return 200 with default limit or 422 for validation error
        print(f"✅ Invalid limit parameter handled (status code: {response.status_code})")
    
    def test_04_import_book_with_different_categories(self):
        """Test importing a book with different categories"""
        # First search for a book to get its Open Library key
        query = "Harry Potter"
        response = requests.get(f"{self.api_url}/openlibrary/search", params={"q": query})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        if not data["books"]:
            self.fail("No books found to test import")
        
        # Get the first book's Open Library key
        ol_key = data["books"][0]["ol_key"]
        
        # Test importing with different categories
        categories = ["roman", "bd", "manga"]
        
        for category in categories:
            # Import the book
            import_data = {
                "ol_key": ol_key,
                "category": category
            }
            
            response = requests.post(f"{self.api_url}/openlibrary/import", json=import_data)
            
            # The first import should succeed, but subsequent ones might fail due to duplicate detection
            if response.status_code == 200:
                book = response.json()
                self.book_ids_to_delete.append(book["_id"])
                
                # Check that the book was imported with the correct data
                self.assertEqual(book["category"], category)
                self.assertIsNotNone(book["title"])
                self.assertIsNotNone(book["author"])
                
                print(f"✅ Successfully imported book with category '{category}'")
                print(f"   Title: {book['title']}")
                print(f"   Author: {book['author']}")
                print(f"   ISBN: {book.get('isbn', 'N/A')}")
                print(f"   Cover URL: {'Present' if book.get('cover_url') else 'Not present'}")
                
            elif response.status_code == 409:
                print(f"✅ Duplicate detection works for category '{category}'")
            else:
                self.fail(f"Import failed with status code {response.status_code}")
    
    def test_05_import_duplicate_detection(self):
        """Test duplicate detection when importing books"""
        # First search for a book to get its Open Library key
        query = "Dune"  # Using a different book to avoid conflicts
        response = requests.get(f"{self.api_url}/openlibrary/search", params={"q": query})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        if not data["books"]:
            self.fail("No books found to test duplicate detection")
        
        # Get the first book's Open Library key
        ol_key = data["books"][0]["ol_key"]
        
        # Import the book
        import_data = {
            "ol_key": ol_key,
            "category": "roman"
        }
        
        response = requests.post(f"{self.api_url}/openlibrary/import", json=import_data)
        
        if response.status_code == 200:
            book = response.json()
            self.book_ids_to_delete.append(book["_id"])
            
            print(f"✅ Successfully imported book: {book['title']} by {book['author']}")
            
            # Try to import the same book again
            response = requests.post(f"{self.api_url}/openlibrary/import", json=import_data)
            self.assertEqual(response.status_code, 409)
            print("✅ Duplicate detection works correctly")
            
            # Check the error message
            error_data = response.json()
            self.assertIn("detail", error_data)
            self.assertIn("existe déjà", error_data["detail"])
        elif response.status_code == 409:
            print("✅ Book already exists, duplicate detection confirmed")
        else:
            self.fail(f"Import failed with status code {response.status_code}")
    
    def test_06_import_invalid_key(self):
        """Test importing a book with an invalid Open Library key"""
        import_data = {
            "ol_key": "/works/invalid_key_that_does_not_exist",
            "category": "roman"
        }
        
        response = requests.post(f"{self.api_url}/openlibrary/import", json=import_data)
        self.assertEqual(response.status_code, 404)
        print("✅ Import with invalid key returns 404 as expected")
    
    def test_07_enrich_book(self):
        """Test enriching an existing book with Open Library data"""
        # Create a basic book to enrich
        response = requests.post(f"{self.api_url}/books", json=self.test_book_data)
        self.assertEqual(response.status_code, 200)
        book = response.json()
        book_id = book["_id"]
        self.book_ids_to_delete.append(book_id)
        
        # Verify the book was created with minimal data
        self.assertIsNone(book.get("isbn"))
        self.assertIsNone(book.get("cover_url"))
        self.assertIsNone(book.get("total_pages"))
        
        print(f"✅ Created basic book: {book['title']} by {book['author']}")
        
        # Enrich the book
        response = requests.post(f"{self.api_url}/books/{book_id}/enrich")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that the response has the expected structure
        self.assertIn("message", data)
        self.assertIn("enriched_fields", data)
        self.assertIn("book", data)
        
        # Check that some fields were enriched
        enriched_book = data["book"]
        enriched_fields = data["enriched_fields"]
        
        # At least some fields should be enriched
        self.assertGreater(len(enriched_fields), 0)
        
        print(f"✅ Book enriched successfully with {len(enriched_fields)} new fields")
        print(f"   Enriched fields: {', '.join(enriched_fields)}")
        
        # Print the enriched data for verification
        for field in enriched_fields:
            print(f"   - {field}: {enriched_book[field]}")
    
    def test_08_enrich_nonexistent_book(self):
        """Test enriching a book that doesn't exist"""
        fake_id = str(uuid.uuid4())
        response = requests.post(f"{self.api_url}/books/{fake_id}/enrich")
        self.assertEqual(response.status_code, 404)
        print("✅ Enriching non-existent book returns 404 as expected")
    
    def test_09_enrich_book_no_match(self):
        """Test enriching a book with no Open Library match"""
        # Create a book with a title that won't match anything on Open Library
        nonsense_book = {
            "title": "XYZ123 This Book Does Not Exist ABCDEF",
            "author": "Nonexistent Author",
            "category": "roman"
        }
        
        response = requests.post(f"{self.api_url}/books", json=nonsense_book)
        self.assertEqual(response.status_code, 200)
        book = response.json()
        book_id = book["_id"]
        self.book_ids_to_delete.append(book_id)
        
        # Try to enrich the book
        response = requests.post(f"{self.api_url}/books/{book_id}/enrich")
        self.assertEqual(response.status_code, 404)
        print("✅ Enriching book with no Open Library match returns 404 as expected")
    
    def test_10_category_detection(self):
        """Test automatic category detection based on subjects"""
        # Search for books that should be detected as different categories
        category_queries = {
            "manga": ["Naruto", "One Piece", "Dragon Ball"],
            "bd": ["Astérix", "Tintin", "Lucky Luke"],
            "roman": ["Harry Potter", "Le Seigneur des Anneaux", "1984"]
        }
        
        for expected_category, queries in category_queries.items():
            for query in queries:
                response = requests.get(f"{self.api_url}/openlibrary/search", params={"q": query})
                self.assertEqual(response.status_code, 200)
                data = response.json()
                
                if data["books"]:
                    # Check if at least one book was correctly categorized
                    category_detected = False
                    for book in data["books"]:
                        if book["category"] == expected_category:
                            category_detected = True
                            print(f"✅ Category detection works for '{query}' (detected as '{expected_category}')")
                            print(f"   Title: {book['title']}")
                            print(f"   Subjects: {book.get('genre', [])}")
                            break
                    
                    if not category_detected:
                        print(f"⚠️ No books detected as '{expected_category}' for query '{query}'")
                else:
                    print(f"⚠️ No books found for '{query}', skipping category detection test")
    
    def test_11_cover_image_handling(self):
        """Test that cover images are correctly handled"""
        # Search for books that typically have covers
        query = "Harry Potter"
        response = requests.get(f"{self.api_url}/openlibrary/search", params={"q": query})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        if not data["books"]:
            self.fail("No books found to test cover images")
        
        # Check if at least one book has a cover URL
        cover_found = False
        for book in data["books"]:
            if book.get("cover_url"):
                cover_found = True
                
                # Verify the cover URL format
                self.assertTrue(book["cover_url"].startswith("https://covers.openlibrary.org/b/id/"))
                self.assertTrue(book["cover_url"].endswith("-L.jpg"))
                
                print(f"✅ Cover URL found: {book['cover_url']}")
                print(f"   For book: {book['title']} by {book['author']}")
                break
        
        self.assertTrue(cover_found, "Should find at least one book with a cover")
    
    def test_12_isbn_validation(self):
        """Test that ISBNs are correctly handled and validated"""
        # Search for books that typically have ISBNs
        query = "Harry Potter"
        response = requests.get(f"{self.api_url}/openlibrary/search", params={"q": query})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        if not data["books"]:
            self.fail("No books found to test ISBNs")
        
        # Check if at least one book has an ISBN
        isbn_found = False
        for book in data["books"]:
            if book.get("isbn"):
                isbn_found = True
                
                # Verify the ISBN format (should be a string)
                self.assertIsInstance(book["isbn"], str)
                
                print(f"✅ ISBN found: {book['isbn']}")
                print(f"   For book: {book['title']} by {book['author']}")
                break
        
        self.assertTrue(isbn_found, "Should find at least one book with an ISBN")
    
    def test_13_performance(self):
        """Test performance with multiple searches"""
        # Perform multiple searches in sequence
        queries = ["Harry Potter", "Astérix", "One Piece", "Le Seigneur des Anneaux", "Naruto"]
        
        start_time = datetime.now()
        
        for query in queries:
            response = requests.get(f"{self.api_url}/openlibrary/search", params={"q": query})
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertGreater(len(data["books"]), 0, f"Should find results for '{query}'")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # All searches combined should take less than 10 seconds
        self.assertLess(duration, 10, f"Multiple searches should complete in less than 10 seconds (took {duration:.2f}s)")
        
        print(f"✅ Performance test passed: {len(queries)} searches completed in {duration:.2f} seconds")


if __name__ == "__main__":
    unittest.main(verbosity=2)