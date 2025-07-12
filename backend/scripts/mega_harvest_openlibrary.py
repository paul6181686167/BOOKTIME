#!/usr/bin/env python3
"""
🎯 MEGA HARVEST OPENLIBRARY - EXPANSION FINALE INTELLIGENTE
Script final d'expansion massive avec stratégies ultra-sophistiquées

Innovation principales :
1. Exploration par mots-clés volumes/tomes spécifiques
2. Recherche séries par pagination (Volume 2, Volume 3, etc.)  
3. Exploration franchises connues avec variations
4. Scan auteurs avec plus de 10 livres
5. Recherche par patterns numériques
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

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/mega_harvest.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MegaHarvestOpenLibrary:
    """Récolteur intelligent final pour expansion maximale"""
    
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
        
        # Stratégies finales ultra-ciblées
        self.volume_patterns = [
            "Volume 2", "Volume 3", "Volume 4", "Volume 5", "Volume 6",
            "Tome 2", "Tome 3", "Tome 4", "Tome 5", "Tome 6", 
            "Book 2", "Book 3", "Book 4", "Book 5", "Book 6",
            "Part 2", "Part 3", "Part 4", "Part 5", "Part 6",
            "Episode 2", "Episode 3", "Episode 4", "Episode 5",
            "Chapter 2", "Chapter 3", "Chapter 4", "Chapter 5"
        ]
        
        # Franchises ultra-populaires avec variations
        self.mega_franchises = [
            # Univers anglais
            ("Harry Potter", ["Hogwarts", "Potter", "Wizarding World"]),
            ("Lord of the Rings", ["Middle Earth", "LOTR", "Tolkien", "Hobbit"]),
            ("Game of Thrones", ["Westeros", "Ice and Fire", "GoT"]),
            ("Chronicles of Narnia", ["Narnia", "Aslan", "Lewis"]),
            ("Dune", ["Arrakis", "Atreides", "Frank Herbert"]),
            ("Foundation", ["Seldon", "Psychohistory", "Isaac Asimov"]),
            ("Wheel of Time", ["Jordan", "Mat", "Rand", "Egwene"]),
            ("Discworld", ["Pratchett", "Ankh Morpork", "Rincewind"]),
            
            # Univers manga/anime populaires
            ("Dragon Ball", ["Goku", "Saiyan", "Toriyama"]),
            ("Naruto", ["Shinobi", "Hokage", "Kishimoto"]), 
            ("One Piece", ["Luffy", "Straw Hat", "Oda"]),
            ("Attack on Titan", ["Titan", "Eren", "Hajime"]),
            ("Death Note", ["Light", "Ryuk", "Kira"]),
            ("Demon Slayer", ["Tanjiro", "Nezuko", "Kimetsu"]),
            ("My Hero Academia", ["Quirk", "Deku", "Hero"]),
            ("Fullmetal Alchemist", ["Edward", "Alphonse", "Alchemy"]),
            
            # Univers BD franco-belge
            ("Asterix", ["Obelix", "Gaul", "Goscinny"]),
            ("Tintin", ["Hergé", "Snowy", "Captain Haddock"]),
            ("Lucky Luke", ["Dalton", "Cowboy", "Morris"]),
            ("Spirou", ["Fantasio", "Marsupilami", "Franquin"]),
            ("Blake and Mortimer", ["Edgar Jacobs", "Time Trap"]),
            ("Thorgal", ["Rosinski", "Viking", "Aaricia"]),
            
            # Séries littéraires classiques
            ("Sherlock Holmes", ["Watson", "Baker Street", "Doyle"]),
            ("James Bond", ["007", "Fleming", "Secret Agent"]),
            ("Hercule Poirot", ["Agatha Christie", "Belgium Detective"]),
            ("Inspector Morse", ["Oxford", "Colin Dexter"]),
            ("Jack Reacher", ["Lee Child", "Military Police"]),
            ("Alex Cross", ["James Patterson", "Detective"]),
        ]
        
        # Patterns série super-précis
        self.super_patterns = [
            # Patterns avec numérotation
            r'(.+?)\s+(?:Vol\.|Volume|Tome|Book|Part)\s*(\d+)',
            r'(.+?)\s+(\d+)(?:st|nd|rd|th)?\s+(?:Book|Volume|Part|Tome)',
            r'(.+?):\s+(?:Book|Volume|Tome|Part)\s+(\d+)',
            r'(.+?)\s+#(\d+)',
            r'(.+?)\s+-\s+(?:Book|Volume|Tome|Part)\s+(\d+)',
            
            # Patterns titre: sous-titre  
            r'(.+?):\s+(.+)',
            r'(.+?)\s+-\s+(.+)',
            r'(.+?)\s+\|\s+(.+)',
            
            # Patterns collection/série
            r'(.+?)\s+(?:Series|Collection|Saga|Chronicles|Adventures|Tales)',
            r'The\s+(.+?)\s+(?:Series|Collection|Saga|Chronicles)',
            
            # Patterns spéciaux manga/light novel
            r'(.+?)\s+(?:Light Novel|LN)\s+(?:Vol\.|Volume)\s*(\d+)',
            r'(.+?)\s+(?:Manga|Comic)\s+(?:Vol\.|Volume)\s*(\d+)',
        ]
        
        # Auteurs ultra-prolifiques identifiés
        self.prolific_authors_targeted = [
            "Isaac Asimov", "Agatha Christie", "Stephen King", "Ray Bradbury",
            "Arthur C. Clarke", "Philip K. Dick", "Ursula K. Le Guin",
            "Terry Pratchett", "Mercedes Lackey", "David Weber", "John Ringo",
            "Brandon Sanderson", "Robert Jordan", "Terry Goodkind",
            "Robin Hobb", "George R.R. Martin", "Patrick Rothfuss",
            "Jim Butcher", "Laurell K. Hamilton", "Charlaine Harris",
            "Janet Evanovich", "Sue Grafton", "Sara Paretsky",
            "John Grisham", "Michael Crichton", "Tom Clancy",
            "Clive Cussler", "James Patterson", "Lee Child",
            "Harlan Coben", "Tess Gerritsen", "Kathy Reichs",
            "Louise Penny", "Tana French", "Ian Rankin"
        ]
    
    async def __aenter__(self):
        """Initialisation session async"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=45),
            headers={'User-Agent': 'BOOKTIME-MegaHarvest/4.0'}
        )
        await self.load_existing_series()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Fermeture session"""
        if self.session:
            await self.session.close()
    
    async def load_existing_series(self):
        """Charge les séries existantes"""
        try:
            with open('/app/backend/data/extended_series_database.json', 'r') as f:
                existing_data = json.load(f)
                self.existing_series = {series['name'].lower() for series in existing_data}
            logger.info(f"📚 Chargé {len(self.existing_series)} séries existantes")
        except Exception as e:
            logger.warning(f"⚠️ Erreur chargement séries existantes: {e}")
            self.existing_series = set()
    
    async def search_targeted(self, query: str, limit: int = 50) -> List[Dict]:
        """Recherche ciblée ultra-optimisée"""
        try:
            await asyncio.sleep(random.uniform(0.1, 0.2))
            
            url = f"{self.base_url}/search.json"
            params = {
                'q': query,
                'limit': limit,
                'fields': 'key,title,author_name,subject,first_publish_year,publisher,isbn,number_of_pages_median,cover_i'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    self.stats['queries_made'] += 1
                    books = data.get('docs', [])
                    self.stats['books_analyzed'] += len(books)
                    return books
                else:
                    return []
        except Exception as e:
            logger.error(f"❌ Erreur recherche: {e}")
            return []
    
    def detect_mega_series_patterns(self, books: List[Dict]) -> List[Dict]:
        """Détection méga-sophistiquée avec patterns multiples"""
        series_candidates = {}
        
        for book in books:
            title = book.get('title', '').strip()
            authors = book.get('author_name', [])
            
            if not title or not authors:
                continue
            
            # Application de tous les patterns
            for pattern in self.super_patterns:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    series_name = match.group(1).strip()
                    
                    # Nettoyage et validation nom série
                    series_name = re.sub(r'\s+', ' ', series_name)  # Normalise espaces
                    series_name = series_name.strip('.,;:-')  # Supprime ponctuation finale
                    
                    if len(series_name) >= 3 and not series_name.lower() in ['the', 'a', 'an']:
                        series_key = (series_name.lower(), authors[0].lower() if authors else "unknown")
                        
                        if series_key not in series_candidates:
                            series_candidates[series_key] = {
                                'name': series_name,
                                'author': authors[0] if authors else "Unknown",
                                'books': [],
                                'volumes': set(),
                                'subjects': set(),
                                'pattern_used': pattern
                            }
                        
                        series_candidates[series_key]['books'].append(book)
                        
                        # Extraction numéro volume si disponible
                        if len(match.groups()) > 1 and match.group(2):
                            vol_str = match.group(2)
                            if vol_str.isdigit():
                                series_candidates[series_key]['volumes'].add(int(vol_str))
                        
                        # Collecte sujets
                        subjects = book.get('subject', [])
                        if subjects:
                            series_candidates[series_key]['subjects'].update(subjects[:3])
                        
                        break  # Première correspondance suffit
        
        # Validation et filtre séries
        valid_series = []
        for (series_name, author), data in series_candidates.items():
            # Critères validation stricts
            has_volumes = len(data['volumes']) >= 2
            has_books = len(data['books']) >= 2
            not_duplicate = series_name not in self.existing_series
            meaningful_name = len(series_name) >= 3 and not series_name.isdigit()
            
            if (has_volumes or has_books) and not_duplicate and meaningful_name:
                valid_series.append(data)
                self.stats['series_detected'] += 1
            else:
                self.stats['duplicates_skipped'] += 1
        
        return valid_series
    
    def smart_categorize(self, series_data: Dict) -> str:
        """Catégorisation intelligente basée sur patterns"""
        subjects = [s.lower() for s in series_data['subjects']]
        author = series_data['author'].lower()
        name = series_data['name'].lower()
        
        # Détection manga par auteur japonais et sujets
        manga_indicators = ['manga', 'anime', 'light novel', 'japanese', 'shonen', 'shojo', 'seinen']
        japanese_names = ['akira', 'hiroshi', 'takeshi', 'kenji', 'yuki', 'masashi', 'naoki']
        
        if (any(indicator in ' '.join(subjects) for indicator in manga_indicators) or
            any(jp_name in author for jp_name in japanese_names)):
            return 'manga'
        
        # Détection BD par patterns européens
        bd_indicators = ['comic', 'graphic novel', 'bande dessinee', 'cartoon', 'illustrated']
        if any(indicator in ' '.join(subjects) for indicator in bd_indicators):
            return 'bd'
        
        # Roman par défaut
        return 'roman'
    
    def create_mega_series_entry(self, series_data: Dict) -> Dict:
        """Création entrée série mega-sophistiquée"""
        name = series_data['name']
        author = series_data['author']
        category = self.smart_categorize(series_data)
        volumes = max(series_data['volumes']) if series_data['volumes'] else len(series_data['books'])
        
        # Génération patterns de détection super-intelligents
        base_name = name.lower().strip()
        keywords = [
            base_name,
            f"{base_name} series",
            f"{base_name} saga"
        ]
        
        # Ajout variations selon catégorie
        if category == 'manga':
            keywords.extend([f"{base_name} manga", f"{base_name} light novel"])
        elif category == 'bd':
            keywords.extend([f"{base_name} comic", f"{base_name} bd"])
        else:
            keywords.extend([f"{base_name} novel", f"{base_name} book"])
        
        # Ajout auteur si pertinent
        if author != "Unknown" and len(author.split()) <= 3:
            author_key = author.lower().split()[-1]  # Nom famille
            if len(author_key) > 2:
                keywords.append(author_key)
        
        # Variations titre
        variations = [name, f"The {name}", f"{name} Series"]
        
        # Exclusions pour éviter faux positifs
        exclusions = ["anthology", "collection", "omnibus", "complete", "selected"]
        
        return {
            "name": name,
            "authors": [author] if author != "Unknown" else [],
            "category": category,
            "volumes": volumes,
            "keywords": keywords[:8],  # Limite pour performance
            "variations": variations,
            "exclusions": exclusions,
            "source": "open_library_mega_harvest",
            "confidence_score": 88,
            "auto_generated": True,
            "detection_date": datetime.now().isoformat(),
            "pattern_info": {
                "detection_pattern": series_data.get('pattern_used', 'unknown'),
                "subjects": list(series_data['subjects'])[:5]
            }
        }
    
    async def harvest_by_volume_patterns(self) -> List[Dict]:
        """Récolte par patterns volume explicites"""
        logger.info("📚 Récolte par patterns volume")
        all_series = []
        
        for pattern in self.volume_patterns[:15]:  # Limite pour performance
            books = await self.search_targeted(f'title:"{pattern}"', 30)
            series = self.detect_mega_series_patterns(books)
            all_series.extend(series)
            
            if len(all_series) % 5 == 0:
                logger.info(f"📈 Volume patterns: {len(all_series)} séries détectées")
        
        return all_series
    
    async def harvest_by_franchises(self) -> List[Dict]:
        """Récolte par franchises populaires avec variations"""
        logger.info("🏢 Récolte par franchises populaires")
        all_series = []
        
        for franchise, variations in self.mega_franchises[:20]:
            # Recherche franchise principale
            books = await self.search_targeted(f'title:"{franchise}"', 25)
            series = self.detect_mega_series_patterns(books)
            all_series.extend(series)
            
            # Recherche variations
            for variation in variations[:2]:  # Limite variations
                books = await self.search_targeted(f'title:"{variation}"', 20)
                series = self.detect_mega_series_patterns(books)
                all_series.extend(series)
        
        return all_series
    
    async def harvest_by_prolific_authors(self) -> List[Dict]:
        """Récolte par auteurs ultra-prolifiques"""
        logger.info("👥 Récolte par auteurs prolifiques")
        all_series = []
        
        for author in self.prolific_authors_targeted[:20]:
            books = await self.search_targeted(f'author:"{author}"', 35)
            series = self.detect_mega_series_patterns(books)
            all_series.extend(series)
            
            if len(all_series) % 10 == 0:
                logger.info(f"📈 Auteurs prolifiques: {len(all_series)} séries détectées")
        
        return all_series
    
    async def harvest_by_numeric_patterns(self) -> List[Dict]:
        """Récolte par patterns numériques sophistiqués"""
        logger.info("🔢 Récolte par patterns numériques")
        all_series = []
        
        # Recherches ciblées avec numéros
        numeric_queries = [
            '"Book 1"', '"Book 2"', '"Book 3"', '"Volume 1"', '"Volume 2"',
            '"Part 1"', '"Part 2"', '"Tome 1"', '"Tome 2"', '"Episode 1"'
        ]
        
        for query in numeric_queries:
            books = await self.search_targeted(query, 30)
            series = self.detect_mega_series_patterns(books)
            all_series.extend(series)
        
        return all_series
    
    def mega_deduplicate(self, all_series: List[Dict]) -> List[Dict]:
        """Déduplication mega-sophistiquée"""
        seen_names = set()
        seen_combos = set()
        unique_series = []
        
        for series in all_series:
            name = series['name'].lower().strip()
            author = series['author'].lower().strip()
            
            # Clés déduplication multiples
            name_key = name
            combo_key = (name, author)
            
            if (name_key not in seen_names and 
                combo_key not in seen_combos and 
                name not in self.existing_series and
                len(name) >= 3):
                
                seen_names.add(name_key)
                seen_combos.add(combo_key)
                unique_series.append(series)
            else:
                self.stats['duplicates_skipped'] += 1
        
        return unique_series
    
    async def run_mega_harvest(self, max_series: int = 100) -> Dict:
        """Exécution mega harvest complète"""
        start_time = datetime.now()
        logger.info(f"🚀 DÉBUT MEGA HARVEST - Objectif: {max_series} nouvelles séries")
        
        try:
            # Stratégies de récolte spécialisées
            all_series = []
            
            # 1. Patterns volume
            series_vol = await self.harvest_by_volume_patterns()
            all_series.extend(series_vol)
            logger.info(f"📚 Volume patterns: {len(series_vol)} séries")
            
            # 2. Franchises populaires
            series_fran = await self.harvest_by_franchises()
            all_series.extend(series_fran)
            logger.info(f"🏢 Franchises: {len(series_fran)} séries")
            
            # 3. Auteurs prolifiques
            series_auth = await self.harvest_by_prolific_authors()
            all_series.extend(series_auth)
            logger.info(f"👥 Auteurs: {len(series_auth)} séries")
            
            # 4. Patterns numériques
            series_num = await self.harvest_by_numeric_patterns()
            all_series.extend(series_num)
            logger.info(f"🔢 Numériques: {len(series_num)} séries")
            
            logger.info(f"📊 Total séries brutes: {len(all_series)}")
            
            # Déduplication mega-sophistiquée
            unique_series = self.mega_deduplicate(all_series)
            logger.info(f"🎯 Séries uniques: {len(unique_series)}")
            
            # Limitation au maximum
            final_series = unique_series[:max_series]
            
            # Conversion format final
            formatted_series = []
            for series in final_series:
                entry = self.create_mega_series_entry(series)
                formatted_series.append(entry)
                self.stats['new_series_added'] += 1
            
            # Sauvegarde
            if formatted_series:
                await self.save_new_series(formatted_series)
            
            # Calcul temps
            self.stats['processing_time'] = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"✅ MEGA HARVEST TERMINÉ: {len(formatted_series)} nouvelles séries")
            return {
                'new_series': formatted_series,
                'stats': self.stats,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur mega harvest: {e}")
            return {
                'new_series': [],
                'stats': self.stats,
                'success': False,
                'error': str(e)
            }
    
    async def save_new_series(self, new_series: List[Dict]):
        """Sauvegarde avec backup sécurisé"""
        try:
            database_path = Path('/app/backend/data/extended_series_database.json')
            with open(database_path, 'r') as f:
                existing_data = json.load(f)
            
            existing_data.extend(new_series)
            
            # Backup
            backup_path = Path(f'/app/backups/series_detection/backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}_mega_harvest.json')
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(backup_path, 'w') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            # Sauvegarde principale
            with open(database_path, 'w') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Database mise à jour: {len(existing_data)} séries totales")
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde: {e}")
            raise

async def main():
    """Point d'entrée mega harvest"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Mega Harvest Open Library")
    parser.add_argument('--limit', type=int, default=100, help='Nombre maximum de nouvelles séries')
    args = parser.parse_args()
    
    print(f"""
🎯 MEGA HARVEST OPEN LIBRARY
=============================
Objectif: {args.limit} nouvelles séries
Stratégies: Volume Patterns + Franchises + Auteurs + Numériques
=============================
""")
    
    async with MegaHarvestOpenLibrary() as harvester:
        result = await harvester.run_mega_harvest(args.limit)
        
        if result['success']:
            stats = result['stats']
            print(f"""
✅ MEGA HARVEST RÉUSSI !
=========================
📊 Nouvelles séries ajoutées: {stats['new_series_added']}
🔍 Requêtes effectuées: {stats['queries_made']}
📚 Livres analysés: {stats['books_analyzed']}
🎯 Séries détectées: {stats['series_detected']}
🔄 Doublons ignorés: {stats['duplicates_skipped']}
⏱️ Temps traitement: {stats['processing_time']:.1f}s
=========================
""")
        else:
            print(f"❌ Échec mega harvest: {result.get('error', 'Erreur inconnue')}")

if __name__ == "__main__":
    asyncio.run(main())