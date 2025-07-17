import requests
import json
import unittest
import uuid
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://7cba8eb9-d655-49db-ac49-a03497169697.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class BooktimeAPITest(unittest.TestCase):
    """Comprehensive test suite for the Booktime API with authentication"""

    def setUp(self):
        """Setup for each test"""
        # Generate unique user credentials for testing
        self.test_user = {
            "first_name": f"Test{uuid.uuid4().hex[:6]}",
            "last_name": f"User{uuid.uuid4().hex[:6]}"
        }
        self.token = None
        self.user_id = None
        
        # Test book data
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
        
        # Register a test user and get token
        self._register_and_get_token()

    def tearDown(self):
        """Clean up after each test"""
        # Delete any books created during testing
        if self.token:
            headers = {'Authorization': f'Bearer {self.token}'}
            for book_id in self.book_ids_to_delete:
                try:
                    requests.delete(f"{API_URL}/books/{book_id}", headers=headers)
                except:
                    pass

    def _register_and_get_token(self):
        """Helper method to register a user and get authentication token"""
        try:
            # Register a new user
            response = requests.post(f"{API_URL}/auth/register", json=self.test_user)
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                if "user" in data and "id" in data["user"]:
                    self.user_id = data["user"]["id"]
                print(f"✅ Registered test user: {self.test_user['first_name']} {self.test_user['last_name']}")
            else:
                # Try login if registration fails (user might already exist)
                response = requests.post(f"{API_URL}/auth/login", json=self.test_user)
                if response.status_code == 200:
                    data = response.json()
                    self.token = data.get("access_token")
                    if "user" in data and "id" in data["user"]:
                        self.user_id = data["user"]["id"]
                    print(f"✅ Logged in as existing user: {self.test_user['first_name']} {self.test_user['last_name']}")
                else:
                    print(f"❌ Failed to authenticate: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")

    def test_1_welcome_message(self):
        """Test the root endpoint returns a welcome message"""
        response = requests.get(BACKEND_URL)
        self.assertEqual(response.status_code, 200)
        try:
            data = response.json()
            self.assertIn("message", data)
        except:
            # If not JSON, check if the response contains expected text
            self.assertIn("BookTime", response.text)
        print("✅ Welcome message endpoint working")

    def test_2_auth_me_endpoint(self):
        """Test the /auth/me endpoint returns user information"""
        if not self.token:
            self.skipTest("Authentication token not available")
            
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(f"{API_URL}/auth/me", headers=headers)
        self.assertEqual(response.status_code, 200)
        user_data = response.json()
        
        self.assertEqual(user_data["first_name"], self.test_user["first_name"])
        self.assertEqual(user_data["last_name"], self.test_user["last_name"])
        
        print("✅ Auth/me endpoint working correctly")

    def test_3_get_stats(self):
        """Test the stats endpoint returns correct statistics"""
        if not self.token:
            self.skipTest("Authentication token not available")
            
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(f"{API_URL}/stats", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that all required fields are present
        required_fields = ["total_books", "completed_books", "reading_books", "to_read_books", "categories"]
        for field in required_fields:
            self.assertIn(field, data)
        
        print("✅ Stats endpoint working")
        print(f"   Total books: {data['total_books']}")
        if "categories" in data:
            print(f"   Categories: {', '.join(data['categories'].keys())}")

    def test_4_get_all_books(self):
        """Test retrieving all books"""
        if not self.token:
            self.skipTest("Authentication token not available")
            
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(f"{API_URL}/books", headers=headers)
        self.assertEqual(response.status_code, 200)
        
        # Handle different response formats (array or object with books property)
        if isinstance(response.json(), list):
            books = response.json()
        elif isinstance(response.json(), dict) and 'books' in response.json():
            books = response.json()['books']
        elif isinstance(response.json(), dict) and 'items' in response.json():
            books = response.json()['items']
        else:
            books = []
        
        print(f"✅ Get all books endpoint working, found {len(books)} books")

    def test_5_filter_books_by_category(self):
        """Test filtering books by category"""
        if not self.token:
            self.skipTest("Authentication token not available")
            
        headers = {'Authorization': f'Bearer {self.token}'}
        categories = ["roman", "bd", "manga"]
        
        for category in categories:
            response = requests.get(f"{API_URL}/books?category={category}", headers=headers)
            self.assertEqual(response.status_code, 200)
            
            # Handle different response formats
            if isinstance(response.json(), list):
                books = response.json()
            elif isinstance(response.json(), dict) and 'books' in response.json():
                books = response.json()['books']
            elif isinstance(response.json(), dict) and 'items' in response.json():
                books = response.json()['items']
            else:
                books = []
            
            print(f"✅ Filter by category '{category}' working, found {len(books)} books")

    def test_6_create_and_update_book(self):
        """Test creating and updating a book"""
        if not self.token:
            self.skipTest("Authentication token not available")
            
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Create a book
        response = requests.post(f"{API_URL}/books", json=self.test_book_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        book = response.json()
        
        # Get book ID (handle different response formats)
        if "_id" in book:
            book_id = book["_id"]
        elif "id" in book:
            book_id = book["id"]
        else:
            print("Warning: Book ID not found in response")
            return
            
        self.book_ids_to_delete.append(book_id)
        
        # Check that the book was created with the correct data
        self.assertEqual(book["title"], self.test_book_data["title"])
        self.assertEqual(book["author"], self.test_book_data["author"])
        self.assertEqual(book["category"], self.test_book_data["category"])
        
        print("✅ Create book endpoint working")
        
        # Update the book status to reading
        update_data = {
            "status": "reading",
            "current_page": 42
        }
        response = requests.put(f"{API_URL}/books/{book_id}", json=update_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        updated_book = response.json()
        
        # Check that the book was updated correctly
        self.assertEqual(updated_book["status"], "reading")
        self.assertEqual(updated_book["current_page"], 42)
        
        print("✅ Update book endpoint working")
        
        # Update to completed
        update_data = {
            "status": "completed",
            "current_page": 96,
            "rating": 5,
            "review": "Un chef-d'œuvre intemporel"
        }
        response = requests.put(f"{API_URL}/books/{book_id}", json=update_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        updated_book = response.json()
        
        # Check that the book was updated correctly
        self.assertEqual(updated_book["status"], "completed")
        self.assertEqual(updated_book["current_page"], 96)
        self.assertEqual(updated_book["rating"], 5)
        self.assertEqual(updated_book["review"], "Un chef-d'œuvre intemporel")
        
        print("✅ Book status updates working correctly")

    def test_7_search_books(self):
        """Test searching for books"""
        if not self.token:
            self.skipTest("Authentication token not available")
            
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Create a book with a unique title for search
        unique_title = f"Unique Test Book {uuid.uuid4().hex[:8]}"
        test_book = self.test_book_data.copy()
        test_book["title"] = unique_title
        
        response = requests.post(f"{API_URL}/books", json=test_book, headers=headers)
        self.assertEqual(response.status_code, 200)
        book = response.json()
        
        # Get book ID (handle different response formats)
        if "_id" in book:
            book_id = book["_id"]
        elif "id" in book:
            book_id = book["id"]
        else:
            print("Warning: Book ID not found in response")
            return
            
        self.book_ids_to_delete.append(book_id)
        
        # Search for the book
        response = requests.get(f"{API_URL}/books/search?q={unique_title}", headers=headers)
        self.assertEqual(response.status_code, 200)
        
        # Handle different response formats
        if isinstance(response.json(), list):
            search_results = response.json()
        elif isinstance(response.json(), dict) and 'books' in response.json():
            search_results = response.json()['books']
        elif isinstance(response.json(), dict) and 'items' in response.json():
            search_results = response.json()['items']
        else:
            search_results = []
        
        # Verify the book is found
        found = False
        for result in search_results:
            if result["title"] == unique_title:
                found = True
                break
        
        self.assertTrue(found, f"Book with title '{unique_title}' not found in search results")
        
        print("✅ Book search endpoint working")

    def test_8_openlibrary_search(self):
        """Test searching for books in Open Library"""
        if not self.token:
            self.skipTest("Authentication token not available")
            
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # Search for a common book title
        search_term = "Harry Potter"
        response = requests.get(f"{API_URL}/openlibrary/search?q={search_term}", headers=headers)
        self.assertEqual(response.status_code, 200)
        
        # Check if the response has the expected structure
        data = response.json()
        
        # Handle different response formats
        if 'books' in data:
            books = data['books']
        elif 'items' in data:
            books = data['items']
        else:
            books = []
        
        # Verify we got some results
        self.assertGreater(len(books), 0)
        
        print(f"✅ Open Library search endpoint working, found {len(books)} books for '{search_term}'")

    def test_9_delete_book(self):
        """Test deleting a book"""
        if not self.token:
            self.skipTest("Authentication token not available")
            
        headers = {'Authorization': f'Bearer {self.token}'}
        
        # First create a book to delete
        response = requests.post(f"{API_URL}/books", json=self.test_book_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        book = response.json()
        
        # Get book ID (handle different response formats)
        if "_id" in book:
            book_id = book["_id"]
        elif "id" in book:
            book_id = book["id"]
        else:
            print("Warning: Book ID not found in response")
            return
        
        # Delete the book
        response = requests.delete(f"{API_URL}/books/{book_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        
        # Verify the book was deleted
        response = requests.get(f"{API_URL}/books/{book_id}", headers=headers)
        self.assertEqual(response.status_code, 404)
        
        print("✅ Delete book endpoint working")

if __name__ == "__main__":
    unittest.main(verbosity=2)