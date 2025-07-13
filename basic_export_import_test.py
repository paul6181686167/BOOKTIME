import requests
import json
import unittest
import uuid
import os
import time
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://0fe5fd4d-bbeb-4285-963f-9f5e9f67241d.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class BasicExportImportTest(unittest.TestCase):
    """Basic test suite for the Export/Import API functionality"""

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
        
        # Headers for authenticated requests
        self.auth_headers = {
            "Authorization": f"Bearer {self.token}"
        }

    def test_export_formats(self):
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
        
        print("✅ GET /api/export-import/export/formats endpoint working correctly")

    def test_import_formats(self):
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
        
        print("✅ GET /api/export-import/import/formats endpoint working correctly")

    def test_template_generation(self):
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
        
        # Check file info
        file_info = data["file_info"]
        self.assertEqual(file_info["detected_format"], "csv")
        
        print("✅ POST /api/export-import/import/preview endpoint working correctly")

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