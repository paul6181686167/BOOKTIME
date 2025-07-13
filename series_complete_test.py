import requests
import json
import unittest
import uuid
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://45b3415b-66f2-4945-a32a-b570a5d90c13.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class SeriesCompleteTest(unittest.TestCase):
    """Test suite for the /api/series/complete endpoint"""

    def setUp(self):
        """Setup for each test"""
        # Create a test user
        self.user_data = {
            "first_name": "Test",
            "last_name": f"User{uuid.uuid4().hex[:6]}"  # Add random suffix to avoid conflicts
        }
        
        # Register the test user
        response = requests.post(f"{API_URL}/auth/register", json=self.user_data)
        self.assertEqual(response.status_code, 200)
        auth_data = response.json()
        self.token = auth_data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Test book data for a series
        self.test_series_book = {
            "title": "Harry Potter et l'École des Sorciers",
            "author": "J.K. Rowling",
            "category": "roman",
            "description": "Premier tome de la saga Harry Potter",
            "saga": "Harry Potter",
            "volume_number": 1,
            "publication_year": 1997,
            "publisher": "Gallimard"
        }
        
        # Test book data for One Piece series
        self.one_piece_book = {
            "title": "One Piece Tome 1",
            "author": "Eiichiro Oda",
            "category": "manga",
            "description": "Premier tome de la saga One Piece",
            "saga": "One Piece",
            "volume_number": 1,
            "publication_year": 1997,
            "publisher": "Glénat"
        }
        
        # Book IDs to be cleaned up during tearDown
        self.book_ids_to_delete = []

    def tearDown(self):
        """Clean up after each test"""
        # Delete any books created during testing
        for book_id in self.book_ids_to_delete:
            try:
                requests.delete(f"{API_URL}/books/{book_id}", headers=self.headers)
            except:
                pass

    def test_series_complete_harry_potter(self):
        """Test auto-completing the Harry Potter series"""
        # First create a book for the series
        response = requests.post(f"{API_URL}/books", json=self.test_series_book, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        book = response.json()
        self.book_ids_to_delete.append(book["id"])
        
        # Now auto-complete the series
        series_data = {
            "series_name": "Harry Potter",
            "target_volumes": 7  # Harry Potter has 7 books
        }
        
        response = requests.post(f"{API_URL}/series/complete", json=series_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        # Verify the response
        self.assertEqual(result["series_name"], "Harry Potter")
        self.assertEqual(result["total_volumes"], 7)
        self.assertEqual(result["existing_volumes"], 1)  # We created volume 1
        self.assertEqual(result["created_volumes"], 6)  # Should have created volumes 2-7
        
        # Add the created book IDs to the cleanup list
        for book in result["created_books"]:
            self.book_ids_to_delete.append(book["id"])
        
        # Verify the created books
        for book in result["created_books"]:
            self.assertEqual(book["saga"], "Harry Potter")
            self.assertEqual(book["author"], "J.K. Rowling")
            self.assertEqual(book["category"], "roman")
            self.assertEqual(book["status"], "to_read")
            self.assertTrue(book["auto_added"])
            self.assertIn(book["volume_number"], range(2, 8))  # Volumes 2-7
        
        # Get all books for the user and verify the series is there
        response = requests.get(f"{API_URL}/books", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        all_books = response.json()
        
        # Filter for Harry Potter books
        harry_potter_books = [book for book in all_books if book.get("saga") == "Harry Potter"]
        
        # Should have 7 books (1 we created + 6 auto-completed)
        self.assertEqual(len(harry_potter_books), 7)
        
        # Verify all volumes 1-7 exist
        volumes = sorted([book["volume_number"] for book in harry_potter_books])
        self.assertEqual(volumes, list(range(1, 8)))
        
        print("✅ Series complete endpoint works for Harry Potter series")
        print(f"   Created volumes 2-7 successfully")
        print(f"   All 7 volumes exist in the user's library")

    def test_series_complete_one_piece(self):
        """Test auto-completing the One Piece series"""
        # First create a book for the series
        response = requests.post(f"{API_URL}/books", json=self.one_piece_book, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        book = response.json()
        self.book_ids_to_delete.append(book["id"])
        
        # Now auto-complete the series
        series_data = {
            "series_name": "One Piece",
            "target_volumes": 5  # We'll add 5 volumes for testing
        }
        
        response = requests.post(f"{API_URL}/series/complete", json=series_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        # Verify the response
        self.assertEqual(result["series_name"], "One Piece")
        self.assertEqual(result["total_volumes"], 5)
        self.assertEqual(result["existing_volumes"], 1)  # We created volume 1
        self.assertEqual(result["created_volumes"], 4)  # Should have created volumes 2-5
        
        # Add the created book IDs to the cleanup list
        for book in result["created_books"]:
            self.book_ids_to_delete.append(book["id"])
        
        # Verify the created books
        for book in result["created_books"]:
            self.assertEqual(book["saga"], "One Piece")
            self.assertEqual(book["author"], "Eiichiro Oda")
            self.assertEqual(book["category"], "manga")
            self.assertEqual(book["status"], "to_read")
            self.assertTrue(book["auto_added"])
            self.assertIn(book["volume_number"], range(2, 6))  # Volumes 2-5
        
        # Get all books for the user and verify the series is there
        response = requests.get(f"{API_URL}/books", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        all_books = response.json()
        
        # Filter for One Piece books
        one_piece_books = [book for book in all_books if book.get("saga") == "One Piece"]
        
        # Should have 5 books (1 we created + 4 auto-completed)
        self.assertEqual(len(one_piece_books), 5)
        
        # Verify all volumes 1-5 exist
        volumes = sorted([book["volume_number"] for book in one_piece_books])
        self.assertEqual(volumes, list(range(1, 6)))
        
        print("✅ Series complete endpoint works for One Piece series")
        print(f"   Created volumes 2-5 successfully")
        print(f"   All 5 volumes exist in the user's library")

    def test_series_complete_error_cases(self):
        """Test error cases for the series complete endpoint"""
        # Test missing series_name
        series_data = {
            "target_volumes": 5
        }
        
        response = requests.post(f"{API_URL}/series/complete", json=series_data, headers=self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Nom de série requis", response.json()["detail"])
        
        # Test non-existent series
        series_data = {
            "series_name": "Non-existent Series",
            "target_volumes": 5
        }
        
        response = requests.post(f"{API_URL}/series/complete", json=series_data, headers=self.headers)
        self.assertEqual(response.status_code, 404)
        self.assertIn("Aucun livre de cette série trouvé", response.json()["detail"])
        
        print("✅ Series complete endpoint correctly handles error cases")
        print("   Returns 400 for missing series_name")
        print("   Returns 404 for non-existent series")

if __name__ == "__main__":
    unittest.main(verbosity=2)