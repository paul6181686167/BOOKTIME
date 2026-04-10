import requests
import json
import unittest
import time
from datetime import datetime

class OpenLibraryUniversalTest(unittest.TestCase):
    """Test suite for the OpenLibrary Universal API endpoints"""

    def setUp(self):
        """Setup for each test"""
        # Get the backend URL from environment or use default
        import os
        self.backend_url = "http://localhost:8002"
        self.api_url = f"{self.backend_url}/api"
        
        # Register a test user
        self.test_user = {
            "first_name": "Test",
            "last_name": "User"
        }
        
        # Register and get token
        response = requests.post(f"{self.api_url}/auth/register", json=self.test_user)
        if response.status_code == 400:  # User might already exist
            response = requests.post(f"{self.api_url}/auth/login", json=self.test_user)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.token = data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        print(f"🚀 Testing OpenLibrary Universal endpoints with backend URL: {self.backend_url}")

    def test_search_universal(self):
        """Test the universal search endpoint"""
        # Test basic search
        query = "Harry Potter"
        response = requests.get(
            f"{self.api_url}/openlibrary/search-universal?q={query}&limit=10",
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check required fields in response
        self.assertIn("books", data)
        self.assertIn("total", data)
        self.assertIn("search_query", data)
        self.assertIn("results_count", data)
        
        # Check that we got some results
        self.assertGreater(len(data["books"]), 0)
        self.assertEqual(data["search_query"], query)
        
        # Check book fields
        for book in data["books"]:
            self.assertIn("title", book)
            self.assertIn("author", book)
            self.assertIn("category", book)
            self.assertIn("in_user_library", book)
            self.assertIn("work_key", book)
            # cover_url might not be present for all books
        
        print(f"✅ Universal search for '{query}' returned {len(data['books'])} books")
        
        # Test with category filter
        query = "Astérix"
        category = "bd"
        response = requests.get(
            f"{self.api_url}/openlibrary/search-universal?q={query}&category={category}",
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that all returned books have the correct category
        for book in data["books"]:
            self.assertEqual(book["category"], category)
        
        print(f"✅ Universal search with category filter '{category}' working")
        
        # Test category detection
        query = "One Piece"
        response = requests.get(
            f"{self.api_url}/openlibrary/search-universal?q={query}",
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that manga is detected correctly
        manga_books = [book for book in data["books"] if book["category"] == "manga"]
        self.assertGreater(len(manga_books), 0, "Should detect manga category for One Piece")
        
        print(f"✅ Category detection working correctly")

    def test_book_details(self):
        """Test the book details endpoint"""
        # Test with a valid work key (Harry Potter)
        work_key = "OL45804W"
        response = requests.get(
            f"{self.api_url}/openlibrary/book/{work_key}",
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        book = response.json()
        
        # Check required fields
        self.assertIn("work_key", book)
        self.assertIn("title", book)
        self.assertIn("description", book)
        self.assertIn("authors", book)
        self.assertIn("editions", book)
        self.assertIn("subjects", book)
        self.assertIn("openlibrary_url", book)
        self.assertIn("in_user_library", book)
        
        # Verify it's Harry Potter
        self.assertIn("Harry Potter", book["title"])
        self.assertEqual(book["work_key"], work_key)
        
        print(f"✅ Book details for '{book['title']}' retrieved successfully")
        
        # Test with invalid work key
        invalid_key = "OL999999W"
        response = requests.get(
            f"{self.api_url}/openlibrary/book/{invalid_key}",
            headers=self.headers
        )
        self.assertEqual(response.status_code, 404)
        
        print("✅ Invalid work key returns 404 as expected")

    def test_author_details(self):
        """Test the author details endpoint"""
        # Test with a valid author (J.K. Rowling)
        author_name = "J.K. Rowling"
        response = requests.get(
            f"{self.api_url}/openlibrary/author/{author_name}",
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        author = response.json()
        
        # Check required fields
        self.assertIn("name", author)
        self.assertIn("biography", author)
        self.assertIn("photo_url", author)
        self.assertIn("bibliography", author)
        self.assertIn("user_stats", author)
        
        # Check bibliography
        self.assertGreater(len(author["bibliography"]), 0)
        for book in author["bibliography"]:
            self.assertIn("title", book)
            self.assertIn("in_user_library", book)
            self.assertIn("category", book)
            # cover_url might not be present for all books
        
        # Check user stats
        self.assertIn("books_read", author["user_stats"])
        self.assertIn("books_reading", author["user_stats"])
        self.assertIn("books_to_read", author["user_stats"])
        self.assertIn("total_user_books", author["user_stats"])
        self.assertIn("completion_percentage", author["user_stats"])
        
        print(f"✅ Author details for '{author_name}' retrieved successfully")
        print(f"   Biography length: {len(author['biography'])} characters")
        print(f"   Bibliography: {len(author['bibliography'])} books")
        print(f"   User stats: {author['user_stats']['total_user_books']} books in library, {author['user_stats']['completion_percentage']}% completion")

    def test_error_handling(self):
        """Test error handling for the OpenLibrary endpoints"""
        # Test search without query parameter
        response = requests.get(
            f"{self.api_url}/openlibrary/search-universal",
            headers=self.headers
        )
        self.assertEqual(response.status_code, 400)
        
        print("✅ Search without query parameter returns 400 as expected")
        
        # Test author endpoint with non-existent author
        author_name = "NonExistentAuthorXYZ123"
        response = requests.get(
            f"{self.api_url}/openlibrary/author/{author_name}",
            headers=self.headers
        )
        # This should still return 200 but with empty bibliography
        self.assertEqual(response.status_code, 200)
        author = response.json()
        self.assertEqual(author["name"], author_name)
        self.assertEqual(len(author["bibliography"]), 0)
        
        print("✅ Non-existent author returns empty bibliography as expected")
        
        # Test without authentication
        response = requests.get(f"{self.api_url}/openlibrary/search-universal?q=Harry Potter")
        self.assertNotEqual(response.status_code, 200)
        
        print("✅ Endpoints require authentication as expected")

    def test_performance(self):
        """Test performance of the OpenLibrary endpoints"""
        start_time = time.time()
        
        # Make 3 consecutive requests
        queries = ["Harry Potter", "Lord of the Rings", "Naruto"]
        for query in queries:
            response = requests.get(
                f"{self.api_url}/openlibrary/search-universal?q={query}&limit=5",
                headers=self.headers
            )
            self.assertEqual(response.status_code, 200)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"✅ Performance test: 3 consecutive searches completed in {total_time:.2f} seconds")
        self.assertLess(total_time, 15, "Searches should complete in under 15 seconds")

if __name__ == "__main__":
    unittest.main(verbosity=2)