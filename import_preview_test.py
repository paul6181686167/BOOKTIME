import requests
import json
import unittest
import uuid
import os
import time
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://d0768c47-f39d-488a-b0c3-1e379d770bfa.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class ImportPreviewTest(unittest.TestCase):
    """Test suite for the Import/Preview functionality"""

    def setUp(self):
        """Setup for each test"""
        # Create a test user
        self.test_user = {
            "first_name": f"Test{uuid.uuid4().hex[:6]}",
            "last_name": "ImportPreview"
        }
        
        # Register the test user
        response = requests.post(f"{API_URL}/auth/register", json=self.test_user)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.token = data["access_token"]
        self.user_id = data["user"]["id"]
        
        # Headers for authenticated requests
        self.auth_headers = {
            "Authorization": f"Bearer {self.token}"
        }
        
        # Create a simple CSV file for import
        self.csv_content = """title,author,category,status,rating,review,current_page,total_pages
Test Import Book 1,Test Author,roman,to_read,0,,0,200
Test Import Book 2,Test Author,bd,reading,0,,50,100
Test Import Book 3,Test Author,manga,completed,4,Great book!,300,300"""
        
        # Create a simple JSON file for import
        self.json_content = json.dumps({
            "books": [
                {
                    "title": "Test JSON Import 1",
                    "author": "Test Author",
                    "category": "roman",
                    "status": "to_read",
                    "total_pages": 200
                },
                {
                    "title": "Test JSON Import 2",
                    "author": "Test Author",
                    "category": "bd",
                    "status": "reading",
                    "current_page": 50,
                    "total_pages": 100
                }
            ]
        })

    def test_import_preview_csv(self):
        """Test import preview with CSV file"""
        # Create a file for import preview
        files = {
            "file": ("import.csv", self.csv_content.encode('utf-8'), "text/csv")
        }
        
        # Test import preview
        response = requests.post(
            f"{API_URL}/export-import/import/preview",
            headers=self.auth_headers,
            files=files
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that the response contains the expected fields
        self.assertIn("success", data)
        self.assertIn("preview", data)
        self.assertIn("sample_books", data)
        self.assertIn("file_info", data)
        
        # Check preview data
        preview = data["preview"]
        self.assertIn("total_books_found", preview)
        self.assertIn("would_import", preview)
        self.assertIn("would_skip", preview)
        
        # Check that books would be imported
        self.assertEqual(preview["total_books_found"], 3)
        self.assertEqual(preview["would_import"], 3)
        self.assertEqual(preview["would_skip"], 0)
        
        # Check file info
        file_info = data["file_info"]
        self.assertEqual(file_info["detected_format"], "csv")
        
        print("✅ POST /api/export-import/import/preview with CSV works correctly")

    def test_import_preview_json(self):
        """Test import preview with JSON file"""
        # Create a file for import preview
        files = {
            "file": ("import.json", self.json_content.encode('utf-8'), "application/json")
        }
        
        # Test import preview
        response = requests.post(
            f"{API_URL}/export-import/import/preview",
            headers=self.auth_headers,
            files=files
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that the response contains the expected fields
        self.assertIn("success", data)
        self.assertIn("preview", data)
        self.assertIn("sample_books", data)
        self.assertIn("file_info", data)
        
        # Check preview data
        preview = data["preview"]
        self.assertIn("total_books_found", preview)
        self.assertIn("would_import", preview)
        self.assertIn("would_skip", preview)
        
        # Check that books would be imported
        self.assertEqual(preview["total_books_found"], 2)
        self.assertEqual(preview["would_import"], 2)
        self.assertEqual(preview["would_skip"], 0)
        
        # Check file info
        file_info = data["file_info"]
        self.assertEqual(file_info["detected_format"], "json")
        
        print("✅ POST /api/export-import/import/preview with JSON works correctly")

    def test_import_csv(self):
        """Test importing data from CSV"""
        # Create a file for import
        files = {
            "file": ("import.csv", self.csv_content.encode('utf-8'), "text/csv")
        }
        
        # Form data for import options
        form_data = {
            "skip_duplicates": "true",
            "update_existing": "false",
            "dry_run": "false"
        }
        
        # Test import
        response = requests.post(
            f"{API_URL}/export-import/import",
            headers=self.auth_headers,
            files=files,
            data=form_data
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that the response contains the expected fields
        self.assertIn("success", data)
        self.assertIn("summary", data)
        self.assertIn("details", data)
        
        # Check summary data
        summary = data["summary"]
        self.assertEqual(summary["total_processed"], 3)
        self.assertEqual(summary["imported_count"], 3)
        self.assertEqual(summary["skipped_count"], 0)
        self.assertEqual(summary["error_count"], 0)
        
        # Verify that the books were imported by checking the user's library
        response = requests.get(f"{API_URL}/books", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        books = response.json()
        self.assertEqual(len(books), 3)
        
        # Verify book titles
        book_titles = [book["title"] for book in books]
        self.assertIn("Test Import Book 1", book_titles)
        self.assertIn("Test Import Book 2", book_titles)
        self.assertIn("Test Import Book 3", book_titles)
        
        print("✅ POST /api/export-import/import with CSV works correctly")

    def test_import_json(self):
        """Test importing data from JSON"""
        # Create a file for import
        files = {
            "file": ("import.json", self.json_content.encode('utf-8'), "application/json")
        }
        
        # Form data for import options
        form_data = {
            "skip_duplicates": "true",
            "update_existing": "false",
            "dry_run": "false"
        }
        
        # Test import
        response = requests.post(
            f"{API_URL}/export-import/import",
            headers=self.auth_headers,
            files=files,
            data=form_data
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that the response contains the expected fields
        self.assertIn("success", data)
        self.assertIn("summary", data)
        self.assertIn("details", data)
        
        # Check summary data
        summary = data["summary"]
        self.assertEqual(summary["total_processed"], 2)
        self.assertEqual(summary["imported_count"], 2)
        self.assertEqual(summary["skipped_count"], 0)
        self.assertEqual(summary["error_count"], 0)
        
        # Verify that the books were imported by checking the user's library
        response = requests.get(f"{API_URL}/books", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        books = response.json()
        self.assertEqual(len(books), 2)
        
        # Verify book titles
        book_titles = [book["title"] for book in books]
        self.assertIn("Test JSON Import 1", book_titles)
        self.assertIn("Test JSON Import 2", book_titles)
        
        print("✅ POST /api/export-import/import with JSON works correctly")

    def test_duplicate_handling(self):
        """Test handling of duplicate books during import"""
        # First import the CSV data
        files = {
            "file": ("import.csv", self.csv_content.encode('utf-8'), "text/csv")
        }
        
        form_data = {
            "skip_duplicates": "true",
            "update_existing": "false",
            "dry_run": "false"
        }
        
        response = requests.post(
            f"{API_URL}/export-import/import",
            headers=self.auth_headers,
            files=files,
            data=form_data
        )
        self.assertEqual(response.status_code, 200)
        
        # Now try to import the same data again
        response = requests.post(
            f"{API_URL}/export-import/import/preview",
            headers=self.auth_headers,
            files=files
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that all books are detected as duplicates
        preview = data["preview"]
        self.assertEqual(preview["total_books_found"], 3)
        self.assertEqual(preview["duplicates_detected"], 3)
        self.assertEqual(preview["would_import"], 0)
        self.assertEqual(preview["would_skip"], 3)
        
        print("✅ Duplicate detection during import works correctly")


if __name__ == "__main__":
    unittest.main(verbosity=2)