import requests
import json
import random
import string
import time
from datetime import datetime

class BooktimeAPITester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.token = None
        self.user_data = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_books = []

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
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
                    return success, response.json() if response.text else {}
                except json.JSONDecodeError:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def generate_random_user(self):
        """Generate random user data for testing"""
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        return {
            "email": f"test_user_{random_suffix}@example.com",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User"
        }

    def register_user(self):
        """Register a new test user"""
        user_data = {
            "first_name": "Test",
            "last_name": f"User{random.randint(1000, 9999)}"
        }
        success, response = self.run_test(
            "Register User",
            "POST",
            "auth/register",
            200,
            data=user_data
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_data = user_data
            print(f"Created test user: {user_data['first_name']} {user_data['last_name']}")
            return True
        return False

    def login_user(self):
        """Login with existing user credentials"""
        if not self.user_data:
            print("No user data available for login")
            return False
            
        login_data = {
            "first_name": self.user_data["first_name"],
            "last_name": self.user_data["last_name"]
        }
        success, response = self.run_test(
            "Login User",
            "POST",
            "auth/login",
            200,
            data=login_data
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            return True
        return False

    def verify_auth(self):
        """Verify authentication with /auth/me endpoint"""
        success, response = self.run_test(
            "Verify Authentication",
            "GET",
            "auth/me",
            200
        )
        if success and 'id' in response:
            print(f"Authenticated as user: {response['first_name']} {response['last_name']}")
            return True
        return False

    def create_book(self, category="roman"):
        """Create a test book"""
        book_data = {
            "title": f"Test Book {datetime.now().strftime('%H:%M:%S')}",
            "author": "Test Author",
            "category": category,
            "description": "This is a test book created by the API tester",
            "publication_year": 2023
        }
        
        success, response = self.run_test(
            f"Create {category.capitalize()} Book",
            "POST",
            "books",
            200,
            data=book_data
        )
        
        if success and 'id' in response:
            self.created_books.append(response)
            print(f"Created book: {response['title']} (ID: {response['id']})")
            return response
        return None

    def get_books(self, category=None, status=None):
        """Get books with optional filters"""
        params = {}
        if category:
            params['category'] = category
        if status:
            params['status'] = status
            
        success, response = self.run_test(
            f"Get Books (category={category}, status={status})",
            "GET",
            "books",
            200,
            params=params
        )
        
        if success:
            print(f"Retrieved {len(response)} books")
            return response
        return []

    def get_book_by_id(self, book_id):
        """Get a specific book by ID"""
        success, response = self.run_test(
            f"Get Book by ID ({book_id})",
            "GET",
            f"books/{book_id}",
            200
        )
        
        if success and 'id' in response:
            print(f"Retrieved book: {response['title']}")
            return response
        return None

    def update_book(self, book_id, updates):
        """Update a book"""
        success, response = self.run_test(
            f"Update Book ({book_id})",
            "PUT",
            f"books/{book_id}",
            200,
            data=updates
        )
        
        if success and 'id' in response:
            print(f"Updated book: {response['title']} - New status: {response['status']}")
            return response
        return None

    def delete_book(self, book_id):
        """Delete a book"""
        success, response = self.run_test(
            f"Delete Book ({book_id})",
            "DELETE",
            f"books/{book_id}",
            200
        )
        
        if success:
            print(f"Deleted book with ID: {book_id}")
            return True
        return False

    def get_stats(self):
        """Get user statistics"""
        success, response = self.run_test(
            "Get User Stats",
            "GET",
            "stats",
            200
        )
        
        if success:
            print(f"User has {response['total_books']} books in total")
            print(f"Categories: Romans: {response['categories']['roman']}, BD: {response['categories']['bd']}, Manga: {response['categories']['manga']}")
            return response
        return None

    def search_openlibrary(self, query):
        """Test OpenLibrary search integration"""
        success, response = self.run_test(
            f"Search OpenLibrary ({query})",
            "GET",
            f"openlibrary/search?q={query}",
            200
        )
        
        if success:
            print(f"Found OpenLibrary search results for '{query}'")
            return response
        return None

def run_tests():
    # Get the backend URL from the frontend .env file
    backend_url = "https://0b242f2a-081a-491a-bb79-9c027627f29c.preview.emergentagent.com"
    
    print(f"🚀 Starting BOOKTIME API tests against {backend_url}")
    tester = BooktimeAPITester(backend_url)
    
    # Authentication tests
    if not tester.register_user():
        print("❌ User registration failed, stopping tests")
        return False
        
    if not tester.verify_auth():
        print("❌ Authentication verification failed, stopping tests")
        return False
    
    # Book creation tests
    roman_book = tester.create_book(category="roman")
    bd_book = tester.create_book(category="bd")
    manga_book = tester.create_book(category="manga")
    
    if not roman_book or not bd_book or not manga_book:
        print("❌ Book creation failed, stopping tests")
        return False
    
    # Get books tests
    all_books = tester.get_books()
    roman_books = tester.get_books(category="roman")
    to_read_books = tester.get_books(status="to_read")
    
    # Get specific book test
    if roman_book:
        book_details = tester.get_book_by_id(roman_book["id"])
        if not book_details:
            print("❌ Failed to get book details")
    
    # Update book test
    if roman_book:
        updated_book = tester.update_book(roman_book["id"], {
            "status": "reading",
            "current_page": 50
        })
        
        if not updated_book or updated_book["status"] != "reading":
            print("❌ Book update failed")
    
    # Get stats test
    stats = tester.get_stats()
    if not stats:
        print("❌ Failed to get user stats")
    
    # OpenLibrary search test
    search_results = tester.search_openlibrary("Harry Potter")
    if not search_results:
        print("❌ OpenLibrary search failed")
    
    # Delete book test
    if manga_book:
        if not tester.delete_book(manga_book["id"]):
            print("❌ Book deletion failed")
    
    # Final stats
    print("\n📊 Test Results:")
    print(f"Tests passed: {tester.tests_passed}/{tester.tests_run} ({tester.tests_passed/tester.tests_run*100:.1f}%)")
    
    return tester.tests_passed == tester.tests_run

if __name__ == "__main__":
    success = run_tests()
    print("\n✅ All tests passed!" if success else "\n❌ Some tests failed!")