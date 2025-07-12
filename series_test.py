import requests
import unittest
import sys
from datetime import datetime

class SeriesAPITester:
    def __init__(self, base_url="https://0b242f2a-081a-491a-bb79-9c027627f29c.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}{endpoint}"
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
                if response.content:
                    try:
                        return success, response.json()
                    except:
                        return success, response.content
                return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                if response.content:
                    try:
                        print(f"Response: {response.json()}")
                    except:
                        print(f"Response: {response.content}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_get_series(self):
        """Test getting all series"""
        return self.run_test(
            "Get All Series",
            "GET",
            "/api/series",
            200
        )

    def test_get_series_details(self):
        """Test getting series details"""
        # First get all series
        success, series_data = self.test_get_series()
        if not success or not series_data.get('series'):
            print("❌ No series found to test series details")
            return False, {}
        
        # Get the first series name
        series_name = series_data['series'][0]['name']
        return self.run_test(
            f"Get Series Details for '{series_name}'",
            "GET",
            f"/api/series/{series_name}",
            200
        )

    def test_create_book_with_saga(self):
        """Test creating a book with saga information"""
        book_data = {
            "title": f"Test Book in Series {datetime.now().strftime('%H%M%S')}",
            "author": "Test Author",
            "category": "roman",
            "description": "Test description",
            "saga": "Test Saga",
            "volume_number": 1
        }
        return self.run_test(
            "Create Book with Saga",
            "POST",
            "/api/books",
            200,
            data=book_data
        )

def main():
    # Setup
    tester = SeriesAPITester()
    
    # Run tests
    tester.test_get_series()
    tester.test_get_series_details()
    tester.test_create_book_with_saga()

    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())