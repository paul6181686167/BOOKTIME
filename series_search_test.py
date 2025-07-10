import requests
import json
import unittest
import time

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://ce60cde4-0958-4720-9786-613598f3ff88.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class BooktimeSeriesSearchTest(unittest.TestCase):
    """Test suite for the Booktime API focusing on series and search functionality"""

    def setUp(self):
        """Setup for each test - register and login a test user"""
        self.test_user = {
            "first_name": "Test",
            "last_name": "Series"
        }
        
        # Register a test user
        response = requests.post(f"{API_URL}/auth/register", json=self.test_user)
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
            print(f"✅ Successfully registered test user: {self.test_user['first_name']} {self.test_user['last_name']}")
        else:
            # Try to login if registration fails (user might already exist)
            response = requests.post(f"{API_URL}/auth/login", json=self.test_user)
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
                print(f"✅ Successfully logged in as existing user: {self.test_user['first_name']} {self.test_user['last_name']}")
            else:
                self.fail(f"Failed to register or login test user: {response.text}")

    def test_health_endpoint(self):
        """Test the health endpoint"""
        response = requests.get(f"{BACKEND_URL}/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["database"], "connected")
        print("✅ Health endpoint is working correctly")

    def test_series_popular_endpoint(self):
        """Test the GET /api/series/popular endpoint"""
        response = requests.get(f"{API_URL}/series/popular", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("series", data)
        self.assertIn("total", data)
        self.assertGreaterEqual(len(data["series"]), 1)
        
        # Check that each series has the required fields
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
        
        print(f"✅ GET /api/series/popular endpoint is working correctly, found {len(data['series'])} series")
        
        # Test with category filter
        for category in ["roman", "manga", "bd"]:
            response = requests.get(f"{API_URL}/series/popular?category={category}", headers=self.headers)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("series", data)
            for series in data["series"]:
                self.assertEqual(series["category"], category)
            print(f"✅ GET /api/series/popular with category={category} filter is working correctly, found {len(data['series'])} series")
        
        # Test with limit parameter
        limit = 3
        response = requests.get(f"{API_URL}/series/popular?limit={limit}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertLessEqual(len(data["series"]), limit)
        print(f"✅ GET /api/series/popular with limit={limit} is working correctly")

    def test_series_search_endpoint(self):
        """Test the GET /api/series/search endpoint"""
        search_term = "Harry Potter"
        response = requests.get(f"{API_URL}/series/search?q={search_term}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("series", data)
        self.assertIn("total", data)
        self.assertIn("search_term", data)
        self.assertEqual(data["search_term"], search_term)
        
        found_harry_potter = False
        for series in data["series"]:
            if "Harry Potter" in series["name"]:
                found_harry_potter = True
                self.assertIn("search_score", series)
                self.assertIn("match_reasons", series)
                break
        
        self.assertTrue(found_harry_potter, "Harry Potter series should be found in search results")
        print(f"✅ GET /api/series/search?q={search_term} is working correctly, found {len(data['series'])} series")

    def test_series_detect_endpoint(self):
        """Test the GET /api/series/detect endpoint"""
        title = "Harry Potter et la Chambre des Secrets"
        response = requests.get(f"{API_URL}/series/detect?title={title}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("detected_series", data)
        self.assertIn("book_info", data)
        self.assertEqual(data["book_info"]["title"], title)
        self.assertGreaterEqual(len(data["detected_series"]), 1)
        
        found_harry_potter = False
        for series_data in data["detected_series"]:
            if "Harry Potter" in series_data["series"]["name"]:
                found_harry_potter = True
                self.assertGreaterEqual(series_data["confidence"], 60)
                self.assertIn("match_reasons", series_data)
                break
        
        self.assertTrue(found_harry_potter, "Harry Potter series should be detected")
        print(f"✅ GET /api/series/detect?title={title} is working correctly")
        
        # Test with another title
        title = "One Piece Tome 42"
        response = requests.get(f"{API_URL}/series/detect?title={title}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        found_one_piece = False
        for series_data in data["detected_series"]:
            if "One Piece" in series_data["series"]["name"]:
                found_one_piece = True
                self.assertGreaterEqual(series_data["confidence"], 60)
                self.assertIn("match_reasons", series_data)
                break
        
        self.assertTrue(found_one_piece, "One Piece series should be detected")
        print(f"✅ GET /api/series/detect?title={title} is working correctly")
        
        # Test with a third title
        title = "Astérix et Obélix: Mission Cléopâtre"
        response = requests.get(f"{API_URL}/series/detect?title={title}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        found_asterix = False
        for series_data in data["detected_series"]:
            if "Astérix" in series_data["series"]["name"]:
                found_asterix = True
                self.assertGreaterEqual(series_data["confidence"], 60)
                self.assertIn("match_reasons", series_data)
                break
        
        self.assertTrue(found_asterix, "Astérix series should be detected")
        print(f"✅ GET /api/series/detect?title={title} is working correctly")

    def test_books_view_mode(self):
        """Test the GET /api/books endpoint with different view_mode values"""
        # Test with view_mode=series
        response = requests.get(f"{API_URL}/books?view_mode=series", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        series_data = response.json()
        # For a new user, this might be empty, which is fine
        print(f"✅ GET /api/books?view_mode=series is working correctly, found {len(series_data)} series")
        
        # Test with view_mode=books
        response = requests.get(f"{API_URL}/books?view_mode=books", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        books_data = response.json()
        # For a new user, this might be empty, which is fine
        print(f"✅ GET /api/books?view_mode=books is working correctly, found {len(books_data)} books")

    def test_books_search_grouped(self):
        """Test the GET /api/books/search-grouped endpoint"""
        search_term = "Harry"
        response = requests.get(f"{API_URL}/books/search-grouped?q={search_term}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("results", data)
        self.assertIn("total_books", data)
        self.assertIn("total_sagas", data)
        self.assertIn("search_term", data)
        # The grouped_by_saga field might not be present for empty results
        # so we'll only check it if there are results
        if data["results"]:
            self.assertIn("grouped_by_saga", data)
        self.assertEqual(data["search_term"], search_term)
        print(f"✅ GET /api/books/search-grouped?q={search_term} is working correctly")

    def test_openlibrary_search(self):
        """Test the GET /api/openlibrary/search endpoint"""
        search_term = "Harry Potter"
        response = requests.get(f"{API_URL}/openlibrary/search?q={search_term}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("books", data)
        self.assertIn("total_found", data)
        self.assertGreaterEqual(data["total_found"], 1)
        self.assertGreaterEqual(len(data["books"]), 1)
        
        # Check that each book has the required fields
        for book in data["books"]:
            self.assertIn("ol_key", book)
            self.assertIn("title", book)
            self.assertIn("author", book)
            self.assertIn("category", book)
            self.assertIn("cover_url", book)
        
        print(f"✅ GET /api/openlibrary/search?q={search_term} is working correctly, found {data['total_found']} books")

if __name__ == "__main__":
    unittest.main(verbosity=2)