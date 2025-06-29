import requests
import sys
import time
import uuid
import json
from datetime import datetime

class BookTimeDuplicationTest:
    def __init__(self, base_url="https://aab14546-30e1-4f64-bbab-d554cb50c977.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user = None
        self.tests_run = 0
        self.tests_passed = 0
        self.added_books = []

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error details: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"Response text: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_register(self, first_name, last_name):
        """Test user registration"""
        success, response = self.run_test(
            "User Registration",
            "POST",
            "/api/auth/register",
            200,
            data={"first_name": first_name, "last_name": last_name}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user = response['user']
            return True
        return False

    def test_login(self, first_name, last_name):
        """Test user login"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "/api/auth/login",
            200,
            data={"first_name": first_name, "last_name": last_name}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user = response['user']
            return True
        return False

    def test_search_open_library(self, query):
        """Test searching books on Open Library"""
        success, response = self.run_test(
            "Search Open Library",
            "GET",
            f"/api/openlibrary/search",
            200,
            params={"q": query, "limit": 5}
        )
        if success and 'books' in response:
            print(f"Found {len(response['books'])} books for query '{query}'")
            return response['books']
        return []

    def test_import_from_open_library(self, ol_key, category="roman"):
        """Test importing a book from Open Library"""
        success, response = self.run_test(
            "Import from Open Library",
            "POST",
            "/api/openlibrary/import",
            200,
            data={"ol_key": ol_key, "category": category}
        )
        if success and 'book' in response:
            self.added_books.append(response['book']['id'])
            print(f"Successfully imported book: {response['book']['title']}")
            return response['book']
        return None

    def test_import_duplicate(self, ol_key, category="roman"):
        """Test importing the same book again (should fail with 409)"""
        success, response = self.run_test(
            "Import Duplicate Book",
            "POST",
            "/api/openlibrary/import",
            409,
            data={"ol_key": ol_key, "category": category}
        )
        # This test is successful if it fails with 409 Conflict
        return not success

    def test_get_books(self):
        """Test getting all books"""
        success, response = self.run_test(
            "Get All Books",
            "GET",
            "/api/books",
            200
        )
        if success:
            print(f"Retrieved {len(response)} books")
            return response
        return []

    def test_duplication_bug(self):
        """Test the duplication bug fix by trying to add the same book multiple times in quick succession"""
        # Search for a book
        search_query = "Harry Potter"
        books = self.test_search_open_library(search_query)
        
        if not books:
            print("❌ No books found for search, cannot test duplication bug")
            return False
        
        # Get the first book
        book_to_import = books[0]
        print(f"Testing duplication bug with book: {book_to_import['title']}")
        
        # Try to import the same book multiple times in quick succession
        ol_key = book_to_import['ol_key']
        category = book_to_import['category']
        
        # First import should succeed
        first_import = self.test_import_from_open_library(ol_key, category)
        if not first_import:
            print("❌ First import failed, cannot test duplication bug")
            return False
        
        # Get initial book count
        initial_books = self.test_get_books()
        initial_count = len(initial_books)
        
        # Try to import the same book 3 more times in quick succession
        print("\n🔄 Testing rapid multiple imports of the same book...")
        for i in range(3):
            print(f"Attempt {i+1} to import the same book...")
            success, response = self.run_test(
                f"Duplicate Import Attempt {i+1}",
                "POST",
                "/api/openlibrary/import",
                409,  # Expect conflict status
                data={"ol_key": ol_key, "category": category}
            )
            # We expect these to fail with 409 Conflict
            if success:
                print("❌ Duplicate import succeeded when it should have failed")
                return False
        
        # Get final book count
        final_books = self.test_get_books()
        final_count = len(final_books)
        
        # Check if the book count increased by exactly 1
        if final_count == initial_count + 1:
            print("✅ Book count increased by exactly 1, no duplication occurred")
            return True
        else:
            print(f"❌ Book count increased by {final_count - initial_count}, expected 1")
            return False

    def cleanup(self):
        """Clean up by deleting all added books"""
        print("\n🧹 Cleaning up test data...")
        for book_id in self.added_books[:]:
            success, _ = self.run_test(
                f"Delete Book {book_id}",
                "DELETE",
                f"/api/books/{book_id}",
                200
            )
            if success:
                self.added_books.remove(book_id)

def main():
    # Setup
    tester = BookTimeDuplicationTest()
    first_name = "Test"
    last_name = "User"

    # Run tests
    print(f"🚀 Starting BookTime Duplication Bug Test at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 API URL: {tester.base_url}")

    # Test authentication
    if not tester.test_register(first_name, last_name):
        print("❌ Registration failed, trying login...")
        if not tester.test_login(first_name, last_name):
            print("❌ Login failed, stopping tests")
            return 1
    
    # Test the duplication bug fix
    duplication_test_passed = tester.test_duplication_bug()
    
    # Clean up
    tester.cleanup()
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    print(f"🐛 Duplication bug test: {'PASSED' if duplication_test_passed else 'FAILED'}")
    
    return 0 if duplication_test_passed else 1

if __name__ == "__main__":
    sys.exit(main())