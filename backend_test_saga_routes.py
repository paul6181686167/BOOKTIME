import requests
import json
import unittest
import uuid
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://716502db-4f85-467f-b61b-dcea530cb7a6.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class BooktimeSagaRoutesTest(unittest.TestCase):
    """Test suite for the saga routes in Booktime API"""

    def setUp(self):
        """Setup for each test"""
        # Register a test user
        self.user_data = {
            "first_name": "Test",
            "last_name": "User"
        }
        
        try:
            response = requests.post(f"{API_URL}/auth/register", json=self.user_data)
            if response.status_code == 200:
                self.token = response.json()["access_token"]
            else:
                # Try to login if registration fails (user might already exist)
                response = requests.post(f"{API_URL}/auth/login", json=self.user_data)
                if response.status_code == 200:
                    self.token = response.json()["access_token"]
                else:
                    self.token = None
        except Exception as e:
            print(f"Error during authentication: {e}")
            self.token = None
            
        self.headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        
        # Create test saga books
        self.saga_name = f"Test Saga {uuid.uuid4().hex[:8]}"
        self.book_ids = []
        
        # Create 3 books in the saga
        for i in range(1, 4):
            book_data = {
                "title": f"{self.saga_name} - Volume {i}",
                "author": "Test Author",
                "category": "roman",
                "saga": self.saga_name,
                "volume_number": i
            }
            
            response = requests.post(f"{API_URL}/books", json=book_data, headers=self.headers)
            if response.status_code == 200:
                book = response.json()
                self.book_ids.append(book["id"])

    def tearDown(self):
        """Clean up after each test"""
        # Delete all books created during testing
        for book_id in self.book_ids:
            try:
                requests.delete(f"{API_URL}/books/{book_id}", headers=self.headers)
            except:
                pass

    def test_get_sagas(self):
        """Test retrieving all sagas with their statistics"""
        response = requests.get(f"{API_URL}/sagas", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        sagas = response.json()
        
        # Find our test saga
        test_saga = next((s for s in sagas if s["name"] == self.saga_name), None)
        self.assertIsNotNone(test_saga, f"Test saga '{self.saga_name}' not found in sagas list")
        
        if test_saga:
            self.assertEqual(test_saga["books_count"], 3)
            self.assertEqual(test_saga["author"], "Test Author")
            self.assertEqual(test_saga["category"], "roman")
            self.assertEqual(test_saga["next_volume"], 4)
            
        print(f"✅ GET /api/sagas endpoint working, found test saga with 3 books")

    def test_get_saga_books(self):
        """Test retrieving books in a saga sorted by volume"""
        response = requests.get(f"{API_URL}/sagas/{self.saga_name}/books", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        books = response.json()
        
        self.assertEqual(len(books), 3, f"Expected 3 books in test saga, got {len(books)}")
        
        # Check that books are sorted by volume_number
        for i in range(len(books) - 1):
            self.assertLessEqual(books[i]["volume_number"], books[i+1]["volume_number"])
            
        # Check that all volumes are present
        volumes = [book["volume_number"] for book in books]
        self.assertEqual(sorted(volumes), [1, 2, 3])
        
        print(f"✅ GET /api/sagas/{self.saga_name}/books endpoint working, books are sorted by volume")

    def test_auto_add_next_volume(self):
        """Test auto-adding the next volume to a saga"""
        # Get current books in the saga
        response = requests.get(f"{API_URL}/sagas/{self.saga_name}/books", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        initial_books = response.json()
        initial_count = len(initial_books)
        
        # Auto-add next volume
        response = requests.post(f"{API_URL}/sagas/{self.saga_name}/auto-add", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        result = response.json()
        
        # Verify the response
        self.assertIn("message", result)
        self.assertIn("book", result)
        new_book = result["book"]
        
        # Add book ID to cleanup list
        if "id" in new_book:
            self.book_ids.append(new_book["id"])
        
        # Verify the new book
        self.assertEqual(new_book["saga"], self.saga_name)
        self.assertEqual(new_book["volume_number"], 4)
        self.assertEqual(new_book["status"], "to_read")
        self.assertTrue(new_book["auto_added"])
        
        # Get updated books in the saga
        response = requests.get(f"{API_URL}/sagas/{self.saga_name}/books", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        updated_books = response.json()
        
        # Should have one more book
        self.assertEqual(len(updated_books), initial_count + 1)
        
        print(f"✅ POST /api/sagas/{self.saga_name}/auto-add endpoint working, added volume 4")
        
        # Test with non-existent saga
        saga_name = "Non-existent Saga"
        response = requests.post(f"{API_URL}/sagas/{saga_name}/auto-add", headers=self.headers)
        self.assertEqual(response.status_code, 404)
        
        print("✅ Auto-add for non-existent saga returns 404 as expected")

    def test_missing_volumes(self):
        """Test detecting missing saga volumes"""
        # Delete the middle volume to create a gap
        if len(self.book_ids) >= 2:
            middle_book_id = self.book_ids[1]  # Volume 2
            response = requests.delete(f"{API_URL}/books/{middle_book_id}", headers=self.headers)
            self.assertEqual(response.status_code, 200)
            self.book_ids.remove(middle_book_id)
            
            # Check missing volumes
            response = requests.get(f"{API_URL}/openlibrary/missing-volumes?saga={self.saga_name}", headers=self.headers)
            self.assertEqual(response.status_code, 200)
            result = response.json()
            
            self.assertIn("saga", result)
            self.assertIn("present_volumes", result)
            self.assertIn("missing_volumes", result)
            self.assertIn("next_volume", result)
            
            self.assertEqual(result["saga"], self.saga_name)
            self.assertEqual(sorted(result["present_volumes"]), [1, 3])
            self.assertEqual(result["missing_volumes"], [2])
            self.assertEqual(result["next_volume"], 4)
            
            print(f"✅ GET /api/openlibrary/missing-volumes endpoint working, detected missing volume 2")

if __name__ == "__main__":
    unittest.main(verbosity=2)