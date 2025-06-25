import requests
import unittest
import os
import sys
import json
from datetime import datetime

class TranslationAPITester:
    def __init__(self, base_url=None):
        self.base_url = base_url or os.environ.get("REACT_APP_BACKEND_URL", "https://c56cd16a-391e-484d-8d06-7faf7600b18a.preview.emergentagent.com")
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

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
            
            # Try to get response data
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text[:200] + "..." if len(response.text) > 200 else response.text}
            
            result = {
                "name": name,
                "success": success,
                "status_code": response.status_code,
                "expected_status": expected_status,
                "response_data": response_data
            }
            
            self.test_results.append(result)
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print("Response: " + response.text[:200] + "...")

            return success, response_data if success else {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            self.test_results.append({
                "name": name,
                "success": False,
                "error": str(e)
            })
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
            return True
        return False

    def test_register(self, first_name, last_name):
        """Test registration"""
        success, response = self.run_test(
            "Register",
            "POST",
            "api/auth/register",
            200,
            data={"first_name": first_name, "last_name": last_name}
        )
        if success and 'access_token' in response:
            self.token = response['access_token']
            return True
        return False

    def test_search_openlibrary(self, query, check_translation=True):
        """Test OpenLibrary search with translation check"""
        success, response = self.run_test(
            f"OpenLibrary Search: {query}",
            "GET",
            "api/openlibrary/search-universal",
            200,
            params={"q": query}
        )
        
        if success and check_translation:
            # Check if we have books with descriptions
            books_with_desc = [book for book in response.get('books', []) if book.get('description')]
            
            if books_with_desc:
                # Check if descriptions contain French words
                french_words = ['le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou', 'avec', 'dans', 'sur', 'pour', 'par', 'est', 'sont']
                
                for book in books_with_desc[:3]:  # Check first 3 books with descriptions
                    desc = book.get('description', '').lower()
                    french_word_count = sum(1 for word in french_words if f' {word} ' in f' {desc} ')
                    
                    translation_test = {
                        "name": f"Translation Check for '{book.get('title')}'",
                        "success": french_word_count >= 3,
                        "french_word_count": french_word_count,
                        "description_sample": desc[:100] + "..." if len(desc) > 100 else desc
                    }
                    
                    self.test_results.append(translation_test)
                    
                    if translation_test["success"]:
                        self.tests_passed += 1
                        print(f"✅ Translation Check Passed - Found {french_word_count} French words")
                    else:
                        print(f"❌ Translation Check Failed - Only found {french_word_count} French words")
                    
                    self.tests_run += 1
        
        return success, response

    def test_get_book_details(self, work_key, check_translation=True):
        """Test getting book details with translation check"""
        success, response = self.run_test(
            f"Get Book Details: {work_key}",
            "GET",
            f"api/openlibrary/book/{work_key}",
            200
        )
        
        if success and check_translation and response.get('description'):
            # Check if description contains French words
            french_words = ['le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou', 'avec', 'dans', 'sur', 'pour', 'par', 'est', 'sont']
            desc = response.get('description', '').lower()
            french_word_count = sum(1 for word in french_words if f' {word} ' in f' {desc} ')
            
            translation_test = {
                "name": f"Translation Check for Book Details",
                "success": french_word_count >= 3,
                "french_word_count": french_word_count,
                "description_sample": desc[:100] + "..." if len(desc) > 100 else desc
            }
            
            self.test_results.append(translation_test)
            
            if translation_test["success"]:
                self.tests_passed += 1
                print(f"✅ Translation Check Passed - Found {french_word_count} French words")
            else:
                print(f"❌ Translation Check Failed - Only found {french_word_count} French words")
            
            self.tests_run += 1
        
        return success, response

    def test_import_book(self, work_key, category="roman"):
        """Test importing a book from OpenLibrary"""
        success, response = self.run_test(
            f"Import Book: {work_key}",
            "POST",
            "api/openlibrary/import",
            200,
            data={"ol_key": work_key, "category": category}
        )
        
        if success and response.get('description'):
            # Check if description contains French words
            french_words = ['le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou', 'avec', 'dans', 'sur', 'pour', 'par', 'est', 'sont']
            desc = response.get('description', '').lower()
            french_word_count = sum(1 for word in french_words if f' {word} ' in f' {desc} ')
            
            translation_test = {
                "name": f"Translation Check for Imported Book",
                "success": french_word_count >= 3,
                "french_word_count": french_word_count,
                "description_sample": desc[:100] + "..." if len(desc) > 100 else desc
            }
            
            self.test_results.append(translation_test)
            
            if translation_test["success"]:
                self.tests_passed += 1
                print(f"✅ Translation Check Passed - Found {french_word_count} French words")
            else:
                print(f"❌ Translation Check Failed - Only found {french_word_count} French words")
            
            self.tests_run += 1
        
        return success, response

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*50)
        print(f"📊 TEST SUMMARY: {self.tests_passed}/{self.tests_run} tests passed")
        print("="*50)
        
        # Print failed tests
        failed_tests = [test for test in self.test_results if not test.get("success")]
        if failed_tests:
            print("\n❌ FAILED TESTS:")
            for test in failed_tests:
                error_msg = test.get('error', '')
                if not error_msg and 'expected_status' in test and 'status_code' in test:
                    error_msg = f"Expected status {test.get('expected_status')}, got {test.get('status_code')}"
                print(f"- {test.get('name')}: {error_msg}")
        
        # Print translation test results
        translation_tests = [test for test in self.test_results if "Translation Check" in test.get("name", "")]
        if translation_tests:
            print("\n🔤 TRANSLATION TESTS:")
            for test in translation_tests:
                status = "✅ PASSED" if test.get("success") else "❌ FAILED"
                print(f"- {test.get('name')}: {status} ({test.get('french_word_count')} French words)")
                print(f"  Sample: {test.get('description_sample')}")
        
        return self.tests_passed == self.tests_run

def main():
    print("="*50)
    print("🔍 BOOKTIME API TESTING - TRANSLATION FEATURE")
    print("="*50)
    
    tester = TranslationAPITester()
    
    # Login with test user
    if not tester.test_login("Test", "User"):
        print("❌ Login failed, trying to register...")
        if not tester.test_register("Test", "User"):
            print("❌ Registration failed, stopping tests")
            return 1
    
    # Test OpenLibrary search with translation
    print("\n📚 Testing OpenLibrary search with translation...")
    books_to_test = ["Harry Potter", "Lord of the Rings", "Pride and Prejudice", "1984"]
    
    for book in books_to_test:
        success, response = tester.test_search_openlibrary(book)
        if success and response.get('books'):
            print(f"Found {len(response['books'])} results for '{book}'")
            
            # If we have a book with a work_key, test the book details
            books_with_key = [b for b in response['books'] if b.get('work_key')]
            if books_with_key:
                work_key = books_with_key[0]['work_key']
                print(f"\n📖 Testing book details for work_key: {work_key}")
                tester.test_get_book_details(work_key)
                
                # Try to import the book
                print(f"\n📥 Testing book import for work_key: {work_key}")
                tester.test_import_book(work_key)
                break
    
    # Print summary
    tester.print_summary()
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())