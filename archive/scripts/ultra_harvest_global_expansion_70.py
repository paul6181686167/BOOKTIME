#!/usr/bin/env python3
"""
🌎 ULTRA HARVEST EXPANSION GLOBALE 70% - SESSION 81.26C
Approche globale avec requêtes étendues et patterns permissifs
Focus sur l'expansion maximale tous azimuts
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
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('UltraHarvestGlobal')

class GlobalExpansionHarvest:
    """Ultra Harvest expansion globale tous azimuts"""
    
    def __init__(self):
        self.new_series_found = []
        self.books_analyzed = 0
        self.api_calls = 0
        self.start_time = datetime.now()
        self.confidence_threshold = 70
        
        # Charger base existante
        self.existing_series = set()
        self._load_existing_series()
        
        # Patterns globaux étendus
        self._init_global_patterns()
    
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
    
    def _init_global_patterns(self):
        """Patterns globaux très permissifs"""
        self.global_patterns = [
            # Patterns numériques classiques
            r'(.+?)\s+(\d+)$',  # Plus permissif
            r'(.+?)\s+#(\d+)',
            r'(.+?)\s+vol\.?\s*(\d+)',
            r'(.+?)\s+volume\s+(\d+)',
            r'(.+?)\s+book\s+(\d+)',
            r'(.+?)\s+tome\s+(\d+)',
            r'(.+?)\s+part\s+(\d+)',
            r'(.+?)\s+episode\s+(\d+)',
            r'(.+?)\s+chapter\s+(\d+)',
            
            # Patterns avec mots-clés série
            r'(.+?)\s+series\s+(\d+)',
            r'(.+?)\s+saga\s+(\d+)',
            r'(.+?)\s+cycle\s+(\d+)',
            r'(.+?)\s+collection\s+(\d+)',
            
            # Patterns ordinaux
            r'(.+?)\s+first\b',
            r'(.+?)\s+second\b',
            r'(.+?)\s+third\b',
            r'(.+?)\s+fourth\b',
            r'(.+?)\s+fifth\b',
            
            # Patterns avec préfixes
            r'(.+?)\s+adventures?\s+(\d+)',
            r'(.+?)\s+chronicles?\s+(\d+)',
            r'(.+?)\s+tales?\s+(\d+)',
            r'(.+?)\s+stories?\s+(\d+)',
            r'(.+?)\s+legends?\s+(\d+)',
            
            # Patterns spéciaux
            r'(.+?)\s+trilogy\s+(\d+)',
            r'(.+?)\s+series\s+finale',
            r'(.+?)\s+prequel',
            r'(.+?)\s+sequel',
            r'(.+?)\s+spin.?off',
        ]
    
    def _generate_global_queries(self):
        """Générer requêtes globales diversifiées"""
        return [
            # Fiction genres populaires
            "fantasy series book", "science fiction saga", "mystery series novel",
            "romance series book", "thriller series novel", "horror series book",
            "adventure series novel", "historical fiction series", "contemporary fiction series",
            
            # Genres spécialisés
            "urban fantasy series", "paranormal romance series", "steampunk series book",
            "cyberpunk series novel", "dystopian series book", "post apocalyptic series",
            "space opera series", "military science fiction", "alternate history series",
            
            # Jeunesse et YA
            "young adult series", "teen fiction series", "middle grade series",
            "children series book", "chapter book series", "early reader series",
            "picture book series", "educational series children", "adventure series kids",
            
            # Non-fiction
            "biography series book", "history series book", "science series book",
            "philosophy series book", "psychology series book", "sociology series book",
            "economics series book", "politics series book", "religion series book",
            
            # Practical et self-help
            "self help series", "business series book", "finance series book",
            "health series book", "fitness series book", "diet series book",
            "cooking series book", "travel series book", "hobby series book",
            
            # Académique accessible
            "textbook series college", "study guide series", "reference series book",
            "handbook series professional", "manual series technical", "guide series practical",
            
            # Arts et culture
            "art series book", "music series book", "photography series book",
            "cinema series book", "theater series book", "dance series book",
            "literature series analysis", "cultural studies series", "media studies series",
            
            # International et culturel
            "japanese series book", "korean series book", "chinese series book",
            "european series book", "african series book", "latin american series",
            "indigenous series book", "multicultural series", "translation series book",
            
            # Formats et médias
            "graphic novel series", "comic book series", "manga series book",
            "light novel series", "web novel series", "audio book series",
            "ebook series", "digital series book", "interactive series book",
            
            # Sujets actuels
            "climate change series", "technology series book", "ai series book",
            "blockchain series book", "sustainability series", "environment series book",
            "social justice series", "equality series book", "diversity series book",
            
            # Wellness et spiritualité
            "mindfulness series book", "meditation series book", "yoga series book",
            "spirituality series book", "new age series", "alternative medicine series",
            
            # Professionnel et carrière
            "career development series", "leadership series book", "management series book",
            "entrepreneur series book", "startup series book", "innovation series book",
            
            # Loisirs et hobbies
            "crafts series book", "diy series book", "gardening series book",
            "sports series book", "games series book", "puzzle series book",
            
            # Sciences et technologie
            "computer science series", "engineering series book", "mathematics series book",
            "physics series book", "chemistry series book", "biology series book",
            
            # Éditeurs prolifiques
            "penguin classics series", "oxford series book", "cambridge series book",
            "harvard series book", "mit press series", "university press series",
            
            # Formats courts
            "short story series", "novella series book", "essay series book",
            "poetry series book", "anthology series book", "collection series book",
            
            # Niches émergentes
            "podcast series book", "youtube series book", "influencer series book",
            "blog series book", "online series book", "social media series",
            
            # Requêtes très larges pour ratisser large
            "book 1", "book 2", "book 3", "volume 1", "volume 2", "volume 3",
            "part one", "part two", "part three", "first book", "second book", "third book"
        ]
    
    def _detect_global_series(self, title, authors, subjects):
        """Détecter séries avec approche globale permissive"""
        if not title or len(title) < 3:
            return None
            
        title_lower = title.lower()
        
        # Essayer tous les patterns
        for pattern in self.global_patterns:
            match = re.search(pattern, title_lower)
            if match:
                if len(match.groups()) >= 2:
                    series_name = match.group(1).strip()
                    volume_num = match.group(2)
                else:
                    series_name = match.group(1).strip()
                    volume_num = "1"
                
                # Validation série
                if (len(series_name) >= 2 and 
                    series_name not in self.existing_series and
                    not self._is_excluded_global(series_name, title, subjects)):
                    
                    confidence = self._calculate_global_confidence(series_name, authors, subjects, title)
                    if confidence >= self.confidence_threshold:
                        return {
                            'name': series_name.title(),
                            'volume': volume_num,
                            'confidence': confidence,
                            'detection_method': 'global_expansion',
                            'original_title': title
                        }
        
        return None
    
    def _is_excluded_global(self, series_name, title, subjects):
        """Exclusions pour éviter faux positifs globaux"""
        excludes = [
            'the', 'a', 'an', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for',
            'journal', 'proceedings', 'conference', 'thesis', 'dissertation',
            'report', 'study', 'research', 'analysis', 'survey', 'review'
        ]
        
        if series_name.lower() in excludes:
            return True
            
        # Exclure titres trop courts ou génériques
        if len(series_name) < 2:
            return True
            
        return False
    
    def _calculate_global_confidence(self, series_name, authors, subjects, original_title):
        """Calculer confiance approche globale"""
        confidence = 70  # Base permissive
        
        title_lower = original_title.lower()
        subjects_text = ' '.join(subjects).lower() if subjects else ''
        
        # Bonus pour mots-clés série
        series_keywords = ['series', 'saga', 'cycle', 'trilogy', 'collection', 'chronicles']
        for keyword in series_keywords:
            if keyword in title_lower:
                confidence += 8
        
        # Bonus pour numérotation claire
        if re.search(r'\b(?:book|volume|part|tome)\s+\d+', title_lower):
            confidence += 10
        
        # Bonus pour auteurs multiples
        if authors and len(authors) > 1:
            confidence += 5
        
        # Bonus pour genres populaires
        popular_genres = ['fiction', 'novel', 'story', 'romance', 'mystery', 'fantasy']
        for genre in popular_genres:
            if genre in subjects_text or genre in title_lower:
                confidence += 3
        
        return min(confidence, 100)
    
    async def _search_global(self, session, query, limit=30):
        """Recherche globale avec délai respectueux"""
        url = "https://openlibrary.org/search.json"
        params = {
            'q': query,
            'limit': limit,
            'fields': 'key,title,author_name,subject,first_publish_year,language'
        }
        
        try:
            await asyncio.sleep(random.uniform(0.4, 0.8))
            
            async with session.get(url, params=params, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    self.api_calls += 1
                    return data.get('docs', [])
                else:
                    return []
                    
        except Exception as e:
            logger.error(f"Erreur: {str(e)}")
            return []
    
    async def expand_globally(self, max_queries=120):
        """Expansion globale massive"""
        logger.info("🌎 DÉBUT EXPANSION GLOBALE TOUS AZIMUTS")
        
        queries = self._generate_global_queries()
        random.shuffle(queries)  # Mélanger pour diversité
        
        discoveries = []
        
        async with aiohttp.ClientSession() as session:
            for i, query in enumerate(queries[:max_queries]):
                if i % 15 == 0:
                    logger.info(f"🌎 Progression globale: {i}/{min(max_queries, len(queries))}")
                
                books = await self._search_global(session, query, 30)
                
                for book in books:
                    self.books_analyzed += 1
                    
                    title = book.get('title', '')
                    authors = book.get('author_name', [])
                    subjects = book.get('subject', [])
                    
                    series_info = self._detect_global_series(title, authors, subjects)
                    if series_info:
                        series_key = series_info['name'].lower()
                        if series_key not in self.existing_series:
                            discoveries.append(series_info)
                            self.existing_series.add(series_key)
                            logger.info(f"🆕 Global: {series_info['name']} (conf: {series_info['confidence']}%)")
                
                # Limite API
                if self.api_calls >= 180:
                    logger.warning("⚠️ Limite API atteinte")
                    break
        
        self.new_series_found = discoveries
        return discoveries
    
    def _save_global_discoveries(self):
        """Sauvegarder découvertes globales"""
        if not self.new_series_found:
            logger.info("❌ Aucune nouvelle série globale trouvée")
            return
        
        # Charger base
        series_path = Path('/app/backend/data/extended_series_database.json')
        with open(series_path, 'r') as f:
            existing_series = json.load(f)
        
        # Créer nouvelles entrées
        new_entries = []
        for discovery in self.new_series_found:
            series_entry = {
                "name": discovery['name'],
                "authors": ["Various"],
                "category": "roman",
                "volumes": 1,
                "keywords": [discovery['name'].lower(), "global expansion"],
                "variations": [discovery['name'], discovery['name'].lower()],
                "languages": ["en", "fr"],
                "description": f"Série expansion globale (confiance: {discovery['confidence']}%)",
                "confidence_score": discovery['confidence'],
                "detection_method": discovery['detection_method'],
                "source": "ultra_harvest_global_expansion_session_81_26c",
                "first_published": 2020,
                "status": "active",
                "subjects": ["global expansion", "diversified"],
                "patterns": {
                    "title_patterns": [discovery['name']],
                    "exclude_patterns": ["journal", "proceedings"]
                }
            }
            new_entries.append(series_entry)
        
        # Backup et sauvegarde
        backup_path = series_path.parent / f"extended_series_database_backup_global_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        import shutil
        shutil.copy2(series_path, backup_path)
        
        existing_series.extend(new_entries)
        
        with open(series_path, 'w', encoding='utf-8') as f:
            json.dump(existing_series, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ {len(new_entries)} nouvelles séries globales ajoutées")
        logger.info(f"💾 Backup: {backup_path.name}")

async def main():
    """Expansion globale principale"""
    harvester = GlobalExpansionHarvest()
    
    logger.info("🌎 ULTRA HARVEST EXPANSION GLOBALE - SESSION 81.26C")
    logger.info(f"📊 Base: {len(harvester.existing_series)} séries")
    
    # Expansion massive
    discoveries = await harvester.expand_globally(max_queries=100)
    
    # Sauvegarder
    harvester._save_global_discoveries()
    
    # Résumé final
    duration = datetime.now() - harvester.start_time
    logger.info("🎯 EXPANSION GLOBALE TERMINÉE")
    logger.info(f"⏱️ Durée: {duration}")
    logger.info(f"📚 Livres analysés: {harvester.books_analyzed}")
    logger.info(f"🔍 API calls: {harvester.api_calls}")
    logger.info(f"🆕 Nouvelles séries: {len(discoveries)}")
    
    if discoveries:
        logger.info("🌟 TOP EXPANSIONS GLOBALES:")
        for i, d in enumerate(discoveries[:15], 1):
            logger.info(f"  {i}. {d['name']} (conf: {d['confidence']}%)")

if __name__ == "__main__":
    asyncio.run(main())