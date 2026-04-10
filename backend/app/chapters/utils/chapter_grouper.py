"""
Utilitaire de regroupement de chapitres en volumes
=================================================

Logique intelligente pour :
- Regrouper chapitres individuels en volumes/tomes
- Détecter patterns de numérotation
- Gérer transitions chapitres → volumes
- Optimiser organisation bibliothèque
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import re
from collections import defaultdict

from ..models import Chapter, Volume, VolumeStatus

logger = logging.getLogger(__name__)


class ChapterGrouper:
    """
    Gestionnaire intelligent de regroupement chapitres → volumes
    
    Fonctionnalités :
    - Détection automatique patterns de groupement
    - Regroupement par numérotation séquentielle
    - Gestion cas spéciaux (chapitres .5, specials, etc.)
    - Optimisation selon format série (manga, webtoon, etc.)
    """
    
    def __init__(self):
        # Patterns de regroupement par format
        self.grouping_patterns = {
            'magazine_manga': {
                'chapters_per_volume': 10,
                'volume_threshold': 8,  # Min chapitres pour créer volume
                'special_handling': True
            },
            'webtoon': {
                'chapters_per_volume': 20,
                'volume_threshold': 15,
                'special_handling': False
            },
            'light_novel': {
                'chapters_per_volume': 6,
                'volume_threshold': 4,
                'special_handling': True
            }
        }
        
        # Patterns numérotation spéciale
        self.special_patterns = {
            'half_chapter': re.compile(r'(\d+)\.5'),
            'special_chapter': re.compile(r'(\d+)\.1|(\d+)\.2|(\d+)\.3'),
            'extra_chapter': re.compile(r'extra|omake|bonus', re.IGNORECASE),
            'volume_extra': re.compile(r'v(\d+)\s*extra', re.IGNORECASE)
        }
    
    async def group_chapters_to_volumes(self, chapters: List[Chapter], 
                                       format_hint: str = "magazine_manga", 
                                       total_volumes_expected: int = None) -> List[Volume]:
        """
        Groupe une liste de chapitres en volumes intelligents
        
        Args:
            chapters: Liste des chapitres à regrouper
            format_hint: Hint sur le format pour optimiser regroupement
            total_volumes_expected: Nombre total de volumes attendus (pour génération complète)
            
        Returns:
            Liste des volumes créés
        """
        if not chapters:
            return []
        
        try:
            # Trier chapitres par numéro
            sorted_chapters = sorted(chapters, key=lambda c: c.chapter_number)
            
            # Analyser pattern de numérotation
            numbering_pattern = await self._analyze_numbering_pattern(sorted_chapters)
            
            # Sélectionner stratégie de regroupement
            grouping_config = self.grouping_patterns.get(format_hint, self.grouping_patterns['magazine_manga'])
            
            # ✅ NOUVEAU : Si total_volumes_expected fourni, générer structure complète
            if total_volumes_expected and total_volumes_expected > 0:
                volumes = await self._generate_complete_volume_structure(
                    sorted_chapters, grouping_config, total_volumes_expected
                )
            else:
                # Regroupement classique basé sur chapitres disponibles
                if numbering_pattern['has_volume_hints']:
                    # Regroupement basé sur indices volumes existants
                    volumes = await self._group_by_volume_hints(sorted_chapters, numbering_pattern)
                else:
                    # Regroupement séquentiel standard
                    volumes = await self._group_sequentially(sorted_chapters, grouping_config)
            
            # Post-traitement et optimisation
            volumes = await self._optimize_grouping(volumes, sorted_chapters)
            
            logger.info(f"Regroupement: {len(chapters)} chapitres → {len(volumes)} volumes")
            return volumes
            
        except Exception as e:
            logger.error(f"Erreur regroupement chapitres: {str(e)}")
            return []
    
    async def suggest_volume_creation(self, chapters: List[Chapter], 
                                    existing_volumes: List[Volume]) -> Optional[Volume]:
        """
        Suggère la création d'un nouveau volume basé sur chapitres disponibles
        
        Args:
            chapters: Chapitres non groupés
            existing_volumes: Volumes existants
            
        Returns:
            Suggestion de volume ou None
        """
        if not chapters:
            return None
        
        try:
            # Trier chapitres
            sorted_chapters = sorted(chapters, key=lambda c: c.chapter_number)
            
            # Trouver séquence continue
            continuous_sequence = await self._find_continuous_sequence(sorted_chapters)
            
            if len(continuous_sequence) < 8:  # Seuil minimum
                return None
            
            # Déterminer numéro volume suivant
            next_volume_num = max([v.volume_number for v in existing_volumes], default=0) + 1
            
            # Créer suggestion volume
            start_ch = int(continuous_sequence[0].chapter_number)
            end_ch = int(continuous_sequence[-1].chapter_number)
            
            suggested_volume = Volume(
                volume_number=next_volume_num,
                chapters_range=f"{start_ch}-{end_ch}",
                chapters_included=[c.chapter_number for c in continuous_sequence],
                status=VolumeStatus.COLLECTING,
                release_date=None  # À déterminer
            )
            
            return suggested_volume
            
        except Exception as e:
            logger.error(f"Erreur suggestion volume: {str(e)}")
            return None
    
    async def _analyze_numbering_pattern(self, chapters: List[Chapter]) -> Dict[str, Any]:
        """Analyse le pattern de numérotation des chapitres"""
        pattern_info = {
            'has_volume_hints': False,
            'has_special_chapters': False,
            'numbering_gaps': [],
            'decimal_chapters': [],
            'volume_indicators': []
        }
        
        try:
            chapter_numbers = [c.chapter_number for c in chapters]
            
            # Détecter chapitres décimaux (.5, .1, etc.)
            decimal_chapters = [num for num in chapter_numbers if num != int(num)]
            pattern_info['decimal_chapters'] = decimal_chapters
            pattern_info['has_special_chapters'] = len(decimal_chapters) > 0
            
            # Détecter gaps dans numérotation
            sorted_numbers = sorted([int(num) for num in chapter_numbers])
            gaps = []
            for i in range(1, len(sorted_numbers)):
                if sorted_numbers[i] - sorted_numbers[i-1] > 1:
                    gaps.append((sorted_numbers[i-1], sorted_numbers[i]))
            pattern_info['numbering_gaps'] = gaps
            
            # Chercher indices volumes dans titres/métadonnées
            volume_hints = []
            for chapter in chapters:
                if chapter.title:
                    # Pattern "Volume X" dans titre
                    vol_match = re.search(r'volume?\s*(\d+)', chapter.title, re.IGNORECASE)
                    if vol_match:
                        volume_hints.append((chapter.chapter_number, int(vol_match.group(1))))
                
                # Vérifier si chapitre déjà associé à volume
                if chapter.grouped_in_volume:
                    volume_hints.append((chapter.chapter_number, chapter.grouped_in_volume))
            
            pattern_info['volume_indicators'] = volume_hints
            pattern_info['has_volume_hints'] = len(volume_hints) > 0
            
            return pattern_info
            
        except Exception as e:
            logger.error(f"Erreur analyse pattern numérotation: {str(e)}")
            return pattern_info
    
    async def _generate_complete_volume_structure(self, chapters: List[Chapter], 
                                                config: Dict[str, Any], 
                                                total_volumes: int) -> List[Volume]:
        """
        Génère une structure complète de volumes (ex: tomes 1-112) même si tous les chapitres ne sont pas disponibles
        
        Args:
            chapters: Chapitres disponibles
            config: Configuration de regroupement
            total_volumes: Nombre total de volumes à générer
            
        Returns:
            Liste complète des volumes
        """
        volumes = []
        chapters_per_volume = config['chapters_per_volume']  # Standard: 10 chapitres par tome
        
        try:
            # Créer un mapping des chapitres disponibles
            available_chapters = {int(ch.chapter_number): ch for ch in chapters}
            
            # Générer tous les volumes de 1 à total_volumes
            for volume_num in range(1, total_volumes + 1):
                # Calculer la range de chapitres pour ce volume
                start_chapter = (volume_num - 1) * chapters_per_volume + 1
                end_chapter = volume_num * chapters_per_volume
                
                # ✅ CORRECTION : Ajuster pour One Piece qui a parfois plus/moins de chapitres par tome
                # Pour les derniers volumes, ajuster la range
                if volume_num == total_volumes:
                    # Dernier volume peut aller jusqu'au chapitre le plus élevé disponible
                    max_available_chapter = max(available_chapters.keys()) if available_chapters else end_chapter
                    end_chapter = max(end_chapter, max_available_chapter)
                
                # Trouver les chapitres disponibles dans cette range
                volume_chapters = []
                chapters_included = []
                
                for ch_num in range(start_chapter, end_chapter + 1):
                    if ch_num in available_chapters:
                        volume_chapters.append(available_chapters[ch_num])
                        chapters_included.append(float(ch_num))
                
                # ✅ NOUVEAU : Inclure aussi les chapitres "orphelins" (ex: 1144-1155 sans tome)
                # Chercher les chapitres sans volume assigné dans une range étendue
                orphan_chapters = []
                for ch_num, chapter in available_chapters.items():
                    # Si chapitre n'a pas de volume assigné ET est dans une range "avancée"
                    if (not chapter.volume_number and 
                        ch_num > (total_volumes - 5) * chapters_per_volume):  # Chapitres récents
                        orphan_chapters.append(chapter)
                        chapters_included.append(float(ch_num))
                
                # Déterminer le statut du volume
                volume_status = VolumeStatus.COLLECTING
                if len(volume_chapters) >= chapters_per_volume * 0.8:  # 80% des chapitres
                    volume_status = VolumeStatus.COMPLETE
                elif len(volume_chapters) > 0:
                    volume_status = VolumeStatus.COLLECTING
                else:
                    volume_status = VolumeStatus.EXPECTED  # Pas encore de chapitres
                
                # Créer le volume
                volume = Volume(
                    volume_number=volume_num,
                    chapters_range=f"{start_chapter}-{end_chapter}",
                    chapters_included=sorted(chapters_included) if chapters_included else [],
                    status=volume_status,
                    release_date=await self._estimate_volume_release_date(volume_chapters + orphan_chapters)
                )
                
                volumes.append(volume)
            
            logger.info(f"Structure complète générée: {len(volumes)} volumes (1-{total_volumes})")
            return volumes
            
        except Exception as e:
            logger.error(f"Erreur génération structure complète: {str(e)}")
            # Fallback vers méthode séquentielle classique
            return await self._group_sequentially(chapters, config)
    
    async def _group_by_volume_hints(self, chapters: List[Chapter], 
                                   pattern_info: Dict[str, Any]) -> List[Volume]:
        """Groupe chapitres basé sur indices volumes détectés"""
        volumes = []
        volume_groups = defaultdict(list)
        
        try:
            # Regrouper chapitres par volume indiqué
            for chapter in chapters:
                volume_num = None
                
                # Chercher volume dans indices détectés
                for ch_num, vol_num in pattern_info['volume_indicators']:
                    if abs(ch_num - chapter.chapter_number) < 0.1:  # Même chapitre
                        volume_num = vol_num
                        break
                
                # Si pas trouvé, estimer basé sur numérotation
                if volume_num is None:
                    volume_num = max(1, int(chapter.chapter_number) // 10)
                
                volume_groups[volume_num].append(chapter)
            
            # Créer volumes
            for vol_num, vol_chapters in volume_groups.items():
                if vol_chapters:  # Seulement si chapitres présents
                    vol_chapters.sort(key=lambda c: c.chapter_number)
                    
                    start_ch = int(vol_chapters[0].chapter_number)
                    end_ch = int(vol_chapters[-1].chapter_number)
                    
                    volume = Volume(
                        volume_number=vol_num,
                        chapters_range=f"{start_ch}-{end_ch}",
                        chapters_included=[c.chapter_number for c in vol_chapters],
                        status=VolumeStatus.COLLECTING,
                        release_date=await self._estimate_volume_release_date(vol_chapters)
                    )
                    volumes.append(volume)
            
            return sorted(volumes, key=lambda v: v.volume_number)
            
        except Exception as e:
            logger.error(f"Erreur regroupement par indices: {str(e)}")
            return []
    
    async def _group_sequentially(self, chapters: List[Chapter], 
                                config: Dict[str, Any]) -> List[Volume]:
        """Groupe chapitres séquentiellement par taille fixe"""
        volumes = []
        chapters_per_volume = config['chapters_per_volume']
        volume_threshold = config['volume_threshold']
        
        try:
            # Filtrer chapitres principaux (ignorer .5, extras, etc.)
            main_chapters = []
            special_chapters = []
            
            for chapter in chapters:
                if chapter.chapter_number == int(chapter.chapter_number):
                    main_chapters.append(chapter)
                else:
                    special_chapters.append(chapter)
            
            # Regrouper chapitres principaux
            current_volume = 1
            for i in range(0, len(main_chapters), chapters_per_volume):
                chunk = main_chapters[i:i + chapters_per_volume]
                
                if len(chunk) >= volume_threshold or i + chapters_per_volume >= len(main_chapters):
                    # Créer volume
                    start_ch = int(chunk[0].chapter_number)
                    end_ch = int(chunk[-1].chapter_number)
                    
                    # Ajouter chapitres spéciaux dans la range
                    volume_chapters = chunk.copy()
                    for special in special_chapters:
                        if start_ch <= special.chapter_number <= end_ch:
                            volume_chapters.append(special)
                    
                    volume = Volume(
                        volume_number=current_volume,
                        chapters_range=f"{start_ch}-{end_ch}",
                        chapters_included=[c.chapter_number for c in volume_chapters],
                        status=VolumeStatus.COLLECTING,
                        release_date=await self._estimate_volume_release_date(volume_chapters)
                    )
                    volumes.append(volume)
                    current_volume += 1
            
            return volumes
            
        except Exception as e:
            logger.error(f"Erreur regroupement séquentiel: {str(e)}")
            return []
    
    async def _optimize_grouping(self, volumes: List[Volume], 
                               all_chapters: List[Chapter]) -> List[Volume]:
        """Optimise le regroupement final"""
        optimized_volumes = []
        
        try:
            for volume in volumes:
                # Vérifier cohérence taille
                if len(volume.chapters_included) < 5:
                    # Volume trop petit, essayer fusion avec suivant
                    continue
                
                # Vérifier gaps dans numérotation
                sorted_chapters = sorted(volume.chapters_included)
                has_major_gaps = False
                
                for i in range(1, len(sorted_chapters)):
                    if sorted_chapters[i] - sorted_chapters[i-1] > 3:  # Gap > 3
                        has_major_gaps = True
                        break
                
                if has_major_gaps:
                    # Recalculer range sans gaps
                    volume.chapters_range = await self._recalculate_range(sorted_chapters)
                
                optimized_volumes.append(volume)
            
            return optimized_volumes
            
        except Exception as e:
            logger.error(f"Erreur optimisation regroupement: {str(e)}")
            return volumes
    
    async def _find_continuous_sequence(self, chapters: List[Chapter]) -> List[Chapter]:
        """Trouve la plus longue séquence continue de chapitres"""
        if not chapters:
            return []
        
        # Trier par numéro
        sorted_chapters = sorted(chapters, key=lambda c: c.chapter_number)
        
        longest_sequence = []
        current_sequence = [sorted_chapters[0]]
        
        for i in range(1, len(sorted_chapters)):
            prev_num = sorted_chapters[i-1].chapter_number
            curr_num = sorted_chapters[i].chapter_number
            
            # Considérer comme continu si différence <= 1.5 (pour gérer .5)
            if curr_num - prev_num <= 1.5:
                current_sequence.append(sorted_chapters[i])
            else:
                # Fin séquence, vérifier si plus longue
                if len(current_sequence) > len(longest_sequence):
                    longest_sequence = current_sequence.copy()
                
                # Commencer nouvelle séquence
                current_sequence = [sorted_chapters[i]]
        
        # Vérifier dernière séquence
        if len(current_sequence) > len(longest_sequence):
            longest_sequence = current_sequence
        
        return longest_sequence
    
    async def _estimate_volume_release_date(self, chapters: List[Chapter]) -> Optional[datetime]:
        """Estime la date de sortie d'un volume basé sur ses chapitres"""
        # Utiliser date du dernier chapitre + délai standard
        released_chapters = [c for c in chapters if c.release_date and c.status == "released"]
        
        if released_chapters:
            latest_date = max(c.release_date for c in released_chapters)
            # Ajouter ~3 mois de délai standard pour publication volume
            return latest_date + timedelta(days=90)
        
        return None
    
    async def _recalculate_range(self, chapter_numbers: List[float]) -> str:
        """Recalcule la range en gérant les gaps"""
        if not chapter_numbers:
            return ""
        
        sorted_nums = sorted(chapter_numbers)
        
        # Trouver séquences continues
        sequences = []
        current_seq = [sorted_nums[0]]
        
        for i in range(1, len(sorted_nums)):
            if sorted_nums[i] - sorted_nums[i-1] <= 1.5:
                current_seq.append(sorted_nums[i])
            else:
                sequences.append(current_seq)
                current_seq = [sorted_nums[i]]
        
        sequences.append(current_seq)
        
        # Formater range
        if len(sequences) == 1:
            # Une séquence continue
            start = int(sequences[0][0])
            end = int(sequences[0][-1])
            return f"{start}-{end}"
        else:
            # Multiples séquences, prendre globale
            start = int(sorted_nums[0])
            end = int(sorted_nums[-1])
            return f"{start}-{end}"