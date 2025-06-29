import requests
import json
import unittest
import uuid
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://aab14546-30e1-4f64-bbab-d554cb50c977.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class ComprehensiveSeriesAPITest(unittest.TestCase):
    """Comprehensive test suite for the Series API endpoints"""

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

    def test_01_get_popular_series(self):
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
        
        # Test with language filter
        response = requests.get(f"{API_URL}/series/popular?language=fr", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that all series support French
        for series in data["series"]:
            self.assertIn("fr", series["languages"])
        
        print(f"✅ Language filter working, found {len(data['series'])} series in French")

    def test_02_detect_series_harry_potter(self):
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
        
        self.assertTrue(detected, "Harry Potter series should be detected")
        
        print("✅ Harry Potter series detection working")
        print(f"   Confidence: {series['confidence']}")
        print(f"   Match reasons: {series['match_reasons']}")
        
        # Test with just title, no author
        response = requests.get(f"{API_URL}/series/detect?title={title}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that Harry Potter is still detected
        detected = False
        for series in data["detected_series"]:
            if series["series"]["name"] == "Harry Potter":
                detected = True
                self.assertGreaterEqual(series["confidence"], 60, "Harry Potter should be detected with decent confidence")
        
        self.assertTrue(detected, "Harry Potter series should be detected even without author")
        
        print("✅ Harry Potter series detection works with just title")

    def test_03_detect_series_one_piece(self):
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
        
        self.assertTrue(detected, "One Piece series should be detected")
        
        print("✅ One Piece series detection working")
        print(f"   Confidence: {series['confidence']}")
        print(f"   Match reasons: {series['match_reasons']}")
        
        # Test with keywords in title
        title = "Aventures de pirates sur Grand Line"
        response = requests.get(f"{API_URL}/series/detect?title={title}&author={author}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that One Piece is detected based on keywords
        detected = False
        for series in data["detected_series"]:
            if series["series"]["name"] == "One Piece":
                detected = True
                self.assertGreaterEqual(series["confidence"], 60, "One Piece should be detected with decent confidence")
                self.assertIn("author_match", series["match_reasons"], "Author match should be a reason")
                if any("keywords_match" in reason for reason in series["match_reasons"]):
                    print("   Keywords match detected")
        
        self.assertTrue(detected, "One Piece series should be detected based on keywords")
        
        print("✅ One Piece series detection works with keywords")

    def test_04_detect_series_asterix(self):
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
        
        self.assertTrue(detected, "Astérix series should be detected")
        
        print("✅ Astérix series detection working")
        print(f"   Confidence: {series['confidence']}")
        print(f"   Match reasons: {series['match_reasons']}")
        
        # Test with just keywords in title
        title = "Aventures de gaulois et potion magique"
        response = requests.get(f"{API_URL}/series/detect?title={title}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that Astérix is detected based on keywords
        detected = False
        for series in data["detected_series"]:
            if series["series"]["name"] == "Astérix":
                detected = True
                if any("keywords_match" in reason for reason in series["match_reasons"]):
                    print("   Keywords match detected for 'gaulois' and 'potion magique'")
        
        self.assertTrue(detected, "Astérix series should be detected based on keywords")
        
        print("✅ Astérix series detection works with keywords only")

    def test_05_complete_series(self):
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
        
        # Test with non-existent series
        series_data = {
            "series_name": "Non-existent Series",
            "target_volumes": 3
        }
        
        response = requests.post(f"{API_URL}/series/complete", json=series_data, headers=self.headers)
        self.assertEqual(response.status_code, 404)
        
        print("✅ Series auto-completion returns 404 for non-existent series")
        
        # Test with missing series_name
        series_data = {
            "target_volumes": 3
        }
        
        response = requests.post(f"{API_URL}/series/complete", json=series_data, headers=self.headers)
        self.assertEqual(response.status_code, 400)
        
        print("✅ Series auto-completion returns 400 for missing series_name")

    def test_06_complete_series_with_template(self):
        """Test auto-completing a series using a template book"""
        # First create a book for a test series
        test_series_name = f"Template Series {uuid.uuid4().hex[:8]}"
        test_book = {
            "title": f"{test_series_name} - Tome 1",
            "author": "Template Author",
            "category": "manga",
            "saga": test_series_name,
            "volume_number": 1,
            "genre": "fantasy",
            "publisher": "Test Publisher"
        }
        
        # Create the book
        response = requests.post(f"{API_URL}/books", json=test_book, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        book = response.json()
        template_book_id = book["id"]
        self.book_ids_to_delete.append(template_book_id)
        
        # Now use the auto-complete endpoint with template_book_id
        series_data = {
            "series_name": test_series_name,
            "target_volumes": 3,
            "template_book_id": template_book_id
        }
        
        response = requests.post(f"{API_URL}/series/complete", json=series_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that the correct number of books were created
        self.assertEqual(data["created_volumes"], 2, "Should have created 2 new volumes (2-3)")
        
        # Add the new book IDs to the cleanup list
        for book in data["created_books"]:
            self.book_ids_to_delete.append(book["id"])
        
        # Check that the books have the correct metadata from the template
        for book in data["created_books"]:
            self.assertEqual(book["saga"], test_series_name)
            self.assertEqual(book["author"], "Template Author")
            self.assertEqual(book["category"], "manga")
            self.assertEqual(book["genre"], "fantasy")
            self.assertEqual(book["publisher"], "Test Publisher")
            self.assertEqual(book["status"], "to_read")
            self.assertTrue(book["auto_added"])
        
        print(f"✅ Series auto-completion with template working, created {data['created_volumes']} volumes for '{test_series_name}'")

    def test_07_integration_detect_and_complete(self):
        """Test integration between detect and complete endpoints"""
        # First create a book that should be detected as part of a known series
        test_book = {
            "title": "Harry Potter et l'École des Sorciers",
            "author": "J.K. Rowling",
            "category": "roman",
            "description": "Le premier tome de la saga Harry Potter",
            "volume_number": 1,
            "publication_year": 1997
        }
        
        # Create the book (without saga information)
        response = requests.post(f"{API_URL}/books", json=test_book, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        book = response.json()
        self.book_ids_to_delete.append(book["id"])
        
        # Now detect the series
        title = test_book["title"]
        author = test_book["author"]
        response = requests.get(f"{API_URL}/series/detect?title={title}&author={author}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Find Harry Potter in the detected series
        harry_potter = None
        for series in data["detected_series"]:
            if series["series"]["name"] == "Harry Potter":
                harry_potter = series["series"]
                break
        
        self.assertIsNotNone(harry_potter, "Harry Potter should be detected")
        
        # Update the book with the detected saga information
        update_data = {
            "saga": "Harry Potter"
        }
        response = requests.put(f"{API_URL}/books/{book['id']}", json=update_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        updated_book = response.json()
        
        # Verify the update
        self.assertEqual(updated_book["saga"], "Harry Potter")
        
        # Now use the auto-complete endpoint to add more volumes
        series_data = {
            "series_name": "Harry Potter",
            "target_volumes": 3
        }
        
        response = requests.post(f"{API_URL}/series/complete", json=series_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Add the new book IDs to the cleanup list
        for book in data["created_books"]:
            self.book_ids_to_delete.append(book["id"])
        
        # Check that the books have the correct metadata
        for book in data["created_books"]:
            self.assertEqual(book["saga"], "Harry Potter")
            self.assertEqual(book["author"], "J.K. Rowling")
            self.assertEqual(book["category"], "roman")
            self.assertEqual(book["status"], "to_read")
            self.assertTrue(book["auto_added"])
        
        print(f"✅ Integration between detect and complete endpoints working")
        print(f"   Created {data['created_volumes']} volumes for Harry Potter")

if __name__ == "__main__":
    unittest.main(verbosity=2)