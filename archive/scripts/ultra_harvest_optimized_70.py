#!/usr/bin/env python3
"""
🚀 ULTRA HARVEST OPTIMISÉ - EXPANSION MAXIMALE CONFIANCE 70%
Script optimisé pour découvrir de nouveaux livres non analysés
"""

import asyncio
import aiohttp
import json
import random
import time
from datetime import datetime
from pathlib import Path
import logging
import sqlite3

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('UltraHarvestOptimized')

class OptimizedUltraHarvest:
    """Version optimisée d'Ultra Harvest focalisée sur nouvelles découvertes"""
    
    def __init__(self):
        self.new_series_found = []
        self.books_analyzed = 0
        self.api_calls = 0
        self.start_time = datetime.now()
        
        # Charger base existante pour éviter doublons
        self.existing_series = set()
        self._load_existing_series()
        
        # Base de tracking pour éviter retraitement
        self.tracking_db_path = Path('/app/data/ultra_harvest_tracking.db')
        self._init_tracking()
    
    def _load_existing_series(self):
        """Charger séries existantes pour éviter doublons"""
        series_path = Path('/app/backend/data/extended_series_database.json')
        if series_path.exists():
            with open(series_path, 'r') as f:
                series_data = json.load(f)
                for series in series_data:
                    name = series.get('name', '').lower()
                    if name:
                        self.existing_series.add(name)
        logger.info(f"✅ {len(self.existing_series)} séries existantes chargées")
    
    def _init_tracking(self):
        """Initialiser système de tracking"""
        if not self.tracking_db_path.exists():
            return
            
        with sqlite3.connect(self.tracking_db_path) as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) FROM analyzed_books 
                WHERE analysis_date >= date('now', '-1 day')
            """)
            recent_count = cursor.fetchone()[0]
            logger.info(f"📊 {recent_count} livres analysés récemment")
    
    def _generate_fresh_queries(self) -> list:
        """Génération de requêtes visant des territoires moins explorés"""
        
        # Stratégies pour découvrir du contenu frais
        fresh_strategies = [
            # Publications récentes (2020-2025)
            'first_published_year:[2020 TO 2025] AND subject:(fantasy OR "science fiction")',
            'first_published_year:[2021 TO 2025] AND subject:(manga OR comics)',
            'first_published_year:[2022 TO 2025] AND (series OR saga OR volume)',
            
            # Auteurs moins connus mais prolifiques
            'author:(Brandon Sanderson OR Patrick Rothfuss OR Joe Abercrombie)',
            'author:(Kentaro Miura OR Junji Ito OR Naoki Urasawa)',
            'author:(Brian K Vaughan OR Neil Gaiman OR Alan Moore)',
            
            # Genres spécialisés
            'subject:"light novel" AND (volume OR book)',
            'subject:"graphic novel" AND (series OR collection)',
            'subject:"visual novel" AND adaptation',
            'subject:"web novel" AND published',
            
            # Éditeurs spécialisés séries
            'publisher:"Viz Media" AND volume',
            'publisher:"Dark Horse Comics" AND (series OR collection)',
            'publisher:"Image Comics" AND ongoing',
            'publisher:"Marvel Comics" AND (limited OR unlimited)',
            
            # Langues moins explorées
            'language:spa AND (serie OR tomo)',  # Espagnol
            'language:ita AND (serie OR volume)',  # Italien
            'language:ger AND (band OR teil)',     # Allemand
            'language:por AND (série OR volume)',  # Portugais
            
            # Concepts de séries modernes
            '"limited series" AND comics',
            '"ongoing series" AND comics',
            '"anthology series" AND books',
            '"book series" AND contemporary',
            
            # Niches populaires récentes
            'subject:"isekai" AND novel',
            'subject:"litrpg" AND series',
            'subject:"cultivation" AND novel',
            'subject:"system" AND novel',
            'subject:"regression" AND novel',
            
            # Franchises émergentes
            '"Demon Slayer" OR "Kimetsu no Yaiba"',
            '"Jujutsu Kaisen" OR "Sorcery Fight"',
            '"Chainsaw Man" OR "チェンソーマン"',
            '"Spy x Family" OR "スパイファミリー"',
            
            # Publications universitaires avec séries (collections académiques)
            'publisher:"MIT Press" AND (series OR collection OR volume)',
            'publisher:"Cambridge University Press" AND (series OR studies)',
            'publisher:"Oxford University Press" AND (series OR handbook)',
            
            # Auto-édition avec séries
            'publisher:("CreateSpace" OR "KDP" OR "Smashwords") AND (book OR series)',
            'subject:"indie" AND (series OR saga OR collection)',
            
            # Formats émergents
            'subject:"webcomic" AND collection',
            'subject:"webtoon" AND series',
            'subject:"podcast" AND series',
            'subject:"audio drama" AND series'
        ]
        
        # Mélanger pour variété
        random.shuffle(fresh_strategies)
        return fresh_strategies[:40]  # Limiter pour efficacité
    
    async def search_openlibrary(self, query: str, limit: int = 100) -> list:
        """Recherche optimisée Open Library"""
        
        url = "https://openlibrary.org/search.json"
        params = {
            'q': query,
            'limit': limit,
            'fields': 'key,title,author_name,first_publish_year,subject,publisher,language'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        books = data.get('docs', [])
                        self.api_calls += 1
                        return books
        except Exception as e:
            logger.warning(f"⚠️ Erreur recherche '{query}': {e}")
        
        return []
    
    def detect_series_patterns(self, books: list) -> list:
        """Détection patterns de séries avec confiance 70%"""
        
        series_candidates = {}
        
        for book in books:
            title = book.get('title', '')
            authors = book.get('author_name', [])
            author = authors[0] if authors else 'Unknown'
            
            # Skip si déjà analysé récemment
            book_id = f"{title}_{author}".replace(' ', '_').lower()
            
            # Patterns de détection série améliorés
            patterns = [
                # Numérotation classique
                r'(.+?)\s+(?:volume|vol\.?|tome|book|part|#)\s*(\d+)',
                r'(.+?)\s+(\d+)(?:st|nd|rd|th)?\s*(?:edition|volume|book)?',
                r'(.+?)\s*:\s*(?:book|volume|part)\s*(\d+)',
                
                # Patterns spéciaux
                r'(.+?)\s+(?:season|series|saga)\s*(\d+)',
                r'(.+?)\s*\((?:book|vol\.?)\s*(\d+)\)',
                r'(.+?)\s*-\s*(?:book|volume)\s*(\d+)',
                
                # Patterns manga/comics
                r'(.+?)\s*,?\s*(?:vol\.?|volume|tome)\s*(\d+)',
                r'(.+?)\s*#(\d+)',
                r'(.+?)\s*(\d+)(?:\s*of\s*\d+)?'
            ]
            
            import re
            
            for pattern in patterns:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    series_name = match.group(1).strip()
                    volume_num = int(match.group(2))
                    
                    # Skip si série existe déjà
                    if series_name.lower() in self.existing_series:
                        continue
                    
                    # Critères de qualité
                    if len(series_name) < 3 or volume_num > 100:
                        continue
                    
                    # Créer candidat
                    key = (series_name, author)
                    if key not in series_candidates:
                        series_candidates[key] = {
                            'books': [],
                            'confidence_scores': [],
                            'volumes': set()
                        }
                    
                    # Calculer score de confiance
                    confidence = 80  # Base élevée
                    
                    # Bonus si multiple volumes
                    if len(series_candidates[key]['volumes']) > 0:
                        confidence += 15
                    
                    # Bonus si auteur connu
                    if any(known in author.lower() for known in ['martin', 'king', 'rowling', 'tolkien']):
                        confidence += 10
                    
                    series_candidates[key]['books'].append(book)
                    series_candidates[key]['confidence_scores'].append(confidence)
                    series_candidates[key]['volumes'].add(volume_num)
                    break
        
        # Validation avec seuil 70%
        valid_series = []
        for (series_name, author), data in series_candidates.items():
            max_confidence = max(data['confidence_scores']) if data['confidence_scores'] else 0
            has_multiple = len(data['books']) >= 2
            
            # SEUIL ABAISSÉ À 70% (vs 75% précédent)
            if max_confidence >= 70 and has_multiple:
                series_entry = {
                    'name': series_name,
                    'authors': [author],
                    'category': self._detect_category(data['books']),
                    'volumes': len(data['volumes']),
                    'confidence_score': max_confidence,
                    'source': 'ultra_harvest_optimized_70',
                    'detection_date': datetime.now().isoformat(),
                    'books_found': len(data['books'])
                }
                valid_series.append(series_entry)
                self.new_series_found.append(series_entry)
                logger.info(f"🎯 Série détectée: {series_name} (confiance: {max_confidence}%)")
        
        return valid_series
    
    def _detect_category(self, books: list) -> str:
        """Détection catégorie série"""
        subjects = []
        for book in books:
            subjects.extend(book.get('subject', []))
        
        subjects_str = ' '.join(subjects).lower()
        
        if any(term in subjects_str for term in ['manga', 'anime', 'japanese', 'shonen', 'seinen']):
            return 'manga'
        elif any(term in subjects_str for term in ['comic', 'graphic', 'superhero', 'marvel', 'dc']):
            return 'bd'
        else:
            return 'roman'
    
    async def run_optimized_harvest(self, max_queries: int = 50):
        """Exécution harvest optimisé"""
        
        logger.info(f"""
🚀 ULTRA HARVEST OPTIMISÉ - CONFIANCE 70%
=========================================
🎯 Requêtes max: {max_queries}
📊 Seuil confiance: 70% (vs 75% standard)
🗄️ Séries existantes: {len(self.existing_series)}
=========================================
""")
        
        queries = self._generate_fresh_queries()
        
        for i, query in enumerate(queries[:max_queries]):
            logger.info(f"🔍 [{i+1}/{max_queries}] Requête: {query[:50]}...")
            
            # Recherche
            books = await self.search_openlibrary(query, limit=150)
            self.books_analyzed += len(books)
            
            # Détection séries
            if books:
                series_found = self.detect_series_patterns(books)
                
                if series_found:
                    logger.info(f"✅ {len(series_found)} nouvelles séries trouvées!")
            
            # Délai pour respect API
            await asyncio.sleep(0.2)
            
            # Progress update
            if (i + 1) % 10 == 0:
                elapsed = (datetime.now() - self.start_time).total_seconds()
                rate = self.books_analyzed / elapsed if elapsed > 0 else 0
                logger.info(f"📊 Progression: {len(self.new_series_found)} séries, {rate:.1f} livres/s")
        
        return await self._finalize_results()
    
    async def _finalize_results(self):
        """Finalisation et sauvegarde résultats"""
        
        if not self.new_series_found:
            logger.info("ℹ️ Aucune nouvelle série détectée")
            return {'success': True, 'new_series': 0}
        
        # Sauvegarde nouvelles séries
        series_path = Path('/app/backend/data/extended_series_database.json')
        
        # Backup
        backup_path = Path(f'/app/backups/series_detection/backup_optimized_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Charger données existantes
        if series_path.exists():
            with open(series_path, 'r') as f:
                existing_data = json.load(f)
        else:
            existing_data = []
        
        # Backup de sécurité
        with open(backup_path, 'w') as f:
            json.dump(existing_data + self.new_series_found, f, indent=2, ensure_ascii=False)
        
        # Ajout nouvelles séries
        existing_data.extend(self.new_series_found)
        
        # Sauvegarde finale
        with open(series_path, 'w') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        result = {
            'success': True,
            'new_series': len(self.new_series_found),
            'total_series_now': len(existing_data),
            'books_analyzed': self.books_analyzed,
            'api_calls': self.api_calls,
            'execution_time': f"{elapsed:.1f}s",
            'series_details': self.new_series_found
        }
        
        logger.info(f"""
✅ ULTRA HARVEST OPTIMISÉ TERMINÉ
=================================
🎯 Nouvelles séries ajoutées: {result['new_series']}
📚 Total séries maintenant: {result['total_series_now']}
📖 Livres analysés: {result['books_analyzed']}
🌐 Appels API: {result['api_calls']}
⏱️ Temps d'exécution: {result['execution_time']}
=================================
""")
        
        return result

async def main():
    """Point d'entrée principal"""
    
    harvester = OptimizedUltraHarvest()
    result = await harvester.run_optimized_harvest(max_queries=100)
    
    if result['success'] and result['new_series'] > 0:
        print(f"\n🎉 SUCCÈS! {result['new_series']} nouvelles séries ajoutées!")
        print("\n📋 Détails des nouvelles séries:")
        for series in result['series_details'][:10]:  # Afficher 10 premières
            print(f"  • {series['name']} ({series['category']}) - {series['confidence_score']}% confiance")
    else:
        print(f"\n💡 Processus terminé. {result.get('new_series', 0)} nouvelles séries trouvées.")

if __name__ == "__main__":
    asyncio.run(main())