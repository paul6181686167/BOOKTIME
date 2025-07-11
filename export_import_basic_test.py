import requests
import json
import unittest
import uuid
import os
import time
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://6241ed7a-f52c-44c0-b38a-428c1f2ac83c.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class ExportImportAPITest(unittest.TestCase):
    """Test suite for the Export/Import API functionality"""

    def setUp(self):
        """Setup for each test"""
        # Create a test user
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
        
        # Test book data
        self.test_books = [
            {
                "title": "Test Book 1",
                "author": "Test Author",
                "category": "roman",
                "status": "to_read",
                "total_pages": 200
            },
            {
                "title": "Test Book 2",
                "author": "Test Author",
                "category": "bd",
                "status": "reading",
                "current_page": 50,
                "total_pages": 100
            },
            {
                "title": "Test Book 3",
                "author": "Test Author",
                "category": "manga",
                "status": "completed",
                "current_page": 300,
                "total_pages": 300,
                "rating": 4,
                "review": "Great book!"
            }
        ]
        
        # Add test books to the user's library
        self.book_ids = []
        for book in self.test_books:
            response = requests.post(f"{API_URL}/books", json=book, headers=self.auth_headers)
            self.assertEqual(response.status_code, 200)
            book_data = response.json()
            self.book_ids.append(book_data["id"])
        
        # Wait a moment for the database to update
        time.sleep(1)

    def tearDown(self):
        """Clean up after each test"""
        # Delete test books
        for book_id in self.book_ids:
            requests.delete(f"{API_URL}/books/{book_id}", headers=self.auth_headers)

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
        self.assertIn("user_id", data)
        
        # Check that the books data contains our test books
        books = data["books"]
        self.assertEqual(len(books), 3)
        
        # Verify book titles
        book_titles = [book["title"] for book in books]
        for test_book in self.test_books:
            self.assertIn(test_book["title"], book_titles)
        
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
        self.assertIn("title,author,category,status", csv_data)
        
        # Check for test book data
        for test_book in self.test_books:
            self.assertIn(test_book["title"], csv_data)
            self.assertIn(test_book["author"], csv_data)
            self.assertIn(test_book["category"], csv_data)
        
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