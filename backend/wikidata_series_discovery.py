#!/usr/bin/env python3
"""
Script pour découvrir de nouvelles séries via Wikidata
et créer le fichier wikidata_new_series_discovery.json
"""

import json
import asyncio
import aiohttp
from typing import Dict, List, Set
import logging
from pathlib import Path

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WikidataSeriesDiscovery:
    def __init__(self):
        self.existing_series: Set[str] = set()
        self.new_series: List[Dict] = []
        self.processed_authors: Set[str] = set()
        
    def load_existing_series(self) -> None:
        """Charger les 10,000 séries existantes"""
        try:
            with open('/app/backend/data/extended_series_database.json', 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                self.existing_series = set(series['name'].lower() for series in existing_data)
            logger.info(f"✅ Chargé {len(self.existing_series)} séries existantes")
        except Exception as e:
            logger.error(f"❌ Erreur chargement séries existantes: {e}")
            
    async def get_wikidata_series(self, session: aiohttp.ClientSession, author_name: str) -> List[Dict]:
        """Récupérer les séries d'un auteur depuis Wikidata"""
        try:
            url = f"http://localhost:8001/api/wikidata/author/{author_name}/series"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('found') and data.get('series'):
                        return data['series']
                return []
        except Exception as e:
            logger.error(f"❌ Erreur API Wikidata pour {author_name}: {e}")
            return []
            
    def extract_new_series(self, wikidata_series: List[Dict], author_name: str) -> List[Dict]:
        """Extraire les nouvelles séries non présentes dans les 10,000 existantes"""
        new_series = []
        
        for series in wikidata_series:
            series_name = series.get('name', '').strip()
            if not series_name:
                continue
                
            # Vérifier si la série existe déjà
            if series_name.lower() not in self.existing_series:
                new_series.append({
                    'name': series_name,
                    'author': author_name,
                    'wikidata_id': series.get('id', ''),
                    'genre': series.get('genre', ''),
                    'status': series.get('status', ''),
                    'description': series.get('description', ''),
                    'source': 'wikidata_discovery'
                })
                logger.info(f"🆕 Nouvelle série trouvée: {series_name} par {author_name}")
                
        return new_series
    
    async def get_sample_authors(self) -> List[str]:
        """Obtenir une liste d'auteurs à traiter"""
        # Pour commencer, utiliser les auteurs populaires
        return [
            "J.K. Rowling",
            "Stephen King", 
            "Agatha Christie",
            "Isaac Asimov",
            "Terry Pratchett",
            "George R.R. Martin",
            "Neil Gaiman",
            "Brandon Sanderson",
            "Robin Hobb",
            "Ursula K. Le Guin",
            "Ray Bradbury",
            "Philip K. Dick",
            "Arthur C. Clarke",
            "Frank Herbert",
            "Douglas Adams",
            "Tolkien",
            "Hemingway",
            "Orwell",
            "Dickens",
            "Shakespeare"
        ]
    
    async def discover_new_series(self) -> None:
        """Processus principal de découverte"""
        logger.info("🚀 Démarrage découverte séries Wikidata")
        
        # Charger les séries existantes
        self.load_existing_series()
        
        # Obtenir les auteurs à traiter
        authors = await self.get_sample_authors()
        
        # Traiter chaque auteur
        async with aiohttp.ClientSession() as session:
            for author_name in authors:
                if author_name in self.processed_authors:
                    continue
                    
                logger.info(f"🔍 Traitement auteur: {author_name}")
                
                # Récupérer les séries Wikidata
                wikidata_series = await self.get_wikidata_series(session, author_name)
                
                if wikidata_series:
                    # Extraire les nouvelles séries
                    new_series = self.extract_new_series(wikidata_series, author_name)
                    self.new_series.extend(new_series)
                    
                    logger.info(f"✅ {author_name}: {len(wikidata_series)} séries totales, {len(new_series)} nouvelles")
                else:
                    logger.info(f"⚠️ {author_name}: Aucune série trouvée")
                    
                self.processed_authors.add(author_name)
                
                # Pause entre les requêtes
                await asyncio.sleep(0.5)
    
    def save_results(self) -> None:
        """Sauvegarder les résultats dans wikidata_new_series_discovery.json"""
        try:
            output_file = '/app/backend/wikidata_new_series_discovery.json'
            
            # Préparer les données de sortie
            output_data = {
                'discovery_info': {
                    'total_existing_series': len(self.existing_series),
                    'total_new_series_found': len(self.new_series),
                    'processed_authors': list(self.processed_authors),
                    'discovery_date': '2025-01-17'
                },
                'new_series': self.new_series
            }
            
            # Sauvegarder
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"✅ Résultats sauvegardés dans {output_file}")
            logger.info(f"📊 Séries existantes: {len(self.existing_series)}")
            logger.info(f"📊 Nouvelles séries découvertes: {len(self.new_series)}")
            logger.info(f"📊 Auteurs traités: {len(self.processed_authors)}")
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde: {e}")

async def main():
    """Fonction principale"""
    discovery = WikidataSeriesDiscovery()
    await discovery.discover_new_series()
    discovery.save_results()

if __name__ == "__main__":
    asyncio.run(main())