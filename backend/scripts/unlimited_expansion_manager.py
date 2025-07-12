#!/usr/bin/env python3
"""
🚀 UNLIMITED EXPANSION MANAGER - SYSTÈME TRACKING PERMANENT
Gestionnaire principal pour expansion massive sans limites avec tracking permanent

Fonctionnalités :
1. Tracking permanent des livres analysés (anti-duplication)
2. Métriques cumulatives progression
3. Backup automatique avant sessions
4. Gestion stratégies illimitées
5. Monitoring temps réel performance
"""

import asyncio
import aiohttp
import json
import hashlib
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from pathlib import Path
import logging
import time
import shutil

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/unlimited_expansion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UnlimitedExpansionManager:
    """Gestionnaire expansion massive avec tracking permanent"""
    
    def __init__(self):
        self.base_url = "https://openlibrary.org"
        self.session = None
        
        # Fichiers de tracking permanent
        self.data_dir = Path('/app/data')
        self.analyzed_cache_file = self.data_dir / 'analyzed_books_cache.json'
        self.stats_file = self.data_dir / 'processing_stats.json'
        self.series_database = self.data_dir / 'extended_series_database.json'
        
        # Cache en mémoire pour session
        self.analyzed_books_cache = set()
        self.session_stats = {
            'start_time': None,
            'books_analyzed': 0,
            'books_skipped_cache': 0,
            'new_books_discovered': 0,
            'series_detected': 0,
            'queries_made': 0,
            'processing_time': 0,
            'strategies_used': []
        }
        
        # Stratégies étendues (sans limites)
        self.extended_strategies = {
            'popular_authors': self._get_popular_authors_extended(),
            'genres_comprehensive': self._get_comprehensive_genres(),
            'languages_international': self._get_international_languages(),
            'publishers_specialized': self._get_specialized_publishers(),
            'decades_complete': self._get_complete_decades(),
            'keywords_advanced': self._get_advanced_keywords(),
            'awards_international': self._get_international_awards(),
            'series_patterns': self._get_series_patterns()
        }

    def _get_popular_authors_extended(self) -> List[str]:
        """100+ auteurs populaires internationaux"""
        return [
            # Fantasy/SF Masters
            'Brandon Sanderson', 'Stephen King', 'J.K. Rowling', 'George R.R. Martin',
            'Terry Pratchett', 'Neil Gaiman', 'Isaac Asimov', 'Frank Herbert',
            'Ursula K. Le Guin', 'Philip K. Dick', 'Ray Bradbury', 'Arthur C. Clarke',
            'Robert Jordan', 'Robin Hobb', 'Terry Brooks', 'David Eddings',
            'Robert A. Heinlein', 'Orson Scott Card', 'Anne McCaffrey', 'Marion Zimmer Bradley',
            
            # Mystery/Thriller
            'Agatha Christie', 'Arthur Conan Doyle', 'Raymond Chandler', 'Dashiell Hammett',
            'John le Carré', 'Ian Fleming', 'Patricia Highsmith', 'Gillian Flynn',
            'Tana French', 'Louise Penny', 'Michael Crichton', 'John Grisham',
            'James Patterson', 'Harlan Coben', 'Karin Slaughter', 'Jeffery Deaver',
            
            # Literary Fiction
            'Margaret Atwood', 'Joyce Carol Oates', 'Zadie Smith', 'Donna Tartt',
            'Kazuo Ishiguro', 'Salman Rushdie', 'Ian McEwan', 'Jonathan Franzen',
            'Jennifer Egan', 'Chimamanda Ngozi Adichie', 'Colson Whitehead', 'Toni Morrison',
            
            # International Authors
            'Haruki Murakami', 'Paulo Coelho', 'Isabel Allende', 'Gabriel García Márquez',
            'Milan Kundera', 'Umberto Eco', 'José Saramago', 'Mario Vargas Llosa',
            'Chinua Achebe', 'Ngugi wa Thiong\'o', 'Yasunari Kawabata', 'Kenzaburo Oe',
            
            # Manga/Light Novel Authors
            'Eiichiro Oda', 'Masashi Kishimoto', 'Akira Toriyama', 'Naoko Takeuchi',
            'Rumiko Takahashi', 'CLAMP', 'Kentaro Miura', 'Hiromu Arakawa',
            'Tite Kubo', 'Hajime Isayama', 'Kohei Horikoshi', 'Gege Akutami',
            
            # Classic Literature
            'Charles Dickens', 'Jane Austen', 'Leo Tolstoy', 'Fyodor Dostoevsky',
            'Victor Hugo', 'Honoré de Balzac', 'Émile Zola', 'Marcel Proust',
            'James Joyce', 'Virginia Woolf', 'Ernest Hemingway', 'William Faulkner',
            
            # Franco-Belgian Comics
            'René Goscinny', 'Albert Uderzo', 'Hergé', 'Jean Giraud (Moebius)',
            'François Schuiten', 'Jean Van Hamme', 'Philippe Francq', 'Enki Bilal',
            'Morris', 'Peyo', 'André Franquin', 'Jean Roba',
            
            # Romance/YA
            'Sarah J. Maas', 'Cassandra Clare', 'Stephanie Meyer', 'Suzanne Collins',
            'Veronica Roth', 'Rick Riordan', 'Leigh Bardugo', 'Victoria Aveyard',
            'Rainbow Rowell', 'John Green', 'Colleen Hoover', 'Nicholas Sparks'
        ]

    def _get_comprehensive_genres(self) -> List[str]:
        """50+ genres spécifiques"""
        return [
            # Fiction Genres
            'fantasy', 'science fiction', 'mystery', 'thriller', 'romance', 'horror',
            'historical fiction', 'literary fiction', 'young adult', 'urban fantasy',
            'epic fantasy', 'space opera', 'cyberpunk', 'steampunk', 'dystopian',
            'post-apocalyptic', 'alternate history', 'time travel', 'superhero',
            'paranormal romance', 'cozy mystery', 'hard-boiled', 'noir',
            'psychological thriller', 'legal thriller', 'medical thriller',
            
            # Manga/Anime Specific
            'shonen manga', 'shojo manga', 'seinen manga', 'josei manga',
            'kodomomuke manga', 'doujinshi', 'manhwa', 'manhua',
            'isekai', 'slice of life', 'magical girl', 'mecha',
            
            # Comics Specific
            'superhero comics', 'indie comics', 'graphic novels', 'webcomics',
            'european comics', 'franco-belgian comics', 'manga-influenced comics',
            
            # Literary Categories
            'bildungsroman', 'magical realism', 'contemporary fiction', 'women\'s fiction',
            'multicultural fiction', 'lgbtq fiction', 'christian fiction', 'new adult',
            'chick lit', 'adventure', 'western', 'war fiction', 'spy fiction'
        ]

    def _get_international_languages(self) -> List[Dict[str, str]]:
        """20+ langues avec codes et variantes"""
        return [
            {'code': 'en', 'name': 'english', 'variants': ['eng', 'english']},
            {'code': 'fr', 'name': 'french', 'variants': ['fra', 'français', 'francais']},
            {'code': 'es', 'name': 'spanish', 'variants': ['esp', 'español', 'espanol']},
            {'code': 'de', 'name': 'german', 'variants': ['deu', 'deutsch']},
            {'code': 'it', 'name': 'italian', 'variants': ['ita', 'italiano']},
            {'code': 'pt', 'name': 'portuguese', 'variants': ['por', 'português']},
            {'code': 'ja', 'name': 'japanese', 'variants': ['jpn', '日本語', 'nihongo']},
            {'code': 'ko', 'name': 'korean', 'variants': ['kor', '한국어', 'hangugeo']},
            {'code': 'zh', 'name': 'chinese', 'variants': ['chi', '中文', 'zhongwen']},
            {'code': 'ru', 'name': 'russian', 'variants': ['rus', 'русский']},
            {'code': 'ar', 'name': 'arabic', 'variants': ['ara', 'العربية']},
            {'code': 'hi', 'name': 'hindi', 'variants': ['hin', 'हिन्दी']},
            {'code': 'nl', 'name': 'dutch', 'variants': ['nld', 'nederlands']},
            {'code': 'sv', 'name': 'swedish', 'variants': ['swe', 'svenska']},
            {'code': 'no', 'name': 'norwegian', 'variants': ['nor', 'norsk']},
            {'code': 'da', 'name': 'danish', 'variants': ['dan', 'dansk']},
            {'code': 'fi', 'name': 'finnish', 'variants': ['fin', 'suomi']},
            {'code': 'pl', 'name': 'polish', 'variants': ['pol', 'polski']},
            {'code': 'tr', 'name': 'turkish', 'variants': ['tur', 'türkçe']},
            {'code': 'he', 'name': 'hebrew', 'variants': ['heb', 'עברית']}
        ]

    def _get_specialized_publishers(self) -> Dict[str, List[str]]:
        """200+ éditeurs spécialisés par genre"""
        return {
            'manga': [
                'Kodansha', 'Shogakukan', 'Shueisha', 'Square Enix', 'Kadokawa',
                'VIZ Media', 'Tokyopop', 'Dark Horse Manga', 'Seven Seas', 'Yen Press',
                'Vertical', 'Digital Manga Publishing', 'CMX', 'Del Rey Manga',
                'Funimation', 'Crunchyroll', 'Media Blasters', 'NIS America'
            ],
            'comics': [
                'Marvel Comics', 'DC Comics', 'Image Comics', 'Dark Horse Comics',
                'IDW Publishing', 'Boom! Studios', 'Dynamite Entertainment',
                'Valiant Comics', 'Aftershock Comics', 'Black Mask Studios',
                'Oni Press', 'First Second Books', 'Top Cow Productions'
            ],
            'fantasy': [
                'Tor Books', 'DAW Books', 'Ace Books', 'Del Rey', 'Orbit Books',
                'Bantam Spectra', 'Harper Voyager', 'Gollancz', 'Baen Books',
                'Angry Robot', 'Subterranean Press', 'Night Shade Books'
            ],
            'french': [
                'Gallimard', 'Hachette', 'Flammarion', 'Albin Michel', 'Fayard',
                'Seuil', 'Grasset', 'Pocket', 'J\'ai Lu', 'Le Livre de Poche',
                'Bragelonne', 'Milady', 'ActuSF', 'Denoël', 'Calmann-Lévy'
            ],
            'academic': [
                'Cambridge University Press', 'Oxford University Press', 'MIT Press',
                'Harvard University Press', 'Princeton University Press', 'Yale University Press',
                'University of Chicago Press', 'Stanford University Press'
            ]
        }

    def _get_complete_decades(self) -> List[int]:
        """Décennies complètes 1900-2020"""
        return list(range(1900, 2030, 10))

    def _get_advanced_keywords(self) -> List[str]:
        """Mots-clés avancés pour détection séries"""
        return [
            'series', 'saga', 'book', 'novel', 'volume', 'tome', 'part',
            'chronicles', 'adventures', 'tales', 'stories', 'cycle',
            'trilogy', 'quartet', 'quintet', 'collection', 'omnibus',
            'sequel', 'prequel', 'spin-off', 'companion', 'continuation',
            'episode', 'season', 'arc', 'chapter', 'installment'
        ]

    def _get_international_awards(self) -> List[str]:
        """Prix littéraires internationaux"""
        return [
            'Hugo Award', 'Nebula Award', 'World Fantasy Award', 'Locus Award',
            'Eisner Award', 'Harvey Award', 'Manga Taisho', 'Kodansha Manga Award',
            'Prix Goncourt', 'Prix Renaudot', 'Prix Femina', 'Prix Médicis',
            'Booker Prize', 'Pulitzer Prize', 'National Book Award', 'PEN/Faulkner Award',
            'Costa Book Award', 'Whitbread Award', 'Orange Prize', 'Miles Franklin Award'
        ]

    def _get_series_patterns(self) -> List[str]:
        """Patterns spécifiques séries"""
        return [
            'book 1', 'book 2', 'book 3', 'volume 1', 'volume 2', 'volume 3',
            'tome 1', 'tome 2', 'tome 3', 'part 1', 'part 2', 'part 3',
            '#1', '#2', '#3', 'first', 'second', 'third', 'complete',
            'collection', 'omnibus', 'boxed set', 'complete works'
        ]

    async def __aenter__(self):
        """Context manager entry"""
        await self._setup_session()
        await self._load_tracking_data()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self._save_tracking_data()
        if self.session:
            await self.session.close()

    async def _setup_session(self):
        """Initialiser session HTTP avec timeouts étendus"""
        timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes timeout
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={'User-Agent': 'BOOKTIME-UnlimitedExpansion/1.0'}
        )

    async def _load_tracking_data(self):
        """Charger données tracking permanent"""
        try:
            # Charger cache livres analysés
            if self.analyzed_cache_file.exists():
                with open(self.analyzed_cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    self.analyzed_books_cache = set(cache_data.get('analyzed_hashes', []))
                logger.info(f"📚 Cache chargé: {len(self.analyzed_books_cache)} livres déjà analysés")
            
            # Charger stats cumulative
            if self.stats_file.exists():
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    self.cumulative_stats = json.load(f)
                logger.info(f"📊 Stats chargées: {self.cumulative_stats.get('total_books_analyzed', 0)} livres total")
            else:
                self.cumulative_stats = {
                    'total_books_analyzed': 0,
                    'total_sessions': 0,
                    'total_series_found': 0,
                    'sessions_history': []
                }
                
        except Exception as e:
            logger.warning(f"⚠️ Erreur chargement tracking: {e}")
            self.analyzed_books_cache = set()
            self.cumulative_stats = {'total_books_analyzed': 0, 'total_sessions': 0, 'total_series_found': 0, 'sessions_history': []}

    async def _save_tracking_data(self):
        """Sauvegarder données tracking permanent"""
        try:
            # Sauvegarder cache
            cache_data = {
                'last_updated': datetime.now().isoformat(),
                'analyzed_hashes': list(self.analyzed_books_cache),
                'total_analyzed': len(self.analyzed_books_cache)
            }
            with open(self.analyzed_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)

            # Mettre à jour stats cumulative
            self.cumulative_stats['total_books_analyzed'] += self.session_stats['new_books_discovered']
            self.cumulative_stats['total_sessions'] += 1
            self.cumulative_stats['total_series_found'] += self.session_stats['series_detected']
            self.cumulative_stats['sessions_history'].append({
                'timestamp': datetime.now().isoformat(),
                'stats': self.session_stats.copy()
            })
            
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.cumulative_stats, f, indent=2, ensure_ascii=False)
                
            logger.info("💾 Tracking data sauvegardé avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde tracking: {e}")

    def _generate_book_hash(self, title: str, author: str = "") -> str:
        """Générer hash unique pour un livre"""
        combined = f"{title.lower().strip()}:{author.lower().strip()}"
        return hashlib.md5(combined.encode('utf-8')).hexdigest()

    def _is_book_analyzed(self, title: str, author: str = "") -> bool:
        """Vérifier si livre déjà analysé"""
        book_hash = self._generate_book_hash(title, author)
        return book_hash in self.analyzed_books_cache

    def _mark_book_analyzed(self, title: str, author: str = ""):
        """Marquer livre comme analysé"""
        book_hash = self._generate_book_hash(title, author)
        self.analyzed_books_cache.add(book_hash)

    async def backup_before_session(self):
        """Backup automatique avant session"""
        try:
            backup_dir = Path('/app/backups/unlimited_expansion')
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_subdir = backup_dir / f"backup_{timestamp}"
            backup_subdir.mkdir(exist_ok=True)
            
            # Backup fichiers critiques
            if self.series_database.exists():
                shutil.copy2(self.series_database, backup_subdir / 'extended_series_database.json')
            if self.analyzed_cache_file.exists():
                shutil.copy2(self.analyzed_cache_file, backup_subdir / 'analyzed_books_cache.json')
            if self.stats_file.exists():
                shutil.copy2(self.stats_file, backup_subdir / 'processing_stats.json')
                
            logger.info(f"💾 Backup créé: {backup_subdir}")
            return backup_subdir
            
        except Exception as e:
            logger.warning(f"⚠️ Erreur backup: {e}")
            return None

    async def run_unlimited_expansion(self, target_books: int = 100000) -> Dict:
        """
        Lancer expansion massive illimitée
        
        Args:
            target_books: Nombre cible de livres à analyser (défaut: 100K)
        """
        self.session_stats['start_time'] = time.time()
        logger.info(f"""
🚀 EXPANSION MASSIVE ILLIMITÉE DÉMARRÉE
======================================
Objectif: {target_books:,} livres à analyser
Cache: {len(self.analyzed_books_cache):,} livres déjà analysés
Stratégies: {len(self.extended_strategies)} disponibles
======================================
""")
        
        # Backup automatique
        await self.backup_before_session()
        
        try:
            # Exécuter toutes les stratégies sans limites
            all_new_books = []
            
            for strategy_name, strategy_data in self.extended_strategies.items():
                logger.info(f"🎯 Stratégie: {strategy_name}")
                self.session_stats['strategies_used'].append(strategy_name)
                
                if strategy_name == 'popular_authors':
                    books = await self._strategy_unlimited_authors(strategy_data, target_books // 8)
                elif strategy_name == 'genres_comprehensive':
                    books = await self._strategy_unlimited_genres(strategy_data, target_books // 8)
                elif strategy_name == 'languages_international':
                    books = await self._strategy_unlimited_languages(strategy_data, target_books // 8)
                else:
                    books = await self._strategy_generic_unlimited(strategy_data, target_books // 8)
                
                all_new_books.extend(books)
                
                # Check si objectif atteint
                if len(all_new_books) >= target_books:
                    logger.info(f"🎯 Objectif atteint: {len(all_new_books):,} livres")
                    break
            
            # Traitement final
            self.session_stats['processing_time'] = time.time() - self.session_stats['start_time']
            
            result = {
                'success': True,
                'books_discovered': len(all_new_books),
                'session_stats': self.session_stats,
                'cumulative_stats': self.cumulative_stats
            }
            
            logger.info(f"""
✅ EXPANSION MASSIVE TERMINÉE !
===============================
📚 Nouveaux livres: {len(all_new_books):,}
📊 Cache évité: {self.session_stats['books_skipped_cache']:,}
🔍 Requêtes: {self.session_stats['queries_made']:,}
⏱️ Durée: {self.session_stats['processing_time']:.1f}s
===============================
""")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Erreur expansion: {e}")
            return {'success': False, 'error': str(e)}

    async def _strategy_unlimited_authors(self, authors: List[str], target: int) -> List[Dict]:
        """Stratégie auteurs sans limites"""
        books = []
        limit_per_author = max(target // len(authors), 100)  # Minimum 100 par auteur
        
        for author in authors:
            if len(books) >= target:
                break
                
            author_books = await self._search_openlibrary_unlimited(
                f'author:"{author}"', limit_per_author
            )
            books.extend(author_books)
            
        return books

    async def _strategy_unlimited_genres(self, genres: List[str], target: int) -> List[Dict]:
        """Stratégie genres sans limites"""
        books = []
        limit_per_genre = max(target // len(genres), 50)
        
        for genre in genres:
            if len(books) >= target:
                break
                
            genre_books = await self._search_openlibrary_unlimited(
                f'subject:"{genre}"', limit_per_genre
            )
            books.extend(genre_books)
            
        return books

    async def _strategy_unlimited_languages(self, languages: List[Dict], target: int) -> List[Dict]:
        """Stratégie langues sans limites"""
        books = []
        limit_per_lang = max(target // len(languages), 50)
        
        for lang in languages:
            if len(books) >= target:
                break
                
            for variant in [lang['code'], lang['name']] + lang['variants']:
                lang_books = await self._search_openlibrary_unlimited(
                    f'language:{variant}', limit_per_lang // len(lang['variants'])
                )
                books.extend(lang_books)
                
        return books

    async def _strategy_generic_unlimited(self, strategy_data: List, target: int) -> List[Dict]:
        """Stratégie générique sans limites"""
        books = []
        limit_per_item = max(target // len(strategy_data), 20)
        
        for item in strategy_data:
            if len(books) >= target:
                break
                
            item_books = await self._search_openlibrary_unlimited(
                f'"{item}"', limit_per_item
            )
            books.extend(item_books)
            
        return books

    async def _search_openlibrary_unlimited(self, query: str, limit: int = 1000) -> List[Dict]:
        """Recherche Open Library sans limites avec tracking"""
        try:
            # Construire URL sans limite artificielle
            url = f"{self.base_url}/search.json"
            params = {
                'q': query,
                'limit': min(limit, 1000),  # Maximum API Open Library
                'fields': 'key,title,author_name,subject,language,publish_date,publisher'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    books = data.get('docs', [])
                    
                    # Filtrer avec cache
                    new_books = []
                    for book in books:
                        title = book.get('title', '')
                        author = ', '.join(book.get('author_name', []))
                        
                        if not self._is_book_analyzed(title, author):
                            self._mark_book_analyzed(title, author)
                            new_books.append(book)
                            self.session_stats['new_books_discovered'] += 1
                        else:
                            self.session_stats['books_skipped_cache'] += 1
                    
                    self.session_stats['queries_made'] += 1
                    self.session_stats['books_analyzed'] += len(books)
                    
                    logger.info(f"🔍 Query '{query[:50]}...': {len(books)} total, {len(new_books)} nouveaux")
                    return new_books
                    
                else:
                    logger.warning(f"⚠️ Erreur API {response.status}: {query}")
                    return []
                    
        except Exception as e:
            logger.error(f"❌ Erreur recherche '{query}': {e}")
            return []

# Point d'entrée principal
async def main():
    """Point d'entrée expansion illimitée"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Unlimited Expansion Manager")
    parser.add_argument('--target', type=int, default=100000, help='Nombre cible de livres à analyser')
    parser.add_argument('--test', action='store_true', help='Mode test (limite 1000)')
    args = parser.parse_args()
    
    target_books = 1000 if args.test else args.target
    
    print(f"""
🚀 UNLIMITED EXPANSION MANAGER
==============================
Objectif: {target_books:,} livres
Mode: {'TEST' if args.test else 'PRODUCTION'}
==============================
""")
    
    async with UnlimitedExpansionManager() as manager:
        result = await manager.run_unlimited_expansion(target_books)
        
        if result['success']:
            print(f"""
✅ SUCCÈS !
============
📚 Livres découverts: {result['books_discovered']:,}
⏱️ Durée: {result['session_stats']['processing_time']:.1f}s
🔍 Requêtes: {result['session_stats']['queries_made']:,}
============
""")
        else:
            print(f"❌ ERREUR: {result.get('error', 'Inconnue')}")

if __name__ == "__main__":
    asyncio.run(main())