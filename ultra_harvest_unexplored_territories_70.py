#!/usr/bin/env python3
"""
🌍 ULTRA HARVEST TERRITOIRES INEXPLORÉS - EXPANSION MASSIVE CONFIANCE 70%
Script spécialisé pour découvrir des territoires complètement nouveaux
Version: Session 81.26 - Exploration maximale niches inédites
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

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('UltraHarvestUnexplored')

class UnexploredTerritoriesHarvest:
    """Ultra Harvest spécialisé pour territoires complètement inexplorés"""
    
    def __init__(self):
        self.new_series_found = []
        self.books_analyzed = 0
        self.api_calls = 0
        self.start_time = datetime.now()
        self.confidence_threshold = 70
        
        # Charger base existante pour éviter doublons
        self.existing_series = set()
        self._load_existing_series()
        
        # Base de tracking
        self.tracking_db_path = Path('/app/data/ultra_harvest_tracking.db')
        self._init_tracking()
        
        # Patterns détection ultra-spécialisés pour territoires inexplorés
        self._init_unexplored_patterns()
    
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
        """Initialiser base SQLite tracking"""
        self.tracking_db_path.parent.mkdir(exist_ok=True)
        with sqlite3.connect(self.tracking_db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS processed_books (
                    ol_key TEXT PRIMARY KEY,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
    
    def _init_unexplored_patterns(self):
        """Patterns pour détecter séries dans territoires inexplorés"""
        self.unexplored_patterns = [
            # Visual novels et interactive fiction
            r'(.+?)\s+(?:visual novel|vn)\s*(\d+)',
            r'(.+?)\s+(?:interactive fiction|if)\s*(\d+)',
            r'(.+?)\s+(?:game book|gamebook)\s*(\d+)',
            
            # Poésie et théâtre
            r'(.+?)\s+(?:poetry|poems|poésie)\s*(?:book|volume)\s*(\d+)',
            r'(.+?)\s+(?:plays|théâtre|theater)\s*(?:book|volume)\s*(\d+)',
            r'(.+?)\s+(?:sonnets|odes)\s*(?:book|volume)\s*(\d+)',
            
            # Séries éducatives
            r'(.+?)\s+(?:textbook|manuel)\s*(\d+)',
            r'(.+?)\s+(?:course|cours)\s*(?:book|livre)\s*(\d+)',
            r'(.+?)\s+(?:workbook|cahier)\s*(\d+)',
            r'(.+?)\s+(?:study guide|guide)\s*(\d+)',
            
            # Littérature internationale spécialisée
            r'(.+?)\s+(?:african|africain)\s+(?:stories|tales)\s*(\d+)',
            r'(.+?)\s+(?:latin american|latino)\s+(?:fiction|novels)\s*(\d+)',
            r'(.+?)\s+(?:slavic|eastern european)\s+(?:tales|stories)\s*(\d+)',
            r'(.+?)\s+(?:nordic|scandinavian)\s+(?:sagas|tales)\s*(\d+)',
            
            # Fiction académique et littéraire
            r'(.+?)\s+(?:academic fiction|campus novel)\s*(\d+)',
            r'(.+?)\s+(?:philosophical novel|roman philosophique)\s*(\d+)',
            r'(.+?)\s+(?:experimental fiction|fiction expérimentale)\s*(\d+)',
            
            # Collections et anthologies spécialisées
            r'(.+?)\s+(?:anthology|anthologie)\s*(?:volume|tome)\s*(\d+)',
            r'(.+?)\s+(?:collection|recueil)\s*(?:volume|tome)\s*(\d+)',
            r'(.+?)\s+(?:compendium|compilation)\s*(\d+)',
            
            # Séries spirituelles et religieuses
            r'(.+?)\s+(?:spiritual|spirituel)\s+(?:journey|path)\s*(\d+)',
            r'(.+?)\s+(?:meditation|méditation)\s+(?:guide|series)\s*(\d+)',
            r'(.+?)\s+(?:religious|religieux)\s+(?:studies|études)\s*(\d+)',
            
            # Artisanat et DIY spécialisés
            r'(.+?)\s+(?:craft|artisanat)\s+(?:project|projects)\s*(\d+)',
            r'(.+?)\s+(?:diy|do it yourself)\s+(?:guide|series)\s*(\d+)',
            r'(.+?)\s+(?:workshop|atelier)\s+(?:manual|manuel)\s*(\d+)',
            
            # Guides de voyage spécialisés
            r'(.+?)\s+(?:travel guide|guide voyage)\s*(\d+)',
            r'(.+?)\s+(?:backpacker|routard)\s+(?:guide|series)\s*(\d+)',
            r'(.+?)\s+(?:cultural guide|guide culturel)\s*(\d+)',
            
            # Biographies et mémoires
            r'(.+?)\s+(?:biography|biographie)\s*(?:volume|tome)\s*(\d+)',
            r'(.+?)\s+(?:memoir|mémoires)\s*(?:book|livre)\s*(\d+)',
            r'(.+?)\s+(?:life story|histoire de vie)\s*(\d+)',
            
            # Documents historiques
            r'(.+?)\s+(?:historical documents|documents historiques)\s*(\d+)',
            r'(.+?)\s+(?:chronicles|chroniques)\s*(?:volume|tome)\s*(\d+)',
            r'(.+?)\s+(?:archives|documents)\s*(?:series|série)\s*(\d+)',
            
            # Séries techniques ultra-spécialisées
            r'(.+?)\s+(?:technical manual|manuel technique)\s*(\d+)',
            r'(.+?)\s+(?:engineering|ingénierie)\s+(?:handbook|manuel)\s*(\d+)',
            r'(.+?)\s+(?:programming|programmation)\s+(?:guide|series)\s*(\d+)',
            
            # Formats émergents
            r'(.+?)\s+(?:podcast|audio)\s+(?:series|série)\s*(\d+)',
            r'(.+?)\s+(?:multimedia|multimédia)\s+(?:book|livre)\s*(\d+)',
            r'(.+?)\s+(?:digital|numérique)\s+(?:edition|édition)\s*(\d+)',
            
            # Genres littéraires spécialisés
            r'(.+?)\s+(?:dystopian|dystopie)\s+(?:series|série)\s*(\d+)',
            r'(.+?)\s+(?:utopian|utopie)\s+(?:fiction|roman)\s*(\d+)',
            r'(.+?)\s+(?:alternate history|histoire alternative)\s*(\d+)',
            r'(.+?)\s+(?:steampunk|cyberpunk)\s+(?:series|série)\s*(\d+)',
            
            # Littérature pour publics spéciaux
            r'(.+?)\s+(?:young adult|jeunes adultes)\s+(?:series|série)\s*(\d+)',
            r'(.+?)\s+(?:middle grade|collégiens)\s+(?:series|série)\s*(\d+)',
            r'(.+?)\s+(?:easy reader|lecture facile)\s*(\d+)',
            r'(.+?)\s+(?:large print|gros caractères)\s*(\d+)',
            
            # Formats courts et nouvelles
            r'(.+?)\s+(?:short stories|nouvelles)\s*(?:collection|recueil)\s*(\d+)',
            r'(.+?)\s+(?:novellas|novelles)\s*(?:series|série)\s*(\d+)',
            r'(.+?)\s+(?:flash fiction|micro-fiction)\s*(\d+)',
        ]
    
    def _generate_unexplored_queries(self):
        """Générer requêtes pour territoires complètement inexplorés"""
        queries = []
        
        # === TERRITOIRES INEXPLORÉS COMPLETS === #
        
        # 1. Visual Novels et Interactive Fiction
        visual_novel_queries = [
            "visual novel series", "interactive fiction book", "game book series",
            "choice book series", "adventure game book", "solo rpg book",
            "branching story book", "cyoa choose your own adventure"
        ]
        
        # 2. Poésie et Arts Littéraires
        poetry_queries = [
            "poetry book series", "sonnets collection", "haiku book series",
            "verse novel series", "epic poetry book", "spoken word collection",
            "slam poetry book", "contemporary poetry series"
        ]
        
        # 3. Théâtre et Scripts
        theater_queries = [
            "play script series", "theater collection", "drama script book",
            "screenplay series", "monologue collection", "one act play",
            "musical theater book", "experimental theater"
        ]
        
        # 4. Éducation Spécialisée
        education_queries = [
            "textbook series mathematics", "science workbook series", "language learning book",
            "study guide series", "exam preparation book", "educational activity book",
            "curriculum guide series", "teacher manual series"
        ]
        
        # 5. Littérature Mondiale Spécialisée
        world_literature_queries = [
            "african literature series", "latin american fiction collection", "nordic saga book",
            "slavic tales collection", "asian folklore series", "middle eastern stories",
            "indigenous literature book", "postcolonial fiction series"
        ]
        
        # 6. Fiction Académique
        academic_fiction_queries = [
            "campus novel series", "philosophical fiction book", "academic mystery series",
            "university fiction collection", "intellectual fiction series", "literary fiction experimental"
        ]
        
        # 7. Anthologies et Collections
        anthology_queries = [
            "anthology series science fiction", "short story collection", "essay collection book",
            "literary magazine collection", "journal anthology", "compendium series"
        ]
        
        # 8. Spiritualité et Philosophie
        spiritual_queries = [
            "meditation guide series", "spiritual journey book", "philosophy series book",
            "mindfulness book series", "wisdom tradition book", "contemplative book series",
            "religious studies series", "theological commentary"
        ]
        
        # 9. Artisanat Ultra-Spécialisé
        craft_queries = [
            "woodworking project book", "pottery guide series", "textile craft book",
            "metalworking manual series", "jewelry making book", "glass art guide",
            "ceramic art book series", "fiber arts collection"
        ]
        
        # 10. Voyage et Culture
        travel_culture_queries = [
            "cultural guide series", "travel photography book", "backpacker guide series",
            "cultural anthropology book", "ethnographic study book", "travel memoir series",
            "adventure travel guide", "cultural immersion book"
        ]
        
        # 11. Biographies Spécialisées
        biography_queries = [
            "artist biography series", "scientist biography book", "explorer biography collection",
            "political biography series", "cultural figure biography", "innovator biography book",
            "historical figure biography", "creative biography series"
        ]
        
        # 12. Documents et Archives
        historical_queries = [
            "historical documents collection", "archive series book", "chronicle collection",
            "primary source book", "documentary series book", "historical evidence collection",
            "witness account book", "oral history collection"
        ]
        
        # 13. Techniques Ultra-Spécialisées
        technical_queries = [
            "engineering handbook series", "technical manual collection", "professional guide book",
            "industry handbook series", "specialized manual book", "expert guide collection",
            "technical reference series", "professional practice book"
        ]
        
        # 14. Formats Émergents
        emerging_format_queries = [
            "audio book series original", "podcast book series", "multimedia book collection",
            "digital book series", "interactive book series", "augmented reality book",
            "virtual reality book", "hybrid media book"
        ]
        
        # 15. Genres Littéraires Émergents
        emerging_genre_queries = [
            "cli-fi climate fiction", "solarpunk fiction series", "biopunk book series",
            "hopepunk fiction book", "cottagecore book series", "dark academia fiction",
            "urban fantasy noir", "contemporary magical realism"
        ]
        
        # 16. Publics Spéciaux
        special_audience_queries = [
            "neurodivergent fiction series", "disability representation book", "lgbtq+ historical fiction",
            "multicultural book series", "bilingual book series", "easy reader adult",
            "high interest low level", "graphic medicine book"
        ]
        
        # 17. Sciences et Recherche
        science_queries = [
            "popular science series", "research methodology book", "scientific biography series",
            "citizen science book", "science communication series", "environmental science book",
            "climate science series", "conservation biology book"
        ]
        
        # 18. Wellness et Développement
        wellness_queries = [
            "wellness guide series", "mental health book series", "therapeutic book collection",
            "healing arts book", "alternative medicine series", "holistic health book",
            "trauma recovery book", "resilience building series"
        ]
        
        # 19. Arts et Créativité
        arts_queries = [
            "art technique book series", "creative process book", "artistic method collection",
            "studio practice book", "creative writing guide", "artistic inspiration series",
            "art history specialized", "medium specific art book"
        ]
        
        # 20. Nouveaux Médias
        new_media_queries = [
            "social media book series", "digital culture book", "internet culture series",
            "meme culture book", "online community book", "digital sociology series",
            "cyber culture book", "virtual community study"
        ]
        
        # Combiner tous les territoires
        all_territories = [
            visual_novel_queries, poetry_queries, theater_queries, education_queries,
            world_literature_queries, academic_fiction_queries, anthology_queries,
            spiritual_queries, craft_queries, travel_culture_queries, biography_queries,
            historical_queries, technical_queries, emerging_format_queries,
            emerging_genre_queries, special_audience_queries, science_queries,
            wellness_queries, arts_queries, new_media_queries
        ]
        
        # Créer requêtes finales
        for territory in all_territories:
            queries.extend(territory)
        
        return queries
    
    def _detect_series_from_title(self, title, authors, subjects):
        """Détecter série potentielle avec patterns territoires inexplorés"""
        if not title:
            return None
            
        title_lower = title.lower()
        
        # Vérifier patterns spécialisés
        for pattern in self.unexplored_patterns:
            match = re.search(pattern, title_lower)
            if match:
                series_name = match.group(1).strip()
                volume_num = match.group(2) if len(match.groups()) > 1 else "1"
                
                # Validation série
                if len(series_name) >= 3 and series_name not in self.existing_series:
                    confidence = self._calculate_confidence(series_name, authors, subjects, title)
                    if confidence >= self.confidence_threshold:
                        return {
                            'name': series_name.title(),
                            'volume': volume_num,
                            'confidence': confidence,
                            'detection_method': 'unexplored_patterns',
                            'original_title': title
                        }
        
        return None
    
    def _calculate_confidence(self, series_name, authors, subjects, original_title):
        """Calculer confiance pour territoires inexplorés"""
        confidence = 70  # Base pour nouveaux territoires
        
        # Bonus pour mots-clés territoires inexplorés
        unexplored_keywords = [
            'visual novel', 'interactive', 'poetry', 'anthology', 'spiritual',
            'cultural', 'biography', 'academic', 'experimental', 'multimedia',
            'educational', 'therapeutic', 'artisanal', 'documentary'
        ]
        
        title_lower = original_title.lower()
        subjects_text = ' '.join(subjects).lower() if subjects else ''
        
        for keyword in unexplored_keywords:
            if keyword in title_lower or keyword in subjects_text:
                confidence += 5
        
        # Bonus pour auteurs multiples (indication série)
        if authors and len(authors) > 1:
            confidence += 5
        
        # Bonus pour numérotation claire
        if re.search(r'\b(?:volume|book|tome|part)\s+\d+', title_lower):
            confidence += 10
        
        return min(confidence, 100)
    
    def _is_excluded_content(self, title, subjects):
        """Vérifier exclusions mais garder nouveaux territoires"""
        if not title and not subjects:
            return True
            
        title_lower = title.lower() if title else ''
        subjects_text = ' '.join(subjects).lower() if subjects else ''
        
        # Exclusions Session 81.18 (cookbooks, academic journals)
        excluded_keywords = [
            'cookbook', 'recipe', 'journal of', 'proceedings of',
            'conference paper', 'research paper', 'thesis'
        ]
        
        for keyword in excluded_keywords:
            if keyword in title_lower or keyword in subjects_text:
                return True
        
        return False
    
    async def _search_books(self, session, query, limit=50):
        """Rechercher livres pour territoire donné"""
        url = "https://openlibrary.org/search.json"
        params = {
            'q': query,
            'limit': limit,
            'fields': 'key,title,author_name,subject,first_publish_year,language'
        }
        
        try:
            await asyncio.sleep(random.uniform(0.3, 0.7))  # Rate limiting respectueux
            
            async with session.get(url, params=params, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    self.api_calls += 1
                    return data.get('docs', [])
                else:
                    logger.warning(f"API error {response.status} for query: {query}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error searching {query}: {str(e)}")
            return []
    
    async def _process_territory(self, session, territory_queries, territory_name):
        """Traiter un territoire complet"""
        logger.info(f"🌍 Exploration territoire: {territory_name}")
        territory_discoveries = []
        
        for query in territory_queries:
            books = await self._search_books(session, query, 30)
            
            for book in books:
                self.books_analyzed += 1
                
                title = book.get('title', '')
                authors = book.get('author_name', [])
                subjects = book.get('subject', [])
                
                if self._is_excluded_content(title, subjects):
                    continue
                
                series_info = self._detect_series_from_title(title, authors, subjects)
                if series_info:
                    # Vérifier nouveauté
                    series_key = series_info['name'].lower()
                    if series_key not in self.existing_series:
                        territory_discoveries.append(series_info)
                        self.existing_series.add(series_key)
                        logger.info(f"🆕 {territory_name}: {series_info['name']} (conf: {series_info['confidence']}%)")
        
        logger.info(f"✅ {territory_name}: {len(territory_discoveries)} nouvelles séries")
        return territory_discoveries
    
    async def explore_unexplored_territories(self, max_territories=20):
        """Exploration massive territoires inexplorés"""
        logger.info("🚀 DÉBUT EXPLORATION TERRITOIRES INEXPLORÉS")
        
        # Définir territoires avec leurs requêtes
        territories = {
            "Visual Novels & Interactive Fiction": [
                "visual novel series", "interactive fiction book", "game book series",
                "choice book series", "adventure game book"
            ],
            "Poetry & Literary Arts": [
                "poetry book series", "sonnets collection", "verse novel series",
                "epic poetry book", "spoken word collection"
            ],
            "Theater & Scripts": [
                "play script series", "theater collection", "drama script book",
                "screenplay series", "monologue collection"
            ],
            "Specialized Education": [
                "textbook series mathematics", "science workbook series", "language learning book",
                "study guide series", "exam preparation book"
            ],
            "World Literature Niches": [
                "african literature series", "latin american fiction collection", "nordic saga book",
                "slavic tales collection", "asian folklore series"
            ],
            "Academic Fiction": [
                "campus novel series", "philosophical fiction book", "academic mystery series",
                "university fiction collection", "intellectual fiction series"
            ],
            "Anthologies & Collections": [
                "anthology series science fiction", "short story collection", "essay collection book",
                "literary magazine collection", "journal anthology"
            ],
            "Spirituality & Philosophy": [
                "meditation guide series", "spiritual journey book", "philosophy series book",
                "mindfulness book series", "wisdom tradition book"
            ],
            "Ultra-Specialized Crafts": [
                "woodworking project book", "pottery guide series", "textile craft book",
                "metalworking manual series", "jewelry making book"
            ],
            "Travel & Cultural Studies": [
                "cultural guide series", "travel photography book", "backpacker guide series",
                "cultural anthropology book", "ethnographic study book"
            ],
            "Specialized Biographies": [
                "artist biography series", "scientist biography book", "explorer biography collection",
                "political biography series", "cultural figure biography"
            ],
            "Historical Documents": [
                "historical documents collection", "archive series book", "chronicle collection",
                "primary source book", "documentary series book"
            ],
            "Technical Ultra-Specialization": [
                "engineering handbook series", "technical manual collection", "professional guide book",
                "industry handbook series", "specialized manual book"
            ],
            "Emerging Media Formats": [
                "audio book series original", "podcast book series", "multimedia book collection",
                "digital book series", "interactive book series"
            ],
            "Emerging Literary Genres": [
                "cli-fi climate fiction", "solarpunk fiction series", "biopunk book series",
                "hopepunk fiction book", "cottagecore book series"
            ],
            "Special Audiences": [
                "neurodivergent fiction series", "disability representation book", "lgbtq+ historical fiction",
                "multicultural book series", "bilingual book series"
            ],
            "Science & Research": [
                "popular science series", "research methodology book", "scientific biography series",
                "citizen science book", "science communication series"
            ],
            "Wellness & Therapy": [
                "wellness guide series", "mental health book series", "therapeutic book collection",
                "healing arts book", "alternative medicine series"
            ],
            "Arts & Creative Process": [
                "art technique book series", "creative process book", "artistic method collection",
                "studio practice book", "creative writing guide"
            ],
            "Digital Culture": [
                "social media book series", "digital culture book", "internet culture series",
                "meme culture book", "online community book"
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            all_discoveries = []
            
            for territory_name, queries in list(territories.items())[:max_territories]:
                territory_discoveries = await self._process_territory(session, queries, territory_name)
                all_discoveries.extend(territory_discoveries)
                
                # Limite sécurisée API calls
                if self.api_calls >= 200:
                    logger.warning("⚠️ Limite API calls atteinte")
                    break
        
        self.new_series_found = all_discoveries
        return all_discoveries
    
    def _save_discoveries(self):
        """Sauvegarder nouvelles découvertes"""
        if not self.new_series_found:
            logger.info("❌ Aucune nouvelle série trouvée")
            return
        
        # Charger base existante
        series_path = Path('/app/backend/data/extended_series_database.json')
        if series_path.exists():
            with open(series_path, 'r') as f:
                existing_series = json.load(f)
        else:
            existing_series = []
        
        # Convertir découvertes en format base
        new_entries = []
        for discovery in self.new_series_found:
            series_entry = {
                "name": discovery['name'],
                "authors": ["Unknown"],
                "category": "roman",  # Défaut, sera affiné
                "volumes": 1,
                "keywords": [discovery['name'].lower(), "unexplored territory"],
                "variations": [discovery['name'], discovery['name'].lower()],
                "languages": ["en", "fr"],
                "description": f"Série détectée dans territoires inexplorés (confiance: {discovery['confidence']}%)",
                "confidence_score": discovery['confidence'],
                "detection_method": discovery['detection_method'],
                "source": "ultra_harvest_unexplored_territories_session_81_26",
                "first_published": 2020,
                "status": "active",
                "subjects": ["unexplored territory", "new discovery"],
                "patterns": {
                    "title_patterns": [discovery['name']],
                    "exclude_patterns": ["anthology", "collection"]
                }
            }
            new_entries.append(series_entry)
        
        # Ajouter à la base
        existing_series.extend(new_entries)
        
        # Backup sécurisé
        backup_path = series_path.parent / f"extended_series_database_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        if series_path.exists():
            import shutil
            shutil.copy2(series_path, backup_path)
        
        # Sauvegarder nouvelle base
        with open(series_path, 'w', encoding='utf-8') as f:
            json.dump(existing_series, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ {len(new_entries)} nouvelles séries ajoutées à la base")
        logger.info(f"💾 Backup créé: {backup_path.name}")
    
    def generate_report(self):
        """Générer rapport détaillé exploration"""
        duration = datetime.now() - self.start_time
        
        report = {
            "session": "81.26 - Ultra Harvest Territoires Inexplorés",
            "timestamp": datetime.now().isoformat(),
            "execution_time": str(duration),
            "statistics": {
                "books_analyzed": self.books_analyzed,
                "api_calls": self.api_calls,
                "new_series_found": len(self.new_series_found),
                "discovery_rate": len(self.new_series_found) / max(self.books_analyzed, 1) * 100
            },
            "discoveries": self.new_series_found,
            "territories_explored": 20,
            "confidence_threshold": self.confidence_threshold
        }
        
        # Sauvegarder rapport
        report_path = Path(f'/app/reports/ultra_harvest_unexplored_territories_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 Rapport sauvegardé: {report_path}")
        return report

async def main():
    """Fonction principale exploration territoires inexplorés"""
    harvester = UnexploredTerritoriesHarvest()
    
    logger.info("🌍 ULTRA HARVEST TERRITOIRES INEXPLORÉS - SESSION 81.26")
    logger.info(f"📊 Base actuelle: {len(harvester.existing_series)} séries")
    logger.info(f"🎯 Seuil confiance: {harvester.confidence_threshold}%")
    
    # Exploration massive
    discoveries = await harvester.explore_unexplored_territories(max_territories=20)
    
    # Sauvegarder et rapport
    harvester._save_discoveries()
    report = harvester.generate_report()
    
    # Résumé final
    logger.info("🎯 EXPLORATION TERRITOIRES INEXPLORÉS TERMINÉE")
    logger.info(f"📚 Livres analysés: {report['statistics']['books_analyzed']}")
    logger.info(f"🔍 Appels API: {report['statistics']['api_calls']}")
    logger.info(f"🆕 Nouvelles séries: {report['statistics']['new_series_found']}")
    logger.info(f"📈 Taux découverte: {report['statistics']['discovery_rate']:.2f}%")
    
    if discoveries:
        logger.info("🌟 TOP DÉCOUVERTES:")
        for i, discovery in enumerate(discoveries[:10], 1):
            logger.info(f"  {i}. {discovery['name']} (confiance: {discovery['confidence']}%)")

if __name__ == "__main__":
    asyncio.run(main())