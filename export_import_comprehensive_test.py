import requests
import json
import unittest
import uuid
import os
import time
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://6efff0cd-ae10-47b6-9f6c-a805e1b2bcd5.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class ExportImportAPITest(unittest.TestCase):
    """Test suite for the Export/Import API functionality"""

    def setUp(self):
        """Setup for each test"""
        # Create a test user with a unique name to avoid conflicts
        self.test_user = {
            "first_name": f"Test{uuid.uuid4().hex[:6]}",
            "last_name": "ExportImport"
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
        
        # Add a test book to ensure we have data to export
        self.test_book = {
            "title": f"Test Book {uuid.uuid4().hex[:6]}",
            "author": "Test Author",
            "category": "roman",
            "status": "to_read"
        }
        
        response = requests.post(f"{API_URL}/books", json=self.test_book, headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        self.book_data = response.json()
        self.book_id = self.book_data["id"]
        
        # Wait a moment for the database to update
        time.sleep(1)

    def tearDown(self):
        """Clean up after each test"""
        # Delete the test book
        if hasattr(self, 'book_id'):
            requests.delete(f"{API_URL}/books/{self.book_id}", headers=self.auth_headers)

    def test_get_export_formats(self):
        """Test getting supported export formats"""
        response = requests.get(f"{API_URL}/export-import/export/formats", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that the response contains the expected fields
        self.assertIn("supported_formats", data)
        self.assertIn("formats_details", data)
        self.assertIn("recommendations", data)
        
        # Check that the supported formats include the expected formats
        supported_formats = data["supported_formats"]
        self.assertIn("json", supported_formats)
        self.assertIn("csv", supported_formats)
        self.assertIn("excel", supported_formats)
        self.assertIn("full_backup", supported_formats)
        
        # Check format details
        formats_details = data["formats_details"]
        for format_type in ["json", "csv", "excel", "full_backup"]:
            self.assertIn(format_type, formats_details)
            format_info = formats_details[format_type]
            self.assertIn("name", format_info)
            self.assertIn("description", format_info)
            self.assertIn("extension", format_info)
            self.assertIn("supports_metadata", format_info)
            self.assertIn("best_for", format_info)
        
        print("✅ GET /api/export-import/export/formats endpoint working correctly")

    def test_get_import_formats(self):
        """Test getting supported import formats"""
        response = requests.get(f"{API_URL}/export-import/import/formats", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that the response contains the expected fields
        self.assertIn("supported_formats", data)
        self.assertIn("tips", data)
        self.assertIn("max_file_size_mb", data)
        
        # Check that the supported formats include the expected formats
        supported_formats = data["supported_formats"]
        self.assertIn("json", supported_formats)
        self.assertIn("csv", supported_formats)
        self.assertIn("goodreads", supported_formats)
        self.assertIn("excel", supported_formats)
        
        # Check format details
        for format_type in ["json", "csv", "goodreads", "excel"]:
            format_info = supported_formats[format_type]
            self.assertIn("name", format_info)
            self.assertIn("description", format_info)
            self.assertIn("extensions", format_info)
            self.assertIn("compatibility", format_info)
            self.assertIn("supports_all_fields", format_info)
        
        print("✅ GET /api/export-import/import/formats endpoint working correctly")

    def test_export_json(self):
        """Test exporting data in JSON format"""
        response = requests.get(
            f"{API_URL}/export-import/export?format_type=json",
            headers=self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        
        # Check content type (may include charset)
        self.assertTrue(response.headers["Content-Type"].startswith("application/json"))
        
        # Check that the response contains the expected data
        data = response.json()
        self.assertIn("books", data)
        
        # Check that the books data contains at least one book
        books = data["books"]
        self.assertGreaterEqual(len(books), 1)
        
        # Get all book titles
        book_titles = [book.get("title") for book in books]
        
        # Check if our test book is in the exported data
        # Note: The export might include books from other tests
        self.assertTrue(any(self.test_book["title"] in title for title in book_titles),
                       f"Test book '{self.test_book['title']}' not found in exported data")
        
        print("✅ GET /api/export-import/export?format_type=json endpoint working correctly")

    def test_export_csv(self):
        """Test exporting data in CSV format"""
        response = requests.get(
            f"{API_URL}/export-import/export?format_type=csv",
            headers=self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        
        # Check content type (may include charset)
        self.assertTrue(response.headers["Content-Type"].startswith("text/csv"))
        
        # Check that the response contains CSV data
        csv_data = response.content.decode("utf-8")
        
        # Check for header row
        self.assertIn("title,author,category", csv_data)
        
        # Check if our test book is in the exported data
        self.assertIn(self.test_book["title"], csv_data)
        self.assertIn(self.test_book["author"], csv_data)
        self.assertIn(self.test_book["category"], csv_data)
        
        print("✅ GET /api/export-import/export?format_type=csv endpoint working correctly")

    def test_export_excel(self):
        """Test exporting data in Excel format"""
        response = requests.get(
            f"{API_URL}/export-import/export?format_type=excel",
            headers=self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        
        # Check content type
        self.assertEqual(response.headers["Content-Type"], 
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        # Check that the response contains binary data (Excel file)
        self.assertGreater(len(response.content), 0)
        
        # Save the Excel file for verification
        with open("test_export.xlsx", "wb") as f:
            f.write(response.content)
        
        # Check that the file exists
        self.assertTrue(os.path.exists("test_export.xlsx"))
        
        # Clean up
        os.remove("test_export.xlsx")
        
        print("✅ GET /api/export-import/export?format_type=excel endpoint working correctly")

    def test_export_full_backup(self):
        """Test exporting data in full backup format"""
        response = requests.get(
            f"{API_URL}/export-import/export?format_type=full_backup",
            headers=self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        
        # Check content type
        self.assertEqual(response.headers["Content-Type"], "application/zip")
        
        # Check that the response contains binary data (ZIP file)
        self.assertGreater(len(response.content), 0)
        
        # Save the ZIP file for verification
        with open("test_backup.zip", "wb") as f:
            f.write(response.content)
        
        # Check that the file exists
        self.assertTrue(os.path.exists("test_backup.zip"))
        
        # Clean up
        os.remove("test_backup.zip")
        
        print("✅ GET /api/export-import/export?format_type=full_backup endpoint working correctly")

    def test_generate_template(self):
        """Test generating an import template"""
        response = requests.post(
            f"{API_URL}/export-import/templates/generate?format_type=csv",
            headers=self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        
        # Check content type (may include charset)
        self.assertTrue(response.headers["Content-Type"].startswith("text/csv"))
        
        # Check that the response contains CSV data
        csv_data = response.content.decode("utf-8")
        
        # Check for header row
        self.assertIn("title,author,category,status", csv_data)
        
        # Check for example data
        self.assertIn("Exemple Livre 1", csv_data)
        self.assertIn("Auteur Exemple", csv_data)
        
        print("✅ POST /api/export-import/templates/generate endpoint working correctly")

    def test_export_history(self):
        """Test getting export history"""
        response = requests.get(
            f"{API_URL}/export-import/user/export-history",
            headers=self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check that the response contains the expected fields
        self.assertIn("success", data)
        self.assertIn("exports", data)
        self.assertIn("message", data)
        
        # Note: The current implementation returns an empty list
        # This is expected based on the code review
        self.assertEqual(data["exports"], [])
        
        print("✅ GET /api/export-import/user/export-history endpoint working correctly")

    def test_import_preview(self):
        """Test import preview functionality"""
        # Create a simple CSV file for import
        csv_content = """title,author,category,status,rating,review,current_page,total_pages
Test Import Book 1,Test Author,roman,to_read,0,,0,200
Test Import Book 2,Test Author,bd,reading,0,,50,100
Test Import Book 3,Test Author,manga,completed,4,Great book!,300,300"""
        
        # Create a file for import preview
        files = {
            "file": ("import.csv", csv_content.encode('utf-8'), "text/csv")
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
        
        # Check file info
        file_info = data["file_info"]
        self.assertEqual(file_info["detected_format"], "csv")
        
        print("✅ POST /api/export-import/import/preview endpoint working correctly")

    def test_import_data(self):
        """Test importing data"""
        # Create a simple CSV file for import
        csv_content = """title,author,category,status,rating,review,current_page,total_pages
Test Import Book 1,Test Author,roman,to_read,0,,0,200
Test Import Book 2,Test Author,bd,reading,0,,50,100
Test Import Book 3,Test Author,manga,completed,4,Great book!,300,300"""
        
        # Create a file for import
        files = {
            "file": ("import.csv", csv_content.encode('utf-8'), "text/csv")
        }
        
        # Form data for import options
        form_data = {
            "skip_duplicates": "true",
            "update_existing": "false",
            "dry_run": "false"
        }
        
        # Get initial book count
        response = requests.get(f"{API_URL}/books", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        initial_books = response.json()
        initial_count = len(initial_books)
        
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
        
        # Verify that books were imported by checking the user's library
        response = requests.get(f"{API_URL}/books", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        books = response.json()
        
        # Verify more books were added
        self.assertGreater(len(books), initial_count)
        
        print("✅ POST /api/export-import/import endpoint working correctly")

    def test_error_handling(self):
        """Test error handling for invalid inputs"""
        # Test invalid export format
        response = requests.get(
            f"{API_URL}/export-import/export?format_type=invalid",
            headers=self.auth_headers
        )
        # Should return 400 or 500 with error message
        self.assertGreaterEqual(response.status_code, 400)
        
        # Test invalid template format
        response = requests.post(
            f"{API_URL}/export-import/templates/generate?format_type=invalid",
            headers=self.auth_headers
        )
        # Should return 400 or 500 with error message
        self.assertGreaterEqual(response.status_code, 400)
        
        print("✅ Error handling for invalid inputs works correctly")


if __name__ == "__main__":
    unittest.main(verbosity=2)