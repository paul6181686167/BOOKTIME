import requests
import json
import unittest
import uuid
from datetime import datetime
import random
import string
import sys

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://725329fe-87ed-4368-b332-4714bc34f0f3.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

def generate_random_email():
    """Generate a random email for testing"""
    random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"test_{random_string}@example.com"

class BooktimeAPITest(unittest.TestCase):
    """Test suite for the Booktime API"""

    def setUp(self):
        """Setup for each test"""
        # Generate random credentials for testing
        self.test_email = generate_random_email()
        self.test_password = "TestPassword123!"
        self.test_first_name = "Test"
        self.test_last_name = "User"
        
        # Test book data
        self.test_book_data = {
            "title": "Le Petit Prince",
            "author": "Antoine de Saint-Exupéry",
            "category": "roman",
            "description": "Un conte philosophique sous forme d'un récit pour enfants",
            "cover_url": "https://example.com/petit-prince.jpg",
            "saga": "",
            "status": "to_read"
        }
        
        # Book IDs to be used/cleaned up during testing
        self.book_ids_to_delete = []
        self.access_token = None

    def tearDown(self):
        """Clean up after each test"""
        # Delete any books created during testing
        if self.access_token:
            for book_id in self.book_ids_to_delete:
                try:
                    headers = {'Authorization': f'Bearer {self.access_token}'}
                    requests.delete(f"{API_URL}/books/{book_id}", headers=headers)
                except:
                    pass

    def test_health_check(self):
        """Test the health endpoint returns OK status"""
        response = requests.get(f"{BACKEND_URL}/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("status", data)
        self.assertEqual(data["status"], "ok")
        print("✅ Health check endpoint working")

    def test_register_and_login(self):
        """Test user registration and login"""
        # Test registration
        register_data = {
            "email": self.test_email,
            "password": self.test_password,
            "first_name": self.test_first_name,
            "last_name": self.test_last_name
        }
        
        response = requests.post(f"{API_URL}/auth/register", json=register_data)
        self.assertEqual(response.status_code, 200, f"Registration failed: {response.text}")
        data = response.json()
        
        # Check that registration returns a token and user data
        self.assertIn("access_token", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["email"], self.test_email)
        self.assertEqual(data["user"]["first_name"], self.test_first_name)
        self.assertEqual(data["user"]["last_name"], self.test_last_name)
        
        # Save token for later tests
        self.access_token = data["access_token"]
        print("✅ Registration endpoint working")
        
        # Test login with the same credentials
        login_data = {
            "email": self.test_email,
            "password": self.test_password
        }
        
        response = requests.post(f"{API_URL}/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200, f"Login failed: {response.text}")
        data = response.json()
        
        # Check that login returns a token and user data
        self.assertIn("access_token", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["email"], self.test_email)
        
        # Update token for later tests
        self.access_token = data["access_token"]
        print("✅ Login endpoint working")

    def test_auth_me(self):
        """Test the auth/me endpoint"""
        # First register to get a token
        self.test_register_and_login()
        
        # Test the auth/me endpoint
        headers = {'Authorization': f'Bearer {self.access_token}'}
        response = requests.get(f"{API_URL}/auth/me", headers=headers)
        self.assertEqual(response.status_code, 200, f"Auth/me failed: {response.text}")
        data = response.json()
        
        # Check that it returns the correct user data
        self.assertEqual(data["email"], self.test_email)
        self.assertEqual(data["first_name"], self.test_first_name)
        self.assertEqual(data["last_name"], self.test_last_name)
        print("✅ Auth/me endpoint working")

    def test_books_crud(self):
        """Test CRUD operations for books"""
        # First register to get a token
        self.test_register_and_login()
        headers = {'Authorization': f'Bearer {self.access_token}'}
        
        # Create a book
        response = requests.post(f"{API_URL}/books", json=self.test_book_data, headers=headers)
        self.assertEqual(response.status_code, 201, f"Create book failed: {response.text}")
        book = response.json()
        
        # Check that the book was created with the correct data
        self.assertEqual(book["title"], self.test_book_data["title"])
        self.assertEqual(book["author"], self.test_book_data["author"])
        self.assertEqual(book["category"], self.test_book_data["category"])
        
        # Save book ID for later tests and cleanup
        book_id = book["id"]
        self.book_ids_to_delete.append(book_id)
        print("✅ Create book endpoint working")
        
        # Get all books
        response = requests.get(f"{API_URL}/books", headers=headers)
        self.assertEqual(response.status_code, 200, f"Get books failed: {response.text}")
        books = response.json()
        
        # Check that our book is in the list
        book_ids = [b["id"] for b in books]
        self.assertIn(book_id, book_ids)
        print("✅ Get books endpoint working")
        
        # Update the book
        update_data = {
            "status": "reading",
            "description": "Updated description"
        }
        response = requests.put(f"{API_URL}/books/{book_id}", json=update_data, headers=headers)
        self.assertEqual(response.status_code, 200, f"Update book failed: {response.text}")
        updated_book = response.json()
        
        # Check that the book was updated correctly
        self.assertEqual(updated_book["status"], "reading")
        self.assertEqual(updated_book["description"], "Updated description")
        print("✅ Update book endpoint working")
        
        # Delete the book
        response = requests.delete(f"{API_URL}/books/{book_id}", headers=headers)
        self.assertEqual(response.status_code, 200, f"Delete book failed: {response.text}")
        
        # Verify the book was deleted
        response = requests.get(f"{API_URL}/books", headers=headers)
        books = response.json()
        book_ids = [b["id"] for b in books]
        self.assertNotIn(book_id, book_ids)
        
        # Remove from cleanup list since we already deleted it
        self.book_ids_to_delete.remove(book_id)
        print("✅ Delete book endpoint working")

    def test_stats(self):
        """Test the stats endpoint"""
        # First register to get a token
        self.test_register_and_login()
        headers = {'Authorization': f'Bearer {self.access_token}'}
        
        # Create a few books with different statuses
        books_data = [
            {
                "title": "Book 1",
                "author": "Author 1",
                "category": "roman",
                "status": "to_read"
            },
            {
                "title": "Book 2",
                "author": "Author 2",
                "category": "bd",
                "status": "reading"
            },
            {
                "title": "Book 3",
                "author": "Author 3",
                "category": "manga",
                "status": "completed"
            }
        ]
        
        for book_data in books_data:
            response = requests.post(f"{API_URL}/books", json=book_data, headers=headers)
            self.assertEqual(response.status_code, 201)
            book = response.json()
            self.book_ids_to_delete.append(book["id"])
        
        # Get stats
        response = requests.get(f"{API_URL}/stats", headers=headers)
        self.assertEqual(response.status_code, 200, f"Get stats failed: {response.text}")
        stats = response.json()
        
        # Check that stats include our books
        self.assertGreaterEqual(stats["total_books"], 3)
        self.assertGreaterEqual(stats["to_read_books"], 1)
        self.assertGreaterEqual(stats["reading_books"], 1)
        self.assertGreaterEqual(stats["completed_books"], 1)
        
        # Check categories
        self.assertGreaterEqual(stats["categories"]["roman"], 1)
        self.assertGreaterEqual(stats["categories"]["bd"], 1)
        self.assertGreaterEqual(stats["categories"]["manga"], 1)
        
        # Check authors count
        self.assertGreaterEqual(stats["authors_count"], 3)
        print("✅ Stats endpoint working")

    def test_openlibrary_search(self):
        """Test the OpenLibrary search endpoint"""
        # First register to get a token
        self.test_register_and_login()
        headers = {'Authorization': f'Bearer {self.access_token}'}
        
        # Search for a book
        query = "Harry Potter"
        response = requests.get(f"{API_URL}/openlibrary/search?q={query}", headers=headers)
        self.assertEqual(response.status_code, 200, f"OpenLibrary search failed: {response.text}")
        data = response.json()
        
        # Check that we got some results
        self.assertIn("books", data)
        self.assertIn("total", data)
        self.assertGreater(data["total"], 0)
        self.assertGreater(len(data["books"]), 0)
        
        # Check that the books have the expected fields
        book = data["books"][0]
        self.assertIn("title", book)
        self.assertIn("author", book)
        print("✅ OpenLibrary search endpoint working")

def run_tests():
    """Run the tests and return the result"""
    suite = unittest.TestLoader().loadTestsFromTestCase(BooktimeAPITest)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)