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
        """Obtenir une liste d'auteurs à traiter - VERSION ÉTENDUE pour 1000 séries"""
        # Liste étendue d'auteurs pour récupérer 1000+ nouvelles séries
        authors_list = [
            # Auteurs déjà traités
            "J.K. Rowling", "Stephen King", "Agatha Christie", "Isaac Asimov", "Terry Pratchett",
            "George R.R. Martin", "Neil Gaiman", "Brandon Sanderson", "Robin Hobb", "Ursula K. Le Guin",
            "Ray Bradbury", "Philip K. Dick", "Arthur C. Clarke", "Frank Herbert", "Douglas Adams",
            "Tolkien", "Hemingway", "Orwell", "Dickens", "Shakespeare",
            
            # Science-Fiction & Fantasy
            "Robert A. Heinlein", "Orson Scott Card", "Dan Simmons", "Kim Stanley Robinson", 
            "Alastair Reynolds", "Peter Watts", "Jeff VanderMeer", "Ann Leckie", "Becky Chambers",
            "Martha Wells", "N.K. Jemisin", "Liu Cixin", "Stanisław Lem", "Ursula K. Le Guin",
            "Philip José Farmer", "Roger Zelazny", "Gene Wolfe", "Jack Vance", "Michael Moorcock",
            "Marion Zimmer Bradley", "Anne McCaffrey", "Poul Anderson", "Larry Niven", "Jerry Pournelle",
            "David Brin", "Gregory Benford", "Connie Willis", "Lois McMaster Bujold", "C.J. Cherryh",
            "Joe Haldeman", "Frederik Pohl", "Clifford D. Simak", "A.E. van Vogt", "E.E. Smith",
            "Robert Silverberg", "Harlan Ellison", "Alfred Bester", "Theodore Sturgeon", "Cordwainer Smith",
            
            # Fantasy
            "Robert Jordan", "Terry Brooks", "R.A. Salvatore", "Mercedes Lackey", "Tad Williams",
            "Raymond E. Feist", "David Eddings", "Terry Goodkind", "Jim Butcher", "Patricia Briggs",
            "Laurell K. Hamilton", "Charlaine Harris", "Kim Harrison", "Kelley Armstrong", "Seanan McGuire",
            "Ben Aaronovitch", "China Miéville", "Joe Abercrombie", "Mark Lawrence", "Robin Hobb",
            "Tad Williams", "Guy Gavriel Kay", "Steven Erikson", "Glen Cook", "Michael J. Sullivan",
            "Brent Weeks", "Peter V. Brett", "Patrick Rothfuss", "Scott Lynch", "Joe Abercrombie",
            
            # Littérature policière/Thriller
            "John le Carré", "Ian Fleming", "Raymond Chandler", "Dashiell Hammett", "Mickey Spillane",
            "Robert B. Parker", "Sue Grafton", "Sara Paretsky", "Janet Evanovich", "Patricia Cornwell",
            "Kathy Reichs", "Tess Gerritsen", "Michael Connelly", "James Patterson", "John Grisham",
            "Tom Clancy", "Robert Ludlum", "Frederick Forsyth", "Ken Follett", "Dan Brown",
            "Stieg Larsson", "Henning Mankell", "Jussi Adler-Olsen", "Jo Nesbø", "Camilla Läckberg",
            "Tana French", "Louise Penny", "Elizabeth George", "P.D. James", "Ruth Rendell",
            
            # Littérature générale
            "Margaret Atwood", "Donna Tartt", "Toni Morrison", "Alice Munro", "Joyce Carol Oates",
            "John Updike", "Philip Roth", "Saul Bellow", "Norman Mailer", "Don DeLillo",
            "Thomas Pynchon", "Kurt Vonnegut", "Joseph Heller", "Jack Kerouac", "Hunter S. Thompson",
            "Tom Wolfe", "Truman Capote", "Harper Lee", "Flannery O'Connor", "Raymond Carver",
            "Tobias Wolff", "Alice Walker", "Maya Angelou", "Zora Neale Hurston", "Langston Hughes",
            
            # Auteurs français
            "Michel Houellebecq", "Amélie Nothomb", "Frédéric Beigbeder", "Guillaume Musso", 
            "Marc Levy", "Anna Gavalda", "Delphine de Vigan", "Leïla Slimani", "Virginie Despentes",
            "Philippe Claudel", "Yasmina Khadra", "Jean-Christophe Grangé", "Maxime Chattam",
            "Franck Thilliez", "Pierre Lemaitre", "Fred Vargas", "Alain Damasio", "Maurice Druon",
            "Bernard Werber", "Serge Brussolo", "Jean-Philippe Jaworski", "Pierre Bordage",
            "Ayerdhal", "Roland C. Wagner", "Laurent Genefort", "Fabrice Colin", "Mathieu Gaborit",
            
            # Manga/Light Novel
            "Akira Toriyama", "Masashi Kishimoto", "Tite Kubo", "Hajime Isayama", "Kentaro Miura",
            "Naoki Urasawa", "Hiromu Arakawa", "Yoshihiro Togashi", "Rumiko Takahashi", "Katsuhiro Otomo",
            "Masamune Shirow", "Osamu Tezuka", "Go Nagai", "Leiji Matsumoto", "Monkey D. Luffy",
            "Reki Kawahara", "Tappei Nagatsuki", "Kugane Maruyama", "Yuu Kamiya", "Rifujin na Magonote",
            
            # Auteurs BD
            "René Goscinny", "Albert Uderzo", "Hergé", "Morris", "André Franquin", "Peyo",
            "Jean Van Hamme", "Philippe Francq", "Jean Giraud", "Alejandro Jodorowsky",
            "Enki Bilal", "François Schuiten", "Benoît Peeters", "Lewis Trondheim", "Joann Sfar",
            "Marjane Satrapi", "Art Spiegelman", "Alan Moore", "Frank Miller", "Neil Gaiman",
            "Grant Morrison", "Warren Ellis", "Garth Ennis", "Brian K. Vaughan", "Robert Kirkman",
            
            # Auteurs historiques
            "Victor Hugo", "Honoré de Balzac", "Émile Zola", "Marcel Proust", "Albert Camus",
            "Jean-Paul Sartre", "Simone de Beauvoir", "André Malraux", "Louis-Ferdinand Céline",
            "Marguerite Duras", "Marguerite Yourcenar", "Colette", "George Sand", "Stendhal",
            "Gustave Flaubert", "Guy de Maupassant", "Alexandre Dumas", "Jules Verne", "Anatole France",
            
            # Auteurs internationaux
            "Gabriel García Márquez", "Jorge Luis Borges", "Octavio Paz", "Mario Vargas Llosa",
            "Isabel Allende", "Julio Cortázar", "Carlos Fuentes", "Roberto Bolaño", "Haruki Murakami",
            "Banana Yoshimoto", "Kenzaburō Ōe", "Yukio Mishima", "Kawabata Yasunari", "Italo Calvino",
            "Umberto Eco", "Elena Ferrante", "Roberto Saviano", "Salman Rushdie", "Arundhati Roy",
            "Vikram Seth", "Rohinton Mistry", "Chinua Achebe", "Wole Soyinka", "Nadine Gordimer",
            "J.M. Coetzee", "Doris Lessing", "V.S. Naipaul", "Zadie Smith", "Kazuo Ishiguro",
            "Ian McEwan", "Martin Amis", "Hilary Mantel", "Jeanette Winterson", "A.S. Byatt"
        ]
        
        # Supprimer les doublons et mélanger
        unique_authors = list(set(authors_list))
        logger.info(f"📊 {len(unique_authors)} auteurs uniques à traiter pour 1000+ séries")
        return unique_authors
    
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
                    
                    logger.info(f"✅ {author_name}: {len(wikidata_series)} séries totales, {len(new_series)} nouvelles - Total découvert: {len(self.new_series)}")
                else:
                    logger.info(f"⚠️ {author_name}: Aucune série trouvée")
                    
                self.processed_authors.add(author_name)
                
                # Pause entre les requêtes (réduite pour traiter plus d'auteurs)
                await asyncio.sleep(0.2)
    
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