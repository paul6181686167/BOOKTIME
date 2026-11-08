"""
Service Wikidata pour requêtes SPARQL
Gestion des requêtes, cache et traitement des données
"""

import aiohttp
import asyncio
import time
import json
from typing import Dict, List, Optional, Any
from urllib.parse import quote_plus
import logging
from datetime import datetime, timedelta

from .models import (
    WikidataAuthor, WikidataSeries, WikidataBook,
    WikidataAuthorResponse, WikidataSeriesResponse, WikidataSeriesSearchResponse
)
from .sparql_queries import (
    GET_AUTHOR_SERIES, GET_SERIES_BOOKS, GET_AUTHOR_INFO, 
    SEARCH_SERIES, GET_SERIES_INFO, SEARCH_AUTHOR_EXACT,
    GET_POPULAR_SERIES, TEST_QUERY, GET_AUTHOR_INDIVIDUAL_BOOKS,
    GET_AUTHOR_ID, GET_AUTHOR_SERIES_BY_ID
)

logger = logging.getLogger(__name__)

class WikidataService:
    """Service pour les requêtes Wikidata SPARQL"""
    
    def __init__(self):
        self.sparql_endpoint = "https://query.wikidata.org/sparql"
        self.cache = {}
        self.cache_ttl = 3600 * 3  # 3 heures (était 1 heure)
        self.request_delay = 0.5  # Réduit à 0.5s (était 1.0s)
        self.last_request_time = 0
        
    async def _execute_sparql_query(self, query: str, timeout: int = 10) -> Optional[Dict]:
        """Exécute une requête SPARQL sur Wikidata"""
        try:
            # Respecter le délai entre requêtes
            now = time.time()
            time_since_last = now - self.last_request_time
            if time_since_last < self.request_delay:
                await asyncio.sleep(self.request_delay - time_since_last)
            
            self.last_request_time = time.time()
            
            headers = {
                'User-Agent': 'BOOKTIME/1.0 (https://example.com/contact) Python/aiohttp',
                'Accept': 'application/json'
            }
            
            params = {
                'query': query,
                'format': 'json'
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(self.sparql_endpoint, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"✅ Requête SPARQL réussie: {len(data.get('results', {}).get('bindings', []))} résultats")
                        return data
                    else:
                        logger.error(f"❌ Erreur SPARQL {response.status}: {await response.text()}")
                        return None
                        
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'exécution de la requête SPARQL: {str(e)}")
            return None
    
    def _get_cache_key(self, query_type: str, params: Dict) -> str:
        """Génère une clé de cache pour la requête"""
        return f"{query_type}:{json.dumps(params, sort_keys=True)}"
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Vérifie si l'entrée du cache est encore valide"""
        if not cache_entry:
            return False
        
        cached_time = cache_entry.get('timestamp', 0)
        return (time.time() - cached_time) < self.cache_ttl
    
    def _extract_wikidata_id(self, uri: str) -> str:
        """Extrait l'ID Wikidata depuis une URI"""
        if uri and uri.startswith('http://www.wikidata.org/entity/'):
            return uri.split('/')[-1]
        return ""
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """Parse une date Wikidata au format ISO"""
        if not date_str:
            return None
        
        try:
            # Format: +1965-07-31T00:00:00Z -> 1965-07-31
            if date_str.startswith('+'):
                date_str = date_str[1:]
            
            if 'T' in date_str:
                date_str = date_str.split('T')[0]
            
            return date_str
        except Exception:
            return None
    
    async def get_author_series(self, author_name: str) -> WikidataAuthorResponse:
        """Récupère les séries d'un auteur"""
        start_time = time.time()
        
        # Vérifier le cache
        cache_key = self._get_cache_key("author_series", {"author": author_name})
        cached_result = self.cache.get(cache_key)
        
        if cached_result and self._is_cache_valid(cached_result):
            logger.info(f"📋 Cache hit pour {author_name}")
            return cached_result['data']
        
        try:
            # Méthode hybride : essayer d'abord avec le nom, puis avec l'ID si échec
            # Préparer les variantes du nom (corriger le problème des espaces doubles)
            author_name_spaced = author_name.replace(".", ". ").replace("  ", " ")  # J.K. -> J. K. (éviter espaces doubles)
            author_name_nospace = author_name.replace(". ", ".").replace(" ", "")  # J. K. -> J.K. (sans espaces)
            
            # Préparer la requête avec les variantes
            query = GET_AUTHOR_SERIES % {
                "author_name": author_name,
                "author_name_spaced": author_name_spaced,
                "author_name_nospace": author_name_nospace
            }
            
            # Exécuter la requête
            result = await self._execute_sparql_query(query)
            
            # Si pas de résultats, essayer avec l'approche ID
            if not result or not result.get('results', {}).get('bindings', []):
                logger.info(f"🔄 Tentative avec recherche par ID pour {author_name}")
                
                # Étape 1: Trouver l'ID de l'auteur
                author_id_query = GET_AUTHOR_ID % {
                    "author_name": author_name,
                    "author_name_spaced": author_name_spaced,
                    "author_name_nospace": author_name_nospace
                }
                
                author_result = await self._execute_sparql_query(author_id_query)
                if author_result and author_result.get('results', {}).get('bindings', []):
                    author_binding = author_result['results']['bindings'][0]
                    author_uri = author_binding.get('author', {}).get('value', '')
                    author_id = self._extract_wikidata_id(author_uri)
                    
                    if author_id:
                        logger.info(f"✅ Auteur trouvé: {author_id}")
                        
                        # Étape 2: Trouver ses séries avec l'ID
                        series_query = GET_AUTHOR_SERIES_BY_ID % {"author_id": author_id}
                        result = await self._execute_sparql_query(series_query)
            
            if not result:
                return WikidataAuthorResponse(
                    found=False,
                    query_time=time.time() - start_time,
                    results_count=0
                )
            
            # Traiter les résultats
            bindings = result.get('results', {}).get('bindings', [])
            
            if not bindings:
                return WikidataAuthorResponse(
                    found=False,
                    query_time=time.time() - start_time,
                    results_count=0
                )
            
            # Construire les séries (dédupliquer par ID)
            series_dict = {}
            for binding in bindings:
                series_id = self._extract_wikidata_id(binding.get('series', {}).get('value', ''))
                series_name = binding.get('seriesLabel', {}).get('value', '')
                genre = binding.get('genreLabel', {}).get('value', '')
                start_date = self._parse_date(binding.get('startDate', {}).get('value'))
                end_date = self._parse_date(binding.get('endDate', {}).get('value'))
                description = binding.get('description', {}).get('value', '')
                
                if series_id and series_name:
                    # Si la série existe déjà, on conserve celle avec le plus d'informations
                    if series_id in series_dict:
                        existing = series_dict[series_id]
                        # Prioriser les descriptions plus longues et les genres plus spécifiques
                        if (description and len(description) > len(existing.description or '')) or \
                           (genre and genre != existing.genre and len(genre) > len(existing.genre or '')):
                            series_dict[series_id].description = description or existing.description
                            series_dict[series_id].genre = genre or existing.genre
                    else:
                        series = WikidataSeries(
                            id=series_id,
                            name=series_name,
                            author_id="",  # Sera rempli si nécessaire
                            author_name=author_name,
                            genre=genre,
                            start_date=start_date,
                            end_date=end_date,
                            status="terminée" if end_date else "en cours",
                            description=description
                        )
                        series_dict[series_id] = series
            
            # Convertir en liste
            series_list = list(series_dict.values())
            
            # Créer la réponse
            response = WikidataAuthorResponse(
                found=len(series_list) > 0,
                query_time=time.time() - start_time,
                results_count=len(series_list),
                series=series_list
            )
            
            # Mettre en cache
            self.cache[cache_key] = {
                'data': response,
                'timestamp': time.time()
            }
            
            logger.info(f"✅ Séries trouvées pour {author_name}: {len(series_list)}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des séries pour {author_name}: {str(e)}")
            return WikidataAuthorResponse(
                found=False,
                query_time=time.time() - start_time,
                results_count=0
            )
    
    async def get_series_books(self, series_id: str) -> WikidataSeriesResponse:
        """Récupère les livres d'une série"""
        start_time = time.time()
        
        # Vérifier le cache
        cache_key = self._get_cache_key("series_books", {"series_id": series_id})
        cached_result = self.cache.get(cache_key)
        
        if cached_result and self._is_cache_valid(cached_result):
            logger.info(f"📋 Cache hit pour série {series_id}")
            return cached_result['data']
        
        try:
            # Préparer la requête
            query = GET_SERIES_BOOKS % {"series_id": series_id}
            
            # Exécuter la requête
            result = await self._execute_sparql_query(query)
            
            if not result:
                return WikidataSeriesResponse(
                    found=False,
                    query_time=time.time() - start_time,
                    results_count=0
                )
            
            # Traiter les résultats
            bindings = result.get('results', {}).get('bindings', [])
            
            # Construire les livres
            books_list = []
            for binding in bindings:
                book_id = self._extract_wikidata_id(binding.get('book', {}).get('value', ''))
                title = binding.get('bookLabel', {}).get('value', '')
                volume_number = binding.get('volumeNumber', {}).get('value')
                pub_date = self._parse_date(binding.get('pubDate', {}).get('value'))
                genre = binding.get('genreLabel', {}).get('value', '')
                pages = binding.get('pages', {}).get('value')
                isbn = binding.get('isbn', {}).get('value', '')
                publisher = binding.get('publisherLabel', {}).get('value', '')
                
                if book_id and title:
                    book = WikidataBook(
                        id=book_id,
                        title=title,
                        series_id=series_id,
                        volume_number=int(volume_number) if volume_number else None,
                        publication_date=pub_date,
                        genre=genre,
                        pages=int(pages) if pages else None,
                        isbn=isbn,
                        publisher=publisher
                    )
                    books_list.append(book)
            
            # Trier par numéro de volume
            books_list.sort(key=lambda x: x.volume_number or 0)
            
            # Créer la réponse
            response = WikidataSeriesResponse(
                found=len(books_list) > 0,
                query_time=time.time() - start_time,
                results_count=len(books_list),
                books=books_list
            )
            
            # Mettre en cache
            self.cache[cache_key] = {
                'data': response,
                'timestamp': time.time()
            }
            
            logger.info(f"✅ Livres trouvés pour série {series_id}: {len(books_list)}")
            return response
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des livres pour série {series_id}: {str(e)}")
            return WikidataSeriesResponse(
                found=False,
                query_time=time.time() - start_time,
                results_count=0
            )
    
    async def get_author_individual_books(self, author_name: str) -> List[WikidataBook]:
        """Récupère les livres individuels d'un auteur (pas dans une série)"""
        start_time = time.time()
        
        # Vérifier le cache
        cache_key = self._get_cache_key("author_individual_books", {"author_name": author_name})
        cached_result = self.cache.get(cache_key)
        
        if cached_result and self._is_cache_valid(cached_result):
            logger.info(f"📋 Cache hit pour livres individuels de {author_name}")
            return cached_result['data']
        
        try:
            # Préparer les variantes du nom (comme dans get_author_series)
            author_name_spaced = author_name.replace(".", ". ").replace("  ", " ")
            author_name_nospace = author_name.replace(". ", ".").replace(" ", "")
            
            # Préparer la requête avec les variantes
            query = GET_AUTHOR_INDIVIDUAL_BOOKS % {
                "author_name": author_name,
                "author_name_spaced": author_name_spaced,
                "author_name_nospace": author_name_nospace
            }
            
            # LOG TEMPORAIRE POUR DÉBOGUER
            logger.info(f"🔍 Requête SPARQL générée pour {author_name}:")
            logger.info(f"📝 Query: {query[:500]}...")
            
            # Exécuter la requête
            result = await self._execute_sparql_query(query)
            
            if not result:
                return []
            
            # Traiter les résultats
            bindings = result.get('results', {}).get('bindings', [])
            
            # Construire les livres
            books_list = []
            seen_titles = set()  # Pour éviter les doublons
            
            for binding in bindings:
                book_id = self._extract_wikidata_id(binding.get('book', {}).get('value', ''))
                title = binding.get('bookLabel', {}).get('value', '')
                pub_date = self._parse_date(binding.get('pubDate', {}).get('value'))
                genre = binding.get('genreLabel', {}).get('value', '')
                book_type = binding.get('typeLabel', {}).get('value', '')
                description = binding.get('description', {}).get('value', '')
                isbn = binding.get('isbn', {}).get('value', '')
                publisher = binding.get('publisherLabel', {}).get('value', '')
                
                # Éviter les doublons par titre
                if book_id and title and title not in seen_titles:
                    book = WikidataBook(
                        id=book_id,
                        title=title,
                        series_id=None,  # Livre individuel, pas de série
                        volume_number=None,
                        publication_date=pub_date,
                        genre=genre,
                        pages=None,
                        isbn=isbn,
                        publisher=publisher,
                        description=None,  # Retiré de la requête optimisée
                        book_type=book_type
                    )
                    books_list.append(book)
                    seen_titles.add(title)
            
            # Trier par date de publication (plus récent d'abord)
            books_list.sort(key=lambda x: x.publication_date or "0000", reverse=True)
            
            # Mettre en cache
            self.cache[cache_key] = {
                'data': books_list,
                'timestamp': time.time()
            }
            
            logger.info(f"✅ Livres individuels trouvés pour {author_name}: {len(books_list)}")
            return books_list
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des livres individuels pour {author_name}: {str(e)}")
            return []
    
    async def get_author_info(self, author_name: str) -> Optional[WikidataAuthor]:
        """Récupère les informations détaillées d'un auteur"""
        start_time = time.time()
        
        try:
            # Préparer la requête
            query = GET_AUTHOR_INFO % {"author_name": author_name}
            
            # Exécuter la requête
            result = await self._execute_sparql_query(query)
            
            if not result:
                return None
            
            # Traiter les résultats
            bindings = result.get('results', {}).get('bindings', [])
            
            if not bindings:
                return None
            
            # Prendre le premier résultat
            binding = bindings[0]
            
            author_id = self._extract_wikidata_id(binding.get('author', {}).get('value', ''))
            name = binding.get('authorLabel', {}).get('value', '')
            birth_date = self._parse_date(binding.get('birthDate', {}).get('value'))
            death_date = self._parse_date(binding.get('deathDate', {}).get('value'))
            nationality = binding.get('nationalityLabel', {}).get('value', '')
            
            # Collecter les occupations, genres et prix
            occupations = []
            genres = []
            awards = []
            
            for b in bindings:
                if b.get('occupationLabel', {}).get('value'):
                    occupations.append(b['occupationLabel']['value'])
                if b.get('genreLabel', {}).get('value'):
                    genres.append(b['genreLabel']['value'])
                if b.get('awardLabel', {}).get('value'):
                    awards.append(b['awardLabel']['value'])
            
            # Déduplication
            occupations = list(set(occupations))
            genres = list(set(genres))
            awards = list(set(awards))
            
            # Image et Wikipedia
            image_url = binding.get('image', {}).get('value', '')
            wikipedia_url = binding.get('wikipedia', {}).get('value', '')
            
            return WikidataAuthor(
                id=author_id,
                name=name,
                birth_date=birth_date,
                death_date=death_date,
                nationality=nationality,
                occupation=occupations,
                genres=genres,
                awards=awards,
                image_url=image_url,
                wikipedia_url=wikipedia_url
            )
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des informations pour {author_name}: {str(e)}")
            return None
    
    async def search_series(self, search_term: str, limit: int = 20) -> WikidataSeriesSearchResponse:
        """Recherche des séries par nom"""
        start_time = time.time()
        
        try:
            # Préparer la requête
            query = SEARCH_SERIES % {"search_term": search_term}
            
            # Exécuter la requête
            result = await self._execute_sparql_query(query)
            
            if not result:
                return WikidataSeriesSearchResponse(
                    found=False,
                    query_time=time.time() - start_time,
                    results_count=0,
                    search_term=search_term
                )
            
            # Traiter les résultats
            bindings = result.get('results', {}).get('bindings', [])
            
            # Construire les séries
            series_list = []
            for binding in bindings[:limit]:
                series_id = self._extract_wikidata_id(binding.get('series', {}).get('value', ''))
                series_name = binding.get('seriesLabel', {}).get('value', '')
                author_id = self._extract_wikidata_id(binding.get('author', {}).get('value', ''))
                author_name = binding.get('authorLabel', {}).get('value', '')
                genre = binding.get('genreLabel', {}).get('value', '')
                start_date = self._parse_date(binding.get('startDate', {}).get('value'))
                description = binding.get('description', {}).get('value', '')
                
                if series_id and series_name:
                    series = WikidataSeries(
                        id=series_id,
                        name=series_name,
                        author_id=author_id,
                        author_name=author_name,
                        genre=genre,
                        start_date=start_date,
                        description=description
                    )
                    series_list.append(series)
            
            return WikidataSeriesSearchResponse(
                found=len(series_list) > 0,
                query_time=time.time() - start_time,
                results_count=len(series_list),
                series=series_list,
                search_term=search_term
            )
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la recherche de séries '{search_term}': {str(e)}")
            return WikidataSeriesSearchResponse(
                found=False,
                query_time=time.time() - start_time,
                results_count=0,
                search_term=search_term
            )
    
    async def test_connection(self, test_author: str = "rowling") -> Dict[str, Any]:
        """Test de connexion et requête simple"""
        start_time = time.time()
        
        try:
            # Préparer la requête de test
            query = TEST_QUERY % {"test_author": test_author}
            
            # Exécuter la requête
            result = await self._execute_sparql_query(query)
            
            if not result:
                return {
                    "success": False,
                    "error": "Pas de réponse du serveur SPARQL",
                    "execution_time": time.time() - start_time
                }
            
            # Traiter les résultats
            bindings = result.get('results', {}).get('bindings', [])
            
            processed_results = []
            for binding in bindings:
                processed_results.append({
                    "series_id": self._extract_wikidata_id(binding.get('series', {}).get('value', '')),
                    "series_name": binding.get('seriesLabel', {}).get('value', ''),
                    "author_id": self._extract_wikidata_id(binding.get('author', {}).get('value', '')),
                    "author_name": binding.get('authorLabel', {}).get('value', '')
                })
            
            return {
                "success": True,
                "query": query,
                "results": bindings,
                "processed_results": processed_results,
                "execution_time": time.time() - start_time
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time
            }

# Instance globale du service
wikidata_service = WikidataService()