"""
🚀 Wikipedia Series Enrichment Service
Service d'enrichissement automatique des séries via Wikipedia
"""

import asyncio
import aiohttp
import re
from datetime import datetime
from typing import List, Dict, Optional
from app.database import db
import logging

logger = logging.getLogger(__name__)

class WikipediaSeriesService:
    """Service d'enrichissement automatique des séries"""
    
    def __init__(self):
        self.base_url = "https://en.wikipedia.org/api/rest_v1/page/summary/"
        self.known_series = {
            'Harry Potter', 'The Dark Tower', 'Discworld', 'Wheel of Time',
            'A Song of Ice and Fire', 'The Hunger Games', 'Percy Jackson',
            'The Mortal Instruments', 'Dune', 'Foundation', 'Earthsea',
            'The Chronicles of Narnia', 'His Dark Materials', 'The Dresden Files',
            'The Witcher', 'Mistborn', 'The Stormlight Archive', 'The Expanse',
            'The Southern Reach', 'The Kingkiller Chronicle', 'The First Law',
            'The Malazan Book of the Fallen', 'The Gentleman Bastard',
            'The Broken Empire', 'The Farseer Trilogy', 'The Culture',
            'Hyperion Cantos', 'The Imperial Radch', 'The Wayfarers',
            'The Expanse', 'The Locked Tomb', 'The Poppy War'
        }
    
    async def get_author_wikipedia_page(self, session: aiohttp.ClientSession, author_name: str) -> Optional[Dict]:
        """Récupère la page Wikipedia d'un auteur"""
        try:
            formatted_name = author_name.replace(' ', '_')
            url = f"{self.base_url}{formatted_name}"
            
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Page Wikipedia trouvée : {author_name}")
                    return data
                else:
                    logger.warning(f"❌ Pas de page Wikipedia : {author_name} ({response.status})")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Erreur Wikipedia {author_name}: {str(e)}")
            return None
    
    def extract_series_from_wikipedia(self, description: str, author_name: str) -> List[Dict]:
        """Extrait les séries depuis la description Wikipedia"""
        series_found = []
        
        # Patterns spécialisés pour différents types de séries
        improved_patterns = [
            # Séries explicites
            (r'(?:author|creator|writer) of (?:the )?([A-Z][a-zA-Z\s]+?) (?:series|saga|cycle)', 90),
            (r'(?:wrote|created|best known for) (?:the )?([A-Z][a-zA-Z\s]+?) (?:series|novels|books)', 85),
            (r'(?:the )?([A-Z][a-zA-Z\s]+?) (?:fantasy|science fiction|mystery|horror) series', 85),
            
            # Séries connues spécifiques
            (r'(Harry Potter)', 95),
            (r'(The Dark Tower)', 95),
            (r'(Discworld)', 95),
            (r'(Wheel of Time)', 95),
            (r'(A Song of Ice and Fire)', 95),
            (r'(The Hunger Games)', 95),
            (r'(Percy Jackson)', 95),
            (r'(The Mortal Instruments)', 95),
            (r'(Foundation)', 95),
            (r'(Dune)', 95),
            (r'(Earthsea)', 95),
            (r'(The Dresden Files)', 95),
            (r'(Mistborn)', 95),
            (r'(The Stormlight Archive)', 95),
            
            # Patterns pour volumes multiples
            (r'([A-Z][a-zA-Z\s]+?) (?:trilogy|tetralogy|pentalogy)', 80),
            (r'([A-Z][a-zA-Z\s]+?) (?:book series|novel series)', 80),
        ]
        
        for pattern, confidence in improved_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                series_name = match.strip()
                
                if self.is_valid_series_name(series_name):
                    series_info = {
                        'name': series_name,
                        'author': author_name,
                        'source': 'wikipedia_api',
                        'detected_at': datetime.now().isoformat(),
                        'confidence': confidence,
                        'validation_passed': True
                    }
                    
                    # Éviter les doublons
                    if not any(s['name'].lower() == series_name.lower() for s in series_found):
                        series_found.append(series_info)
                        logger.info(f"📚 Série détectée : {series_name} par {author_name} ({confidence}%)")
        
        return series_found
    
    def is_valid_series_name(self, name: str) -> bool:
        """Valide si le nom est une vraie série"""
        invalid_keywords = [
            'literature', 'fiction', 'books', 'novels', 'works', 'writing',
            'style', 'genre', 'career', 'life', 'biography', 'awards',
            'university', 'college', 'school', 'education', 'degree',
            'her', 'his', 'and', 'the author', 'bestselling', 'award',
            'children', 'young adult', 'dystopian', 'horror', 'fantasy',
            'science fiction', 'mystery', 'graphic', 'unfinished'
        ]
        
        name_lower = name.lower().strip()
        
        # Vérifications de base
        if len(name) < 3 or len(name) > 60:
            return False
            
        # Filtrage des mots-clés invalides
        if any(keyword in name_lower for keyword in invalid_keywords):
            return False
            
        # Doit contenir des lettres
        if not re.search(r'[a-zA-Z]', name):
            return False
            
        # Filtrage des fragments
        if name_lower.startswith(('a ', 'an ', 'the ', 'and ', 'her ', 'his ')):
            return False
            
        # Vérification séries connues
        if any(known.lower() in name_lower for known in self.known_series):
            return True
            
        # Doit ressembler à un titre
        if re.match(r'^[A-Z][a-zA-Z\s]+$', name):
            return True
            
        return False
    
    def get_existing_authors_from_db(self) -> List[str]:
        """Récupère les auteurs existants depuis la base de données"""
        try:
            # Agrégation pour obtenir les auteurs uniques
            pipeline = [
                {"$group": {"_id": "$author", "count": {"$sum": 1}}},
                {"$match": {"count": {"$gte": 1}}},  # Au moins 1 livre
                {"$sort": {"count": -1}},  # Tri par nombre de livres
                {"$limit": 50}  # Limite à 50 auteurs
            ]
            
            authors_cursor = db.books.aggregate(pipeline)
            authors = [doc["_id"] for doc in authors_cursor if doc["_id"]]
            
            logger.info(f"📚 {len(authors)} auteurs trouvés dans la base")
            return authors
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération auteurs : {str(e)}")
            return []
    
    async def enrich_series_for_author(self, session: aiohttp.ClientSession, author_name: str) -> List[Dict]:
        """Enrichit les séries pour un auteur"""
        logger.info(f"🚀 Enrichissement pour : {author_name}")
        
        # Récupération page Wikipedia
        wiki_page = await self.get_author_wikipedia_page(session, author_name)
        if not wiki_page:
            return []
        
        # Extraction des séries
        description = wiki_page.get('extract', '')
        if not description:
            logger.warning(f"❌ Pas de description pour : {author_name}")
            return []
        
        series_found = self.extract_series_from_wikipedia(description, author_name)
        logger.info(f"✅ {len(series_found)} séries trouvées pour {author_name}")
        
        return series_found
    
    def save_series_to_ultra_harvest(self, series_data: List[Dict]) -> Dict:
        """Sauvegarde les séries dans Ultra Harvest"""
        try:
            # Collection Ultra Harvest (on peut créer une collection dédiée)
            ultra_harvest_collection = db.ultra_harvest_wikipedia
            
            # Statistiques
            new_series = 0
            updated_series = 0
            
            for series in series_data:
                # Préparation document
                document = {
                    'name': series['name'],
                    'author': series['author'],
                    'source': 'wikipedia_enrichment',
                    'confidence': series['confidence'],
                    'detected_at': series['detected_at'],
                    'category': 'auto_detected',  # Catégorie par défaut
                    'status': 'active',
                    'enrichment_version': '2.0'
                }
                
                # Upsert (insert ou update)
                result = ultra_harvest_collection.replace_one(
                    {
                        'name': series['name'],
                        'author': series['author']
                    },
                    document,
                    upsert=True
                )
                
                if result.upserted_id:
                    new_series += 1
                else:
                    updated_series += 1
            
            logger.info(f"💾 Sauvegarde : {new_series} nouvelles, {updated_series} mises à jour")
            
            return {
                'new_series': new_series,
                'updated_series': updated_series,
                'total_processed': len(series_data)
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde Ultra Harvest : {str(e)}")
            return {
                'new_series': 0,
                'updated_series': 0,
                'total_processed': 0,
                'error': str(e)
            }
    
    async def run_enrichment_process(self, limit_authors: int = 50) -> Dict:
        """Lance le processus d'enrichissement complet"""
        logger.info(f"🚀 Démarrage enrichissement automatique (limite: {limit_authors})")
        
        # Récupération des auteurs existants
        existing_authors = self.get_existing_authors_from_db()
        if not existing_authors:
            logger.error("❌ Aucun auteur trouvé dans la base")
            return {
                'success': False,
                'error': 'No authors found in database'
            }
        
        # Limitation
        authors_to_process = existing_authors[:limit_authors]
        logger.info(f"📚 Traitement de {len(authors_to_process)} auteurs")
        
        # Enrichissement parallèle
        all_series = []
        
        async with aiohttp.ClientSession() as session:
            # Traitement avec semaphore pour limiter les requêtes
            semaphore = asyncio.Semaphore(3)  # Max 3 requêtes simultanées
            
            async def process_author_with_semaphore(author):
                async with semaphore:
                    return await self.enrich_series_for_author(session, author)
            
            # Exécution parallèle
            results = await asyncio.gather(
                *[process_author_with_semaphore(author) for author in authors_to_process],
                return_exceptions=True
            )
            
            # Agrégation des résultats
            for result in results:
                if isinstance(result, list):
                    all_series.extend(result)
        
        # Filtrage par confiance
        high_confidence_series = [s for s in all_series if s['confidence'] >= 85]
        
        # Sauvegarde dans Ultra Harvest
        save_result = self.save_series_to_ultra_harvest(high_confidence_series)
        
        # Statistiques finales
        final_stats = {
            'success': True,
            'authors_processed': len(authors_to_process),
            'total_series_detected': len(all_series),
            'high_confidence_series': len(high_confidence_series),
            'ultra_harvest_update': save_result,
            'enrichment_completed_at': datetime.now().isoformat(),
            'version': '2.0'
        }
        
        logger.info(f"🎯 Enrichissement terminé : {len(high_confidence_series)} séries haute confiance")
        
        return final_stats

# Instance globale du service
wikipedia_series_service = WikipediaSeriesService()