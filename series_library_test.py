import requests
import sys
import json
from datetime import datetime

class SeriesLibraryTester:
    def __init__(self, base_url="https://27aef6f0-9be2-4486-a564-dbcd34faac2c.preview.emergentagent.com"):
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

    def test_login(self, first_name, last_name):
        """Test login and get token"""
        success, response = self.run_test(
            "Login",
            "POST",
            "api/auth/login",
            200,
            data={"first_name": first_name, "last_name": last_name}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            if 'user' in response and 'id' in response['user']:
                self.user_id = response['user']['id']
            return True
        return False

    def test_register(self, first_name, last_name):
        """Test registration and get token"""
        success, response = self.run_test(
            "Register",
            "POST",
            "api/auth/register",
            200,
            data={"first_name": first_name, "last_name": last_name}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            if 'user' in response and 'id' in response['user']:
                self.user_id = response['user']['id']
            return True
        return False

    def test_search_series(self, query):
        """Test searching for series"""
        success, response = self.run_test(
            f"Search Series: '{query}'",
            "GET",
            f"api/series/search",
            200,
            params={"q": query}
        )
        return success, response

    def test_add_series_to_library(self, series_data):
        """Test adding a series to the library"""
        success, response = self.run_test(
            f"Add Series to Library: '{series_data['series_name']}'",
            "POST",
            "api/series/library",
            200,
            data=series_data
        )
        return success, response

    def test_get_library_series(self):
        """Test getting all series in the library"""
        success, response = self.run_test(
            "Get Library Series",
            "GET",
            "api/series/library",
            200
        )
        return success, response

def main():
    # Setup
    tester = SeriesLibraryTester()
    
    # Test user credentials
    test_first_name = "Test"
    test_last_name = "User"

    # Run tests
    print("\n===== Testing BookTime API Series Library Functionality =====")
    
    # Login
    if not tester.test_login(test_first_name, test_last_name):
        print("❌ Login failed, trying to register...")
        if not tester.test_register(test_first_name, test_last_name):
            print("❌ Registration failed, stopping tests")
            return 1
    
    # Search for Harry Potter series
    search_success, search_results = tester.test_search_series("harry potter")
    if not search_success:
        print("❌ Series search failed, stopping tests")
        return 1
    
    print(f"\n📚 Found {len(search_results.get('series', []))} series matching 'harry potter'")
    
    # Check if Harry Potter series is in the results
    harry_potter_series = None
    for series in search_results.get('series', []):
        if series.get('name', '').lower() == 'harry potter':
            harry_potter_series = series
            print(f"✅ Found Harry Potter series in search results")
            break
    
    if not harry_potter_series:
        print("❌ Harry Potter series not found in search results, stopping tests")
        return 1
    
    # Prepare series data for adding to library
    series_data = {
        "series_name": harry_potter_series.get('name', 'Harry Potter'),
        "authors": harry_potter_series.get('authors', ['J.K. Rowling']),
        "category": harry_potter_series.get('category', 'roman'),
        "total_volumes": 7,
        "volumes": [
            {"volume_number": 1, "volume_title": "Harry Potter à l'École des Sorciers", "is_read": False},
            {"volume_number": 2, "volume_title": "Harry Potter et la Chambre des Secrets", "is_read": False},
            {"volume_number": 3, "volume_title": "Harry Potter et le Prisonnier d'Azkaban", "is_read": False},
            {"volume_number": 4, "volume_title": "Harry Potter et la Coupe de Feu", "is_read": False},
            {"volume_number": 5, "volume_title": "Harry Potter et l'Ordre du Phénix", "is_read": False},
            {"volume_number": 6, "volume_title": "Harry Potter et le Prince de Sang-Mêlé", "is_read": False},
            {"volume_number": 7, "volume_title": "Harry Potter et les Reliques de la Mort", "is_read": False}
        ],
        "series_status": "to_read",
        "description_fr": harry_potter_series.get('description', 'La saga emblématique du jeune sorcier Harry Potter'),
        "cover_image_url": "",
        "first_published": "1997",
        "last_published": "2007",
        "publisher": "Gallimard"
    }
    
    # Add series to library
    add_success, add_result = tester.test_add_series_to_library(series_data)
    if not add_success:
        print("❌ Adding series to library failed")
    else:
        print(f"✅ Successfully added series to library: {add_result.get('message', '')}")
    
    # Get all series in library
    get_success, get_result = tester.test_get_library_series()
    if not get_success:
        print("❌ Getting library series failed")
    else:
        series_count = len(get_result.get('series', []))
        print(f"✅ Found {series_count} series in library")
        
        # Check if Harry Potter is in the library
        harry_potter_in_library = False
        for series in get_result.get('series', []):
            if series.get('series_name', '').lower() == 'harry potter':
                harry_potter_in_library = True
                print(f"✅ Harry Potter series found in library with {len(series.get('volumes', []))} volumes")
                break
        
        if not harry_potter_in_library:
            print("❌ Harry Potter series not found in library after adding")
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())