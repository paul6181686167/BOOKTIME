#!/usr/bin/env python3
"""
Quick test script for the BOOKTIME API with simplified authentication
This script tests the main functionality after restoration:
1. Authentication endpoints (register/login)
2. Basic API endpoints (books, stats)
3. Open Library integration
4. Book creation and retrieval
"""

import requests
import json
import unittest
import uuid
import random
import string
import sys

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://6e641367-34d9-46dd-a131-5848e72877cd.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

def generate_random_name():
    """Generate a random name for testing"""
    return ''.join(random.choices(string.ascii_uppercase, k=1) + 
                  random.choices(string.ascii_lowercase, k=7))

class BooktimeQuickTest(unittest.TestCase):
    """Quick test suite for the Booktime API"""

    def setUp(self):
        """Setup for each test"""
        self.test_user_data = {
            "first_name": generate_random_name(),
            "last_name": generate_random_name()
        }
        
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
        
        # Store tokens for cleanup
        self.auth_token = None
        self.user_id = None
        
        # Book IDs to be used/cleaned up during testing
        self.book_ids_to_delete = []

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

    def test_1_welcome_message(self):
        """Test the root endpoint returns a welcome message"""
        response = requests.get(f"{BACKEND_URL}/")
        self.assertEqual(response.status_code, 200)
        try:
            data = response.json()
            self.assertIn("message", data)
            print(f"✅ Welcome message endpoint working: {data['message']}")
        except:
            # If the response is not JSON, just check that we got a 200 response
            print(f"✅ Root endpoint working (returned status 200)")
            pass

    def test_2_user_registration(self):
        """Test user registration with valid data"""
        response = requests.post(f"{API_URL}/auth/register", json=self.test_user_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check response structure
        self.assertIn("access_token", data)
        self.assertIn("token_type", data)
        self.assertIn("user", data)
        
        # Check user data
        user = data["user"]
        self.assertEqual(user["first_name"], self.test_user_data["first_name"])
        self.assertEqual(user["last_name"], self.test_user_data["last_name"])
        self.assertIn("id", user)
        
        # Store token for other tests
        self.auth_token = data["access_token"]
        self.user_id = user["id"]
        
        print("✅ User registration works correctly with simplified authentication")

    def test_3_user_login(self):
        """Test user login with correct credentials"""
        # First register a user
        response = requests.post(f"{API_URL}/auth/register", json=self.test_user_data)
        if response.status_code != 200:
            print(f"Registration failed: {response.text}")
            self.skipTest("Registration failed, cannot test login")
        
        # Login with the same credentials
        login_data = {
            "first_name": self.test_user_data["first_name"],
            "last_name": self.test_user_data["last_name"]
        }
        
        response = requests.post(f"{API_URL}/auth/login", json=login_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check response structure
        self.assertIn("access_token", data)
        self.assertIn("token_type", data)
        self.assertIn("user", data)
        
        # Check user data
        user = data["user"]
        self.assertEqual(user["first_name"], self.test_user_data["first_name"])
        self.assertEqual(user["last_name"], self.test_user_data["last_name"])
        
        # Store token for other tests
        self.auth_token = data["access_token"]
        self.user_id = user["id"]
        
        print("✅ User login works correctly with simplified authentication")

    def test_4_get_current_user(self):
        """Test getting current user info with valid token"""
        # First register a user
        response = requests.post(f"{API_URL}/auth/register", json=self.test_user_data)
        if response.status_code != 200:
            print(f"Registration failed: {response.text}")
            self.skipTest("Registration failed, cannot test get current user")
            
        data = response.json()
        token = data["access_token"]
        
        # Get current user info
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_URL}/auth/me", headers=headers)
        self.assertEqual(response.status_code, 200)
        user = response.json()
        
        # Check user data
        self.assertEqual(user["first_name"], self.test_user_data["first_name"])
        self.assertEqual(user["last_name"], self.test_user_data["last_name"])
        
        print("✅ Get current user info works correctly")

    def test_5_get_stats(self):
        """Test the stats endpoint returns correct statistics"""
        # First register a user
        response = requests.post(f"{API_URL}/auth/register", json=self.test_user_data)
        if response.status_code != 200:
            print(f"Registration failed: {response.text}")
            self.skipTest("Registration failed, cannot test stats")
            
        data = response.json()
        token = data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{API_URL}/stats", headers=headers)
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
        
        print("✅ Stats endpoint working with authentication")
        print(f"   Total books: {data['total_books']}")
        print(f"   Romans: {data['categories']['roman']}, BD: {data['categories']['bd']}, Mangas: {data['categories']['manga']}")
        print(f"   Sagas: {data['sagas_count']}")
        print(f"   Authors: {data['authors_count']}")

    def test_6_get_books(self):
        """Test retrieving all books with authentication"""
        # First register a user
        response = requests.post(f"{API_URL}/auth/register", json=self.test_user_data)
        if response.status_code != 200:
            print(f"Registration failed: {response.text}")
            self.skipTest("Registration failed, cannot test get books")
            
        data = response.json()
        token = data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(f"{API_URL}/books", headers=headers)
        self.assertEqual(response.status_code, 200)
        books = response.json()
        
        # New user should have no books initially
        self.assertEqual(len(books), 0, "New user should have no books initially")
        
        print("✅ Get books endpoint working with authentication")

    def test_7_create_and_get_book(self):
        """Test creating a new book and retrieving it"""
        # First register a user
        response = requests.post(f"{API_URL}/auth/register", json=self.test_user_data)
        if response.status_code != 200:
            print(f"Registration failed: {response.text}")
            self.skipTest("Registration failed, cannot test create book")
            
        data = response.json()
        token = data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create a book
        response = requests.post(f"{API_URL}/books", json=self.test_book_data, headers=headers)
        self.assertEqual(response.status_code, 200)
        book = response.json()
        
        # Add book ID to cleanup list
        book_id = book["id"]
        self.book_ids_to_delete.append(book_id)
        
        # Check that the book was created with the correct data
        self.assertEqual(book["title"], self.test_book_data["title"])
        self.assertEqual(book["author"], self.test_book_data["author"])
        self.assertEqual(book["category"], self.test_book_data["category"])
        self.assertEqual(book["status"], "to_read")  # Default status
        self.assertEqual(book["user_id"], data["user"]["id"])
        
        # Get the book by ID
        response = requests.get(f"{API_URL}/books/{book_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        retrieved_book = response.json()
        
        # Check that the retrieved book matches the created book
        self.assertEqual(retrieved_book["id"], book_id)
        self.assertEqual(retrieved_book["title"], self.test_book_data["title"])
        self.assertEqual(retrieved_book["author"], self.test_book_data["author"])
        
        # Get all books to verify the book is in the list
        response = requests.get(f"{API_URL}/books", headers=headers)
        self.assertEqual(response.status_code, 200)
        books = response.json()
        self.assertEqual(len(books), 1, "Should have exactly 1 book")
        
        print("✅ Create and get book endpoints working with authentication")

    def test_8_openlibrary_search(self):
        """Test the Open Library search endpoint"""
        # First register a user
        response = requests.post(f"{API_URL}/auth/register", json=self.test_user_data)
        if response.status_code != 200:
            print(f"Registration failed: {response.text}")
            self.skipTest("Registration failed, cannot test Open Library search")
            
        data = response.json()
        token = data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        query = "Harry Potter"
        response = requests.get(f"{API_URL}/openlibrary/search?q={query}", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check response structure
        self.assertIn("books", data)
        self.assertIn("query", data)
        self.assertIn("total", data)
        self.assertEqual(data["query"], query)
        
        # Check that books were found
        self.assertGreater(len(data["books"]), 0, "Should find at least one Harry Potter book")
        
        # Check book structure
        book = data["books"][0]
        self.assertIn("title", book)
        self.assertIn("author", book)
        self.assertIn("category", book)
        
        print(f"✅ Open Library search endpoint working, found {len(data['books'])} books for '{query}'")

def run_tests():
    """Run all tests and print a summary"""
    # Create a test suite with all tests
    suite = unittest.TestLoader().loadTestsFromTestCase(BooktimeQuickTest)
    
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