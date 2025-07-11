import requests
import json
import unittest
import uuid
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://08bd90bc-cd2e-49c8-99d9-71fefc6983a7.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class SeriesAPITest(unittest.TestCase):
    """Test suite for the Series API endpoints"""

    def setUp(self):
        """Setup for each test"""
        # Register a test user for authentication
        self.user_data = {
            "first_name": "Test",
            "last_name": "Series"
        }
        
        # Register and login
        response = requests.post(f"{API_URL}/auth/register", json=self.user_data)
        if response.status_code == 400:  # User already exists
            response = requests.post(f"{API_URL}/auth/login", json=self.user_data)
        
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Test book data for series testing
        self.test_book_data = {
            "title": "Harry Potter et l'École des Sorciers",
            "author": "J.K. Rowling",
            "category": "roman",
            "description": "Le premier tome de la saga Harry Potter",
            "saga": "Harry Potter",
            "volume_number": 1,
            "publication_year": 1997
        }
        
        # Book IDs to be used/cleaned up during testing
        self.book_ids_to_delete = []

    def tearDown(self):
        """Clean up after each test"""
        # Delete any books created during testing
        for book_id in self.book_ids_to_delete:
            try:
                requests.delete(f"{API_URL}/books/{book_id}", headers=self.headers)
            except:
                pass

    def test_get_popular_series(self):
        """Test retrieving popular series"""
        # Test without filters
        response = requests.get(f"{API_URL}/series/popular", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that the response has the expected structure
        self.assertIn("series", data)
        self.assertIn("total", data)
        self.assertGreaterEqual(data["total"], 5, "Should have at least 5 popular series")
        
        # Check that each series has the required metadata
        for series in data["series"]:
            self.assertIn("name", series)
            self.assertIn("category", series)
            self.assertIn("score", series)
            self.assertIn("keywords", series)
            self.assertIn("authors", series)
            self.assertIn("variations", series)
            self.assertIn("volumes", series)
            self.assertIn("languages", series)
            self.assertIn("description", series)
            self.assertIn("first_published", series)
            self.assertIn("status", series)
        
        print(f"✅ Get popular series endpoint working, found {data['total']} series")
        
        # Test with category filter - Roman
        response = requests.get(f"{API_URL}/series/popular?category=roman", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that all series are of category "roman"
        for series in data["series"]:
            self.assertEqual(series["category"], "roman")
        
        print(f"✅ Filter by category 'roman' working, found {len(data['series'])} series")
        
        # Test with category filter - Manga
        response = requests.get(f"{API_URL}/series/popular?category=manga", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that all series are of category "manga"
        for series in data["series"]:
            self.assertEqual(series["category"], "manga")
        
        print(f"✅ Filter by category 'manga' working, found {len(data['series'])} series")
        
        # Test with category filter - BD
        response = requests.get(f"{API_URL}/series/popular?category=bd", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that all series are of category "bd"
        for series in data["series"]:
            self.assertEqual(series["category"], "bd")
        
        print(f"✅ Filter by category 'bd' working, found {len(data['series'])} series")
        
        # Test with limit parameter
        limit = 3
        response = requests.get(f"{API_URL}/series/popular?limit={limit}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that the number of series is limited
        self.assertLessEqual(len(data["series"]), limit)
        
        print(f"✅ Limit parameter working, limited to {limit} series")

    def test_detect_series_harry_potter(self):
        """Test detecting Harry Potter series"""
        title = "Harry Potter et la Chambre des Secrets"
        author = "J.K. Rowling"
        
        response = requests.get(f"{API_URL}/series/detect?title={title}&author={author}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that the response has the expected structure
        self.assertIn("detected_series", data)
        self.assertIn("book_info", data)
        
        # Check that Harry Potter is detected with high confidence
        detected = False
        for series in data["detected_series"]:
            if series["series"]["name"] == "Harry Potter":
                detected = True
                self.assertGreaterEqual(series["confidence"], 80, "Harry Potter should be detected with high confidence")
                self.assertIn("author_match", series["match_reasons"], "Author match should be a reason")
                self.assertIn("title_variation", series["match_reasons"], "Title variation should be a reason")
                
                # Print the confidence score and match reasons
                print("✅ Harry Potter series detection working")
                print(f"   Confidence: {series['confidence']}")
                print(f"   Match reasons: {series['match_reasons']}")
        
        self.assertTrue(detected, "Harry Potter series should be detected")

    def test_detect_series_one_piece(self):
        """Test detecting One Piece series"""
        title = "One Piece Tome 42"
        author = "Eiichiro Oda"
        
        response = requests.get(f"{API_URL}/series/detect?title={title}&author={author}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that One Piece is detected with high confidence
        detected = False
        for series in data["detected_series"]:
            if series["series"]["name"] == "One Piece":
                detected = True
                self.assertGreaterEqual(series["confidence"], 80, "One Piece should be detected with high confidence")
                self.assertIn("author_match", series["match_reasons"], "Author match should be a reason")
                self.assertIn("title_variation", series["match_reasons"], "Title variation should be a reason")
                
                # Print the confidence score and match reasons
                print("✅ One Piece series detection working")
                print(f"   Confidence: {series['confidence']}")
                print(f"   Match reasons: {series['match_reasons']}")
        
        self.assertTrue(detected, "One Piece series should be detected")

    def test_detect_series_asterix(self):
        """Test detecting Astérix series"""
        title = "Astérix et Obélix: Mission Cléopâtre"
        author = "René Goscinny"
        
        response = requests.get(f"{API_URL}/series/detect?title={title}&author={author}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that Astérix is detected with high confidence
        detected = False
        for series in data["detected_series"]:
            if series["series"]["name"] == "Astérix":
                detected = True
                self.assertGreaterEqual(series["confidence"], 60, "Astérix should be detected with decent confidence")
                
                # Check for match reasons
                if "author_match" in series["match_reasons"]:
                    print("   Author match detected")
                if "title_variation" in series["match_reasons"]:
                    print("   Title variation detected")
                if any("keywords_match" in reason for reason in series["match_reasons"]):
                    print("   Keywords match detected")
                
                # Print the confidence score and match reasons
                print("✅ Astérix series detection working")
                print(f"   Confidence: {series['confidence']}")
                print(f"   Match reasons: {series['match_reasons']}")
        
        self.assertTrue(detected, "Astérix series should be detected")

    def test_complete_series(self):
        """Test auto-completing a series"""
        # First create a book for a test series
        test_series_name = f"Test Series {uuid.uuid4().hex[:8]}"
        test_book = {
            "title": f"{test_series_name} - Tome 1",
            "author": "Test Author",
            "category": "roman",
            "saga": test_series_name,
            "volume_number": 1
        }
        
        # Create the book
        response = requests.post(f"{API_URL}/books", json=test_book, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        book = response.json()
        self.book_ids_to_delete.append(book["id"])
        
        # Now use the auto-complete endpoint
        series_data = {
            "series_name": test_series_name,
            "target_volumes": 5
        }
        
        response = requests.post(f"{API_URL}/series/complete", json=series_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that the response has the expected structure
        self.assertIn("created_books", data)
        self.assertIn("series_name", data)
        self.assertIn("total_volumes", data)
        self.assertIn("existing_volumes", data)
        self.assertIn("created_volumes", data)
        
        # Check that the correct number of books were created
        self.assertEqual(data["created_volumes"], 4, "Should have created 4 new volumes (2-5)")
        
        # Add the new book IDs to the cleanup list
        for book in data["created_books"]:
            self.book_ids_to_delete.append(book["id"])
        
        # Check that the books have the correct metadata
        for book in data["created_books"]:
            self.assertEqual(book["saga"], test_series_name)
            self.assertEqual(book["author"], "Test Author")
            self.assertEqual(book["category"], "roman")
            self.assertEqual(book["status"], "to_read")
            self.assertTrue(book["auto_added"])
            self.assertGreaterEqual(book["volume_number"], 2)
            self.assertLessEqual(book["volume_number"], 5)
        
        # Verify that all volumes now exist by getting the saga books
        response = requests.get(f"{API_URL}/sagas/{test_series_name}/books", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        saga_books = response.json()
        
        # Should have 5 books (1 original + 4 created)
        self.assertEqual(len(saga_books), 5)
        
        # Check that all volumes 1-5 exist
        volumes = sorted([book["volume_number"] for book in saga_books])
        self.assertEqual(volumes, [1, 2, 3, 4, 5])
        
        print(f"✅ Series auto-completion working, created {data['created_volumes']} volumes for '{test_series_name}'")

if __name__ == "__main__":
    unittest.main(verbosity=2)