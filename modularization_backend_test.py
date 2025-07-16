import requests
import json
import unittest
import uuid
import time
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://349fc2df-7f00-4c0a-b53e-ed8ab7c61456.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class BooktimeAPITest(unittest.TestCase):
    """Test suite for the Booktime API endpoints after frontend modularization"""

    def setUp(self):
        """Setup for each test"""
        # Register a test user
        self.test_user = {
            "first_name": f"Test{uuid.uuid4().hex[:6]}",
            "last_name": f"User{uuid.uuid4().hex[:6]}"
        }
        
        # Register the user and get the token
        response = requests.post(f"{API_URL}/auth/register", json=self.test_user)
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
            self.user_id = data["user"]["id"]
            print(f"Created test user: {self.test_user['first_name']} {self.test_user['last_name']}")
        else:
            self.fail(f"Failed to register test user: {response.text}")
        
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
        
        # Book IDs to be used/cleaned up during testing
        self.book_ids_to_delete = []
        self.series_ids_to_delete = []

    def tearDown(self):
        """Clean up after each test"""
        # Delete any books created during testing
        for book_id in self.book_ids_to_delete:
            try:
                requests.delete(f"{API_URL}/books/{book_id}", headers=self.headers)
            except:
                pass
        
        # Delete any series created during testing
        for series_id in self.series_ids_to_delete:
            try:
                requests.delete(f"{API_URL}/series/library/{series_id}", headers=self.headers)
            except:
                pass

    # 1. Authentication Endpoints
    def test_auth_endpoints(self):
        """Test all authentication endpoints"""
        print("\n--- Testing Authentication Endpoints ---")
        
        # 1. Test registration
        new_user = {
            "first_name": f"New{uuid.uuid4().hex[:6]}",
            "last_name": f"User{uuid.uuid4().hex[:6]}"
        }
        
        response = requests.post(f"{API_URL}/auth/register", json=new_user)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["first_name"], new_user["first_name"])
        self.assertEqual(data["user"]["last_name"], new_user["last_name"])
        print("✅ POST /api/auth/register - User registration working")
        
        # Save token for later tests
        new_token = data["access_token"]
        new_headers = {"Authorization": f"Bearer {new_token}"}
        
        # 2. Test login
        response = requests.post(f"{API_URL}/auth/login", json=new_user)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertIn("user", data)
        self.assertEqual(data["user"]["first_name"], new_user["first_name"])
        self.assertEqual(data["user"]["last_name"], new_user["last_name"])
        print("✅ POST /api/auth/login - User login working")
        
        # 3. Test get current user
        response = requests.get(f"{API_URL}/auth/me", headers=new_headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["first_name"], new_user["first_name"])
        self.assertEqual(data["last_name"], new_user["last_name"])
        print("✅ GET /api/auth/me - Get current user working")
        
        # 4. Test invalid login
        invalid_user = {
            "first_name": "NonExistent",
            "last_name": "User"
        }
        response = requests.post(f"{API_URL}/auth/login", json=invalid_user)
        self.assertEqual(response.status_code, 400)
        print("✅ POST /api/auth/login - Invalid login correctly rejected")
        
        # 5. Test invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = requests.get(f"{API_URL}/auth/me", headers=invalid_headers)
        self.assertEqual(response.status_code, 401)
        print("✅ GET /api/auth/me - Invalid token correctly rejected")

    # 2. Books Endpoints
    def test_books_endpoints(self):
        """Test all book endpoints"""
        print("\n--- Testing Books Endpoints ---")
        
        # 1. Test get all books
        response = requests.get(f"{API_URL}/books", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        books = response.json()
        self.assertIsInstance(books, list)
        print(f"✅ GET /api/books - Get all books working, found {len(books)} books")
        
        # 2. Test create book
        response = requests.post(f"{API_URL}/books", json=self.test_book_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        book = response.json()
        self.book_ids_to_delete.append(book["id"])
        
        # Check that the book was created with the correct data
        self.assertEqual(book["title"], self.test_book_data["title"])
        self.assertEqual(book["author"], self.test_book_data["author"])
        self.assertEqual(book["category"], self.test_book_data["category"])
        print("✅ POST /api/books - Create book working")
        
        # 3. Test get book by ID
        response = requests.get(f"{API_URL}/books/{book['id']}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        retrieved_book = response.json()
        self.assertEqual(retrieved_book["id"], book["id"])
        print("✅ GET /api/books/{id} - Get book by ID working")
        
        # 4. Test update book
        update_data = {
            "status": "reading",
            "current_page": 42,
            "rating": 4,
            "review": "Excellent book!"
        }
        
        response = requests.put(f"{API_URL}/books/{book['id']}", json=update_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        updated_book = response.json()
        
        # Check that the book was updated correctly
        self.assertEqual(updated_book["status"], update_data["status"])
        self.assertEqual(updated_book["current_page"], update_data["current_page"])
        self.assertEqual(updated_book["rating"], update_data["rating"])
        self.assertEqual(updated_book["review"], update_data["review"])
        print("✅ PUT /api/books/{id} - Update book working")
        
        # 5. Test get books with filters
        # Create books with different categories and statuses
        categories = ["roman", "bd", "manga"]
        statuses = ["to_read", "reading", "completed"]
        
        for i, (category, status) in enumerate(zip(categories, statuses)):
            book_data = self.test_book_data.copy()
            book_data["title"] = f"Test Book {i+1}"
            book_data["category"] = category
            book_data["status"] = status
            
            response = requests.post(f"{API_URL}/books", json=book_data, headers=self.headers)
            self.assertEqual(response.status_code, 200)
            created_book = response.json()
            self.book_ids_to_delete.append(created_book["id"])
        
        # Test category filters
        for category in categories:
            response = requests.get(f"{API_URL}/books?category={category}", headers=self.headers)
            self.assertEqual(response.status_code, 200)
            filtered_books = response.json()
            
            # At least one book should have this category
            category_books = [b for b in filtered_books if b["category"] == category]
            self.assertGreaterEqual(len(category_books), 1)
            print(f"✅ GET /api/books?category={category} - Filter by category working")
        
        # Test status filters
        for status in statuses:
            response = requests.get(f"{API_URL}/books?status={status}", headers=self.headers)
            self.assertEqual(response.status_code, 200)
            filtered_books = response.json()
            
            # At least one book should have this status
            status_books = [b for b in filtered_books if b["status"] == status]
            self.assertGreaterEqual(len(status_books), 1)
            print(f"✅ GET /api/books?status={status} - Filter by status working")
        
        # 6. Test delete book
        response = requests.delete(f"{API_URL}/books/{book['id']}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        # Verify the book was deleted
        response = requests.get(f"{API_URL}/books/{book['id']}", headers=self.headers)
        self.assertEqual(response.status_code, 404)
        
        # Remove from cleanup list since we already deleted it
        self.book_ids_to_delete.remove(book["id"])
        
        print("✅ DELETE /api/books/{id} - Delete book working")

    # 3. Series Endpoints
    def test_series_endpoints(self):
        """Test all series endpoints"""
        print("\n--- Testing Series Endpoints ---")
        
        # 1. Test get popular series
        response = requests.get(f"{API_URL}/series/popular", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("series", data)
        self.assertIn("total", data)
        
        # Should have at least 8 series
        self.assertGreaterEqual(len(data["series"]), 8)
        print(f"✅ GET /api/series/popular - Get popular series working, found {len(data['series'])} series")
        
        # 2. Test search series
        search_terms = ["Harry Potter", "One Piece", "Astérix"]
        
        for term in search_terms:
            response = requests.get(f"{API_URL}/series/search?q={term}", headers=self.headers)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("series", data)
            self.assertIn("total", data)
            self.assertIn("search_term", data)
            
            # Should find at least one series
            self.assertGreaterEqual(len(data["series"]), 1)
            print(f"✅ GET /api/series/search?q={term} - Search series working, found {len(data['series'])} series")
        
        # 3. Test series complete
        # First create a book that belongs to a series
        book_data = {
            "title": "Harry Potter à l'école des sorciers",
            "author": "J.K. Rowling",
            "category": "roman",
            "description": "Premier tome de la saga Harry Potter",
            "total_pages": 309,
            "saga": "Harry Potter",
            "volume_number": 1
        }
        
        response = requests.post(f"{API_URL}/books", json=book_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        created_book = response.json()
        self.book_ids_to_delete.append(created_book["id"])
        
        # Auto-complete the series
        series_data = {
            "series_name": book_data["saga"],
            "target_volumes": 4
        }
        
        response = requests.post(f"{API_URL}/series/complete", json=series_data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should have created 3 more books (volumes 2-4)
        self.assertEqual(len(data["created_books"]), 3)
        
        # Add the created books to the cleanup list
        for book in data["created_books"]:
            self.book_ids_to_delete.append(book["id"])
            
        print(f"✅ POST /api/series/complete - Series complete working, created {len(data['created_books'])} additional volumes")
        
        # 4. Test get series library
        # Create a series in the library
        series_data = {
            "series_name": "Test Series",
            "authors": ["Test Author"],
            "category": "roman",
            "total_volumes": 3,
            "volumes": [
                {"volume_number": 1, "volume_title": "Test Series Volume 1", "is_read": False},
                {"volume_number": 2, "volume_title": "Test Series Volume 2", "is_read": False},
                {"volume_number": 3, "volume_title": "Test Series Volume 3", "is_read": False}
            ],
            "description_fr": "Test series description",
            "cover_image_url": "https://example.com/test-series.jpg",
            "first_published": "2020",
            "last_published": "2022",
            "publisher": "Test Publisher",
            "series_status": "to_read"
        }
        
        response = requests.post(f"{API_URL}/series/library", json=series_data, headers=self.headers)
        if response.status_code == 200:
            created_series = response.json()
            self.series_ids_to_delete.append(created_series["series_id"])
            
            # Get all series
            response = requests.get(f"{API_URL}/series/library", headers=self.headers)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("series", data)
            self.assertIn("total_count", data)
            
            # Should have at least one series
            self.assertGreaterEqual(len(data["series"]), 1)
            print(f"✅ GET /api/series/library - Get series library working, found {len(data['series'])} series")
        else:
            print(f"⚠️ POST /api/series/library - Could not create test series: {response.text}")

    # 4. Open Library Endpoints
    def test_openlibrary_endpoints(self):
        """Test Open Library endpoints"""
        print("\n--- Testing Open Library Endpoints ---")
        
        # Test search
        search_terms = ["Harry Potter", "Le Petit Prince", "One Piece"]
        
        for term in search_terms:
            response = requests.get(f"{API_URL}/openlibrary/search?q={term}", headers=self.headers)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # Should have books, total_found, and filters_applied
            self.assertIn("books", data)
            self.assertIn("total_found", data)
            self.assertIn("filters_applied", data)
            
            # Should find at least one book
            self.assertGreaterEqual(len(data["books"]), 1)
            print(f"✅ GET /api/openlibrary/search?q={term} - Open Library search working, found {len(data['books'])} books")

    # 5. Stats Endpoints
    def test_stats_endpoint(self):
        """Test stats endpoint"""
        print("\n--- Testing Stats Endpoint ---")
        
        response = requests.get(f"{API_URL}/stats", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that all required fields are present
        required_fields = [
            "total_books", "completed_books", "reading_books", "to_read_books",
            "categories", "authors_count", "sagas_count", "auto_added_count"
        ]
        
        for field in required_fields:
            self.assertIn(field, data)
            
        # Check that categories contains the expected subcategories
        self.assertIn("roman", data["categories"])
        self.assertIn("bd", data["categories"])
        self.assertIn("manga", data["categories"])
        
        print("✅ GET /api/stats - Stats endpoint working")

    # 6. Health Check
    def test_health_check(self):
        """Test health check endpoint"""
        print("\n--- Testing Health Check Endpoint ---")
        
        response = requests.get(f"{BACKEND_URL}/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["database"], "connected")
        self.assertIn("timestamp", data)
        print("✅ GET /health - Health check endpoint working")

if __name__ == "__main__":
    unittest.main(verbosity=2)