#!/usr/bin/env python3
"""
Comprehensive test script for the BookTime API
This script tests all backend API endpoints and functionality after FastAPI/Starlette compatibility fix
"""

import requests
import json
import unittest
import uuid
import time
from datetime import datetime
import sys

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://8c8b9cc8-8549-4c1c-a355-e2de2cd1dbe0.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class BooktimeAPITest(unittest.TestCase):
    """Test suite for the Booktime API"""

    def setUp(self):
        """Setup for each test"""
        # Register a test user
        timestamp = int(time.time())
        self.user_data = {
            "first_name": f"Test{timestamp}",
            "last_name": f"User{timestamp}"
        }
        
        try:
            response = requests.post(f"{API_URL}/auth/register", json=self.user_data)
            if response.status_code == 200:
                self.token = response.json()["access_token"]
                self.user = response.json()["user"]
                print(f"✅ Registered test user: {self.user['first_name']} {self.user['last_name']}")
            else:
                # Try to login if registration fails (user might already exist)
                response = requests.post(f"{API_URL}/auth/login", json=self.user_data)
                if response.status_code == 200:
                    self.token = response.json()["access_token"]
                    self.user = response.json()["user"]
                    print(f"✅ Logged in as test user: {self.user['first_name']} {self.user['last_name']}")
                else:
                    print(f"❌ Failed to authenticate: {response.status_code} - {response.text}")
                    self.token = None
                    self.user = None
        except Exception as e:
            print(f"❌ Error during authentication: {e}")
            self.token = None
            self.user = None
            
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        
        self.test_book_data = {
            "title": "Le Petit Prince",
            "author": "Antoine de Saint-Exupéry",
            "category": "roman",
            "description": "Un conte philosophique sous forme d'un récit pour enfants",
            "cover_url": "https://example.com/petit-prince.jpg",
            "total_pages": 96,
            "isbn": "978-2-07-040850-4"
        }
        
        # Test book with saga information
        self.test_saga_book_data = {
            "title": "Harry Potter et la Chambre des Secrets",
            "author": "J.K. Rowling",
            "category": "roman",
            "description": "Deuxième tome de la saga Harry Potter",
            "total_pages": 368,
            "saga": "Harry Potter Test",
            "volume_number": 2,
            "genre": "fantasy",
            "publication_year": 1998,
            "publisher": "Gallimard"
        }
        
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

    def test_01_welcome_message(self):
        """Test the root endpoint returns a welcome message"""
        response = requests.get(BACKEND_URL)
        self.assertEqual(response.status_code, 200)
        try:
            data = response.json()
            self.assertIn("message", data)
        except:
            # If not JSON, check that the response is not empty
            self.assertTrue(len(response.text) > 0)
        print("✅ Welcome message endpoint working")

    def test_02_authentication(self):
        """Test authentication endpoints"""
        if not self.token:
            self.fail("Authentication failed during setup")
            
        # Test get current user
        response = requests.get(f"{API_URL}/auth/me", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        user = response.json()
        self.assertEqual(user["first_name"], self.user["first_name"])
        self.assertEqual(user["last_name"], self.user["last_name"])
        
        # Test invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = requests.get(f"{API_URL}/auth/me", headers=invalid_headers)
        self.assertIn(response.status_code, [401, 403, 404])  # Accept either 401, 403, or 404
        
        # Test missing token
        response = requests.get(f"{API_URL}/auth/me")
        self.assertIn(response.status_code, [401, 403, 404])  # Accept either 401, 403, or 404
        
        print("✅ Authentication endpoints working")

    def test_03_get_stats(self):
        """Test the stats endpoint returns correct statistics"""
        response = requests.get(f"{API_URL}/stats", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that all required fields are present
        required_fields = ["total_books", "completed_books", "reading_books", 
                          "to_read_books", "categories", "sagas_count", 
                          "authors_count", "auto_added_count"]
        for field in required_fields:
            self.assertIn(field, data)
        
        # Check that categories contains the expected subcategories
        self.assertIn("roman", data["categories"])
        self.assertIn("bd", data["categories"])
        self.assertIn("manga", data["categories"])
        
        print("✅ Stats endpoint working")

    def test_04_get_all_books(self):
        """Test retrieving all books"""
        response = requests.get(f"{API_URL}/books", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        books = response.json()
        
        # Check that each book has the required fields if any books exist
        if books:
            for book in books:
                self.assertIn("id", book)
                self.assertIn("title", book)
                self.assertIn("author", book)
                self.assertIn("category", book)
                self.assertIn("status", book)
        
        print(f"✅ Get all books endpoint working, found {len(books)} books")

    def test_05_filter_books(self):
        """Test filtering books by category and status"""
        # Create books with different categories and statuses
        categories = ["roman", "bd", "manga"]
        statuses = ["to_read", "reading", "completed"]
        
        for i, (category, status) in enumerate(zip(categories, statuses)):
            book_data = self.test_book_data.copy()
            book_data["title"] = f"Test Book {i+1}"
            book_data["category"] = category
            book_data["status"] = status
            
            response = requests.post(f"{API_URL}/books", json=book_data, headers=self.headers)
            self.assertEqual(response.status_code, 200)
            book = response.json()
            self.book_ids_to_delete.append(book["id"])
        
        # Test filtering by category
        for category in categories:
            response = requests.get(f"{API_URL}/books?category={category}", headers=self.headers)
            self.assertEqual(response.status_code, 200)
            books = response.json()
            
            # Check that all returned books have the correct category
            for book in books:
                self.assertEqual(book["category"], category)
            
            print(f"✅ Filter by category '{category}' working")
        
        # Test filtering by status
        for status in statuses:
            response = requests.get(f"{API_URL}/books?status={status}", headers=self.headers)
            self.assertEqual(response.status_code, 200)
            books = response.json()
            
            # Check that all returned books have the correct status
            for book in books:
                self.assertEqual(book["status"], status)
            
            print(f"✅ Filter by status '{status}' working")

    def test_06_crud_operations(self):
        """Test CRUD operations on books"""
        # Create a book
        response = requests.post(f"{API_URL}/books", json=self.test_book_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        book = response.json()
        book_id = book["id"]
        self.book_ids_to_delete.append(book_id)
        
        # Check that the book was created with the correct data
        self.assertEqual(book["title"], self.test_book_data["title"])
        self.assertEqual(book["author"], self.test_book_data["author"])
        self.assertEqual(book["category"], self.test_book_data["category"])
        
        # Get the book
        response = requests.get(f"{API_URL}/books/{book_id}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        retrieved_book = response.json()
        self.assertEqual(retrieved_book["id"], book_id)
        
        # Update the book
        update_data = {
            "status": "reading",
            "current_page": 42
        }
        response = requests.put(f"{API_URL}/books/{book_id}", json=update_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        updated_book = response.json()
        self.assertEqual(updated_book["status"], "reading")
        self.assertEqual(updated_book["current_page"], 42)
        
        # Delete the book
        response = requests.delete(f"{API_URL}/books/{book_id}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        # Verify the book was deleted
        response = requests.get(f"{API_URL}/books/{book_id}", headers=self.headers)
        self.assertEqual(response.status_code, 404)
        
        # Remove from cleanup list since we already deleted it
        self.book_ids_to_delete.remove(book_id)
        
        print("✅ CRUD operations working")

    def test_07_validation(self):
        """Test validation rules"""
        # Test creating a book without a title
        invalid_book = self.test_book_data.copy()
        del invalid_book["title"]
        
        response = requests.post(f"{API_URL}/books", json=invalid_book, headers=self.headers)
        self.assertNotEqual(response.status_code, 200)
        
        # Test updating a non-existent book
        fake_id = str(uuid.uuid4())
        update_data = {"status": "reading"}
        response = requests.put(f"{API_URL}/books/{fake_id}", json=update_data, headers=self.headers)
        self.assertEqual(response.status_code, 404)
        
        # Test category validation
        valid_categories = ["roman", "bd", "manga", "Roman", "BD", "Manga"]
        invalid_categories = ["fiction", "comic", "novel", "science-fiction"]
        
        for category in valid_categories:
            test_book = self.test_book_data.copy()
            test_book["title"] = f"Test Book with {category} category"
            test_book["category"] = category
            
            response = requests.post(f"{API_URL}/books", json=test_book, headers=self.headers)
            self.assertEqual(response.status_code, 200)
            
            if response.status_code == 200:
                book = response.json()
                self.book_ids_to_delete.append(book["id"])
                # Category should be normalized to lowercase
                self.assertEqual(book["category"], category.lower())
        
        for category in invalid_categories:
            test_book = self.test_book_data.copy()
            test_book["title"] = f"Test Book with {category} category"
            test_book["category"] = category
            
            response = requests.post(f"{API_URL}/books", json=test_book, headers=self.headers)
            self.assertNotEqual(response.status_code, 200)
        
        print("✅ Validation rules working")

    def test_08_authors_endpoints(self):
        """Test authors endpoints"""
        # Create books by different authors
        authors = ["Victor Hugo", "Albert Camus", "Simone de Beauvoir"]
        
        for i, author in enumerate(authors):
            book_data = self.test_book_data.copy()
            book_data["title"] = f"Test Book by {author}"
            book_data["author"] = author
            
            response = requests.post(f"{API_URL}/books", json=book_data, headers=self.headers)
            self.assertEqual(response.status_code, 200)
            book = response.json()
            self.book_ids_to_delete.append(book["id"])
        
        # Get all authors
        response = requests.get(f"{API_URL}/authors", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        all_authors = response.json()
        
        # Check that our authors are in the list
        for author in authors:
            found = any(a["name"] == author for a in all_authors)
            self.assertTrue(found, f"Author {author} not found in authors list")
        
        # Get books by a specific author
        author = authors[0]
        response = requests.get(f"{API_URL}/authors/{author}/books", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        author_books = response.json()
        
        # Check that all books are by the specified author
        for book in author_books:
            self.assertEqual(book["author"], author)
        
        print("✅ Authors endpoints working")

    def test_09_sagas_endpoints(self):
        """Test sagas endpoints"""
        # Create books in a saga
        saga_name = "Test Saga"
        volumes = 3
        
        for i in range(volumes):
            book_data = self.test_book_data.copy()
            book_data["title"] = f"{saga_name} - Tome {i+1}"
            book_data["saga"] = saga_name
            book_data["volume_number"] = i+1
            
            response = requests.post(f"{API_URL}/books", json=book_data, headers=self.headers)
            self.assertEqual(response.status_code, 200)
            book = response.json()
            self.book_ids_to_delete.append(book["id"])
        
        # Get all sagas
        response = requests.get(f"{API_URL}/sagas", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        sagas = response.json()
        
        # Check that our saga is in the list
        found_saga = next((s for s in sagas if s["name"] == saga_name), None)
        self.assertIsNotNone(found_saga, f"Saga {saga_name} not found in sagas list")
        
        if found_saga:
            self.assertEqual(found_saga["books_count"], volumes)
            
        # Get books in the saga
        response = requests.get(f"{API_URL}/sagas/{saga_name}/books", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        saga_books = response.json()
        
        # Check that all books are in the specified saga and sorted by volume
        self.assertEqual(len(saga_books), volumes)
        for i, book in enumerate(saga_books):
            self.assertEqual(book["saga"], saga_name)
            self.assertEqual(book["volume_number"], i+1)
        
        # Auto-add next volume
        response = requests.post(f"{API_URL}/sagas/{saga_name}/auto-add", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        new_book = response.json()["book"]
        self.book_ids_to_delete.append(new_book["id"])
        
        # Verify the new book
        self.assertEqual(new_book["saga"], saga_name)
        self.assertEqual(new_book["volume_number"], volumes+1)
        self.assertEqual(new_book["status"], "to_read")
        self.assertTrue(new_book["auto_added"])
        
        print("✅ Sagas endpoints working")

    def test_10_openlibrary_search(self):
        """Test searching books on Open Library"""
        # Test basic search
        query = "Harry Potter"
        response = requests.get(f"{API_URL}/openlibrary/search?q={query}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertIn("books", result)
        self.assertIn("total_found", result)
        
        if len(result["books"]) > 0:
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
        
        print("✅ Open Library search endpoint working")

    def test_11_openlibrary_import(self):
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
        
        print("✅ Open Library import endpoint working")

    def test_12_book_enrichment(self):
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
        
        print("✅ Book enrichment endpoint working")

    def test_13_openlibrary_advanced_search(self):
        """Test advanced search on Open Library"""
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
        
        print("✅ Open Library advanced search endpoint working")

    def test_14_openlibrary_search_isbn(self):
        """Test searching by ISBN on Open Library"""
        # Test with a valid ISBN
        isbn = "9780747532743"  # Harry Potter ISBN
        
        response = requests.get(f"{API_URL}/openlibrary/search-isbn?isbn={isbn}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertIn("book", result)
        self.assertIn("found", result)
        
        print("✅ Open Library ISBN search endpoint working")

    def test_15_openlibrary_search_author(self):
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
        
        print("✅ Open Library author search endpoint working")

    def test_16_openlibrary_missing_volumes(self):
        """Test detecting missing saga volumes"""
        # Create a test saga with volumes 1, 2, and 4 (missing 3)
        saga_name = "Test Missing Volumes Saga"
        volumes = [1, 2, 4]
        
        for volume in volumes:
            book_data = self.test_book_data.copy()
            book_data["title"] = f"{saga_name} - Tome {volume}"
            book_data["saga"] = saga_name
            book_data["volume_number"] = volume
            
            response = requests.post(f"{API_URL}/books", json=book_data, headers=self.headers)
            self.assertEqual(response.status_code, 200)
            book = response.json()
            self.book_ids_to_delete.append(book["id"])
        
        # Test missing volumes detection
        response = requests.get(f"{API_URL}/openlibrary/missing-volumes?saga={saga_name}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertIn("saga", result)
        self.assertIn("present_volumes", result)
        self.assertIn("missing_volumes", result)
        self.assertIn("next_volume", result)
        
        # Verify missing volume 3
        self.assertEqual(result["present_volumes"], volumes)
        self.assertEqual(result["missing_volumes"], [3])
        self.assertEqual(result["next_volume"], 5)
        
        print("✅ Open Library missing volumes endpoint working")

    def test_17_openlibrary_recommendations(self):
        """Test getting personalized recommendations"""
        response = requests.get(f"{API_URL}/openlibrary/recommendations", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertIn("recommendations", result)
        
        print("✅ Open Library recommendations endpoint working")

    def test_18_openlibrary_suggestions(self):
        """Test getting import suggestions"""
        response = requests.get(f"{API_URL}/openlibrary/suggestions", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertIn("suggestions", result)
        
        print("✅ Open Library suggestions endpoint working")

    def test_19_search_grouped(self):
        """Test search with saga grouping"""
        # Create books in a saga
        saga_name = "Test Search Saga"
        volumes = 3
        
        for i in range(volumes):
            book_data = self.test_book_data.copy()
            book_data["title"] = f"{saga_name} - Tome {i+1}"
            book_data["saga"] = saga_name
            book_data["volume_number"] = i+1
            
            response = requests.post(f"{API_URL}/books", json=book_data, headers=self.headers)
            self.assertEqual(response.status_code, 200)
            book = response.json()
            self.book_ids_to_delete.append(book["id"])
        
        # Search for the saga
        response = requests.get(f"{API_URL}/books/search-grouped?q={saga_name}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        self.assertIn("results", result)
        self.assertIn("total_books", result)
        self.assertIn("total_sagas", result)
        self.assertIn("search_term", result)
        self.assertIn("grouped_by_saga", result)
        
        # Should find our saga
        self.assertEqual(result["total_books"], volumes)
        self.assertEqual(result["total_sagas"], 1)
        
        # Check saga grouping
        if result["results"]:
            saga_group = result["results"][0]
            self.assertEqual(saga_group["type"], "saga")
            self.assertEqual(saga_group["name"], saga_name)
            self.assertEqual(len(saga_group["books"]), volumes)
        
        print("✅ Search with saga grouping endpoint working")

    def test_20_bulk_import(self):
        """Test bulk import from Open Library"""
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
        
        print("✅ Bulk import endpoint working")

def run_tests():
    """Run all tests and print a summary"""
    # Create a test suite with all tests
    suite = unittest.TestLoader().loadTestsFromTestCase(BooktimeAPITest)
    
    # Run the tests
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # Print summary
    print("\n=== TEST SUMMARY ===")
    print(f"Total tests: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    sys.exit(run_tests())