"""
Prédicteur de sorties de chapitres
=================================

Algorithme ML/statistique pour prédire :
- Dates de sorties prochains chapitres
- Dates de sorties prochains volumes
- Patterns de publication
- Confiance des prédictions
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import statistics
import math
from dataclasses import dataclass

from ..models import SeriesChapters, Chapter, ChapterPrediction, VolumePrediction, ReleaseSchedule

logger = logging.getLogger(__name__)


@dataclass
class ReleasePattern:
    """Structure pour un pattern de sortie détecté"""
    pattern_type: str  # weekly, biweekly, monthly, irregular
    average_interval_days: float
    variance: float
    confidence: float
    last_releases: List[datetime]
    total_data_points: int


class ChapterPredictor:
    """
    Prédicteur intelligent de sorties de chapitres
    
    Utilise plusieurs méthodes :
    - Analyse patterns temporels
    - Régression linéaire simple
    - Moyennes mobiles pondérées
    - Détection anomalies/pauses
    - Saisonnalité (vacances, etc.)
    """
    
    def __init__(self):
        # Patterns de base connus
        self.known_patterns = {
            'weekly_shonen_jump': {
                'interval_days': 7,
                'variance_tolerance': 1.5,
                'break_frequency': 0.15,  # 15% de pauses
                'typical_break_duration': 14  # 2 semaines
            },
            'monthly_magazine': {
                'interval_days': 30,
                'variance_tolerance': 5,
                'break_frequency': 0.05,
                'typical_break_duration': 30
            },
            'biweekly': {
                'interval_days': 14,
                'variance_tolerance': 2,
                'break_frequency': 0.10,
                'typical_break_duration': 14
            }
        }
        
        # Facteurs externes (vacances japonaises, etc.)
        self.seasonal_factors = {
            'golden_week': {'start': (5, 1), 'end': (5, 7), 'impact': -0.3},
            'summer_break': {'start': (8, 10), 'end': (8, 20), 'impact': -0.2},
            'new_year': {'start': (12, 28), 'end': (1, 7), 'impact': -0.4},
            'author_break': {'frequency': 0.1, 'duration_weeks': 2}
        }
    
    async def predict_next_chapter(self, series_data: SeriesChapters) -> Optional[ChapterPrediction]:
        """
        Prédit le prochain chapitre d'une série
        
        Args:
            series_data: Données complètes de la série
            
        Returns:
            Prédiction du prochain chapitre ou None
        """
        try:
            if not series_data.current_chapters:
                logger.warning(f"Aucun chapitre disponible pour prédiction: {series_data.series_name}")
                return None
            
            # Analyser le pattern de sortie
            pattern = await self._analyze_release_pattern(series_data.current_chapters)
            if not pattern:
                return None
            
            # Déterminer le prochain numéro de chapitre
            next_chapter_number = await self._predict_next_chapter_number(series_data.current_chapters)
            
            # Prédire la date
            predicted_date = await self._predict_next_date(pattern, series_data.current_chapters)
            
            # Ajuster pour facteurs saisonniers
            if predicted_date:
                predicted_date = await self._adjust_for_seasonal_factors(predicted_date, series_data.series_name)
            
            # Calculer confiance globale
            confidence = await self._calculate_prediction_confidence(pattern, series_data)
            
            return ChapterPrediction(
                estimated_number=next_chapter_number,
                estimated_date=predicted_date,
                confidence=confidence,
                method=f"{pattern.pattern_type}_analysis"
            )
            
        except Exception as e:
            logger.error(f"Erreur prédiction chapitre {series_data.series_name}: {str(e)}")
            return None
    
    async def predict_next_volume(self, series_data: SeriesChapters) -> Optional[VolumePrediction]:
        """
        Prédit le prochain volume d'une série
        
        Args:
            series_data: Données complètes de la série
            
        Returns:
            Prédiction du prochain volume ou None
        """
        try:
            if not series_data.volumes or not series_data.current_chapters:
                return None
            
            # Analyser pattern volumes
            chapters_per_volume = series_data.average_chapters_per_volume or await self._calculate_avg_chapters_per_volume(series_data)
            
            if not chapters_per_volume:
                return None
            
            # Dernier volume et chapitre
            last_volume = max(series_data.volumes, key=lambda v: v.volume_number) if series_data.volumes else None
            latest_chapter = max(series_data.current_chapters, key=lambda c: c.chapter_number)
            
            if not last_volume:
                return None
            
            # Estimer prochain numéro de volume
            next_volume_number = last_volume.volume_number + 1
            
            # Estimer range de chapitres pour le prochain volume
            start_chapter = int(latest_chapter.chapter_number) + 1
            end_chapter = start_chapter + int(chapters_per_volume) - 1
            estimated_range = f"{start_chapter}-{end_chapter}"
            
            # Prédire date sortie volume (généralement 3-6 mois après début collecte)
            volume_delay_months = await self._estimate_volume_delay(series_data)
            predicted_date = datetime.utcnow() + timedelta(days=volume_delay_months * 30)
            
            # Confiance basée sur régularité volumes précédents
            confidence = await self._calculate_volume_confidence(series_data)
            
            return VolumePrediction(
                estimated_number=next_volume_number,
                estimated_date=predicted_date,
                estimated_chapters_range=estimated_range,
                confidence=confidence,
                method="volume_pattern_analysis"
            )
            
        except Exception as e:
            logger.error(f"Erreur prédiction volume {series_data.series_name}: {str(e)}")
            return None
    
    async def _analyze_release_pattern(self, chapters: List[Chapter]) -> Optional[ReleasePattern]:
        """Analyse le pattern de sortie des chapitres"""
        if len(chapters) < 3:
            return None
        
        # Extraire dates et trier
        chapter_dates = []
        for chapter in chapters:
            if chapter.release_date and chapter.status == "released":
                chapter_dates.append((chapter.chapter_number, chapter.release_date))
        
        if len(chapter_dates) < 3:
            return None
        
        # Trier par date
        chapter_dates.sort(key=lambda x: x[1])
        
        # Calculer intervalles
        intervals = []
        for i in range(1, len(chapter_dates)):
            interval = (chapter_dates[i][1] - chapter_dates[i-1][1]).days
            if interval > 0:  # Ignorer intervals négatifs/nuls
                intervals.append(interval)
        
        if not intervals:
            return None
        
        # Statistiques
        avg_interval = statistics.mean(intervals)
        variance = statistics.variance(intervals) if len(intervals) > 1 else 0
        
        # Déterminer type de pattern
        pattern_type = await self._classify_pattern(avg_interval, variance)
        
        # Confiance basée sur consistance
        confidence = await self._calculate_pattern_confidence(intervals, pattern_type)
        
        return ReleasePattern(
            pattern_type=pattern_type,
            average_interval_days=avg_interval,
            variance=variance,
            confidence=confidence,
            last_releases=[date for _, date in chapter_dates[-5:]],  # 5 dernières
            total_data_points=len(intervals)
        )
    
    async def _classify_pattern(self, avg_interval: float, variance: float) -> str:
        """Classifie le type de pattern de sortie"""
        # Weekly (6-8 jours)
        if 6 <= avg_interval <= 8 and variance < 4:
            return "weekly"
        
        # Biweekly (13-15 jours)
        elif 13 <= avg_interval <= 15 and variance < 9:
            return "biweekly"
        
        # Monthly (28-32 jours)
        elif 28 <= avg_interval <= 35 and variance < 16:
            return "monthly"
        
        # Semi-monthly (14-16 jours)
        elif 14 <= avg_interval <= 16:
            return "semi_monthly"
        
        # Irregular
        else:
            return "irregular"
    
    async def _calculate_pattern_confidence(self, intervals: List[int], pattern_type: str) -> float:
        """Calcule la confiance dans le pattern détecté"""
        if not intervals:
            return 0.0
        
        # Confiance basée sur variance
        variance = statistics.variance(intervals) if len(intervals) > 1 else 0
        avg_interval = statistics.mean(intervals)
        
        # Coefficient de variation
        cv = (variance ** 0.5) / avg_interval if avg_interval > 0 else float('inf')
        
        # Score de régularité
        if pattern_type == "weekly":
            # Weekly doit être très régulier
            if cv < 0.15:  # < 15% variation
                return 0.9
            elif cv < 0.25:
                return 0.7
            else:
                return 0.4
        
        elif pattern_type == "monthly":
            # Monthly peut avoir plus de variance
            if cv < 0.20:
                return 0.8
            elif cv < 0.35:
                return 0.6
            else:
                return 0.3
        
        elif pattern_type == "irregular":
            # Irregular = faible confiance par défaut
            return 0.3
        
        else:
            # Patterns intermédiaires
            if cv < 0.25:
                return 0.6
            else:
                return 0.4
    
    async def _predict_next_chapter_number(self, chapters: List[Chapter]) -> float:
        """Prédit le numéro du prochain chapitre"""
        if not chapters:
            return 1.0
        
        # Trouver le chapitre le plus récent
        latest_chapter = max(chapters, key=lambda c: c.chapter_number)
        
        # Généralement +1, mais peut être +0.5 pour chapitres spéciaux
        next_number = latest_chapter.chapter_number + 1
        
        # Vérifier s'il y a des patterns de numérotation spéciaux
        # (ex: 150.5, 150.1, etc.)
        recent_numbers = sorted([c.chapter_number for c in chapters[-10:]])
        
        # Détecter chapitres .5 récents
        has_half_chapters = any(str(num).endswith('.5') for num in recent_numbers)
        
        if has_half_chapters and latest_chapter.chapter_number == int(latest_chapter.chapter_number):
            # Possibilité d'un chapitre .5
            return latest_chapter.chapter_number + 0.5
        
        return next_number
    
    async def _predict_next_date(self, pattern: ReleasePattern, chapters: List[Chapter]) -> Optional[datetime]:
        """Prédit la date du prochain chapitre"""
        if not pattern.last_releases:
            return None
        
        last_release = max(pattern.last_releases)
        
        # Prédiction basée sur pattern
        if pattern.pattern_type == "weekly":
            # Généralement lundi pour Shonen Jump
            days_to_add = 7
            next_monday = last_release + timedelta(days=days_to_add)
            
            # Ajuster au lundi le plus proche
            while next_monday.weekday() != 0:  # 0 = lundi
                next_monday += timedelta(days=1)
            
            return next_monday
        
        elif pattern.pattern_type == "monthly":
            # Ajouter ~30 jours
            return last_release + timedelta(days=int(pattern.average_interval_days))
        
        else:
            # Utiliser intervalle moyen
            return last_release + timedelta(days=int(pattern.average_interval_days))
    
    async def _adjust_for_seasonal_factors(self, predicted_date: datetime, series_name: str) -> datetime:
        """Ajuste la prédiction pour facteurs saisonniers"""
        # Vérifier vacances japonaises connues
        month, day = predicted_date.month, predicted_date.day
        
        # Golden Week (début mai)
        if month == 5 and 1 <= day <= 7:
            # Décaler d'une semaine
            return predicted_date + timedelta(days=7)
        
        # Vacances d'été (mi-août)
        elif month == 8 and 10 <= day <= 20:
            return predicted_date + timedelta(days=7)
        
        # Nouvel An (fin décembre - début janvier)
        elif (month == 12 and day >= 28) or (month == 1 and day <= 7):
            return predicted_date + timedelta(days=14)
        
        return predicted_date
    
    async def _calculate_prediction_confidence(self, pattern: ReleasePattern, series_data: SeriesChapters) -> float:
        """Calcule la confiance globale de la prédiction"""
        base_confidence = pattern.confidence
        
        # Facteurs d'ajustement
        data_points_factor = min(1.0, pattern.total_data_points / 10)  # Plus de données = plus fiable
        series_status_factor = 1.0 if series_data.release_schedule != "irregular" else 0.7
        
        # Confiance finale
        final_confidence = base_confidence * data_points_factor * series_status_factor
        
        return min(0.95, max(0.1, final_confidence))
    
    async def _calculate_avg_chapters_per_volume(self, series_data: SeriesChapters) -> Optional[float]:
        """Calcule la moyenne de chapitres par volume"""
        if not series_data.volumes:
            # Valeurs par défaut selon type
            if series_data.source_format == "magazine":
                return 10.0  # ~10 chapitres par tankoubon
            return 8.0
        
        chapters_counts = []
        for volume in series_data.volumes:
            if volume.chapters_included:
                chapters_counts.append(len(volume.chapters_included))
            elif volume.chapters_range:
                # Parser range comme "1-10"
                try:
                    start, end = volume.chapters_range.split('-')
                    count = int(end) - int(start) + 1
                    chapters_counts.append(count)
                except:
                    continue
        
        return statistics.mean(chapters_counts) if chapters_counts else 10.0
    
    async def _estimate_volume_delay(self, series_data: SeriesChapters) -> int:
        """Estime le délai avant sortie volume (en mois)"""
        # Analyse historique volumes si disponible
        if len(series_data.volumes) >= 2:
            # Calculer délai moyen entre volumes
            volume_dates = []
            for vol in series_data.volumes:
                if vol.release_date:
                    volume_dates.append(vol.release_date)
            
            if len(volume_dates) >= 2:
                volume_dates.sort()
                intervals = []
                for i in range(1, len(volume_dates)):
                    interval = (volume_dates[i] - volume_dates[i-1]).days
                    intervals.append(interval)
                
                avg_interval_days = statistics.mean(intervals)
                return int(avg_interval_days / 30)  # Convertir en mois
        
        # Valeurs par défaut selon format
        if series_data.source_format == "magazine":
            return 4  # ~4 mois pour magazine traditionnel
        elif series_data.source_format == "webtoon":
            return 6  # ~6 mois pour webtoons
        
        return 4  # Défaut
    
    async def _calculate_volume_confidence(self, series_data: SeriesChapters) -> float:
        """Calcule la confiance pour prédiction volume"""
        base_confidence = 0.6
        
        # Plus de volumes = plus de données = plus fiable
        if len(series_data.volumes) >= 5:
            base_confidence = 0.8
        elif len(series_data.volumes) >= 3:
            base_confidence = 0.7
        
        # Série active = plus fiable
        if series_data.total_chapters_released > 50:
            base_confidence += 0.1
        
        return min(0.9, base_confidence)