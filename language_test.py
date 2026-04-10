import requests
import sys
import json
from datetime import datetime

class BooktimeLanguageAPITester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
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
                return success, response.json() if response.content else {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_get_books(self):
        """Test getting all books"""
        return self.run_test(
            "Get All Books",
            "GET",
            "api/books",
            200
        )

    def test_create_book_with_languages(self, book_data):
        """Test creating a book with language information"""
        return self.run_test(
            "Create Book with Language Information",
            "POST",
            "api/books",
            200,
            data=book_data
        )

    def test_update_book_languages(self, book_id, update_data):
        """Test updating a book's language information"""
        return self.run_test(
            "Update Book Language Information",
            "PUT",
            f"api/books/{book_id}",
            200,
            data=update_data
        )

def main():
    # Get backend URL from environment or use default
    backend_url = "http://localhost:8001"
    
    # Setup tester
    tester = BooktimeLanguageAPITester(backend_url)
    
    # Test 1: Get all books to check language fields
    success, books = tester.test_get_books()
    if not success:
        print("❌ Failed to get books, stopping tests")
        return 1
    
    print(f"📚 Found {len(books)} books in the database")
    
    # Check if we have the test books with language information
    test_books = [book for book in books if book['title'] in ["Le Seigneur des Anneaux", "One Piece - Tome 1"]]
    if len(test_books) == 2:
        print("✅ Found both test books in the database")
        
        # Print language information for test books
        for book in test_books:
            print(f"\n📖 Book: {book['title']}")
            print(f"   Original language: {book['original_language']}")
            print(f"   Reading language: {book['reading_language']}")
            print(f"   Available translations: {', '.join(book['available_translations']) if book['available_translations'] else 'None'}")
    else:
        print("⚠️ Did not find both test books in the database")
    
    # Test 2: Create a new book with language information
    new_book = {
        "title": "Test Book with Languages",
        "author": "Test Author",
        "category": "roman",
        "description": "A test book with language information",
        "original_language": "anglais",
        "reading_language": "français",
        "available_translations": ["français", "espagnol", "allemand"]
    }
    
    success, created_book = tester.test_create_book_with_languages(new_book)
    if success:
        print(f"✅ Created new book with ID: {created_book['_id']}")
        book_id = created_book['_id']
        
        # Verify language fields
        print(f"   Original language: {created_book['original_language']}")
        print(f"   Reading language: {created_book['reading_language']}")
        print(f"   Available translations: {', '.join(created_book['available_translations'])}")
        
        # Test 3: Update the book's language information
        update_data = {
            "reading_language": "espagnol",
            "available_translations": ["français", "espagnol", "allemand", "italien"]
        }
        
        success, updated_book = tester.test_update_book_languages(book_id, update_data)
        if success:
            print("✅ Updated book language information")
            print(f"   New reading language: {updated_book['reading_language']}")
            print(f"   Updated translations: {', '.join(updated_book['available_translations'])}")
        else:
            print("❌ Failed to update book language information")
        
        # Clean up - delete the test book
        try:
            requests.delete(f"{backend_url}/api/books/{book_id}")
            print(f"✅ Cleaned up test book with ID: {book_id}")
        except Exception as e:
            print(f"⚠️ Failed to clean up test book: {str(e)}")
    
    # Print results
    print(f"\n📋 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())