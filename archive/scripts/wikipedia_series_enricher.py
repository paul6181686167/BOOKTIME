#!/usr/bin/env python3
"""
🚀 WIKIPEDIA SERIES ENRICHER - Enrichissement Automatique Ultra Harvest
Expansion automatique des séries basée sur les auteurs existants via Wikipedia
"""

import asyncio
import aiohttp
import re
import json
from datetime import datetime
from typing import List, Dict, Optional
import logging

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WikipediaSeriesEnricher:
    """Enrichisseur automatique de séries via Wikipedia"""
    
    def __init__(self):
        self.session = None
        self.base_url = "https://en.wikipedia.org/api/rest_v1/page/summary/"
        self.series_detected = []
        self.authors_processed = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_author_wikipedia_page(self, author_name: str) -> Optional[Dict]:
        """Récupère la page Wikipedia d'un auteur"""
        try:
            # Formatage nom pour URL Wikipedia
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
    
    def extract_series_from_description(self, description: str, author_name: str) -> List[Dict]:
        """Extrait les séries depuis la description Wikipedia"""
        series_found = []
        
        # Patterns pour détecter les séries
        series_patterns = [
            r'(?:creator|author|writer) of (?:the )?([A-Z][^,\.]+?) (?:series|saga)',
            r'(?:wrote|created) (?:the )?([A-Z][^,\.]+?) (?:series|novels)',
            r'best known for (?:the )?([A-Z][^,\.]+?) (?:series|saga)',
            r'(?:famous|known) for (?:the )?([A-Z][^,\.]+?) (?:series|novels)',
            r'([A-Z][^,\.]+?) (?:book series|novel series)',
            r'(?:the )?([A-Z][^,\.]+?) (?:fantasy|science fiction|mystery) series'
        ]
        
        logger.info(f"🔍 Analyse description pour : {author_name}")
        
        for pattern in series_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                series_name = match.strip()
                
                # Filtrage des faux positifs
                if self.is_valid_series_name(series_name):
                    series_info = {
                        'name': series_name,
                        'author': author_name,
                        'source': 'wikipedia_description',
                        'detected_at': datetime.now().isoformat(),
                        'confidence': 85
                    }
                    series_found.append(series_info)
                    logger.info(f"📚 Série détectée : {series_name} par {author_name}")
        
        return series_found
    
    def is_valid_series_name(self, name: str) -> bool:
        """Valide si le nom est une vraie série"""
        # Filtres pour éviter les faux positifs
        invalid_keywords = [
            'literature', 'fiction', 'books', 'novels', 'works', 'writing',
            'style', 'genre', 'career', 'life', 'biography', 'awards',
            'university', 'college', 'school', 'education', 'degree'
        ]
        
        name_lower = name.lower()
        
        # Vérifications
        if len(name) < 3 or len(name) > 50:
            return False
            
        if any(keyword in name_lower for keyword in invalid_keywords):
            return False
            
        # Doit contenir des lettres
        if not re.search(r'[a-zA-Z]', name):
            return False
            
        return True
    
    def get_sample_authors(self) -> List[str]:
        """Auteurs d'exemple pour tester le système"""
        return [
            "J.K. Rowling",
            "Stephen King", 
            "Agatha Christie",
            "Isaac Asimov",
            "Terry Pratchett",
            "George R.R. Martin",
            "Brandon Sanderson",
            "Robert Jordan",
            "Jim Butcher",
            "Rick Riordan",
            "Suzanne Collins",
            "Cassandra Clare",
            "Neil Gaiman",
            "Douglas Adams",
            "Orson Scott Card",
            "Frank Herbert",
            "Ursula K. Le Guin",
            "Philip K. Dick",
            "Arthur C. Clarke",
            "Ray Bradbury"
        ]
    
    async def enrich_series_for_author(self, author_name: str) -> List[Dict]:
        """Enrichit les séries pour un auteur donné"""
        logger.info(f"🚀 Enrichissement pour : {author_name}")
        
        # Récupération page Wikipedia
        wiki_page = await self.get_author_wikipedia_page(author_name)
        if not wiki_page:
            return []
        
        # Extraction des séries
        description = wiki_page.get('extract', '')
        if not description:
            logger.warning(f"❌ Pas de description pour : {author_name}")
            return []
        
        series_found = self.extract_series_from_description(description, author_name)
        
        # Ajout à la liste globale
        self.series_detected.extend(series_found)
        self.authors_processed.append(author_name)
        
        logger.info(f"✅ {len(series_found)} séries trouvées pour {author_name}")
        return series_found
    
    async def process_all_authors(self, authors: List[str]) -> Dict:
        """Traite tous les auteurs en parallèle"""
        logger.info(f"🚀 Démarrage enrichissement pour {len(authors)} auteurs")
        
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
        
        # Statistiques finales
        total_series = len(self.series_detected)
        total_authors = len(self.authors_processed)
        
        logger.info(f"🎯 ENRICHISSEMENT TERMINÉ :")
        logger.info(f"   📚 {total_series} séries détectées")
        logger.info(f"   👤 {total_authors} auteurs traités")
        
        return {
            'total_series_detected': total_series,
            'total_authors_processed': total_authors,
            'series_detected': self.series_detected,
            'authors_processed': self.authors_processed,
            'enrichment_completed_at': datetime.now().isoformat()
        }
    
    def save_results(self, results: Dict, filename: str = "wikipedia_series_enrichment.json"):
        """Sauvegarde les résultats"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 Résultats sauvegardés : {filename}")
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde : {str(e)}")

async def main():
    """Fonction principale d'enrichissement"""
    logger.info("🚀 DÉMARRAGE WIKIPEDIA SERIES ENRICHER")
    
    async with WikipediaSeriesEnricher() as enricher:
        # Récupération des auteurs d'exemple
        authors = enricher.get_sample_authors()
        
        # Traitement de tous les auteurs
        results = await enricher.process_all_authors(authors)
        
        # Sauvegarde des résultats
        enricher.save_results(results)
        
        # Affichage résumé
        print("\n🎯 RÉSUMÉ ENRICHISSEMENT WIKIPÉDIA :")
        print(f"📚 Séries détectées : {results['total_series_detected']}")
        print(f"👤 Auteurs traités : {results['total_authors_processed']}")
        print(f"📊 Taux succès : {results['total_authors_processed']}/{len(authors)} auteurs")
        
        # Affichage des séries trouvées
        print("\n📚 SÉRIES DÉTECTÉES :")
        for series in results['series_detected'][:10]:  # Affiche les 10 premières
            print(f"   • {series['name']} - {series['author']}")
        
        if len(results['series_detected']) > 10:
            print(f"   ... et {len(results['series_detected']) - 10} autres")

if __name__ == "__main__":
    asyncio.run(main())