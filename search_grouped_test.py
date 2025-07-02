import requests
import json
import unittest
import uuid
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://7ae4fa51-ec10-4cd1-9cba-3578e322acb9.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class SearchGroupedAPITest(unittest.TestCase):
    """Test suite for the Booktime Search Grouped API"""

    def setUp(self):
        """Setup for each test"""
        # Register a test user
        self.user_data = {
            "first_name": "Test",
            "last_name": "User"
        }
        
        # Register and get token
        response = requests.post(f"{API_URL}/auth/register", json=self.user_data)
        if response.status_code == 200:
            data = response.json()
            self.token = data["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            # Try to login if registration fails (user might already exist)
            response = requests.post(f"{API_URL}/auth/login", json=self.user_data)
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.headers = {"Authorization": f"Bearer {self.token}"}
            else:
                self.fail(f"Failed to authenticate: {response.text}")
        
        # Create test books with saga information
        self.harry_potter_books = [
            {
                "title": "Harry Potter à l'école des sorciers",
                "author": "J.K. Rowling",
                "category": "roman",
                "saga": "Harry Potter",
                "volume_number": 1,
                "description": "Le premier tome de la saga Harry Potter"
            },
            {
                "title": "Harry Potter et la Chambre des Secrets",
                "author": "J.K. Rowling",
                "category": "roman",
                "saga": "Harry Potter",
                "volume_number": 2,
                "description": "Le deuxième tome de la saga Harry Potter"
            },
            {
                "title": "Harry Potter et le Prisonnier d'Azkaban",
                "author": "J.K. Rowling",
                "category": "roman",
                "saga": "Harry Potter",
                "volume_number": 3,
                "description": "Le troisième tome de la saga Harry Potter"
            }
        ]
        
        self.individual_books = [
            {
                "title": "Le Seigneur des Anneaux",
                "author": "J.R.R. Tolkien",
                "category": "roman",
                "description": "Un roman de fantasy épique"
            },
            {
                "title": "Naruto Tome 1",
                "author": "Masashi Kishimoto",
                "category": "manga",
                "saga": "Naruto",
                "volume_number": 1,
                "description": "Le premier tome du manga Naruto"
            }
        ]
        
        # Book IDs to be used/cleaned up during testing
        self.book_ids_to_delete = []
        
        # Create the test books
        for book in self.harry_potter_books + self.individual_books:
            response = requests.post(f"{API_URL}/books", json=book, headers=self.headers)
            if response.status_code == 200:
                book_data = response.json()
                self.book_ids_to_delete.append(book_data["id"])

    def tearDown(self):
        """Clean up after each test"""
        # Delete any books created during testing
        for book_id in self.book_ids_to_delete:
            try:
                requests.delete(f"{API_URL}/books/{book_id}", headers=self.headers)
            except:
                pass

    def test_search_grouped_basic(self):
        """Test basic search with grouping"""
        # Search for Harry Potter
        response = requests.get(f"{API_URL}/books/search-grouped?q=harry potter", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check the structure of the response
        self.assertIn("results", data)
        self.assertIn("total_books", data)
        self.assertIn("total_sagas", data)
        self.assertIn("search_term", data)
        self.assertIn("grouped_by_saga", data)
        
        # Verify the search term
        self.assertEqual(data["search_term"], "harry potter")
        
        # Verify that books are grouped by saga
        self.assertEqual(data["total_sagas"], 1)
        self.assertEqual(data["total_books"], 3)
        
        # Check the first result (should be the Harry Potter saga)
        results = data["results"]
        self.assertGreaterEqual(len(results), 1)
        
        # Find the Harry Potter saga in the results
        harry_potter_saga = None
        for result in results:
            if result.get("type") == "saga" and result.get("name") == "Harry Potter":
                harry_potter_saga = result
                break
        
        self.assertIsNotNone(harry_potter_saga, "Harry Potter saga should be in the results")
        
        # Verify the saga structure
        self.assertEqual(harry_potter_saga["type"], "saga")
        self.assertEqual(harry_potter_saga["name"], "Harry Potter")
        self.assertEqual(harry_potter_saga["total_books"], 3)
        self.assertEqual(harry_potter_saga["author"], "J.K. Rowling")
        self.assertEqual(harry_potter_saga["category"], "roman")
        
        # Verify the books in the saga
        self.assertEqual(len(harry_potter_saga["books"]), 3)
        
        print("✅ Basic search with grouping works correctly")
        print(f"   Found {data['total_books']} books in {data['total_sagas']} saga")

    def test_search_grouped_with_existing_saga(self):
        """Test search with a known saga"""
        # Search for Harry Potter
        response = requests.get(f"{API_URL}/books/search-grouped?q=harry", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify that books are grouped by saga
        self.assertEqual(data["total_sagas"], 1)
        self.assertGreaterEqual(data["total_books"], 3)
        
        # Find the Harry Potter saga in the results
        harry_potter_saga = None
        for result in data["results"]:
            if result.get("type") == "saga" and result.get("name") == "Harry Potter":
                harry_potter_saga = result
                break
        
        self.assertIsNotNone(harry_potter_saga, "Harry Potter saga should be in the results")
        
        # Verify the saga statistics
        self.assertEqual(harry_potter_saga["total_books"], 3)
        self.assertEqual(harry_potter_saga["completed_books"] + harry_potter_saga["reading_books"] + harry_potter_saga["to_read_books"], 3)
        
        print("✅ Search with existing saga works correctly")
        print(f"   Found Harry Potter saga with {harry_potter_saga['total_books']} books")
        print(f"   Completed: {harry_potter_saga['completed_books']}, Reading: {harry_potter_saga['reading_books']}, To Read: {harry_potter_saga['to_read_books']}")

    def test_search_grouped_with_individual_book(self):
        """Test search with an individual book (no saga)"""
        # Search for Seigneur des Anneaux
        response = requests.get(f"{API_URL}/books/search-grouped?q=seigneur", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify that there are no sagas
        self.assertEqual(data["total_sagas"], 0)
        self.assertEqual(data["total_books"], 1)
        
        # Check the first result (should be the individual book)
        results = data["results"]
        self.assertEqual(len(results), 1)
        
        # Verify the book structure
        book = results[0]
        self.assertEqual(book["type"], "book")
        self.assertEqual(book["title"], "Le Seigneur des Anneaux")
        self.assertEqual(book["author"], "J.R.R. Tolkien")
        
        print("✅ Search with individual book works correctly")
        print(f"   Found individual book: {book['title']} by {book['author']}")

    def test_search_grouped_data_structure(self):
        """Test the data structure of search results"""
        # Search for all books
        response = requests.get(f"{API_URL}/books/search-grouped?q=tome", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check each result for proper structure
        for result in data["results"]:
            # Check type field
            self.assertIn("type", result)
            
            if result["type"] == "saga":
                # Check saga fields
                self.assertIn("name", result)
                self.assertIn("books", result)
                self.assertIn("total_books", result)
                self.assertIn("completed_books", result)
                self.assertIn("reading_books", result)
                self.assertIn("to_read_books", result)
                self.assertIn("author", result)
                self.assertIn("category", result)
                self.assertIn("latest_volume", result)
                
                # Check books array
                self.assertIsInstance(result["books"], list)
                self.assertEqual(len(result["books"]), result["total_books"])
                
            elif result["type"] == "book":
                # Check individual book fields
                self.assertIn("id", result)
                self.assertIn("title", result)
                self.assertIn("author", result)
                self.assertIn("category", result)
                self.assertIn("status", result)
                
        print("✅ Search results data structure is correct")
        print(f"   Verified structure of {len(data['results'])} results")

    def test_search_grouped_with_empty_term(self):
        """Test search with empty or short term"""
        # Test with empty term
        response = requests.get(f"{API_URL}/books/search-grouped?q=", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should return empty results
        self.assertEqual(len(data["results"]), 0)
        self.assertEqual(data["total_books"], 0)
        self.assertEqual(data["total_sagas"], 0)
        
        # Test with short term (less than 2 characters)
        response = requests.get(f"{API_URL}/books/search-grouped?q=a", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Should return empty results
        self.assertEqual(len(data["results"]), 0)
        self.assertEqual(data["total_books"], 0)
        self.assertEqual(data["total_sagas"], 0)
        
        print("✅ Search with empty or short term returns empty results as expected")

if __name__ == "__main__":
    unittest.main(verbosity=2)