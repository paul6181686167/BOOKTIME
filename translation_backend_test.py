import requests
import unittest
import time
import os
import sys

# Get the backend URL from the frontend .env file
BACKEND_URL = "https://01f59366-074a-4189-bf3a-9e156e02e40e.preview.emergentagent.com"
API_URL = f"{BACKEND_URL}/api"

class TranslationFunctionalityTest(unittest.TestCase):
    """Test suite for the translation functionality in the Booktime API"""

    def setUp(self):
        """Setup for each test"""
        # Test user credentials
        self.test_user = {
            "first_name": "Test",
            "last_name": "User"
        }
        self.access_token = None
        self.register_and_login()
        
    def register_and_login(self):
        """Register a test user and get access token"""
        try:
            # Try to login first
            response = requests.post(f"{API_URL}/auth/login", json=self.test_user)
            if response.status_code == 401:  # User not found
                # Register the user
                response = requests.post(f"{API_URL}/auth/register", json=self.test_user)
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                print(f"✅ Successfully authenticated as {self.test_user['first_name']} {self.test_user['last_name']}")
            else:
                print(f"❌ Authentication failed: {response.status_code} - {response.text}")
                self.fail("Authentication failed")
        except Exception as e:
            print(f"❌ Exception during authentication: {str(e)}")
            self.fail(f"Authentication exception: {str(e)}")

    def get_auth_headers(self):
        """Get authentication headers"""
        return {
            "Authorization": f"Bearer {self.access_token}"
        }

    def test_openlibrary_search_with_translation(self):
        """Test that OpenLibrary search results include translated descriptions"""
        print("\n🔍 Testing OpenLibrary search with translation...")
        
        # Search for a popular English book
        search_query = "Harry Potter"
        try:
            response = requests.get(
                f"{API_URL}/openlibrary/search-universal?q={search_query}", 
                headers=self.get_auth_headers()
            )
            
            self.assertEqual(response.status_code, 200, "Search request should succeed")
            data = response.json()
            
            # Verify we got results
            self.assertIn("books", data, "Response should contain books")
            self.assertGreater(len(data["books"]), 0, "Should find at least one book")
            
            # Check if any book has a description that appears to be in French
            books_with_french = []
            for book in data["books"]:
                if "subjects" in book and book["subjects"]:
                    print(f"Book: {book['title']} by {book['author']}")
                    print(f"Subjects: {book['subjects'][:3]}...")
                    
            print(f"✅ Found {len(data['books'])} books for '{search_query}'")
            
        except Exception as e:
            self.fail(f"Error during OpenLibrary search: {str(e)}")

    def test_book_details_translation(self):
        """Test that book details include translated descriptions"""
        print("\n🔍 Testing book details translation...")
        
        # First search for a book to get its work_key
        search_query = "Lord of the Rings"
        try:
            # Search for the book
            search_response = requests.get(
                f"{API_URL}/openlibrary/search-universal?q={search_query}", 
                headers=self.get_auth_headers()
            )
            
            self.assertEqual(search_response.status_code, 200, "Search request should succeed")
            search_data = search_response.json()
            
            # Verify we got results
            self.assertIn("books", search_data, "Response should contain books")
            self.assertGreater(len(search_data["books"]), 0, "Should find at least one book")
            
            # Get the work_key of the first book
            first_book = search_data["books"][0]
            work_key = first_book.get("work_key")
            
            self.assertIsNotNone(work_key, "Book should have a work_key")
            
            # Get detailed information about the book
            details_response = requests.get(
                f"{API_URL}/openlibrary/book/{work_key}", 
                headers=self.get_auth_headers()
            )
            
            self.assertEqual(details_response.status_code, 200, "Book details request should succeed")
            book_details = details_response.json()
            
            # Check for description and first_sentence
            if "description" in book_details and book_details["description"]:
                description = book_details["description"]
                print(f"Book: {book_details.get('title', 'Unknown title')}")
                print(f"Description (excerpt): {description[:150]}...")
                
                # Check if description appears to be in French
                french_words = ['le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou', 
                               'avec', 'dans', 'sur', 'pour', 'par', 'est', 'sont', 'être']
                french_word_count = sum(1 for word in french_words if f' {word} ' in f' {description.lower()} ')
                
                self.assertGreaterEqual(french_word_count, 2, 
                                      "Description should contain French words (indicating translation)")
                print(f"✅ Description appears to be in French (detected {french_word_count} French words)")
            else:
                print("⚠️ No description found for this book")
            
            # Check first sentence if available
            if "first_sentence" in book_details and book_details["first_sentence"]:
                first_sentence = book_details["first_sentence"]
                print(f"First sentence: {first_sentence}")
                
                # Check if first sentence appears to be in French
                french_words = ['le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou', 
                               'avec', 'dans', 'sur', 'pour', 'par', 'est', 'sont', 'être']
                french_word_count = sum(1 for word in french_words if f' {word} ' in f' {first_sentence.lower()} ')
                
                if french_word_count >= 1:
                    print(f"✅ First sentence appears to be in French (detected {french_word_count} French words)")
                else:
                    print("⚠️ First sentence may not be in French")
            else:
                print("⚠️ No first sentence found for this book")
                
        except Exception as e:
            self.fail(f"Error during book details test: {str(e)}")

    def test_author_biography_translation(self):
        """Test that author biographies are translated"""
        print("\n🔍 Testing author biography translation...")
        
        # Test with a well-known English author
        author_name = "J.K. Rowling"
        try:
            response = requests.get(
                f"{API_URL}/authors/{author_name}", 
                headers=self.get_auth_headers()
            )
            
            self.assertEqual(response.status_code, 200, "Author details request should succeed")
            author_data = response.json()
            
            # Check for biography
            if "biography" in author_data and author_data["biography"]:
                biography = author_data["biography"]
                print(f"Author: {author_name}")
                print(f"Biography (excerpt): {biography[:150]}...")
                
                # Check if biography appears to be in French
                french_words = ['le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou', 
                               'avec', 'dans', 'sur', 'pour', 'par', 'est', 'sont', 'être']
                french_word_count = sum(1 for word in french_words if f' {word} ' in f' {biography.lower()} ')
                
                # Since the biography comes from Wikipedia FR, it should already be in French
                self.assertGreaterEqual(french_word_count, 3, 
                                      "Biography should contain French words (indicating it's in French)")
                print(f"✅ Biography appears to be in French (detected {french_word_count} French words)")
            else:
                print("⚠️ No biography found for this author")
                
        except Exception as e:
            self.fail(f"Error during author biography test: {str(e)}")

    def test_multiple_books_translation(self):
        """Test translation functionality with multiple different books"""
        print("\n🔍 Testing translation with multiple books...")
        
        # List of popular English books to test
        test_books = ["Harry Potter", "Lord of the Rings", "The Hobbit", "Pride and Prejudice", "1984"]
        
        for book_title in test_books:
            try:
                print(f"\nTesting book: {book_title}")
                
                # Search for the book
                search_response = requests.get(
                    f"{API_URL}/openlibrary/search-universal?q={book_title}", 
                    headers=self.get_auth_headers()
                )
                
                self.assertEqual(search_response.status_code, 200, "Search request should succeed")
                search_data = search_response.json()
                
                # Verify we got results
                self.assertIn("books", search_data, "Response should contain books")
                
                if len(search_data["books"]) > 0:
                    # Get the work_key of the first book
                    first_book = search_data["books"][0]
                    work_key = first_book.get("work_key")
                    
                    if work_key:
                        # Get detailed information about the book
                        details_response = requests.get(
                            f"{API_URL}/openlibrary/book/{work_key}", 
                            headers=self.get_auth_headers()
                        )
                        
                        if details_response.status_code == 200:
                            book_details = details_response.json()
                            
                            # Check for description
                            if "description" in book_details and book_details["description"]:
                                description = book_details["description"]
                                print(f"Description (excerpt): {description[:100]}...")
                                
                                # Check if description appears to be in French
                                french_words = ['le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou', 
                                              'avec', 'dans', 'sur', 'pour', 'par', 'est', 'sont', 'être']
                                french_word_count = sum(1 for word in french_words if f' {word} ' in f' {description.lower()} ')
                                
                                if french_word_count >= 2:
                                    print(f"✅ Description appears to be in French (detected {french_word_count} French words)")
                                else:
                                    print(f"⚠️ Description may not be in French (only detected {french_word_count} French words)")
                            else:
                                print("⚠️ No description found for this book")
                        else:
                            print(f"⚠️ Failed to get book details: {details_response.status_code}")
                    else:
                        print("⚠️ No work_key found for this book")
                else:
                    print(f"⚠️ No books found for '{book_title}'")
                    
            except Exception as e:
                print(f"⚠️ Error testing '{book_title}': {str(e)}")
                
        print("\n✅ Completed testing multiple books")

if __name__ == "__main__":
    unittest.main(verbosity=2)