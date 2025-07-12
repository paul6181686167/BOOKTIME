#!/usr/bin/env python3
"""
Modular Architecture Validation Test for BOOKTIME API
This script tests the modular architecture of the backend API
"""

import requests
import json
import unittest
import uuid
import time
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://579ff41b-7a86-4f34-b52b-3121e30e773f.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class BooktimeModularArchitectureTest(unittest.TestCase):
    """Test suite for the Booktime API modular architecture"""

    @classmethod
    def setUpClass(cls):
        """Setup once for all tests"""
        # Register a test user for all tests
        cls.test_user = {
            "first_name": f"TestUser{uuid.uuid4().hex[:6]}",
            "last_name": f"ModularTest{uuid.uuid4().hex[:6]}"
        }
        
        # Register the user and get the token
        response = requests.post(f"{API_URL}/auth/register", json=cls.test_user)
        if response.status_code == 200:
            data = response.json()
            cls.token = data["access_token"]
            cls.headers = {"Authorization": f"Bearer {cls.token}"}
            cls.user_id = data["user"]["id"]
            print(f"Created test user: {cls.test_user['first_name']} {cls.test_user['last_name']}")
        else:
            raise Exception(f"Failed to register test user: {response.text}")
        
        # Book IDs to be used/cleaned up during testing
        cls.book_ids_to_delete = []
        cls.series_ids_to_delete = []

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        # Delete any books created during testing
        for book_id in cls.book_ids_to_delete:
            try:
                requests.delete(f"{API_URL}/books/{book_id}", headers=cls.headers)
            except:
                pass
        
        # Delete any series created during testing
        for series_id in cls.series_ids_to_delete:
            try:
                requests.delete(f"{API_URL}/series/library/{series_id}", headers=cls.headers)
            except:
                pass

    def test_01_health_check(self):
        """Test health check endpoint"""
        print("\n--- Testing Health Check ---")
        
        response = requests.get(f"{BACKEND_URL}/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["database"], "connected")
        self.assertIn("timestamp", data)
        print("✅ GET /health - Health check endpoint working")

    def test_02_auth_module(self):
        """Test auth module endpoints"""
        print("\n--- Testing Auth Module ---")
        
        # Test login
        response = requests.post(f"{API_URL}/auth/login", json=self.__class__.test_user)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertIn("user", data)
        print("✅ POST /api/auth/login - User login working")
        
        # Test get current user
        response = requests.get(f"{API_URL}/auth/me", headers=self.__class__.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["first_name"], self.__class__.test_user["first_name"])
        self.assertEqual(data["last_name"], self.__class__.test_user["last_name"])
        print("✅ GET /api/auth/me - Get current user working")

    def test_03_books_module(self):
        """Test books module endpoints"""
        print("\n--- Testing Books Module ---")
        
        # Test get all books
        response = requests.get(f"{API_URL}/books", headers=self.__class__.headers)
        self.assertEqual(response.status_code, 200)
        books = response.json()
        self.assertIsInstance(books, list)
        print(f"✅ GET /api/books - Get all books working, found {len(books)} books")
        
        # Test create book
        book_data = {
            "title": "Test Book for Modular Architecture",
            "author": "Test Author",
            "category": "roman",
            "description": "A test book for modular architecture testing",
            "cover_url": "https://example.com/test-book.jpg",
            "total_pages": 100
        }
        
        response = requests.post(f"{API_URL}/books", json=book_data, headers=self.__class__.headers)
        self.assertEqual(response.status_code, 200)
        book = response.json()
        book_id = book.get("id") or book.get("_id")
        self.__class__.book_ids_to_delete.append(book_id)
        print("✅ POST /api/books - Create book working")

    def test_04_series_module(self):
        """Test series module endpoints"""
        print("\n--- Testing Series Module ---")
        
        # Test get popular series
        response = requests.get(f"{API_URL}/series/popular", headers=self.__class__.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("series", data)
        self.assertIn("total", data)
        print(f"✅ GET /api/series/popular - Get popular series working, found {len(data['series'])} series")
        
        # Test search series
        response = requests.get(f"{API_URL}/series/search?q=Harry Potter", headers=self.__class__.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("series", data)
        self.assertIn("total", data)
        self.assertIn("search_term", data)
        print(f"✅ GET /api/series/search - Search series working, found {len(data['series'])} series")

    def test_05_sagas_module(self):
        """Test sagas module endpoints"""
        print("\n--- Testing Sagas Module ---")
        
        # Test get all sagas
        response = requests.get(f"{API_URL}/sagas", headers=self.__class__.headers)
        self.assertEqual(response.status_code, 200)
        sagas = response.json()
        print(f"✅ GET /api/sagas - Get all sagas working, found {len(sagas)} sagas")

    def test_06_openlibrary_module(self):
        """Test OpenLibrary module endpoints"""
        print("\n--- Testing OpenLibrary Module ---")
        
        # Test search
        response = requests.get(f"{API_URL}/openlibrary/search?q=Harry Potter", headers=self.__class__.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("books", data)
        self.assertIn("total_found", data)
        print(f"✅ GET /api/openlibrary/search - Open Library search working, found {data['total_found']} books")

    def test_07_stats_module(self):
        """Test stats module endpoints"""
        print("\n--- Testing Stats Module ---")
        
        response = requests.get(f"{API_URL}/stats", headers=self.__class__.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that all required fields are present
        required_fields = [
            "total_books", "completed_books", "reading_books", "to_read_books",
            "categories", "authors_count", "sagas_count", "auto_added_count"
        ]
        
        for field in required_fields:
            self.assertIn(field, data)
            
        print("✅ GET /api/stats - Stats endpoint working")

    def test_08_authors_module(self):
        """Test authors module endpoints"""
        print("\n--- Testing Authors Module ---")
        
        # Test get all authors
        response = requests.get(f"{API_URL}/authors", headers=self.__class__.headers)
        self.assertEqual(response.status_code, 200)
        authors = response.json()
        print(f"✅ GET /api/authors - Get all authors working, found {len(authors)} authors")

def run_tests():
    """Run all tests and print a summary"""
    # Create a test suite with all tests
    loader = unittest.TestLoader()
    # Sort tests by name to ensure they run in order
    loader.sortTestMethodsUsing = lambda x, y: 1 if x > y else -1 if x < y else 0
    suite = loader.loadTestsFromTestCase(BooktimeModularArchitectureTest)
    
    # Run the tests
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    # Print summary
    print("\n=== TEST SUMMARY ===")
    print(f"Total tests: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    # Print failures and errors
    if result.failures:
        print("\n=== FAILURES ===")
        for i, (test, traceback) in enumerate(result.failures):
            print(f"Failure {i+1}: {test}")
            print(traceback)
    
    if result.errors:
        print("\n=== ERRORS ===")
        for i, (test, traceback) in enumerate(result.errors):
            print(f"Error {i+1}: {test}")
            print(traceback)
    
    # Return exit code based on test results
    return 0 if result.wasSuccessful() else 1

if __name__ == "__main__":
    run_tests()