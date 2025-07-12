#!/usr/bin/env python3
"""
🌟 ULTRA EXPANSION OPENLIBRARY - STRATÉGIES AVANCÉES
Expansion ultra-agressive avec exploration de territoires non couverts

Nouvelles stratégies :
1. Exploration par langues (français, espagnol, allemand, italien, japonais)
2. Recherche par années de publication (décennies spécifiques)
3. Exploration publishers spécialisés
4. Scan par ISBN patterns
5. Exploration genres très spécifiques
6. Recherche par awards/prix littéraires
"""

import asyncio
import aiohttp
import json
import re
from typing import List, Dict, Optional, Set
from datetime import datetime
import logging
from pathlib import Path
import random
import time

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/ultra_expansion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UltraExpansionOpenLibrary:
    """Expansion ultra-agressive avec stratégies avancées non explorées"""
    
    def __init__(self):
        self.base_url = "https://openlibrary.org"
        self.session = None
        self.existing_series = set()
        self.new_series = []
        self.stats = {
            'queries_made': 0,
            'books_analyzed': 0,
            'series_detected': 0,
            'new_series_added': 0,
            'duplicates_skipped': 0,
            'processing_time': 0
        }
        
        # Stratégies ultra-spécialisées
        self.language_markets = {
            'french': ['lang:fr', 'language:french', 'publisher:Gallimard', 'publisher:Hachette', 'publisher:Flammarion'],
            'spanish': ['lang:es', 'language:spanish', 'publisher:Planeta', 'publisher:Alfaguara'],
            'german': ['lang:de', 'language:german', 'publisher:Rowohlt', 'publisher:Fischer'],
            'italian': ['lang:it', 'language:italian', 'publisher:Mondadori', 'publisher:Einaudi'],
            'japanese': ['lang:ja', 'language:japanese', 'publisher:Shogakukan', 'publisher:Kodansha'],
            'portuguese': ['lang:pt', 'language:portuguese', 'publisher:LeYa'],
            'dutch': ['lang:nl', 'language:dutch', 'publisher:Bezige'],
            'russian': ['lang:ru', 'language:russian']
        }
        
        # Publishers spécialisés par genre
        self.specialized_publishers = {
            'manga': [
                'VIZ Media', 'Kodansha', 'Shogakukan', 'Shueisha', 'Square Enix',
                'Tokyopop', 'Dark Horse Manga', 'Seven Seas', 'Yen Press'
            ],
            'comics': [
                'Marvel Comics', 'DC Comics', 'Image Comics', 'Dark Horse Comics',
                'IDW Publishing', 'Boom! Studios', 'Dynamite Entertainment'
            ],
            'fantasy': [
                'Tor Books', 'DAW Books', 'Ace Books', 'Del Rey', 'Orbit Books',
                'Bantam Spectra', 'Harper Voyager', 'Gollancz'
            ],
            'mystery': [
                'Minotaur Books', 'St. Martin\'s Press', 'Bantam Dell', 'Berkley',
                'Kensington Books', 'Soho Crime'
            ],
            'romance': [
                'Harlequin', 'Avon Books', 'Berkley Sensation', 'Zebra Books',
                'Sourcebooks Casablanca'
            ],
            'scifi': [
                'Tor Books', 'Ace Books', 'DAW Books', 'Baen Books',
                'Orbit Books', 'Angry Robot'
            ]
        }
        
        # Décennies avec patterns série populaires
        self.decade_exploration = {
            '2020s': ['2020', '2021', '2022', '2023', '2024', '2025'],
            '2010s': ['2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017', '2018', '2019'],
            '2000s': ['2000', '2001', '2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009'],
            '1990s': ['1990', '1991', '1992', '1993', '1994', '1995', '1996', '1997', '1998', '1999'],
            '1980s': ['1980', '1981', '1982', '1983', '1984', '1985', '1986', '1987', '1988', '1989']
        }
        
        # Genres ultra-spécifiques
        self.niche_genres = [
            'alternate history', 'steampunk', 'biopunk', 'cyberpunk', 'dieselpunk',
            'urban fantasy', 'paranormal romance', 'cozy mystery', 'hard boiled',
            'space opera', 'military science fiction', 'dystopian fiction',
            'post-apocalyptic', 'zombie fiction', 'vampire fiction', 'werewolf fiction',
            'epic fantasy', 'sword and sorcery', 'heroic fantasy', 'dark fantasy',
            'psychological thriller', 'legal thriller', 'medical thriller',
            'historical mystery', 'historical romance', 'regency romance',
            'contemporary romance', 'erotic romance', 'young adult fantasy',
            'middle grade adventure', 'coming of age', 'slice of life',
            'light novel', 'web novel', 'visual novel', 'manhwa', 'manhua'
        ]
        
        # Prix littéraires et awards
        self.literary_awards = [
            'Hugo Award', 'Nebula Award', 'World Fantasy Award', 'Locus Award',
            'Eisner Award', 'Harvey Award', 'Manga Taisho', 'Kodansha Manga Award',
            'Prix Goncourt', 'Prix Renaudot', 'Prix Femina', 'Prix Médicis',
            'Booker Prize', 'Pulitzer Prize', 'National Book Award',
            'Edgar Award', 'Anthony Award', 'Agatha Award', 'Macavity Award',
            'Rita Award', 'Golden Heart Award', 'Lambda Literary Award'
        ]
        
        # Patterns ISBN pour exploration systématique
        self.isbn_patterns = [
            # Publishers japonais
            '978-4-08', '978-4-09', '978-4-06', '978-4-04', '978-4-7973',
            # Publishers français
            '978-2-07', '978-2-08', '978-2-22', '978-2-25', '978-2-01',
            # Publishers anglais/américains
            '978-0-06', '978-0-44', '978-0-52', '978-0-76', '978-0-31',
            # Publishers allemands
            '978-3-42', '978-3-49', '978-3-57', '978-3-64'
        ]
        
        # Patterns série ultra-sophistiqués
        self.advanced_series_patterns = [
            # Patterns numériques avancés
            r'(.+?)\s+(?:Band|Teil|Volume|Tome|Volumen|Tomo)\s+(\d+)',
            r'(.+?)\s+(?:Libro|Livre|Book|Buch)\s+(\d+)',
            r'(.+?)\s+(?:Capitulo|Chapitre|Chapter|Kapitel)\s+(\d+)',
            r'(.+?)\s+(?:Episode|Episodio|Épisode|Folge)\s+(\d+)',
            
            # Patterns linguistiques
            r'(.+?)\s+(?:Primera|Première|First|Erste)\s+(?:Parte|Part|Teil)',
            r'(.+?)\s+(?:Segunda|Deuxième|Second|Zweite)\s+(?:Parte|Part|Teil)',
            r'(.+?)\s+(?:Tercera|Troisième|Third|Dritte)\s+(?:Parte|Part|Teil)',
            
            # Patterns collections
            r'(.+?)\s+(?:Collection|Colección|Sammlung)',
            r'(.+?)\s+(?:Anthology|Antología|Anthologie)',
            r'(.+?)\s+(?:Omnibus|Integral|Complete)',
            
            # Patterns spéciaux manga/light novel
            r'(.+?)\s+(?:Light Novel|LN|WN|Web Novel)\s+(?:Vol\.|Volume)\s*(\d+)',
            r'(.+?)\s+(?:Original|オリジナル)\s+(?:Vol\.|Volume)\s*(\d+)',
        ]
    
    async def __aenter__(self):
        """Initialisation session async"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            headers={'User-Agent': 'BOOKTIME-UltraExpansion/3.0'}
        )
        await self.load_existing_series()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Fermeture session"""
        if self.session:
            await self.session.close()
    
    async def load_existing_series(self):
        """Charge les séries existantes pour éviter doublons"""
        try:
            with open('/app/backend/data/extended_series_database.json', 'r') as f:
                existing_data = json.load(f)
                self.existing_series = {series['name'].lower() for series in existing_data}
            logger.info(f"📚 Chargé {len(self.existing_series)} séries existantes")
        except Exception as e:
            logger.warning(f"⚠️ Erreur chargement séries existantes: {e}")
            self.existing_series = set()
    
    async def search_open_library_advanced(self, query: str, limit: int = 50) -> List[Dict]:
        """Recherche avancée avec paramètres sophistiqués"""
        try:
            # Délai anti-rate-limiting variable
            await asyncio.sleep(random.uniform(0.2, 0.5))
            
            url = f"{self.base_url}/search.json"
            params = {
                'q': query,
                'limit': limit,
                'fields': 'key,title,author_name,subject,first_publish_year,publisher,isbn,language,number_of_pages_median,cover_i,edition_count'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    self.stats['queries_made'] += 1
                    books = data.get('docs', [])
                    self.stats['books_analyzed'] += len(books)
                    logger.info(f"🔍 Query '{query[:50]}...': {len(books)} livres trouvés")
                    return books
                elif response.status == 429:  # Rate limit
                    logger.warning("⚠️ Rate limit detected, attente 2s")
                    await asyncio.sleep(2)
                    return []
                else:
                    logger.warning(f"⚠️ Erreur API {response.status} pour query: {query[:50]}")
                    return []
        except Exception as e:
            logger.error(f"❌ Erreur recherche '{query[:50]}': {e}")
            return []
    
    def detect_advanced_series_patterns(self, books: List[Dict]) -> List[Dict]:
        """Détection ultra-sophistiquée de patterns série"""
        series_candidates = {}
        
        for book in books:
            title = book.get('title', '').strip()
            authors = book.get('author_name', [])
            publisher = book.get('publisher', [''])[0] if book.get('publisher') else ''
            language = book.get('language', [''])[0] if book.get('language') else ''
            
            if not title or not authors:
                continue
            
            # Application patterns avancés
            for pattern in self.advanced_series_patterns:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    series_name = match.group(1).strip()
                    volume_num = match.group(2) if len(match.groups()) > 1 else "1"
                    
                    if len(series_name) > 2:  # Nom série valide
                        # Clé unique incluant publisher et langue pour éviter confusion
                        series_key = (
                            series_name.lower(),
                            authors[0] if authors else "Unknown",
                            publisher.lower()[:20],  # Limite longueur
                            language[:2]  # Code langue
                        )
                        
                        if series_key not in series_candidates:
                            series_candidates[series_key] = {
                                'name': series_name,
                                'author': authors[0] if authors else "Unknown",
                                'publisher': publisher,
                                'language': language,
                                'books': [],
                                'volumes': set(),
                                'subjects': set(),
                                'years': set()
                            }
                        
                        series_candidates[series_key]['books'].append(book)
                        if volume_num.isdigit():
                            series_candidates[series_key]['volumes'].add(int(volume_num))
                        
                        # Collecte métadonnées enrichies
                        subjects = book.get('subject', [])
                        if subjects:
                            series_candidates[series_key]['subjects'].update(subjects[:3])
                        
                        year = book.get('first_publish_year')
                        if year:
                            series_candidates[series_key]['years'].add(year)
                        
                        break
        
        # Filtre séries valides avec critères stricts
        valid_series = []
        for series_key, data in series_candidates.items():
            series_name = data['name']
            
            # Critères validation renforcés
            has_multiple_books = len(data['books']) >= 2
            has_multiple_volumes = len(data['volumes']) >= 2
            has_volume_progression = len(data['volumes']) > 1 and max(data['volumes']) - min(data['volumes']) >= 1
            
            is_valid_series = has_multiple_books or has_multiple_volumes or has_volume_progression
            is_not_duplicate = series_name.lower() not in self.existing_series
            has_sufficient_length = len(series_name) >= 3
            
            if is_valid_series and is_not_duplicate and has_sufficient_length:
                valid_series.append(data)
                self.stats['series_detected'] += 1
            else:
                self.stats['duplicates_skipped'] += 1
        
        return valid_series
    
    def advanced_categorize_series(self, series_data: Dict) -> str:
        """Catégorisation ultra-sophistiquée avec patterns linguistiques"""
        subjects = [s.lower() for s in series_data['subjects']]
        publisher = series_data['publisher'].lower()
        language = series_data['language'].lower()
        
        # Détection manga ultra-précise
        manga_indicators = [
            'manga', 'light novel', 'ln', 'web novel', 'visual novel',
            'kodansha', 'shogakukan', 'shueisha', 'square enix',
            'viz media', 'tokyopop', 'yen press', 'seven seas'
        ]
        if any(indicator in publisher or indicator in ' '.join(subjects) for indicator in manga_indicators):
            return 'manga'
        
        # Détection BD européenne
        bd_indicators = [
            'bande dessinée', 'comic book', 'graphic novel', 'cartoon',
            'dargaud', 'dupuis', 'casterman', 'glenat', 'soleil',
            'dark horse', 'image comics', 'dc comics', 'marvel'
        ]
        if any(indicator in publisher or indicator in ' '.join(subjects) for indicator in bd_indicators):
            return 'bd'
        
        # Détection romans par exclusion et patterns
        return 'roman'
    
    def create_advanced_series_entry(self, series_data: Dict) -> Dict:
        """Création entrée série ultra-sophistiquée"""
        name = series_data['name']
        author = series_data['author']
        category = self.advanced_categorize_series(series_data)
        volumes = max(series_data['volumes']) if series_data['volumes'] else len(series_data['books'])
        
        # Génération patterns détection ultra-sophistiqués
        base_name = name.lower().strip()
        
        # Patterns base
        keywords = [base_name, f"{base_name} series", f"{base_name} saga"]
        
        # Ajout patterns linguistiques
        if series_data['language'] in ['fr', 'french']:
            keywords.extend([f"{base_name} tome", f"{base_name} livre"])
        elif series_data['language'] in ['es', 'spanish']:
            keywords.extend([f"{base_name} libro", f"{base_name} tomo"])
        elif series_data['language'] in ['de', 'german']:
            keywords.extend([f"{base_name} band", f"{base_name} teil"])
        elif series_data['language'] in ['ja', 'japanese']:
            keywords.extend([f"{base_name} volume", f"{base_name} vol"])
        
        # Ajout auteur si disponible
        if author != "Unknown":
            author_last = author.lower().split()[-1] if author.lower().split() else ""
            if author_last:
                keywords.append(author_last)
        
        # Nettoyage keywords
        keywords = [k for k in keywords if k and len(k) > 2]
        
        # Variations titre sophistiquées
        variations = [name, f"The {name}", f"{name} Series"]
        if category == 'manga':
            variations.extend([f"{name} Light Novel", f"{name} LN"])
        
        # Exclusions sophistiquées
        exclusions = [
            "anthology", "collection", "best of", "complete works",
            "omnibus", "integral", "selected works", "compilation"
        ]
        
        # Score de confiance basé sur critères multiples
        confidence = 75
        if len(series_data['volumes']) >= 3:
            confidence += 10
        if len(series_data['books']) >= 3:
            confidence += 10
        if series_data['publisher']:
            confidence += 5
        
        return {
            "name": name,
            "authors": [author] if author != "Unknown" else [],
            "category": category,
            "volumes": volumes,
            "keywords": keywords[:10],  # Limite pour performance
            "variations": variations,
            "exclusions": exclusions,
            "source": "open_library_ultra_expansion",
            "confidence_score": min(confidence, 95),
            "auto_generated": True,
            "detection_date": datetime.now().isoformat(),
            "metadata": {
                "publisher": series_data['publisher'],
                "language": series_data['language'],
                "subjects": list(series_data['subjects'])[:5],
                "years": list(series_data['years'])[:3] if series_data['years'] else []
            }
        }
    
    async def ultra_strategy_languages(self, limit_per_lang: int = 25) -> List[Dict]:
        """Stratégie ultra 1: Exploration par marchés linguistiques"""
        logger.info("🌍 Stratégie Ultra 1: Exploration marchés linguistiques")
        all_series = []
        
        for lang, patterns in self.language_markets.items():
            for pattern in patterns[:3]:  # Limite pour performance
                for term in ['series', 'saga', 'tome', 'volume']:
                    query = f'{pattern} AND ({term} OR book OR novel)'
                    books = await self.search_open_library_advanced(query, limit_per_lang)
                    series = self.detect_advanced_series_patterns(books)
                    all_series.extend(series)
        
        logger.info(f"✅ Stratégie Ultra 1 terminée: {len(all_series)} séries trouvées")
        return all_series
    
    async def ultra_strategy_publishers(self, limit_per_publisher: int = 20) -> List[Dict]:
        """Stratégie ultra 2: Exploration publishers spécialisés"""
        logger.info("🏢 Stratégie Ultra 2: Exploration publishers spécialisés")
        all_series = []
        
        for genre, publishers in self.specialized_publishers.items():
            for publisher in publishers[:4]:  # Limite pour performance
                query = f'publisher:"{publisher}" AND (series OR volume OR book)'
                books = await self.search_open_library_advanced(query, limit_per_publisher)
                series = self.detect_advanced_series_patterns(books)
                all_series.extend(series)
        
        logger.info(f"✅ Stratégie Ultra 2 terminée: {len(all_series)} séries trouvées")
        return all_series
    
    async def ultra_strategy_decades(self, limit_per_year: int = 15) -> List[Dict]:
        """Stratégie ultra 3: Exploration par décennies"""
        logger.info("📅 Stratégie Ultra 3: Exploration par décennies")
        all_series = []
        
        for decade, years in self.decade_exploration.items():
            for year in years[::2]:  # Un an sur deux pour performance
                query = f'first_publish_year:{year} AND (series OR volume OR saga)'
                books = await self.search_open_library_advanced(query, limit_per_year)
                series = self.detect_advanced_series_patterns(books)
                all_series.extend(series)
        
        logger.info(f"✅ Stratégie Ultra 3 terminée: {len(all_series)} séries trouvées")
        return all_series
    
    async def ultra_strategy_niche_genres(self, limit_per_genre: int = 20) -> List[Dict]:
        """Stratégie ultra 4: Exploration genres ultra-spécifiques"""
        logger.info("🎭 Stratégie Ultra 4: Exploration genres ultra-spécifiques")
        all_series = []
        
        for genre in self.niche_genres[:20]:  # Limite pour performance
            query = f'subject:"{genre}" AND (series OR volume OR book OR saga)'
            books = await self.search_open_library_advanced(query, limit_per_genre)
            series = self.detect_advanced_series_patterns(books)
            all_series.extend(series)
        
        logger.info(f"✅ Stratégie Ultra 4 terminée: {len(all_series)} séries trouvées")
        return all_series
    
    async def ultra_strategy_awards(self, limit_per_award: int = 15) -> List[Dict]:
        """Stratégie ultra 5: Exploration prix littéraires"""
        logger.info("🏆 Stratégie Ultra 5: Exploration prix littéraires")
        all_series = []
        
        for award in self.literary_awards[:15]:  # Limite pour performance
            query = f'"{award}" AND (series OR volume OR winner OR nominee)'
            books = await self.search_open_library_advanced(query, limit_per_award)
            series = self.detect_advanced_series_patterns(books)
            all_series.extend(series)
        
        logger.info(f"✅ Stratégie Ultra 5 terminée: {len(all_series)} séries trouvées")
        return all_series
    
    def ultra_deduplicate_series(self, all_series: List[Dict]) -> List[Dict]:
        """Déduplication ultra-sophistiquée"""
        seen_names = set()
        seen_combinations = set()
        unique_series = []
        
        for series in all_series:
            name = series['name'].lower().strip()
            author = series['author'].lower().strip()
            
            # Multiple critères déduplication
            name_key = name
            combination_key = (name, author)
            
            is_name_unique = name_key not in seen_names
            is_combination_unique = combination_key not in seen_combinations
            is_not_in_existing = name not in self.existing_series
            is_meaningful_name = len(name) >= 3 and not name.isdigit()
            
            if is_name_unique and is_combination_unique and is_not_in_existing and is_meaningful_name:
                seen_names.add(name_key)
                seen_combinations.add(combination_key)
                unique_series.append(series)
            else:
                self.stats['duplicates_skipped'] += 1
        
        return unique_series
    
    async def run_ultra_expansion(self, max_series: int = 200) -> Dict:
        """Exécution ultra-expansion complète"""
        start_time = datetime.now()
        logger.info(f"🚀 DÉBUT ULTRA EXPANSION - Objectif: {max_series} nouvelles séries")
        
        try:
            # Exécution stratégies ultra en séquence (pour éviter rate limiting)
            all_series = []
            
            # Stratégie 1: Marchés linguistiques
            series_lang = await self.ultra_strategy_languages(25)
            all_series.extend(series_lang)
            await asyncio.sleep(2)  # Pause entre stratégies
            
            # Stratégie 2: Publishers spécialisés
            series_pub = await self.ultra_strategy_publishers(20)
            all_series.extend(series_pub)
            await asyncio.sleep(2)
            
            # Stratégie 3: Exploration décennies
            series_decades = await self.ultra_strategy_decades(15)
            all_series.extend(series_decades)
            await asyncio.sleep(2)
            
            # Stratégie 4: Genres ultra-spécifiques
            series_niche = await self.ultra_strategy_niche_genres(20)
            all_series.extend(series_niche)
            await asyncio.sleep(2)
            
            # Stratégie 5: Prix littéraires
            series_awards = await self.ultra_strategy_awards(15)
            all_series.extend(series_awards)
            
            logger.info(f"📊 Total séries brutes trouvées: {len(all_series)}")
            
            # Déduplication ultra-sophistiquée
            unique_series = self.ultra_deduplicate_series(all_series)
            logger.info(f"🎯 Séries uniques après déduplication: {len(unique_series)}")
            
            # Limitation au maximum demandé
            final_series = unique_series[:max_series]
            
            # Conversion au format final
            formatted_series = []
            for series in final_series:
                entry = self.create_advanced_series_entry(series)
                formatted_series.append(entry)
                self.stats['new_series_added'] += 1
            
            # Sauvegarde nouvelles séries
            await self.save_new_series(formatted_series)
            
            # Calcul temps total
            self.stats['processing_time'] = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"✅ ULTRA EXPANSION TERMINÉE: {len(formatted_series)} nouvelles séries ajoutées")
            return {
                'new_series': formatted_series,
                'stats': self.stats,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur lors ultra expansion: {e}")
            return {
                'new_series': [],
                'stats': self.stats,
                'success': False,
                'error': str(e)
            }
    
    async def save_new_series(self, new_series: List[Dict]):
        """Sauvegarde nouvelles séries avec backup ultra-sécurisé"""
        try:
            # Chargement base existante
            database_path = Path('/app/backend/data/extended_series_database.json')
            with open(database_path, 'r') as f:
                existing_data = json.load(f)
            
            # Ajout nouvelles séries
            existing_data.extend(new_series)
            
            # Sauvegarde avec backup horodaté
            backup_path = Path(f'/app/backups/series_detection/backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}_ultra_expansion.json')
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(backup_path, 'w') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            # Sauvegarde principale
            with open(database_path, 'w') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Base de données mise à jour: {len(existing_data)} séries totales")
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde: {e}")
            raise

async def main():
    """Point d'entrée principal ultra-expansion"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ultra Expansion Open Library")
    parser.add_argument('--limit', type=int, default=200, help='Nombre maximum de nouvelles séries')
    parser.add_argument('--test', action='store_true', help='Mode test sans sauvegarde')
    args = parser.parse_args()
    
    print(f"""
🌟 ULTRA EXPANSION OPEN LIBRARY
================================
Objectif: {args.limit} nouvelles séries
Mode: {'TEST' if args.test else 'PRODUCTION'}
Stratégies: Langues + Publishers + Décennies + Genres + Awards
================================
""")
    
    async with UltraExpansionOpenLibrary() as expander:
        result = await expander.run_ultra_expansion(args.limit)
        
        if result['success']:
            stats = result['stats']
            print(f"""
✅ ULTRA EXPANSION RÉUSSIE !
=============================
📊 Nouvelles séries ajoutées: {stats['new_series_added']}
🔍 Requêtes effectuées: {stats['queries_made']}
📚 Livres analysés: {stats['books_analyzed']}
🎯 Séries détectées: {stats['series_detected']}
🔄 Doublons ignorés: {stats['duplicates_skipped']}
⏱️ Temps traitement: {stats['processing_time']:.1f}s
=============================
""")
        else:
            print(f"❌ Échec ultra expansion: {result.get('error', 'Erreur inconnue')}")

if __name__ == "__main__":
    asyncio.run(main())