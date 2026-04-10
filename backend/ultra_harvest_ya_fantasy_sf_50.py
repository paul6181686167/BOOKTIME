#!/usr/bin/env python3
"""
Ultra Harvest 100k AutoExpansion OpenLibrary - Young Adult Fantasy/Science Fiction Focus
Mission: Maximiser découvertes séries YA Fantasy/SF avec confiance 50%
Date: 12 Mars 2025
"""

import json
import requests
import time
import re
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path
import logging
from dataclasses import dataclass, asdict

# Configuration
CONFIDENCE_THRESHOLD = 50  # Confiance 50% pour maximiser découvertes
API_BASE_URL = "https://openlibrary.org/search.json"
MAX_REQUESTS = 200  # Respecter les limites API
DELAY_BETWEEN_REQUESTS = 0.4  # Respectueux
RESULTS_PER_REQUEST = 50  # Maximiser efficacité

# Mots-clés YA Fantasy/Science Fiction spécialisés
YA_FANTASY_KEYWORDS = [
    # Fantasy YA classique
    "young adult fantasy", "YA fantasy", "teen fantasy", "teenage fantasy",
    "magic", "magical", "wizard", "witch", "dragon", "fairy", "faerie", "fae",
    "vampire", "werewolf", "shapeshifter", "supernatural", "paranormal",
    "academy", "school magic", "chosen one", "prophecy", "quest",
    "realm", "kingdom", "empire", "medieval", "sword", "sorcery",
    
    # Science Fiction YA
    "young adult science fiction", "YA sci-fi", "YA science fiction", 
    "teen science fiction", "teenage sci-fi", "dystopian", "dystopia",
    "space", "alien", "robot", "cyborg", "android", "future", "futuristic",
    "time travel", "spaceship", "galaxy", "planet", "colony", "space station",
    "genetic", "clone", "mutation", "technology", "AI", "artificial intelligence",
    "post-apocalyptic", "apocalypse", "survival", "wasteland",
    
    # Sous-genres populaires
    "urban fantasy", "dark fantasy", "epic fantasy", "high fantasy",
    "steampunk", "cyberpunk", "space opera", "hard science fiction",
    "alternate history", "parallel universe", "dimension", "multiverse",
    "time loop", "superhero", "superpower", "ability", "gifted",
    
    # Thèmes YA populaires
    "academy", "boarding school", "training", "tournament", "competition",
    "romance", "love triangle", "forbidden love", "enemies to lovers",
    "coming of age", "first love", "friendship", "betrayal", "sacrifice",
    "destiny", "fate", "curse", "blessing", "power", "magic system"
]

# Auteurs YA Fantasy/SF populaires
YA_FANTASY_AUTHORS = [
    "Sarah J. Maas", "Cassandra Clare", "Leigh Bardugo", "Victoria Aveyard",
    "Stephanie Meyer", "Suzanne Collins", "Veronica Roth", "Kiera Cass",
    "Jennifer L. Armentrout", "Elise Kova", "Alexandra Bracken", "Marie Lu",
    "Tahereh Mafi", "Renée Ahdieh", "Sabaa Tahir", "Tomi Adeyemi",
    "Adrienne Young", "Stephanie Perkins", "Maggie Stiefvater", "Holly Black",
    "Cassandra Jean", "Richelle Mead", "Ally Condie", "Scott Westerfeld",
    "James Dashner", "Pierce Brown", "Kass Morgan", "Beth Revis",
    "Marissa Meyer", "Cinder", "Scarlet", "Cress", "Winter"
]

# Séries YA Fantasy/SF iconiques (pour patterns)
ICONIC_YA_SERIES = [
    "Throne of Glass", "A Court of", "Shadow and Bone", "Red Queen",
    "The Hunger Games", "Divergent", "The Selection", "The Mortal Instruments",
    "The Infernal Devices", "Twilight", "Harry Potter", "Percy Jackson",
    "The Maze Runner", "The 100", "Shatter Me", "The Wicked Trilogy",
    "From Blood and Ash", "The Seven Husbands", "Six of Crows", "Crooked Kingdom",
    "The Cruel Prince", "The Folk of the Air", "Caraval", "Once Upon a Broken Heart",
    "The Poppy War", "Children of Blood and Bone", "Sky in the Deep",
    "The Raven Boys", "The Vampire Academy", "Matched", "Uglies",
    "The Giver", "The Testing", "The Fifth Wave", "The Darkest Minds"
]

@dataclass
class SeriesCandidate:
    name: str
    author: str
    category: str
    confidence: int
    match_reasons: List[str]
    volumes: int
    genre: str
    ol_key: str
    sample_titles: List[str]
    ya_score: int

class UltraHarvestYAFantasySF:
    def __init__(self):
        self.setup_logging()
        self.discovered_series: Set[str] = set()
        self.new_series: List[SeriesCandidate] = []
        self.total_books_analyzed = 0
        self.total_api_calls = 0
        self.session_start_time = time.time()
        
        # Charger base existante
        self.load_existing_series()
        
        # Patterns de détection optimisés pour YA Fantasy/SF
        self.setup_ya_detection_patterns()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/app/backend/ultra_harvest_ya_fantasy_sf.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def load_existing_series(self):
        """Charger la base existante pour éviter les doublons"""
        try:
            with open('/app/backend/data/extended_series_database.json', 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                self.discovered_series = set(series['name'].lower() for series in existing_data)
                self.logger.info(f"Base existante chargée: {len(self.discovered_series)} séries")
        except Exception as e:
            self.logger.error(f"Erreur chargement base existante: {e}")
            self.discovered_series = set()

    def setup_ya_detection_patterns(self):
        """Patterns ultra-optimisés pour YA Fantasy/SF"""
        self.series_patterns = [
            # Patterns YA Fantasy classiques
            r'(.+?)\s+(?:book|novel|tome|volume|vol)\s*(\d+)',
            r'(.+?)\s+(?:part|partie)\s*(\d+)',
            r'(.+?)\s+#(\d+)',
            r'(.+?)\s+(\d+)(?:st|nd|rd|th)?\s+(?:book|novel|installment)',
            
            # Patterns séries fantasy spécifiques
            r'(.+?)\s+(?:saga|series|chronicle|chronicles|trilogy|duology|quartet)\s*(\d+)',
            r'(.+?)\s+(?:legend|legends|tale|tales|story|stories)\s*(\d+)',
            r'(.+?)\s+(?:realm|kingdom|empire|world|lands)\s*(\d+)',
            
            # Patterns académies et écoles magiques
            r'(.+?)\s+(?:academy|school|institute|university)\s*(\d+)',
            r'(.+?)\s+(?:year|grade|level|class)\s*(\d+)',
            
            # Patterns dystopian/SF
            r'(.+?)\s+(?:season|phase|wave|generation)\s*(\d+)',
            r'(.+?)\s+(?:sector|district|zone|area)\s*(\d+)',
            r'(.+?)\s+(?:colony|station|outpost|base)\s*(\d+)',
            
            # Patterns romance fantasy
            r'(.+?)\s+(?:love|heart|kiss|passion|desire)\s*(\d+)',
            r'(.+?)\s+(?:prince|princess|king|queen|lord|lady)\s*(\d+)',
            
            # Patterns ultra-permissifs pour YA
            r'(.+?)\s+(\d+)(?:\s*[-:]\s*.+)?$',
            r'(.+?)\s+(?:no\.?|number|n°|num)\s*(\d+)',
            r'(.+?)\s+(?:episode|chapter|arc)\s*(\d+)',
        ]

    def get_ya_fantasy_search_queries(self) -> List[str]:
        """Générer requêtes de recherche YA Fantasy/SF"""
        queries = []
        
        # Requêtes par genre
        genre_queries = [
            "young adult fantasy",
            "YA fantasy",
            "teen fantasy",
            "young adult science fiction",
            "YA sci-fi",
            "dystopian young adult",
            "paranormal young adult",
            "urban fantasy young adult",
            "YA supernatural",
            "teenage fantasy",
            "teenage science fiction"
        ]
        
        # Requêtes par thème
        theme_queries = [
            "magic academy",
            "vampire academy",
            "dragon rider",
            "chosen one",
            "prophecy fantasy",
            "time travel YA",
            "space opera YA",
            "post-apocalyptic YA",
            "supernatural romance",
            "fantasy romance",
            "dystopian trilogy",
            "magic system",
            "faerie court",
            "dragon series",
            "vampire series",
            "werewolf series",
            "witch series",
            "alien invasion YA",
            "superhero YA",
            "mutant powers"
        ]
        
        # Requêtes par auteur populaire
        author_queries = [
            f"author:{author}" for author in YA_FANTASY_AUTHORS[:10]  # Top 10
        ]
        
        # Requêtes par mots-clés populaires
        keyword_queries = [
            "subject:young adult",
            "subject:fantasy",
            "subject:science fiction",
            "subject:paranormal",
            "subject:supernatural",
            "subject:dystopian",
            "subject:magic",
            "subject:vampire",
            "subject:dragon",
            "subject:academy"
        ]
        
        queries.extend(genre_queries)
        queries.extend(theme_queries)
        queries.extend(author_queries)
        queries.extend(keyword_queries)
        
        return queries

    def search_ya_fantasy_books(self, query: str) -> List[Dict]:
        """Rechercher livres YA Fantasy/SF"""
        all_books = []
        
        try:
            params = {
                'q': query,
                'limit': RESULTS_PER_REQUEST,
                'fields': 'title,author_name,subject,first_publish_year,key,isbn,publisher'
            }
            
            response = requests.get(API_BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            books = data.get('docs', [])
            
            self.total_api_calls += 1
            self.total_books_analyzed += len(books)
            
            # Filtrer pour YA Fantasy/SF
            filtered_books = []
            for book in books:
                if self.is_ya_fantasy_sf_book(book):
                    filtered_books.append(book)
            
            all_books.extend(filtered_books)
            
            self.logger.info(f"Query '{query}': {len(filtered_books)} livres YA Fantasy/SF trouvés")
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
            
        except Exception as e:
            self.logger.error(f"Erreur recherche query '{query}': {e}")
        
        return all_books

    def is_ya_fantasy_sf_book(self, book: Dict) -> bool:
        """Vérifier si un livre est YA Fantasy/SF"""
        title = book.get('title', '').lower()
        subjects = book.get('subject', [])
        authors = book.get('author_name', [])
        
        # Score YA Fantasy/SF
        ya_score = 0
        
        # Vérifier titre
        for keyword in YA_FANTASY_KEYWORDS:
            if keyword.lower() in title:
                ya_score += 2
        
        # Vérifier sujets
        if subjects:
            subject_text = ' '.join(subjects).lower()
            ya_indicators = [
                'young adult', 'teen', 'teenage', 'ya', 'juvenile fiction',
                'fantasy', 'science fiction', 'paranormal', 'supernatural',
                'dystopian', 'magic', 'vampire', 'dragon', 'academy'
            ]
            
            for indicator in ya_indicators:
                if indicator in subject_text:
                    ya_score += 3
        
        # Vérifier auteurs
        if authors:
            author_text = ' '.join(authors).lower()
            for ya_author in YA_FANTASY_AUTHORS:
                if ya_author.lower() in author_text:
                    ya_score += 5
        
        # Vérifier séries iconiques
        for series in ICONIC_YA_SERIES:
            if series.lower() in title:
                ya_score += 4
        
        return ya_score >= 3  # Seuil pour considérer comme YA Fantasy/SF

    def detect_ya_series_from_books(self, books: List[Dict]) -> List[SeriesCandidate]:
        """Détecter séries YA Fantasy/SF à partir des livres"""
        series_candidates = {}
        
        for book in books:
            title = book.get('title', '').strip()
            if not title:
                continue
                
            # Tester tous les patterns
            for pattern in self.series_patterns:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    series_name = match.group(1).strip()
                    volume_num = match.group(2)
                    
                    # Validation YA Fantasy/SF
                    if not self.is_valid_ya_series_name(series_name):
                        continue
                    
                    # Nettoyer le nom de série
                    series_name = self.clean_ya_series_name(series_name)
                    series_key = series_name.lower()
                    
                    if series_key in self.discovered_series:
                        continue
                    
                    # Calculer confiance YA
                    confidence = self.calculate_ya_confidence(book, series_name, volume_num)
                    ya_score = self.calculate_ya_score(book, series_name)
                    
                    if confidence >= CONFIDENCE_THRESHOLD and ya_score >= 5:
                        if series_key not in series_candidates:
                            series_candidates[series_key] = {
                                'name': series_name,
                                'author': self.get_primary_author(book),
                                'category': self.detect_ya_category(book),
                                'confidence': confidence,
                                'match_reasons': [],
                                'volumes': set(),
                                'genre': self.detect_ya_genre(book),
                                'ol_key': book.get('key', ''),
                                'sample_titles': [],
                                'ya_score': ya_score
                            }
                        
                        # Mettre à jour les informations
                        candidate = series_candidates[series_key]
                        candidate['volumes'].add(volume_num)
                        candidate['sample_titles'].append(title)
                        candidate['confidence'] = max(candidate['confidence'], confidence)
                        candidate['ya_score'] = max(candidate['ya_score'], ya_score)
                        
                        # Raisons de correspondance
                        reasons = self.get_ya_match_reasons(book, series_name, volume_num)
                        candidate['match_reasons'].extend(reasons)
                        
                        break
        
        # Convertir en SeriesCandidate
        results = []
        for candidate in series_candidates.values():
            candidate['volumes'] = len(candidate['volumes'])
            candidate['match_reasons'] = list(set(candidate['match_reasons']))
            candidate['sample_titles'] = list(set(candidate['sample_titles']))[:3]
            
            results.append(SeriesCandidate(**candidate))
        
        return results

    def is_valid_ya_series_name(self, name: str) -> bool:
        """Valider nom de série YA"""
        if len(name) < 2 or len(name) > 80:
            return False
            
        # Mots-clés YA positifs
        name_lower = name.lower()
        ya_positive = [
            'academy', 'school', 'magic', 'dragon', 'vampire', 'witch',
            'prince', 'princess', 'kingdom', 'realm', 'throne', 'crown',
            'shadow', 'dark', 'light', 'fire', 'ice', 'blood', 'bone',
            'heart', 'soul', 'destiny', 'prophecy', 'chosen', 'curse',
            'legend', 'tale', 'story', 'saga', 'chronicle', 'quest'
        ]
        
        for keyword in ya_positive:
            if keyword in name_lower:
                return True
        
        # Accepter noms avec patterns YA
        if any(word in name_lower for word in ['of', 'and', 'the', 'a', 'an']):
            return True
            
        return len(name) >= 5  # Accepter noms longs

    def clean_ya_series_name(self, name: str) -> str:
        """Nettoyer nom de série YA"""
        # Supprimer préfixes/suffixes YA
        name = re.sub(r'^(the|a|an)\s+', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s+(series|saga|trilogy|duology|quartet|chronicles?)$', '', name, flags=re.IGNORECASE)
        
        # Nettoyer caractères spéciaux
        name = re.sub(r'[^\w\s\-\'\"&]', '', name)
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name

    def calculate_ya_confidence(self, book: Dict, series_name: str, volume_num: str) -> int:
        """Calculer confiance YA spécialisée"""
        confidence = 50  # Base
        
        # Bonus volume
        try:
            vol_int = int(volume_num)
            if 1 <= vol_int <= 20:
                confidence += 20
        except:
            pass
        
        # Bonus auteur YA
        authors = book.get('author_name', [])
        if authors:
            author_text = ' '.join(authors).lower()
            for ya_author in YA_FANTASY_AUTHORS:
                if ya_author.lower() in author_text:
                    confidence += 25
                    break
        
        # Bonus sujets YA
        subjects = book.get('subject', [])
        if subjects:
            subject_text = ' '.join(subjects).lower()
            ya_subjects = ['young adult', 'fantasy', 'science fiction', 'paranormal', 'supernatural']
            for subject in ya_subjects:
                if subject in subject_text:
                    confidence += 10
        
        # Bonus série iconique
        series_lower = series_name.lower()
        for iconic in ICONIC_YA_SERIES:
            if iconic.lower() in series_lower:
                confidence += 30
                break
        
        return min(confidence, 100)

    def calculate_ya_score(self, book: Dict, series_name: str) -> int:
        """Calculer score YA spécialisé"""
        score = 0
        
        title = book.get('title', '').lower()
        subjects = book.get('subject', [])
        authors = book.get('author_name', [])
        
        # Score titre
        for keyword in YA_FANTASY_KEYWORDS:
            if keyword.lower() in title:
                score += 2
        
        # Score sujets
        if subjects:
            subject_text = ' '.join(subjects).lower()
            ya_indicators = [
                'young adult', 'teen', 'fantasy', 'science fiction',
                'paranormal', 'supernatural', 'dystopian', 'magic'
            ]
            for indicator in ya_indicators:
                if indicator in subject_text:
                    score += 3
        
        # Score auteur
        if authors:
            author_text = ' '.join(authors).lower()
            for ya_author in YA_FANTASY_AUTHORS:
                if ya_author.lower() in author_text:
                    score += 5
        
        # Score série iconique
        for series in ICONIC_YA_SERIES:
            if series.lower() in series_name.lower():
                score += 4
        
        return score

    def detect_ya_category(self, book: Dict) -> str:
        """Détecter catégorie YA (roman par défaut)"""
        subjects = book.get('subject', [])
        title = book.get('title', '').lower()
        
        # Analyser sujets
        if subjects:
            subject_text = ' '.join(subjects).lower()
            if any(word in subject_text for word in ['graphic novel', 'comic', 'manga']):
                return 'bd'
        
        # Analyser titre pour manga
        if any(word in title for word in ['manga', 'vol', 'chapter']):
            return 'manga'
        
        return 'roman'  # YA Fantasy/SF est principalement roman

    def detect_ya_genre(self, book: Dict) -> str:
        """Détecter genre YA spécifique"""
        title = book.get('title', '').lower()
        subjects = book.get('subject', [])
        
        # Analyser titre et sujets
        text = title
        if subjects:
            text += ' ' + ' '.join(subjects).lower()
        
        # Fantasy sous-genres
        if any(word in text for word in ['vampire', 'werewolf', 'supernatural', 'paranormal']):
            return 'paranormal_fantasy'
        elif any(word in text for word in ['urban', 'modern', 'contemporary']):
            return 'urban_fantasy'
        elif any(word in text for word in ['dragon', 'wizard', 'magic', 'medieval', 'kingdom']):
            return 'high_fantasy'
        elif any(word in text for word in ['academy', 'school', 'university']):
            return 'academy_fantasy'
        
        # Science Fiction sous-genres
        elif any(word in text for word in ['dystopian', 'dystopia', 'post-apocalyptic']):
            return 'dystopian_sf'
        elif any(word in text for word in ['space', 'alien', 'galaxy', 'planet']):
            return 'space_opera'
        elif any(word in text for word in ['time travel', 'time loop', 'temporal']):
            return 'time_travel_sf'
        elif any(word in text for word in ['cyborg', 'android', 'ai', 'robot']):
            return 'cyberpunk_sf'
        
        # Défaut
        elif any(word in text for word in ['fantasy', 'magic', 'supernatural']):
            return 'fantasy'
        elif any(word in text for word in ['science fiction', 'sci-fi', 'future']):
            return 'science_fiction'
        
        return 'young_adult'

    def get_primary_author(self, book: Dict) -> str:
        """Obtenir auteur principal"""
        authors = book.get('author_name', [])
        if authors:
            return authors[0]
        return "Unknown"

    def get_ya_match_reasons(self, book: Dict, series_name: str, volume_num: str) -> List[str]:
        """Obtenir raisons de correspondance YA"""
        reasons = []
        
        # Volume
        try:
            vol_int = int(volume_num)
            reasons.append(f"ya_volume_{vol_int}")
        except:
            reasons.append("ya_volume_pattern")
        
        # Auteur YA
        authors = book.get('author_name', [])
        if authors:
            author_text = ' '.join(authors).lower()
            for ya_author in YA_FANTASY_AUTHORS:
                if ya_author.lower() in author_text:
                    reasons.append(f"ya_author_{ya_author.lower().replace(' ', '_')}")
                    break
        
        # Genre YA
        genre = self.detect_ya_genre(book)
        reasons.append(f"genre_{genre}")
        
        # Série iconique
        for series in ICONIC_YA_SERIES:
            if series.lower() in series_name.lower():
                reasons.append(f"iconic_series_{series.lower().replace(' ', '_')}")
                break
        
        # Mots-clés YA
        title_lower = series_name.lower()
        for keyword in YA_FANTASY_KEYWORDS[:20]:  # Top 20
            if keyword.lower() in title_lower:
                reasons.append(f"ya_keyword_{keyword.lower().replace(' ', '_')}")
                break
        
        return reasons

    def run_ya_ultra_harvest(self):
        """Exécuter Ultra Harvest YA Fantasy/SF"""
        self.logger.info("🚀 Démarrage Ultra Harvest YA Fantasy/Science Fiction")
        
        # Générer requêtes
        queries = self.get_ya_fantasy_search_queries()
        self.logger.info(f"Requêtes YA Fantasy/SF: {len(queries)} requêtes générées")
        
        for i, query in enumerate(queries, 1):
            if self.total_api_calls >= MAX_REQUESTS:
                self.logger.info("Limite API atteinte, arrêt")
                break
                
            self.logger.info(f"[{i}/{len(queries)}] Analyse query: {query}")
            
            # Rechercher livres
            books = self.search_ya_fantasy_books(query)
            
            if not books:
                continue
            
            # Détecter séries
            series_candidates = self.detect_ya_series_from_books(books)
            
            # Filtrer nouvelles séries
            new_series = []
            for candidate in series_candidates:
                if candidate.name.lower() not in self.discovered_series:
                    new_series.append(candidate)
                    self.discovered_series.add(candidate.name.lower())
            
            self.new_series.extend(new_series)
            
            self.logger.info(f"Query {query}: {len(new_series)} nouvelles séries YA découvertes")
            
            # Afficher top découvertes
            if new_series:
                for series in sorted(new_series, key=lambda x: x.confidence, reverse=True)[:2]:
                    self.logger.info(f"  ⭐ {series.name} ({series.genre}) - {series.confidence}%")
        
        # Rapport final
        self.generate_ya_final_report()

    def generate_ya_final_report(self):
        """Générer rapport final YA"""
        duration = time.time() - self.session_start_time
        
        self.logger.info("\n" + "="*80)
        self.logger.info("🎯 RAPPORT FINAL - ULTRA HARVEST YA FANTASY/SCIENCE FICTION")
        self.logger.info("="*80)
        self.logger.info(f"Nouvelles séries YA découvertes: {len(self.new_series)}")
        self.logger.info(f"Livres analysés: {self.total_books_analyzed}")
        self.logger.info(f"API calls utilisés: {self.total_api_calls}/{MAX_REQUESTS}")
        self.logger.info(f"Durée: {duration:.2f} secondes")
        
        if self.total_books_analyzed > 0:
            self.logger.info(f"Taux de découverte: {len(self.new_series)/self.total_books_analyzed*100:.2f}%")
        
        # Top découvertes par genre
        if self.new_series:
            self.logger.info("\n🏆 TOP 15 DÉCOUVERTES YA FANTASY/SF:")
            top_series = sorted(self.new_series, key=lambda x: (x.confidence, x.ya_score), reverse=True)[:15]
            for i, series in enumerate(top_series, 1):
                self.logger.info(f"{i:2d}. {series.name} ({series.genre}) - {series.confidence}% - YA Score: {series.ya_score}")
        
        # Répartition par genre
        if self.new_series:
            genre_counts = {}
            for series in self.new_series:
                genre = series.genre
                genre_counts[genre] = genre_counts.get(genre, 0) + 1
            
            self.logger.info("\n📊 RÉPARTITION PAR GENRE:")
            for genre, count in sorted(genre_counts.items(), key=lambda x: x[1], reverse=True):
                self.logger.info(f"  {genre}: {count} séries")
        
        # Sauvegarde
        self.save_ya_results()

    def save_ya_results(self):
        """Sauvegarder résultats YA"""
        if not self.new_series:
            self.logger.info("Aucune nouvelle série YA à sauvegarder")
            return
        
        # Charger base existante
        try:
            with open('/app/backend/data/extended_series_database.json', 'r', encoding='utf-8') as f:
                existing_series = json.load(f)
        except:
            existing_series = []
        
        # Ajouter nouvelles séries
        for series in self.new_series:
            new_entry = {
                "name": series.name,
                "category": series.category,
                "score": series.confidence,
                "keywords": series.match_reasons,
                "authors": [series.author],
                "variations": series.sample_titles,
                "volumes": series.volumes,
                "languages": ["en", "fr"],
                "description": f"Série YA {series.genre} découverte via Ultra Harvest (confiance {series.confidence}%, YA score {series.ya_score})",
                "first_published": None,
                "status": "active",
                "genre": series.genre,
                "ya_score": series.ya_score,
                "ol_key": series.ol_key,
                "discovery_method": "ultra_harvest_ya_fantasy_sf_50",
                "discovery_date": time.strftime("%Y-%m-%d")
            }
            existing_series.append(new_entry)
        
        # Sauvegarder
        backup_file = f'/app/backend/data/backup_before_ya_fantasy_sf_{int(time.time())}.json'
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(existing_series[:-len(self.new_series)], f, indent=2, ensure_ascii=False)
        
        with open('/app/backend/data/extended_series_database.json', 'w', encoding='utf-8') as f:
            json.dump(existing_series, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"✅ Sauvegarde YA réussie: {len(self.new_series)} nouvelles séries ajoutées")
        self.logger.info(f"Backup créé: {backup_file}")

if __name__ == "__main__":
    harvester = UltraHarvestYAFantasySF()
    harvester.run_ya_ultra_harvest()