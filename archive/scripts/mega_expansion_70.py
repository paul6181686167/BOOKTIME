#!/usr/bin/env python3
"""
🚀 ULTRA HARVEST MEGA EXPANSION - CONFIANCE 70%
Script ultra-spécialisé pour découvrir des séries dans des niches spécifiques
"""

import asyncio
import aiohttp
import json
import random
import time
from datetime import datetime
from pathlib import Path
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('MegaExpansion')

class MegaExpansionHarvest:
    """Harvest ultra-spécialisé pour niches non explorées"""
    
    def __init__(self):
        self.new_series_found = []
        self.books_analyzed = 0
        self.start_time = datetime.now()
        
        # Charger séries existantes
        self.existing_series = set()
        self._load_existing_series()
    
    def _load_existing_series(self):
        """Charger séries existantes"""
        series_path = Path('/app/backend/data/extended_series_database.json')
        if series_path.exists():
            with open(series_path, 'r') as f:
                series_data = json.load(f)
                for series in series_data:
                    name = series.get('name', '').lower()
                    if name:
                        self.existing_series.add(name)
        logger.info(f"✅ {len(self.existing_series)} séries existantes chargées")
    
    def _generate_ultra_specialized_queries(self) -> list:
        """Génération de requêtes ultra-spécialisées pour niches"""
        
        specialized_queries = [
            # Light novels japonais
            'subject:"light novel" AND (volume OR vol)',
            'title:"light novel" AND series',
            '"ライトノベル" AND volume',
            
            # Web novels et adaptations
            'subject:"web novel" AND adaptation',
            'subject:"webnovel" AND (series OR volume)',
            '"web novel" AND published',
            
            # Manhwa coréens
            'language:kor AND (volume OR series)',
            'subject:"manhwa" AND (vol OR tome)',
            'subject:"korean comic" AND series',
            
            # Manhua chinois
            'language:chi AND (volume OR series)',
            'subject:"manhua" AND (vol OR tome)',
            'subject:"chinese comic" AND series',
            
            # Romans graphiques indépendants
            'subject:"indie comic" AND (volume OR series)',
            'subject:"independent comic" AND series',
            'publisher:"Image Comics" AND (limited OR ongoing)',
            
            # Fantasy urbaine moderne
            'subject:"urban fantasy" AND (series OR saga)',
            'subject:"paranormal romance" AND (book OR volume)',
            'subject:"supernatural" AND (series OR collection)',
            
            # LitRPG et GameLit
            'subject:"litrpg" AND (book OR volume)',
            'subject:"gamelit" AND series',
            '"virtual reality" AND novel AND series',
            
            # Cultivation novels
            'subject:"cultivation novel" AND (book OR volume)',
            'subject:"xianxia" AND novel',
            'subject:"wuxia" AND series',
            
            # Science-fiction moderne
            'subject:"cyberpunk" AND (series OR trilogy)',
            'subject:"space opera" AND (book OR volume)',
            'subject:"hard science fiction" AND series',
            
            # Young Adult spécialisé
            'subject:"ya fantasy" AND (series OR saga)',
            'subject:"teen fiction" AND (book OR series)',
            'subject:"coming of age" AND series',
            
            # Genres émergents
            'subject:"climate fiction" AND series',
            'subject:"solarpunk" AND novel',
            'subject:"biopunk" AND series',
            
            # Auto-édition prolifique
            'publisher:"CreateSpace" AND (series OR saga)',
            'publisher:"Kindle Direct Publishing" AND series',
            'subject:"self published" AND (book OR volume)',
            
            # Comics alternatifs
            'publisher:"Vertigo" AND (series OR collection)',
            'publisher:"Dark Horse" AND (ongoing OR limited)',
            'subject:"alternative comics" AND series',
            
            # Adaptations multi-médias
            'subject:"anime adaptation" AND novel',
            'subject:"manga adaptation" AND series',
            'subject:"video game" AND novel AND series',
            
            # Littérature genre spécialisée
            'subject:"sword and sorcery" AND (series OR saga)',
            'subject:"steampunk" AND (novel OR series)',
            'subject:"alternate history" AND series',
            
            # Non-fiction sérialisée
            'subject:"true crime" AND (series OR collection)',
            'subject:"biography" AND (series OR volume)',
            'subject:"memoir" AND (series OR part)',
            
            # Éditeurs spécialisés manga
            'publisher:"Viz Media" AND (vol OR volume)',
            'publisher:"Kodansha" AND series',
            'publisher:"Shogakukan" AND volume',
            
            # Collectibles et éditions spéciales
            '"limited edition" AND (series OR collection)',
            '"collector edition" AND (volume OR set)',
            '"omnibus edition" AND series',
            
            # Séries audio
            'subject:"audiobook" AND (series OR collection)',
            'subject:"podcast" AND series',
            'subject:"radio drama" AND series',
            
            # Formats émergents
            'subject:"webtoon" AND series',
            'subject:"webcomic" AND (ongoing OR collection)',
            'subject:"digital comic" AND series',
            
            # Thématiques spécialisées
            'subject:"medical thriller" AND series',
            'subject:"legal thriller" AND (book OR series)',
            'subject:"military science fiction" AND series',
            
            # Langues moins communes
            'language:rus AND (том OR серия)',  # Russe
            'language:jpn AND (巻 OR シリーズ)',   # Japonais
            'language:fra AND (tome OR série)',   # Français
            'language:deu AND (band OR serie)',   # Allemand
            
            # Auteurs prolifiques spécialisés
            'author:"Brandon Sanderson" AND (book OR volume)',
            'author:"Rick Riordan" AND series',
            'author:"James S.A. Corey" AND book',
            'author:"Cassandra Clare" AND series',
            
            # Franchises transmédias
            '"Warhammer 40000" AND novel',
            '"Dungeons and Dragons" AND novel',
            '"Magic: The Gathering" AND book',
            '"World of Warcraft" AND novel',
            
            # Sub-genres fantasy
            'subject:"high fantasy" AND (epic OR saga)',
            'subject:"dark fantasy" AND series',
            'subject:"epic fantasy" AND (book OR volume)',
            
            # Romance spécialisée
            'subject:"historical romance" AND series',
            'subject:"contemporary romance" AND (book OR series)',
            'subject:"paranormal romance" AND saga',
            
            # Littérature jeunesse avancée
            'subject:"middle grade" AND (series OR adventure)',
            'subject:"chapter book" AND series',
            'subject:"early reader" AND collection'
        ]
        
        # Mélanger pour diversité
        random.shuffle(specialized_queries)
        return specialized_queries
    
    async def search_openlibrary_advanced(self, query: str, limit: int = 200) -> list:
        """Recherche avancée Open Library avec timeout étendu"""
        
        url = "https://openlibrary.org/search.json"
        params = {
            'q': query,
            'limit': limit,
            'fields': 'key,title,author_name,first_publish_year,subject,publisher,language,isbn'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=45) as response:
                    if response.status == 200:
                        data = await response.json()
                        books = data.get('docs', [])
                        logger.info(f"🔍 Requête '{query[:40]}...' → {len(books)} livres")
                        return books
        except Exception as e:
            logger.warning(f"⚠️ Erreur recherche '{query[:30]}...': {e}")
        
        return []
    
    def detect_ultra_series_patterns(self, books: list, query_type: str) -> list:
        """Détection ultra-sophistiquée avec confiance 70%"""
        
        series_candidates = {}
        
        for book in books:
            title = book.get('title', '')
            authors = book.get('author_name', [])
            author = authors[0] if authors else 'Unknown'
            subjects = book.get('subject', [])
            
            # Patterns ultra-sophistiqués
            advanced_patterns = [
                # Patterns classiques améliorés
                r'(.+?)\s+(?:volume|vol\.?|tome|book|part|#|chapter|episode)\s*(\d+)',
                r'(.+?)\s+(\d+)(?:st|nd|rd|th)?\s*(?:edition|volume|book|part)?',
                r'(.+?)\s*:\s*(?:book|volume|part|chapter)\s*(\d+)',
                r'(.+?)\s*\((?:book|vol\.?|volume|part)\s*(\d+)\)',
                
                # Patterns spécialisés light novels
                r'(.+?)\s+(?:light novel|ln)\s*(\d+)',
                r'(.+?)\s*ライトノベル\s*(\d+)',
                
                # Patterns manga/manhwa/manhua
                r'(.+?)\s*,?\s*(?:vol\.?|volume|tome)\s*(\d+)',
                r'(.+?)\s*#(\d+)',
                r'(.+?)\s*(\d+)(?:\s*of\s*\d+)?',
                r'(.+?)\s*巻\s*(\d+)',  # Japonais
                r'(.+?)\s*권\s*(\d+)',   # Coréen
                
                # Patterns séries spécialisées
                r'(.+?)\s+(?:saga|series|collection)\s*(\d+)',
                r'(.+?)\s*-\s*(?:book|volume|part)\s*(\d+)',
                r'(.+?)\s+(?:season|arc)\s*(\d+)',
                
                # Patterns formats spéciaux
                r'(.+?)\s+(?:omnibus|deluxe|complete)\s*(\d+)',
                r'(.+?)\s*:\s*(?:season|series)\s*(\d+)',
                
                # Patterns romans web
                r'(.+?)\s+(?:novel|ln)\s*(\d+)',
                r'(.+?)\s+web\s*novel\s*(\d+)',
                
                # Patterns romans graphiques
                r'(.+?)\s+(?:graphic novel|gn)\s*(\d+)',
                r'(.+?)\s*graphic\s+novel\s*(\d+)'
            ]
            
            for pattern in advanced_patterns:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    series_name = match.group(1).strip()
                    try:
                        volume_num = int(match.group(2))
                    except (ValueError, IndexError):
                        continue
                    
                    # Nettoyage nom série
                    series_name = re.sub(r'\s*[,.:;-]\s*$', '', series_name)
                    series_name = series_name.strip()
                    
                    # Critères de qualité stricts
                    if (len(series_name) < 2 or 
                        volume_num > 200 or 
                        volume_num < 1 or
                        series_name.lower() in self.existing_series):
                        continue
                    
                    # Créer candidat
                    key = (series_name, author)
                    if key not in series_candidates:
                        series_candidates[key] = {
                            'books': [],
                            'confidence_scores': [],
                            'volumes': set(),
                            'subjects': set(),
                            'query_type': query_type
                        }
                    
                    # Calculer score de confiance sophistiqué
                    confidence = 75  # Base élevée
                    
                    # Bonus contexte de requête
                    if 'light novel' in query_type.lower():
                        confidence += 10
                    if 'manga' in query_type.lower() or 'comic' in query_type.lower():
                        confidence += 8
                    if 'series' in title.lower():
                        confidence += 5
                    
                    # Bonus patterns avancés
                    if 'vol' in title.lower() or 'volume' in title.lower():
                        confidence += 7
                    if volume_num > 1:
                        confidence += 5
                    
                    # Bonus sujets pertinents
                    relevant_subjects = ['fiction', 'fantasy', 'comics', 'manga', 'novel']
                    if any(subj in ' '.join(subjects).lower() for subj in relevant_subjects):
                        confidence += 8
                    
                    series_candidates[key]['books'].append(book)
                    series_candidates[key]['confidence_scores'].append(confidence)
                    series_candidates[key]['volumes'].add(volume_num)
                    series_candidates[key]['subjects'].update(subjects[:5])  # Limiter
                    break
        
        # Validation avec seuil 70%
        valid_series = []
        for (series_name, author), data in series_candidates.items():
            max_confidence = max(data['confidence_scores']) if data['confidence_scores'] else 0
            unique_volumes = len(data['volumes'])
            
            # SEUIL 70% + au moins 2 volumes OU confiance très élevée
            if (max_confidence >= 70 and unique_volumes >= 2) or max_confidence >= 90:
                category = self._detect_advanced_category(data['books'], data['subjects'], data['query_type'])
                
                series_entry = {
                    'name': series_name,
                    'authors': [author],
                    'category': category,
                    'volumes': unique_volumes,
                    'confidence_score': max_confidence,
                    'source': f'mega_expansion_70_{data["query_type"][:20]}',
                    'detection_date': datetime.now().isoformat(),
                    'books_found': len(data['books']),
                    'subjects': list(data['subjects'])[:5],
                    'query_context': data['query_type']
                }
                valid_series.append(series_entry)
                self.new_series_found.append(series_entry)
                
                logger.info(f"🎯 Série: {series_name} ({category}) - {max_confidence}% - {unique_volumes} vols")
        
        return valid_series
    
    def _detect_advanced_category(self, books: list, subjects: set, query_type: str) -> str:
        """Détection catégorie avancée"""
        
        subjects_str = ' '.join(subjects).lower() + ' ' + query_type.lower()
        
        # Analyse des titres aussi
        titles_str = ' '.join([book.get('title', '') for book in books]).lower()
        combined = subjects_str + ' ' + titles_str
        
        # Manga/Anime
        manga_terms = ['manga', 'anime', 'japanese', 'shonen', 'seinen', 'shoujo', 'light novel', 'ln', 'manhwa', 'manhua']
        if any(term in combined for term in manga_terms):
            return 'manga'
        
        # BD/Comics
        comic_terms = ['comic', 'graphic', 'superhero', 'marvel', 'dc', 'vertigo', 'image', 'dark horse']
        if any(term in combined for term in comic_terms):
            return 'bd'
        
        # Par défaut roman
        return 'roman'
    
    async def run_mega_expansion(self, max_queries: int = 80):
        """Exécution mega expansion"""
        
        logger.info(f"""
🚀 MEGA EXPANSION HARVEST - CONFIANCE 70%
=========================================
🎯 Requêtes spécialisées: {max_queries}
📊 Seuil confiance: 70%
🔍 Focus: Niches ultra-spécialisées
🗄️ Base actuelle: {len(self.existing_series)} séries
=========================================
""")
        
        queries = self._generate_ultra_specialized_queries()
        successful_queries = 0
        
        for i, query in enumerate(queries[:max_queries]):
            logger.info(f"🔍 [{i+1}/{max_queries}] {query}")
            
            # Recherche
            books = await self.search_openlibrary_advanced(query, limit=200)
            self.books_analyzed += len(books)
            
            # Détection
            if books:
                series_found = self.detect_ultra_series_patterns(books, query)
                if series_found:
                    successful_queries += 1
                    logger.info(f"✅ {len(series_found)} séries trouvées!")
            
            # Délai respectueux
            await asyncio.sleep(0.3)
            
            # Checkpoint tous les 20
            if (i + 1) % 20 == 0:
                elapsed = (datetime.now() - self.start_time).total_seconds()
                logger.info(f"📊 Checkpoint: {len(self.new_series_found)} séries trouvées en {elapsed:.1f}s")
        
        return await self._save_mega_results()
    
    async def _save_mega_results(self):
        """Sauvegarde résultats mega expansion"""
        
        if not self.new_series_found:
            logger.info("ℹ️ Aucune nouvelle série détectée")
            return {'success': True, 'new_series': 0}
        
        # Sauvegarde
        series_path = Path('/app/backend/data/extended_series_database.json')
        
        # Backup
        backup_path = Path(f'/app/backups/series_detection/backup_mega_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Charger et fusionner
        if series_path.exists():
            with open(series_path, 'r') as f:
                existing_data = json.load(f)
        else:
            existing_data = []
        
        # Backup sécurisé
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
            'execution_time': f"{elapsed:.1f}s",
            'expansion_rate': len(self.new_series_found) / (elapsed/60) if elapsed > 0 else 0
        }
        
        logger.info(f"""
✅ MEGA EXPANSION TERMINÉE
=========================
🎯 Nouvelles séries: {result['new_series']}
📚 Total maintenant: {result['total_series_now']}
📖 Livres analysés: {result['books_analyzed']}
⏱️ Durée: {result['execution_time']}
📈 Taux: {result['expansion_rate']:.1f} séries/min
=========================
""")
        
        return result

async def main():
    """Point d'entrée mega expansion"""
    
    harvester = MegaExpansionHarvest()
    result = await harvester.run_mega_expansion(max_queries=100)
    
    if result['success'] and result['new_series'] > 0:
        print(f"\n🎉 MEGA EXPANSION RÉUSSIE! {result['new_series']} nouvelles séries!")
        print(f"📊 Total séries: {result['total_series_now']}")
        print(f"⚡ Taux d'expansion: {result['expansion_rate']:.1f} séries/min")
    else:
        print(f"\n💡 Mega expansion terminée. Total: {result.get('total_series_now', 'N/A')} séries")

if __name__ == "__main__":
    asyncio.run(main())