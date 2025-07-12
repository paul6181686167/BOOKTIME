#!/usr/bin/env python3
"""
Ultra Harvest 100k AutoExpansion OpenLibrary - Focus Auteurs Découverts
Mission: Maximiser découvertes séries des auteurs trouvés dans Session 81.30
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

# Auteurs découverts dans Session 81.30 + extensions
DISCOVERED_AUTHORS = [
    # Auteurs principaux découverts Session 81.30
    "Sarah J. Maas", "Cassandra Clare", "Leigh Bardugo", "Victoria Aveyard",
    "Kiera Cass", "Scott Westerfeld", "Ally Condie", "Jennifer L. Armentrout",
    "Elise Kova", "Alexandra Bracken", "Marie Lu", "Tahereh Mafi",
    "Renée Ahdieh", "Sabaa Tahir", "Tomi Adeyemi", "Adrienne Young",
    "Maggie Stiefvater", "Holly Black", "Richelle Mead", "Marissa Meyer",
    
    # Extensions auteurs YA populaires
    "Stephanie Meyer", "Suzanne Collins", "Veronica Roth", "James Dashner",
    "Pierce Brown", "Kass Morgan", "Beth Revis", "Kami Garcia",
    "Margaret Stohl", "Laini Taylor", "Kiersten White", "Rainbow Rowell",
    "Stephanie Perkins", "Anna Todd", "Colleen Hoover", "Cassandra Jean",
    
    # Auteurs Fantasy/SF établis
    "Brandon Sanderson", "Patrick Rothfuss", "Jim Butcher", "Kim Harrison",
    "Patricia Briggs", "Kelley Armstrong", "Laurell K. Hamilton", "Anne Rice",
    "Charlaine Harris", "Sherrilyn Kenyon", "Gena Showalter", "Kresley Cole",
    
    # Auteurs émergents YA
    "Stephanie Hans", "Rebecca Ross", "Adrienne Tooley", "Akshaya Raman",
    "Chloe Gong", "Xiran Jay Zhao", "Erin A. Craig", "Hafsah Faizal",
    "Namina Forna", "Tracy Wolff", "Jennifer Lynn Barnes", "Kerri Maniscalco",
    
    # Variantes orthographiques
    "Sarah Maas", "J. L. Armentrout", "Jennifer Armentrout", "J.L. Armentrout"
]

# Séries connues par auteur (pour éviter doublons)
KNOWN_AUTHOR_SERIES = {
    "Sarah J. Maas": ["Throne of Glass", "A Court of", "Crescent City"],
    "Cassandra Clare": ["Mortal Instruments", "Infernal Devices", "Dark Artifices"],
    "Leigh Bardugo": ["Shadow and Bone", "Six of Crows", "King of Scars"],
    "Victoria Aveyard": ["Red Queen", "Realm Breaker"],
    "Kiera Cass": ["The Selection", "The Siren"],
    "Scott Westerfeld": ["Uglies", "Leviathan", "Midnighters"],
    "Ally Condie": ["Matched", "Atlantia"],
    "Jennifer L. Armentrout": ["Covenant", "Lux", "From Blood and Ash"],
    "Suzanne Collins": ["The Hunger Games", "Underland Chronicles"],
    "Veronica Roth": ["Divergent", "Carve the Mark"],
    "Stephanie Meyer": ["Twilight", "The Host"],
    "Marissa Meyer": ["Lunar Chronicles", "Renegades", "Gilded"]
}

@dataclass
class AuthorSeriesCandidate:
    name: str
    author: str
    category: str
    confidence: int
    match_reasons: List[str]
    volumes: int
    author_score: int
    ol_key: str
    sample_titles: List[str]
    publication_years: List[int]

class UltraHarvestDiscoveredAuthors:
    def __init__(self):
        self.setup_logging()
        self.discovered_series: Set[str] = set()
        self.new_series: List[AuthorSeriesCandidate] = []
        self.total_books_analyzed = 0
        self.total_api_calls = 0
        self.session_start_time = time.time()
        self.authors_processed = 0
        
        # Charger base existante
        self.load_existing_series()
        
        # Patterns de détection optimisés pour auteurs
        self.setup_author_detection_patterns()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('/app/backend/ultra_harvest_discovered_authors.log'),
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

    def setup_author_detection_patterns(self):
        """Patterns ultra-optimisés pour séries d'auteurs"""
        self.series_patterns = [
            # Patterns séries classiques
            r'(.+?)\s+(?:book|novel|tome|volume|vol)\s*(\d+)',
            r'(.+?)\s+(?:part|partie|chapter)\s*(\d+)',
            r'(.+?)\s+#(\d+)',
            r'(.+?)\s+(\d+)(?:st|nd|rd|th)?\s+(?:book|novel|installment)',
            
            # Patterns séries nommées
            r'(.+?)\s+(?:series|saga|trilogy|duology|quartet|chronicles?)\s*(\d+)',
            r'(.+?)\s+(?:collection|cycle|sequence)\s*(\d+)',
            
            # Patterns titres avec numérotation
            r'(.+?)\s+(\d+)(?:\s*[-:]\s*.+)?$',
            r'(.+?)\s+(?:no\.?|number|n°|num)\s*(\d+)',
            
            # Patterns sous-titres
            r'(.+?):\s*(.+?)\s+(\d+)',
            r'(.+?)\s*-\s*(.+?)\s+(\d+)',
            
            # Patterns fantasy/SF spécifiques
            r'(.+?)\s+(?:legend|tale|story|chronicle)\s*(\d+)',
            r'(.+?)\s+(?:realm|world|kingdom|empire)\s*(\d+)',
            r'(.+?)\s+(?:academy|school|institute)\s*(\d+)',
            
            # Patterns romance
            r'(.+?)\s+(?:love|heart|desire|passion)\s*(\d+)',
            r'(.+?)\s+(?:prince|princess|duke|lord|lady)\s*(\d+)',
            
            # Patterns ultra-permissifs
            r'(.+?)\s+(\d+)$',
            r'(.+?)\s+(?:episode|arc|phase)\s*(\d+)',
        ]

    def search_author_books(self, author: str) -> List[Dict]:
        """Rechercher tous les livres d'un auteur spécifique"""
        all_books = []
        
        # Variantes de recherche pour chaque auteur
        search_variants = [
            f'author:"{author}"',
            f'author:{author}',
            f'author:"{author.lower()}"',
            f'author:{author.replace(" ", "+")}',
            # Recherche par nom/prénom inversé si applicable
        ]
        
        # Ajouter variantes nom/prénom
        if " " in author:
            parts = author.split()
            if len(parts) == 2:
                # Prénom Nom -> Nom, Prénom
                search_variants.append(f'author:"{parts[1]}, {parts[0]}"')
                # Initiales
                search_variants.append(f'author:"{parts[0][0]}. {parts[1]}"')
                search_variants.append(f'author:"{parts[1]}, {parts[0][0]}."')
        
        for variant in search_variants:
            if self.total_api_calls >= MAX_REQUESTS:
                break
                
            try:
                params = {
                    'q': variant,
                    'limit': RESULTS_PER_REQUEST,
                    'fields': 'title,author_name,subject,first_publish_year,key,isbn,publisher'
                }
                
                response = requests.get(API_BASE_URL, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                books = data.get('docs', [])
                
                self.total_api_calls += 1
                self.total_books_analyzed += len(books)
                
                # Filtrer pour s'assurer que c'est bien le bon auteur
                filtered_books = []
                for book in books:
                    authors = book.get('author_name', [])
                    if authors and self.is_matching_author(author, authors):
                        filtered_books.append(book)
                
                all_books.extend(filtered_books)
                
                self.logger.info(f"Auteur '{author}' ({variant}): {len(filtered_books)} livres trouvés")
                
                time.sleep(DELAY_BETWEEN_REQUESTS)
                
            except Exception as e:
                self.logger.error(f"Erreur recherche auteur '{author}' ({variant}): {e}")
                continue
        
        # Déduplication par titre
        unique_books = {}
        for book in all_books:
            title = book.get('title', '').lower().strip()
            if title and title not in unique_books:
                unique_books[title] = book
        
        return list(unique_books.values())

    def is_matching_author(self, target_author: str, book_authors: List[str]) -> bool:
        """Vérifier si l'auteur correspond"""
        target_lower = target_author.lower()
        
        for book_author in book_authors:
            book_author_lower = book_author.lower()
            
            # Correspondance exacte
            if target_lower == book_author_lower:
                return True
                
            # Correspondance partielle (nom de famille)
            target_parts = target_lower.split()
            book_parts = book_author_lower.split()
            
            if len(target_parts) >= 2 and len(book_parts) >= 2:
                # Même nom de famille
                if target_parts[-1] == book_parts[-1]:
                    # Même première lettre du prénom
                    if target_parts[0][0] == book_parts[0][0]:
                        return True
        
        return False

    def detect_author_series_from_books(self, books: List[Dict], author: str) -> List[AuthorSeriesCandidate]:
        """Détecter séries d'un auteur à partir de ses livres"""
        series_candidates = {}
        
        for book in books:
            title = book.get('title', '').strip()
            if not title:
                continue
                
            # Tester tous les patterns
            for pattern in self.series_patterns:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    
                    # Gérer patterns avec 2 ou 3 groupes
                    if len(groups) == 2:
                        series_name = groups[0].strip()
                        volume_num = groups[1]
                    elif len(groups) == 3:
                        # Pattern avec sous-titre: Group1 - Group2 Number
                        series_name = f"{groups[0].strip()} - {groups[1].strip()}"
                        volume_num = groups[2]
                    else:
                        continue
                    
                    # Validation série
                    if not self.is_valid_author_series_name(series_name, author):
                        continue
                    
                    # Nettoyer le nom de série
                    series_name = self.clean_author_series_name(series_name)
                    series_key = f"{author.lower()}:{series_name.lower()}"
                    
                    if series_key in self.discovered_series or series_name.lower() in self.discovered_series:
                        continue
                    
                    # Vérifier séries connues
                    if self.is_known_series(author, series_name):
                        continue
                    
                    # Calculer confiance auteur
                    confidence = self.calculate_author_confidence(book, series_name, volume_num, author)
                    author_score = self.calculate_author_score(book, author)
                    
                    if confidence >= CONFIDENCE_THRESHOLD:
                        if series_key not in series_candidates:
                            series_candidates[series_key] = {
                                'name': series_name,
                                'author': author,
                                'category': self.detect_category(book),
                                'confidence': confidence,
                                'match_reasons': [],
                                'volumes': set(),
                                'author_score': author_score,
                                'ol_key': book.get('key', ''),
                                'sample_titles': [],
                                'publication_years': []
                            }
                        
                        # Mettre à jour les informations
                        candidate = series_candidates[series_key]
                        candidate['volumes'].add(volume_num)
                        candidate['sample_titles'].append(title)
                        candidate['confidence'] = max(candidate['confidence'], confidence)
                        candidate['author_score'] = max(candidate['author_score'], author_score)
                        
                        # Année de publication
                        year = book.get('first_publish_year')
                        if year and isinstance(year, int):
                            candidate['publication_years'].append(year)
                        
                        # Raisons de correspondance
                        reasons = self.get_author_match_reasons(book, series_name, volume_num, author)
                        candidate['match_reasons'].extend(reasons)
                        
                        break
        
        # Convertir en AuthorSeriesCandidate
        results = []
        for candidate in series_candidates.values():
            candidate['volumes'] = len(candidate['volumes'])
            candidate['match_reasons'] = list(set(candidate['match_reasons']))
            candidate['sample_titles'] = list(set(candidate['sample_titles']))[:3]
            candidate['publication_years'] = sorted(set(candidate['publication_years']))[:3]
            
            results.append(AuthorSeriesCandidate(**candidate))
        
        return results

    def is_valid_author_series_name(self, name: str, author: str) -> bool:
        """Valider nom de série pour un auteur"""
        if len(name) < 2 or len(name) > 100:
            return False
            
        # Éviter noms trop génériques
        generic_names = [
            'book', 'novel', 'story', 'tale', 'collection', 'anthology',
            'volume', 'tome', 'chapter', 'part', 'number', 'series'
        ]
        
        name_lower = name.lower()
        if any(generic in name_lower for generic in generic_names):
            if len(name) < 10:  # Noms génériques courts
                return False
        
        # Éviter noms avec nom d'auteur seulement
        author_parts = author.lower().split()
        if all(part in name_lower for part in author_parts):
            if len(name) < len(author) + 5:  # Nom série = nom auteur + peu de mots
                return False
        
        return True

    def is_known_series(self, author: str, series_name: str) -> bool:
        """Vérifier si la série est déjà connue pour cet auteur"""
        known_series = KNOWN_AUTHOR_SERIES.get(author, [])
        series_lower = series_name.lower()
        
        for known in known_series:
            if known.lower() in series_lower or series_lower in known.lower():
                return True
                
        return False

    def clean_author_series_name(self, name: str) -> str:
        """Nettoyer nom de série d'auteur"""
        # Supprimer préfixes/suffixes
        name = re.sub(r'^(the|a|an|le|la|les)\s+', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s+(series|saga|trilogy|duology|collection)$', '', name, flags=re.IGNORECASE)
        
        # Nettoyer caractères spéciaux
        name = re.sub(r'[^\w\s\-\'\"&]', '', name)
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name

    def calculate_author_confidence(self, book: Dict, series_name: str, volume_num: str, author: str) -> int:
        """Calculer confiance spécialisée auteur"""
        confidence = 50  # Base
        
        # Bonus volume valide
        try:
            vol_int = int(volume_num)
            if 1 <= vol_int <= 15:
                confidence += 25
            elif 16 <= vol_int <= 30:
                confidence += 15
        except:
            confidence += 5  # Pattern détecté même si numéro invalide
        
        # Bonus auteur découvert
        if author in DISCOVERED_AUTHORS:
            confidence += 20
        
        # Bonus année de publication
        year = book.get('first_publish_year')
        if year and isinstance(year, int):
            if 1990 <= year <= 2024:
                confidence += 10
        
        # Bonus ISBN (signe de qualité)
        isbn = book.get('isbn')
        if isbn:
            confidence += 10
        
        # Bonus sujets pertinents
        subjects = book.get('subject', [])
        if subjects:
            subject_text = ' '.join(subjects).lower()
            relevant_subjects = [
                'fiction', 'fantasy', 'science fiction', 'young adult',
                'romance', 'mystery', 'thriller', 'adventure'
            ]
            for subject in relevant_subjects:
                if subject in subject_text:
                    confidence += 5
                    break
        
        return min(confidence, 100)

    def calculate_author_score(self, book: Dict, author: str) -> int:
        """Calculer score spécialisé auteur"""
        score = 0
        
        # Score auteur découvert
        if author in DISCOVERED_AUTHORS:
            score += 10
        
        # Score sujets
        subjects = book.get('subject', [])
        if subjects:
            subject_text = ' '.join(subjects).lower()
            relevant = ['fiction', 'fantasy', 'science fiction', 'young adult', 'romance']
            for subj in relevant:
                if subj in subject_text:
                    score += 3
        
        # Score année récente
        year = book.get('first_publish_year')
        if year and isinstance(year, int):
            if 2000 <= year <= 2024:
                score += 5
            elif 1990 <= year <= 1999:
                score += 3
        
        # Score éditeur
        publishers = book.get('publisher', [])
        if publishers:
            major_publishers = [
                'penguin', 'random house', 'harpercollins', 'macmillan',
                'simon schuster', 'hachette', 'scholastic'
            ]
            pub_text = ' '.join(publishers).lower()
            for pub in major_publishers:
                if pub in pub_text:
                    score += 5
                    break
        
        return score

    def detect_category(self, book: Dict) -> str:
        """Détecter catégorie livre"""
        subjects = book.get('subject', [])
        title = book.get('title', '').lower()
        
        # Analyser sujets
        if subjects:
            subject_text = ' '.join(subjects).lower()
            if any(word in subject_text for word in ['graphic novel', 'comic', 'manga']):
                return 'bd'
            elif any(word in subject_text for word in ['manga', 'anime']):
                return 'manga'
        
        # Analyser titre
        if any(word in title for word in ['manga', 'vol', 'tome']):
            return 'manga'
        elif any(word in title for word in ['comic', 'graphic']):
            return 'bd'
        
        return 'roman'  # Défaut

    def get_author_match_reasons(self, book: Dict, series_name: str, volume_num: str, author: str) -> List[str]:
        """Obtenir raisons de correspondance auteur"""
        reasons = []
        
        # Volume
        try:
            vol_int = int(volume_num)
            reasons.append(f"author_volume_{vol_int}")
        except:
            reasons.append("author_volume_pattern")
        
        # Auteur découvert
        if author in DISCOVERED_AUTHORS:
            reasons.append(f"discovered_author_{author.lower().replace(' ', '_')}")
        
        # Année
        year = book.get('first_publish_year')
        if year and isinstance(year, int):
            if 2000 <= year <= 2024:
                reasons.append("recent_publication")
            elif 1990 <= year <= 1999:
                reasons.append("modern_publication")
        
        # Sujets
        subjects = book.get('subject', [])
        if subjects:
            subject_text = ' '.join(subjects).lower()
            if 'young adult' in subject_text:
                reasons.append("ya_genre")
            elif 'fantasy' in subject_text:
                reasons.append("fantasy_genre")
            elif 'science fiction' in subject_text:
                reasons.append("sf_genre")
            elif 'romance' in subject_text:
                reasons.append("romance_genre")
        
        # ISBN qualité
        isbn = book.get('isbn')
        if isbn:
            reasons.append("isbn_quality")
        
        return reasons

    def run_discovered_authors_harvest(self):
        """Exécuter Ultra Harvest sur auteurs découverts"""
        self.logger.info("🚀 Démarrage Ultra Harvest Auteurs Découverts")
        self.logger.info(f"Auteurs ciblés: {len(DISCOVERED_AUTHORS)} auteurs")
        
        for i, author in enumerate(DISCOVERED_AUTHORS, 1):
            if self.total_api_calls >= MAX_REQUESTS:
                self.logger.info("Limite API atteinte, arrêt")
                break
                
            self.logger.info(f"[{i}/{len(DISCOVERED_AUTHORS)}] Analyse auteur: {author}")
            
            # Rechercher livres de l'auteur
            books = self.search_author_books(author)
            
            if not books:
                self.logger.info(f"Aucun livre trouvé pour {author}")
                continue
            
            # Détecter séries
            series_candidates = self.detect_author_series_from_books(books, author)
            
            # Filtrer nouvelles séries
            new_series = []
            for candidate in series_candidates:
                series_key = f"{author.lower()}:{candidate.name.lower()}"
                if (series_key not in self.discovered_series and 
                    candidate.name.lower() not in self.discovered_series):
                    new_series.append(candidate)
                    self.discovered_series.add(series_key)
                    self.discovered_series.add(candidate.name.lower())
            
            self.new_series.extend(new_series)
            self.authors_processed += 1
            
            self.logger.info(f"Auteur {author}: {len(new_series)} nouvelles séries découvertes")
            
            # Afficher top découvertes
            if new_series:
                for series in sorted(new_series, key=lambda x: x.confidence, reverse=True)[:2]:
                    self.logger.info(f"  ⭐ {series.name} - {series.confidence}% (Score: {series.author_score})")
        
        # Rapport final
        self.generate_authors_final_report()

    def generate_authors_final_report(self):
        """Générer rapport final auteurs"""
        duration = time.time() - self.session_start_time
        
        self.logger.info("\n" + "="*80)
        self.logger.info("🎯 RAPPORT FINAL - ULTRA HARVEST AUTEURS DÉCOUVERTS")
        self.logger.info("="*80)
        self.logger.info(f"Auteurs analysés: {self.authors_processed}/{len(DISCOVERED_AUTHORS)}")
        self.logger.info(f"Nouvelles séries découvertes: {len(self.new_series)}")
        self.logger.info(f"Livres analysés: {self.total_books_analyzed}")
        self.logger.info(f"API calls utilisés: {self.total_api_calls}/{MAX_REQUESTS}")
        self.logger.info(f"Durée: {duration:.2f} secondes")
        
        if self.total_books_analyzed > 0:
            self.logger.info(f"Taux de découverte: {len(self.new_series)/self.total_books_analyzed*100:.2f}%")
        
        # Top découvertes par auteur
        if self.new_series:
            self.logger.info("\n🏆 TOP 15 DÉCOUVERTES PAR AUTEUR:")
            top_series = sorted(self.new_series, key=lambda x: (x.confidence, x.author_score), reverse=True)[:15]
            for i, series in enumerate(top_series, 1):
                years = f" ({min(series.publication_years)}-{max(series.publication_years)})" if series.publication_years else ""
                self.logger.info(f"{i:2d}. {series.name} - {series.author} - {series.confidence}%{years}")
        
        # Répartition par auteur
        if self.new_series:
            author_counts = {}
            for series in self.new_series:
                author = series.author
                author_counts[author] = author_counts.get(author, 0) + 1
            
            self.logger.info("\n📊 RÉPARTITION PAR AUTEUR (Top 10):")
            top_authors = sorted(author_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            for author, count in top_authors:
                self.logger.info(f"  {author}: {count} séries")
        
        # Sauvegarde
        self.save_authors_results()

    def save_authors_results(self):
        """Sauvegarder résultats auteurs"""
        if not self.new_series:
            self.logger.info("Aucune nouvelle série auteur à sauvegarder")
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
                "description": f"Série de {series.author} découverte via Ultra Harvest (confiance {series.confidence}%, score auteur {series.author_score})",
                "first_published": min(series.publication_years) if series.publication_years else None,
                "status": "active",
                "author_score": series.author_score,
                "publication_years": series.publication_years,
                "ol_key": series.ol_key,
                "discovery_method": "ultra_harvest_discovered_authors_50",
                "discovery_date": time.strftime("%Y-%m-%d")
            }
            existing_series.append(new_entry)
        
        # Sauvegarder
        backup_file = f'/app/backend/data/backup_before_discovered_authors_{int(time.time())}.json'
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(existing_series[:-len(self.new_series)], f, indent=2, ensure_ascii=False)
        
        with open('/app/backend/data/extended_series_database.json', 'w', encoding='utf-8') as f:
            json.dump(existing_series, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"✅ Sauvegarde auteurs réussie: {len(self.new_series)} nouvelles séries ajoutées")
        self.logger.info(f"Backup créé: {backup_file}")

if __name__ == "__main__":
    harvester = UltraHarvestDiscoveredAuthors()
    harvester.run_discovered_authors_harvest()