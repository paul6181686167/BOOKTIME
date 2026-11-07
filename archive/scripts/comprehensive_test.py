import requests
import json
import unittest
import uuid
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "http://localhost:8001"
API_URL = f"{BACKEND_URL}/api"

class BooktimeComprehensiveTest(unittest.TestCase):
    """Comprehensive test suite for the Booktime API based on the review request"""

    def setUp(self):
        """Setup for each test"""
        self.test_book_data = {
            "title": "Test Book",
            "author": "Test Author",
            "category": "roman",
            "description": "A test book for API testing",
            "total_pages": 200,
            "isbn": "978-3-16-148410-0"
        }
        
        # Book IDs to be used/cleaned up during testing
        self.book_ids_to_delete = []

    def tearDown(self):
        """Clean up after each test"""
        # Delete any books created during testing
        for book_id in self.book_ids_to_delete:
            try:
                requests.delete(f"{API_URL}/books/{book_id}")
            except:
                pass

    def test_1_welcome_message(self):
        """Test the root endpoint returns a welcome message"""
        response = requests.get(BACKEND_URL)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("Welcome to BOOKTIME API", data["message"])
        print("✅ Welcome message endpoint working")

    def test_2_stats(self):
        """Test the stats endpoint returns correct statistics"""
        response = requests.get(f"{API_URL}/stats")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that all required fields are present
        required_fields = ["total_books", "completed_books", "reading_books", 
                          "to_read_books", "categories", "sagas_count", 
                          "authors_count", "auto_added_count"]
        for field in required_fields:
            self.assertIn(field, data)
        
        # Verify the specific stats from the review request
        self.assertEqual(data["total_books"], 18, "Should have exactly 18 books")
        self.assertEqual(data["categories"]["roman"], 7, "Should have 7 roman books")
        self.assertEqual(data["categories"]["bd"], 4, "Should have 4 bd books")
        self.assertEqual(data["categories"]["manga"], 7, "Should have 7 manga books")
        self.assertEqual(data["sagas_count"], 7, "Should have 7 sagas")
        self.assertEqual(data["authors_count"], 9, "Should have 9 authors")
        self.assertEqual(data["auto_added_count"], 5, "Should have 5 auto-added books")
        
        print("✅ Stats endpoint working with correct data:")
        print(f"   Total books: {data['total_books']}")
        print(f"   Romans: {data['categories']['roman']}, BD: {data['categories']['bd']}, Mangas: {data['categories']['manga']}")
        print(f"   Sagas: {data['sagas_count']}")
        print(f"   Authors: {data['authors_count']}")
        print(f"   Auto-added books: {data['auto_added_count']}")

    def test_3_get_all_books(self):
        """Test retrieving all books"""
        response = requests.get(f"{API_URL}/books")
        self.assertEqual(response.status_code, 200)
        books = response.json()
        
        # Should have 18 books as mentioned in the review request
        self.assertEqual(len(books), 18, "Should have exactly 18 books")
        
        # Check that each book has the required fields
        for book in books:
            self.assertIn("_id", book)
            self.assertIn("title", book)
            self.assertIn("author", book)
            self.assertIn("category", book)
            self.assertIn("status", book)
        
        print(f"✅ Get all books endpoint working, found {len(books)} books")

    def test_4_filter_books(self):
        """Test filtering books by category and status"""
        # Test category filters
        categories = ["roman", "bd", "manga"]
        expected_counts = {"roman": 7, "bd": 4, "manga": 7}
        
        for category in categories:
            response = requests.get(f"{API_URL}/books?category={category}")
            self.assertEqual(response.status_code, 200)
            books = response.json()
            
            # Check count matches expected
            self.assertEqual(len(books), expected_counts[category], 
                            f"Should have {expected_counts[category]} {category} books")
            
            # Check that all returned books have the correct category
            for book in books:
                self.assertEqual(book["category"], category)
            
            print(f"✅ Filter by category '{category}' working, found {len(books)} books")
        
        # Test status filters
        statuses = ["to_read", "reading", "completed"]
        
        for status in statuses:
            response = requests.get(f"{API_URL}/books?status={status}")
            self.assertEqual(response.status_code, 200)
            books = response.json()
            
            # Check that all returned books have the correct status
            for book in books:
                self.assertEqual(book["status"], status)
            
            print(f"✅ Filter by status '{status}' working, found {len(books)} books")

    def test_5_get_specific_book(self):
        """Test retrieving a specific book by ID"""
        # First get all books to find a valid ID
        response = requests.get(f"{API_URL}/books")
        books = response.json()
        
        if books:
            book_id = books[0]["_id"]
            response = requests.get(f"{API_URL}/books/{book_id}")
            self.assertEqual(response.status_code, 200)
            book = response.json()
            self.assertEqual(book["_id"], book_id)
            print(f"✅ Get specific book endpoint working")
        else:
            self.fail("No books found to test specific book retrieval")

    def test_6_create_update_delete_book(self):
        """Test CRUD operations for books"""
        # Create a book
        response = requests.post(f"{API_URL}/books", json=self.test_book_data)
        self.assertEqual(response.status_code, 200)
        book = response.json()
        book_id = book["_id"]
        self.book_ids_to_delete.append(book_id)
        
        # Check that the book was created with the correct data
        self.assertEqual(book["title"], self.test_book_data["title"])
        self.assertEqual(book["author"], self.test_book_data["author"])
        self.assertEqual(book["category"], self.test_book_data["category"])
        self.assertEqual(book["status"], "to_read")  # Default status
        print("✅ Create book endpoint working")
        
        # Update the book
        update_data = {
            "status": "reading",
            "current_page": 50
        }
        response = requests.put(f"{API_URL}/books/{book_id}", json=update_data)
        self.assertEqual(response.status_code, 200)
        updated_book = response.json()
        
        # Check that the book was updated correctly
        self.assertEqual(updated_book["status"], "reading")
        self.assertEqual(updated_book["current_page"], 50)
        self.assertIsNotNone(updated_book["date_started"])  # Should be set automatically
        print("✅ Update book endpoint working")
        
        # Delete the book
        response = requests.delete(f"{API_URL}/books/{book_id}")
        self.assertEqual(response.status_code, 200)
        
        # Verify the book was deleted
        response = requests.get(f"{API_URL}/books/{book_id}")
        self.assertEqual(response.status_code, 404)
        
        # Remove from cleanup list since we already deleted it
        self.book_ids_to_delete.remove(book_id)
        print("✅ Delete book endpoint working")

    def test_7_authors_api(self):
        """Test the authors API endpoints"""
        # Get all authors
        response = requests.get(f"{API_URL}/authors")
        self.assertEqual(response.status_code, 200)
        authors = response.json()
        
        # Should have 9 authors as mentioned in the review request
        self.assertEqual(len(authors), 9, "Should have exactly 9 authors")
        
        # Check that each author has the required fields
        for author in authors:
            self.assertIn("name", author)
            self.assertIn("books_count", author)
            self.assertIn("categories", author)
            self.assertIn("sagas", author)
        
        # Test getting books by a specific author
        if authors:
            author_name = authors[0]["name"]
            response = requests.get(f"{API_URL}/authors/{author_name}/books")
            self.assertEqual(response.status_code, 200)
            books = response.json()
            
            # Check that all books are by the specified author
            for book in books:
                self.assertEqual(book["author"], author_name)
            
            print(f"✅ Authors API working, found {len(authors)} authors")
            print(f"✅ Books by author endpoint working, found {len(books)} books by {author_name}")

    def test_8_sagas_api(self):
        """Test the sagas API endpoints"""
        # Get all sagas
        response = requests.get(f"{API_URL}/sagas")
        self.assertEqual(response.status_code, 200)
        sagas = response.json()
        
        # Should have 7 sagas as mentioned in the review request
        self.assertEqual(len(sagas), 7, "Should have exactly 7 sagas")
        
        # Check that each saga has the required fields
        for saga in sagas:
            self.assertIn("name", saga)
            self.assertIn("books_count", saga)
            self.assertIn("completed_books", saga)
            self.assertIn("author", saga)
            self.assertIn("category", saga)
            self.assertIn("next_volume", saga)
        
        # Test getting books in a specific saga
        if sagas:
            saga_name = sagas[0]["name"]
            response = requests.get(f"{API_URL}/sagas/{saga_name}/books")
            self.assertEqual(response.status_code, 200)
            books = response.json()
            
            # Check that all books are in the specified saga
            for book in books:
                self.assertEqual(book["saga"], saga_name)
            
            # Check that books are sorted by volume_number
            for i in range(1, len(books)):
                self.assertLessEqual(books[i-1]["volume_number"], books[i]["volume_number"])
            
            print(f"✅ Sagas API working, found {len(sagas)} sagas")
            print(f"✅ Books in saga endpoint working, found {len(books)} books in {saga_name}")
            
            # Test auto-adding the next volume
            response = requests.post(f"{API_URL}/sagas/{saga_name}/auto-add")
            self.assertEqual(response.status_code, 200)
            new_book = response.json()
            self.book_ids_to_delete.append(new_book["_id"])
            
            # Verify the new book
            self.assertEqual(new_book["saga"], saga_name)
            self.assertEqual(new_book["status"], "to_read")
            self.assertTrue(new_book["auto_added"])
            
            print(f"✅ Auto-add next volume endpoint working for {saga_name}")

    def test_9_validation(self):
        """Test validation rules"""
        # Test category validation
        invalid_book = self.test_book_data.copy()
        invalid_book["category"] = "fiction"  # Not one of roman, bd, manga
        
        response = requests.post(f"{API_URL}/books", json=invalid_book)
        self.assertNotEqual(response.status_code, 200)
        
        # Test that valid categories work
        valid_categories = ["roman", "bd", "manga", "Roman", "BD", "Manga"]
        
        for category in valid_categories:
            test_book = self.test_book_data.copy()
            test_book["title"] = f"Test Book with {category} category"
            test_book["category"] = category
            
            response = requests.post(f"{API_URL}/books", json=test_book)
            self.assertEqual(response.status_code, 200, f"Creating book with category '{category}' should succeed")
            
            if response.status_code == 200:
                book = response.json()
                self.book_ids_to_delete.append(book["_id"])
                # Category should be normalized to lowercase
                self.assertEqual(book["category"], category.lower())
        
        print("✅ Category validation works correctly")
        print("   - Valid categories (roman, bd, manga) are accepted and normalized to lowercase")
        print("   - Invalid categories are rejected")
        
        # Test 404 for non-existent resources
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{API_URL}/books/{fake_id}")
        self.assertEqual(response.status_code, 404)
        
        response = requests.get(f"{API_URL}/sagas/NonExistentSaga/books")
        self.assertEqual(response.status_code, 200)  # Returns empty list, not 404
        self.assertEqual(len(response.json()), 0)
        
        response = requests.post(f"{API_URL}/sagas/NonExistentSaga/auto-add")
        self.assertEqual(response.status_code, 404)
        
        print("✅ 404 errors for non-existent resources working correctly")

if __name__ == "__main__":
    unittest.main(verbosity=2)