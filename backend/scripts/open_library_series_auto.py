#!/usr/bin/env python3
"""
🚀 PHASE 2A - AUTOMATISATION OPEN LIBRARY SÉRIES
Script automatique pour récupérer et ajouter les séries depuis Open Library

Fonctionnalités :
- Récupération automatique séries populaires Open Library
- Parsing intelligent des métadonnées
- Conversion au format EXTENDED_SERIES_DATABASE
- Ajout batch avec détection doublons
- Mise à jour système de détection
- Logs détaillés et statistiques

Utilisation :
python open_library_series_auto.py --authors="top_authors" --limit=50
python open_library_series_auto.py --categories="fantasy,mystery,manga" --limit=30
python open_library_series_auto.py --popular --limit=100
"""

import asyncio
import aiohttp
import json
import re
from typing import List, Dict, Optional, Set
from datetime import datetime
import argparse
import logging
from pathlib import Path

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/open_library_auto.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OpenLibrarySeriesAutomator:
    """Automatisation complète récupération séries Open Library"""
    
    def __init__(self):
        self.base_url = "https://openlibrary.org"
        self.session = None
        self.series_database = []
        self.stats = {
            'total_searched': 0,
            'series_found': 0,
            'series_added': 0,
            'duplicates_skipped': 0,
            'errors': 0
        }
        
        # Auteurs populaires pour récupération automatique
        self.popular_authors = [
            # Romans Fantasy/SF
            "Brandon Sanderson", "Stephen King", "Terry Pratchett",
            "George R.R. Martin", "J.R.R. Tolkien", "Robin Hobb",
            "Neil Gaiman", "Patrick Rothfuss", "Joe Abercrombie",
            "Robert Jordan", "Isaac Asimov", "Frank Herbert",
            
            # Romans Classiques/Populaires
            "Agatha Christie", "Arthur Conan Doyle", "Lee Child",
            "John Grisham", "Michael Crichton", "Dan Brown",
            "James Patterson", "Gillian Flynn", "Harlan Coben",
            "Louise Penny", "Tana French", "John le Carré",
            
            # Littérature Française
            "Michel Houellebecq", "Amélie Nothomb", "Guillaume Musso",
            "Marc Levy", "Anna Gavalda", "Katherine Pancol",
            "Virginie Despentes", "Leïla Slimani", "Delphine de Vigan",
            
            # Manga/Comics (via traductions)
            "Naoki Urasawa", "Osamu Tezuka", "Junji Ito",
            "Hiromu Arakawa", "Kentaro Miura", "Makoto Yukimura",
            "Alan Moore", "Neil Gaiman", "Frank Miller",
            "Grant Morrison", "Warren Ellis", "Brian K. Vaughan"
        ]
        
        # Catégories pour recherche ciblée
        self.categories_mapping = {
            'fantasy': ['fantasy', 'epic fantasy', 'urban fantasy', 'dark fantasy'],
            'mystery': ['mystery', 'crime', 'detective', 'thriller', 'police'],
            'scifi': ['science fiction', 'sci-fi', 'space opera', 'cyberpunk'],
            'romance': ['romance', 'contemporary romance', 'historical romance'],
            'horror': ['horror', 'supernatural', 'gothic', 'psychological horror'],
            'manga': ['manga', 'graphic novel', 'comics', 'japanese comics'],
            'classic': ['classics', 'literature', 'literary fiction', 'classic literature'],
            'adventure': ['adventure', 'action', 'thriller', 'suspense']
        }
    
    async def __aenter__(self):
        """Initialisation session async"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'BOOKTIME-SeriesAutomator/1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Fermeture session"""
        if self.session:
            await self.session.close()
    
    async def search_author_series(self, author: str, limit: int = 10) -> List[Dict]:
        """Recherche séries d'un auteur spécifique"""
        try:
            logger.info(f"🔍 Recherche séries pour auteur: {author}")
            
            # Recherche auteur
            url = f"{self.base_url}/search/authors.json"
            params = {'q': author, 'limit': 5}
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"Erreur recherche auteur {author}: {response.status}")
                    return []
                
                data = await response.json()
                if not data.get('docs'):
                    logger.warning(f"Auteur non trouvé: {author}")
                    return []
                
                author_key = data['docs'][0]['key']
                logger.info(f"Auteur trouvé: {author} ({author_key})")
            
            # Récupération œuvres de l'auteur
            url = f"{self.base_url}/authors/{author_key}/works.json"
            params = {'limit': limit * 5}  # Plus large pour filtrer
            
            async with self.session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"Erreur récupération œuvres {author}: {response.status}")
                    return []
                
                data = await response.json()
                works = data.get('entries', [])
                
                # Filtrage et parsing des séries
                series_data = []
                for work in works:
                    series_info = await self.parse_work_for_series(work, author)
                    if series_info:
                        series_data.append(series_info)
                    
                    if len(series_data) >= limit:
                        break
                
                logger.info(f"Trouvé {len(series_data)} séries pour {author}")
                return series_data
        
        except Exception as e:
            logger.error(f"Erreur recherche auteur {author}: {str(e)}")
            self.stats['errors'] += 1
            return []
    
    async def parse_work_for_series(self, work: Dict, author: str) -> Optional[Dict]:
        """Parse une œuvre pour identifier si c'est une série"""
        try:
            title = work.get('title', '').strip()
            if not title:
                return None
            
            # Détection patterns séries
            series_patterns = [
                r'(.+?)\s+(?:Book|Volume|Vol\.?|Tome|#)\s*(\d+)',
                r'(.+?)\s+(\d+)(?:st|nd|rd|th)?\s*(?:Book|Volume|Tome)',
                r'(.+?):\s*(.+)',  # "Series: Book Title"
                r'(.+?)\s+\((.+?)\s+#\d+\)',  # "Title (Series #1)"
                r'(.+?)\s+-\s+(.+)'  # "Series - Book Title"
            ]
            
            series_name = None
            for pattern in series_patterns:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    series_name = match.group(1).strip()
                    break
            
            if not series_name:
                # Vérification si titre suggère une série
                series_indicators = [
                    'saga', 'series', 'cycle', 'chronicles', 'adventures',
                    'trilogy', 'quartet', 'collection', 'omnibus'
                ]
                
                if any(indicator in title.lower() for indicator in series_indicators):
                    series_name = title
                else:
                    return None
            
            # Récupération métadonnées supplémentaires
            subjects = work.get('subjects', [])
            first_published = work.get('first_publish_date')
            
            # Détection catégorie
            category = self.detect_category(title, subjects)
            
            # Construction objet série
            series_data = {
                'name': series_name,
                'authors': [author],
                'category': category,
                'volumes': 1,  # Sera mis à jour lors de l'agrégation
                'keywords': self.extract_keywords(title, subjects),
                'variations': self.generate_variations(series_name),
                'first_published': first_published,
                'status': 'ongoing',
                'source': 'open_library_auto',
                'ol_work_key': work.get('key'),
                'description': work.get('description', ''),
                'subjects': subjects[:10],  # Limite à 10 sujets
                'languages': work.get('languages', []),
                'translations': {
                    'en': series_name,
                    'fr': series_name  # Sera amélioré avec traduction
                }
            }
            
            logger.debug(f"Série parsée: {series_name} ({category})")
            return series_data
        
        except Exception as e:
            logger.error(f"Erreur parsing œuvre {work.get('title', 'Unknown')}: {str(e)}")
            return None
    
    def detect_category(self, title: str, subjects: List[str]) -> str:
        """Détection automatique catégorie livre"""
        text = (title + ' ' + ' '.join(subjects)).lower()
        
        # Patterns BD/Comics
        comics_patterns = [
            'comic', 'graphic novel', 'manga', 'bande dessinée',
            'superhero', 'batman', 'superman', 'marvel', 'dc comics',
            'tintin', 'asterix', 'bd', 'comics'
        ]
        
        # Patterns Manga spécifiques
        manga_patterns = [
            'manga', 'anime', 'japanese comics', 'shonen', 'shojo',
            'seinen', 'josei', 'light novel', 'visual novel'
        ]
        
        # Vérification manga d'abord (plus spécifique)
        if any(pattern in text for pattern in manga_patterns):
            return 'manga'
        
        # Vérification BD/Comics
        if any(pattern in text for pattern in comics_patterns):
            return 'bd'
        
        # Par défaut: roman
        return 'roman'
    
    def extract_keywords(self, title: str, subjects: List[str]) -> List[str]:
        """Extraction mots-clés pour détection"""
        keywords = []
        
        # Mots-clés du titre
        title_words = re.findall(r'\b[a-zA-Z]{3,}\b', title.lower())
        keywords.extend(title_words[:5])  # Limite à 5 mots
        
        # Mots-clés des sujets
        subject_keywords = []
        for subject in subjects[:5]:  # Limite à 5 sujets
            words = re.findall(r'\b[a-zA-Z]{3,}\b', subject.lower())
            subject_keywords.extend(words)
        
        keywords.extend(subject_keywords[:10])  # Limite à 10 mots
        
        # Déduplication et nettoyage
        keywords = list(set(keywords))
        
        # Suppression mots trop communs
        common_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all',
            'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day',
            'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now',
            'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its',
            'let', 'put', 'say', 'she', 'too', 'use'
        }
        
        keywords = [kw for kw in keywords if kw not in common_words]
        
        return keywords[:15]  # Limite finale à 15 mots-clés
    
    def generate_variations(self, series_name: str) -> List[str]:
        """Génération variations nom série pour détection"""
        variations = [series_name]
        
        # Variations avec/sans articles
        articles = ['the', 'a', 'an', 'le', 'la', 'les', 'un', 'une', 'des']
        for article in articles:
            # Ajout article
            variations.append(f"{article} {series_name}")
            variations.append(f"{article.title()} {series_name}")
            
            # Suppression article
            if series_name.lower().startswith(article + ' '):
                variations.append(series_name[len(article)+1:])
        
        # Variations abréviations
        abbrev_map = {
            'and': '&',
            '&': 'and',
            'of': '',
            'the': '',
            'Chronicles': 'Chron',
            'Adventures': 'Adv',
            'Legends': 'Leg'
        }
        
        for full, abbrev in abbrev_map.items():
            if full in series_name:
                variations.append(series_name.replace(full, abbrev))
        
        # Variations casse
        variations.extend([
            series_name.lower(),
            series_name.upper(),
            series_name.title()
        ])
        
        # Déduplication
        return list(set(variations))
    
    async def search_popular_series(self, limit: int = 50) -> List[Dict]:
        """Recherche séries populaires génériques"""
        logger.info(f"🔍 Recherche {limit} séries populaires")
        
        # Termes de recherche pour séries populaires
        search_terms = [
            'fantasy series', 'mystery series', 'science fiction series',
            'romance series', 'thriller series', 'adventure series',
            'manga series', 'comic series', 'graphic novel series',
            'book series', 'novel series', 'saga books'
        ]
        
        all_series = []
        
        for term in search_terms:
            try:
                logger.info(f"Recherche avec terme: {term}")
                
                url = f"{self.base_url}/search.json"
                params = {
                    'q': term,
                    'limit': limit // len(search_terms) + 5,
                    'has_fulltext': 'true'
                }
                
                async with self.session.get(url, params=params) as response:
                    if response.status != 200:
                        logger.error(f"Erreur recherche {term}: {response.status}")
                        continue
                    
                    data = await response.json()
                    works = data.get('docs', [])
                    
                    for work in works:
                        series_info = await self.parse_search_result_for_series(work)
                        if series_info:
                            all_series.append(series_info)
                
                # Limite pour éviter too many requests
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Erreur recherche terme {term}: {str(e)}")
                continue
        
        # Déduplication par nom de série
        unique_series = {}
        for series in all_series:
            key = series['name'].lower().strip()
            if key not in unique_series:
                unique_series[key] = series
        
        result = list(unique_series.values())[:limit]
        logger.info(f"Trouvé {len(result)} séries populaires uniques")
        return result
    
    async def parse_search_result_for_series(self, work: Dict) -> Optional[Dict]:
        """Parse résultat recherche pour identifier série"""
        try:
            title = work.get('title', '').strip()
            authors = work.get('author_name', [])
            if not title or not authors:
                return None
            
            # Détection série similaire à parse_work_for_series
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
                    'trilogy', 'quartet', 'collection'
                ]
                
                if any(indicator in title.lower() for indicator in series_indicators):
                    series_name = title
                else:
                    return None
            
            # Métadonnées
            subjects = work.get('subject', [])
            first_published = work.get('first_publish_year')
            
            # Construction objet série
            series_data = {
                'name': series_name,
                'authors': authors[:3],  # Limite à 3 auteurs
                'category': self.detect_category(title, subjects),
                'volumes': 1,
                'keywords': self.extract_keywords(title, subjects),
                'variations': self.generate_variations(series_name),
                'first_published': first_published,
                'status': 'ongoing',
                'source': 'open_library_search',
                'ol_key': work.get('key'),
                'description': '',
                'subjects': subjects[:10],
                'languages': work.get('language', []),
                'translations': {
                    'en': series_name,
                    'fr': series_name
                }
            }
            
            return series_data
        
        except Exception as e:
            logger.error(f"Erreur parsing résultat recherche: {str(e)}")
            return None
    
    def load_existing_series(self) -> Set[str]:
        """Chargement séries existantes pour éviter doublons"""
        try:
            # Chemin vers le fichier des séries existantes
            series_file = Path('/app/backend/data/extended_series_database.json')
            if not series_file.exists():
                logger.warning("Fichier séries existantes non trouvé")
                return set()
            
            with open(series_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            
            existing_names = set()
            for series in existing_data:
                existing_names.add(series['name'].lower().strip())
                # Ajouter aussi les variations
                for variation in series.get('variations', []):
                    existing_names.add(variation.lower().strip())
            
            logger.info(f"Chargé {len(existing_names)} noms/variations de séries existantes")
            return existing_names
        
        except Exception as e:
            logger.error(f"Erreur chargement séries existantes: {str(e)}")
            return set()
    
    def is_duplicate(self, series_name: str, existing_names: Set[str]) -> bool:
        """Vérification si série est un doublon"""
        name_lower = series_name.lower().strip()
        
        # Vérification exacte
        if name_lower in existing_names:
            return True
        
        # Vérification similarité (mots-clés communs)
        name_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', name_lower))
        
        for existing_name in existing_names:
            existing_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', existing_name))
            
            # Si plus de 80% des mots sont communs, considérer comme doublon
            if len(name_words) > 0 and len(existing_words) > 0:
                common_words = name_words.intersection(existing_words)
                similarity = len(common_words) / max(len(name_words), len(existing_words))
                
                if similarity > 0.8:
                    return True
        
        return False
    
    def aggregate_series(self, series_list: List[Dict]) -> List[Dict]:
        """Agrégation séries similaires et comptage volumes"""
        aggregated = {}
        
        for series in series_list:
            name = series['name'].lower().strip()
            
            if name in aggregated:
                # Agrégation
                existing = aggregated[name]
                existing['volumes'] += 1
                
                # Merge auteurs
                for author in series['authors']:
                    if author not in existing['authors']:
                        existing['authors'].append(author)
                
                # Merge keywords
                for keyword in series['keywords']:
                    if keyword not in existing['keywords']:
                        existing['keywords'].append(keyword)
                
                # Merge variations
                for variation in series['variations']:
                    if variation not in existing['variations']:
                        existing['variations'].append(variation)
                
                # Merge subjects
                for subject in series['subjects']:
                    if subject not in existing['subjects']:
                        existing['subjects'].append(subject)
                
                # Mise à jour date première publication
                if series['first_published'] and (
                    not existing['first_published'] or 
                    series['first_published'] < existing['first_published']
                ):
                    existing['first_published'] = series['first_published']
            
            else:
                aggregated[name] = series.copy()
        
        return list(aggregated.values())
    
    def save_series_to_database(self, series_list: List[Dict]) -> int:
        """Sauvegarde séries dans la base de données"""
        try:
            # Chargement base existante
            series_file = Path('/app/backend/data/extended_series_database.json')
            existing_series = []
            
            if series_file.exists():
                with open(series_file, 'r', encoding='utf-8') as f:
                    existing_series = json.load(f)
            
            # Ajout nouvelles séries
            existing_series.extend(series_list)
            
            # Création dossier si nécessaire
            series_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Sauvegarde
            with open(series_file, 'w', encoding='utf-8') as f:
                json.dump(existing_series, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Sauvegardé {len(series_list)} nouvelles séries")
            return len(series_list)
        
        except Exception as e:
            logger.error(f"Erreur sauvegarde séries: {str(e)}")
            return 0
    
    def generate_report(self, series_list: List[Dict]) -> str:
        """Génération rapport d'exécution"""
        report = f"""
🚀 RAPPORT AUTOMATISATION OPEN LIBRARY SÉRIES
==============================================

📊 STATISTIQUES GÉNÉRALES
- Total recherches effectuées: {self.stats['total_searched']}
- Séries trouvées: {self.stats['series_found']}
- Séries ajoutées: {self.stats['series_added']}
- Doublons ignorés: {self.stats['duplicates_skipped']}
- Erreurs rencontrées: {self.stats['errors']}

📚 RÉPARTITION PAR CATÉGORIE
"""
        
        # Comptage par catégorie
        categories = {}
        for series in series_list:
            cat = series['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        for cat, count in sorted(categories.items()):
            report += f"- {cat.title()}: {count} séries\n"
        
        report += f"""
🔍 SÉRIES AJOUTÉES (Top 10)
"""
        
        # Top 10 séries par nombre de volumes
        top_series = sorted(series_list, key=lambda x: x['volumes'], reverse=True)[:10]
        
        for i, series in enumerate(top_series, 1):
            authors = ', '.join(series['authors'][:2])
            report += f"{i}. {series['name']} - {authors} ({series['volumes']} volumes, {series['category']})\n"
        
        report += f"""
⚡ PERFORMANCE
- Durée d'exécution: {datetime.now().strftime('%H:%M:%S')}
- Séries par minute: {self.stats['series_found'] / max(1, self.stats['total_searched'] / 60):.1f}
- Taux de succès: {(self.stats['series_found'] / max(1, self.stats['total_searched'])) * 100:.1f}%

🎯 PROCHAINES ÉTAPES
- Vérification manuelle des séries ajoutées
- Mise à jour système de détection
- Test du masquage intelligent
- Optimisation des mots-clés de détection
"""
        
        return report
    
    async def run_automation(self, 
                           mode: str = 'popular',
                           limit: int = 50,
                           authors: Optional[List[str]] = None,
                           categories: Optional[List[str]] = None) -> Dict:
        """Exécution automatisation complète"""
        
        logger.info(f"🚀 Démarrage automatisation Open Library - Mode: {mode}, Limit: {limit}")
        start_time = datetime.now()
        
        # Chargement séries existantes
        existing_names = self.load_existing_series()
        
        # Récupération séries selon mode
        all_series = []
        
        if mode == 'authors':
            authors_list = authors or self.popular_authors
            for author in authors_list[:20]:  # Limite à 20 auteurs
                series_data = await self.search_author_series(author, limit // len(authors_list) + 2)
                all_series.extend(series_data)
                self.stats['total_searched'] += 1
                await asyncio.sleep(0.3)  # Rate limiting
        
        elif mode == 'popular':
            all_series = await self.search_popular_series(limit)
            self.stats['total_searched'] = limit
        
        elif mode == 'categories':
            categories_list = categories or ['fantasy', 'mystery', 'scifi']
            for category in categories_list:
                # Recherche par catégorie (implementation simplifiée)
                series_data = await self.search_popular_series(limit // len(categories_list))
                all_series.extend(series_data)
                self.stats['total_searched'] += limit // len(categories_list)
                await asyncio.sleep(0.5)
        
        # Agrégation et déduplication
        logger.info(f"📊 Traitement de {len(all_series)} séries brutes")
        aggregated_series = self.aggregate_series(all_series)
        
        # Filtrage doublons
        new_series = []
        for series in aggregated_series:
            if not self.is_duplicate(series['name'], existing_names):
                new_series.append(series)
                self.stats['series_added'] += 1
            else:
                self.stats['duplicates_skipped'] += 1
        
        self.stats['series_found'] = len(new_series)
        
        # Sauvegarde
        if new_series:
            saved_count = self.save_series_to_database(new_series)
            logger.info(f"💾 Sauvegardé {saved_count} nouvelles séries")
        
        # Génération rapport
        report = self.generate_report(new_series)
        
        # Sauvegarde rapport
        report_file = Path(f'/app/logs/open_library_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        duration = datetime.now() - start_time
        logger.info(f"✅ Automatisation terminée en {duration}")
        
        return {
            'success': True,
            'series_added': len(new_series),
            'duplicates_skipped': self.stats['duplicates_skipped'],
            'duration': str(duration),
            'report_file': str(report_file),
            'new_series': new_series
        }


async def main():
    """Fonction principale avec arguments CLI"""
    parser = argparse.ArgumentParser(description='Automatisation Open Library Séries')
    parser.add_argument('--mode', 
                       choices=['popular', 'authors', 'categories'],
                       default='popular',
                       help='Mode de récupération')
    parser.add_argument('--limit', 
                       type=int, 
                       default=50,
                       help='Nombre maximum de séries à récupérer')
    parser.add_argument('--authors',
                       nargs='+',
                       help='Liste d\'auteurs spécifiques')
    parser.add_argument('--categories',
                       nargs='+',
                       help='Liste de catégories spécifiques')
    parser.add_argument('--dry-run',
                       action='store_true',
                       help='Simulation sans sauvegarde')
    
    args = parser.parse_args()
    
    # Création dossiers logs
    Path('/app/logs').mkdir(exist_ok=True)
    Path('/app/backend/data').mkdir(parents=True, exist_ok=True)
    
    # Exécution automatisation
    async with OpenLibrarySeriesAutomator() as automator:
        result = await automator.run_automation(
            mode=args.mode,
            limit=args.limit,
            authors=args.authors,
            categories=args.categories
        )
        
        print(f"\n🎯 RÉSULTATS AUTOMATISATION")
        print(f"✅ Séries ajoutées: {result['series_added']}")
        print(f"⏭️  Doublons ignorés: {result['duplicates_skipped']}")
        print(f"⏱️  Durée: {result['duration']}")
        print(f"📄 Rapport: {result['report_file']}")
        
        if result['series_added'] > 0:
            print(f"\n🚀 {result['series_added']} nouvelles séries ajoutées à la base BOOKTIME !")
            print(f"🔄 Redémarrage recommandé pour mise à jour du système de détection")


if __name__ == "__main__":
    asyncio.run(main())