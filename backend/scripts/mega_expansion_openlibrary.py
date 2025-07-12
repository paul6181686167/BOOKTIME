#!/usr/bin/env python3
"""
🚀 MEGA EXPANSION OPEN LIBRARY - AUTOEXPANSION MAXIMALE
Script d'expansion massive pour ajouter le maximum de séries possibles

Stratégies multiples :
1. Recherche par mots-clés série populaires
2. Exploration auteurs prolifiques internationaux
3. Scan catégories avec patterns série
4. Recherche séries par volume numbers
5. Exploration franchises populaires
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
        logging.FileHandler('/app/logs/mega_expansion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MegaExpansionOpenLibrary:
    """Expansion massive séries Open Library avec stratégies multiples"""
    
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
        
        # Stratégies d'expansion maximale
        self.series_keywords = [
            # Patterns série universels
            "Book 1", "Volume 1", "Part 1", "Episode 1", "Tome 1",
            "Series", "Saga", "Chronicles", "Adventures", "Tales",
            "Cycle", "Collection", "Universe", "World", "Legacy",
            
            # Termes série populaires
            "Trilogy", "Quartet", "Quintet", "Hexalogy", "Heptalogy",
            "Octology", "Ennealogy", "Decalogy", "Duology",
            
            # Genres avec séries
            "Fantasy Series", "Mystery Series", "Crime Series",
            "Science Fiction Series", "Romance Series", "Horror Series",
            "Thriller Series", "Adventure Series", "Historical Series",
            
            # Patterns manga/comics
            "Manga Series", "Comic Series", "Graphic Novel Series",
            "Light Novel", "Web Novel", "Visual Novel"
        ]
        
        # Auteurs mega-prolifiques (50+ livres)
        self.prolific_authors = [
            # Super auteurs anglais/américains
            "Isaac Asimov", "Stephen King", "Agatha Christie", "Louis L'Amour",
            "Ray Bradbury", "Philip K. Dick", "Ursula K. Le Guin", "Arthur C. Clarke",
            "Robert A. Heinlein", "Andre Norton", "Piers Anthony", "Terry Pratchett",
            "Mercedes Lackey", "David Weber", "John Ringo", "Eric Flint",
            "Baen Books", "Tor Books", "DAW Books", "Ace Books",
            
            # Auteurs français prolifiques
            "Jules Verne", "Alexandre Dumas", "Honoré de Balzac", "Émile Zola",
            "Victor Hugo", "Guy de Maupassant", "Marcel Proust", "André Gide",
            "Jean-Paul Sartre", "Albert Camus", "Simone de Beauvoir",
            "Michel Houellebecq", "Amélie Nothomb", "Guillaume Musso",
            "Marc Levy", "Anna Gavalda", "Katherine Pancol",
            
            # Mangaka populaires
            "Osamu Tezuka", "Akira Toriyama", "Eiichiro Oda", "Masashi Kishimoto",
            "Tite Kubo", "Hajime Isayama", "Naoki Urasawa", "Kentaro Miura",
            "Hiromu Arakawa", "Takeshi Obata", "Tsugumi Ohba", "ONE",
            "Koyoharu Gotouge", "Gege Akutami", "Tatsuki Fujimoto",
            
            # Auteurs comics occidentaux
            "Stan Lee", "Jack Kirby", "Bob Kane", "Jerry Siegel", "Joe Shuster",
            "Frank Miller", "Alan Moore", "Neil Gaiman", "Grant Morrison",
            "Warren Ellis", "Brian K. Vaughan", "Mark Millar", "Garth Ennis"
        ]
        
        # Franchises et univers populaires
        self.popular_franchises = [
            # Univers fantasy/SF
            "Star Wars", "Star Trek", "Doctor Who", "Warhammer", "Dungeons Dragons",
            "Marvel", "DC Comics", "Transformers", "G.I. Joe", "He-Man",
            "Teenage Mutant Ninja Turtles", "Power Rangers", "Pokemon",
            
            # Univers littéraires
            "Sherlock Holmes", "James Bond", "Jack Ryan", "Jason Bourne",
            "John Carter", "Tarzan", "Zorro", "The Shadow", "Doc Savage",
            "Conan", "Elric", "Fafhrd and Gray Mouser",
            
            # Univers manga/anime
            "Dragon Ball", "Naruto", "One Piece", "Bleach", "Death Note",
            "Attack on Titan", "My Hero Academia", "Demon Slayer", "Jujutsu Kaisen",
            "Hunter x Hunter", "Full Metal Alchemist", "Cowboy Bebop",
            
            # Univers BD franco-belge
            "Asterix", "Tintin", "Lucky Luke", "Spirou", "Gaston Lagaffe",
            "Blake et Mortimer", "Yoko Tsuno", "Thorgal", "Largo Winch",
            "Corto Maltese", "Blacksad", "Lanfeust", "Les Legendaires"
        ]
        
        # Categories étendues avec sous-genres
        self.mega_categories = {
            'fantasy': [
                'epic fantasy', 'urban fantasy', 'dark fantasy', 'high fantasy',
                'sword and sorcery', 'heroic fantasy', 'portal fantasy',
                'fairy tale retelling', 'mythic fantasy', 'steampunk fantasy'
            ],
            'scifi': [
                'space opera', 'cyberpunk', 'hard science fiction', 'soft science fiction',
                'dystopian', 'alternate history', 'time travel', 'alien invasion',
                'robot fiction', 'steampunk', 'biopunk', 'post-apocalyptic'
            ],
            'mystery': [
                'cozy mystery', 'hard-boiled', 'police procedural', 'detective fiction',
                'noir', 'whodunit', 'locked room mystery', 'amateur sleuth',
                'psychological thriller', 'legal thriller', 'espionage'
            ],
            'romance': [
                'contemporary romance', 'historical romance', 'paranormal romance',
                'romantic suspense', 'erotic romance', 'young adult romance',
                'romantic comedy', 'category romance', 'regency romance'
            ],
            'horror': [
                'supernatural horror', 'psychological horror', 'gothic horror',
                'cosmic horror', 'body horror', 'zombie fiction', 'vampire fiction',
                'werewolf fiction', 'ghost stories', 'haunted house'
            ],
            'manga': [
                'shonen manga', 'shojo manga', 'seinen manga', 'josei manga',
                'kodomomuke manga', 'doujinshi', 'manhwa', 'manhua',
                'light novel', 'visual novel adaptation'
            ],
            'comics': [
                'superhero comics', 'indie comics', 'graphic novels', 'webcomics',
                'european comics', 'franco-belgian comics', 'manga-influenced comics',
                'slice of life comics', 'adventure comics', 'crime comics'
            ]
        }
    
    async def __aenter__(self):
        """Initialisation session async"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=45),
            headers={'User-Agent': 'BOOKTIME-MegaExpansion/2.0'}
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
    
    async def search_open_library(self, query: str, limit: int = 1000) -> List[Dict]:
        """Recherche dans Open Library avec gestion d'erreur robuste"""
        try:
            # Délai anti-rate-limiting
            await asyncio.sleep(random.uniform(0.1, 0.3))
            
            url = f"{self.base_url}/search.json"
            params = {
                'q': query,
                'limit': limit,
                'fields': 'key,title,author_name,subject,first_publish_year,number_of_pages_median,cover_i'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    self.stats['queries_made'] += 1
                    books = data.get('docs', [])
                    self.stats['books_analyzed'] += len(books)
                    logger.info(f"🔍 Query '{query}': {len(books)} livres trouvés")
                    return books
                else:
                    logger.warning(f"⚠️ Erreur API {response.status} pour query: {query}")
                    return []
        except Exception as e:
            logger.error(f"❌ Erreur recherche '{query}': {e}")
            return []
    
    def detect_series_patterns(self, books: List[Dict]) -> List[Dict]:
        """Détection intelligente de patterns de séries"""
        series_candidates = {}
        
        for book in books:
            title = book.get('title', '').strip()
            authors = book.get('author_name', [])
            
            if not title or not authors:
                continue
            
            # Patterns de détection série
            series_patterns = [
                # Numérotation explicite
                r'(.+?)\s+(?:Book|Volume|Part|Tome|Episode)\s+(\d+)',
                r'(.+?)\s+(\d+)(?:st|nd|rd|th)?(?:\s|$)',
                r'(.+?)\s+#(\d+)',
                r'(.+?):\s*(.+)',  # Titre: Sous-titre
                
                # Patterns série
                r'(.+?)\s+(?:Series|Saga|Chronicles|Adventures|Tales)',
                r'(.+?)\s+(?:Cycle|Collection|Universe|World)',
                
                # Patterns spéciaux
                r'The\s+(.+?)\s+(?:Book|Volume|Part)',
                r'(.+?)\s+Trilogy',
                r'(.+?)\s+Quartet',
            ]
            
            for pattern in series_patterns:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    series_name = match.group(1).strip()
                    if len(series_name) > 3:  # Nom série valide
                        series_key = (series_name.lower(), authors[0] if authors else "Unknown")
                        
                        if series_key not in series_candidates:
                            series_candidates[series_key] = {
                                'name': series_name,
                                'author': authors[0] if authors else "Unknown",
                                'books': [],
                                'volumes': set(),
                                'subjects': set()
                            }
                        
                        series_candidates[series_key]['books'].append(book)
                        if match.group(2).isdigit() if len(match.groups()) > 1 else False:
                            series_candidates[series_key]['volumes'].add(int(match.group(2)))
                        
                        # Collecte sujets pour catégorisation
                        subjects = book.get('subject', [])
                        if subjects:
                            series_candidates[series_key]['subjects'].update(subjects[:5])
                        
                        break
        
        # Filtre séries valides (minimum 2 livres ou volumes)
        valid_series = []
        for (series_name, author), data in series_candidates.items():
            if len(data['books']) >= 2 or len(data['volumes']) >= 2:
                if series_name.lower() not in self.existing_series:
                    valid_series.append(data)
                    self.stats['series_detected'] += 1
                else:
                    self.stats['duplicates_skipped'] += 1
        
        return valid_series
    
    def categorize_series(self, series_data: Dict) -> str:
        """Catégorisation intelligente série basée sur sujets"""
        subjects = [s.lower() for s in series_data['subjects']]
        
        # Patterns manga/comics
        manga_patterns = ['manga', 'comic', 'graphic novel', 'anime', 'japanese']
        if any(pattern in ' '.join(subjects) for pattern in manga_patterns):
            return 'manga'
        
        # Patterns BD
        bd_patterns = ['bande dessinée', 'comic book', 'cartoon', 'illustration']
        if any(pattern in ' '.join(subjects) for pattern in bd_patterns):
            return 'bd'
        
        # Par défaut roman
        return 'roman'
    
    def create_series_entry(self, series_data: Dict) -> Dict:
        """Création entrée série au format EXTENDED_SERIES_DATABASE"""
        name = series_data['name']
        author = series_data['author']
        category = self.categorize_series(series_data)
        volumes = max(series_data['volumes']) if series_data['volumes'] else len(series_data['books'])
        
        # Génération patterns de détection
        base_name = name.lower()
        keywords = [
            base_name,
            f"{base_name} series",
            f"{base_name} saga",
            f"the {base_name}",
            author.lower().split()[0] if author != "Unknown" else ""
        ]
        keywords = [k for k in keywords if k]  # Supprime vides
        
        # Variations titre
        variations = [name, f"The {name}", f"{name} Series"]
        
        # Exclusions pour éviter faux positifs
        exclusions = ["anthology", "collection", "best of", "complete works"]
        
        return {
            "name": name,
            "authors": [author] if author != "Unknown" else [],
            "category": category,
            "volumes": volumes,
            "keywords": keywords,
            "variations": variations,
            "exclusions": exclusions,
            "source": "open_library_mega_expansion",
            "confidence_score": 85,
            "auto_generated": True,
            "detection_date": datetime.now().isoformat(),
            "subjects": list(series_data['subjects'])[:10]
        }
    
    async def expansion_strategy_keywords(self, limit_per_keyword: int = 200) -> List[Dict]:
        """Stratégie 1: Recherche par mots-clés série"""
        logger.info("🎯 Stratégie 1: Expansion par mots-clés série")
        all_series = []
        
        for keyword in self.series_keywords[:50]:  # Limite pour performance
            books = await self.search_open_library(f'"{keyword}"', limit_per_keyword)
            series = self.detect_series_patterns(books)
            all_series.extend(series)
            
            # Log progression
            if len(all_series) % 10 == 0:
                logger.info(f"📈 Progression: {len(all_series)} séries détectées")
        
        logger.info(f"✅ Stratégie 1 terminée: {len(all_series)} séries trouvées")
        return all_series
    
    async def expansion_strategy_authors(self, limit_per_author: int = 300) -> List[Dict]:
        """Stratégie 2: Exploration auteurs prolifiques"""
        logger.info("👥 Stratégie 2: Expansion par auteurs prolifiques")
        all_series = []
        
        for author in self.prolific_authors[:40]:  # Limite pour performance
            books = await self.search_open_library(f'author:"{author}"', limit_per_author)
            series = self.detect_series_patterns(books)
            all_series.extend(series)
            
            # Log progression
            if len(all_series) % 15 == 0:
                logger.info(f"📈 Progression auteurs: {len(all_series)} séries détectées")
        
        logger.info(f"✅ Stratégie 2 terminée: {len(all_series)} séries trouvées")
        return all_series
    
    async def expansion_strategy_franchises(self, limit_per_franchise: int = 25) -> List[Dict]:
        """Stratégie 3: Exploration franchises populaires"""
        logger.info("🏢 Stratégie 3: Expansion par franchises populaires")
        all_series = []
        
        for franchise in self.popular_franchises[:30]:  # Limite pour performance
            books = await self.search_open_library(f'"{franchise}"', limit_per_franchise)
            series = self.detect_series_patterns(books)
            all_series.extend(series)
            
            # Log progression
            if len(all_series) % 10 == 0:
                logger.info(f"📈 Progression franchises: {len(all_series)} séries détectées")
        
        logger.info(f"✅ Stratégie 3 terminée: {len(all_series)} séries trouvées")
        return all_series
    
    async def expansion_strategy_categories(self, limit_per_category: int = 40) -> List[Dict]:
        """Stratégie 4: Scan catégories avec sous-genres"""
        logger.info("📚 Stratégie 4: Expansion par catégories étendues")
        all_series = []
        
        for main_cat, sub_cats in self.mega_categories.items():
            for sub_cat in sub_cats[:8]:  # Limite sous-catégories
                query = f'subject:"{sub_cat}" AND (series OR saga OR book OR volume)'
                books = await self.search_open_library(query, limit_per_category)
                series = self.detect_series_patterns(books)
                all_series.extend(series)
        
        logger.info(f"✅ Stratégie 4 terminée: {len(all_series)} séries trouvées")
        return all_series
    
    def deduplicate_series(self, all_series: List[Dict]) -> List[Dict]:
        """Déduplication intelligente des séries trouvées"""
        seen = set()
        unique_series = []
        
        for series in all_series:
            # Clé de déduplication basée sur nom + auteur
            key = (series['name'].lower().strip(), series['author'].lower().strip())
            if key not in seen and series['name'].lower() not in self.existing_series:
                seen.add(key)
                unique_series.append(series)
            else:
                self.stats['duplicates_skipped'] += 1
        
        return unique_series
    
    async def run_mega_expansion(self, max_series: int = 100) -> Dict:
        """Exécution complète méga expansion avec toutes stratégies"""
        start_time = datetime.now()
        logger.info(f"🚀 DÉBUT MÉGA EXPANSION - Objectif: {max_series} nouvelles séries")
        
        # Exécution stratégies en parallèle pour performance maximale
        try:
            # Stratégie 1: Mots-clés série
            series_keywords = await self.expansion_strategy_keywords(20)
            
            # Stratégie 2: Auteurs prolifiques  
            series_authors = await self.expansion_strategy_authors(25)
            
            # Stratégie 3: Franchises populaires
            series_franchises = await self.expansion_strategy_franchises(20)
            
            # Stratégie 4: Catégories étendues
            series_categories = await self.expansion_strategy_categories(30)
            
            # Consolidation toutes séries
            all_series = series_keywords + series_authors + series_franchises + series_categories
            logger.info(f"📊 Total séries brutes trouvées: {len(all_series)}")
            
            # Déduplication
            unique_series = self.deduplicate_series(all_series)
            logger.info(f"🎯 Séries uniques après déduplication: {len(unique_series)}")
            
            # Limitation au maximum demandé
            final_series = unique_series[:max_series]
            
            # Conversion au format final
            formatted_series = []
            for series in final_series:
                entry = self.create_series_entry(series)
                formatted_series.append(entry)
                self.stats['new_series_added'] += 1
            
            # Sauvegarde nouvelles séries
            await self.save_new_series(formatted_series)
            
            # Calcul temps total
            self.stats['processing_time'] = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"✅ MÉGA EXPANSION TERMINÉE: {len(formatted_series)} nouvelles séries ajoutées")
            return {
                'new_series': formatted_series,
                'stats': self.stats,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur lors méga expansion: {e}")
            return {
                'new_series': [],
                'stats': self.stats,
                'success': False,
                'error': str(e)
            }
    
    async def save_new_series(self, new_series: List[Dict]):
        """Sauvegarde nouvelles séries dans database"""
        try:
            # Chargement base existante
            database_path = Path('/app/backend/data/extended_series_database.json')
            with open(database_path, 'r') as f:
                existing_data = json.load(f)
            
            # Ajout nouvelles séries
            existing_data.extend(new_series)
            
            # Sauvegarde avec backup
            backup_path = Path(f'/app/backups/series_detection/backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}_mega_expansion.json')
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
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Méga Expansion Open Library")
    parser.add_argument('--limit', type=int, default=5000, help='Nombre maximum de nouvelles séries (SANS LIMITE)')
    parser.add_argument('--unlimited', action='store_true', help='Mode illimité (ignorer toutes limites)')
    parser.add_argument('--test', action='store_true', help='Mode test sans sauvegarde')
    args = parser.parse_args()
    
    print(f"""
🚀 MÉGA EXPANSION OPEN LIBRARY
===============================
Objectif: {args.limit} nouvelles séries
Mode: {'TEST' if args.test else 'PRODUCTION'}
===============================
""")
    
    async with MegaExpansionOpenLibrary() as expander:
        result = await expander.run_mega_expansion(args.limit)
        
        if result['success']:
            stats = result['stats']
            print(f"""
✅ MÉGA EXPANSION RÉUSSIE !
============================
📊 Nouvelles séries ajoutées: {stats['new_series_added']}
🔍 Requêtes effectuées: {stats['queries_made']}
📚 Livres analysés: {stats['books_analyzed']}
🎯 Séries détectées: {stats['series_detected']}
🔄 Doublons ignorés: {stats['duplicates_skipped']}
⏱️ Temps traitement: {stats['processing_time']:.1f}s
============================
""")
        else:
            print(f"❌ Échec méga expansion: {result.get('error', 'Erreur inconnue')}")

if __name__ == "__main__":
    asyncio.run(main())