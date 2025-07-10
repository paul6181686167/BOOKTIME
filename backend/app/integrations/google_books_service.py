"""
PHASE 3.5 - Service Google Books Integration
Service pour intégration avec Google Books API
"""
import asyncio
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class GoogleBooksService:
    """Service d'intégration avec Google Books API"""
    
    def __init__(self):
        self.base_url = "https://www.googleapis.com/books/v1"
        self.session = None
        
    async def get_session(self):
        """Obtenir une session HTTP"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def search_books(self, query: str, max_results: int = 20) -> List[Dict]:
        """Rechercher des livres sur Google Books"""
        try:
            session = await self.get_session()
            
            params = {
                'q': query,
                'maxResults': min(max_results, 40),
                'printType': 'books',
                'langRestrict': 'fr'
            }
            
            async with session.get(f"{self.base_url}/volumes", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    books = []
                    
                    for item in data.get('items', []):
                        book = await self._parse_google_book(item)
                        if book:
                            books.append(book)
                    
                    logger.info(f"Found {len(books)} books from Google Books for query: {query}")
                    return books
                else:
                    logger.error(f"Google Books API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error searching Google Books: {str(e)}")
            return []
    
    async def get_book_details(self, volume_id: str) -> Optional[Dict]:
        """Récupérer les détails d'un livre par son ID Google Books"""
        try:
            session = await self.get_session()
            
            async with session.get(f"{self.base_url}/volumes/{volume_id}") as response:
                if response.status == 200:
                    data = await response.json()
                    return await self._parse_google_book(data)
                else:
                    logger.error(f"Google Books API error for volume {volume_id}: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting book details from Google Books: {str(e)}")
            return None
    
    async def _parse_google_book(self, item: Dict) -> Optional[Dict]:
        """Parse un livre Google Books au format BookTime"""
        try:
            volume_info = item.get('volumeInfo', {})
            
            # Informations de base
            title = volume_info.get('title', '')
            authors = volume_info.get('authors', [])
            author = ', '.join(authors) if authors else ''
            
            # Description
            description = volume_info.get('description', '')
            if len(description) > 1000:
                description = description[:1000] + '...'
            
            # Catégories
            categories = volume_info.get('categories', [])
            category = self._determine_category_from_google(categories)
            
            # Images
            image_links = volume_info.get('imageLinks', {})
            cover_url = image_links.get('thumbnail', '').replace('http://', 'https://') if image_links else ''
            
            # Identifiants
            industry_identifiers = volume_info.get('industryIdentifiers', [])
            isbn = ''
            isbn13 = ''
            
            for identifier in industry_identifiers:
                if identifier.get('type') == 'ISBN_10':
                    isbn = identifier.get('identifier', '')
                elif identifier.get('type') == 'ISBN_13':
                    isbn13 = identifier.get('identifier', '')
            
            book = {
                'title': title,
                'author': author,
                'category': category,
                'description': description,
                'cover_url': cover_url,
                'isbn': isbn,
                'isbn13': isbn13,
                'publication_year': self._extract_year(volume_info.get('publishedDate', '')),
                'publisher': volume_info.get('publisher', ''),
                'total_pages': volume_info.get('pageCount', 0),
                'language': volume_info.get('language', 'fr'),
                'source': 'google_books',
                'google_books_id': item.get('id', ''),
                'metadata': {
                    'google_books_id': item.get('id', ''),
                    'categories': categories,
                    'published_date': volume_info.get('publishedDate', ''),
                    'subtitle': volume_info.get('subtitle', ''),
                    'average_rating': volume_info.get('averageRating', 0),
                    'ratings_count': volume_info.get('ratingsCount', 0),
                    'maturity_rating': volume_info.get('maturityRating', ''),
                    'preview_link': volume_info.get('previewLink', ''),
                    'info_link': volume_info.get('infoLink', '')
                }
            }
            
            return book
            
        except Exception as e:
            logger.error(f"Error parsing Google Book: {str(e)}")
            return None
    
    def _determine_category_from_google(self, categories: List[str]) -> str:
        """Détermine la catégorie à partir des catégories Google Books"""
        if not categories:
            return 'roman'
        
        category_text = ' '.join(categories).lower()
        
        # BD/Comics
        if any(keyword in category_text for keyword in ['comic', 'graphic', 'bande', 'dessinée']):
            return 'bd'
        
        # Manga
        if any(keyword in category_text for keyword in ['manga', 'anime', 'japanese']):
            return 'manga'
        
        # Roman par défaut
        return 'roman'
    
    def _extract_year(self, date_string: str) -> int:
        """Extrait l'année d'une date"""
        try:
            if date_string:
                # Format YYYY-MM-DD ou YYYY
                return int(date_string.split('-')[0])
            return 0
        except:
            return 0
    
    async def close(self):
        """Fermer la session HTTP"""
        if self.session:
            await self.session.close()
            self.session = None

# Instance globale
google_books_service = GoogleBooksService()