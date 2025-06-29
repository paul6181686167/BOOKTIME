import requests
import json
import unittest
import uuid
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://4d0fa139-856b-4b90-9226-6c383550f064.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class RapidBooktimeAPITest(unittest.TestCase):
    """Rapid test suite for the Booktime API core functionalities"""

    def setUp(self):
        """Setup for each test"""
        # Test user data for authentication
        self.test_user_data = {
            "first_name": "Jean",
            "last_name": "Dupont"
        }
        
        # Test book data for CRUD operations
        self.test_book_data = {
            "title": "Le Petit Prince",
            "author": "Antoine de Saint-Exupéry",
            "category": "roman",
            "description": "Un conte philosophique sous forme d'un récit pour enfants",
            "cover_url": "https://example.com/petit-prince.jpg",
            "total_pages": 96,
            "isbn": "978-2-07-040850-4"
        }
        
        # Book IDs to be used/cleaned up during testing
        self.book_ids_to_delete = []
        self.auth_token = None
        
        # Register and login to get auth token
        self.register_and_login()

    def tearDown(self):
        """Clean up after each test"""
        # Delete any books created during testing
        if self.auth_token:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            for book_id in self.book_ids_to_delete:
                try:
                    requests.delete(f"{API_URL}/books/{book_id}", headers=headers)
                except:
                    pass

    def register_and_login(self):
        """Register a test user and login to get auth token"""
        # Try to register first
        try:
            response = requests.post(f"{API_URL}/auth/register", json=self.test_user_data)
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data["access_token"]
                print(f"✅ Successfully registered user: {self.test_user_data['first_name']} {self.test_user_data['last_name']}")
            else:
                # If registration fails (user might already exist), try login
                response = requests.post(f"{API_URL}/auth/login", json=self.test_user_data)
                if response.status_code == 200:
                    data = response.json()
                    self.auth_token = data["access_token"]
                    print(f"✅ Successfully logged in as: {self.test_user_data['first_name']} {self.test_user_data['last_name']}")
                else:
                    print(f"❌ Failed to authenticate: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")

    def test_1_authentication(self):
        """Test registration and login with first name/last name"""
        # Test that we have a valid token from setup
        self.assertIsNotNone(self.auth_token, "Authentication token should be obtained during setup")
        
        # Test getting current user info
        if self.auth_token:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = requests.get(f"{API_URL}/auth/me", headers=headers)
            self.assertEqual(response.status_code, 200)
            user_data = response.json()
            self.assertEqual(user_data["first_name"], self.test_user_data["first_name"])
            self.assertEqual(user_data["last_name"], self.test_user_data["last_name"])
            print(f"✅ Successfully retrieved user profile for: {user_data['first_name']} {user_data['last_name']}")
        
        # Test registration with a different user
        test_user2 = {
            "first_name": "Marie",
            "last_name": "Durand"
        }
        
        response = requests.post(f"{API_URL}/auth/register", json=test_user2)
        if response.status_code == 200:
            data = response.json()
            self.assertIn("access_token", data)
            self.assertIn("user", data)
            self.assertEqual(data["user"]["first_name"], test_user2["first_name"])
            self.assertEqual(data["user"]["last_name"], test_user2["last_name"])
            print(f"✅ Successfully registered second user: {test_user2['first_name']} {test_user2['last_name']}")
        elif response.status_code == 400 and "existe déjà" in response.text:
            print(f"ℹ️ User {test_user2['first_name']} {test_user2['last_name']} already exists")
        else:
            self.fail(f"Registration failed with status {response.status_code}: {response.text}")
        
        # Test login with the second user
        response = requests.post(f"{API_URL}/auth/login", json=test_user2)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["first_name"], test_user2["first_name"])
        self.assertEqual(data["user"]["last_name"], test_user2["last_name"])
        print(f"✅ Successfully logged in as second user: {test_user2['first_name']} {test_user2['last_name']}")

    def test_2_crud_books(self):
        """Test CRUD operations for books"""
        self.assertIsNotNone(self.auth_token, "Authentication token should be obtained during setup")
        
        if not self.auth_token:
            self.fail("No authentication token available")
            return
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # CREATE - Test creating a new book
        response = requests.post(f"{API_URL}/books", json=self.test_book_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        book = response.json()
        
        # Save book ID for later tests and cleanup
        book_id = book["id"]
        self.book_ids_to_delete.append(book_id)
        
        # Check that the book was created with the correct data
        self.assertEqual(book["title"], self.test_book_data["title"])
        self.assertEqual(book["author"], self.test_book_data["author"])
        self.assertEqual(book["category"], self.test_book_data["category"])
        print(f"✅ CREATE: Successfully created book: {book['title']} by {book['author']}")
        
        # READ - Test retrieving the created book
        response = requests.get(f"{API_URL}/books/{book_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        retrieved_book = response.json()
        self.assertEqual(retrieved_book["id"], book_id)
        self.assertEqual(retrieved_book["title"], self.test_book_data["title"])
        print(f"✅ READ: Successfully retrieved book: {retrieved_book['title']}")
        
        # READ ALL - Test retrieving all books
        response = requests.get(f"{API_URL}/books", headers=headers)
        self.assertEqual(response.status_code, 200)
        books = response.json()
        self.assertGreaterEqual(len(books), 1)
        print(f"✅ READ ALL: Successfully retrieved {len(books)} books")
        
        # UPDATE - Test updating the book
        update_data = {
            "status": "reading",
            "current_page": 42,
            "description": "Un magnifique conte philosophique"
        }
        response = requests.put(f"{API_URL}/books/{book_id}", json=update_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        updated_book = response.json()
        
        # Check that the book was updated correctly
        self.assertEqual(updated_book["status"], "reading")
        self.assertEqual(updated_book["current_page"], 42)
        self.assertEqual(updated_book["description"], "Un magnifique conte philosophique")
        print(f"✅ UPDATE: Successfully updated book status to '{updated_book['status']}' and current page to {updated_book['current_page']}")
        
        # DELETE - Test deleting the book
        response = requests.delete(f"{API_URL}/books/{book_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        
        # Verify the book was deleted
        response = requests.get(f"{API_URL}/books/{book_id}", headers=headers)
        self.assertEqual(response.status_code, 404)
        
        # Remove from cleanup list since we already deleted it
        self.book_ids_to_delete.remove(book_id)
        print(f"✅ DELETE: Successfully deleted book")

    def test_3_open_library_search(self):
        """Test Open Library search functionality"""
        self.assertIsNotNone(self.auth_token, "Authentication token should be obtained during setup")
        
        if not self.auth_token:
            self.fail("No authentication token available")
            return
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Test basic search
        search_term = "Harry Potter"
        response = requests.get(f"{API_URL}/openlibrary/search?q={search_term}&limit=5", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("books", data)
        self.assertIn("total_found", data)
        self.assertGreater(data["total_found"], 0)
        self.assertGreater(len(data["books"]), 0)
        
        # Check that the first book has all required fields
        first_book = data["books"][0]
        self.assertIn("ol_key", first_book)
        self.assertIn("title", first_book)
        self.assertIn("author", first_book)
        self.assertIn("category", first_book)
        
        print(f"✅ Open Library search works for '{search_term}', found {data['total_found']} books")
        
        # Test search with filters
        search_term = "Lord of the Rings"
        response = requests.get(
            f"{API_URL}/openlibrary/search?q={search_term}&limit=3&year_start=1950&year_end=1970", 
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("books", data)
        self.assertIn("filters_applied", data)
        self.assertIn("year_range", data["filters_applied"])
        
        print(f"✅ Open Library search with filters works for '{search_term}'")
        
        # Test ISBN search
        isbn = "9780747532743"  # Harry Potter and the Philosopher's Stone
        response = requests.get(f"{API_URL}/openlibrary/search-isbn?isbn={isbn}", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn("book", data)
        self.assertIn("found", data)
        self.assertTrue(data["found"])
        
        book = data["book"]
        self.assertIn("title", book)
        self.assertIn("author", book)
        
        print(f"✅ Open Library ISBN search works for '{isbn}', found: {book['title']}")

    def test_4_user_statistics(self):
        """Test retrieving user statistics"""
        self.assertIsNotNone(self.auth_token, "Authentication token should be obtained during setup")
        
        if not self.auth_token:
            self.fail("No authentication token available")
            return
            
        headers = {"Authorization": f"Bearer {self.auth_token}"}
        
        # Get initial stats
        response = requests.get(f"{API_URL}/stats", headers=headers)
        self.assertEqual(response.status_code, 200)
        stats = response.json()
        
        # Check that all required fields are present
        required_fields = [
            "total_books", "completed_books", "reading_books", "to_read_books", 
            "categories", "authors_count", "sagas_count", "auto_added_count"
        ]
        for field in required_fields:
            self.assertIn(field, stats)
        
        # Check that categories contains the expected subcategories
        self.assertIn("roman", stats["categories"])
        self.assertIn("bd", stats["categories"])
        self.assertIn("manga", stats["categories"])
        
        initial_total = stats["total_books"]
        print(f"✅ Stats endpoint working, user has {initial_total} books")
        print(f"   - {stats['completed_books']} completed, {stats['reading_books']} reading, {stats['to_read_books']} to read")
        print(f"   - {stats['categories']['roman']} romans, {stats['categories']['bd']} BD, {stats['categories']['manga']} mangas")
        print(f"   - {stats['authors_count']} authors, {stats['sagas_count']} sagas, {stats['auto_added_count']} auto-added")
        
        # Add a book and check that stats are updated
        response = requests.post(f"{API_URL}/books", json=self.test_book_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        book = response.json()
        self.book_ids_to_delete.append(book["id"])
        
        # Get updated stats
        response = requests.get(f"{API_URL}/stats", headers=headers)
        self.assertEqual(response.status_code, 200)
        updated_stats = response.json()
        
        # Check that total books increased by 1
        self.assertEqual(updated_stats["total_books"], initial_total + 1)
        # Check that to_read books increased by 1 (default status)
        self.assertEqual(updated_stats["to_read_books"], stats["to_read_books"] + 1)
        # Check that roman count increased by 1
        self.assertEqual(updated_stats["categories"]["roman"], stats["categories"]["roman"] + 1)
        
        print(f"✅ Stats update correctly after adding a book")
        print(f"   - Total books: {updated_stats['total_books']} (+1)")
        print(f"   - To read books: {updated_stats['to_read_books']} (+1)")
        print(f"   - Roman books: {updated_stats['categories']['roman']} (+1)")


if __name__ == "__main__":
    unittest.main(verbosity=2)