#!/usr/bin/env python3
"""
🚀 WIKIPEDIA SERIES ENRICHER V2.0 - Détection Améliorée
Patterns spécialisés pour séries populaires + validation renforcée
"""

import asyncio
import aiohttp
import re
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WikipediaSeriesEnricherV2:
    """Version améliorée avec patterns spécialisés"""
    
    def __init__(self):
        self.session = None
        self.base_url = "https://en.wikipedia.org/api/rest_v1/page/summary/"
        self.series_detected = []
        self.authors_processed = []
        
        # Séries connues pour validation
        self.known_series = {
            'Harry Potter', 'The Dark Tower', 'Discworld', 'Wheel of Time',
            'A Song of Ice and Fire', 'The Hunger Games', 'Percy Jackson',
            'The Mortal Instruments', 'Dune', 'Foundation', 'Earthsea',
            'The Chronicles of Narnia', 'His Dark Materials', 'The Dresden Files',
            'The Witcher', 'Mistborn', 'The Stormlight Archive', 'The Expanse',
            'The Southern Reach', 'The Kingkiller Chronicle', 'The First Law',
            'The Malazan Book of the Fallen', 'The Gentleman Bastard',
            'The Broken Empire', 'The Farseer Trilogy', 'The Culture',
            'Hyperion Cantos', 'The Imperial Radch', 'The Wayfarers',
            'The Expanse', 'The Locked Tomb', 'The Poppy War'
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_author_wikipedia_page(self, author_name: str) -> Optional[Dict]:
        """Récupère la page Wikipedia d'un auteur"""
        try:
            formatted_name = author_name.replace(' ', '_')
            url = f"{self.base_url}{formatted_name}"
            
            logger.info(f"🔍 Recherche Wikipedia pour : {author_name}")
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"✅ Page Wikipedia trouvée : {author_name}")
                    return data
                else:
                    logger.warning(f"❌ Pas de page Wikipedia : {author_name}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Erreur Wikipedia {author_name}: {str(e)}")
            return None
    
    def extract_series_with_improved_patterns(self, description: str, author_name: str) -> List[Dict]:
        """Extraction améliorée avec patterns spécialisés"""
        series_found = []
        
        # Patterns spécialisés pour différents types de séries
        improved_patterns = [
            # Pattern pour séries explicites
            (r'(?:author|creator|writer) of (?:the )?([A-Z][a-zA-Z\s]+?) (?:series|saga|cycle)', 90),
            (r'(?:wrote|created|best known for) (?:the )?([A-Z][a-zA-Z\s]+?) (?:series|novels|books)', 85),
            (r'(?:the )?([A-Z][a-zA-Z\s]+?) (?:fantasy|science fiction|mystery|horror) series', 85),
            
            # Patterns pour séries connues
            (r'(Harry Potter)', 95),
            (r'(The Dark Tower)', 95),
            (r'(Discworld)', 95),
            (r'(Wheel of Time)', 95),
            (r'(A Song of Ice and Fire)', 95),
            (r'(The Hunger Games)', 95),
            (r'(Percy Jackson)', 95),
            (r'(The Mortal Instruments)', 95),
            (r'(Foundation)', 95),
            (r'(Dune)', 95),
            (r'(Earthsea)', 95),
            (r'(The Dresden Files)', 95),
            (r'(Mistborn)', 95),
            (r'(The Stormlight Archive)', 95),
            
            # Patterns pour volumes multiples
            (r'([A-Z][a-zA-Z\s]+?) (?:trilogy|tetralogy|pentalogy)', 80),
            (r'([A-Z][a-zA-Z\s]+?) (?:book series|novel series)', 80),
            (r'([A-Z][a-zA-Z\s]+?) (?:seven|six|five|four|three) (?:books|novels|volumes)', 75),
        ]
        
        logger.info(f"🔍 Analyse améliorée pour : {author_name}")
        
        for pattern, confidence in improved_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                series_name = match.strip()
                
                # Validation renforcée
                if self.is_valid_series_name_v2(series_name):
                    series_info = {
                        'name': series_name,
                        'author': author_name,
                        'source': 'wikipedia_improved',
                        'detected_at': datetime.now().isoformat(),
                        'confidence': confidence,
                        'validation_passed': True
                    }
                    
                    # Vérifier si déjà détecté
                    if not self.is_duplicate_series(series_info):
                        series_found.append(series_info)
                        logger.info(f"📚 Série validée : {series_name} par {author_name} (conf: {confidence}%)")
        
        return series_found
    
    def is_valid_series_name_v2(self, name: str) -> bool:
        """Validation renforcée des noms de séries"""
        # Filtres négatifs
        invalid_keywords = [
            'literature', 'fiction', 'books', 'novels', 'works', 'writing',
            'style', 'genre', 'career', 'life', 'biography', 'awards',
            'university', 'college', 'school', 'education', 'degree',
            'her', 'his', 'and', 'the author', 'bestselling', 'award',
            'children', 'young adult', 'dystopian', 'horror', 'fantasy',
            'science fiction', 'mystery', 'graphic', 'unfinished'
        ]
        
        name_lower = name.lower().strip()
        
        # Vérifications de base
        if len(name) < 3 or len(name) > 60:
            return False
            
        # Filtrage des mots-clés invalides
        if any(keyword in name_lower for keyword in invalid_keywords):
            return False
            
        # Doit contenir des lettres
        if not re.search(r'[a-zA-Z]', name):
            return False
            
        # Filtrage des fragments
        if name_lower.startswith(('a ', 'an ', 'the ', 'and ', 'her ', 'his ')):
            return False
            
        # Vérification séries connues (boost de confiance)
        if any(known.lower() in name_lower for known in self.known_series):
            return True
            
        # Doit ressembler à un titre
        if re.match(r'^[A-Z][a-zA-Z\s]+$', name):
            return True
            
        return False
    
    def is_duplicate_series(self, series_info: Dict) -> bool:
        """Vérifie les doublons"""
        for existing in self.series_detected:
            if (existing['name'].lower() == series_info['name'].lower() and 
                existing['author'] == series_info['author']):
                return True
        return False
    
    def get_fantasy_scifi_authors(self) -> List[str]:
        """Auteurs spécialisés fantasy/sci-fi avec séries connues"""
        return [
            "J.K. Rowling",          # Harry Potter
            "Stephen King",          # The Dark Tower
            "Terry Pratchett",       # Discworld
            "George R.R. Martin",    # A Song of Ice and Fire
            "Robert Jordan",         # Wheel of Time
            "Brandon Sanderson",     # Mistborn, Stormlight Archive
            "Jim Butcher",           # The Dresden Files
            "Rick Riordan",          # Percy Jackson
            "Suzanne Collins",       # The Hunger Games
            "Cassandra Clare",       # The Mortal Instruments
            "Frank Herbert",         # Dune
            "Isaac Asimov",          # Foundation
            "Ursula K. Le Guin",     # Earthsea
            "Douglas Adams",         # Hitchhiker's Guide
            "Neil Gaiman",           # Various series
            "Orson Scott Card",      # Ender's Game
            "Philip K. Dick",        # Various series
            "Arthur C. Clarke",      # Various series
            "Ray Bradbury",          # Various series
            "Agatha Christie",       # Poirot, Miss Marple
            "James S.A. Corey",      # The Expanse
            "Robin Hobb",            # Farseer Trilogy
            "Joe Abercrombie",       # The First Law
            "Patrick Rothfuss",      # The Kingkiller Chronicle
            "Scott Lynch",           # Gentleman Bastard
            "Mark Lawrence",         # The Broken Empire
            "N.K. Jemisin",          # The Broken Earth
            "Becky Chambers",        # Wayfarers
            "Martha Wells",          # The Murderbot Diaries
            "Jeff VanderMeer",       # Southern Reach
        ]
    
    async def enrich_series_for_author(self, author_name: str) -> List[Dict]:
        """Enrichit les séries pour un auteur donné"""
        logger.info(f"🚀 Enrichissement amélioré pour : {author_name}")
        
        # Récupération page Wikipedia
        wiki_page = await self.get_author_wikipedia_page(author_name)
        if not wiki_page:
            return []
        
        # Extraction des séries
        description = wiki_page.get('extract', '')
        if not description:
            logger.warning(f"❌ Pas de description pour : {author_name}")
            return []
        
        series_found = self.extract_series_with_improved_patterns(description, author_name)
        
        # Ajout à la liste globale
        self.series_detected.extend(series_found)
        self.authors_processed.append(author_name)
        
        logger.info(f"✅ {len(series_found)} séries validées pour {author_name}")
        return series_found
    
    async def process_all_authors(self, authors: List[str]) -> Dict:
        """Traite tous les auteurs en parallèle"""
        logger.info(f"🚀 Démarrage enrichissement amélioré pour {len(authors)} auteurs")
        
        # Traitement parallèle avec limitation
        semaphore = asyncio.Semaphore(3)  # Max 3 requêtes simultanées
        
        async def process_author_with_semaphore(author):
            async with semaphore:
                return await self.enrich_series_for_author(author)
        
        # Exécution parallèle
        results = await asyncio.gather(
            *[process_author_with_semaphore(author) for author in authors],
            return_exceptions=True
        )
        
        # Tri par confiance
        self.series_detected.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Statistiques finales
        total_series = len(self.series_detected)
        total_authors = len(self.authors_processed)
        high_confidence = len([s for s in self.series_detected if s['confidence'] >= 85])
        
        logger.info(f"🎯 ENRICHISSEMENT AMÉLIORÉ TERMINÉ :")
        logger.info(f"   📚 {total_series} séries détectées")
        logger.info(f"   🎯 {high_confidence} séries haute confiance (≥85%)")
        logger.info(f"   👤 {total_authors} auteurs traités")
        
        return {
            'total_series_detected': total_series,
            'high_confidence_series': high_confidence,
            'total_authors_processed': total_authors,
            'series_detected': self.series_detected,
            'authors_processed': self.authors_processed,
            'enrichment_completed_at': datetime.now().isoformat(),
            'version': '2.0'
        }
    
    def save_results(self, results: Dict, filename: str = "wikipedia_series_enrichment_v2.json"):
        """Sauvegarde les résultats"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Résultats sauvegardés : {filename}")
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde : {str(e)}")

async def main():
    """Fonction principale d'enrichissement amélioré"""
    logger.info("🚀 DÉMARRAGE WIKIPEDIA SERIES ENRICHER V2.0")
    
    async with WikipediaSeriesEnricherV2() as enricher:
        # Récupération des auteurs spécialisés
        authors = enricher.get_fantasy_scifi_authors()
        
        # Traitement de tous les auteurs
        results = await enricher.process_all_authors(authors)
        
        # Sauvegarde des résultats
        enricher.save_results(results)
        
        # Affichage résumé
        print("\n🎯 RÉSUMÉ ENRICHISSEMENT WIKIPÉDIA V2.0 :")
        print(f"📚 Séries détectées : {results['total_series_detected']}")
        print(f"🎯 Haute confiance : {results['high_confidence_series']} (≥85%)")
        print(f"👤 Auteurs traités : {results['total_authors_processed']}")
        print(f"📊 Taux succès : {results['total_authors_processed']}/{len(authors)} auteurs")
        
        # Affichage des séries haute confiance
        print("\n📚 SÉRIES HAUTE CONFIANCE DÉTECTÉES :")
        high_conf_series = [s for s in results['series_detected'] if s['confidence'] >= 85]
        for series in high_conf_series[:15]:  # Affiche les 15 premières
            print(f"   • {series['name']} - {series['author']} ({series['confidence']}%)")
        
        if len(high_conf_series) > 15:
            print(f"   ... et {len(high_conf_series) - 15} autres")

if __name__ == "__main__":
    asyncio.run(main())