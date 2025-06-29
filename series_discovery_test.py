import requests
import json
import unittest
import uuid
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://8c7e2f13-c249-4384-9811-ccdf587ab2c4.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class SeriesDiscoveryTest(unittest.TestCase):
    """Test suite for the Series Discovery feature"""

    def setUp(self):
        """Setup for each test - login with an existing user"""
        # Use an existing user
        self.test_user = {
            "first_name": "Test",
            "last_name": "User"
        }
        
        # Login with the user
        response = requests.post(f"{API_URL}/auth/login", json=self.test_user)
        self.assertEqual(response.status_code, 200, "Failed to login with test user")
        
        user_data = response.json()
        self.token = user_data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Book IDs to be cleaned up after tests
        self.book_ids_to_delete = []

    def tearDown(self):
        """Clean up after each test"""
        # Delete any books created during testing
        for book_id in self.book_ids_to_delete:
            try:
                requests.delete(f"{API_URL}/books/{book_id}", headers=self.headers)
            except:
                pass

    def test_discover_series_by_name(self):
        """Test discovering a series by name"""
        # Test with Harry Potter series
        series_name = "Harry Potter"
        response = requests.get(f"{API_URL}/series/discover?series_name={series_name}", headers=self.headers)
        
        self.assertEqual(response.status_code, 200, "Series discovery endpoint failed")
        data = response.json()
        
        # Check that the response has the expected structure
        self.assertEqual(data["series_name"], series_name)
        self.assertIn("statistics", data)
        self.assertIn("books", data)
        self.assertIn("recommendations", data)
        
        # Check statistics
        stats = data["statistics"]
        self.assertIn("total_discovered", stats)
        self.assertIn("owned_count", stats)
        self.assertIn("completion_percentage", stats)
        self.assertIn("main_series_count", stats)
        self.assertIn("main_series_owned", stats)
        self.assertIn("main_series_completion", stats)
        self.assertIn("missing_volumes", stats)
        
        # Check that we found some books
        self.assertGreater(stats["total_discovered"], 0, "No books discovered for Harry Potter")
        
        # Check book categories
        books = data["books"]
        self.assertIn("main_series", books)
        self.assertIn("spin_offs", books)
        self.assertIn("companions", books)
        self.assertIn("related", books)
        
        # Check that main series has books
        self.assertGreater(len(books["main_series"]), 0, "No main series books found for Harry Potter")
        
        # Check book metadata
        first_book = books["main_series"][0]
        self.assertIn("title", first_book)
        self.assertIn("author", first_book)
        self.assertIn("cover_url", first_book)
        self.assertIn("volume_number", first_book)
        self.assertIn("ol_key", first_book)
        self.assertIn("is_owned", first_book)
        
        # Verify J.K. Rowling is the author
        self.assertIn("Rowling", first_book["author"], "J.K. Rowling should be the author of Harry Potter books")
        
        print(f"✅ Series discovery for '{series_name}' works correctly")
        print(f"   Found {stats['total_discovered']} books in total")
        print(f"   Main series: {stats['main_series_count']} books")
        print(f"   First book: {first_book['title']} by {first_book['author']}")

    def test_discover_series_by_author(self):
        """Test discovering a series by author"""
        # Test with J.K. Rowling as author
        author = "J.K. Rowling"
        response = requests.get(f"{API_URL}/series/discover?series_name=Harry Potter&author={author}", headers=self.headers)
        
        self.assertEqual(response.status_code, 200, "Series discovery by author endpoint failed")
        data = response.json()
        
        # Check that the response has the expected structure
        self.assertEqual(data["author"], author)
        
        # Check statistics
        stats = data["statistics"]
        self.assertGreater(stats["total_discovered"], 0, f"No books discovered for author {author}")
        
        # Check that all main series books are by the author
        books = data["books"]["main_series"]
        for book in books:
            self.assertIn(author, book["author"], f"Book {book['title']} should be by {author}")
        
        print(f"✅ Series discovery for author '{author}' works correctly")
        print(f"   Found {stats['total_discovered']} books in total")
        print(f"   Main series: {stats['main_series_count']} books")

    def test_statistics_accuracy(self):
        """Test the accuracy of the statistics returned by the discover endpoint"""
        # Test with Harry Potter series
        series_name = "Harry Potter"
        response = requests.get(f"{API_URL}/series/discover?series_name={series_name}", headers=self.headers)
        
        self.assertEqual(response.status_code, 200, "Series discovery endpoint failed")
        data = response.json()
        
        # Check statistics calculations
        stats = data["statistics"]
        books = data["books"]
        
        # Count books in each category
        total_books_in_response = (
            len(books["main_series"]) + 
            len(books["spin_offs"]) + 
            len(books["companions"]) + 
            len(books["related"])
        )
        
        # Verify total_discovered is at least as many as the books in the response
        # (There might be more books discovered than returned in the response due to limits)
        self.assertLessEqual(total_books_in_response, stats["total_discovered"], 
                           "Total discovered books should match or exceed the sum of all categories")
        
        # Count owned books
        owned_books = sum(1 for category in books.values() for book in category if book["is_owned"])
        
        # Verify owned_count matches
        self.assertEqual(owned_books, stats["owned_count"], 
                       "Owned count should match the number of books marked as owned")
        
        # Verify completion percentage calculation
        if stats["total_discovered"] > 0:
            expected_completion = round((owned_books / stats["total_discovered"]) * 100)
            self.assertEqual(stats["completion_percentage"], expected_completion,
                           "Completion percentage calculation is incorrect")
        
        # Verify main series completion calculation
        if stats["main_series_count"] > 0:
            owned_main_series = sum(1 for book in books["main_series"] if book["is_owned"])
            expected_main_completion = round((owned_main_series / stats["main_series_count"]) * 100)
            self.assertEqual(stats["main_series_completion"], expected_main_completion,
                           "Main series completion calculation is incorrect")
        
        print(f"✅ Statistics for '{series_name}' are accurate")
        print(f"   Total discovered: {stats['total_discovered']}")
        print(f"   Owned: {stats['owned_count']}")
        print(f"   Completion: {stats['completion_percentage']}%")
        print(f"   Main series completion: {stats['main_series_completion']}%")

    def test_import_missing_books(self):
        """Test importing missing books from a series"""
        # First discover the series to get book keys
        series_name = "Harry Potter"
        response = requests.get(f"{API_URL}/series/discover?series_name={series_name}", headers=self.headers)
        
        self.assertEqual(response.status_code, 200, "Series discovery endpoint failed")
        data = response.json()
        
        # Get OL keys for a few books that aren't owned
        unowned_books = [book for book in data["books"]["main_series"] if not book["is_owned"]]
        
        if not unowned_books:
            self.skipTest("No unowned books found to import")
        
        # Take up to 2 books to import
        books_to_import = unowned_books[:2]
        ol_keys = [book["ol_key"].replace("/works/", "") for book in books_to_import]
        
        # Import the books
        import_data = {
            "ol_keys": ol_keys,
            "series_name": series_name
        }
        
        response = requests.post(f"{API_URL}/series/import-missing", json=import_data, headers=self.headers)
        
        self.assertEqual(response.status_code, 200, "Import missing books endpoint failed")
        import_result = response.json()
        
        # Check that the import was successful
        self.assertIn("imported_books", import_result)
        self.assertIn("statistics", import_result)
        
        # Add imported book IDs to cleanup list
        for book in import_result["imported_books"]:
            self.book_ids_to_delete.append(book["id"])
        
        # Verify import statistics
        stats = import_result["statistics"]
        self.assertEqual(stats["total_requested"], len(ol_keys), "Total requested count is incorrect")
        self.assertGreaterEqual(stats["imported"], 1, "At least one book should be imported")
        
        # Verify imported books have the correct series name
        for book in import_result["imported_books"]:
            self.assertEqual(book["saga"], series_name, f"Book {book['title']} should be in the {series_name} saga")
            self.assertEqual(book["status"], "to_read", f"Book {book['title']} should have 'to_read' status")
        
        print(f"✅ Successfully imported {stats['imported']} books from '{series_name}'")
        for book in import_result["imported_books"]:
            print(f"   - {book['title']} (Volume {book['volume_number']})")

if __name__ == "__main__":
    unittest.main(verbosity=2)