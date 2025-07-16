from fastapi import APIRouter, Depends
from ..database.connection import books_collection
from ..security.jwt import get_current_user

router = APIRouter(prefix="/api/authors", tags=["authors"])

@router.get("")
async def get_authors(current_user: dict = Depends(get_current_user)):
    """Obtenir la liste des auteurs avec leurs livres"""
    user_filter = {"user_id": current_user["id"]}
    
    # Grouper les livres par auteur
    pipeline = [
        {"$match": user_filter},
        {"$group": {
            "_id": "$author",
            "total_books": {"$sum": 1},
            "completed_books": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}},
            "reading_books": {"$sum": {"$cond": [{"$eq": ["$status", "reading"]}, 1, 0]}},
            "to_read_books": {"$sum": {"$cond": [{"$eq": ["$status", "to_read"]}, 1, 0]}},
            "categories": {"$addToSet": "$category"},
            "last_read": {"$max": "$date_completed"}
        }},
        {"$sort": {"total_books": -1}}
    ]
    
    authors_data = list(books_collection.aggregate(pipeline))
    
    # Nettoyer les données
    authors = []
    for author_data in authors_data:
        if author_data["_id"]:  # Exclure les auteurs vides
            authors.append({
                "name": author_data["_id"],
                "total_books": author_data["total_books"],
                "completed_books": author_data["completed_books"],
                "reading_books": author_data["reading_books"],
                "to_read_books": author_data["to_read_books"],
                "categories": author_data["categories"],
                "last_read": author_data["last_read"]
            })
    
    return authors

@router.get("/{author_name}/books")
async def get_author_books(author_name: str, current_user: dict = Depends(get_current_user)):
    """Obtenir les livres d'un auteur spécifique depuis Wikipedia + OpenLibrary combinées"""
    
    try:
        # 1. Récupérer les informations Wikipedia pour les œuvres principales
        wikipedia_works = await get_wikipedia_author_works(author_name)
        
        # 2. Récupérer les œuvres OpenLibrary avec filtrage intelligent
        openlibrary_works = await get_openlibrary_author_works(author_name)
        
        # 3. Combiner et déduplicater les œuvres
        combined_works = combine_and_deduplicate_works(wikipedia_works, openlibrary_works)
        
        # 4. Organiser par séries et livres individuels
        organized_works = organize_author_works(combined_works)
        
        return {
            "author": author_name,
            "series": organized_works["series"],
            "individual_books": organized_works["individual_books"],
            "total_books": organized_works["total_books"],
            "total_series": organized_works["total_series"],
            "total_individual_books": organized_works["total_individual_books"],
            "sources": organized_works["sources"]
        }
        
    except Exception as e:
        # Fallback vers la méthode originale (bibliothèque utilisateur)
        return await get_author_books_from_library(author_name, current_user)


async def get_wikipedia_author_works(author_name: str):
    """Récupérer les œuvres principales depuis Wikipedia"""
    try:
        import httpx
        
        # Rechercher la page Wikipedia de l'auteur
        search_url = "https://en.wikipedia.org/w/api.php"
        search_params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": author_name,
            "srlimit": 1,
            "srprop": "snippet"
        }
        
        async with httpx.AsyncClient(timeout=10) as client:
            search_response = await client.get(search_url, params=search_params)
            search_data = search_response.json()
            
            if not search_data.get("query", {}).get("search"):
                return []
            
            # Récupérer le contenu de la page
            page_title = search_data["query"]["search"][0]["title"]
            content_params = {
                "action": "query",
                "format": "json",
                "prop": "extracts",
                "titles": page_title,
                "exintro": False,
                "explaintext": True,
                "exsectionformat": "plain"
            }
            
            content_response = await client.get(search_url, params=content_params)
            content_data = content_response.json()
            
            # Extraire les œuvres principales du contenu
            works = extract_works_from_wikipedia_content(content_data, author_name)
            
            return works
            
    except Exception as e:
        print(f"Erreur Wikipedia works: {e}")
        return []


async def get_openlibrary_author_works(author_name: str):
    """Récupérer les œuvres depuis OpenLibrary avec filtrage intelligent"""
    try:
        import requests
        
        # 1. Rechercher l'auteur
        search_url = f"https://openlibrary.org/search/authors.json"
        search_params = {"q": author_name, "limit": 1}
        
        response = requests.get(search_url, params=search_params, timeout=10)
        response.raise_for_status()
        search_data = response.json()
        
        if not search_data.get("docs"):
            return []
        
        # 2. Récupérer les œuvres de l'auteur
        author_data = search_data["docs"][0]
        author_key = author_data.get("key", "")
        
        if not author_key:
            return []
        
        # 3. Récupérer les œuvres avec filtrage
        works_url = f"https://openlibrary.org{author_key}/works.json"
        works_params = {"limit": 100}  # Limiter pour éviter surcharge
        
        works_response = requests.get(works_url, params=works_params, timeout=15)
        works_response.raise_for_status()
        works_data = works_response.json()
        
        # 4. Filtrer et nettoyer les œuvres
        filtered_works = filter_openlibrary_works(works_data.get("entries", []), author_name)
        
        return filtered_works
        
    except Exception as e:
        print(f"Erreur OpenLibrary works: {e}")
        return []


def extract_works_from_wikipedia_content(content_data, author_name):
    """Extraire les œuvres principales du contenu Wikipedia"""
    works = []
    
    try:
        pages = content_data.get("query", {}).get("pages", {})
        
        for page_id, page_data in pages.items():
            content = page_data.get("extract", "")
            
            # Patterns pour détecter les œuvres principales
            import re
            
            # Détecter les séries populaires
            series_patterns = [
                r'(Harry Potter)\s+(?:series|saga|books)',
                r'(Game of Thrones|A Song of Ice and Fire)',
                r'(Lord of the Rings|The Hobbit)',
                r'(Sherlock Holmes)',
                r'(Hercule Poirot)',
                r'(Chronicles of Narnia)',
                r'(Dune)\s+(?:series|saga)',
                r'(Foundation)\s+(?:series|saga)'
            ]
            
            for pattern in series_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    works.append({
                        "title": match,
                        "type": "series",
                        "source": "wikipedia",
                        "author": author_name,
                        "description": f"Série principale de {author_name}"
                    })
            
            # Détecter les livres individuels mentionnés
            book_patterns = [
                r'"([^"]+)"\s+\((?:19|20)\d{2}\)',  # Livres entre guillemets avec année
                r'(?:novel|book|work)\s+"([^"]+)"',   # "novel/book/work" suivi du titre
                r'(?:published|wrote|authored)\s+"([^"]+)"'  # Verbes de publication
            ]
            
            for pattern in book_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if len(match) > 3 and len(match) < 100:  # Filtrer les titres réalistes
                        works.append({
                            "title": match.strip(),
                            "type": "individual",
                            "source": "wikipedia",
                            "author": author_name,
                            "description": f"Œuvre de {author_name}"
                        })
            
        # Dédupliquer et limiter
        seen_titles = set()
        unique_works = []
        
        for work in works:
            title_lower = work["title"].lower()
            if title_lower not in seen_titles and len(unique_works) < 20:
                seen_titles.add(title_lower)
                unique_works.append(work)
        
        return unique_works
        
    except Exception as e:
        print(f"Erreur extraction Wikipedia: {e}")
        return []


def filter_openlibrary_works(works_entries, author_name):
    """Filtrer intelligemment les œuvres OpenLibrary"""
    filtered_works = []
    seen_titles = set()
    
    try:
        for work in works_entries:
            title = work.get("title", "")
            
            # Filtres de qualité
            if not title or len(title) < 3:
                continue
                
            # Ignorer les traductions évidentes
            if any(lang in title.lower() for lang in ["japanese", "français", "deutsch", "español", "italiano"]):
                continue
                
            # Ignorer les éditions spéciales
            if any(edition in title.lower() for edition in ["special edition", "deluxe", "anniversary", "collector"]):
                continue
                
            # Ignorer les doublons
            title_clean = title.lower().strip()
            if title_clean in seen_titles:
                continue
                
            seen_titles.add(title_clean)
            
            # Extraire l'année de publication
            first_publish_date = work.get("first_publish_date", "")
            year = None
            if first_publish_date:
                import re
                year_match = re.search(r'(\d{4})', first_publish_date)
                if year_match:
                    year = int(year_match.group(1))
            
            # Détecter si c'est une série ou un livre individuel
            work_type = "individual"
            if any(keyword in title.lower() for keyword in ["series", "saga", "volume", "book 1", "book 2", "tome"]):
                work_type = "series"
            
            filtered_works.append({
                "title": title,
                "type": work_type,
                "source": "openlibrary",
                "author": author_name,
                "year": year,
                "first_publish_date": first_publish_date,
                "key": work.get("key", ""),
                "description": work.get("description", "")
            })
            
            # Limiter à 30 œuvres maximum
            if len(filtered_works) >= 30:
                break
        
        return filtered_works
        
    except Exception as e:
        print(f"Erreur filtrage OpenLibrary: {e}")
        return []


def combine_and_deduplicate_works(wikipedia_works, openlibrary_works):
    """Combiner et déduplicater les œuvres des deux sources"""
    combined = []
    seen_titles = set()
    
    # Priorité à Wikipedia (meilleure qualité)
    for work in wikipedia_works:
        title_clean = work["title"].lower().strip()
        if title_clean not in seen_titles:
            seen_titles.add(title_clean)
            combined.append(work)
    
    # Compléter avec OpenLibrary
    for work in openlibrary_works:
        title_clean = work["title"].lower().strip()
        if title_clean not in seen_titles:
            seen_titles.add(title_clean)
            combined.append(work)
    
    return combined


def organize_author_works(works):
    """Organiser les œuvres par séries et livres individuels"""
    series_works = {}
    individual_works = []
    sources = {"wikipedia": 0, "openlibrary": 0}
    
    for work in works:
        # Compter les sources
        sources[work["source"]] += 1
        
        if work["type"] == "series":
            series_name = work["title"]
            if series_name not in series_works:
                series_works[series_name] = {
                    "name": series_name,
                    "type": "series",
                    "author": work["author"],
                    "source": work["source"],
                    "description": work.get("description", ""),
                    "books": []
                }
        else:
            individual_works.append({
                "title": work["title"],
                "type": "individual",
                "author": work["author"],
                "year": work.get("year"),
                "source": work["source"],
                "description": work.get("description", "")
            })
    
    # Trier par année
    individual_works.sort(key=lambda x: x.get("year", 9999))
    
    # Convertir series_works en liste
    series_list = list(series_works.values())
    
    return {
        "series": series_list,
        "individual_books": individual_works,
        "total_books": len(works),
        "total_series": len(series_list),
        "total_individual_books": len(individual_works),
        "sources": sources
    }


async def get_author_books_from_library(author_name: str, current_user: dict):
    """Méthode fallback : récupérer les livres depuis la bibliothèque utilisateur"""
    books = list(books_collection.find({
        "user_id": current_user["id"],
        "author": author_name
    }, {"_id": 0}))
    
    if not books:
        return {
            "author": author_name,
            "series": [],
            "individual_books": [],
            "total_books": 0,
            "total_series": 0,
            "total_individual_books": 0,
            "sources": {"library": 0},
            "fallback": True
        }
    
    # Organiser comme avant pour la bibliothèque
    series_books = {}
    individual_books = []
    
    for book in books:
        if book.get("saga") and book.get("saga").strip():
            saga_name = book["saga"]
            if saga_name not in series_books:
                series_books[saga_name] = []
            series_books[saga_name].append(book)
        else:
            individual_books.append(book)
    
    # Trier les livres de chaque série
    sorted_series = []
    for saga_name, saga_books in series_books.items():
        saga_books.sort(key=lambda x: (x.get("volume_number", 0), x.get("publication_year", 0)))
        
        total_volumes = len(saga_books)
        completed_volumes = sum(1 for book in saga_books if book.get("status") == "completed")
        reading_volumes = sum(1 for book in saga_books if book.get("status") == "reading")
        to_read_volumes = sum(1 for book in saga_books if book.get("status") == "to_read")
        
        sorted_series.append({
            "name": saga_name,
            "type": "series",
            "books": saga_books,
            "total_volumes": total_volumes,
            "completed_volumes": completed_volumes,
            "reading_volumes": reading_volumes,
            "to_read_volumes": to_read_volumes,
            "first_published": min((book.get("publication_year", 9999) for book in saga_books if book.get("publication_year")), default=None),
            "last_published": max((book.get("publication_year", 0) for book in saga_books if book.get("publication_year")), default=None)
        })
    
    sorted_series.sort(key=lambda x: x.get("first_published", 9999))
    individual_books.sort(key=lambda x: x.get("publication_year", 9999))
    
    organized_individual_books = []
    for book in individual_books:
        organized_individual_books.append({
            "type": "individual",
            "book": book
        })
    
    return {
        "author": author_name,
        "series": sorted_series,
        "individual_books": organized_individual_books,
        "total_books": len(books),
        "total_series": len(sorted_series),
        "total_individual_books": len(individual_books),
        "sources": {"library": len(books)},
        "fallback": True
    }