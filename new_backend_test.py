import requests
import sys
import time
import uuid
import json
from datetime import datetime

class BookTimeAPITester:
    def __init__(self, base_url="https://66108431-6c31-4487-92e5-9a510df007c4.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_books = []

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
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
                    print(f"Error details: {error_data}")
                except:
                    print(f"Response text: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_register(self):
        """Test user registration"""
        # Generate unique user name to avoid conflicts
        first_name = f"Test{uuid.uuid4().hex[:6]}"
        last_name = f"User{uuid.uuid4().hex[:6]}"
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "api/auth/register",
            200,
            data={"first_name": first_name, "last_name": last_name}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user = response['user']
            print(f"Created user: {first_name} {last_name}")
            return True
        return False

    def test_login(self):
        """Test user login with the registered user"""
        if not self.user:
            print("❌ Cannot test login - no registered user")
            return False
            
        success, response = self.run_test(
            "User Login",
            "POST",
            "api/auth/login",
            200,
            data={"first_name": self.user['first_name'], "last_name": self.user['last_name']}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            return True
        return False

    def test_get_me(self):
        """Test getting current user profile"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "api/auth/me",
            200
        )
        return success

    def test_create_book(self, book_data=None):
        """Test creating a book"""
        if book_data is None:
            book_data = {
                "title": f"Test Book {uuid.uuid4().hex[:6]}",
                "author": "Test Author",
                "category": "roman",
                "description": "This is a test book description",
                "saga": "Test Saga",
                "status": "to_read"
            }
            
        success, response = self.run_test(
            f"Create Book: {book_data['title']}",
            "POST",
            "api/books",
            200,
            data=book_data
        )
        
        if success and 'id' in response:
            self.created_books.append(response)
            return True, response
        return False, None

    def test_get_books(self):
        """Test getting all books"""
        success, response = self.run_test(
            "Get All Books",
            "GET",
            "api/books",
            200
        )
        
        if success:
            print(f"Retrieved {len(response)} books")
        return success

    def test_get_book_details(self, book_id):
        """Test getting book details"""
        success, response = self.run_test(
            f"Get Book Details (ID: {book_id})",
            "GET",
            f"api/books/{book_id}",
            200
        )
        
        if success:
            print(f"Book title: {response.get('title')}")
            if 'enriched_data' in response and response['enriched_data']:
                print(f"Book has enriched data from OpenLibrary")
        return success

    def test_update_book(self, book_id):
        """Test updating a book"""
        update_data = {
            "status": "reading",
            "rating": 4,
            "review": "This is an updated review for testing purposes."
        }
        
        success, response = self.run_test(
            f"Update Book (ID: {book_id})",
            "PUT",
            f"api/books/{book_id}",
            200,
            data=update_data
        )
        
        if success:
            print(f"Updated book status to: {response.get('status')}")
        return success

    def test_delete_book(self, book_id):
        """Test deleting a book"""
        success, _ = self.run_test(
            f"Delete Book (ID: {book_id})",
            "DELETE",
            f"api/books/{book_id}",
            200
        )
        return success

    def test_get_stats(self):
        """Test getting user statistics"""
        success, response = self.run_test(
            "Get User Statistics",
            "GET",
            "api/stats",
            200
        )
        
        if success:
            print(f"Total books: {response.get('total_books')}")
            print(f"Categories: {response.get('categories')}")
        return success

    def test_search_openlibrary(self, query="Harry Potter"):
        """Test searching OpenLibrary"""
        success, response = self.run_test(
            f"Search OpenLibrary for '{query}'",
            "GET",
            "api/openlibrary/search",
            200,
            params={"q": query}
        )
        
        if success:
            print(f"Found {len(response.get('books', []))} books in OpenLibrary")
        return success

    def test_search_openlibrary_universal(self, query="Harry Potter"):
        """Test universal search in OpenLibrary"""
        success, response = self.run_test(
            f"Universal Search in OpenLibrary for '{query}'",
            "GET",
            "api/openlibrary/search-universal",
            200,
            params={"q": query}
        )
        
        if success:
            print(f"Found {len(response.get('books', []))} books in universal search")
            if response.get('books'):
                # Check if the first book has category detection
                first_book = response['books'][0]
                print(f"First book: {first_book.get('title')} - Category: {first_book.get('category')}")
        return success

    def test_get_author_details(self, author_name="J.K. Rowling"):
        """Test getting author details"""
        success, response = self.run_test(
            f"Get Author Details for '{author_name}'",
            "GET",
            f"api/authors/{author_name}",
            200
        )
        
        if success:
            print(f"Author biography length: {len(response.get('biography', ''))}")
            print(f"Bibliography items: {len(response.get('bibliography', []))}")
        return success

    def test_get_author_books(self, author_name="J.K. Rowling"):
        """Test getting author books"""
        success, response = self.run_test(
            f"Get Author Books for '{author_name}'",
            "GET",
            f"api/authors/{author_name}/books",
            200
        )
        
        if success:
            print(f"Total books by author: {len(response)}")
            print(f"Books in user library: {len([b for b in response if b.get('user_owned', False)])}")
        return success

    def test_get_openlibrary_book(self, work_key="OL82586W"):
        """Test getting OpenLibrary book details"""
        success, response = self.run_test(
            f"Get OpenLibrary Book Details for work_key '{work_key}'",
            "GET",
            f"api/openlibrary/book/{work_key}",
            200
        )
        
        if success:
            print(f"Book title: {response.get('title')}")
            print(f"Author: {response.get('author')}")
            if response.get('subjects'):
                print(f"Subjects: {len(response.get('subjects'))} items")
        return success

    def run_all_tests(self):
        """Run all API tests in sequence"""
        print("🚀 Starting BookTime API Tests")
        
        # Authentication tests
        if not self.test_register():
            print("❌ Registration failed, stopping tests")
            return False
            
        self.test_login()
        self.test_get_me()
        
        # Book management tests
        success, book = self.test_create_book()
        if success and book:
            book_id = book['id']
            self.test_get_books()
            self.test_get_book_details(book_id)
            self.test_update_book(book_id)
            
            # Create a few more books for testing
            for i in range(2):
                self.test_create_book({
                    "title": f"Test Book {i+1}",
                    "author": "Test Author",
                    "category": ["roman", "bd", "manga"][i % 3],
                    "status": ["to_read", "reading", "completed"][i % 3]
                })
            
            self.test_get_stats()
            
            # Delete the first book
            self.test_delete_book(book_id)
        
        # OpenLibrary integration tests
        self.test_search_openlibrary()
        self.test_search_openlibrary_universal()
        self.test_get_author_details()
        self.test_get_author_books()
        self.test_get_openlibrary_book()
        
        # Print results
        print(f"\n📊 Tests passed: {self.tests_passed}/{self.tests_run} ({self.tests_passed/self.tests_run*100:.1f}%)")
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = BookTimeAPITester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)