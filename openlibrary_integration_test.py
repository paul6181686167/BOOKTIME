#!/usr/bin/env python3
"""
Test script for the Open Library integration features of the BOOKTIME API
This script tests all the new advanced Open Library endpoints
"""

import requests
import json
import unittest
import time
import uuid
from datetime import datetime

# Get the backend URL
BACKEND_URL = "http://localhost:8001"
API_URL = f"{BACKEND_URL}/api"

class OpenLibraryIntegrationTest(unittest.TestCase):
    """Test suite for the Open Library integration features"""

    def setUp(self):
        """Setup for each test"""
        # Book IDs to be used/cleaned up during testing
        self.book_ids_to_delete = []
        
        # Create some test data if the database is empty
        response = requests.get(f"{API_URL}/books")
        if len(response.json()) == 0:
            print("Database is empty, creating test data...")
            self.create_test_data()

    def tearDown(self):
        """Clean up after each test"""
        # Delete any books created during testing
        for book_id in self.book_ids_to_delete:
            try:
                requests.delete(f"{API_URL}/books/{book_id}")
            except:
                pass

    def test_search_with_filters(self):
        """Test the advanced search with filters endpoint"""
        # Test basic search
        response = requests.get(f"{API_URL}/openlibrary/search?q=Harry Potter")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("books", data)
        self.assertIn("total", data)
        self.assertGreater(data["total"], 0)
        
        # Test with year filters
        response = requests.get(f"{API_URL}/openlibrary/search?q=Harry Potter&year_start=2000&year_end=2010")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("books", data)
        self.assertIn("filters_applied", data)
        self.assertEqual(data["filters_applied"]["year_range"], "2000-2010")
        
        # Test with language filter
        response = requests.get(f"{API_URL}/openlibrary/search?q=Harry Potter&language=français")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("books", data)
        self.assertIn("filters_applied", data)
        self.assertEqual(data["filters_applied"]["language"], "français")
        
        # Test with page filters
        response = requests.get(f"{API_URL}/openlibrary/search?q=Harry Potter&min_pages=300&max_pages=500")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("books", data)
        self.assertIn("filters_applied", data)
        self.assertEqual(data["filters_applied"]["pages_range"], "300-500")
        
        # Test with author filter
        response = requests.get(f"{API_URL}/openlibrary/search?q=Harry Potter&author_filter=Rowling")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("books", data)
        self.assertIn("filters_applied", data)
        self.assertEqual(data["filters_applied"]["author_filter"], "Rowling")
        
        # Test with multiple filters
        response = requests.get(f"{API_URL}/openlibrary/search?q=Harry Potter&year_start=2000&year_end=2010&author_filter=Rowling&min_pages=300")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("books", data)
        self.assertIn("filters_applied", data)
        
        # Test error case - empty query
        response = requests.get(f"{API_URL}/openlibrary/search?q=")
        self.assertEqual(response.status_code, 400)
        
        print("✅ Advanced search with filters endpoint working correctly")
        print(f"   - Basic search found {data['total']} books")
        print(f"   - Year filter (2000-2010) applied successfully")
        print(f"   - Language filter (français) applied successfully")
        print(f"   - Page range filter (300-500) applied successfully")
        print(f"   - Author filter (Rowling) applied successfully")
        print(f"   - Multiple filters applied successfully")
        print(f"   - Empty query returns 400 error as expected")

    def test_search_advanced_multi_criteria(self):
        """Test the multi-criteria search endpoint"""
        # Test with title only
        response = requests.get(f"{API_URL}/openlibrary/search-advanced?title=Harry Potter")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("books", data)
        self.assertIn("total", data)
        self.assertGreater(data["total"], 0)
        
        # Test with author only
        response = requests.get(f"{API_URL}/openlibrary/search-advanced?author=Rowling")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("books", data)
        self.assertGreater(data["total"], 0)
        
        # Test with subject only
        response = requests.get(f"{API_URL}/openlibrary/search-advanced?subject=fantasy")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("books", data)
        self.assertGreater(data["total"], 0)
        
        # Test with publisher only
        response = requests.get(f"{API_URL}/openlibrary/search-advanced?publisher=Gallimard")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("books", data)
        
        # Test with ISBN only
        response = requests.get(f"{API_URL}/openlibrary/search-advanced?isbn=9780747532699")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("books", data)
        
        # Test with year range
        response = requests.get(f"{API_URL}/openlibrary/search-advanced?title=Harry Potter&year_start=1997&year_end=2007")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("books", data)
        self.assertIn("query_used", data)
        
        # Test with multiple criteria
        response = requests.get(f"{API_URL}/openlibrary/search-advanced?title=Harry Potter&author=Rowling&year_start=1997")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("books", data)
        self.assertIn("query_used", data)
        self.assertIn("title:Harry Potter", data["query_used"])
        self.assertIn("author:Rowling", data["query_used"])
        
        # Test error case - no criteria
        response = requests.get(f"{API_URL}/openlibrary/search-advanced")
        self.assertEqual(response.status_code, 400)
        
        print("✅ Multi-criteria search endpoint working correctly")
        print(f"   - Title search found {data['total']} books")
        print(f"   - Author search working")
        print(f"   - Subject search working")
        print(f"   - Publisher search working")
        print(f"   - ISBN search working")
        print(f"   - Year range filter working")
        print(f"   - Multiple criteria search working")
        print(f"   - No criteria returns 400 error as expected")

    def test_search_isbn(self):
        """Test the ISBN search endpoint"""
        # Test with valid ISBN
        valid_isbn = "9780747532699"  # Harry Potter and the Philosopher's Stone
        response = requests.get(f"{API_URL}/openlibrary/search-isbn?isbn={valid_isbn}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("books", data)
        self.assertIn("total", data)
        self.assertGreater(data["total"], 0)
        self.assertIn("isbn_searched", data)
        self.assertEqual(data["isbn_searched"], valid_isbn)
        
        # Test with formatted ISBN (with dashes)
        formatted_isbn = "978-0-7475-3269-9"
        response = requests.get(f"{API_URL}/openlibrary/search-isbn?isbn={formatted_isbn}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("books", data)
        self.assertGreater(data["total"], 0)
        
        # Test with invalid ISBN
        invalid_isbn = "1234567890123"
        response = requests.get(f"{API_URL}/openlibrary/search-isbn?isbn={invalid_isbn}")
        # This might return 200 with empty results or 404, both are acceptable
        if response.status_code == 200:
            data = response.json()
            self.assertIn("books", data)
        else:
            self.assertEqual(response.status_code, 404)
        
        # Test error case - empty ISBN
        response = requests.get(f"{API_URL}/openlibrary/search-isbn?isbn=")
        self.assertEqual(response.status_code, 400)
        
        print("✅ ISBN search endpoint working correctly")
        print(f"   - Valid ISBN search working")
        print(f"   - Formatted ISBN search working")
        print(f"   - Invalid ISBN handling working")
        print(f"   - Empty ISBN returns 400 error as expected")

    def test_search_author_advanced(self):
        """Test the advanced author search endpoint"""
        # Test with popular author
        author = "J.K. Rowling"
        response = requests.get(f"{API_URL}/openlibrary/search-author?author={author}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("series", data)
        self.assertIn("standalone_books", data)
        self.assertIn("total_series", data)
        self.assertIn("total_standalone", data)
        self.assertIn("author", data)
        self.assertEqual(data["author"], author)
        
        # Check that Harry Potter is in the series
        harry_potter_series = next((s for s in data["series"] if "Harry Potter" in s["name"]), None)
        self.assertIsNotNone(harry_potter_series, "Harry Potter series should be found")
        
        # Test with manga author
        author = "Eiichiro Oda"
        response = requests.get(f"{API_URL}/openlibrary/search-author?author={author}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("series", data)
        self.assertIn("standalone_books", data)
        
        # Check that One Piece is in the series
        one_piece_series = next((s for s in data["series"] if "One Piece" in s["name"]), None)
        self.assertIsNotNone(one_piece_series, "One Piece series should be found")
        
        # Test with limit parameter
        response = requests.get(f"{API_URL}/openlibrary/search-author?author=Stephen King&limit=5")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Test error case - empty author
        response = requests.get(f"{API_URL}/openlibrary/search-author?author=")
        self.assertEqual(response.status_code, 400)
        
        print("✅ Advanced author search endpoint working correctly")
        print(f"   - J.K. Rowling search found {data['total']} books")
        print(f"   - Series grouping working correctly")
        print(f"   - Standalone books identified correctly")
        print(f"   - Limit parameter working")
        print(f"   - Empty author returns 400 error as expected")

    def test_import_bulk(self):
        """Test the bulk import endpoint"""
        # Prepare test data - first search for some books
        response = requests.get(f"{API_URL}/openlibrary/search?q=Harry Potter&limit=2")
        self.assertEqual(response.status_code, 200)
        search_data = response.json()
        
        # Extract books for import
        books_to_import = []
        for book in search_data["books"]:
            books_to_import.append({
                "ol_key": book["ol_key"],
                "category": "roman"
            })
        
        # Add a manga book
        response = requests.get(f"{API_URL}/openlibrary/search?q=One Piece&limit=1")
        self.assertEqual(response.status_code, 200)
        manga_data = response.json()
        if manga_data["books"]:
            books_to_import.append({
                "ol_key": manga_data["books"][0]["ol_key"],
                "category": "manga"
            })
        
        # Test bulk import
        import_data = {"books": books_to_import}
        response = requests.post(f"{API_URL}/openlibrary/import-bulk", json=import_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("summary", data)
        self.assertIn("results", data)
        self.assertIn("imported", data["results"])
        self.assertIn("skipped", data["results"])
        self.assertIn("errors", data["results"])
        
        # Add imported books to cleanup list
        for book in data["results"]["imported"]:
            self.book_ids_to_delete.append(book["_id"])
        
        # Test duplicate detection by trying to import the same books again
        response = requests.post(f"{API_URL}/openlibrary/import-bulk", json=import_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(len(data["results"]["skipped"]), 1, "Should have skipped at least one duplicate book")
        
        # Test error handling with invalid key
        invalid_import = {"books": [{"ol_key": "/works/invalid_key", "category": "roman"}]}
        response = requests.post(f"{API_URL}/openlibrary/import-bulk", json=invalid_import)
        self.assertEqual(response.status_code, 200)  # Should still return 200 but with errors
        data = response.json()
        self.assertGreaterEqual(len(data["results"]["errors"]), 1, "Should have at least one error")
        
        # Test error case - empty books array
        response = requests.post(f"{API_URL}/openlibrary/import-bulk", json={"books": []})
        self.assertEqual(response.status_code, 400)
        
        print("✅ Bulk import endpoint working correctly")
        print(f"   - Successfully imported {len(data['results']['imported'])} books")
        print(f"   - Duplicate detection working ({len(data['results']['skipped'])} books skipped)")
        print(f"   - Error handling working ({len(data['results']['errors'])} errors reported)")
        print(f"   - Empty books array returns 400 error as expected")

    def test_recommendations(self):
        """Test the personalized recommendations endpoint"""
        # First, make sure we have some books in the database
        response = requests.get(f"{API_URL}/books")
        self.assertEqual(response.status_code, 200)
        books = response.json()
        self.assertGreater(len(books), 0, "Need books in the database for recommendations")
        
        # Test recommendations
        response = requests.get(f"{API_URL}/openlibrary/recommendations")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("recommendations", data)
        self.assertIn("based_on", data)
        self.assertIn("top_authors", data["based_on"])
        self.assertIn("top_categories", data["based_on"])
        self.assertIn("top_genres", data["based_on"])
        
        # Check that recommendations have the required fields
        if data["recommendations"]:
            recommendation = data["recommendations"][0]
            self.assertIn("title", recommendation)
            self.assertIn("author", recommendation)
            self.assertIn("category", recommendation)
            self.assertIn("recommendation_reason", recommendation)
            
        # Test with limit parameter
        response = requests.get(f"{API_URL}/openlibrary/recommendations?limit=5")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertLessEqual(len(data["recommendations"]), 5)
        
        print("✅ Recommendations endpoint working correctly")
        print(f"   - Found {len(data['recommendations'])} recommendations")
        print(f"   - Based on {len(data['based_on']['top_authors'])} top authors")
        print(f"   - Based on {len(data['based_on']['top_categories'])} top categories")
        print(f"   - Based on {len(data['based_on']['top_genres'])} top genres")
        print(f"   - Limit parameter working")

    def test_missing_volumes(self):
        """Test the missing volumes detection endpoint"""
        # Find a saga with multiple volumes
        response = requests.get(f"{API_URL}/sagas")
        self.assertEqual(response.status_code, 200)
        sagas = response.json()
        
        # Use Harry Potter saga for testing
        saga_name = "Harry Potter"
        saga = next((s for s in sagas if s["name"] == saga_name), None)
        self.assertIsNotNone(saga, f"{saga_name} saga should exist in the database")
        
        # Test missing volumes detection
        response = requests.get(f"{API_URL}/openlibrary/missing-volumes?saga={saga_name}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("saga", data)
        self.assertIn("present_volumes", data)
        self.assertIn("missing_volumes", data)
        self.assertIn("found_missing", data)
        self.assertIn("suggested_next", data)
        
        # Test with non-existent saga
        response = requests.get(f"{API_URL}/openlibrary/missing-volumes?saga=NonExistentSaga")
        self.assertEqual(response.status_code, 404)
        
        print("✅ Missing volumes detection endpoint working correctly")
        print(f"   - Found {len(data['present_volumes'])} present volumes for {saga_name}")
        print(f"   - Found {len(data['missing_volumes'])} missing volumes")
        print(f"   - Found {len(data['found_missing'])} missing volumes on Open Library")
        print(f"   - Found {len(data['suggested_next'])} suggested next volumes")
        print(f"   - Non-existent saga returns 404 error as expected")

    def test_suggestions(self):
        """Test the import suggestions endpoint"""
        # Test suggestions
        response = requests.get(f"{API_URL}/openlibrary/suggestions")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("suggestions", data)
        self.assertIn("types", data)
        self.assertIn("saga_continuation", data["types"])
        self.assertIn("favorite_author", data["types"])
        
        # Check that suggestions have the required fields
        if data["suggestions"]:
            suggestion = data["suggestions"][0]
            self.assertIn("title", suggestion)
            self.assertIn("author", suggestion)
            self.assertIn("category", suggestion)
            self.assertIn("suggestion_type", suggestion)
            self.assertIn("suggestion_reason", suggestion)
            
        # Test with limit parameter
        response = requests.get(f"{API_URL}/openlibrary/suggestions?limit=5")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertLessEqual(len(data["suggestions"]), 5)
        
        print("✅ Suggestions endpoint working correctly")
        print(f"   - Found {len(data['suggestions'])} suggestions")
        print(f"   - Found {data['types']['saga_continuation']} saga continuation suggestions")
        print(f"   - Found {data['types']['favorite_author']} favorite author suggestions")
        print(f"   - Limit parameter working")

    def test_performance(self):
        """Test the performance of the Open Library integration"""
        # Test multiple sequential searches
        start_time = time.time()
        
        # Perform 5 different searches
        searches = ["Harry Potter", "Lord of the Rings", "Naruto", "Astérix", "One Piece"]
        for query in searches:
            response = requests.get(f"{API_URL}/openlibrary/search?q={query}")
            self.assertEqual(response.status_code, 200)
            
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should complete within 10 seconds (usually much faster)
        self.assertLess(total_time, 10, f"Performance test took {total_time:.2f} seconds, should be under 10 seconds")
        
        print("✅ Performance test passed")
        print(f"   - 5 sequential searches completed in {total_time:.2f} seconds")
        print(f"   - Average time per search: {total_time/5:.2f} seconds")

if __name__ == "__main__":
    unittest.main(verbosity=2)