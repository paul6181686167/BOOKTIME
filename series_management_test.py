import requests
import sys
import json
from datetime import datetime

class SeriesManagementTester:
    def __init__(self, base_url="https://8063c975-82b7-4130-880b-48ffa3ce128f.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None

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
                    return success, response.json() if response.text else {}
                except json.JSONDecodeError:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json() if response.text else {}
                    print(f"Error details: {error_data}")
                    return False, error_data
                except json.JSONDecodeError:
                    return False, {"error": "Invalid JSON response"}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {"error": str(e)}

    def register_user(self, first_name, last_name):
        """Register a new user"""
        success, response = self.run_test(
            "Register User",
            "POST",
            "api/auth/register",
            200,
            data={"first_name": first_name, "last_name": last_name}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response.get('user', {}).get('id')
            return True
        return False

    def login_user(self, first_name, last_name):
        """Login with existing user"""
        success, response = self.run_test(
            "Login User",
            "POST",
            "api/auth/login",
            200,
            data={"first_name": first_name, "last_name": last_name}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response.get('user', {}).get('id')
            return True
        return False

    def test_get_library_series(self, category=None):
        """Test getting library series"""
        params = {}
        if category:
            params['category'] = category
        
        success, response = self.run_test(
            f"Get Library Series{' for ' + category if category else ''}",
            "GET",
            "api/library/series",
            200,
            params=params
        )
        return success, response

    def test_get_books(self, category=None, view_mode="series"):
        """Test getting books with view mode"""
        params = {}
        if category:
            params['category'] = category
        if view_mode:
            params['view_mode'] = view_mode
        
        success, response = self.run_test(
            f"Get Books with view_mode={view_mode}{' for ' + category if category else ''}",
            "GET",
            "api/books",
            200,
            params=params
        )
        return success, response

    def test_search_books_grouped(self, query, category=None):
        """Test searching books with grouping"""
        params = {'q': query}
        if category:
            params['category'] = category
        
        success, response = self.run_test(
            f"Search Books Grouped for '{query}'",
            "GET",
            "api/books/search-grouped",
            200,
            params=params
        )
        return success, response

    def test_get_saga_books(self, saga_name):
        """Test getting books for a specific saga"""
        success, response = self.run_test(
            f"Get Books for Saga '{saga_name}'",
            "GET",
            f"api/sagas/{saga_name}/books",
            200
        )
        return success, response

    def test_series_search(self, query, category=None):
        """Test searching for series"""
        params = {'q': query}
        if category:
            params['category'] = category
        
        success, response = self.run_test(
            f"Search Series for '{query}'",
            "GET",
            "api/series/search",
            200,
            params=params
        )
        return success, response

    def test_popular_series(self, category=None):
        """Test getting popular series"""
        params = {}
        if category:
            params['category'] = category
        
        success, response = self.run_test(
            f"Get Popular Series{' for ' + category if category else ''}",
            "GET",
            "api/series/popular",
            200,
            params=params
        )
        return success, response

    def add_book(self, title, author, category="roman", saga="", volume_number=None):
        """Add a book to the library"""
        book_data = {
            "title": title,
            "author": author,
            "category": category,
            "saga": saga,
            "volume_number": volume_number,
            "status": "to_read"
        }
        
        success, response = self.run_test(
            f"Add Book '{title}'",
            "POST",
            "api/books",
            200,
            data=book_data
        )
        return success, response

def main():
    # Setup
    tester = SeriesManagementTester()
    test_user = f"Test_{datetime.now().strftime('%H%M%S')}"
    
    # Register user
    if not tester.register_user(test_user, "User"):
        print("❌ User registration failed, stopping tests")
        return 1

    print("\n=== TESTING PROMPT 1: SIMPLIFIED SERIES MANAGEMENT ===")
    
    # Test 1: Get books with series view mode (default)
    success, books_series = tester.test_get_books(view_mode="series")
    if not success:
        print("❌ Failed to get books with series view mode")
    else:
        print(f"📊 Found {len(books_series)} series/books in series view mode")
        
        # Check if series are displayed as unique entities
        series_cards = [book for book in books_series if book.get('isSeriesCard', False)]
        print(f"📊 Found {len(series_cards)} series cards in the response")
        
        # Check if progress is visible on series cards
        has_progress = any('progress_text' in card or 'completion_percentage' in card for card in series_cards)
        print(f"📊 Series cards show progress: {has_progress}")
    
    # Test 2: Get library series directly
    success, library_series = tester.test_get_library_series()
    if not success:
        print("❌ Failed to get library series")
    else:
        print(f"📊 Found {len(library_series)} series in library")
        
        # Check if progress information is available
        has_progress_info = any('progress_text' in series for series in library_series)
        print(f"📊 Series have progress information: {has_progress_info}")
    
    # Test 3: Search for Harry Potter series
    success, search_results = tester.test_search_books_grouped("Harry Potter")
    if not success:
        print("❌ Failed to search for Harry Potter")
    else:
        print(f"📊 Search results: {len(search_results.get('results', []))} items found")
        # Check if series are prioritized in results
        series_first = search_results.get('series_first', False)
        print(f"📊 Series First: {series_first}")
        
        # Check if Harry Potter appears as a series
        harry_potter_series = next((item for item in search_results.get('results', []) 
                                   if item.get('type') == 'saga' and 'Harry Potter' in item.get('name', '')), None)
        print(f"📊 Harry Potter appears as a series: {harry_potter_series is not None}")
    
    print("\n=== TESTING PROMPT 2: GLOBAL SEARCH ===")
    
    # Test 4: Global search across categories
    success, global_search = tester.test_search_books_grouped("Potter")
    if not success:
        print("❌ Failed to perform global search")
    else:
        print(f"📊 Global search results: {len(global_search.get('results', []))} items found")
        # Check if results are grouped by saga
        grouped_by_saga = global_search.get('grouped_by_saga', False)
        print(f"📊 Grouped by Saga: {grouped_by_saga}")
        
        # Check if results contain mixed categories
        categories = set()
        for item in global_search.get('results', []):
            if 'category' in item:
                categories.add(item['category'])
        
        print(f"📊 Search results contain multiple categories: {len(categories) > 1}")
        print(f"📊 Categories found: {', '.join(categories)}")
    
    # Add books from different categories to test intelligent placement
    print("\n--- Adding test books from different categories ---")
    tester.add_book("Test Roman", "Test Author", category="roman")
    tester.add_book("Test BD", "Test Author", category="bd")
    tester.add_book("Test Manga", "Test Author", category="manga")
    
    print("\n=== TESTING PROMPT 3: SPECIFIC SERIES FILTERING ===")
    
    # Test 5: Get popular series
    success, popular_series = tester.test_popular_series()
    if not success:
        print("❌ Failed to get popular series")
    else:
        print(f"📊 Found {len(popular_series.get('series', []))} popular series")
        
        # Find Astérix in popular series
        asterix_series = next((s for s in popular_series.get('series', []) if s.get('name') == 'Astérix'), None)
        if asterix_series:
            print("✅ Found Astérix in popular series")
            
            # Test 6: Get books for Astérix saga
            success, asterix_books = tester.test_get_saga_books("Astérix")
            if not success:
                print("❌ Failed to get Astérix books")
            else:
                print(f"📊 Found {len(asterix_books)} Astérix books")
                
                # Check if all books are from Astérix series
                all_asterix = all(book.get('saga') == 'Astérix' for book in asterix_books)
                print(f"📊 All books are from Astérix series: {all_asterix}")
                
                # Check if there are no other Goscinny works
                has_other_goscinny = any('goscinny' in book.get('author', '').lower() and 'lucky luke' in book.get('title', '').lower() for book in asterix_books)
                print(f"📊 Contains other Goscinny works (like Lucky Luke): {has_other_goscinny}")
        else:
            print("❌ Astérix not found in popular series")
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())