import requests
import unittest
import uuid

# Get the backend URL from the frontend .env file
BACKEND_URL = "http://localhost:8001"
API_URL = f"{BACKEND_URL}/api"

class CategoryValidationTest(unittest.TestCase):
    """Test suite for the category validation in the Booktime API"""

    def setUp(self):
        """Setup for each test"""
        self.test_book_base = {
            "title": "Test Book",
            "author": "Test Author",
            "description": "A test book for category validation",
            "total_pages": 100
        }
        
        # Book IDs to be cleaned up during tearDown
        self.book_ids_to_delete = []

    def tearDown(self):
        """Clean up after each test"""
        # Delete any books created during testing
        for book_id in self.book_ids_to_delete:
            try:
                requests.delete(f"{API_URL}/books/{book_id}")
            except:
                pass

    def test_valid_categories(self):
        """Test creating books with valid categories (roman, bd, manga)"""
        valid_categories = ["roman", "bd", "manga"]
        
        for category in valid_categories:
            test_book = self.test_book_base.copy()
            test_book["category"] = category
            
            response = requests.post(f"{API_URL}/books", json=test_book)
            self.assertEqual(response.status_code, 200, f"Failed to create book with valid category '{category}'")
            
            book = response.json()
            self.book_ids_to_delete.append(book["_id"])
            
            self.assertEqual(book["category"], category)
            print(f"✅ Successfully created book with valid category '{category}'")

    def test_invalid_categories(self):
        """Test creating books with invalid categories (should be rejected)"""
        invalid_categories = ["test", "other", "science-fiction", "fantasy", "biography"]
        
        for category in invalid_categories:
            test_book = self.test_book_base.copy()
            test_book["category"] = category
            
            response = requests.post(f"{API_URL}/books", json=test_book)
            
            # Should fail with a 422 Unprocessable Entity or similar error
            self.assertNotEqual(response.status_code, 200, 
                              f"Book with invalid category '{category}' was created, but should have been rejected")
            
            print(f"✅ Correctly rejected book with invalid category '{category}'")
            
            # Verify the error message mentions category validation
            error_data = response.json()
            error_detail = error_data.get("detail", "")
            
            # Handle both string and list error details
            if isinstance(error_detail, list):
                error_text = str(error_detail).lower()
            else:
                error_text = str(error_detail).lower()
                
            self.assertIn("category", error_text, 
                         f"Error message should mention category validation issue: {error_detail}")

    def test_category_case_conversion(self):
        """Test that categories are converted to lowercase"""
        test_cases = [
            ("Roman", "roman"),
            ("BD", "bd"),
            ("Manga", "manga"),
            ("ROMAN", "roman"),
            ("Bd", "bd"),
            ("MaNgA", "manga")
        ]
        
        for input_category, expected_category in test_cases:
            test_book = self.test_book_base.copy()
            test_book["category"] = input_category
            
            response = requests.post(f"{API_URL}/books", json=test_book)
            self.assertEqual(response.status_code, 200, 
                           f"Failed to create book with category '{input_category}'")
            
            book = response.json()
            self.book_ids_to_delete.append(book["_id"])
            
            self.assertEqual(book["category"], expected_category, 
                           f"Category '{input_category}' should be converted to '{expected_category}'")
            
            print(f"✅ Category '{input_category}' correctly converted to '{expected_category}'")

if __name__ == "__main__":
    unittest.main(verbosity=2)