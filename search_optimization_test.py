import requests
import json
import sys
from datetime import datetime

class SearchOptimizationTester:
    def __init__(self, base_url="https://8d6421dd-3206-4a67-a223-7a1f1a7e4ca5.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, expected_content=None):
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
            
            # Try to parse response as JSON
            response_data = None
            try:
                response_data = response.json()
            except:
                response_data = response.text
                
            # Check content if expected_content is provided
            content_match = True
            content_details = ""
            if success and expected_content and response_data:
                if isinstance(response_data, dict):
                    for key, value in expected_content.items():
                        if key not in response_data:
                            content_match = False
                            content_details = f"Missing key: {key}"
                            break
                        if callable(value):
                            if not value(response_data[key]):
                                content_match = False
                                content_details = f"Value check failed for key: {key}"
                                break
                        elif response_data[key] != value:
                            content_match = False
                            content_details = f"Value mismatch for key: {key}. Expected: {value}, Got: {response_data[key]}"
                            break
                elif isinstance(response_data, list) and callable(expected_content):
                    if not expected_content(response_data):
                        content_match = False
                        content_details = "List content check failed"
            
            if success and content_match:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
            else:
                if not success:
                    print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                else:
                    print(f"❌ Failed - Content check: {content_details}")

            return success and content_match, response_data

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, None

    def test_register(self, first_name, last_name):
        """Test user registration"""
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

    def test_login(self, first_name, last_name):
        """Test user login"""
        success, response = self.run_test(
            "Login",
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

    def test_orthographic_tolerance(self, query, expected_series_name):
        """Test orthographic tolerance in series search"""
        success, response = self.run_test(
            f"Orthographic Tolerance: '{query}'",
            "GET",
            f"api/series/search?q={query}",
            200
        )
        
        if success and response and 'series' in response and len(response['series']) > 0:
            # Check if expected series is in top position
            top_result = response['series'][0]
            print(f"  Top result: {top_result['name']} (Score: {top_result.get('search_score', 'N/A')})")
            
            if top_result['name'] == expected_series_name:
                print(f"  ✅ Expected series '{expected_series_name}' found in position #1")
                return True
            else:
                # Check if it's in the results at all
                series_positions = [(i+1, s['name']) for i, s in enumerate(response['series']) if s['name'] == expected_series_name]
                if series_positions:
                    print(f"  ⚠️ Expected series '{expected_series_name}' found at position #{series_positions[0][0]}")
                    return False
                else:
                    print(f"  ❌ Expected series '{expected_series_name}' not found in results")
                    return False
        
        return False

    def test_series_prioritization(self, query, expected_series_name):
        """Test series prioritization in grouped search"""
        success, response = self.run_test(
            f"Series Prioritization: '{query}'",
            "GET",
            f"api/books/search-grouped?q={query}",
            200
        )
        
        if success and response and 'results' in response and len(response['results']) > 0:
            # Check if results contain series cards
            series_results = [r for r in response['results'] if r.get('isSeriesCard', False)]
            book_results = [r for r in response['results'] if not r.get('isSeriesCard', False)]
            
            print(f"  Found {len(series_results)} series and {len(book_results)} books")
            
            # Check if series are prioritized (appear first)
            if series_results and book_results and response['results'][0].get('isSeriesCard', False):
                print(f"  ✅ Series cards are prioritized (appear first)")
                
                # Check if expected series is in top position
                if series_results[0]['name'] == expected_series_name:
                    print(f"  ✅ Expected series '{expected_series_name}' found in position #1")
                    
                    # Check if series has high score (100000+)
                    if 'relevanceScore' in series_results[0] and series_results[0]['relevanceScore'] >= 100000:
                        print(f"  ✅ Series has high priority score: {series_results[0]['relevanceScore']}")
                        return True
                    else:
                        print(f"  ⚠️ Series does not have expected high priority score")
                        return False
                else:
                    # Check if it's in the results at all
                    series_positions = [(i+1, s['name']) for i, s in enumerate(series_results) if s['name'] == expected_series_name]
                    if series_positions:
                        print(f"  ⚠️ Expected series '{expected_series_name}' found at position #{series_positions[0][0]}")
                        return False
                    else:
                        print(f"  ❌ Expected series '{expected_series_name}' not found in results")
                        return False
            elif not series_results:
                print(f"  ❌ No series cards found in results")
                return False
            else:
                print(f"  ❌ Series cards are not prioritized")
                return False
        
        return False

    def test_strict_filtering(self, saga_name, excluded_terms):
        """Test strict filtering for saga books"""
        success, response = self.run_test(
            f"Strict Filtering: '{saga_name}'",
            "GET",
            f"api/sagas/{saga_name}/books",
            200
        )
        
        if success and isinstance(response, list):
            print(f"  Found {len(response)} books in saga '{saga_name}'")
            
            # Check if all books belong to the specified saga
            all_match = all(book.get('saga') == saga_name for book in response)
            if all_match:
                print(f"  ✅ All books correctly belong to saga '{saga_name}'")
            else:
                print(f"  ❌ Some books don't match the saga name")
                return False
            
            # Check for exclusions
            for term in excluded_terms:
                excluded_books = [b for b in response if term.lower() in b.get('title', '').lower() or 
                                 term.lower() in b.get('author', '').lower()]
                if not excluded_books:
                    print(f"  ✅ No '{term}' found (correctly filtered)")
                else:
                    print(f"  ❌ Found {len(excluded_books)} '{term}' items that should be filtered")
                    return False
            
            return True
        
        return False

    def add_test_books(self):
        """Add test books for search optimization testing"""
        books = [
            {
                "title": "Harry Potter à l'École des Sorciers",
                "author": "J.K. Rowling",
                "category": "roman",
                "saga": "Harry Potter",
                "volume_number": 1,
                "status": "completed"
            },
            {
                "title": "Harry Potter et la Chambre des Secrets",
                "author": "J.K. Rowling",
                "category": "roman",
                "saga": "Harry Potter",
                "volume_number": 2,
                "status": "completed"
            },
            {
                "title": "Harry Potter et le Prisonnier d'Azkaban",
                "author": "J.K. Rowling",
                "category": "roman",
                "saga": "Harry Potter",
                "volume_number": 3,
                "status": "completed"
            },
            {
                "title": "Harry Potter Guide Officiel",
                "author": "J.K. Rowling",
                "category": "roman",
                "saga": "Harry Potter",
                "volume_number": 0,
                "status": "to_read"
            },
            {
                "title": "Astérix le Gaulois",
                "author": "René Goscinny, Albert Uderzo",
                "category": "bd",
                "saga": "Astérix",
                "volume_number": 1,
                "status": "completed"
            },
            {
                "title": "Astérix - La Serpe d'Or",
                "author": "René Goscinny, Albert Uderzo",
                "category": "bd",
                "saga": "Astérix",
                "volume_number": 2,
                "status": "completed"
            },
            {
                "title": "Astérix et les Normands",
                "author": "Jean-Yves Ferri, Didier Conrad",
                "category": "bd",
                "saga": "Astérix",
                "volume_number": 39,
                "status": "to_read"
            },
            {
                "title": "One Piece Tome 1",
                "author": "Eiichiro Oda",
                "category": "manga",
                "saga": "One Piece",
                "volume_number": 1,
                "status": "completed"
            },
            {
                "title": "One Piece Tome 2",
                "author": "Eiichiro Oda",
                "category": "manga",
                "saga": "One Piece",
                "volume_number": 2,
                "status": "reading"
            },
            {
                "title": "Naruto Tome 1",
                "author": "Masashi Kishimoto",
                "category": "manga",
                "saga": "Naruto",
                "volume_number": 1,
                "status": "completed"
            },
            {
                "title": "Boruto: Naruto Next Generations",
                "author": "Ukyo Kodachi",
                "category": "manga",
                "saga": "Naruto",
                "volume_number": 1,
                "status": "to_read"
            },
            {
                "title": "Le Seigneur des Anneaux: La Communauté de l'Anneau",
                "author": "J.R.R. Tolkien",
                "category": "roman",
                "saga": "Le Seigneur des Anneaux",
                "volume_number": 1,
                "status": "completed"
            },
            {
                "title": "A Game of Thrones",
                "author": "George R.R. Martin",
                "category": "roman",
                "saga": "Le Trône de Fer",
                "volume_number": 1,
                "status": "reading"
            }
        ]
        
        added_count = 0
        for book in books:
            success, response = self.run_test(
                f"Add Book: {book['title']}",
                "POST",
                "api/books",
                200,
                data=book
            )
            if success:
                added_count += 1
        
        print(f"\n✅ Added {added_count}/{len(books)} test books")
        return added_count > 0

def main():
    # Setup
    tester = SearchOptimizationTester()
    test_user = f"test_user_{datetime.now().strftime('%H%M%S')}"
    
    # Register and login
    if not tester.test_register(test_user, "Tester"):
        print("❌ Registration failed, stopping tests")
        return 1
    
    # Add test books
    tester.add_test_books()
    
    print("\n=== TESTING ORTHOGRAPHIC TOLERANCE ===")
    
    # Test orthographic tolerance
    orthographic_tests = [
        ("herry potter", "Harry Potter"),
        ("astérics", "Astérix"),
        ("one pece", "One Piece"),
        ("seigneur anneaux", "Le Seigneur des Anneaux"),
        ("game of throne", "Le Trône de Fer")
    ]
    
    for query, expected in orthographic_tests:
        tester.test_orthographic_tolerance(query, expected)
    
    print("\n=== TESTING SERIES PRIORITIZATION ===")
    
    # Test series prioritization in search results
    prioritization_tests = [
        ("harry", "Harry Potter"),
        ("aster", "Astérix"),
        ("one", "One Piece"),
        ("seigneur", "Le Seigneur des Anneaux"),
        ("throne", "Le Trône de Fer")
    ]
    
    for query, expected in prioritization_tests:
        tester.test_series_prioritization(query, expected)
    
    print("\n=== TESTING STRICT FILTERING ===")
    
    # Test strict filtering
    filtering_tests = [
        ("Harry Potter", ["guide"]),
        ("Astérix", ["ferri", "conrad"]),
        ("Naruto", ["boruto"]),
        ("One Piece", ["guide", "databook"])
    ]
    
    for saga, excluded_terms in filtering_tests:
        tester.test_strict_filtering(saga, excluded_terms)
    
    # Print results
    print(f"\n📊 Tests passed: {tester.tests_passed}/{tester.tests_run}")
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())