"""
PHASE 3.5 - Service Goodreads Integration
Service pour intégration avec Goodreads et synchronisation
"""
import asyncio
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class GoodreadsService:
    """Service d'intégration avec Goodreads"""
    
    def __init__(self):
        self.base_url = "https://www.goodreads.com"
        self.session = None
        
    async def get_session(self):
        """Obtenir une session HTTP"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def parse_goodreads_export(self, csv_content: str) -> List[Dict]:
        """Parse un export CSV de Goodreads"""
        try:
            import csv
            import io
            
            books = []
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            
            for row in csv_reader:
                book = {
                    'title': row.get('Title', ''),
                    'author': row.get('Author', ''),
                    'isbn': row.get('ISBN', ''),
                    'isbn13': row.get('ISBN13', ''),
                    'rating': int(row.get('My Rating', 0)) if row.get('My Rating') else 0,
                    'date_read': row.get('Date Read', ''),
                    'date_added': row.get('Date Added', ''),
                    'bookshelves': row.get('Bookshelves', ''),
                    'review': row.get('My Review', ''),
                    'pages': int(row.get('Number of Pages', 0)) if row.get('Number of Pages') else 0,
                    'year_published': int(row.get('Year Published', 0)) if row.get('Year Published') else 0,
                    'original_publication_year': int(row.get('Original Publication Year', 0)) if row.get('Original Publication Year', 0) else 0,
                    'goodreads_book_id': row.get('Book Id', ''),
                    'publisher': row.get('Publisher', '')
                }
                books.append(book)
            
            logger.info(f"Parsed {len(books)} books from Goodreads export")
            return books
            
        except Exception as e:
            logger.error(f"Error parsing Goodreads export: {str(e)}")
            return []
    
    async def convert_to_booktime_format(self, goodreads_books: List[Dict]) -> List[Dict]:
        """Convertit les livres Goodreads au format BookTime"""
        try:
            booktime_books = []
            
            for book in goodreads_books:
                # Déterminer la catégorie (approximation)
                category = self._determine_category(book)
                
                # Convertir le statut
                status = self._convert_status(book)
                
                booktime_book = {
                    'title': book.get('title', ''),
                    'author': book.get('author', ''),
                    'category': category,
                    'total_pages': book.get('pages', 0),
                    'rating': book.get('rating', 0),
                    'review': book.get('review', ''),
                    'isbn': book.get('isbn', ''),
                    'publication_year': book.get('year_published', 0),
                    'publisher': book.get('publisher', ''),
                    'status': status,
                    'source': 'goodreads_import',
                    'metadata': {
                        'goodreads_id': book.get('goodreads_book_id', ''),
                        'isbn13': book.get('isbn13', ''),
                        'bookshelves': book.get('bookshelves', ''),
                        'original_publication_year': book.get('original_publication_year', 0),
                        'date_read': book.get('date_read', ''),
                        'date_added': book.get('date_added', '')
                    }
                }
                
                booktime_books.append(booktime_book)
            
            logger.info(f"Converted {len(booktime_books)} books to BookTime format")
            return booktime_books
            
        except Exception as e:
            logger.error(f"Error converting to BookTime format: {str(e)}")
            return []
    
    def _determine_category(self, book: Dict) -> str:
        """Détermine la catégorie d'un livre"""
        bookshelves = book.get('bookshelves', '').lower()
        title = book.get('title', '').lower()
        
        # Indices pour BD/Comics
        if any(keyword in bookshelves for keyword in ['comic', 'graphic', 'bd', 'bande-dessinée']):
            return 'bd'
        
        # Indices pour Manga
        if any(keyword in bookshelves for keyword in ['manga', 'anime', 'japanese']):
            return 'manga'
        
        # Par défaut roman
        return 'roman'
    
    def _convert_status(self, book: Dict) -> str:
        """Convertit le statut Goodreads vers BookTime"""
        date_read = book.get('date_read', '')
        rating = book.get('rating', 0)
        
        if date_read and date_read.strip():
            return 'completed'
        elif rating > 0:
            return 'completed'
        else:
            return 'to_read'
    
    async def close(self):
        """Fermer la session HTTP"""
        if self.session:
            await self.session.close()
            self.session = None

# Instance globale
goodreads_service = GoodreadsService()