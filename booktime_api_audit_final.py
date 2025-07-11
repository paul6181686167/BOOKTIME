import requests
import json
import time
from datetime import datetime

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://52d4c65f-3964-4e03-b64d-fbb28998c357.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

def run_audit():
    """Run a comprehensive audit of the BookTime API"""
    timestamp = int(time.time())
    results = {
        "health_check": False,
        "user_registration": False,
        "user_login": False,
        "get_current_user": False,
        "create_book": False,
        "get_books": False,
        "get_stats": False,
        "open_library_search": False
    }
    
    # Test 1: Health Check
    print("\n1. Testing Health Check endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ok" and data.get("database") == "connected":
                results["health_check"] = True
                print("✅ Health check endpoint is working correctly")
            else:
                print(f"❌ Health check endpoint returned unexpected data: {data}")
        else:
            print(f"❌ Health check endpoint returned status code {response.status_code}")
    except Exception as e:
        print(f"❌ Error testing health check endpoint: {e}")
    
    # Create a unique test user
    test_user = {
        "first_name": "Audit",
        "last_name": f"User{timestamp}"
    }
    
    # Test 2: User Registration
    print("\n2. Testing User Registration...")
    access_token = None
    headers = {}
    user_id = None
    
    try:
        response = requests.post(f"{API_URL}/auth/register", json=test_user)
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data and "user" in data:
                access_token = data["access_token"]
                headers = {"Authorization": f"Bearer {access_token}"}
                user_id = data["user"]["id"]
                results["user_registration"] = True
                print(f"✅ User registration is working correctly. Created user: {test_user['first_name']} {test_user['last_name']}")
            else:
                print(f"❌ User registration endpoint returned unexpected data: {data}")
        else:
            print(f"❌ User registration endpoint returned status code {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Error testing user registration endpoint: {e}")
    
    # Test 3: User Login
    print("\n3. Testing User Login...")
    if results["user_registration"]:  # Only test login if registration worked
        try:
            response = requests.post(f"{API_URL}/auth/login", json=test_user)
            if response.status_code == 200:
                data = response.json()
                if "access_token" in data and "user" in data:
                    # Update token
                    access_token = data["access_token"]
                    headers = {"Authorization": f"Bearer {access_token}"}
                    results["user_login"] = True
                    print(f"✅ User login is working correctly for user: {test_user['first_name']} {test_user['last_name']}")
                else:
                    print(f"❌ User login endpoint returned unexpected data: {data}")
            else:
                print(f"❌ User login endpoint returned status code {response.status_code}: {response.text}")
        except Exception as e:
            print(f"❌ Error testing user login endpoint: {e}")
    else:
        print("⚠️ Skipping user login test because registration failed")
    
    # Test 4: Get Current User
    print("\n4. Testing Get Current User...")
    if access_token:  # Only test if we have a token
        try:
            response = requests.get(f"{API_URL}/auth/me", headers=headers)
            if response.status_code == 200:
                user = response.json()
                if user.get("first_name") == test_user["first_name"] and user.get("last_name") == test_user["last_name"]:
                    results["get_current_user"] = True
                    print(f"✅ Get current user endpoint is working correctly")
                else:
                    print(f"❌ Get current user endpoint returned unexpected data: {user}")
            else:
                print(f"❌ Get current user endpoint returned status code {response.status_code}: {response.text}")
        except Exception as e:
            print(f"❌ Error testing get current user endpoint: {e}")
    else:
        print("⚠️ Skipping get current user test because no token is available")
    
    # Test 5: Create Book
    print("\n5. Testing Create Book...")
    book_id = None
    test_book_data = {
        "title": f"Test Book {timestamp}",
        "author": "Test Author",
        "category": "roman",
        "description": "A test book for audit purposes"
    }
    
    if access_token:  # Only test if we have a token
        try:
            response = requests.post(
                f"{API_URL}/books", 
                json=test_book_data,
                headers=headers
            )
            if response.status_code == 200:
                book = response.json()
                if (book.get("title") == test_book_data["title"] and 
                    book.get("author") == test_book_data["author"] and
                    book.get("category") == test_book_data["category"]):
                    book_id = book.get("id")
                    results["create_book"] = True
                    print(f"✅ Create book endpoint is working correctly")
                else:
                    print(f"❌ Create book endpoint returned unexpected data: {book}")
            else:
                print(f"❌ Create book endpoint returned status code {response.status_code}: {response.text}")
        except Exception as e:
            print(f"❌ Error testing create book endpoint: {e}")
    else:
        print("⚠️ Skipping create book test because no token is available")
    
    # Test 6: Get Books
    print("\n6. Testing Get Books...")
    if access_token:  # Only test if we have a token
        try:
            response = requests.get(f"{API_URL}/books", headers=headers)
            if response.status_code == 200:
                books = response.json()
                if isinstance(books, list):
                    # If we created a book, check if it's in the list
                    if book_id:
                        book_found = any(b.get("id") == book_id for b in books)
                        if book_found:
                            results["get_books"] = True
                            print(f"✅ Get books endpoint is working correctly. Found {len(books)} books including our test book.")
                        else:
                            print(f"❌ Get books endpoint did not return our test book. Found {len(books)} books.")
                    else:
                        # If we didn't create a book, just check if the endpoint returns a list
                        results["get_books"] = True
                        print(f"✅ Get books endpoint is working correctly. Found {len(books)} books.")
                else:
                    print(f"❌ Get books endpoint returned unexpected data type: {type(books)}")
            else:
                print(f"❌ Get books endpoint returned status code {response.status_code}: {response.text}")
        except Exception as e:
            print(f"❌ Error testing get books endpoint: {e}")
    else:
        print("⚠️ Skipping get books test because no token is available")
    
    # Test 7: Get Stats
    print("\n7. Testing Get Stats...")
    if access_token:  # Only test if we have a token
        try:
            response = requests.get(f"{API_URL}/stats", headers=headers)
            if response.status_code == 200:
                stats = response.json()
                required_fields = [
                    "total_books", "completed_books", "reading_books", 
                    "to_read_books", "categories", "authors_count", 
                    "sagas_count", "auto_added_count"
                ]
                if all(field in stats for field in required_fields):
                    results["get_stats"] = True
                    print(f"✅ Get stats endpoint is working correctly")
                    print(f"   Total books: {stats['total_books']}")
                    print(f"   Reading: {stats['reading_books']}, To Read: {stats['to_read_books']}, Completed: {stats['completed_books']}")
                else:
                    print(f"❌ Get stats endpoint is missing required fields. Got: {list(stats.keys())}")
            else:
                print(f"❌ Get stats endpoint returned status code {response.status_code}: {response.text}")
        except Exception as e:
            print(f"❌ Error testing get stats endpoint: {e}")
    else:
        print("⚠️ Skipping get stats test because no token is available")
    
    # Test 8: Open Library Search
    print("\n8. Testing Open Library Search...")
    if access_token:  # Only test if we have a token
        try:
            response = requests.get(
                f"{API_URL}/openlibrary/search?q=harry potter",
                headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                if "books" in data and "total_found" in data:
                    if data["total_found"] > 0 and len(data["books"]) > 0:
                        # Check if at least one book has "Harry Potter" in the title
                        harry_potter_book = next((b for b in data["books"] if "Harry Potter" in b.get("title", "")), None)
                        if harry_potter_book:
                            results["open_library_search"] = True
                            print(f"✅ Open Library search endpoint is working correctly. Found {data['total_found']} books for 'Harry Potter'")
                        else:
                            print(f"❌ Open Library search did not find any 'Harry Potter' books in the results")
                    else:
                        print(f"❌ Open Library search returned no results for 'Harry Potter'")
                else:
                    print(f"❌ Open Library search endpoint returned unexpected data: {data}")
            else:
                print(f"❌ Open Library search endpoint returned status code {response.status_code}: {response.text}")
        except Exception as e:
            print(f"❌ Error testing Open Library search endpoint: {e}")
    else:
        print("⚠️ Skipping Open Library search test because no token is available")
    
    # Clean up - delete the test book if it was created
    if book_id and access_token:
        try:
            requests.delete(f"{API_URL}/books/{book_id}", headers=headers)
            print(f"\nCleanup: Deleted test book with ID {book_id}")
        except:
            pass
    
    # Print summary
    print("\n=== AUDIT TEST SUMMARY ===")
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    print(f"Tests run: {total_tests}")
    print(f"Tests passed: {passed_tests}")
    print(f"Tests failed: {total_tests - passed_tests}")
    
    if passed_tests == total_tests:
        print("\n✅ All audit tests passed successfully!")
    else:
        print("\n⚠️ Some audit tests failed:")
    
    print("\nCRITICAL API ENDPOINTS STATUS:")
    print(f"{'✅' if results['health_check'] else '❌'} GET /health - Health check")
    print(f"{'✅' if results['user_registration'] else '❌'} POST /api/auth/register - User registration")
    print(f"{'✅' if results['user_login'] else '❌'} POST /api/auth/login - User login")
    print(f"{'✅' if results['get_current_user'] else '❌'} GET /api/auth/me - Get current user")
    print(f"{'✅' if results['create_book'] else '❌'} POST /api/books - Create book")
    print(f"{'✅' if results['get_books'] else '❌'} GET /api/books - Get all books")
    print(f"{'✅' if results['get_stats'] else '❌'} GET /api/stats - Get user statistics")
    print(f"{'✅' if results['open_library_search'] else '❌'} GET /api/openlibrary/search - Open Library search")

if __name__ == "__main__":
    run_audit()