"""
Service principal pour la gestion des chapitres
==============================================

Orchestration des fonctionnalités :
- Récupération données APIs externes
- Cache intelligent
- Prédictions dates sorties
- Regroupement chapitres → volumes
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import uuid4

from ..database import db as database_db
from .models import (
    SeriesChapters, 
    Chapter, 
    Volume, 
    ChapterPrediction, 
    VolumePrediction,
    ChapterStatus,
    VolumeStatus,
    ReleaseSchedule,
    SourceFormat
)

# Imports des intégrations (à créer)
from .integrations.anilist import AniListService
from .integrations.mangaupdates import MangaUpdatesService 
from .integrations.predictor import ChapterPredictor
from .utils.chapter_grouper import ChapterGrouper
from .utils.date_calculator import DateCalculator

logger = logging.getLogger(__name__)


class ChapterService:
    """
    Service principal pour la gestion des chapitres individuels
    
    Fonctionnalités :
    - Récupération données séries depuis APIs externes
    - Mise en cache intelligente avec TTL
    - Prédictions dates sorties basées sur patterns
    - Regroupement automatique chapitres → volumes
    - Synchronisation multi-sources
    """
    
    def __init__(self):
        self.db = None  # Initialisé dans _ensure_db()
        self.collection_name = "series_chapters"
        
        # Services externes
        self.anilist = AniListService()
        self.mangaupdates = MangaUpdatesService()
        self.predictor = ChapterPredictor()
        
        # Utilitaires
        self.grouper = ChapterGrouper()
        self.calculator = DateCalculator()
        
        # Configuration cache
        self.cache_duration = timedelta(hours=3)
        self.prediction_cache_duration = timedelta(hours=1)
        
    async def _ensure_db(self):
        """Initialise la connexion base de données si nécessaire"""
        if self.db is None:
            self.db = database_db
            
    async def get_series_chapters(self, series_name: str, force_refresh: bool = False) -> Optional[SeriesChapters]:
        """
        Récupère les informations de chapitres pour une série
        
        Args:
            series_name: Nom de la série
            force_refresh: Forcer le rafraîchissement depuis les APIs
            
        Returns:
            SeriesChapters ou None si non trouvé
        """
        await self._ensure_db()
        
        try:
            # 1. Vérifier cache local d'abord (sauf si force_refresh)
            if not force_refresh:
                cached_data = await self._get_cached_series(series_name)
                if cached_data and not self._is_cache_expired(cached_data):
                    logger.info(f"Données de cache utilisées pour {series_name}")
                    return cached_data
            
            # 2. Récupération depuis APIs externes
            logger.info(f"Récupération données externes pour {series_name}")
            series_data = await self._fetch_from_external_apis(series_name)
            
            if not series_data:
                logger.warning(f"Aucune donnée trouvée pour {series_name}")
                return None
                
            # 3. Enrichissement avec prédictions
            series_data = await self._enrich_with_predictions(series_data)
            
            # 4. Regroupement automatique en volumes
            if series_data.auto_volume_grouping:
                series_data = await self._auto_group_volumes(series_data)
            
            # 5. Sauvegarde cache
            await self._save_to_cache(series_data)
            
            logger.info(f"Données complétées pour {series_name}: {len(series_data.current_chapters)} chapitres")
            return series_data
            
        except Exception as e:
            logger.error(f"Erreur récupération chapitres {series_name}: {str(e)}")
            # Fallback sur cache même expiré
            cached_data = await self._get_cached_series(series_name)
            return cached_data
    
    async def refresh_series_chapters(self, series_name: str) -> bool:
        """
        Force le rafraîchissement des données d'une série
        
        Args:
            series_name: Nom de la série
            
        Returns:
            True si succès, False sinon
        """
        try:
            result = await self.get_series_chapters(series_name, force_refresh=True)
            return result is not None
        except Exception as e:
            logger.error(f"Erreur rafraîchissement {series_name}: {str(e)}")
            return False
    
    async def search_series_in_apis(self, series_name: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Recherche une série dans les APIs externes pour mapping
        
        Args:
            series_name: Nom de la série à rechercher
            
        Returns:
            Dictionnaire avec résultats AniList et MangaUpdates
        """
        try:
            # Recherche parallèle dans les APIs
            anilist_results, mu_results = await asyncio.gather(
                self.anilist.search_manga(series_name),
                self.mangaupdates.search_series(series_name),
                return_exceptions=True
            )
            
            # Gestion des erreurs
            if isinstance(anilist_results, Exception):
                logger.error(f"Erreur recherche AniList: {anilist_results}")
                anilist_results = []
            
            if isinstance(mu_results, Exception):
                logger.error(f"Erreur recherche MangaUpdates: {mu_results}")
                mu_results = []
            
            return {
                "anilist_matches": anilist_results or [],
                "mangaupdates_matches": mu_results or [],
                "confidence_scores": self._calculate_confidence_scores(
                    series_name, anilist_results or [], mu_results or []
                )
            }
            
        except Exception as e:
            logger.error(f"Erreur recherche série {series_name}: {str(e)}")
            return {
                "anilist_matches": [],
                "mangaupdates_matches": [],
                "confidence_scores": {}
            }
    
    async def map_series_ids(self, series_name: str, anilist_id: Optional[int] = None, 
                           mangaupdates_id: Optional[int] = None) -> bool:
        """
        Associe une série aux IDs des APIs externes
        
        Args:
            series_name: Nom de la série
            anilist_id: ID AniList (optionnel)
            mangaupdates_id: ID MangaUpdates (optionnel)
            
        Returns:
            True si succès
        """
        await self._ensure_db()
        
        try:
            # Récupérer ou créer l'entrée série
            collection = self.db[self.collection_name]
            
            update_data = {
                "last_updated": datetime.utcnow()
            }
            
            if anilist_id:
                update_data["manga_id_anilist"] = anilist_id
            if mangaupdates_id:
                update_data["manga_id_mangaupdates"] = mangaupdates_id
            
            result = collection.update_one(
                {"series_name": series_name},
                {"$set": update_data},
                upsert=True
            )
            
            logger.info(f"IDs mappés pour {series_name}: AniList={anilist_id}, MU={mangaupdates_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur mapping IDs {series_name}: {str(e)}")
            return False
    
    async def get_upcoming_releases(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Récupère le planning des sorties à venir
        
        Returns:
            Dictionnaire avec sorties cette semaine, semaine prochaine, ce mois
        """
        await self._ensure_db()
        
        try:
            collection = self.db[self.collection_name]
            now = datetime.utcnow()
            
            # Dates de référence
            end_of_week = now + timedelta(days=(6 - now.weekday()))
            end_of_next_week = end_of_week + timedelta(days=7)
            end_of_month = now.replace(day=28) + timedelta(days=4)  # Fin du mois
            
            # Récupérer toutes les séries avec prédictions
            cursor = collection.find(
                {"next_chapter.estimated_date": {"$exists": True}}
            )
            
            this_week = []
            next_week = []
            this_month = []
            
            for series_doc in cursor:
                if "next_chapter" in series_doc and series_doc["next_chapter"]:
                    pred = series_doc["next_chapter"]
                    est_date = pred.get("estimated_date")
                    
                    if est_date:
                        release_info = {
                            "series_name": series_doc["series_name"],
                            "chapter_number": pred.get("estimated_number"),
                            "estimated_date": est_date.isoformat(),
                            "confidence": pred.get("confidence", 0.5)
                        }
                        
                        if est_date <= end_of_week:
                            this_week.append(release_info)
                        elif est_date <= end_of_next_week:
                            next_week.append(release_info)
                        elif est_date <= end_of_month:
                            this_month.append(release_info)
            
            # Tri par date
            for releases in [this_week, next_week, this_month]:
                releases.sort(key=lambda x: x["estimated_date"])
            
            return {
                "this_week": this_week,
                "next_week": next_week,
                "this_month": this_month
            }
            
        except Exception as e:
            logger.error(f"Erreur récupération planning: {str(e)}")
            return {"this_week": [], "next_week": [], "this_month": []}
    
    async def get_integration_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Vérifie le statut des intégrations externes
        
        Returns:
            Dictionnaire avec statut de chaque API
        """
        try:
            # Tests parallèles des APIs
            anilist_status, mu_status = await asyncio.gather(
                self._test_anilist_connection(),
                self._test_mangaupdates_connection(),
                return_exceptions=True
            )
            
            return {
                "anilist": self._format_integration_status(anilist_status),
                "mangaupdates": self._format_integration_status(mu_status)
            }
            
        except Exception as e:
            logger.error(f"Erreur vérification intégrations: {str(e)}")
            return {
                "anilist": {"status": "error", "error_message": str(e)},
                "mangaupdates": {"status": "error", "error_message": str(e)}
            }
    
    # Méthodes privées helpers
    
    async def _get_cached_series(self, series_name: str) -> Optional[SeriesChapters]:
        """Récupère les données depuis le cache local"""
        collection = self.db[self.collection_name]
        doc = collection.find_one({"series_name": series_name})
        
        if doc:
            # Conversion MongoDB _id → id pour Pydantic
            if '_id' in doc:
                doc['id'] = str(doc['_id'])
                del doc['_id']
            
            # Conversion document MongoDB → modèle Pydantic
            return SeriesChapters(**doc)
        return None
    
    def _is_cache_expired(self, series_data: SeriesChapters) -> bool:
        """Vérifie si le cache est expiré"""
        if not series_data.cache_expires:
            return True
        return datetime.utcnow() > series_data.cache_expires
    
    async def _fetch_from_external_apis(self, series_name: str) -> Optional[SeriesChapters]:
        """Récupère données depuis APIs externes"""
        logger.info(f"Récupération APIs externes pour {series_name}")
        
        try:
            # ✅ CORRIGÉ : Utiliser directement get_recent_releases_by_name pour récupérer toutes les données
            
            # 1. Récupérer les releases directement par nom (méthode simplifiée)
            releases = await self.mangaupdates.get_recent_releases_by_name(series_name, days_back=365)
            
            if not releases:
                logger.warning(f"Aucune release trouvée pour {series_name}")
                return None
            
            # 2. Récupérer aussi les métadonnées de la série
            search_results = await self.search_series_in_apis(series_name)
            mangaupdates_matches = search_results.get("mangaupdates_matches", [])
            anilist_matches = search_results.get("anilist_matches", [])
            
            # 3. Prendre les métadonnées du meilleur match si disponible
            best_match = mangaupdates_matches[0] if mangaupdates_matches else {}
            series_id = best_match.get('id')
            # Valeurs réelles issues de l'API (peuvent être absentes / None).
            total_volumes = best_match.get('total_volumes')
            latest_chapter = best_match.get('latest_chapter')

            # 4. Convertir releases en objets Chapter
            chapters = []
            for release in releases:
                chapter_number = release.get('chapter_number')
                if chapter_number is None:
                    continue
                chapter = Chapter(
                    id=str(uuid4()),
                    chapter_number=chapter_number,
                    title=release.get('title', f"Chapter {chapter_number}"),
                    release_date=datetime.strptime(release['release_date'], '%Y-%m-%d') if release.get('release_date') else None,
                    status=ChapterStatus.RELEASED if release.get('release_date') else ChapterStatus.UPCOMING,
                    volume_number=release.get('volume'),  # Renseigné uniquement si MangaUpdates a étiqueté le tome
                    url="",
                    source_format=SourceFormat.MANGA
                )
                chapters.append(chapter)

            # Statistiques dérivées, robustes aux valeurs manquantes.
            highest_chapter = max((c.chapter_number for c in chapters), default=0)
            total_chapters_released = int(latest_chapter) if latest_chapter else int(highest_chapter)

            # 5. Créer SeriesChapters avec vraies données
            series_data = SeriesChapters(
                id=str(uuid4()),
                series_name=series_name,
                current_chapters=chapters,
                volumes=[],  # Rempli par le regroupement (tag volume MangaUpdates)
                total_chapters_released=total_chapters_released,
                total_volumes_released=int(total_volumes) if total_volumes else 0,
                average_chapters_per_volume=None,
                manga_id_mangaupdates=series_id,
                manga_id_anilist=anilist_matches[0].get('id') if anilist_matches else None,
                release_schedule=ReleaseSchedule.WEEKLY,
                source_format=SourceFormat.MANGA,
                enable_predictions=True,
                auto_volume_grouping=True,
                cache_expires=datetime.utcnow() + self.cache_duration
            )

            logger.info(f"Données récupérées pour {series_name}: {len(chapters)} chapitres, {series_data.total_volumes_released} volumes")
            return series_data
            
        except Exception as e:
            logger.error(f"Erreur récupération APIs pour {series_name}: {str(e)}")
            return None
    
    async def _enrich_with_predictions(self, series_data: SeriesChapters) -> SeriesChapters:
        """Enrichit avec prédictions de sorties"""
        if not series_data.enable_predictions:
            return series_data
        
        # Prédiction prochain chapitre
        next_chapter = await self.predictor.predict_next_chapter(series_data)
        if next_chapter:
            series_data.next_chapter = next_chapter
        
        # Prédiction prochain volume  
        next_volume = await self.predictor.predict_next_volume(series_data)
        if next_volume:
            series_data.next_volume = next_volume
        
        return series_data
    
    async def _auto_group_volumes(self, series_data: SeriesChapters) -> SeriesChapters:
        """
        Regroupe les chapitres en tomes strictement d'après le tag ``volume`` de
        MangaUpdates. Les chapitres non étiquetés restent orphelins (affichés
        chapitre par chapitre). Les dates officielles de tomes sont ajoutées en
        aval (Wikidata / Google Books).
        """
        grouped_volumes = await self.grouper.group_by_volume_tag(
            series_data.current_chapters
        )
        series_data.volumes = grouped_volumes
        return series_data
    
    async def _save_to_cache(self, series_data: SeriesChapters) -> bool:
        """Sauvegarde dans le cache local"""
        try:
            collection = self.db[self.collection_name]
            doc = series_data.dict()
            
            collection.replace_one(
                {"series_name": series_data.series_name},
                doc,
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Erreur sauvegarde cache: {str(e)}")
            return False
    
    def _calculate_confidence_scores(self, query: str, anilist_results: List, mu_results: List) -> Dict[str, float]:
        """Calcule scores de confiance pour les résultats de recherche"""
        # Implémentation basique - peut être enrichie avec algorithmes plus sophistiqués
        scores = {}
        
        if anilist_results:
            # Score basé sur correspondance titre
            best_match = max(anilist_results, key=lambda x: self._string_similarity(query, x.get('title', '')))
            scores['anilist'] = self._string_similarity(query, best_match.get('title', ''))
        
        if mu_results:
            best_match = max(mu_results, key=lambda x: self._string_similarity(query, x.get('title', '')))
            scores['mangaupdates'] = self._string_similarity(query, best_match.get('title', ''))
        
        return scores
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calcul simple de similarité entre chaînes"""
        # Implémentation basique - peut utiliser des libs comme difflib
        s1, s2 = s1.lower().strip(), s2.lower().strip()
        if s1 == s2:
            return 1.0
        
        # Correspondance partielle
        if s1 in s2 or s2 in s1:
            return 0.8
        
        # Score basique basé sur mots communs
        words1 = set(s1.split())
        words2 = set(s2.split())
        common = len(words1.intersection(words2))
        total = len(words1.union(words2))
        
        return common / total if total > 0 else 0.0
    
    async def _test_anilist_connection(self) -> Dict[str, Any]:
        """Test de connexion AniList"""
        try:
            start_time = datetime.utcnow()
            result = await self.anilist.health_check()
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return {
                "status": "ok" if result else "error",
                "response_time": int(response_time),
                "last_success": datetime.utcnow() if result else None
            }
        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e),
                "response_time": None
            }
    
    async def _test_mangaupdates_connection(self) -> Dict[str, Any]:
        """Test de connexion MangaUpdates"""
        try:
            start_time = datetime.utcnow()
            result = await self.mangaupdates.health_check()
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return {
                "status": "ok" if result else "error", 
                "response_time": int(response_time),
                "last_success": datetime.utcnow() if result else None
            }
        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e),
                "response_time": None
            }
    
    def _format_integration_status(self, status_result) -> Dict[str, Any]:
        """Formate le résultat de statut d'intégration"""
        if isinstance(status_result, Exception):
            return {
                "status": "error",
                "error_message": str(status_result),
                "response_time": None
            }
        elif isinstance(status_result, dict):
            return status_result
        else:
            return {
                "status": "unknown",
                "error_message": "Format de réponse inattendu"
            }