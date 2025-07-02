#!/usr/bin/env python3
"""
Authentication test script for the BOOKTIME API with simplified authentication
This script tests all authentication-related endpoints using first_name and last_name only
"""

import requests
import json
import unittest
import uuid
from datetime import datetime
import sys
import random
import string

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://176ce24c-0b0e-40df-bd2e-39594d81d3da.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

def generate_random_name():
    """Generate a random name for testing"""
    return ''.join(random.choices(string.ascii_uppercase, k=1) + 
                  random.choices(string.ascii_lowercase, k=7))

class BooktimeSimplifiedAuthTest(unittest.TestCase):
    """Test suite for the Booktime API Simplified Authentication (first_name and last_name only)"""

    def setUp(self):
        """Setup for each test"""
        self.test_user_data = {
            "first_name": generate_random_name(),
            "last_name": generate_random_name()
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

    def test_1_user_registration(self):
        """Test user registration with valid data (first_name and last_name only)"""
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
        
        print("✅ User registration works correctly with first_name and last_name only")

    def test_2_register_duplicate_user(self):
        """Test registration with existing first_name and last_name (should fail)"""
        # First register a user
        response = requests.post(f"{API_URL}/auth/register", json=self.test_user_data)
        self.assertEqual(response.status_code, 200)
        
        # Try to register again with the same first_name and last_name
        response = requests.post(f"{API_URL}/auth/register", json=self.test_user_data)
        self.assertEqual(response.status_code, 400)
        
        print("✅ Registration with existing first_name and last_name fails as expected")

    def test_3_register_missing_fields(self):
        """Test registration with missing required fields"""
        required_fields = ["first_name", "last_name"]
        
        for field in required_fields:
            invalid_user = self.test_user_data.copy()
            del invalid_user[field]
            
            response = requests.post(f"{API_URL}/auth/register", json=invalid_user)
            self.assertEqual(response.status_code, 422)
            
        print("✅ Registration with missing fields fails as expected")

    def test_4_user_login(self):
        """Test user login with correct credentials (first_name and last_name only)"""
        # First register a user
        response = requests.post(f"{API_URL}/auth/register", json=self.test_user_data)
        self.assertEqual(response.status_code, 200)
        
        # Login with correct credentials
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
        
        print("✅ User login works correctly with first_name and last_name only")

    def test_5_login_nonexistent_user(self):
        """Test login with non-existent user"""
        login_data = {
            "first_name": "Nonexistent",
            "last_name": "User"
        }
        
        response = requests.post(f"{API_URL}/auth/login", json=login_data)
        self.assertEqual(response.status_code, 400)
        
        print("✅ Login with non-existent user fails as expected")

    def test_6_get_current_user(self):
        """Test getting current user info with valid token"""
        # First register a user
        response = requests.post(f"{API_URL}/auth/register", json=self.test_user_data)
        self.assertEqual(response.status_code, 200)
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

    def test_7_get_user_invalid_token(self):
        """Test getting user info with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = requests.get(f"{API_URL}/auth/me", headers=headers)
        self.assertEqual(response.status_code, 401)
        
        print("✅ Get user info with invalid token fails as expected")

    def test_8_get_user_no_token(self):
        """Test getting user info without token"""
        response = requests.get(f"{API_URL}/auth/me")
        self.assertIn(response.status_code, [401, 403])
        
        print("✅ Get user info without token fails as expected")

    def test_9_protected_books_endpoint(self):
        """Test that books endpoint requires authentication"""
        # Try without token
        response = requests.get(f"{API_URL}/books")
        self.assertIn(response.status_code, [401, 403])
        
        # Register and get token
        response = requests.post(f"{API_URL}/auth/register", json=self.test_user_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        token = data["access_token"]
        
        # Try with token
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{API_URL}/books", headers=headers)
        self.assertEqual(response.status_code, 200)
        
        print("✅ Books endpoint requires authentication")

    def test_10_user_specific_books(self):
        """Test that users only see their own books"""
        # Create two users
        user1_data = {
            "first_name": generate_random_name(),
            "last_name": generate_random_name()
        }
        
        user2_data = {
            "first_name": generate_random_name(),
            "last_name": generate_random_name()
        }
        
        # Register user 1
        response = requests.post(f"{API_URL}/auth/register", json=user1_data)
        self.assertEqual(response.status_code, 200)
        user1 = response.json()
        user1_token = user1["access_token"]
        
        # Register user 2
        response = requests.post(f"{API_URL}/auth/register", json=user2_data)
        self.assertEqual(response.status_code, 200)
        user2 = response.json()
        user2_token = user2["access_token"]
        
        # Create a book for user 1
        book_data = {
            "title": "User 1's Book",
            "author": "Test Author",
            "category": "roman"
        }
        
        headers1 = {"Authorization": f"Bearer {user1_token}"}
        response = requests.post(f"{API_URL}/books", json=book_data, headers=headers1)
        self.assertEqual(response.status_code, 200)
        user1_book = response.json()
        
        # Create a book for user 2
        book_data = {
            "title": "User 2's Book",
            "author": "Test Author",
            "category": "roman"
        }
        
        headers2 = {"Authorization": f"Bearer {user2_token}"}
        response = requests.post(f"{API_URL}/books", json=book_data, headers=headers2)
        self.assertEqual(response.status_code, 200)
        user2_book = response.json()
        
        # User 1 should see only their book
        response = requests.get(f"{API_URL}/books", headers=headers1)
        self.assertEqual(response.status_code, 200)
        books = response.json()
        
        # Find user1's book in the list
        user1_book_found = False
        user2_book_found = False
        
        for book in books:
            if book["id"] == user1_book["id"]:
                user1_book_found = True
            if "id" in book and book["id"] == user2_book["id"]:
                user2_book_found = True
        
        self.assertTrue(user1_book_found, "User 1 should see their own book")
        self.assertFalse(user2_book_found, "User 1 should not see User 2's book")
        
        # User 2 should see only their book
        response = requests.get(f"{API_URL}/books", headers=headers2)
        self.assertEqual(response.status_code, 200)
        books = response.json()
        
        # Find user2's book in the list
        user1_book_found = False
        user2_book_found = False
        
        for book in books:
            if "id" in book and book["id"] == user1_book["id"]:
                user1_book_found = True
            if book["id"] == user2_book["id"]:
                user2_book_found = True
        
        self.assertFalse(user1_book_found, "User 2 should not see User 1's book")
        self.assertTrue(user2_book_found, "User 2 should see their own book")
        
        # Clean up - delete the books
        requests.delete(f"{API_URL}/books/{user1_book['id']}", headers=headers1)
        requests.delete(f"{API_URL}/books/{user2_book['id']}", headers=headers2)
        
        print("✅ Users only see their own books")

def run_tests():
    """Run all tests and print a summary"""
    # Create a test suite with all tests
    suite = unittest.TestLoader().loadTestsFromTestCase(BooktimeSimplifiedAuthTest)
    
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