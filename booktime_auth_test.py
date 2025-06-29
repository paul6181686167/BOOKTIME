import requests
import json
import unittest
import uuid
import time
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://8c7e2f13-c249-4384-9811-ccdf587ab2c4.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class BooktimeAuthAPITest(unittest.TestCase):
    """Test suite for the Booktime API Authentication and Book Endpoints"""

    def setUp(self):
        """Setup for each test"""
        # Generate unique test user
        timestamp = int(time.time())
        self.test_first_name = f"Test{timestamp}"
        self.test_last_name = f"User{timestamp}"
        
        # Test book data
        self.test_book_data = {
            "title": f"Test Book {timestamp}",
            "author": "Test Author",
            "category": "roman",
            "description": "A test book created during API testing",
            "total_pages": 200
        }
        
        # Store tokens and book IDs for cleanup
        self.token = None
        self.user_id = None
        self.book_ids_to_delete = []
        
        # Debug info
        print(f"\nUsing API URL: {API_URL}")

    def tearDown(self):
        """Clean up after each test"""
        # Delete any books created during testing
        if self.token:
            for book_id in self.book_ids_to_delete:
                try:
                    headers = {'Authorization': f'Bearer {self.token}'}
                    requests.delete(f"{API_URL}/books/{book_id}", headers=headers)
                except:
                    pass

    def test_1_register(self):
        """Test user registration with first_name and last_name"""
        print("\n🔍 Testing user registration...")
        
        # Register a new user
        user_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name
        }
        
        print(f"Sending registration request to {API_URL}/auth/register with data: {user_data}")
        
        try:
            response = requests.post(f"{API_URL}/auth/register", json=user_data)
            print(f"Response status code: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Response text: {response.text}")
            
            self.assertEqual(response.status_code, 200, f"Registration failed: {response.text}")
            
            data = response.json()
            self.assertIn("access_token", data, "No access token in response")
            self.assertIn("user", data, "No user data in response")
            self.assertIn("first_name", data["user"], "No first_name in user data")
            self.assertIn("last_name", data["user"], "No last_name in user data")
            
            # Store token for subsequent tests
            self.token = data["access_token"]
            self.user_id = data["user"]["id"]
            
            print(f"✅ User registered: {self.test_first_name} {self.test_last_name}")
            print(f"✅ Token received: {self.token[:10]}...")
            
        except Exception as e:
            print(f"❌ Exception during registration: {str(e)}")
            raise

    def test_2_login(self):
        """Test user login with first_name and last_name"""
        print("\n🔍 Testing user login...")
        
        # First register a user
        user_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name
        }
        
        # Register the user
        print(f"Registering user first: {user_data}")
        register_response = requests.post(f"{API_URL}/auth/register", json=user_data)
        print(f"Registration response: {register_response.status_code} - {register_response.text[:100]}...")
        
        if register_response.status_code != 200:
            self.skipTest(f"Registration failed with status {register_response.status_code}, skipping login test")
            return
        
        # Now try to login with the same credentials
        print(f"Attempting login with: {user_data}")
        login_response = requests.post(f"{API_URL}/auth/login", json=user_data)
        print(f"Login response: {login_response.status_code} - {login_response.text[:100]}...")
        
        self.assertEqual(login_response.status_code, 200, f"Login failed: {login_response.text}")
        
        data = login_response.json()
        self.assertIn("access_token", data, "No access token in response")
        self.assertIn("user", data, "No user data in response")
        self.assertIn("first_name", data["user"], "No first_name in user data")
        self.assertIn("last_name", data["user"], "No last_name in user data")
        
        # Store token for subsequent tests
        self.token = data["access_token"]
        self.user_id = data["user"]["id"]
        
        print(f"✅ User logged in: {self.test_first_name} {self.test_last_name}")
        print(f"✅ Token received: {self.token[:10]}...")

    def test_3_get_me(self):
        """Test getting current user info with valid token"""
        print("\n🔍 Testing get current user...")
        
        # First register a user
        user_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name
        }
        
        print(f"Registering user first: {user_data}")
        register_response = requests.post(f"{API_URL}/auth/register", json=user_data)
        print(f"Registration response: {register_response.status_code} - {register_response.text[:100]}...")
        
        if register_response.status_code != 200:
            self.skipTest(f"Registration failed with status {register_response.status_code}, skipping get_me test")
            return
        
        data = register_response.json()
        self.token = data["access_token"]
        
        # Now get current user info
        print(f"Getting user info with token: {self.token[:10]}...")
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(f"{API_URL}/auth/me", headers=headers)
        print(f"Get me response: {response.status_code} - {response.text[:100]}...")
        
        self.assertEqual(response.status_code, 200, f"Get current user failed: {response.text}")
        
        user_data = response.json()
        self.assertEqual(user_data["first_name"], self.test_first_name, "First name doesn't match")
        self.assertEqual(user_data["last_name"], self.test_last_name, "Last name doesn't match")
        
        print(f"✅ Current user info retrieved: {user_data['first_name']} {user_data['last_name']}")

    def test_4_get_books_with_auth(self):
        """Test getting books with authentication"""
        print("\n🔍 Testing get books with authentication...")
        
        # First register a user
        user_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name
        }
        
        print(f"Registering user first: {user_data}")
        register_response = requests.post(f"{API_URL}/auth/register", json=user_data)
        print(f"Registration response: {register_response.status_code} - {register_response.text[:100]}...")
        
        if register_response.status_code != 200:
            self.skipTest(f"Registration failed with status {register_response.status_code}, skipping get_books test")
            return
        
        data = register_response.json()
        self.token = data["access_token"]
        
        # Now get books
        print(f"Getting books with token: {self.token[:10]}...")
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(f"{API_URL}/books", headers=headers)
        print(f"Get books response: {response.status_code} - {response.text[:100]}...")
        
        self.assertEqual(response.status_code, 200, f"Get books failed: {response.text}")
        
        books = response.json()
        self.assertIsInstance(books, list, "Books response is not a list")
        
        print(f"✅ Books retrieved with authentication: {len(books)} books")

    def test_5_get_books_without_auth(self):
        """Test getting books without authentication (should fail)"""
        print("\n🔍 Testing get books without authentication...")
        
        response = requests.get(f"{API_URL}/books")
        self.assertNotEqual(response.status_code, 200, "Get books without auth should fail")
        self.assertIn(response.status_code, [401, 403], "Expected 401 or 403 status code")
        
        print("✅ Books endpoint correctly requires authentication")

    def test_6_get_stats_with_auth(self):
        """Test getting stats with authentication"""
        print("\n🔍 Testing get stats with authentication...")
        
        # First register a user
        user_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name
        }
        
        print(f"Registering user first: {user_data}")
        register_response = requests.post(f"{API_URL}/auth/register", json=user_data)
        print(f"Registration response: {register_response.status_code} - {register_response.text[:100]}...")
        
        if register_response.status_code != 200:
            self.skipTest(f"Registration failed with status {register_response.status_code}, skipping get_stats test")
            return
        
        data = register_response.json()
        self.token = data["access_token"]
        
        # Now get stats
        print(f"Getting stats with token: {self.token[:10]}...")
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.get(f"{API_URL}/stats", headers=headers)
        print(f"Get stats response: {response.status_code} - {response.text[:100]}...")
        
        self.assertEqual(response.status_code, 200, f"Get stats failed: {response.text}")
        
        stats = response.json()
        self.assertIn("total_books", stats, "No total_books in stats")
        self.assertIn("categories", stats, "No categories in stats")
        
        print(f"✅ Stats retrieved with authentication")
        print(f"   Total books: {stats['total_books']}")
        if 'categories' in stats:
            print(f"   Categories: {stats['categories']}")

    def test_7_create_book_with_auth(self):
        """Test creating a book with authentication"""
        print("\n🔍 Testing create book with authentication...")
        
        # First register a user
        user_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name
        }
        
        register_response = requests.post(f"{API_URL}/auth/register", json=user_data)
        self.assertEqual(register_response.status_code, 200, "Registration failed")
        
        data = register_response.json()
        self.token = data["access_token"]
        
        # Now create a book
        headers = {'Authorization': f'Bearer {self.token}'}
        response = requests.post(f"{API_URL}/books", json=self.test_book_data, headers=headers)
        self.assertEqual(response.status_code, 200, f"Create book failed: {response.text}")
        
        book = response.json()
        self.assertIn("id", book, "No id in book data")
        self.assertEqual(book["title"], self.test_book_data["title"], "Book title doesn't match")
        self.assertEqual(book["author"], self.test_book_data["author"], "Book author doesn't match")
        
        # Store book ID for cleanup
        self.book_ids_to_delete.append(book["id"])
        
        print(f"✅ Book created with authentication: {book['title']}")

    def test_8_invalid_token(self):
        """Test using an invalid token (should fail)"""
        print("\n🔍 Testing invalid token...")
        
        # Use an invalid token
        headers = {'Authorization': 'Bearer invalid_token_here'}
        response = requests.get(f"{API_URL}/books", headers=headers)
        self.assertNotEqual(response.status_code, 200, "Request with invalid token should fail")
        self.assertIn(response.status_code, [401, 403], "Expected 401 or 403 status code")
        
        print("✅ Invalid token correctly rejected")

    def test_9_duplicate_user(self):
        """Test registering a duplicate user (should fail)"""
        print("\n🔍 Testing duplicate user registration...")
        
        # First register a user
        user_data = {
            "first_name": self.test_first_name,
            "last_name": self.test_last_name
        }
        
        register_response = requests.post(f"{API_URL}/auth/register", json=user_data)
        self.assertEqual(register_response.status_code, 200, "First registration failed")
        
        # Try to register the same user again
        duplicate_response = requests.post(f"{API_URL}/auth/register", json=user_data)
        self.assertNotEqual(duplicate_response.status_code, 200, "Duplicate registration should fail")
        self.assertEqual(duplicate_response.status_code, 400, "Expected 400 status code")
        
        print("✅ Duplicate user registration correctly rejected")

    def test_10_login_nonexistent_user(self):
        """Test logging in with a non-existent user (should fail)"""
        print("\n🔍 Testing login with non-existent user...")
        
        # Try to login with a non-existent user
        user_data = {
            "first_name": "NonExistent",
            "last_name": "User"
        }
        
        login_response = requests.post(f"{API_URL}/auth/login", json=user_data)
        self.assertNotEqual(login_response.status_code, 200, "Login with non-existent user should fail")
        self.assertEqual(login_response.status_code, 400, "Expected 400 status code")
        
        print("✅ Login with non-existent user correctly rejected")

if __name__ == "__main__":
    unittest.main(verbosity=2)