import requests
import json
import unittest
import uuid
import time
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://ac7e2eb9-934f-4dd0-be04-a2d67e65866e.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class BooktimeAPIAuditTest(unittest.TestCase):
    """Audit test suite for the Booktime API"""

    def setUp(self):
        """Setup for each test"""
        # Create a unique test user for this audit
        timestamp = int(time.time())
        self.test_user = {
            "first_name": "Audit",
            "last_name": f"User{timestamp}"
        }
        self.access_token = None
        self.headers = {}
        
        # Test book data
        self.test_book_data = {
            "title": f"Test Book {timestamp}",
            "author": "Test Author",
            "category": "roman",
            "description": "A test book for audit purposes"
        }
        
        # Book IDs to be cleaned up
        self.book_ids_to_delete = []

    def tearDown(self):
        """Clean up after each test"""
        # Delete any books created during testing
        if self.access_token:
            for book_id in self.book_ids_to_delete:
                try:
                    requests.delete(
                        f"{API_URL}/books/{book_id}", 
                        headers=self.headers
                    )
                except:
                    pass

    def test_health_check(self):
        """Test the health check endpoint"""
        response = requests.get(f"{BACKEND_URL}/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check required fields
        self.assertIn("status", data)
        self.assertIn("database", data)
        self.assertIn("timestamp", data)
        
        # Check values
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["database"], "connected")
        
        print("✅ Health check endpoint is working correctly")

    def test_user_registration(self):
        """Test user registration"""
        print(f"Attempting to register user: {self.test_user}")
        response = requests.post(f"{API_URL}/auth/register", json=self.test_user)
        print(f"Registration response status code: {response.status_code}")
        print(f"Registration response body: {response.text}")
        
        # If user already exists, try to login instead
        if response.status_code == 400 and "existe déjà" in response.text:
            print("User already exists, trying to login instead")
            return self.test_user_login()
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check required fields
        self.assertIn("access_token", data)
        self.assertIn("token_type", data)
        self.assertIn("user", data)
        
        # Save token for subsequent tests
        self.access_token = data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Check user data
        user = data["user"]
        self.assertEqual(user["first_name"], self.test_user["first_name"])
        self.assertEqual(user["last_name"], self.test_user["last_name"])
        
        print(f"✅ User registration is working correctly. Created user: {self.test_user['first_name']} {self.test_user['last_name']}")
        return True

    def test_user_login(self):
        """Test user login"""
        # Skip if we already have a token
        if self.access_token:
            print("Already logged in, skipping login test")
            return True
            
        print(f"Attempting to login with user: {self.test_user}")
        response = requests.post(f"{API_URL}/auth/login", json=self.test_user)
        print(f"Login response status code: {response.status_code}")
        print(f"Login response body: {response.text}")
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check required fields
        self.assertIn("access_token", data)
        self.assertIn("token_type", data)
        self.assertIn("user", data)
        
        # Update token
        self.access_token = data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.access_token}"}
        
        # Check user data
        user = data["user"]
        self.assertEqual(user["first_name"], self.test_user["first_name"])
        self.assertEqual(user["last_name"], self.test_user["last_name"])
        
        print(f"✅ User login is working correctly for user: {self.test_user['first_name']} {self.test_user['last_name']}")
        return True

    def test_get_current_user(self):
        """Test getting current user info"""
        # First register/login if not already done
        if not self.access_token:
            if not self.test_user_registration():
                self.skipTest("Registration/login failed, skipping test")
        
        # Get current user
        response = requests.get(f"{API_URL}/auth/me", headers=self.headers)
        print(f"Get current user response status code: {response.status_code}")
        print(f"Get current user response body: {response.text}")
        
        self.assertEqual(response.status_code, 200)
        user = response.json()
        
        # Check user data
        self.assertEqual(user["first_name"], self.test_user["first_name"])
        self.assertEqual(user["last_name"], self.test_user["last_name"])
        
        print(f"✅ Get current user endpoint is working correctly")

    def test_create_book(self):
        """Test creating a new book"""
        # First register/login if not already done
        if not self.access_token:
            if not self.test_user_registration():
                self.skipTest("Registration/login failed, skipping test")
        
        # Create a book
        print(f"Creating book with data: {self.test_book_data}")
        response = requests.post(
            f"{API_URL}/books", 
            json=self.test_book_data,
            headers=self.headers
        )
        print(f"Create book response status code: {response.status_code}")
        print(f"Create book response body: {response.text}")
        
        self.assertEqual(response.status_code, 200)
        book = response.json()
        
        # Save book ID for cleanup
        self.book_ids_to_delete.append(book["id"])
        
        # Check book data
        self.assertEqual(book["title"], self.test_book_data["title"])
        self.assertEqual(book["author"], self.test_book_data["author"])
        self.assertEqual(book["category"], self.test_book_data["category"])
        self.assertEqual(book["status"], "to_read")  # Default status
        
        print(f"✅ Create book endpoint is working correctly")

    def test_get_books(self):
        """Test getting all books"""
        # First register/login if not already done
        if not self.access_token:
            if not self.test_user_registration():
                self.skipTest("Registration/login failed, skipping test")
        
        # Create a book first to ensure we have at least one
        try:
            self.test_create_book()
        except Exception as e:
            print(f"Error creating test book: {e}")
        
        # Get all books
        response = requests.get(f"{API_URL}/books", headers=self.headers)
        print(f"Get books response status code: {response.status_code}")
        print(f"Get books response body: {response.text[:200]}...")  # Show just the beginning
        
        self.assertEqual(response.status_code, 200)
        books = response.json()
        
        # For a new user, we should have at least the book we just created
        self.assertGreaterEqual(len(books), 1)
        
        # Check that our test book is in the list
        test_book = next((b for b in books if b["id"] in self.book_ids_to_delete), None)
        self.assertIsNotNone(test_book)
        
        print(f"✅ Get books endpoint is working correctly. Found {len(books)} books.")

    def test_get_stats(self):
        """Test getting user statistics"""
        # First register/login if not already done
        if not self.access_token:
            if not self.test_user_registration():
                self.skipTest("Registration/login failed, skipping test")
        
        # Create a book first to ensure we have some stats
        try:
            self.test_create_book()
        except Exception as e:
            print(f"Error creating test book: {e}")
        
        # Get stats
        response = requests.get(f"{API_URL}/stats", headers=self.headers)
        print(f"Get stats response status code: {response.status_code}")
        print(f"Get stats response body: {response.text}")
        
        self.assertEqual(response.status_code, 200)
        stats = response.json()
        
        # Check required fields
        required_fields = [
            "total_books", "completed_books", "reading_books", 
            "to_read_books", "categories", "authors_count", 
            "sagas_count", "auto_added_count"
        ]
        for field in required_fields:
            self.assertIn(field, stats)
        
        # For a new user with one book, we should have specific stats
        self.assertGreaterEqual(stats["total_books"], 1)
        self.assertGreaterEqual(stats["to_read_books"], 1)  # Our book is "to_read"
        self.assertGreaterEqual(stats["categories"]["roman"], 1)  # Our book is "roman"
        
        print(f"✅ Get stats endpoint is working correctly")

    def test_open_library_search(self):
        """Test searching books on Open Library"""
        # First register/login if not already done
        if not self.access_token:
            if not self.test_user_registration():
                self.skipTest("Registration/login failed, skipping test")
        
        # Search for Harry Potter
        response = requests.get(
            f"{API_URL}/openlibrary/search?q=harry potter",
            headers=self.headers
        )
        print(f"Open Library search response status code: {response.status_code}")
        print(f"Open Library search response body: {response.text[:200]}...")  # Show just the beginning
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check required fields
        self.assertIn("books", data)
        self.assertIn("total_found", data)
        
        # Should find many Harry Potter books
        self.assertGreater(data["total_found"], 100)
        self.assertGreater(len(data["books"]), 0)
        
        # Check book data
        if data["books"]:
            book = data["books"][0]
            self.assertIn("title", book)
            self.assertIn("author", book)
            self.assertIn("category", book)
            self.assertIn("cover_url", book)
            
            # At least one book should have "Harry Potter" in the title
            harry_potter_book = next((b for b in data["books"] if "Harry Potter" in b["title"]), None)
            self.assertIsNotNone(harry_potter_book)
        
        print(f"✅ Open Library search endpoint is working correctly. Found {data['total_found']} books for 'Harry Potter'")

def run_audit_tests():
    """Run all audit tests"""
    # Create a test suite with all tests
    suite = unittest.TestSuite()
    suite.addTest(BooktimeAPIAuditTest('test_health_check'))
    suite.addTest(BooktimeAPIAuditTest('test_user_registration'))
    suite.addTest(BooktimeAPIAuditTest('test_user_login'))
    suite.addTest(BooktimeAPIAuditTest('test_get_current_user'))
    suite.addTest(BooktimeAPIAuditTest('test_create_book'))
    suite.addTest(BooktimeAPIAuditTest('test_get_books'))
    suite.addTest(BooktimeAPIAuditTest('test_get_stats'))
    suite.addTest(BooktimeAPIAuditTest('test_open_library_search'))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n=== AUDIT TEST SUMMARY ===")
    print(f"Tests run: {result.testsRun}")
    print(f"Errors: {len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    
    if result.wasSuccessful():
        print("\n✅ All audit tests passed successfully!")
    else:
        print("\n❌ Some audit tests failed:")
        for i, failure in enumerate(result.failures):
            print(f"\nFailure {i+1}: {failure[0]}")
            print(f"Error message: {failure[1]}")
        for i, error in enumerate(result.errors):
            print(f"\nError {i+1}: {error[0]}")
            print(f"Error message: {error[1]}")

if __name__ == "__main__":
    run_audit_tests()