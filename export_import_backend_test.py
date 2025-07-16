import requests
import json
import unittest
import uuid
import os
import time
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://b16e2314-ae06-4775-b2d0-fc50a903187d.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class ExportImportBackendTest(unittest.TestCase):
    """Comprehensive test suite for the Export/Import API functionality"""

    def setUp(self):
        """Setup for each test"""
        # Create a test user
        self.test_user = {
            "first_name": f"Test{uuid.uuid4().hex[:6]}",
            "last_name": "BackendTest"
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
        self.test_book = {
            "title": f"Test Book {uuid.uuid4().hex[:6]}",
            "author": "Test Author",
            "category": "roman",
            "status": "to_read",
            "total_pages": 200
        }
        
        # Add a test book
        response = requests.post(f"{API_URL}/books", json=self.test_book, headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        self.book_data = response.json()
        self.book_id = self.book_data["id"]

    def tearDown(self):
        """Clean up after each test"""
        # Delete the test book
        if hasattr(self, 'book_id'):
            requests.delete(f"{API_URL}/books/{self.book_id}", headers=self.auth_headers)

    def test_export_import_functionality(self):
        """Test the complete export/import functionality"""
        # 1. Test export formats endpoint
        response = requests.get(f"{API_URL}/export-import/export/formats", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("supported_formats", data)
        self.assertIn("formats_details", data)
        print("✅ GET /api/export-import/export/formats endpoint working")
        
        # 2. Test import formats endpoint
        response = requests.get(f"{API_URL}/export-import/import/formats", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("supported_formats", data)
        self.assertIn("tips", data)
        print("✅ GET /api/export-import/import/formats endpoint working")
        
        # 3. Test export in JSON format
        response = requests.get(
            f"{API_URL}/export-import/export?format_type=json",
            headers=self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["Content-Type"].startswith("application/json"))
        export_data = response.json()
        self.assertIn("books", export_data)
        print("✅ GET /api/export-import/export?format_type=json endpoint working")
        
        # 4. Test export in CSV format
        response = requests.get(
            f"{API_URL}/export-import/export?format_type=csv",
            headers=self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["Content-Type"].startswith("text/csv"))
        print("✅ GET /api/export-import/export?format_type=csv endpoint working")
        
        # 5. Test export in Excel format
        response = requests.get(
            f"{API_URL}/export-import/export?format_type=excel",
            headers=self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], 
                         "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        print("✅ GET /api/export-import/export?format_type=excel endpoint working")
        
        # 6. Test export in full backup format
        response = requests.get(
            f"{API_URL}/export-import/export?format_type=full_backup",
            headers=self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/zip")
        print("✅ GET /api/export-import/export?format_type=full_backup endpoint working")
        
        # 7. Test template generation
        response = requests.post(
            f"{API_URL}/export-import/templates/generate?format_type=csv",
            headers=self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["Content-Type"].startswith("text/csv"))
        print("✅ POST /api/export-import/templates/generate endpoint working")
        
        # 8. Test import preview
        csv_content = """title,author,category,status,rating,review,current_page,total_pages
Test Import Book 1,Test Author,roman,to_read,0,,0,200
Test Import Book 2,Test Author,bd,reading,0,,50,100
Test Import Book 3,Test Author,manga,completed,4,Great book!,300,300"""
        
        files = {
            "file": ("import.csv", csv_content.encode('utf-8'), "text/csv")
        }
        
        response = requests.post(
            f"{API_URL}/export-import/import/preview",
            headers=self.auth_headers,
            files=files
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("success", data)
        self.assertIn("preview", data)
        print("✅ POST /api/export-import/import/preview endpoint working")
        
        # 9. Test actual import
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
        data = response.json()
        self.assertIn("success", data)
        self.assertIn("summary", data)
        print("✅ POST /api/export-import/import endpoint working")
        
        # 10. Test export history
        response = requests.get(
            f"{API_URL}/export-import/user/export-history",
            headers=self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("success", data)
        self.assertIn("exports", data)
        print("✅ GET /api/export-import/user/export-history endpoint working")
        
        # 11. Test error handling
        response = requests.get(
            f"{API_URL}/export-import/export?format_type=invalid",
            headers=self.auth_headers
        )
        self.assertGreaterEqual(response.status_code, 400)
        print("✅ Error handling for invalid inputs works correctly")


if __name__ == "__main__":
    unittest.main(verbosity=2)