"""
Service d'intégration AniList GraphQL
===================================

Intégration complète avec l'API AniList pour :
- Recherche de manga/séries
- Récupération métadonnées complètes  
- Mapping IDs et données enrichies
- Gestion cache et rate limiting
"""

import aiohttp
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class AniListService:
    """
    Service d'intégration avec l'API AniList GraphQL
    
    Fonctionnalités :
    - Recherche manga par nom
    - Récupération détails complets
    - Cache intelligent des requêtes
    - Rate limiting automatique
    - Gestion erreurs robuste
    """
    
    BASE_URL = "https://graphql.anilist.co"
    
    def __init__(self):
        self.session = None
        self.rate_limit_delay = 1.0  # Délai entre requêtes en secondes
        self.last_request_time = datetime.min
        self.cache = {}  # Cache simple en mémoire
        self.cache_duration = timedelta(hours=6)
    
    async def _ensure_session(self):
        """Initialise la session HTTP si nécessaire"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'User-Agent': 'BOOKTIME-Chapters/1.0'
                }
            )
    
    async def _rate_limit(self):
        """Applique le rate limiting"""
        now = datetime.now()
        elapsed = (now - self.last_request_time).total_seconds()
        
        if elapsed < self.rate_limit_delay:
            wait_time = self.rate_limit_delay - elapsed
            await asyncio.sleep(wait_time)
        
        self.last_request_time = datetime.now()
    
    async def _make_request(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Effectue une requête GraphQL vers AniList
        
        Args:
            query: Requête GraphQL
            variables: Variables pour la requête
            
        Returns:
            Réponse JSON de l'API
        """
        await self._ensure_session()
        await self._rate_limit()
        
        payload = {
            'query': query,
            'variables': variables or {}
        }
        
        try:
            async with self.session.post(self.BASE_URL, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'errors' in data:
                        logger.error(f"Erreurs GraphQL AniList: {data['errors']}")
                        return {}
                    
                    return data.get('data', {})
                
                elif response.status == 429:
                    # Rate limit dépassé
                    logger.warning("Rate limit AniList atteint, attente...")
                    await asyncio.sleep(60)  # Attendre 1 minute
                    return await self._make_request(query, variables)  # Retry
                
                else:
                    logger.error(f"Erreur HTTP AniList: {response.status}")
                    return {}
                    
        except aiohttp.ClientError as e:
            logger.error(f"Erreur connexion AniList: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Erreur inattendue AniList: {str(e)}")
            return {}
    
    async def search_manga(self, series_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Recherche un manga par nom sur AniList
        
        Args:
            series_name: Nom de la série à rechercher
            limit: Nombre maximum de résultats
            
        Returns:
            Liste des manga trouvés avec métadonnées
        """
        # ✅ CORRECTION : Protection contre series_name None
        if not series_name or not isinstance(series_name, str):
            logger.warning(f"Series name invalide: {series_name}")
            return []
        
        # Vérifier cache d'abord
        cache_key = f"search_{series_name.lower()}_{limit}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        query = """
        query ($search: String, $page: Int, $perPage: Int) {
          Page(page: $page, perPage: $perPage) {
            pageInfo {
              total
              currentPage
              lastPage
              hasNextPage
            }
            media(search: $search, type: MANGA, sort: POPULARITY_DESC) {
              id
              title {
                romaji
                english
                native
              }
              description(asHtml: false)
              chapters
              volumes
              status
              format
              countryOfOrigin
              startDate {
                year
                month
                day
              }
              endDate {
                year
                month
                day  
              }
              genres
              synonyms
              averageScore
              popularity
              staff {
                edges {
                  role
                  node {
                    name {
                      first
                      last
                      full
                    }
                  }
                }
              }
              coverImage {
                large
                medium
              }
              bannerImage
              siteUrl
              updatedAt
            }
          }
        }
        """
        
        variables = {
            'search': series_name,
            'page': 1,
            'perPage': limit
        }
        
        try:
            data = await self._make_request(query, variables)
            
            if not data or 'Page' not in data:
                logger.warning(f"Aucun résultat AniList pour '{series_name}'")
                return []
            
            media_list = data['Page'].get('media', [])
            
            # Formatage des résultats
            results = []
            for media in media_list:
                result = {
                    'id': media.get('id'),
                    'title': self._extract_best_title(media.get('title', {})),
                    'alternative_titles': self._extract_all_titles(media.get('title', {})),
                    'description': media.get('description', ''),
                    'chapters': media.get('chapters'),
                    'volumes': media.get('volumes'),
                    'status': media.get('status', '').lower(),
                    'format': media.get('format', '').lower(),
                    'country_of_origin': media.get('countryOfOrigin', 'JP'),
                    'start_date': self._format_date(media.get('startDate')),
                    'end_date': self._format_date(media.get('endDate')),
                    'genres': media.get('genres', []),
                    'synonyms': media.get('synonyms', []),
                    'score': media.get('averageScore'),
                    'popularity': media.get('popularity'),
                    'authors': self._extract_authors(media.get('staff', {})),
                    'cover_image': media.get('coverImage', {}).get('large'),
                    'banner_image': media.get('bannerImage'),
                    'anilist_url': media.get('siteUrl'),
                    'last_updated': media.get('updatedAt'),
                    'confidence': self._calculate_search_confidence(series_name, media)
                }
                results.append(result)
            
            # Tri par confiance puis popularité
            results.sort(key=lambda x: (x['confidence'], x['popularity'] or 0), reverse=True)
            
            # Mise en cache
            self._save_to_cache(cache_key, results)
            
            logger.info(f"AniList: {len(results)} résultats pour '{series_name}'")
            return results
            
        except Exception as e:
            logger.error(f"Erreur recherche AniList '{series_name}': {str(e)}")
            return []
    
    async def get_manga_by_id(self, anilist_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère les détails d'un manga par son ID AniList
        
        Args:
            anilist_id: ID AniList du manga
            
        Returns:
            Détails complets du manga ou None
        """
        # Cache
        cache_key = f"manga_id_{anilist_id}"
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result
        
        query = """
        query ($id: Int) {
          Media(id: $id, type: MANGA) {
            id
            title {
              romaji
              english
              native
            }
            description(asHtml: false)
            chapters
            volumes
            status
            format
            countryOfOrigin
            startDate {
              year
              month
              day
            }
            endDate {
              year
              month
              day
            }
            genres
            synonyms
            averageScore
            popularity
            favourites
            staff {
              edges {
                role
                node {
                  name {
                    first
                    last
                    full
                  }
                }
              }
            }
            characters {
              edges {
                role
                node {
                  name {
                    first
                    last
                    full
                  }
                }
              }
            }
            relations {
              edges {
                relationType
                node {
                  id
                  title {
                    romaji
                    english
                  }
                  format
                  status
                }
              }
            }
            coverImage {
              extraLarge
              large
              medium
            }
            bannerImage
            siteUrl
            updatedAt
            tags {
              name
              description
              rank
            }
          }
        }
        """
        
        variables = {'id': anilist_id}
        
        try:
            data = await self._make_request(query, variables)
            
            if not data or 'Media' not in data:
                logger.warning(f"Manga AniList ID {anilist_id} non trouvé")
                return None
            
            media = data['Media']
            
            result = {
                'id': media.get('id'),
                'title': self._extract_best_title(media.get('title', {})),
                'alternative_titles': self._extract_all_titles(media.get('title', {})),
                'description': media.get('description', ''),
                'chapters': media.get('chapters'),
                'volumes': media.get('volumes'),
                'status': media.get('status', '').lower(),
                'format': media.get('format', '').lower(),
                'country_of_origin': media.get('countryOfOrigin', 'JP'),
                'start_date': self._format_date(media.get('startDate')),
                'end_date': self._format_date(media.get('endDate')),
                'genres': media.get('genres', []),
                'synonyms': media.get('synonyms', []),
                'score': media.get('averageScore'),
                'popularity': media.get('popularity'),
                'favourites': media.get('favourites'),
                'authors': self._extract_authors(media.get('staff', {})),
                'characters': self._extract_characters(media.get('characters', {})),
                'relations': self._extract_relations(media.get('relations', {})),
                'cover_image': media.get('coverImage', {}).get('extraLarge'),
                'banner_image': media.get('bannerImage'),
                'anilist_url': media.get('siteUrl'),
                'last_updated': media.get('updatedAt'),
                'tags': self._extract_tags(media.get('tags', []))
            }
            
            # Cache avec durée plus longue pour les détails complets
            self._save_to_cache(cache_key, result, duration=timedelta(hours=12))
            
            logger.info(f"AniList: Détails récupérés pour ID {anilist_id}")
            return result
            
        except Exception as e:
            logger.error(f"Erreur récupération manga ID {anilist_id}: {str(e)}")
            return None
    
    async def health_check(self) -> bool:
        """
        Vérifie la connectivité avec l'API AniList
        
        Returns:
            True si l'API est accessible
        """
        simple_query = """
        query {
          Media(id: 30013, type: MANGA) {
            id
            title {
              romaji
            }
          }
        }
        """
        
        try:
            data = await self._make_request(simple_query)
            return bool(data and 'Media' in data)
        except Exception:
            return False
    
    # Méthodes utilitaires privées
    
    def _extract_best_title(self, title_obj: Dict[str, Any]) -> str:
        """Extrait le meilleur titre disponible"""
        if not title_obj:
            return ""
        
        # Priorité : english > romaji > native
        return (title_obj.get('english') or 
                title_obj.get('romaji') or 
                title_obj.get('native') or 
                "")
    
    def _extract_all_titles(self, title_obj: Dict[str, Any]) -> List[str]:
        """Extrait tous les titres disponibles"""
        if not title_obj:
            return []
        
        titles = []
        for key in ['english', 'romaji', 'native']:
            title = title_obj.get(key)
            if title and title not in titles:
                titles.append(title)
        
        return titles
    
    def _format_date(self, date_obj: Optional[Dict[str, Any]]) -> Optional[str]:
        """Formate une date AniList en ISO"""
        if not date_obj:
            return None
        
        year = date_obj.get('year')
        month = date_obj.get('month', 1)
        day = date_obj.get('day', 1)
        
        if year:
            try:
                date = datetime(year, month, day)
                return date.isoformat().split('T')[0]
            except ValueError:
                return f"{year}-01-01"
        
        return None
    
    def _extract_authors(self, staff_obj: Dict[str, Any]) -> List[str]:
        """Extrait la liste des auteurs"""
        authors = []
        
        edges = staff_obj.get('edges', [])
        for edge in edges:
            role = edge.get('role', '').lower()
            if any(keyword in role for keyword in ['story', 'art', 'original creator']):
                node = edge.get('node', {})
                name_obj = node.get('name', {})
                name = name_obj.get('full') or f"{name_obj.get('first', '')} {name_obj.get('last', '')}".strip()
                if name and name not in authors:
                    authors.append(name)
        
        return authors
    
    def _extract_characters(self, characters_obj: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrait la liste des personnages principaux"""
        characters = []
        
        edges = characters_obj.get('edges', [])[:5]  # Limiter aux 5 principaux
        for edge in edges:
            role = edge.get('role', '')
            node = edge.get('node', {})
            name_obj = node.get('name', {})
            name = name_obj.get('full') or f"{name_obj.get('first', '')} {name_obj.get('last', '')}".strip()
            
            if name:
                characters.append({
                    'name': name,
                    'role': role
                })
        
        return characters
    
    def _extract_relations(self, relations_obj: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrait les œuvres liées"""
        relations = []
        
        edges = relations_obj.get('edges', [])
        for edge in edges:
            relation_type = edge.get('relationType', '')
            node = edge.get('node', {})
            
            if node:
                title_obj = node.get('title', {})
                title = self._extract_best_title(title_obj)
                
                relations.append({
                    'id': node.get('id'),
                    'title': title,
                    'relation_type': relation_type,
                    'format': node.get('format', ''),
                    'status': node.get('status', '')
                })
        
        return relations
    
    def _extract_tags(self, tags_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extrait et filtre les tags pertinents"""
        relevant_tags = []
        
        for tag in tags_list[:10]:  # Top 10 tags
            if tag.get('rank', 0) >= 60:  # Seulement tags populaires
                relevant_tags.append({
                    'name': tag.get('name', ''),
                    'description': tag.get('description', ''),
                    'rank': tag.get('rank', 0)
                })
        
        return relevant_tags
    
    def _calculate_search_confidence(self, query: str, media: Dict[str, Any]) -> float:
        """Calcule un score de confiance pour un résultat de recherche"""
        if not media:
            return 0.0
        
        query_lower = query.lower().strip()
        
        # Vérifier correspondance exacte
        title_obj = media.get('title', {})
        titles = [
            title_obj.get('english', '').lower(),
            title_obj.get('romaji', '').lower(),
            title_obj.get('native', '').lower()
        ]
        
        # Correspondance exacte
        if query_lower in [t.strip() for t in titles if t]:
            return 1.0
        
        # Correspondance partielle
        for title in titles:
            if title and (query_lower in title or title in query_lower):
                return 0.9
        
        # Synonymes
        synonyms = media.get('synonyms', [])
        for synonym in synonyms:
            if synonym and query_lower in synonym.lower():
                return 0.8
        
        # Score basé sur popularité si pas de correspondance claire
        popularity = media.get('popularity', 0)
        if popularity > 10000:
            return 0.6
        elif popularity > 1000:
            return 0.4
        
        return 0.2
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Récupère une valeur du cache"""
        if key in self.cache:
            cached_data, timestamp = self.cache[key]
            if datetime.now() - timestamp < self.cache_duration:
                return cached_data
            else:
                del self.cache[key]
        return None
    
    def _save_to_cache(self, key: str, value: Any, duration: timedelta = None) -> None:
        """Sauvegarde une valeur dans le cache"""
        if duration is None:
            duration = self.cache_duration
        
        self.cache[key] = (value, datetime.now())
        
        # Nettoyage périodique du cache (basique)
        if len(self.cache) > 1000:
            # Supprimer les plus anciennes entrées
            sorted_items = sorted(self.cache.items(), key=lambda x: x[1][1])
            for old_key, _ in sorted_items[:100]:
                del self.cache[old_key]
    
    async def close(self):
        """Ferme la session HTTP"""
        if self.session:
            await self.session.close()
            self.session = None