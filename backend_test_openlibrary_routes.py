import requests
import json
import unittest
import uuid
import time
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://9db1f1c3-95d8-4bb0-bed7-aa3f0a4ecd38.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class BooktimeOpenLibraryRoutesTest(unittest.TestCase):
    """Test suite for the Open Library routes in Booktime API"""

    def setUp(self):
        """Setup for each test"""
        # Register a test user
        self.user_data = {
            "first_name": "Test",
            "last_name": "User"
        }
        
        try:
            response = requests.post(f"{API_URL}/auth/register", json=self.user_data)
            if response.status_code == 200:
                self.token = response.json()["access_token"]
            else:
                # Try to login if registration fails (user might already exist)
                response = requests.post(f"{API_URL}/auth/login", json=self.user_data)
                if response.status_code == 200:
                    self.token = response.json()["access_token"]
                else:
                    self.token = None
        except Exception as e:
            print(f"Error during authentication: {e}")
            self.token = None
            
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        
        # Book IDs to be used/cleaned up during testing
        self.book_ids_to_delete = []

    def tearDown(self):
        """Clean up after each test"""
        # Delete any books created during testing
        for book_id in self.book_ids_to_delete:
            try:
                requests.delete(f"{API_URL}/books/{book_id}", headers=self.headers)
            except:
                pass

    def test_openlibrary_search(self):
        """Test searching books on Open Library"""
        # Test basic search
        query = "Harry Potter"
        response = requests.get(f"{API_URL}/openlibrary/search?q={query}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertIn("books", result)
        self.assertIn("total_found", result)
        self.assertGreater(len(result["books"]), 0)
        
        # Check book fields
        book = result["books"][0]
        required_fields = ["ol_key", "title", "author", "category", "cover_url"]
        for field in required_fields:
            self.assertIn(field, book)
            
        # Test with filters
        response = requests.get(
            f"{API_URL}/openlibrary/search?q={query}&limit=5&year_start=1997&year_end=2007", 
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertIn("filters_applied", result)
        self.assertIn("year_range", result["filters_applied"])
        
        # Test with language filter
        response = requests.get(
            f"{API_URL}/openlibrary/search?q={query}&language=fre", 
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        
        # Test with page filters
        response = requests.get(
            f"{API_URL}/openlibrary/search?q={query}&min_pages=200&max_pages=500", 
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        
        # Test with author filter
        response = requests.get(
            f"{API_URL}/openlibrary/search?q={query}&author_filter=Rowling", 
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        
        # Test with empty query
        response = requests.get(f"{API_URL}/openlibrary/search", headers=self.headers)
        self.assertNotEqual(response.status_code, 200)
        
        print("✅ GET /api/openlibrary/search endpoint working with all filters")

    def test_openlibrary_import(self):
        """Test importing a book from Open Library"""
        # First search for a book to import
        query = "Lord of the Rings"
        response = requests.get(f"{API_URL}/openlibrary/search?q={query}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        search_result = response.json()
        
        if not search_result["books"]:
            self.skipTest("No books found to import")
            
        # Import the first book
        book_to_import = search_result["books"][0]
        import_data = {
            "ol_key": book_to_import["ol_key"],
            "category": "roman"
        }
        
        response = requests.post(f"{API_URL}/openlibrary/import", json=import_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertIn("message", result)
        self.assertIn("book", result)
        imported_book = result["book"]
        
        # Add book ID to cleanup list
        if "id" in imported_book:
            self.book_ids_to_delete.append(imported_book["id"])
        
        # Verify imported book
        self.assertEqual(imported_book["title"], book_to_import["title"])
        self.assertEqual(imported_book["author"], book_to_import["author"])
        self.assertEqual(imported_book["category"], "roman")
        self.assertEqual(imported_book["status"], "to_read")
        
        # Test duplicate detection
        response = requests.post(f"{API_URL}/openlibrary/import", json=import_data, headers=self.headers)
        self.assertEqual(response.status_code, 409)  # Conflict
        
        # Test with invalid key
        import_data = {
            "ol_key": "/works/invalid-key",
            "category": "roman"
        }
        response = requests.post(f"{API_URL}/openlibrary/import", json=import_data, headers=self.headers)
        self.assertNotEqual(response.status_code, 200)
        
        # Test with missing key
        import_data = {
            "category": "roman"
        }
        response = requests.post(f"{API_URL}/openlibrary/import", json=import_data, headers=self.headers)
        self.assertEqual(response.status_code, 400)
        
        print("✅ POST /api/openlibrary/import endpoint working with all test cases")

    def test_book_enrichment(self):
        """Test enriching an existing book with Open Library data"""
        # Create a basic book
        book_data = {
            "title": "The Hobbit",
            "author": "J.R.R. Tolkien",
            "category": "roman"
        }
        
        response = requests.post(f"{API_URL}/books", json=book_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        book = response.json()
        book_id = book["id"]
        self.book_ids_to_delete.append(book_id)
        
        # Enrich the book
        response = requests.post(f"{API_URL}/books/{book_id}/enrich", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertIn("message", result)
        self.assertIn("book", result)
        self.assertIn("fields_updated", result)
        
        enriched_book = result["book"]
        
        # Verify that some fields were enriched
        self.assertEqual(enriched_book["title"], book_data["title"])
        self.assertEqual(enriched_book["author"], book_data["author"])
        
        # At least one of these fields should be enriched
        enriched_fields = ["cover_url", "isbn", "publication_year", "publisher", "total_pages"]
        self.assertTrue(any(field in result["fields_updated"] for field in enriched_fields))
        
        # Test with non-existent book
        fake_id = str(uuid.uuid4())
        response = requests.post(f"{API_URL}/books/{fake_id}/enrich", headers=self.headers)
        self.assertEqual(response.status_code, 404)
        
        print("✅ POST /api/books/{book_id}/enrich endpoint working")

    def test_openlibrary_search_advanced(self):
        """Test multi-criteria search on Open Library"""
        # Test with title and author
        params = {
            "title": "Harry Potter",
            "author": "Rowling"
        }
        
        response = requests.get(f"{API_URL}/openlibrary/search-advanced", params=params, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertIn("books", result)
        self.assertIn("total_found", result)
        self.assertIn("query_used", result)
        self.assertGreater(len(result["books"]), 0)
        
        # Test with subject
        params = {
            "subject": "fantasy",
            "year_start": 1990,
            "year_end": 2010
        }
        
        response = requests.get(f"{API_URL}/openlibrary/search-advanced", params=params, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        # Test with publisher
        params = {
            "publisher": "Scholastic"
        }
        
        response = requests.get(f"{API_URL}/openlibrary/search-advanced", params=params, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        # Test with ISBN
        params = {
            "isbn": "9780747532743"
        }
        
        response = requests.get(f"{API_URL}/openlibrary/search-advanced", params=params, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        # Test with missing criteria
        response = requests.get(f"{API_URL}/openlibrary/search-advanced", headers=self.headers)
        self.assertEqual(response.status_code, 400)
        
        print("✅ GET /api/openlibrary/search-advanced endpoint working with all criteria")

    def test_openlibrary_search_isbn(self):
        """Test searching by ISBN on Open Library"""
        # Test with a valid ISBN
        isbn = "9780747532743"  # Harry Potter ISBN
        
        response = requests.get(f"{API_URL}/openlibrary/search-isbn?isbn={isbn}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertIn("book", result)
        self.assertIn("found", result)
        
        if result["found"]:
            book = result["book"]
            required_fields = ["ol_key", "title", "category", "isbn"]
            for field in required_fields:
                self.assertIn(field, book)
        
        # Test with formatted ISBN (with dashes)
        isbn = "978-0-7475-3274-3"
        response = requests.get(f"{API_URL}/openlibrary/search-isbn?isbn={isbn}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        # Test with invalid ISBN
        isbn = "invalid-isbn"
        response = requests.get(f"{API_URL}/openlibrary/search-isbn?isbn={isbn}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertIn("found", result)
        self.assertFalse(result["found"])
        
        # Test with missing ISBN
        response = requests.get(f"{API_URL}/openlibrary/search-isbn", headers=self.headers)
        self.assertEqual(response.status_code, 422)  # Unprocessable Entity
        
        print("✅ GET /api/openlibrary/search-isbn endpoint working with all test cases")

    def test_openlibrary_search_author(self):
        """Test advanced author search on Open Library"""
        # Test with a known author
        author = "J.K. Rowling"
        
        response = requests.get(f"{API_URL}/openlibrary/search-author?author={author}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertIn("author", result)
        self.assertIn("series", result)
        self.assertIn("standalone_books", result)
        self.assertIn("total_found", result)
        
        # Check that we got some books
        total_books = len(result["standalone_books"])
        for series in result["series"]:
            total_books += len(series["books"])
            
        self.assertGreater(total_books, 0)
        
        # Test with missing author
        response = requests.get(f"{API_URL}/openlibrary/search-author", headers=self.headers)
        self.assertEqual(response.status_code, 422)  # Unprocessable Entity
        
        print("✅ GET /api/openlibrary/search-author endpoint working")

    def test_openlibrary_import_bulk(self):
        """Test importing multiple books from Open Library"""
        # First search for books to import
        query = "Tolkien"
        response = requests.get(f"{API_URL}/openlibrary/search?q={query}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        search_result = response.json()
        
        if len(search_result["books"]) < 2:
            self.skipTest("Not enough books found to test bulk import")
            
        # Import the first two books
        books_to_import = search_result["books"][:2]
        import_data = {
            "books": [
                {"ol_key": books_to_import[0]["ol_key"], "category": "roman"},
                {"ol_key": books_to_import[1]["ol_key"], "category": "roman"}
            ]
        }
        
        response = requests.post(f"{API_URL}/openlibrary/import-bulk", json=import_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertIn("summary", result)
        self.assertIn("results", result)
        
        # Check summary
        self.assertEqual(result["summary"]["total_requested"], 2)
        
        # Add imported book IDs to cleanup list
        for book in result["results"]["imported"]:
            if "id" in book:
                self.book_ids_to_delete.append(book["id"])
        
        # Test with one valid and one invalid key
        import_data = {
            "books": [
                {"ol_key": books_to_import[0]["ol_key"], "category": "roman"},
                {"ol_key": "/works/invalid-key", "category": "roman"}
            ]
        }
        
        response = requests.post(f"{API_URL}/openlibrary/import-bulk", json=import_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertEqual(result["summary"]["errors"], 1)
        
        # Test with empty book list
        import_data = {"books": []}
        response = requests.post(f"{API_URL}/openlibrary/import-bulk", json=import_data, headers=self.headers)
        self.assertEqual(response.status_code, 400)
        
        print("✅ POST /api/openlibrary/import-bulk endpoint working with all test cases")

    def test_openlibrary_recommendations(self):
        """Test getting personalized recommendations"""
        # Create some books to get recommendations based on
        book_data = [
            {
                "title": "Harry Potter and the Philosopher's Stone",
                "author": "J.K. Rowling",
                "category": "roman",
                "saga": "Harry Potter",
                "volume_number": 1
            },
            {
                "title": "Harry Potter and the Chamber of Secrets",
                "author": "J.K. Rowling",
                "category": "roman",
                "saga": "Harry Potter",
                "volume_number": 2
            },
            {
                "title": "The Hobbit",
                "author": "J.R.R. Tolkien",
                "category": "roman"
            }
        ]
        
        for data in book_data:
            response = requests.post(f"{API_URL}/books", json=data, headers=self.headers)
            if response.status_code == 200:
                book = response.json()
                self.book_ids_to_delete.append(book["id"])
        
        # Get recommendations
        response = requests.get(f"{API_URL}/openlibrary/recommendations", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertIn("recommendations", result)
        
        if "based_on" in result:
            self.assertIn("favorite_authors", result["based_on"])
            self.assertIn("favorite_category", result["based_on"])
            self.assertIn("collection_size", result["based_on"])
            
        # Check recommendation format if any
        if result["recommendations"]:
            recommendation = result["recommendations"][0]
            required_fields = ["ol_key", "title", "author", "category", "reason"]
            for field in required_fields:
                self.assertIn(field, recommendation)
        
        # Test with limit parameter
        limit = 5
        response = requests.get(f"{API_URL}/openlibrary/recommendations?limit={limit}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        if result["recommendations"]:
            self.assertLessEqual(len(result["recommendations"]), limit)
        
        print("✅ GET /api/openlibrary/recommendations endpoint working")

    def test_openlibrary_suggestions(self):
        """Test getting import suggestions"""
        # Create some books to get suggestions based on
        book_data = [
            {
                "title": "Harry Potter and the Philosopher's Stone",
                "author": "J.K. Rowling",
                "category": "roman",
                "saga": "Harry Potter",
                "volume_number": 1
            },
            {
                "title": "Harry Potter and the Chamber of Secrets",
                "author": "J.K. Rowling",
                "category": "roman",
                "saga": "Harry Potter",
                "volume_number": 2
            },
            {
                "title": "The Hobbit",
                "author": "J.R.R. Tolkien",
                "category": "roman"
            }
        ]
        
        for data in book_data:
            response = requests.post(f"{API_URL}/books", json=data, headers=self.headers)
            if response.status_code == 200:
                book = response.json()
                self.book_ids_to_delete.append(book["id"])
        
        # Get suggestions
        response = requests.get(f"{API_URL}/openlibrary/suggestions", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertIn("suggestions", result)
        
        if "types" in result:
            self.assertIn("saga_continuation", result["types"])
            self.assertIn("favorite_author", result["types"])
            
        # Check suggestion format if any
        if result["suggestions"]:
            suggestion = result["suggestions"][0]
            required_fields = ["type", "ol_key", "title", "author", "reason"]
            for field in required_fields:
                self.assertIn(field, suggestion)
        
        # Test with limit parameter
        limit = 5
        response = requests.get(f"{API_URL}/openlibrary/suggestions?limit={limit}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        if result["suggestions"]:
            self.assertLessEqual(len(result["suggestions"]), limit)
        
        print("✅ GET /api/openlibrary/suggestions endpoint working")

    def test_performance(self):
        """Test performance of the Open Library integration"""
        start_time = time.time()
        
        # Perform 5 consecutive searches
        queries = ["Harry Potter", "Lord of the Rings", "Naruto", "One Piece", "Astérix"]
        
        for query in queries:
            response = requests.get(f"{API_URL}/openlibrary/search?q={query}", headers=self.headers)
            self.assertEqual(response.status_code, 200)
            
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete in under 10 seconds
        self.assertLess(total_time, 10, f"Performance test took {total_time:.2f} seconds, which is too slow")
        
        print(f"✅ Performance test passed: 5 consecutive searches completed in {total_time:.2f} seconds")

if __name__ == "__main__":
    unittest.main(verbosity=2)