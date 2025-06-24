import requests
import json
import unittest
import uuid
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "http://localhost:8001"
API_URL = f"{BACKEND_URL}/api"

class BooktimeAPITest(unittest.TestCase):
    """Test suite for the Booktime API"""

    def setUp(self):
        """Setup for each test"""
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
            "saga": "Harry Potter",
            "volume_number": 2,
            "genre": ["fantasy", "young adult"],
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
                requests.delete(f"{API_URL}/books/{book_id}")
            except:
                pass

    def test_welcome_message(self):
        """Test the root endpoint returns a welcome message"""
        response = requests.get(BACKEND_URL)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("Welcome to BOOKTIME API", data["message"])
        print("✅ Welcome message endpoint working")

    def test_get_stats(self):
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
        
        # Check that categories contains the expected subcategories
        self.assertIn("roman", data["categories"])
        self.assertIn("bd", data["categories"])
        self.assertIn("manga", data["categories"])
        
        # Verify that the sum of status counts equals total books
        status_sum = data["completed_books"] + data["reading_books"] + data["to_read_books"]
        self.assertEqual(data["total_books"], status_sum)
        
        # Verify the extended stats
        self.assertGreaterEqual(data["total_books"], 18, "Should have at least 18 books")
        self.assertGreaterEqual(data["sagas_count"], 7, "Should have at least 7 sagas")
        self.assertGreaterEqual(data["authors_count"], 9, "Should have at least 9 authors")
        self.assertGreaterEqual(data["auto_added_count"], 5, "Should have at least 5 auto-added books")
        
        print("✅ Stats endpoint working with extended stats")
        print(f"   Total books: {data['total_books']}")
        print(f"   Sagas: {data['sagas_count']}")
        print(f"   Authors: {data['authors_count']}")
        print(f"   Auto-added books: {data['auto_added_count']}")

    def test_get_all_books(self):
        """Test retrieving all books"""
        response = requests.get(f"{API_URL}/books")
        self.assertEqual(response.status_code, 200)
        books = response.json()
        
        # Should have at least 8 books as mentioned in the context
        self.assertGreaterEqual(len(books), 8)
        
        # Check that each book has the required fields
        for book in books:
            self.assertIn("_id", book)
            self.assertIn("title", book)
            self.assertIn("author", book)
            self.assertIn("category", book)
            self.assertIn("status", book)
        
        print(f"✅ Get all books endpoint working, found {len(books)} books")

    def test_filter_books_by_category(self):
        """Test filtering books by category"""
        categories = ["roman", "bd", "manga"]
        
        for category in categories:
            response = requests.get(f"{API_URL}/books?category={category}")
            self.assertEqual(response.status_code, 200)
            books = response.json()
            
            # Check that all returned books have the correct category
            for book in books:
                self.assertEqual(book["category"], category)
            
            print(f"✅ Filter by category '{category}' working, found {len(books)} books")

    def test_filter_books_by_status(self):
        """Test filtering books by status"""
        statuses = ["to_read", "reading", "completed"]
        
        for status in statuses:
            response = requests.get(f"{API_URL}/books?status={status}")
            self.assertEqual(response.status_code, 200)
            books = response.json()
            
            # Check that all returned books have the correct status
            for book in books:
                self.assertEqual(book["status"], status)
            
            print(f"✅ Filter by status '{status}' working, found {len(books)} books")

    def test_get_specific_book(self):
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

    def test_get_nonexistent_book(self):
        """Test retrieving a non-existent book"""
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{API_URL}/books/{fake_id}")
        self.assertEqual(response.status_code, 404)
        print("✅ Get non-existent book returns 404 as expected")

    def test_create_book(self):
        """Test creating a new book"""
        response = requests.post(f"{API_URL}/books", json=self.test_book_data)
        self.assertEqual(response.status_code, 200)
        book = response.json()
        
        # Add book ID to cleanup list
        self.book_ids_to_delete.append(book["_id"])
        
        # Check that the book was created with the correct data
        self.assertEqual(book["title"], self.test_book_data["title"])
        self.assertEqual(book["author"], self.test_book_data["author"])
        self.assertEqual(book["category"], self.test_book_data["category"])
        self.assertEqual(book["status"], "to_read")  # Default status
        self.assertEqual(book["current_page"], 0)    # Default current page
        
        print("✅ Create book endpoint working")

    def test_create_book_without_title(self):
        """Test creating a book without a title (should fail)"""
        invalid_book = self.test_book_data.copy()
        del invalid_book["title"]
        
        response = requests.post(f"{API_URL}/books", json=invalid_book)
        self.assertNotEqual(response.status_code, 200)
        print("✅ Create book without title fails as expected")

    def test_update_book(self):
        """Test updating a book"""
        # First create a book to update
        response = requests.post(f"{API_URL}/books", json=self.test_book_data)
        self.assertEqual(response.status_code, 200)
        book = response.json()
        book_id = book["_id"]
        self.book_ids_to_delete.append(book_id)
        
        # Update the book status to reading
        update_data = {
            "status": "reading",
            "current_page": 42
        }
        response = requests.put(f"{API_URL}/books/{book_id}", json=update_data)
        self.assertEqual(response.status_code, 200)
        updated_book = response.json()
        
        # Check that the book was updated correctly
        self.assertEqual(updated_book["status"], "reading")
        self.assertEqual(updated_book["current_page"], 42)
        self.assertIsNotNone(updated_book["date_started"])  # Should be set automatically
        
        # Update to completed
        update_data = {
            "status": "completed",
            "current_page": 96,
            "rating": 5,
            "review": "Un chef-d'œuvre intemporel"
        }
        response = requests.put(f"{API_URL}/books/{book_id}", json=update_data)
        self.assertEqual(response.status_code, 200)
        updated_book = response.json()
        
        # Check that the book was updated correctly
        self.assertEqual(updated_book["status"], "completed")
        self.assertEqual(updated_book["current_page"], 96)
        self.assertEqual(updated_book["rating"], 5)
        self.assertEqual(updated_book["review"], "Un chef-d'œuvre intemporel")
        self.assertIsNotNone(updated_book["date_completed"])  # Should be set automatically
        
        print("✅ Update book endpoint working")

    def test_update_nonexistent_book(self):
        """Test updating a non-existent book"""
        fake_id = str(uuid.uuid4())
        update_data = {"status": "reading"}
        response = requests.put(f"{API_URL}/books/{fake_id}", json=update_data)
        self.assertEqual(response.status_code, 404)
        print("✅ Update non-existent book returns 404 as expected")

    def test_delete_book(self):
        """Test deleting a book"""
        # First create a book to delete
        response = requests.post(f"{API_URL}/books", json=self.test_book_data)
        self.assertEqual(response.status_code, 200)
        book = response.json()
        book_id = book["_id"]
        
        # Delete the book
        response = requests.delete(f"{API_URL}/books/{book_id}")
        self.assertEqual(response.status_code, 200)
        
        # Verify the book was deleted
        response = requests.get(f"{API_URL}/books/{book_id}")
        self.assertEqual(response.status_code, 404)
        
        print("✅ Delete book endpoint working")

    def test_delete_nonexistent_book(self):
        """Test deleting a non-existent book"""
        fake_id = str(uuid.uuid4())
        response = requests.delete(f"{API_URL}/books/{fake_id}")
        self.assertEqual(response.status_code, 404)
        print("✅ Delete non-existent book returns 404 as expected")

    def test_invalid_category(self):
        """Test creating a book with an invalid category"""
        invalid_book = self.test_book_data.copy()
        invalid_book["category"] = "science-fiction"  # Not in the allowed categories
        
        # The API doesn't explicitly validate categories, so this should succeed
        # but the category will be stored in lowercase
        response = requests.post(f"{API_URL}/books", json=invalid_book)
        self.assertEqual(response.status_code, 200)
        book = response.json()
        self.book_ids_to_delete.append(book["_id"])
        
        # Check that the category was stored as provided (in lowercase)
        self.assertEqual(book["category"], "science-fiction")
        
        print("⚠️ Invalid category validation not implemented in API")

    def test_stats_update_after_crud(self):
        """Test that stats are updated after CRUD operations"""
        # Get initial stats
        response = requests.get(f"{API_URL}/stats")
        initial_stats = response.json()
        
        # Create a new book
        new_book = self.test_book_data.copy()
        new_book["category"] = "manga"  # Use manga for easier tracking
        response = requests.post(f"{API_URL}/books", json=new_book)
        self.assertEqual(response.status_code, 200)
        book = response.json()
        book_id = book["_id"]
        self.book_ids_to_delete.append(book_id)
        
        # Get updated stats
        response = requests.get(f"{API_URL}/stats")
        after_create_stats = response.json()
        
        # Check that total books increased by 1
        self.assertEqual(after_create_stats["total_books"], initial_stats["total_books"] + 1)
        # Check that to_read books increased by 1
        self.assertEqual(after_create_stats["to_read_books"], initial_stats["to_read_books"] + 1)
        # Check that manga count increased by 1
        self.assertEqual(after_create_stats["categories"]["manga"], 
                         initial_stats["categories"]["manga"] + 1)
        
        # Update book to reading
        update_data = {"status": "reading"}
        response = requests.put(f"{API_URL}/books/{book_id}", json=update_data)
        self.assertEqual(response.status_code, 200)
        
        # Get updated stats
        response = requests.get(f"{API_URL}/stats")
        after_update_stats = response.json()
        
        # Check that to_read books decreased by 1
        self.assertEqual(after_update_stats["to_read_books"], after_create_stats["to_read_books"] - 1)
        # Check that reading books increased by 1
        self.assertEqual(after_update_stats["reading_books"], after_create_stats["reading_books"] + 1)
        
        # Delete the book
        response = requests.delete(f"{API_URL}/books/{book_id}")
        self.assertEqual(response.status_code, 200)
        self.book_ids_to_delete.remove(book_id)  # Remove from cleanup list
        
        # Get final stats
        response = requests.get(f"{API_URL}/stats")
        after_delete_stats = response.json()
        
        # Check that total books decreased by 1
        self.assertEqual(after_delete_stats["total_books"], after_update_stats["total_books"] - 1)
        # Check that reading books decreased by 1
        self.assertEqual(after_delete_stats["reading_books"], after_update_stats["reading_books"] - 1)
        # Check that manga count decreased by 1
        self.assertEqual(after_delete_stats["categories"]["manga"], 
                         after_update_stats["categories"]["manga"] - 1)
        
        print("✅ Stats update correctly after CRUD operations")


if __name__ == "__main__":
    unittest.main(verbosity=2)