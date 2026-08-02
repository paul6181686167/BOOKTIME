"""
PHASE 3.1 - Service Open Library étendu pour les recommandations
Extension du service existant avec méthodes spécialisées
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiohttp
import asyncio
from typing import List, Dict, Optional
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class OpenLibraryService:
    """Service étendu pour l'API Open Library"""
    
    def __init__(self):
        self.base_url = "https://openlibrary.org"
        self.session = None
        self.timeout = 10
    
    async def _get_session(self):
        """Obtient une session HTTP réutilisable"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self.session
    
    async def search_books_by_author(self, author: str, limit: int = 10) -> List[Dict]:
        """
        Recherche des livres par auteur
        
        Args:
            author: Nom de l'auteur
            limit: Nombre maximum de résultats
            
        Returns:
            Liste des livres trouvés
        """
        try:
            session = await self._get_session()
            
            # Recherche par auteur
            url = f"{self.base_url}/search.json"
            params = {
                'author': author,
                'limit': limit,
                'fields': 'title,author_name,cover_i,first_publish_year,key,subject'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    books = []
                    
                    for doc in data.get('docs', []):
                        book = {
                            'title': doc.get('title', ''),
                            'author': ', '.join(doc.get('author_name', [])),
                            'cover_url': self._get_cover_url(doc.get('cover_i')),
                            'publication_year': doc.get('first_publish_year'),
                            'ol_key': doc.get('key', ''),
                            'category': self._determine_category(doc.get('subject', [])),
                            'subjects': doc.get('subject', [])[:5]  # Top 5 sujets
                        }
                        books.append(book)
                    
                    return books
                else:
                    logger.error(f"Erreur API Open Library: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Erreur recherche par auteur: {str(e)}")
            return []
    
    async def search_popular_books(self, category: str, limit: int = 10) -> List[Dict]:
        """
        Recherche des livres populaires par catégorie
        
        Args:
            category: Catégorie (roman, bd, manga)
            limit: Nombre maximum de résultats
            
        Returns:
            Liste des livres populaires
        """
        try:
            session = await self._get_session()
            
            # Mapping des catégories vers les sujets Open Library
            category_mapping = {
                'roman': ['fiction', 'literature', 'novel'],
                'bd': ['comics', 'graphic novels', 'bande dessinée'],
                'manga': ['manga', 'japanese comics', 'anime']
            }
            
            subjects = category_mapping.get(category, ['fiction'])
            
            url = f"{self.base_url}/search.json"
            params = {
                'subject': subjects[0],  # Prendre le premier sujet
                'limit': limit,
                'sort': 'rating desc',  # Trier par note
                'fields': 'title,author_name,cover_i,first_publish_year,key,subject,ratings_average'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    books = []
                    
                    for doc in data.get('docs', []):
                        book = {
                            'title': doc.get('title', ''),
                            'author': ', '.join(doc.get('author_name', [])),
                            'cover_url': self._get_cover_url(doc.get('cover_i')),
                            'publication_year': doc.get('first_publish_year'),
                            'ol_key': doc.get('key', ''),
                            'category': category,
                            'rating': doc.get('ratings_average', 0),
                            'subjects': doc.get('subject', [])[:5]
                        }
                        books.append(book)
                    
                    return books
                else:
                    logger.error(f"Erreur API Open Library: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Erreur recherche populaire: {str(e)}")
            return []
    
    async def search_series(self, series_name: str, limit: int = 10) -> List[Dict]:
        """
        Recherche des livres d'une série
        
        Args:
            series_name: Nom de la série
            limit: Nombre maximum de résultats
            
        Returns:
            Liste des livres de la série
        """
        try:
            session = await self._get_session()
            
            url = f"{self.base_url}/search.json"
            params = {
                'q': f'title:"{series_name}"',
                'limit': limit,
                'fields': 'title,author_name,cover_i,first_publish_year,key,subject'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    books = []
                    
                    for doc in data.get('docs', []):
                        book = {
                            'title': doc.get('title', ''),
                            'author': ', '.join(doc.get('author_name', [])),
                            'cover_url': self._get_cover_url(doc.get('cover_i')),
                            'publication_year': doc.get('first_publish_year'),
                            'ol_key': doc.get('key', ''),
                            'category': self._determine_category(doc.get('subject', [])),
                            'series_name': series_name
                        }
                        books.append(book)
                    
                    return books
                else:
                    logger.error(f"Erreur API Open Library: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Erreur recherche série: {str(e)}")
            return []
    
    async def get_book_details(self, ol_key: str) -> Optional[Dict]:
        """
        Récupère les détails d'un livre par sa clé Open Library
        
        Args:
            ol_key: Clé Open Library du livre
            
        Returns:
            Détails du livre ou None
        """
        try:
            session = await self._get_session()
            
            url = f"{self.base_url}{ol_key}.json"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return {
                        'title': data.get('title', ''),
                        'description': self._extract_description(data.get('description')),
                        'publication_year': self._extract_year(data.get('first_publish_date')),
                        'isbn': self._extract_isbn(data.get('isbn_13', [])),
                        'subjects': data.get('subjects', [])[:10],
                        'language': data.get('languages', []),
                        'page_count': data.get('number_of_pages')
                    }
                else:
                    logger.error(f"Erreur récupération détails: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Erreur détails livre: {str(e)}")
            return None
    
    async def get_popular_books(self, limit: int = 20) -> List[Dict]:
        """
        Récupère les livres populaires généraux
        
        Args:
            limit: Nombre maximum de résultats
            
        Returns:
            Liste des livres populaires
        """
        try:
            session = await self._get_session()
            
            url = f"{self.base_url}/search.json"
            params = {
                'q': 'fiction',
                'limit': limit,
                'sort': 'rating desc',
                'fields': 'title,author_name,cover_i,first_publish_year,key,subject,ratings_average'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    books = []
                    
                    for doc in data.get('docs', []):
                        book = {
                            'title': doc.get('title', ''),
                            'author': ', '.join(doc.get('author_name', [])),
                            'cover_url': self._get_cover_url(doc.get('cover_i')),
                            'publication_year': doc.get('first_publish_year'),
                            'ol_key': doc.get('key', ''),
                            'category': self._determine_category(doc.get('subject', [])),
                            'rating': doc.get('ratings_average', 0),
                            'subjects': doc.get('subject', [])[:5]
                        }
                        books.append(book)
                    
                    return books
                else:
                    logger.error(f"Erreur API Open Library: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Erreur livres populaires: {str(e)}")
            return []
    
    def _get_cover_url(self, cover_id: Optional[int]) -> Optional[str]:
        """Génère l'URL de la couverture"""
        if cover_id:
            return f"https://covers.openlibrary.org/b/id/{cover_id}-M.jpg"
        return None
    
    def _determine_category(self, subjects: List[str]) -> str:
        """Détermine la catégorie basée sur les sujets"""
        subjects_lower = [s.lower() for s in subjects]
        
        manga_keywords = ['manga', 'japanese comics', 'anime']
        bd_keywords = ['comics', 'graphic novels', 'bande dessinée', 'comic']
        
        for keyword in manga_keywords:
            if any(keyword in subject for subject in subjects_lower):
                return 'manga'
        
        for keyword in bd_keywords:
            if any(keyword in subject for subject in subjects_lower):
                return 'bd'
        
        return 'roman'  # Par défaut
    
    def _extract_description(self, description) -> str:
        """Extrait la description du livre"""
        if isinstance(description, dict):
            return description.get('value', '')
        elif isinstance(description, str):
            return description
        return ''
    
    def _extract_year(self, publish_date) -> Optional[int]:
        """Extrait l'année de publication"""
        if isinstance(publish_date, str):
            try:
                return int(publish_date.split('-')[0])
            except (ValueError, IndexError):
                return None
        return None
    
    def _extract_isbn(self, isbn_list: List[str]) -> Optional[str]:
        """Extrait le premier ISBN"""
        return isbn_list[0] if isbn_list else None

    async def search_similar_books(
        self, title: str, author: str = "", limit: int = 8
    ) -> List[Dict]:
        """
        Trouve des livres similaires à un titre bien noté via les sujets Open Library.
        """
        if not title or not title.strip():
            return []

        try:
            session = await self._get_session()
            url = f"{self.base_url}/search.json"
            seed_title = title.strip()
            seed_norm = seed_title.lower()[:50]

            # 1) Récupérer les sujets du livre seed
            seed_params = {
                "q": seed_title[:80],
                "limit": 5,
                "fields": "title,author_name,cover_i,first_publish_year,key,subject,ratings_average",
            }
            if author:
                seed_params["author"] = author.split(",")[0].strip()

            subjects: List[str] = []
            async with session.get(url, params=seed_params) as response:
                if response.status == 200:
                    data = await response.json()
                    preferred_kw = (
                        "fiction", "novel", "literature", "fantasy", "mystery",
                        "thriller", "romance", "science fiction", "horror",
                        "historical", "adventure", "young adult", "crime",
                        "detective", "manga", "comics", "bande", "polar",
                    )
                    for doc in data.get("docs", []):
                        doc_subjects = doc.get("subject") or []
                        preferred = [
                            s for s in doc_subjects
                            if any(k in s.lower() for k in preferred_kw) and 3 < len(s) < 50
                        ]
                        if preferred:
                            subjects = preferred[:5]
                            break
                        fallback = [s for s in doc_subjects if 3 < len(s) < 40][:5]
                        if fallback:
                            subjects = fallback
                            break

            books: List[Dict] = []
            seen_keys = set()

            def _append_doc(doc: Dict) -> bool:
                t = (doc.get("title") or "").strip()
                if not t:
                    return False
                t_norm = t.lower()
                if seed_norm and (seed_norm in t_norm or t_norm[:40] in seed_norm):
                    return False
                key = doc.get("key") or f"{t}|{','.join(doc.get('author_name') or [])}"
                if key in seen_keys:
                    return False
                seen_keys.add(key)
                books.append({
                    "title": t,
                    "author": ", ".join(doc.get("author_name") or []),
                    "cover_url": self._get_cover_url(doc.get("cover_i")),
                    "publication_year": doc.get("first_publish_year"),
                    "ol_key": doc.get("key", ""),
                    "category": self._determine_category(doc.get("subject") or []),
                    "rating": doc.get("ratings_average", 0),
                    "subjects": (doc.get("subject") or [])[:5],
                })
                return True

            # 2) Recherche par sujets
            for subject in subjects[:3]:
                if len(books) >= limit:
                    break
                params = {
                    "subject": subject,
                    "limit": limit + 8,
                    "sort": "rating desc",
                    "fields": "title,author_name,cover_i,first_publish_year,key,subject,ratings_average",
                }
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        continue
                    data = await response.json()
                    for doc in data.get("docs", []):
                        _append_doc(doc)
                        if len(books) >= limit:
                            break

            # 3) Repli : mots significatifs du titre
            if len(books) < limit:
                words = [w for w in seed_title.replace(":", " ").split() if len(w) > 3][:4]
                if words:
                    params = {
                        "q": " ".join(words),
                        "limit": limit + 8,
                        "sort": "rating desc",
                        "fields": "title,author_name,cover_i,first_publish_year,key,subject,ratings_average",
                    }
                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            for doc in data.get("docs", []):
                                _append_doc(doc)
                                if len(books) >= limit:
                                    break

            return books[:limit]

        except Exception as e:
            logger.error(f"Erreur recherche similaires pour « {title} »: {str(e)}")
            return []
    
    async def close(self):
        """Ferme la session HTTP"""
        if self.session:
            await self.session.close()