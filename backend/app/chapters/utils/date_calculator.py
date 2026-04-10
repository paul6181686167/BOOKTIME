"""
Calculateur de patterns temporels et dates de sorties
====================================================

Utilitaires spécialisés pour :
- Analyse patterns temporels complexes
- Calculs dates sorties intelligents
- Gestion calendriers spéciaux (japonais, etc.)
- Optimisation prédictions temporelles
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, date
import calendar
from enum import Enum
import statistics
import math

logger = logging.getLogger(__name__)


class ReleaseDay(Enum):
    """Jours de sortie standards"""
    MONDAY = 0
    TUESDAY = 1 
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class PublicationPattern(Enum):
    """Patterns de publication connus"""
    WEEKLY_SHONEN_JUMP = "weekly_shonen_jump"  # Lundis
    WEEKLY_SHONEN_MAGAZINE = "weekly_shonen_magazine"  # Mercredis
    MONTHLY_SHONEN_ACE = "monthly_shonen_ace"  # 26e du mois
    BIWEEKLY_GRAND_JUMP = "biweekly_grand_jump"  # 2x par mois
    WEBTOON_DAILY = "webtoon_daily"  # Quotidien
    IRREGULAR = "irregular"


class DateCalculator:
    """
    Calculateur intelligent de patterns temporels et prédictions
    
    Fonctionnalités avancées :
    - Détection automatique patterns publication
    - Calcul dates optimisées selon calendriers
    - Gestion vacances et pauses éditoriales
    - Ajustements saisonniers intelligents
    - Support multiples fuseaux horaires
    """
    
    def __init__(self):
        # Calendrier vacances japonaises (principales)
        self.japanese_holidays = {
            'new_year': [(1, 1), (1, 2), (1, 3)],
            'golden_week': [(4, 29), (5, 3), (5, 4), (5, 5)],
            'summer_obon': [(8, 13), (8, 14), (8, 15), (8, 16)],
            'autumn_equinox': [(9, 23)],  # Variable
            'culture_day': [(11, 3)],
            'christmas_period': [(12, 23), (12, 24), (12, 25)]
        }
        
        # Patterns magazines connus
        self.magazine_patterns = {
            PublicationPattern.WEEKLY_SHONEN_JUMP: {
                'release_day': ReleaseDay.MONDAY,
                'interval_days': 7,
                'break_frequency': 0.15,  # 15% de pauses
                'break_seasons': ['summer', 'winter'],
                'timezone': 'Asia/Tokyo'
            },
            PublicationPattern.WEEKLY_SHONEN_MAGAZINE: {
                'release_day': ReleaseDay.WEDNESDAY,
                'interval_days': 7,
                'break_frequency': 0.12,
                'break_seasons': ['summer', 'winter'],
                'timezone': 'Asia/Tokyo'
            },
            PublicationPattern.MONTHLY_SHONEN_ACE: {
                'release_day_of_month': 26,
                'interval_days': 30,
                'break_frequency': 0.05,
                'break_seasons': [],
                'timezone': 'Asia/Tokyo'
            }
        }
        
        # Facteurs d'ajustement saisonniers
        self.seasonal_adjustments = {
            'spring': {'factor': 1.0, 'variance': 0.1},
            'summer': {'factor': 1.1, 'variance': 0.2},  # Plus de pauses
            'autumn': {'factor': 0.95, 'variance': 0.1},  # Plus régulier
            'winter': {'factor': 1.15, 'variance': 0.25}  # Vacances fin d'année
        }
    
    async def detect_publication_pattern(self, release_dates: List[datetime]) -> Dict[str, Any]:
        """
        Détecte le pattern de publication à partir de dates historiques
        
        Args:
            release_dates: Liste des dates de sorties historiques
            
        Returns:
            Informations détaillées sur le pattern détecté
        """
        if len(release_dates) < 3:
            return {'pattern': PublicationPattern.IRREGULAR, 'confidence': 0.0}
        
        try:
            # Trier les dates
            sorted_dates = sorted(release_dates)
            
            # Analyser intervalles
            intervals = []
            for i in range(1, len(sorted_dates)):
                interval = (sorted_dates[i] - sorted_dates[i-1]).days
                intervals.append(interval)
            
            # Statistiques intervalles
            avg_interval = statistics.mean(intervals)
            interval_variance = statistics.variance(intervals) if len(intervals) > 1 else 0
            
            # Analyser jours de semaine
            weekdays = [d.weekday() for d in sorted_dates]
            most_common_weekday = max(set(weekdays), key=weekdays.count)
            weekday_consistency = weekdays.count(most_common_weekday) / len(weekdays)
            
            # Détecter pattern
            detected_pattern = await self._classify_publication_pattern(
                avg_interval, interval_variance, most_common_weekday, weekday_consistency
            )
            
            # Calculer confiance
            confidence = await self._calculate_pattern_confidence(
                intervals, most_common_weekday, weekday_consistency, detected_pattern
            )
            
            return {
                'pattern': detected_pattern,
                'confidence': confidence,
                'avg_interval_days': avg_interval,
                'interval_variance': interval_variance,
                'most_common_weekday': most_common_weekday,
                'weekday_consistency': weekday_consistency,
                'total_releases': len(release_dates),
                'date_range': {
                    'start': sorted_dates[0].isoformat(),
                    'end': sorted_dates[-1].isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur détection pattern: {str(e)}")
            return {'pattern': PublicationPattern.IRREGULAR, 'confidence': 0.0}
    
    async def calculate_next_release_date(self, last_release: datetime, 
                                        pattern_info: Dict[str, Any]) -> Optional[datetime]:
        """
        Calcule la prochaine date de sortie optimisée
        
        Args:
            last_release: Dernière date de sortie connue
            pattern_info: Informations sur le pattern détecté
            
        Returns:
            Date prédite pour la prochaine sortie
        """
        try:
            pattern = pattern_info.get('pattern', PublicationPattern.IRREGULAR)
            confidence = pattern_info.get('confidence', 0.5)
            
            if confidence < 0.3:
                # Pattern trop incertain, utiliser moyenne simple
                avg_interval = pattern_info.get('avg_interval_days', 7)
                return last_release + timedelta(days=int(avg_interval))
            
            # Calcul selon pattern spécifique
            if pattern == PublicationPattern.WEEKLY_SHONEN_JUMP:
                return await self._calculate_weekly_jump_date(last_release)
            
            elif pattern == PublicationPattern.WEEKLY_SHONEN_MAGAZINE:
                return await self._calculate_weekly_magazine_date(last_release)
            
            elif pattern == PublicationPattern.MONTHLY_SHONEN_ACE:
                return await self._calculate_monthly_ace_date(last_release)
            
            else:
                # Pattern général basé sur jour de semaine détecté
                return await self._calculate_general_pattern_date(last_release, pattern_info)
                
        except Exception as e:
            logger.error(f"Erreur calcul prochaine date: {str(e)}")
            return None
    
    async def adjust_for_holidays(self, predicted_date: datetime, 
                                country_code: str = 'JP') -> datetime:
        """
        Ajuste une date prédite pour éviter les vacances
        
        Args:
            predicted_date: Date initialement prédite
            country_code: Code pays pour calendrier vacances
            
        Returns:
            Date ajustée évitant les vacances
        """
        if country_code == 'JP':
            return await self._adjust_for_japanese_holidays(predicted_date)
        
        # Pour d'autres pays, retourner tel quel pour l'instant
        return predicted_date
    
    async def calculate_seasonal_adjustment(self, base_date: datetime) -> float:
        """
        Calcule un facteur d'ajustement saisonnier
        
        Args:
            base_date: Date de base pour déterminer saison
            
        Returns:
            Facteur multiplicateur (1.0 = normal, >1.0 = retards plus probables)
        """
        month = base_date.month
        
        # Déterminer saison (hémisphère nord)
        if month in [3, 4, 5]:
            season = 'spring'
        elif month in [6, 7, 8]:
            season = 'summer'
        elif month in [9, 10, 11]:
            season = 'autumn'
        else:
            season = 'winter'
        
        adjustment = self.seasonal_adjustments.get(season, {'factor': 1.0})
        return adjustment['factor']
    
    async def predict_multiple_dates(self, last_release: datetime, 
                                   pattern_info: Dict[str, Any], 
                                   count: int = 5) -> List[Dict[str, Any]]:
        """
        Prédit plusieurs dates de sortie successives
        
        Args:
            last_release: Dernière sortie connue
            pattern_info: Pattern détecté
            count: Nombre de prédictions à générer
            
        Returns:
            Liste des prédictions avec confiance décroissante
        """
        predictions = []
        current_date = last_release
        base_confidence = pattern_info.get('confidence', 0.5)
        
        try:
            for i in range(count):
                # Calculer prochaine date
                next_date = await self.calculate_next_release_date(current_date, pattern_info)
                if not next_date:
                    break
                
                # Ajuster pour vacances
                adjusted_date = await self.adjust_for_holidays(next_date)
                
                # Calculer facteur saisonnier
                seasonal_factor = await self.calculate_seasonal_adjustment(adjusted_date)
                
                # Confiance décroissante avec distance temporelle
                prediction_confidence = base_confidence * (0.9 ** i) * (1 / seasonal_factor)
                
                predictions.append({
                    'date': adjusted_date.isoformat(),
                    'confidence': min(0.95, max(0.1, prediction_confidence)),
                    'seasonal_factor': seasonal_factor,
                    'adjusted_for_holidays': adjusted_date != next_date,
                    'prediction_index': i + 1
                })
                
                current_date = adjusted_date
            
            return predictions
            
        except Exception as e:
            logger.error(f"Erreur prédictions multiples: {str(e)}")
            return []
    
    # Méthodes privées spécialisées
    
    async def _classify_publication_pattern(self, avg_interval: float, variance: float,
                                          weekday: int, consistency: float) -> PublicationPattern:
        """Classifie le pattern de publication"""
        
        # Weekly patterns (6-8 jours)
        if 6 <= avg_interval <= 8 and variance < 4:
            if weekday == 0 and consistency > 0.7:  # Lundi
                return PublicationPattern.WEEKLY_SHONEN_JUMP
            elif weekday == 2 and consistency > 0.7:  # Mercredi
                return PublicationPattern.WEEKLY_SHONEN_MAGAZINE
            else:
                return PublicationPattern.IRREGULAR  # Weekly mais pas pattern connu
        
        # Monthly patterns (28-35 jours)
        elif 28 <= avg_interval <= 35 and variance < 25:
            return PublicationPattern.MONTHLY_SHONEN_ACE
        
        # Biweekly patterns (13-15 jours)
        elif 13 <= avg_interval <= 15 and variance < 9:
            return PublicationPattern.BIWEEKLY_GRAND_JUMP
        
        # Daily/frequent (1-2 jours) - webtoons
        elif 1 <= avg_interval <= 2:
            return PublicationPattern.WEBTOON_DAILY
        
        return PublicationPattern.IRREGULAR
    
    async def _calculate_pattern_confidence(self, intervals: List[int], weekday: int,
                                          consistency: float, pattern: PublicationPattern) -> float:
        """Calcule la confiance dans le pattern détecté"""
        
        base_confidence = 0.5
        
        # Bonus pour consistance jour de semaine
        if consistency > 0.8:
            base_confidence += 0.3
        elif consistency > 0.6:
            base_confidence += 0.2
        
        # Bonus pour régularité intervalles
        if intervals:
            cv = (statistics.stdev(intervals) / statistics.mean(intervals)) if statistics.mean(intervals) > 0 else float('inf')
            if cv < 0.15:  # Très régulier
                base_confidence += 0.2
            elif cv < 0.25:  # Assez régulier
                base_confidence += 0.1
        
        # Bonus patterns connus
        if pattern in [PublicationPattern.WEEKLY_SHONEN_JUMP, PublicationPattern.WEEKLY_SHONEN_MAGAZINE]:
            base_confidence += 0.1
        
        return min(0.95, max(0.1, base_confidence))
    
    async def _calculate_weekly_jump_date(self, last_release: datetime) -> datetime:
        """Calcule prochaine date Shonen Jump (lundis)"""
        next_date = last_release + timedelta(days=7)
        
        # Ajuster au lundi
        while next_date.weekday() != 0:
            next_date += timedelta(days=1)
        
        return next_date
    
    async def _calculate_weekly_magazine_date(self, last_release: datetime) -> datetime:
        """Calcule prochaine date Shonen Magazine (mercredis)"""
        next_date = last_release + timedelta(days=7)
        
        # Ajuster au mercredi
        while next_date.weekday() != 2:
            next_date += timedelta(days=1)
        
        return next_date
    
    async def _calculate_monthly_ace_date(self, last_release: datetime) -> datetime:
        """Calcule prochaine date Monthly Ace (26e du mois)"""
        # Prochaine occurrence du 26 du mois
        current_month = last_release.month
        current_year = last_release.year
        
        # Essayer mois suivant
        next_month = current_month + 1
        next_year = current_year
        
        if next_month > 12:
            next_month = 1
            next_year += 1
        
        try:
            next_date = datetime(next_year, next_month, 26)
            return next_date
        except ValueError:
            # Si 26 n'existe pas dans ce mois, prendre dernier jour
            last_day = calendar.monthrange(next_year, next_month)[1]
            return datetime(next_year, next_month, min(26, last_day))
    
    async def _calculate_general_pattern_date(self, last_release: datetime,
                                           pattern_info: Dict[str, Any]) -> datetime:
        """Calcule date selon pattern général détecté"""
        avg_interval = pattern_info.get('avg_interval_days', 7)
        target_weekday = pattern_info.get('most_common_weekday', 0)
        
        next_date = last_release + timedelta(days=int(avg_interval))
        
        # Ajuster au jour de semaine cible si bonne consistance
        if pattern_info.get('weekday_consistency', 0) > 0.6:
            while next_date.weekday() != target_weekday:
                next_date += timedelta(days=1)
        
        return next_date
    
    async def _adjust_for_japanese_holidays(self, predicted_date: datetime) -> datetime:
        """Ajuste pour vacances japonaises"""
        month, day = predicted_date.month, predicted_date.day
        
        # Vérifier vacances fixes
        for holiday_name, dates in self.japanese_holidays.items():
            for h_month, h_day in dates:
                if month == h_month and day == h_day:
                    # Décaler d'une semaine
                    return predicted_date + timedelta(days=7)
        
        # Périodes spéciales avec décalage plus long
        if month == 12 and day >= 20:  # Fin d'année
            return predicted_date + timedelta(days=14)
        
        if month == 1 and day <= 10:  # Début d'année
            return predicted_date + timedelta(days=7)
        
        if month == 8 and 10 <= day <= 20:  # Obon
            return predicted_date + timedelta(days=7)
        
        return predicted_date