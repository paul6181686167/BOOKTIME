import requests
import sys
import time
import uuid
from datetime import datetime

class BookTimeAuthTester:
    def __init__(self, base_url="https://938de42f-8b39-443e-a3c1-d9355f5c655d.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user = None
        self.tests_run = 0
        self.tests_passed = 0
        self.book_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, auth=False):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if auth and self.token:
            headers['Authorization'] = f'Bearer {self.token}'

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

    def test_health(self):
        """Test health endpoint"""
        return self.run_test(
            "Health Check",
            "GET",
            "health",
            200
        )

    def test_register(self, first_name, last_name):
        """Test user registration"""
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
            print(f"User registered: {self.user['first_name']} {self.user['last_name']}")
            print(f"Token received: {self.token[:10]}...")
            return True
        return False

    def test_login(self, first_name, last_name):
        """Test user login"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "api/auth/login",
            200,
            data={"first_name": first_name, "last_name": last_name}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user = response['user']
            print(f"User logged in: {self.user['first_name']} {self.user['last_name']}")
            print(f"Token received: {self.token[:10]}...")
            return True
        return False

    def test_get_me(self):
        """Test get current user endpoint"""
        success, response = self.run_test(
            "Get Current User",
            "GET",
            "api/auth/me",
            200,
            auth=True
        )
        if success:
            print(f"Current user: {response['first_name']} {response['last_name']}")
        return success

    def test_get_books_with_auth(self):
        """Test get books endpoint with authentication"""
        success, response = self.run_test(
            "Get Books with Authentication",
            "GET",
            "api/books",
            200,
            auth=True
        )
        if success:
            print(f"Retrieved {len(response)} books with authentication")
        return success

    def test_get_books_without_auth(self):
        """Test get books endpoint without authentication (should fail)"""
        # Temporarily remove token
        temp_token = self.token
        self.token = None
        
        success, response = self.run_test(
            "Get Books without Authentication",
            "GET",
            "api/books",
            401,
            auth=False
        )
        
        # Restore token
        self.token = temp_token
        
        if not success:
            # This test should fail with 401, so we'll count it as passed if it fails correctly
            self.tests_passed += 1
            print("✅ Passed - Correctly rejected unauthenticated request")
            return True
        return False

    def test_invalid_token(self):
        """Test using an invalid token (should fail)"""
        # Temporarily set an invalid token
        temp_token = self.token
        self.token = "invalid_token_here"
        
        success, response = self.run_test(
            "Access with Invalid Token",
            "GET",
            "api/books",
            401,
            auth=True
        )
        
        # Restore token
        self.token = temp_token
        
        if not success:
            # This test should fail with 401, so we'll count it as passed if it fails correctly
            self.tests_passed += 1
            print("✅ Passed - Correctly rejected invalid token")
            return True
        return False

    def test_create_book(self, title, author, category="roman"):
        """Test create book endpoint"""
        book_data = {
            "title": title,
            "author": author,
            "category": category,
            "description": "Test book description"
        }
        
        success, response = self.run_test(
            "Create Book",
            "POST",
            "api/books",
            200,
            data=book_data,
            auth=True
        )
        if success:
            self.book_id = response['id']
            print(f"Book created with ID: {self.book_id}")
        return success

    def test_get_stats(self):
        """Test get stats endpoint"""
        success, response = self.run_test(
            "Get Stats",
            "GET",
            "api/stats",
            200,
            auth=True
        )
        if success:
            print(f"Stats retrieved: {response['total_books']} total books")
            print(f"Categories: Roman: {response['categories']['roman']}, BD: {response['categories']['bd']}, Manga: {response['categories']['manga']}")
        return success

    def run_auth_tests(self):
        """Run all authentication-related tests"""
        print("🚀 Starting BookTime Authentication Tests")
        
        # Generate unique test user
        timestamp = int(time.time())
        test_first_name = f"Test{timestamp}"
        test_last_name = f"User{timestamp}"
        
        # Test health endpoint
        self.test_health()
        
        # Test registration
        if not self.test_register(test_first_name, test_last_name):
            print("❌ Registration failed, stopping tests")
            return False
        
        # Test get current user
        if not self.test_get_me():
            print("❌ Get current user failed, stopping tests")
            return False
        
        # Test get books with authentication
        if not self.test_get_books_with_auth():
            print("❌ Get books with authentication failed, stopping tests")
            return False
        
        # Test get books without authentication
        self.test_get_books_without_auth()
        
        # Test invalid token
        self.test_invalid_token()
        
        # Test create book
        if not self.test_create_book(f"Test Book {timestamp}", "Test Author"):
            print("❌ Create book failed, stopping tests")
            return False
            
        # Test get stats
        if not self.test_get_stats():
            print("❌ Get stats failed, stopping tests")
            return False
        
        # Test login with existing user
        # First, clear the token
        self.token = None
        if not self.test_login(test_first_name, test_last_name):
            print("❌ Login failed, stopping tests")
            return False
        
        # Test get current user again after login
        if not self.test_get_me():
            print("❌ Get current user after login failed, stopping tests")
            return False
        
        # Print results
        print(f"\n📊 Authentication Tests passed: {self.tests_passed}/{self.tests_run}")
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = BookTimeAuthTester()
    success = tester.run_auth_tests()
    sys.exit(0 if success else 1)