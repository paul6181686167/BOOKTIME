#!/usr/bin/env python3
"""
🚀 ULTRA HARVEST 100K AUTOEXPANSION OPENLIBRARY
Script avancé pour l'expansion massive des séries BOOKTIME

Fonctionnalités :
- Traitement du fichier wikidata_new_series_discovery.json
- Ajout séries Robert Muchamore (CHERUB, Henderson's Boys)
- Ajout série Red Rising (Pierce Brown)
- Expansion ultra-rapide 100k+ séries OpenLibrary
- Sauvegarde automatique avec backup
- Statistiques détaillées

Utilisation :
python ultra_harvest_100k_expansion.py --wikidata --muchamore --red-rising --expansion-limit=1000
"""

import asyncio
import aiohttp
import json
import re
import logging
from typing import List, Dict, Optional, Set
from datetime import datetime
from pathlib import Path
import argparse
import uuid

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/ultra_harvest_100k.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UltraHarvest100kExpansion:
    """Expansion massive des séries avec méthode Ultra Harvest 100k"""
    
    def __init__(self):
        self.session = None
        self.series_database_path = Path('/app/backend/data/extended_series_database.json')
        self.wikidata_file_path = Path('/app/backend/wikidata_new_series_discovery.json')
        self.backup_dir = Path('/app/backend/data/backups')
        self.backup_dir.mkdir(exist_ok=True)
        
        self.stats = {
            'wikidata_processed': 0,
            'wikidata_added': 0,
            'muchamore_added': 0,
            'red_rising_added': 0,
            'expansion_processed': 0,
            'expansion_added': 0,
            'total_added': 0,
            'duplicates_skipped': 0,
            'errors': 0
        }
        
        self.existing_series = set()
        self.new_series = []
    
    async def __aenter__(self):
        """Initialisation session async"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'BOOKTIME-UltraHarvest/2.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Fermeture session"""
        if self.session:
            await self.session.close()
    
    def load_existing_series(self) -> Set[str]:
        """Charger les séries existantes pour éviter les doublons"""
        try:
            if not self.series_database_path.exists():
                logger.warning("Base de données des séries non trouvée, création d'une nouvelle")
                return set()
            
            with open(self.series_database_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            
            existing_names = set()
            for series in existing_data:
                existing_names.add(series['name'].lower().strip())
                # Ajouter variations
                for variation in series.get('variations', []):
                    existing_names.add(variation.lower().strip())
            
            logger.info(f"✅ Chargé {len(existing_names)} noms/variations de séries existantes")
            return existing_names
        
        except Exception as e:
            logger.error(f"❌ Erreur chargement séries existantes: {e}")
            return set()
    
    def is_duplicate(self, series_name: str) -> bool:
        """Vérifier si une série est un doublon"""
        name_lower = series_name.lower().strip()
        
        # Vérification exacte
        if name_lower in self.existing_series:
            return True
        
        # Vérification similarité
        name_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', name_lower))
        
        for existing_name in self.existing_series:
            existing_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', existing_name))
            
            if len(name_words) > 0 and len(existing_words) > 0:
                common_words = name_words.intersection(existing_words)
                similarity = len(common_words) / max(len(name_words), len(existing_words))
                
                if similarity > 0.85:  # Seuil élevé pour éviter faux positifs
                    return True
        
        return False
    
    def create_backup(self):
        """Créer une sauvegarde de la base de données actuelle"""
        try:
            if not self.series_database_path.exists():
                logger.info("Aucune base existante à sauvegarder")
                return
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"extended_series_database_backup_ultraharvest_{timestamp}.json"
            
            import shutil
            shutil.copy2(self.series_database_path, backup_file)
            
            logger.info(f"✅ Sauvegarde créée: {backup_file}")
        
        except Exception as e:
            logger.error(f"❌ Erreur création sauvegarde: {e}")
    
    def process_wikidata_discovery(self) -> int:
        """Traiter le fichier wikidata_new_series_discovery.json"""
        try:
            if not self.wikidata_file_path.exists():
                logger.warning("Fichier wikidata_new_series_discovery.json non trouvé")
                return 0
            
            with open(self.wikidata_file_path, 'r', encoding='utf-8') as f:
                wikidata_data = json.load(f)
            
            new_series_data = wikidata_data.get('new_series', [])
            logger.info(f"🔍 Traitement de {len(new_series_data)} séries Wikidata")
            
            added_count = 0
            for series_data in new_series_data:
                self.stats['wikidata_processed'] += 1
                
                series_name = series_data.get('name', '').strip()
                if not series_name or self.is_duplicate(series_name):
                    self.stats['duplicates_skipped'] += 1
                    continue
                
                # Conversion au format BOOKTIME
                booktime_series = {
                    'name': series_name,
                    'authors': [series_data.get('author', 'Unknown')],
                    'category': self.map_wikidata_category(series_data.get('genre', '')),
                    'volumes': 1,  # Sera mis à jour par recherche
                    'keywords': self.extract_keywords_from_wikidata(series_data),
                    'variations': self.generate_variations(series_name),
                    'first_published': None,
                    'status': series_data.get('status', 'ongoing'),
                    'description': series_data.get('description', ''),
                    'source': 'wikidata_discovery',
                    'wikidata_id': series_data.get('wikidata_id'),
                    'subjects': [series_data.get('genre', '')],
                    'languages': ['en', 'fr'],
                    'translations': {
                        'en': series_name,
                        'fr': series_name
                    },
                    'ultra_harvest_info': {
                        'processed_date': datetime.now().isoformat(),
                        'source_file': 'wikidata_new_series_discovery.json'
                    }
                }
                
                self.new_series.append(booktime_series)
                self.existing_series.add(series_name.lower().strip())
                added_count += 1
                self.stats['wikidata_added'] += 1
            
            logger.info(f"✅ Ajouté {added_count} séries depuis Wikidata")
            return added_count
        
        except Exception as e:
            logger.error(f"❌ Erreur traitement Wikidata: {e}")
            self.stats['errors'] += 1
            return 0
    
    def map_wikidata_category(self, genre: str) -> str:
        """Mapper les genres Wikidata vers les catégories BOOKTIME"""
        genre_lower = genre.lower()
        
        if any(keyword in genre_lower for keyword in ['fantasy', 'science-fiction', 'littérature', 'roman', 'fiction']):
            return 'roman'
        elif any(keyword in genre_lower for keyword in ['comic', 'graphic', 'bd', 'bande dessinée']):
            return 'bd'
        elif any(keyword in genre_lower for keyword in ['manga', 'anime', 'japanese']):
            return 'manga'
        else:
            return 'roman'  # Défaut
    
    def extract_keywords_from_wikidata(self, series_data: Dict) -> List[str]:
        """Extraire mots-clés depuis données Wikidata"""
        keywords = []
        
        # Mots-clés du nom
        name = series_data.get('name', '')
        name_words = re.findall(r'\b[a-zA-Z]{3,}\b', name.lower())
        keywords.extend(name_words[:5])
        
        # Mots-clés de l'auteur
        author = series_data.get('author', '')
        author_words = re.findall(r'\b[a-zA-Z]{3,}\b', author.lower())
        keywords.extend(author_words[:2])
        
        # Mots-clés du genre
        genre = series_data.get('genre', '')
        genre_words = re.findall(r'\b[a-zA-Z]{3,}\b', genre.lower())
        keywords.extend(genre_words[:2])
        
        # Déduplication
        return list(set(keywords))
    
    def add_robert_muchamore_series(self) -> int:
        """Ajouter les séries de Robert Muchamore"""
        try:
            muchamore_series = [
                {
                    'name': 'CHERUB',
                    'authors': ['Robert Muchamore'],
                    'category': 'roman',
                    'volumes': 17,
                    'keywords': ['cherub', 'espionnage', 'adolescent', 'agent', 'mission', 'robert'],
                    'variations': ['CHERUB', 'Cherub', 'CHERUB Series'],
                    'first_published': 2004,
                    'status': 'completed',
                    'description': 'Série d\'espionnage mettant en scène des adolescents agents secrets',
                    'source': 'manual_muchamore',
                    'subjects': ['spy fiction', 'young adult', 'action', 'thriller'],
                    'languages': ['en', 'fr'],
                    'translations': {
                        'en': 'CHERUB',
                        'fr': 'CHERUB'
                    },
                    'ultra_harvest_info': {
                        'processed_date': datetime.now().isoformat(),
                        'manual_addition': True,
                        'user_requested': True
                    }
                },
                {
                    'name': 'Henderson\'s Boys',
                    'authors': ['Robert Muchamore'],
                    'category': 'roman',
                    'volumes': 7,
                    'keywords': ['henderson', 'boys', 'guerre', 'mondiale', 'resistance', 'robert'],
                    'variations': ['Henderson\'s Boys', 'Hendersons Boys', 'Henderson Boys'],
                    'first_published': 2009,
                    'status': 'completed',
                    'description': 'Série se déroulant pendant la Seconde Guerre mondiale, préquelle à CHERUB',
                    'source': 'manual_muchamore',
                    'subjects': ['world war 2', 'historical fiction', 'young adult', 'resistance'],
                    'languages': ['en', 'fr'],
                    'translations': {
                        'en': 'Henderson\'s Boys',
                        'fr': 'Henderson\'s Boys'
                    },
                    'ultra_harvest_info': {
                        'processed_date': datetime.now().isoformat(),
                        'manual_addition': True,
                        'user_requested': True
                    }
                }
            ]
            
            added_count = 0
            for series_data in muchamore_series:
                if not self.is_duplicate(series_data['name']):
                    self.new_series.append(series_data)
                    self.existing_series.add(series_data['name'].lower().strip())
                    added_count += 1
                    self.stats['muchamore_added'] += 1
                else:
                    self.stats['duplicates_skipped'] += 1
            
            logger.info(f"✅ Ajouté {added_count} séries de Robert Muchamore")
            return added_count
        
        except Exception as e:
            logger.error(f"❌ Erreur ajout séries Muchamore: {e}")
            self.stats['errors'] += 1
            return 0
    
    def add_red_rising_series(self) -> int:
        """Ajouter la série Red Rising"""
        try:
            red_rising_series = {
                'name': 'Red Rising',
                'authors': ['Pierce Brown'],
                'category': 'roman',
                'volumes': 6,  # Mise à jour 2025
                'keywords': ['red', 'rising', 'dystopia', 'science', 'fiction', 'pierce', 'brown'],
                'variations': ['Red Rising', 'Red Rising Saga', 'Red Rising Series'],
                'first_published': 2014,
                'status': 'ongoing',
                'description': 'Saga science-fiction dystopique de Pierce Brown',
                'source': 'manual_red_rising',
                'subjects': ['science fiction', 'dystopian', 'space opera', 'young adult'],
                'languages': ['en', 'fr'],
                'translations': {
                    'en': 'Red Rising',
                    'fr': 'Red Rising'
                },
                'ultra_harvest_info': {
                    'processed_date': datetime.now().isoformat(),
                    'manual_addition': True,
                    'user_requested': True,
                    'volumes_info': {
                        'total_planned': 7,
                        'published': 6,
                        'next_release': 'Red God (2026)'
                    }
                }
            }
            
            if not self.is_duplicate(red_rising_series['name']):
                self.new_series.append(red_rising_series)
                self.existing_series.add(red_rising_series['name'].lower().strip())
                self.stats['red_rising_added'] += 1
                logger.info("✅ Ajouté série Red Rising")
                return 1
            else:
                self.stats['duplicates_skipped'] += 1
                logger.info("⏭️ Série Red Rising déjà existante")
                return 0
        
        except Exception as e:
            logger.error(f"❌ Erreur ajout série Red Rising: {e}")
            self.stats['errors'] += 1
            return 0
    
    async def ultra_expansion_openlibrary(self, limit: int = 1000) -> int:
        """Expansion ultra-rapide depuis OpenLibrary"""
        try:
            logger.info(f"🚀 Démarrage Ultra Expansion OpenLibrary (limite: {limit})")
            
            # Termes de recherche optimisés pour séries
            search_terms = [
                'book series fantasy', 'manga series', 'comic series', 'novel series',
                'fantasy trilogy', 'science fiction series', 'mystery series',
                'thriller series', 'adventure series', 'romance series',
                'light novel series', 'graphic novel series', 'dystopian series',
                'urban fantasy series', 'epic fantasy series', 'space opera series'
            ]
            
            added_count = 0
            processed_count = 0
            
            for term in search_terms[:8]:  # Limite à 8 termes pour éviter rate limiting
                try:
                    logger.info(f"🔍 Recherche: {term}")
                    
                    url = "https://openlibrary.org/search.json"
                    params = {
                        'q': term,
                        'limit': limit // len(search_terms[:8]) + 10,
                        'has_fulltext': 'true',
                        'sort': 'rating'
                    }
                    
                    async with self.session.get(url, params=params) as response:
                        if response.status != 200:
                            logger.error(f"❌ Erreur recherche {term}: {response.status}")
                            continue
                        
                        data = await response.json()
                        works = data.get('docs', [])
                        
                        for work in works:
                            processed_count += 1
                            self.stats['expansion_processed'] += 1
                            
                            if processed_count >= limit:
                                break
                            
                            series_info = self.parse_openlibrary_work(work)
                            if series_info and not self.is_duplicate(series_info['name']):
                                self.new_series.append(series_info)
                                self.existing_series.add(series_info['name'].lower().strip())
                                added_count += 1
                                self.stats['expansion_added'] += 1
                            else:
                                self.stats['duplicates_skipped'] += 1
                    
                    # Rate limiting
                    await asyncio.sleep(0.5)
                    
                    if processed_count >= limit:
                        break
                
                except Exception as e:
                    logger.error(f"❌ Erreur recherche terme {term}: {e}")
                    continue
            
            logger.info(f"✅ Ultra Expansion terminée: {added_count} séries ajoutées")
            return added_count
        
        except Exception as e:
            logger.error(f"❌ Erreur Ultra Expansion: {e}")
            self.stats['errors'] += 1
            return 0
    
    def parse_openlibrary_work(self, work: Dict) -> Optional[Dict]:
        """Parser une œuvre OpenLibrary pour extraire une série"""
        try:
            title = work.get('title', '').strip()
            authors = work.get('author_name', [])
            if not title or not authors:
                return None
            
            # Patterns de détection de série
            series_patterns = [
                r'(.+?)\s+(?:Book|Volume|Vol\.?|Tome|#)\s*(\d+)',
                r'(.+?)\s+(\d+)(?:st|nd|rd|th)?\s*(?:Book|Volume|Tome)',
                r'(.+?):\s*(.+)',
                r'(.+?)\s+\((.+?)\s+#\d+\)',
                r'(.+?)\s+-\s+(.+)'
            ]
            
            series_name = None
            for pattern in series_patterns:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    series_name = match.group(1).strip()
                    break
            
            if not series_name:
                # Vérification indicateurs série
                series_indicators = [
                    'saga', 'series', 'cycle', 'chronicles', 'adventures',
                    'trilogy', 'quartet', 'collection', 'omnibus'
                ]
                
                if any(indicator in title.lower() for indicator in series_indicators):
                    series_name = title
                else:
                    return None
            
            # Métadonnées
            subjects = work.get('subject', [])
            first_published = work.get('first_publish_year')
            
            # Détection catégorie
            category = self.detect_category_from_subjects(subjects)
            
            return {
                'name': series_name,
                'authors': authors[:2],  # Limite à 2 auteurs
                'category': category,
                'volumes': 1,  # Sera agrégé plus tard
                'keywords': self.extract_keywords_from_work(title, subjects),
                'variations': self.generate_variations(series_name),
                'first_published': first_published,
                'status': 'ongoing',
                'source': 'ultra_expansion_openlibrary',
                'ol_key': work.get('key'),
                'description': '',
                'subjects': subjects[:8],
                'languages': work.get('language', ['en']),
                'translations': {
                    'en': series_name,
                    'fr': series_name
                },
                'ultra_harvest_info': {
                    'processed_date': datetime.now().isoformat(),
                    'method': 'ultra_expansion_100k',
                    'confidence_score': 85
                }
            }
        
        except Exception as e:
            logger.error(f"❌ Erreur parsing work: {e}")
            return None
    
    def detect_category_from_subjects(self, subjects: List[str]) -> str:
        """Détecter catégorie depuis les sujets"""
        text = ' '.join(subjects).lower()
        
        # Patterns manga
        if any(keyword in text for keyword in ['manga', 'anime', 'japanese comics', 'light novel']):
            return 'manga'
        
        # Patterns BD
        if any(keyword in text for keyword in ['comic', 'graphic novel', 'superhero', 'cartoons']):
            return 'bd'
        
        # Défaut roman
        return 'roman'
    
    def extract_keywords_from_work(self, title: str, subjects: List[str]) -> List[str]:
        """Extraire mots-clés depuis un work OpenLibrary"""
        keywords = []
        
        # Mots-clés du titre
        title_words = re.findall(r'\b[a-zA-Z]{3,}\b', title.lower())
        keywords.extend(title_words[:5])
        
        # Mots-clés des sujets
        for subject in subjects[:3]:
            subject_words = re.findall(r'\b[a-zA-Z]{3,}\b', subject.lower())
            keywords.extend(subject_words[:2])
        
        # Déduplication et nettoyage
        common_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all',
            'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day',
            'book', 'novel', 'story', 'series', 'volume', 'tome'
        }
        
        keywords = [kw for kw in list(set(keywords)) if kw not in common_words]
        return keywords[:10]
    
    def generate_variations(self, series_name: str) -> List[str]:
        """Générer variations nom série"""
        variations = [series_name]
        
        # Variations avec/sans articles
        articles = ['the', 'a', 'an', 'le', 'la', 'les', 'un', 'une', 'des']
        for article in articles:
            variations.append(f"{article} {series_name}")
            variations.append(f"{article.title()} {series_name}")
        
        # Variations casse
        variations.extend([
            series_name.lower(),
            series_name.upper(),
            series_name.title()
        ])
        
        return list(set(variations))
    
    def save_series_database(self) -> bool:
        """Sauvegarder la base de données mise à jour"""
        try:
            # Charger séries existantes
            existing_series = []
            if self.series_database_path.exists():
                with open(self.series_database_path, 'r', encoding='utf-8') as f:
                    existing_series = json.load(f)
            
            # Ajouter nouvelles séries
            updated_series = existing_series + self.new_series
            
            # Création dossier parent si nécessaire
            self.series_database_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Sauvegarde avec formatage
            with open(self.series_database_path, 'w', encoding='utf-8') as f:
                json.dump(updated_series, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Base de données sauvegardée: {len(updated_series)} séries total")
            return True
        
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde base: {e}")
            return False
    
    def generate_report(self) -> str:
        """Générer rapport d'exécution"""
        total_added = sum([
            self.stats['wikidata_added'],
            self.stats['muchamore_added'],
            self.stats['red_rising_added'],
            self.stats['expansion_added']
        ])
        
        report = f"""
🚀 ULTRA HARVEST 100K AUTOEXPANSION - RAPPORT FINAL
==================================================

📊 STATISTIQUES GÉNÉRALES
- Total séries ajoutées: {total_added}
- Doublons ignorés: {self.stats['duplicates_skipped']}
- Erreurs rencontrées: {self.stats['errors']}

📋 DÉTAIL PAR SOURCE
- Wikidata discovery: {self.stats['wikidata_added']} ({self.stats['wikidata_processed']} traitées)
- Robert Muchamore: {self.stats['muchamore_added']} (CHERUB + Henderson's Boys)
- Red Rising: {self.stats['red_rising_added']} (Pierce Brown)
- Ultra Expansion: {self.stats['expansion_added']} ({self.stats['expansion_processed']} traitées)

🎯 SÉRIES AJOUTÉES TOP 10
"""
        
        # Top 10 par nombre de volumes
        top_series = sorted(self.new_series, key=lambda x: x.get('volumes', 0), reverse=True)[:10]
        
        for i, series in enumerate(top_series, 1):
            authors = ', '.join(series['authors'][:2])
            volumes = series.get('volumes', 1)
            report += f"{i}. {series['name']} - {authors} ({volumes} vol, {series['category']})\n"
        
        report += f"""
📊 RÉPARTITION PAR CATÉGORIE
"""
        
        # Comptage par catégorie
        categories = {}
        for series in self.new_series:
            cat = series['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        for cat, count in sorted(categories.items()):
            report += f"- {cat.title()}: {count} séries\n"
        
        report += f"""
⚡ PERFORMANCE
- Durée traitement: {datetime.now().strftime('%H:%M:%S')}
- Séries par seconde: {total_added / max(1, 60):.1f}
- Taux de succès: {(total_added / max(1, total_added + self.stats['duplicates_skipped'])) * 100:.1f}%

🚀 PROCHAINES ÉTAPES
- Redémarrage services recommandé
- Vérification détection automatique
- Test masquage intelligent
- Validation interface utilisateur

📁 FICHIERS GÉNÉRÉS
- Base de données: {self.series_database_path}
- Sauvegardes: {self.backup_dir}
- Logs: /app/logs/ultra_harvest_100k.log
"""
        
        return report
    
    async def run_ultra_harvest(self, 
                              process_wikidata: bool = True,
                              add_muchamore: bool = True,
                              add_red_rising: bool = True,
                              expansion_limit: int = 1000) -> Dict:
        """Exécution complète Ultra Harvest 100k"""
        
        start_time = datetime.now()
        logger.info("🚀 DÉMARRAGE ULTRA HARVEST 100K AUTOEXPANSION")
        
        # Étape 1: Chargement séries existantes
        self.existing_series = self.load_existing_series()
        
        # Étape 2: Création sauvegarde
        self.create_backup()
        
        total_added = 0
        
        # Étape 3: Traitement Wikidata
        if process_wikidata:
            logger.info("📊 PHASE 1: Traitement Wikidata Discovery")
            wikidata_added = self.process_wikidata_discovery()
            total_added += wikidata_added
        
        # Étape 4: Ajout séries Muchamore
        if add_muchamore:
            logger.info("📚 PHASE 2: Ajout séries Robert Muchamore")
            muchamore_added = self.add_robert_muchamore_series()
            total_added += muchamore_added
        
        # Étape 5: Ajout série Red Rising
        if add_red_rising:
            logger.info("🔴 PHASE 3: Ajout série Red Rising")
            red_rising_added = self.add_red_rising_series()
            total_added += red_rising_added
        
        # Étape 6: Ultra Expansion OpenLibrary
        if expansion_limit > 0:
            logger.info("🌐 PHASE 4: Ultra Expansion OpenLibrary")
            expansion_added = await self.ultra_expansion_openlibrary(expansion_limit)
            total_added += expansion_added
        
        # Étape 7: Sauvegarde
        logger.info("💾 PHASE 5: Sauvegarde base de données")
        save_success = self.save_series_database()
        
        # Étape 8: Génération rapport
        report = self.generate_report()
        
        # Sauvegarde rapport
        report_file = Path(f'/app/logs/ultra_harvest_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        duration = datetime.now() - start_time
        logger.info(f"✅ ULTRA HARVEST TERMINÉ: {total_added} séries ajoutées en {duration}")
        
        return {
            'success': save_success,
            'total_added': total_added,
            'duration': str(duration),
            'report_file': str(report_file),
            'stats': self.stats,
            'new_series_count': len(self.new_series)
        }


async def main():
    """Fonction principale CLI"""
    parser = argparse.ArgumentParser(description='Ultra Harvest 100k AutoExpansion')
    parser.add_argument('--wikidata', action='store_true', help='Traiter fichier Wikidata')
    parser.add_argument('--muchamore', action='store_true', help='Ajouter séries Robert Muchamore')
    parser.add_argument('--red-rising', action='store_true', help='Ajouter série Red Rising')
    parser.add_argument('--expansion-limit', type=int, default=1000, help='Limite expansion OpenLibrary')
    parser.add_argument('--all', action='store_true', help='Activer toutes les options')
    
    args = parser.parse_args()
    
    # Si --all, activer toutes les options
    if args.all:
        args.wikidata = True
        args.muchamore = True
        args.red_rising = True
    
    # Vérifier qu'au moins une option est activée
    if not any([args.wikidata, args.muchamore, args.red_rising, args.expansion_limit > 0]):
        print("❌ Au moins une option doit être activée")
        parser.print_help()
        return 1
    
    # Création dossiers
    Path('/app/logs').mkdir(exist_ok=True)
    Path('/app/backend/data').mkdir(parents=True, exist_ok=True)
    
    # Exécution
    async with UltraHarvest100kExpansion() as harvester:
        result = await harvester.run_ultra_harvest(
            process_wikidata=args.wikidata,
            add_muchamore=args.muchamore,
            add_red_rising=args.red_rising,
            expansion_limit=args.expansion_limit
        )
        
        print(f"\n🎯 RÉSULTATS ULTRA HARVEST 100K")
        print(f"✅ Séries ajoutées: {result['total_added']}")
        print(f"⏱️ Durée: {result['duration']}")
        print(f"📊 Détail: {result['stats']}")
        print(f"📄 Rapport: {result['report_file']}")
        
        if result['success']:
            print(f"\n🚀 {result['total_added']} nouvelles séries ajoutées à BOOKTIME !")
            print(f"🔄 Redémarrage services recommandé")
        else:
            print(f"\n❌ Erreur lors de la sauvegarde")
            return 1
    
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))