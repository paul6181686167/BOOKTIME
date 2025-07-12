#!/usr/bin/env python3
"""
🔍 ULTRA HARVEST NICHES ULTRA-SPÉCIALISÉES 70% - SESSION 81.26B
Script pour explorer des micro-niches très spécialisées avec seuil 70%
Focus sur des domaines ultra-techniques et spécialisés
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
logger = logging.getLogger('UltraHarvestMicroNiches')

class MicroNichesHarvest:
    """Ultra Harvest pour micro-niches ultra-spécialisées"""
    
    def __init__(self):
        self.new_series_found = []
        self.books_analyzed = 0
        self.api_calls = 0
        self.start_time = datetime.now()
        self.confidence_threshold = 70
        
        # Charger base existante
        self.existing_series = set()
        self._load_existing_series()
        
        # Patterns ultra-spécialisés
        self._init_micro_patterns()
    
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
    
    def _init_micro_patterns(self):
        """Patterns pour micro-niches ultra-spécialisées"""
        self.micro_patterns = [
            # Professions ultra-spécialisées
            r'(.+?)\s+(?:certification|cert)\s+(?:guide|book)\s*(\d+)',
            r'(.+?)\s+(?:professional|pro)\s+(?:handbook|manual)\s*(\d+)',
            r'(.+?)\s+(?:training|formation)\s+(?:course|cours)\s*(\d+)',
            
            # Hobbies ultra-spécialisés
            r'(.+?)\s+(?:collecting|collection)\s+(?:guide|handbook)\s*(\d+)',
            r'(.+?)\s+(?:modeling|models)\s+(?:book|guide)\s*(\d+)',
            r'(.+?)\s+(?:restoration|repair)\s+(?:manual|guide)\s*(\d+)',
            
            # Régions géographiques spécifiques
            r'(.+?)\s+(?:regional|local)\s+(?:guide|handbook)\s*(\d+)',
            r'(.+?)\s+(?:provincial|state)\s+(?:series|collection)\s*(\d+)',
            r'(.+?)\s+(?:county|district)\s+(?:history|guide)\s*(\d+)',
            
            # Sciences ultra-spécialisées
            r'(.+?)\s+(?:microscopy|microsc)\s+(?:handbook|guide)\s*(\d+)',
            r'(.+?)\s+(?:spectroscopy|spectr)\s+(?:manual|book)\s*(\d+)',
            r'(.+?)\s+(?:crystallography|crystal)\s+(?:guide|handbook)\s*(\d+)',
            
            # Arts martiaux et sports spécialisés
            r'(.+?)\s+(?:martial arts|arts martiaux)\s+(?:series|guide)\s*(\d+)',
            r'(.+?)\s+(?:aikido|judo|karate)\s+(?:book|manual)\s*(\d+)',
            r'(.+?)\s+(?:archery|tir à l\'arc)\s+(?:guide|handbook)\s*(\d+)',
            
            # Musique ultra-spécialisée
            r'(.+?)\s+(?:sheet music|partition)\s+(?:book|collection)\s*(\d+)',
            r'(.+?)\s+(?:instrument|musical)\s+(?:method|méthode)\s*(\d+)',
            r'(.+?)\s+(?:composition|theory)\s+(?:book|guide)\s*(\d+)',
            
            # Langues rares
            r'(.+?)\s+(?:language|langue)\s+(?:course|cours)\s*(?:book|livre)\s*(\d+)',
            r'(.+?)\s+(?:dictionary|dictionnaire)\s*(?:volume|tome)\s*(\d+)',
            r'(.+?)\s+(?:grammar|grammaire)\s+(?:book|livre)\s*(\d+)',
            
            # Collectibles et antiquités
            r'(.+?)\s+(?:antique|antiques)\s+(?:guide|collector)\s*(\d+)',
            r'(.+?)\s+(?:vintage|collectible)\s+(?:book|guide)\s*(\d+)',
            r'(.+?)\s+(?:price guide|guide prix)\s*(\d+)',
            
            # Santé alternative
            r'(.+?)\s+(?:herbal|herbs)\s+(?:medicine|guide)\s*(\d+)',
            r'(.+?)\s+(?:homeopathy|homeo)\s+(?:handbook|guide)\s*(\d+)',
            r'(.+?)\s+(?:acupuncture|energy)\s+(?:healing|guide)\s*(\d+)',
            
            # Industries spécialisées
            r'(.+?)\s+(?:aerospace|aviation)\s+(?:handbook|manual)\s*(\d+)',
            r'(.+?)\s+(?:maritime|marine)\s+(?:guide|handbook)\s*(\d+)',
            r'(.+?)\s+(?:mining|petroleum)\s+(?:manual|guide)\s*(\d+)',
            
            # Technologies émergentes
            r'(.+?)\s+(?:blockchain|crypto)\s+(?:guide|handbook)\s*(\d+)',
            r'(.+?)\s+(?:ai|artificial intelligence)\s+(?:book|guide)\s*(\d+)',
            r'(.+?)\s+(?:iot|internet of things)\s+(?:handbook|guide)\s*(\d+)',
        ]
    
    def _generate_micro_niche_queries(self):
        """Générer requêtes pour micro-niches ultra-spécialisées"""
        return [
            # Professions ultra-spécialisées
            "sommelier certification book", "genealogy research guide", "private investigator manual",
            "funeral director handbook", "locksmith training book", "elevator technician guide",
            "court reporter certification", "water well drilling manual", "chimney sweep handbook",
            "piano tuner guide book", "clockmaker restoration manual", "taxidermy guide book",
            
            # Hobbies ultra-spécialisés  
            "vintage radio collecting", "meteorite hunting guide", "bottle cap collecting book",
            "postcard collecting handbook", "coin grading guide book", "stamp catalog series",
            "model railroad scenery book", "rc helicopter manual", "slot car racing guide",
            "dollhouse miniatures book", "origami advanced techniques", "paper airplane design",
            
            # Sports et activités nichées
            "falconry training manual", "beekeeping seasonal guide", "mushroom foraging book",
            "geocaching adventure guide", "metal detecting handbook", "fossil hunting guide",
            "astronomy observation log", "bird watching field guide", "wildflower identification",
            "tree identification guide", "butterfly field guide", "mineral identification",
            
            # Arts et crafts ultra-spécialisés
            "bookbinding traditional methods", "calligraphy brush techniques", "stained glass patterns",
            "chain mail making guide", "blacksmithing projects book", "leather working patterns",
            "soap making advanced", "candle making techniques", "pewter casting manual",
            "glass blowing guide", "pottery wheel throwing", "silk painting techniques",
            
            # Cultures et traditions
            "bagpipe music collection", "dulcimer playing guide", "hurdy gurdy manual",
            "concertina instruction book", "morris dancing guide", "folk dance collection",
            "traditional crafts revival", "heritage skills manual", "ancestral techniques",
            
            # Sciences appliquées nichées
            "beehive inspection guide", "soil analysis handbook", "water quality testing",
            "air quality monitoring", "noise level measurement", "electromagnetic fields guide",
            "radiation detection manual", "chemical analysis guide", "microscopy techniques",
            
            # Réparation ultra-spécialisée
            "antique clock repair", "vintage camera restoration", "tube radio service",
            "mechanical watch repair", "fountain pen restoration", "typewriter maintenance",
            "player piano restoration", "grandfather clock repair", "music box restoration",
            
            # Collections spécialisées
            "military button collecting", "thimble collecting guide", "spoon collecting handbook",
            "key collecting reference", "matchbook collecting", "tobacco card collecting",
            "vintage toy collecting", "advertising memorabilia", "railroad memorabilia guide",
            
            # Régions géographiques ultra-spécifiques
            "appalachian folklore collection", "pacific northwest mushrooms", "desert survival manual",
            "arctic exploration guide", "tropical plant identification", "coastal ecology handbook",
            "mountain climbing routes", "cave exploration guide", "swamp navigation manual",
            
            # Langues et cultures rares
            "gaelic language course", "sanskrit learning guide", "ancient greek primer",
            "latin conversation book", "esperanto grammar book", "sign language regional",
            "native american languages", "polynesian culture guide", "celtic mythology collection",
            
            # Médecines alternatives
            "crystal healing handbook", "essential oils guide", "reflexology manual",
            "reiki healing methods", "chakra balancing guide", "feng shui home design",
            "ayurveda cooking book", "traditional chinese medicine", "naturopathy handbook",
            
            # Technologies ultra-spécialisées
            "cnc machining manual", "3d printing advanced", "laser cutting guide",
            "vacuum tube electronics", "ham radio construction", "antenna design book",
            "microcontroller projects", "sensor network design", "embedded systems guide",
            
            # Industries de niche
            "beekeeping commercial", "aquaculture systems", "greenhouse management",
            "hydroponics advanced", "permaculture design", "sustainable farming",
            "organic certification", "biodynamic agriculture", "regenerative farming",
            
            # Arts martiaux spécialisés
            "kendo practice guide", "iaido sword training", "kyudo archery manual",
            "capoeira movement book", "escrima stick fighting", "wing chun techniques",
            "tai chi advanced forms", "qigong energy work", "aikido philosophy book",
            
            # Collectibles vintage
            "vintage electronics repair", "antique furniture restoration", "classic car maintenance",
            "vintage clothing care", "retro gaming repair", "old book conservation",
            "vinyl record care", "antique jewelry guide", "vintage watch collecting"
        ]
    
    def _detect_micro_series(self, title, authors, subjects):
        """Détecter séries dans micro-niches"""
        if not title:
            return None
            
        title_lower = title.lower()
        
        # Patterns spécialisés
        for pattern in self.micro_patterns:
            match = re.search(pattern, title_lower)
            if match:
                series_name = match.group(1).strip()
                volume_num = match.group(2) if len(match.groups()) > 1 else "1"
                
                if len(series_name) >= 3 and series_name not in self.existing_series:
                    confidence = self._calculate_micro_confidence(series_name, authors, subjects, title)
                    if confidence >= self.confidence_threshold:
                        return {
                            'name': series_name.title(),
                            'volume': volume_num,
                            'confidence': confidence,
                            'detection_method': 'micro_niche_patterns',
                            'original_title': title
                        }
        
        return None
    
    def _calculate_micro_confidence(self, series_name, authors, subjects, original_title):
        """Calculer confiance pour micro-niches"""
        confidence = 70  # Base
        
        # Mots-clés micro-niches
        micro_keywords = [
            'certification', 'professional', 'handbook', 'manual', 'guide',
            'collecting', 'restoration', 'repair', 'traditional', 'specialized',
            'advanced', 'techniques', 'methods', 'training', 'course'
        ]
        
        title_lower = original_title.lower()
        subjects_text = ' '.join(subjects).lower() if subjects else ''
        
        for keyword in micro_keywords:
            if keyword in title_lower or keyword in subjects_text:
                confidence += 3
        
        # Bonus pour numérotation
        if re.search(r'\b(?:volume|book|part|level)\s+\d+', title_lower):
            confidence += 10
        
        # Bonus pour séries techniques
        if any(word in title_lower for word in ['series', 'collection', 'set']):
            confidence += 5
        
        return min(confidence, 100)
    
    async def _search_micro_niche(self, session, query, limit=25):
        """Rechercher dans micro-niche"""
        url = "https://openlibrary.org/search.json"
        params = {
            'q': query,
            'limit': limit,
            'fields': 'key,title,author_name,subject,first_publish_year'
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
            logger.error(f"Error: {str(e)}")
            return []
    
    async def explore_micro_niches(self, max_queries=100):
        """Explorer micro-niches intensivement"""
        logger.info("🔍 DÉBUT EXPLORATION MICRO-NICHES ULTRA-SPÉCIALISÉES")
        
        queries = self._generate_micro_niche_queries()
        discoveries = []
        
        async with aiohttp.ClientSession() as session:
            for i, query in enumerate(queries[:max_queries]):
                if i % 10 == 0:
                    logger.info(f"🔍 Progression: {i}/{min(max_queries, len(queries))} niches explorées")
                
                books = await self._search_micro_niche(session, query, 25)
                
                for book in books:
                    self.books_analyzed += 1
                    
                    title = book.get('title', '')
                    authors = book.get('author_name', [])
                    subjects = book.get('subject', [])
                    
                    # Exclure académique basique
                    if any(x in title.lower() for x in ['journal of', 'proceedings', 'thesis']):
                        continue
                    
                    series_info = self._detect_micro_series(title, authors, subjects)
                    if series_info:
                        series_key = series_info['name'].lower()
                        if series_key not in self.existing_series:
                            discoveries.append(series_info)
                            self.existing_series.add(series_key)
                            logger.info(f"🆕 Micro-niche: {series_info['name']} (conf: {series_info['confidence']}%)")
                
                # Limite sécurisée
                if self.api_calls >= 150:
                    logger.warning("⚠️ Limite API atteinte")
                    break
        
        self.new_series_found = discoveries
        return discoveries
    
    def _save_micro_discoveries(self):
        """Sauvegarder découvertes micro-niches"""
        if not self.new_series_found:
            logger.info("❌ Aucune nouvelle série micro-niche trouvée")
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
                "authors": ["Specialist"],
                "category": "roman",  # Sera affiné
                "volumes": 1,
                "keywords": [discovery['name'].lower(), "micro niche", "specialized"],
                "variations": [discovery['name'], discovery['name'].lower()],
                "languages": ["en", "fr"],
                "description": f"Série micro-niche ultra-spécialisée (confiance: {discovery['confidence']}%)",
                "confidence_score": discovery['confidence'],
                "detection_method": discovery['detection_method'],
                "source": "ultra_harvest_micro_niches_session_81_26b",
                "first_published": 2020,
                "status": "active",
                "subjects": ["micro niche", "specialized", "professional"],
                "patterns": {
                    "title_patterns": [discovery['name']],
                    "exclude_patterns": ["anthology", "journal"]
                }
            }
            new_entries.append(series_entry)
        
        # Backup et sauvegarde
        backup_path = series_path.parent / f"extended_series_database_backup_micro_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        import shutil
        shutil.copy2(series_path, backup_path)
        
        existing_series.extend(new_entries)
        
        with open(series_path, 'w', encoding='utf-8') as f:
            json.dump(existing_series, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ {len(new_entries)} nouvelles séries micro-niches ajoutées")
        logger.info(f"💾 Backup: {backup_path.name}")

async def main():
    """Exploration micro-niches principale"""
    harvester = MicroNichesHarvest()
    
    logger.info("🔍 ULTRA HARVEST MICRO-NICHES - SESSION 81.26B")
    logger.info(f"📊 Base: {len(harvester.existing_series)} séries")
    
    # Explorer intensivement
    discoveries = await harvester.explore_micro_niches(max_queries=80)
    
    # Sauvegarder
    harvester._save_micro_discoveries()
    
    # Résumé
    duration = datetime.now() - harvester.start_time
    logger.info("🎯 MICRO-NICHES EXPLORATION TERMINÉE")
    logger.info(f"⏱️ Durée: {duration}")
    logger.info(f"📚 Livres analysés: {harvester.books_analyzed}")
    logger.info(f"🔍 API calls: {harvester.api_calls}")
    logger.info(f"🆕 Nouvelles séries: {len(discoveries)}")
    
    if discoveries:
        logger.info("🌟 TOP MICRO-NICHES:")
        for i, d in enumerate(discoveries[:10], 1):
            logger.info(f"  {i}. {d['name']} (conf: {d['confidence']}%)")

if __name__ == "__main__":
    asyncio.run(main())