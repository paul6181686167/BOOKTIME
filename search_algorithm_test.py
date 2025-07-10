import requests
import sys
import json
from datetime import datetime

class SearchAlgorithmTester:
    def __init__(self, base_url="https://80ed81fe-8288-46c1-beac-9587a62a6265.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = {}

    def run_test(self, name, method, endpoint, expected_status, data=None, expected_data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        if self.token:
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
                
                # Check expected data if provided
                if expected_data and response.status_code < 300:
                    response_data = response.json()
                    data_match = True
                    
                    for key, value in expected_data.items():
                        if key not in response_data or response_data[key] != value:
                            data_match = False
                            print(f"❌ Data mismatch - Expected {key}={value}, got {response_data.get(key, 'missing')}")
                    
                    if data_match:
                        print("✅ Response data matches expected values")
                    else:
                        success = False
                        self.tests_passed -= 1
                        print("❌ Response data does not match expected values")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                if response.status_code < 500:
                    try:
                        print(f"Response: {response.json()}")
                    except:
                        print(f"Response: {response.text}")

            # Store test result
            self.test_results[name] = {
                "success": success,
                "status_code": response.status_code,
                "expected_status": expected_status
            }
            
            if success and response.status_code < 300:
                try:
                    return success, response.json()
                except:
                    return success, {}
            return success, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.test_results[name] = {
                "success": False,
                "error": str(e)
            }
            return False, {}

    def register_user(self, first_name, last_name):
        """Register a test user"""
        success, response = self.run_test(
            "Register User",
            "POST",
            "api/auth/register",
            200,
            data={"first_name": first_name, "last_name": last_name}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            return True
        return False

    def login_user(self, first_name, last_name):
        """Login a test user"""
        success, response = self.run_test(
            "Login User",
            "POST",
            "api/auth/login",
            200,
            data={"first_name": first_name, "last_name": last_name}
        )
        
        if success and 'access_token' in response:
            self.token = response['access_token']
            self.user_id = response['user']['id']
            return True
        return False

    def search_books_grouped(self, query):
        """Search for books with the given query using the grouped search endpoint"""
        success, response = self.run_test(
            f"Search Books Grouped: {query}",
            "GET",
            f"api/books/search-grouped?q={query}",
            200
        )
        
        return success, response

    def search_series(self, query):
        """Search for series with the given query"""
        success, response = self.run_test(
            f"Search Series: {query}",
            "GET",
            f"api/series/search?q={query}",
            200
        )
        
        return success, response

    def get_saga_books(self, saga_name):
        """Get books for a specific saga"""
        success, response = self.run_test(
            f"Get Saga Books: {saga_name}",
            "GET",
            f"api/sagas/{saga_name}/books",
            200
        )
        
        return success, response

    def print_summary(self):
        """Print a summary of all test results"""
        print("\n" + "="*50)
        print(f"📊 TEST SUMMARY: {self.tests_passed}/{self.tests_run} tests passed")
        print("="*50)
        
        # Group tests by category
        categories = {
            "Series Prioritization": [test for test in self.test_results if test.startswith("Search Books Grouped:")],
            "Spelling Tolerance": [test for test in self.test_results if test.startswith("Search Series:")],
            "Strict Filtering": [test for test in self.test_results if test.startswith("Get Saga Books:")]
        }
        
        for category, tests in categories.items():
            passed = sum(1 for test in tests if test in self.test_results and self.test_results[test]["success"])
            total = len(tests)
            if total > 0:
                print(f"\n{category}: {passed}/{total} passed")
                for test in tests:
                    if test in self.test_results:
                        status = "✅ PASS" if self.test_results[test]["success"] else "❌ FAIL"
                        print(f"  {status} - {test}")
        
        return self.tests_passed == self.tests_run

def test_series_prioritization(tester):
    """Test that series always appear first in search results"""
    print("\n" + "="*50)
    print("🔍 TESTING SERIES PRIORITIZATION")
    print("="*50)
    print("Verifying that series always appear FIRST in search results")
    
    # Test search prioritization
    tests = [
        {"query": "harry potter", "expected_series": "Harry Potter"},
        {"query": "astérix", "expected_series": "Astérix"},
        {"query": "one piece", "expected_series": "One Piece"},
        {"query": "tintin", "expected_series": "Tintin"}
    ]
    
    results = []
    for test in tests:
        success, response = tester.search_books_grouped(test["query"])
        if success and response.get("results"):
            first_result = response["results"][0]
            
            # Check if the first result is a series
            is_series = False
            series_name = ""
            
            if first_result.get("type") == "saga" or first_result.get("isSeriesCard", False):
                is_series = True
                series_name = first_result.get("name", "")
            
            # Check if the expected series is found
            expected_series_found = test["expected_series"].lower() in series_name.lower()
            
            if is_series and expected_series_found:
                print(f"✅ '{test['query']}' search shows '{series_name}' series first with badge '📚 SÉRIE'")
                print(f"   Score: {first_result.get('relevanceScore', 'N/A')}")
                results.append(True)
            elif is_series:
                print(f"⚠️ '{test['query']}' shows a series first, but not the expected one: '{series_name}'")
                results.append(False)
            else:
                print(f"❌ '{test['query']}' search does not show series first")
                results.append(False)
        else:
            print(f"❌ Search for '{test['query']}' failed")
            results.append(False)
    
    return all(results)

def test_spelling_tolerance(tester):
    """Test that the search algorithm handles spelling errors"""
    print("\n" + "="*50)
    print("🔍 TESTING SPELLING TOLERANCE")
    print("="*50)
    print("Verifying that the algorithm finds series despite spelling errors")
    
    # Test with misspelled queries
    tests = [
        {"query": "herry potter", "expected_match": "Harry Potter"},
        {"query": "astérics", "expected_match": "Astérix"},
        {"query": "one pece", "expected_match": "One Piece"},
        {"query": "naroto", "expected_match": "Naruto"},
        {"query": "seigneur anneaux", "expected_match": "Le Seigneur des Anneaux"},
        {"query": "game of throne", "expected_match": "Le Trône de Fer"}
    ]
    
    results = []
    for test in tests:
        success, response = tester.search_series(test["query"])
        if success and response.get("series"):
            found_match = False
            match_type = ""
            score = 0
            
            for series in response["series"]:
                if test["expected_match"].lower() in series["name"].lower():
                    found_match = True
                    match_type = series.get("match_reasons", ["unknown"])[0] if series.get("match_reasons") else "unknown"
                    score = series.get("search_score", 0)
                    print(f"✅ Misspelled '{test['query']}' correctly matched '{series['name']}'")
                    print(f"   Match type: {match_type}, Score: {score}")
                    break
            
            if not found_match:
                print(f"❌ Misspelled '{test['query']}' did not match '{test['expected_match']}'")
                results.append(False)
            else:
                results.append(True)
        else:
            print(f"❌ Search for misspelled '{test['query']}' failed")
            results.append(False)
    
    return all(results)

def test_strict_filtering(tester):
    """Test that series pages only show official works"""
    print("\n" + "="*50)
    print("🔍 TESTING STRICT FILTERING")
    print("="*50)
    print("Verifying that series pages only show official works")
    
    # Test strict filtering
    tests = [
        {"saga": "Harry Potter", "excluded": ["Tales of Beedle", "Fantastic Beasts"]},
        {"saga": "Astérix", "excluded": ["Ferri", "Conrad"]},
        {"saga": "Naruto", "excluded": ["Boruto", "Next Generation"]},
        {"saga": "Dragon Ball", "excluded": ["Dragon Ball Super", "GT"]}
    ]
    
    results = []
    for test in tests:
        success, response = tester.get_saga_books(test["saga"])
        if success:
            excluded_found = []
            
            for excluded_term in test["excluded"]:
                for book in response:
                    if excluded_term.lower() in book["title"].lower() or excluded_term.lower() in book.get("description", "").lower():
                        excluded_found.append(f"{excluded_term} in {book['title']}")
                        break
            
            if excluded_found:
                print(f"❌ Saga '{test['saga']}' incorrectly includes excluded works: {', '.join(excluded_found)}")
                results.append(False)
            else:
                print(f"✅ Saga '{test['saga']}' correctly excludes non-official works")
                results.append(True)
        else:
            print(f"❌ Getting books for saga '{test['saga']}' failed")
            results.append(False)
    
    return all(results)

def main():
    # Setup
    tester = SearchAlgorithmTester()
    test_user = f"test_user_{datetime.now().strftime('%H%M%S')}"
    
    # Register and login
    if not tester.register_user(test_user, "Tester"):
        print("❌ Registration failed, stopping tests")
        return 1
    
    # Run test suites
    prioritization_passed = test_series_prioritization(tester)
    spelling_passed = test_spelling_tolerance(tester)
    filtering_passed = test_strict_filtering(tester)
    
    # Print overall summary
    tester.print_summary()
    
    print("\n" + "="*50)
    print("📋 REQUIREMENTS VALIDATION")
    print("="*50)
    print(f"1. SERIES PRIORITIZATION: {'✅ PASSED' if prioritization_passed else '❌ FAILED'}")
    print(f"2. SPELLING TOLERANCE: {'✅ PASSED' if spelling_passed else '❌ FAILED'}")
    print(f"3. STRICT FILTERING: {'✅ PASSED' if filtering_passed else '❌ FAILED'}")
    
    return 0 if prioritization_passed and spelling_passed and filtering_passed else 1

if __name__ == "__main__":
    sys.exit(main())