#!/usr/bin/env python3
"""
Ultra Harvest 100k AutoExpansion OpenLibrary - Major Publishers Focus
Mission: Maximiser découvertes séries avec confiance 50% sur éditeurs majeurs
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
CONFIDENCE_THRESHOLD = 50  # Abaissé à 50% pour maximiser découvertes
API_BASE_URL = "https://openlibrary.org/search.json"
MAX_REQUESTS = 200  # Respecter les limites API
DELAY_BETWEEN_REQUESTS = 0.5  # Respectueux
RESULTS_PER_REQUEST = 50  # Maximiser efficacité

# Éditeurs majeurs ciblés (29 éditeurs)
MAJOR_PUBLISHERS = [
    "RELX Group", "Reed Elsevier", "Elsevier",
    "Thomson Reuters", "Reuters",
    "Bertelsmann", "Penguin Random House", "Penguin", "Random House",
    "Pearson", "Pearson Education",
    "Wolters Kluwer",
    "Hachette Livre", "Hachette",
    "HarperCollins", "Harper", "Collins",
    "Wiley", "John Wiley",
    "Springer Nature", "Springer", "Nature Publishing",
    "Phoenix Publishing & Media", "Phoenix Publishing",
    "Shueisha",
    "Scholastic", "Scholastic Inc",
    "Holtzbrinck", "Macmillan", "Macmillan Publishers",
    "McGraw-Hill Education", "McGraw-Hill", "McGraw Hill",
    "Kodansha",
    "Cengage Learning", "Cengage",
    "China South Publishing & Media", "China South Publishing",
    "Informa", "Informa plc",
    "Kadokawa Publishing", "Kadokawa",
    "Simon & Schuster", "Simon Schuster",
    "Klett Gruppe", "Klett",
    "Grupo Planeta", "Planeta",
    "Editis",
    "Madrigall", "Gallimard", "Flammarion",
    "Media-Participations", "Media Participations",
    "Lefebvre-Sarrut",
    "Albin Michel",
    "Shogakukan",
    "Bonnier Group", "Bonnier"
]

@dataclass
class SeriesCandidate:
    name: str
    author: str
    category: str
    confidence: int
    match_reasons: List[str]
    volumes: int
    publisher: str
    ol_key: str
    sample_titles: List[str]

class UltraHarvestMajorPublishers:
    def __init__(self):
        self.setup_logging()
        self.discovered_series: Set[str] = set()
        self.new_series: List[SeriesCandidate] = []
        self.total_books_analyzed = 0
        self.total_api_calls = 0
        self.session_start_time = time.time()
        
        # Charger base existante
        self.load_existing_series()
        
        # Patterns de détection optimisés pour éditeurs majeurs
        self.setup_detection_patterns()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/app/backend/ultra_harvest_major_publishers.log'),
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

    def setup_detection_patterns(self):
        """Patterns ultra-optimisés pour éditeurs majeurs (confiance 50%)"""
        self.series_patterns = [
            # Academic & Professional Series (Pearson, McGraw-Hill, Wiley, Springer)
            r'(.+?)\s+(?:series|handbook|guide|manual|textbook)\s*(?:volume|vol|part|book)?\s*(\d+)',
            r'(.+?)\s+(?:edition|ed\.?)\s*(\d+)',
            r'(.+?)\s+(?:course|level|grade)\s*(\d+)',
            r'(.+?)\s+(?:advanced|intermediate|basic)\s+(\d+)',
            
            # Fiction Series (Penguin Random House, HarperCollins, Hachette)
            r'(.+?)\s+(?:book|novel|story)\s*(\d+)',
            r'(.+?)\s+(?:part|tome|volume)\s*(\d+)',
            r'(.+?)\s+#(\d+)',
            r'(.+?)\s+(\d+)(?:st|nd|rd|th)?\s+(?:book|novel|story)',
            
            # Manga & Comics (Shueisha, Kodansha, Shogakukan)
            r'(.+?)\s+(?:vol|volume|tome)\s*(\d+)',
            r'(.+?)\s+(?:chapter|chapitre)\s*(\d+)',
            r'(.+?)\s+(\d+)(?:巻|話|集)',
            
            # Reference & Encyclopedia (Britannica, Oxford, Cambridge)
            r'(.+?)\s+(?:encyclopedia|encyclopaedia|dictionary)\s*(?:volume|vol)?\s*(\d+)',
            r'(.+?)\s+(?:reference|handbook|companion)\s*(\d+)',
            
            # Children's Series (Scholastic, Disney, etc.)
            r'(.+?)\s+(?:adventures?|stories?)\s*(\d+)',
            r'(.+?)\s+(?:collection|anthology)\s*(\d+)',
            
            # Ultra-permissive patterns (confiance 50%)
            r'(.+?)\s+(\d+)(?:\s*[-:]\s*.+)?$',
            r'(.+?)\s+(?:no\.?|number|n°)\s*(\d+)',
            r'(.+?)\s+(?:phase|stage|step)\s*(\d+)',
            r'(.+?)\s+(?:season|saison)\s*(\d+)',
        ]
        
        # Mots-clés spécialisés par éditeur
        self.publisher_keywords = {
            'academic': ['textbook', 'handbook', 'manual', 'guide', 'course', 'study', 'reference'],
            'fiction': ['novel', 'story', 'adventure', 'mystery', 'fantasy', 'romance', 'thriller'],
            'manga': ['volume', 'chapter', 'tome', 'vol', 'manga', 'anime'],
            'children': ['stories', 'adventures', 'tales', 'friends', 'family', 'kids'],
            'professional': ['business', 'management', 'finance', 'medical', 'legal', 'technical']
        }

    def search_books_by_publisher(self, publisher: str) -> List[Dict]:
        """Rechercher livres par éditeur spécifique"""
        all_books = []
        
        # Variantes de requête pour chaque éditeur
        search_queries = [
            f'publisher:"{publisher}"',
            f'publisher:{publisher}',
            f'publisher:"{publisher.lower()}"',
            f'publisher:{publisher.replace(" ", "+")}'
        ]
        
        for query in search_queries:
            if self.total_api_calls >= MAX_REQUESTS:
                break
                
            try:
                params = {
                    'q': query,
                    'limit': RESULTS_PER_REQUEST,
                    'fields': 'title,author_name,publisher,subject,first_publish_year,key,isbn'
                }
                
                response = requests.get(API_BASE_URL, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                books = data.get('docs', [])
                
                self.total_api_calls += 1
                self.total_books_analyzed += len(books)
                
                # Filtrer par éditeur pour éviter faux positifs
                filtered_books = []
                for book in books:
                    publishers = book.get('publisher', [])
                    if isinstance(publishers, list):
                        publishers = [p.lower() for p in publishers]
                        if any(publisher.lower() in p for p in publishers):
                            filtered_books.append(book)
                    elif isinstance(publishers, str):
                        if publisher.lower() in publishers.lower():
                            filtered_books.append(book)
                
                all_books.extend(filtered_books)
                
                self.logger.info(f"Publisher '{publisher}': {len(filtered_books)} livres trouvés")
                
                time.sleep(DELAY_BETWEEN_REQUESTS)
                
            except Exception as e:
                self.logger.error(f"Erreur recherche publisher '{publisher}': {e}")
                continue
        
        return all_books

    def detect_series_from_books(self, books: List[Dict]) -> List[SeriesCandidate]:
        """Détecter séries à partir des livres avec confiance 50%"""
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
                    
                    # Validation minimale pour confiance 50%
                    if len(series_name) < 3 or len(series_name) > 100:
                        continue
                    
                    # Nettoyer le nom de série
                    series_name = self.clean_series_name(series_name)
                    series_key = series_name.lower()
                    
                    if series_key in self.discovered_series:
                        continue
                    
                    # Calculer confiance (permissive à 50%)
                    confidence = self.calculate_confidence_permissive(book, series_name, volume_num)
                    
                    if confidence >= CONFIDENCE_THRESHOLD:
                        if series_key not in series_candidates:
                            series_candidates[series_key] = {
                                'name': series_name,
                                'author': self.get_primary_author(book),
                                'category': self.detect_category(book),
                                'confidence': confidence,
                                'match_reasons': [],
                                'volumes': set(),
                                'publisher': self.get_primary_publisher(book),
                                'ol_key': book.get('key', ''),
                                'sample_titles': []
                            }
                        
                        # Mettre à jour les informations
                        candidate = series_candidates[series_key]
                        candidate['volumes'].add(volume_num)
                        candidate['sample_titles'].append(title)
                        candidate['confidence'] = max(candidate['confidence'], confidence)
                        
                        # Raisons de correspondance
                        reasons = self.get_match_reasons(book, series_name, volume_num)
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

    def calculate_confidence_permissive(self, book: Dict, series_name: str, volume_num: str) -> int:
        """Calculer confiance avec seuil permissif 50%"""
        confidence = 50  # Base permissive
        
        # Bonus pour numéro de volume valide
        try:
            vol_int = int(volume_num)
            if 1 <= vol_int <= 50:
                confidence += 15
            elif 51 <= vol_int <= 100:
                confidence += 10
        except:
            pass
        
        # Bonus pour auteur connu
        authors = book.get('author_name', [])
        if authors:
            confidence += 10
        
        # Bonus pour éditeur majeur
        publishers = book.get('publisher', [])
        if publishers:
            for pub in publishers:
                if any(major_pub.lower() in pub.lower() for major_pub in MAJOR_PUBLISHERS):
                    confidence += 20
                    break
        
        # Bonus pour année de publication
        year = book.get('first_publish_year')
        if year and isinstance(year, int):
            if 1950 <= year <= 2024:
                confidence += 5
        
        # Bonus pour ISBN (signe de qualité)
        isbn = book.get('isbn')
        if isbn:
            confidence += 5
        
        # Bonus pour mots-clés spécialisés
        title_lower = series_name.lower()
        for category, keywords in self.publisher_keywords.items():
            if any(keyword in title_lower for keyword in keywords):
                confidence += 10
                break
        
        return min(confidence, 100)

    def clean_series_name(self, name: str) -> str:
        """Nettoyer nom de série"""
        # Supprimer préfixes/suffixes courants
        name = re.sub(r'^(the|a|an|le|la|les|un|une|des)\s+', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s+(series|collection|saga|suite)$', '', name, flags=re.IGNORECASE)
        
        # Nettoyer caractères spéciaux
        name = re.sub(r'[^\w\s\-\'\"&]', '', name)
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name

    def get_primary_author(self, book: Dict) -> str:
        """Obtenir auteur principal"""
        authors = book.get('author_name', [])
        if authors:
            return authors[0]
        return "Unknown"

    def get_primary_publisher(self, book: Dict) -> str:
        """Obtenir éditeur principal"""
        publishers = book.get('publisher', [])
        if publishers:
            if isinstance(publishers, list):
                return publishers[0]
            return str(publishers)
        return "Unknown"

    def detect_category(self, book: Dict) -> str:
        """Détecter catégorie avec logique éditeur"""
        subjects = book.get('subject', [])
        title = book.get('title', '').lower()
        publishers = book.get('publisher', [])
        
        # Logique spécifique par éditeur
        pub_text = ' '.join(publishers).lower() if publishers else ''
        
        # Manga (Shueisha, Kodansha, Shogakukan)
        if any(pub in pub_text for pub in ['shueisha', 'kodansha', 'shogakukan']):
            return 'manga'
        
        # BD (éditeurs européens)
        if any(pub in pub_text for pub in ['media-participations', 'dargaud', 'dupuis']):
            return 'bd'
        
        # Academic/Professional
        if any(pub in pub_text for pub in ['pearson', 'mcgraw-hill', 'wiley', 'springer']):
            return 'roman'  # Considéré comme roman pour simplifier
        
        # Fiction majeure
        if any(pub in pub_text for pub in ['penguin', 'random house', 'harpercollins', 'hachette']):
            return 'roman'
        
        # Analyse par sujet
        if subjects:
            subject_text = ' '.join(subjects).lower()
            if any(word in subject_text for word in ['comic', 'manga', 'graphic novel']):
                return 'bd'
            elif any(word in subject_text for word in ['children', 'juvenile', 'young adult']):
                return 'roman'
        
        return 'roman'  # Défaut

    def get_match_reasons(self, book: Dict, series_name: str, volume_num: str) -> List[str]:
        """Obtenir raisons de correspondance"""
        reasons = []
        
        # Volume numéroté
        try:
            vol_int = int(volume_num)
            if 1 <= vol_int <= 10:
                reasons.append(f"volume_{vol_int}")
            else:
                reasons.append("numbered_volume")
        except:
            reasons.append("volume_pattern")
        
        # Auteur
        authors = book.get('author_name', [])
        if authors:
            reasons.append("author_present")
        
        # Éditeur majeur
        publishers = book.get('publisher', [])
        if publishers:
            pub_text = ' '.join(publishers).lower()
            for major_pub in MAJOR_PUBLISHERS:
                if major_pub.lower() in pub_text:
                    reasons.append(f"major_publisher_{major_pub.lower().replace(' ', '_')}")
                    break
        
        # Pattern spécialisé
        title_lower = series_name.lower()
        for category, keywords in self.publisher_keywords.items():
            if any(keyword in title_lower for keyword in keywords):
                reasons.append(f"specialized_{category}")
                break
        
        return reasons

    def run_ultra_harvest(self):
        """Exécuter Ultra Harvest sur éditeurs majeurs"""
        self.logger.info("🚀 Démarrage Ultra Harvest Major Publishers (Confiance 50%)")
        self.logger.info(f"Éditeurs ciblés: {len(MAJOR_PUBLISHERS)} éditeurs majeurs")
        
        for i, publisher in enumerate(MAJOR_PUBLISHERS, 1):
            if self.total_api_calls >= MAX_REQUESTS:
                self.logger.info("Limite API atteinte, arrêt")
                break
                
            self.logger.info(f"[{i}/{len(MAJOR_PUBLISHERS)}] Analyse éditeur: {publisher}")
            
            # Rechercher livres
            books = self.search_books_by_publisher(publisher)
            
            if not books:
                self.logger.info(f"Aucun livre trouvé pour {publisher}")
                continue
            
            # Détecter séries
            series_candidates = self.detect_series_from_books(books)
            
            # Filtrer nouvelles séries
            new_series = []
            for candidate in series_candidates:
                if candidate.name.lower() not in self.discovered_series:
                    new_series.append(candidate)
                    self.discovered_series.add(candidate.name.lower())
            
            self.new_series.extend(new_series)
            
            self.logger.info(f"Éditeur {publisher}: {len(new_series)} nouvelles séries découvertes")
            
            # Afficher top découvertes
            if new_series:
                for series in sorted(new_series, key=lambda x: x.confidence, reverse=True)[:3]:
                    self.logger.info(f"  ⭐ {series.name} (Confiance: {series.confidence}%)")
        
        # Rapport final
        self.generate_final_report()

    def generate_final_report(self):
        """Générer rapport final"""
        duration = time.time() - self.session_start_time
        
        self.logger.info("\n" + "="*80)
        self.logger.info("🎯 RAPPORT FINAL - ULTRA HARVEST MAJOR PUBLISHERS")
        self.logger.info("="*80)
        self.logger.info(f"Nouvelles séries découvertes: {len(self.new_series)}")
        self.logger.info(f"Livres analysés: {self.total_books_analyzed}")
        self.logger.info(f"API calls utilisés: {self.total_api_calls}/{MAX_REQUESTS}")
        self.logger.info(f"Durée: {duration:.2f} secondes")
        self.logger.info(f"Taux de découverte: {len(self.new_series)/self.total_books_analyzed*100:.2f}%")
        
        # Top découvertes
        if self.new_series:
            self.logger.info("\n🏆 TOP 10 DÉCOUVERTES:")
            top_series = sorted(self.new_series, key=lambda x: x.confidence, reverse=True)[:10]
            for i, series in enumerate(top_series, 1):
                self.logger.info(f"{i:2d}. {series.name} ({series.category}) - {series.confidence}% - {series.publisher}")
        
        # Sauvegarde
        self.save_results()

    def save_results(self):
        """Sauvegarder résultats"""
        if not self.new_series:
            self.logger.info("Aucune nouvelle série à sauvegarder")
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
                "languages": ["fr", "en"],
                "description": f"Série découverte via Ultra Harvest Major Publishers (confiance {series.confidence}%)",
                "first_published": None,
                "status": "active",
                "publisher": series.publisher,
                "ol_key": series.ol_key,
                "discovery_method": "ultra_harvest_major_publishers_50",
                "discovery_date": time.strftime("%Y-%m-%d")
            }
            existing_series.append(new_entry)
        
        # Sauvegarder
        backup_file = f'/app/backend/data/backup_before_major_publishers_{int(time.time())}.json'
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(existing_series[:-len(self.new_series)], f, indent=2, ensure_ascii=False)
        
        with open('/app/backend/data/extended_series_database.json', 'w', encoding='utf-8') as f:
            json.dump(existing_series, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"✅ Sauvegarde réussie: {len(self.new_series)} nouvelles séries ajoutées")
        self.logger.info(f"Backup créé: {backup_file}")

if __name__ == "__main__":
    harvester = UltraHarvestMajorPublishers()
    harvester.run_ultra_harvest()