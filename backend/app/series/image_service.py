"""
Service d'enrichissement d'images pour les séries
Utilise Open Library API et vision_expert_agent pour obtenir des images de couverture
"""
import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Union
from urllib.parse import quote

logger = logging.getLogger(__name__)

class SeriesImageService:
    """Service pour enrichir les séries avec des images de couverture"""
    
    def __init__(self):
        self.session = None
        self.base_openlibrary_url = "https://openlibrary.org"
        self.base_covers_url = "https://covers.openlibrary.org/b"
        
    async def get_session(self):
        """Obtenir une session aiohttp réutilisable"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def close(self):
        """Fermer la session aiohttp"""
        if self.session:
            await self.session.close()
            self.session = None
    
    async def search_series_cover_openlibrary(self, series_name: str, author: str = None) -> Optional[str]:
        """
        Rechercher une image de couverture pour une série via Open Library
        
        Args:
            series_name: Nom de la série
            author: Auteur de la série (optionnel)
            
        Returns:
            URL de l'image de couverture ou None
        """
        try:
            session = await self.get_session()
            
            # Construire la requête de recherche
            search_query = series_name
            if author:
                search_query += f" {author}"
            
            # Rechercher dans Open Library
            search_url = f"{self.base_openlibrary_url}/search.json"
            params = {
                'q': search_query,
                'limit': 5,
                'fields': 'key,title,author_name,cover_i,first_publish_year'
            }
            
            async with session.get(search_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    docs = data.get('docs', [])
                    
                    # Chercher un livre avec une couverture
                    for doc in docs:
                        cover_id = doc.get('cover_i')
                        if cover_id:
                            # Construire l'URL de la couverture
                            cover_url = f"{self.base_covers_url}/id/{cover_id}-M.jpg"
                            
                            # Vérifier que l'image existe
                            if await self._verify_image_exists(cover_url):
                                logger.info(f"✅ Image trouvée pour '{series_name}': {cover_url}")
                                return cover_url
                    
                    logger.info(f"❌ Aucune image trouvée sur Open Library pour '{series_name}'")
                    return None
                else:
                    logger.warning(f"⚠️ Erreur Open Library search: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Erreur lors de la recherche d'image pour '{series_name}': {e}")
            return None
    
    async def _verify_image_exists(self, image_url: str) -> bool:
        """Vérifier qu'une image existe et est accessible"""
        try:
            session = await self.get_session()
            async with session.head(image_url) as response:
                return response.status == 200
        except:
            return False
    
    async def get_placeholder_image_from_vision_expert(self, series_name: str, category: str = None) -> Optional[str]:
        """
        Obtenir une image placeholder de qualité via vision_expert_agent
        
        Args:
            series_name: Nom de la série
            category: Catégorie (roman, bd, manga)
            
        Returns:
            URL de l'image ou None
        """
        try:
            # Déterminer le contexte selon la catégorie
            context_map = {
                'roman': 'book cover novel',
                'bd': 'comic book cover graphic novel',
                'manga': 'manga cover japanese comic',
                'default': 'book series cover'
            }
            
            context = context_map.get(category, context_map['default'])
            
            # Construire la requête pour vision_expert_agent
            search_keywords = f"{series_name}, {context}"
            problem_statement = f"Need a professional cover image for the series '{series_name}' in category '{category}'. The image will be used as a book series cover in a library management application."
            
            # Note: vision_expert_agent serait appelé ici
            # Pour l'instant, on retourne None et laisse le fallback sur le dégradé
            logger.info(f"📸 Vision expert agent requis pour '{series_name}' (catégorie: {category})")
            return None
            
        except Exception as e:
            logger.error(f"❌ Erreur vision expert pour '{series_name}': {e}")
            return None
    
    async def enrich_series_with_image(self, series_data: Dict) -> Dict:
        """
        Enrichir une série avec une image de couverture
        
        Args:
            series_data: Données de la série
            
        Returns:
            Données de la série enrichies avec cover_url
        """
        series_name = series_data.get('name', '')
        author = series_data.get('authors', [])
        author_name = author[0] if author and isinstance(author, list) else str(author) if author else None
        category = series_data.get('category', 'roman')
        
        if not series_name:
            return series_data
        
        # Étape 1: Chercher sur Open Library
        cover_url = await self.search_series_cover_openlibrary(series_name, author_name)
        
        # Étape 2: Si pas trouvé, utiliser vision expert (placeholder pour l'instant)
        if not cover_url:
            cover_url = await self.get_placeholder_image_from_vision_expert(series_name, category)
        
        # Ajouter l'URL de couverture si trouvée
        if cover_url:
            series_data['cover_url'] = cover_url
            logger.info(f"✅ Série '{series_name}' enrichie avec image: {cover_url}")
        else:
            logger.info(f"📷 Série '{series_name}' conserve le dégradé par défaut")
        
        return series_data
    
    async def batch_enrich_series(self, series_list: List[Dict], max_concurrent: int = 10) -> List[Dict]:
        """
        Enrichir une liste de séries avec des images en parallèle
        
        Args:
            series_list: Liste des séries à enrichir
            max_concurrent: Nombre maximum de requêtes simultanées
            
        Returns:
            Liste des séries enrichies
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def enrich_with_semaphore(series):
            async with semaphore:
                return await self.enrich_series_with_image(series)
        
        try:
            # Traiter en parallèle avec limite de concurrence
            enriched_series = await asyncio.gather(
                *[enrich_with_semaphore(series) for series in series_list],
                return_exceptions=True
            )
            
            # Filtrer les erreurs et retourner les résultats valides
            valid_results = []
            for i, result in enumerate(enriched_series):
                if isinstance(result, Exception):
                    logger.error(f"❌ Erreur enrichissement série {i}: {result}")
                    valid_results.append(series_list[i])  # Garder les données originales
                else:
                    valid_results.append(result)
            
            logger.info(f"✅ Enrichissement terminé: {len(valid_results)} séries traitées")
            return valid_results
            
        except Exception as e:
            logger.error(f"❌ Erreur batch enrichissement: {e}")
            return series_list  # Retourner les données originales en cas d'erreur
    
    async def enrich_series_database(self, database_path: str, output_path: str = None, sample_size: int = None):
        """
        Enrichir toute la base de données des séries avec des images
        
        Args:
            database_path: Chemin vers le fichier JSON de la base
            output_path: Chemin de sortie (optionnel)
            sample_size: Nombre de séries à traiter (None = toutes)
        """
        try:
            # Charger la base de données
            with open(database_path, 'r', encoding='utf-8') as f:
                series_database = json.load(f)
            
            logger.info(f"📚 Base chargée: {len(series_database)} séries")
            
            # Échantillonner si demandé
            series_to_process = series_database
            if sample_size and sample_size < len(series_database):
                series_to_process = series_database[:sample_size]
                logger.info(f"🎯 Traitement échantillon: {sample_size} séries")
            
            # Enrichir en parallèle
            enriched_series = await self.batch_enrich_series(series_to_process, max_concurrent=5)
            
            # Sauvegarder le résultat
            output_file = output_path or database_path.replace('.json', '_enriched.json')
            
            # Pour l'échantillon, on remplace seulement les séries traitées
            if sample_size:
                final_database = series_database.copy()
                final_database[:sample_size] = enriched_series
            else:
                final_database = enriched_series
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(final_database, f, ensure_ascii=False, indent=2)
            
            # Statistiques
            enriched_count = sum(1 for series in enriched_series if series.get('cover_url'))
            total_processed = len(enriched_series)
            
            logger.info(f"✅ Enrichissement terminé:")
            logger.info(f"   📊 {enriched_count}/{total_processed} séries avec images ({enriched_count/total_processed*100:.1f}%)")
            logger.info(f"   💾 Sauvegardé dans: {output_file}")
            
            return {
                'total_processed': total_processed,
                'enriched_count': enriched_count,
                'success_rate': enriched_count/total_processed if total_processed > 0 else 0,
                'output_file': output_file
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur enrichissement base: {e}")
            raise
        finally:
            await self.close()

# Instance globale
image_service = SeriesImageService()