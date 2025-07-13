#!/usr/bin/env python3
"""
BOOKTIME - Tests Backend Système Unifié (Phases A-D)
Tests complets pour validation du système unifié avec authentification JWT
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Configuration
BACKEND_URL = "https://2edc0e99-0260-4be3-89a3-942129c74df3.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class BooktimeUnifiedTester:
    def __init__(self):
        self.token = None
        self.headers = {'Content-Type': 'application/json'}
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'errors': []
        }
        self.cleanup_ids = []

    def log_result(self, test_name, success, message="", error=None):
        """Log test result"""
        self.test_results['total_tests'] += 1
        if success:
            self.test_results['passed_tests'] += 1
            print(f"✅ {test_name}: {message}")
        else:
            self.test_results['failed_tests'] += 1
            error_msg = f"❌ {test_name}: {message}"
            if error:
                error_msg += f" - Error: {error}"
            print(error_msg)
            self.test_results['errors'].append(error_msg)

    def test_health_check(self):
        """Test 1: Basic health and connectivity"""
        print("\n🔍 Test 1: Health Check and Connectivity")
        
        try:
            # Test health endpoint
            response = requests.get(f"{BACKEND_URL}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok" and data.get("database") == "connected":
                    self.log_result("Health Check", True, "Backend and database connected")
                    return True
                else:
                    self.log_result("Health Check", False, f"Unexpected health response: {data}")
            else:
                self.log_result("Health Check", False, f"Health endpoint returned {response.status_code}")
        except Exception as e:
            self.log_result("Health Check", False, "Health endpoint failed", str(e))
        
        return False

    def test_authentication(self):
        """Test 2: JWT Authentication System"""
        print("\n🔐 Test 2: Authentication System")
        
        # Generate unique user data
        timestamp = int(time.time())
        test_user = {
            "first_name": f"TestUser{timestamp}",
            "last_name": f"Unified{timestamp}",
            "password": "testpass123"
        }
        
        try:
            # Test registration
            response = requests.post(f"{API_URL}/auth/register", json=test_user, timeout=10)
            if response.status_code == 200:
                user_data = response.json()
                if "access_token" in user_data:
                    self.token = user_data["access_token"]
                    self.headers['Authorization'] = f'Bearer {self.token}'
                    self.log_result("User Registration", True, f"User {test_user['first_name']} registered")
                    
                    # Test login
                    login_data = {
                        "first_name": test_user["first_name"],
                        "last_name": test_user["last_name"],
                        "password": test_user["password"]
                    }
                    response = requests.post(f"{API_URL}/auth/login", json=login_data, timeout=10)
                    if response.status_code == 200:
                        login_result = response.json()
                        if "access_token" in login_result:
                            self.log_result("User Login", True, "Login successful")
                            return True
                        else:
                            self.log_result("User Login", False, "No access token in login response")
                    else:
                        self.log_result("User Login", False, f"Login failed with status {response.status_code}")
                else:
                    self.log_result("User Registration", False, "No access token in registration response")
            else:
                # User might already exist, try login
                login_data = {
                    "first_name": test_user["first_name"],
                    "last_name": test_user["last_name"],
                    "password": test_user["password"]
                }
                response = requests.post(f"{API_URL}/auth/login", json=login_data, timeout=10)
                if response.status_code == 200:
                    login_result = response.json()
                    if "access_token" in login_result:
                        self.token = login_result["access_token"]
                        self.headers['Authorization'] = f'Bearer {self.token}'
                        self.log_result("User Login (existing)", True, "Login with existing user successful")
                        return True
                
                self.log_result("Authentication", False, f"Registration failed with status {response.status_code}")
        except Exception as e:
            self.log_result("Authentication", False, "Authentication failed", str(e))
        
        return False

    def test_unified_content_endpoints(self):
        """Test 3: Unified Content System Endpoints"""
        print("\n🔄 Test 3: Unified Content System")
        
        if not self.token:
            self.log_result("Unified Content", False, "No authentication token available")
            return False
        
        try:
            # Test books endpoint
            response = requests.get(f"{API_URL}/books", headers=self.headers, timeout=10)
            if response.status_code == 200:
                books = response.json()
                self.log_result("Books Endpoint", True, f"Retrieved {len(books)} books")
            else:
                self.log_result("Books Endpoint", False, f"Books endpoint returned {response.status_code}")
                return False
            
            # Test stats endpoint
            response = requests.get(f"{API_URL}/stats", headers=self.headers, timeout=10)
            if response.status_code == 200:
                stats = response.json()
                if "total_books" in stats:
                    self.log_result("Stats Endpoint", True, f"Stats retrieved - Total books: {stats.get('total_books', 0)}")
                else:
                    self.log_result("Stats Endpoint", False, "Stats missing total_books field")
            else:
                self.log_result("Stats Endpoint", False, f"Stats endpoint returned {response.status_code}")
            
            # Test series library endpoint
            response = requests.get(f"{API_URL}/library/series", headers=self.headers, timeout=10)
            if response.status_code == 200:
                series = response.json()
                self.log_result("Series Library", True, f"Retrieved {len(series)} series")
                return True
            else:
                self.log_result("Series Library", False, f"Series library returned {response.status_code}")
                
        except Exception as e:
            self.log_result("Unified Content", False, "Unified content test failed", str(e))
        
        return False

    def test_book_operations(self):
        """Test 4: Book CRUD Operations"""
        print("\n📚 Test 4: Book Operations")
        
        if not self.token:
            self.log_result("Book Operations", False, "No authentication token available")
            return False
        
        try:
            # Test adding a book
            test_book = {
                "title": f"Test Book {int(time.time())}",
                "author": "Test Author",
                "category": "roman",
                "description": "Test book for unified system"
            }
            
            response = requests.post(f"{API_URL}/books", json=test_book, headers=self.headers, timeout=10)
            if response.status_code == 200:
                book_result = response.json()
                book_id = book_result.get("_id")
                if book_id:
                    self.cleanup_ids.append(book_id)
                    self.log_result("Book Creation", True, f"Book '{test_book['title']}' created")
                    
                    # Test updating the book
                    update_data = {"status": "reading", "current_page": 50}
                    response = requests.put(f"{API_URL}/books/{book_id}", json=update_data, headers=self.headers, timeout=10)
                    if response.status_code == 200:
                        self.log_result("Book Update", True, "Book status updated to reading")
                        
                        # Test retrieving the book
                        response = requests.get(f"{API_URL}/books/{book_id}", headers=self.headers, timeout=10)
                        if response.status_code == 200:
                            updated_book = response.json()
                            if updated_book.get("status") == "reading":
                                self.log_result("Book Retrieval", True, "Book retrieved with updated status")
                                return True
                            else:
                                self.log_result("Book Retrieval", False, "Book status not updated correctly")
                        else:
                            self.log_result("Book Retrieval", False, f"Book retrieval returned {response.status_code}")
                    else:
                        self.log_result("Book Update", False, f"Book update returned {response.status_code}")
                else:
                    self.log_result("Book Creation", False, "No book ID returned")
            else:
                self.log_result("Book Creation", False, f"Book creation returned {response.status_code}")
                
        except Exception as e:
            self.log_result("Book Operations", False, "Book operations failed", str(e))
        
        return False

    def test_open_library_integration(self):
        """Test 5: Open Library Integration"""
        print("\n🌐 Test 5: Open Library Integration")
        
        if not self.token:
            self.log_result("Open Library", False, "No authentication token available")
            return False
        
        try:
            # Test Open Library search
            search_query = "Dune"
            response = requests.get(f"{API_URL}/openlibrary/search?q={search_query}", headers=self.headers, timeout=15)
            if response.status_code == 200:
                search_results = response.json()
                if isinstance(search_results, list) and len(search_results) > 0:
                    self.log_result("Open Library Search", True, f"Found {len(search_results)} results for '{search_query}'")
                    return True
                else:
                    self.log_result("Open Library Search", False, "No search results returned")
            else:
                self.log_result("Open Library Search", False, f"Search returned {response.status_code}")
                
        except Exception as e:
            self.log_result("Open Library", False, "Open Library test failed", str(e))
        
        return False

    def test_performance_metrics(self):
        """Test 6: Performance and Caching"""
        print("\n⚡ Test 6: Performance Metrics")
        
        if not self.token:
            self.log_result("Performance", False, "No authentication token available")
            return False
        
        try:
            # Test multiple rapid requests to check performance
            start_time = time.time()
            successful_requests = 0
            
            for i in range(3):
                response = requests.get(f"{API_URL}/books", headers=self.headers, timeout=10)
                if response.status_code == 200:
                    successful_requests += 1
            
            total_time = (time.time() - start_time) * 1000  # Convert to ms
            
            if successful_requests == 3:
                if total_time < 3000:  # Less than 3 seconds for 3 requests
                    self.log_result("Performance Test", True, f"3 requests completed in {total_time:.0f}ms")
                    return True
                else:
                    self.log_result("Performance Test", False, f"Performance slow: {total_time:.0f}ms for 3 requests")
            else:
                self.log_result("Performance Test", False, f"Only {successful_requests}/3 requests successful")
                
        except Exception as e:
            self.log_result("Performance", False, "Performance test failed", str(e))
        
        return False

    def cleanup(self):
        """Clean up test data"""
        if self.token and self.cleanup_ids:
            print(f"\n🧹 Cleaning up {len(self.cleanup_ids)} test items...")
            for item_id in self.cleanup_ids:
                try:
                    requests.delete(f"{API_URL}/books/{item_id}", headers=self.headers, timeout=5)
                except:
                    pass

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 BOOKTIME - Tests Backend Système Unifié (Phases A-D)")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run tests in sequence
        tests = [
            self.test_health_check,
            self.test_authentication,
            self.test_unified_content_endpoints,
            self.test_book_operations,
            self.test_open_library_integration,
            self.test_performance_metrics
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                self.log_result(test.__name__, False, "Test execution failed", str(e))
        
        # Cleanup
        self.cleanup()
        
        # Final results
        total_time = time.time() - start_time
        print("\n" + "=" * 60)
        print("📊 RÉSULTATS FINAUX")
        print("=" * 60)
        print(f"Tests exécutés: {self.test_results['total_tests']}")
        print(f"Tests réussis: {self.test_results['passed_tests']}")
        print(f"Tests échoués: {self.test_results['failed_tests']}")
        print(f"Temps total: {total_time:.2f}s")
        
        success_rate = (self.test_results['passed_tests'] / self.test_results['total_tests']) * 100 if self.test_results['total_tests'] > 0 else 0
        print(f"Taux de réussite: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 SYSTÈME VALIDÉ - Prêt pour les tests frontend")
        elif success_rate >= 60:
            print("⚠️ SYSTÈME PARTIELLEMENT FONCTIONNEL - Corrections mineures nécessaires")
        else:
            print("❌ SYSTÈME NON FONCTIONNEL - Corrections majeures requises")
        
        if self.test_results['errors']:
            print("\n🔍 ERREURS DÉTECTÉES:")
            for error in self.test_results['errors']:
                print(f"  • {error}")
        
        return success_rate >= 60

if __name__ == "__main__":
    tester = BooktimeUnifiedTester()
    success = tester.run_all_tests()
    exit(0 if success else 1)