from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import Optional
import uuid
import requests
from ..database.connection import books_collection
from ..security.jwt import get_current_user
from ..utils.validation import validate_category

router = APIRouter(prefix="/api/openlibrary", tags=["openlibrary"])

def detect_category_from_subjects(subjects):
    """Détecter la catégorie d'un livre à partir de ses sujets"""
    if not subjects:
        return "roman"
    
    subjects_str = " ".join(subjects).lower()
    
    # Détection manga
    manga_keywords = ["manga", "japanese comics", "graphic novel", "anime", "manhwa", "manhua"]
    if any(keyword in subjects_str for keyword in manga_keywords):
        return "manga"
    
    # Détection BD
    bd_keywords = ["comic", "bande dessinée", "graphic novel", "comic book", "illustration"]
    if any(keyword in subjects_str for keyword in bd_keywords):
        return "bd"
    
    # Par défaut: roman
    return "roman"

def extract_cover_url(cover_i):
    """Extraire l'URL de couverture depuis l'ID de couverture"""
    if cover_i:
        return f"https://covers.openlibrary.org/b/id/{cover_i}-M.jpg"
    return ""

@router.get("/search")
async def search_open_library(
    q: str,
    limit: int = 10,
    year_start: Optional[int] = None,
    year_end: Optional[int] = None,
    language: Optional[str] = None,
    min_pages: Optional[int] = None,
    max_pages: Optional[int] = None,
    author_filter: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Rechercher des livres dans Open Library"""
    try:
        params = {
            "q": q,
            "limit": limit,
            "fields": "key,title,author_name,first_publish_year,isbn,cover_i,subject,number_of_pages_median,publisher,language"
        }
        
        # Construire la requête avec filtres
        query_parts = [q]
        
        if year_start and year_end:
            query_parts.append(f"first_publish_year:[{year_start} TO {year_end}]")
        elif year_start:
            query_parts.append(f"first_publish_year:[{year_start} TO *]")
        elif year_end:
            query_parts.append(f"first_publish_year:[* TO {year_end}]")
        
        if language:
            query_parts.append(f"language:{language}")
        
        if author_filter:
            query_parts.append(f"author:{author_filter}")
        
        params["q"] = " AND ".join(query_parts)
        
        response = requests.get("https://openlibrary.org/search.json", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        books = []
        for doc in data.get("docs", []):
            # Appliquer filtres de pages
            if min_pages and doc.get("number_of_pages_median", 0) < min_pages:
                continue
            if max_pages and doc.get("number_of_pages_median", float('inf')) > max_pages:
                continue
            
            book = {
                "ol_key": doc.get("key", ""),
                "title": doc.get("title", ""),
                "author": ", ".join(doc.get("author_name", [])) if doc.get("author_name") else "",
                "category": detect_category_from_subjects(doc.get("subject", [])),
                "cover_url": extract_cover_url(doc.get("cover_i")),
                "first_publish_year": doc.get("first_publish_year"),
                "isbn": doc.get("isbn", [""])[0] if doc.get("isbn") else "",
                "subjects": doc.get("subject", [])[:5],  # Premiers 5 sujets
                "number_of_pages": doc.get("number_of_pages_median"),
                "publisher": ", ".join(doc.get("publisher", [])) if doc.get("publisher") else ""
            }
            books.append(book)
        
        return {
            "books": books[:limit],
            "total_found": data.get("numFound", 0),
            "filters_applied": {
                "year_range": f"{year_start}-{year_end}" if year_start or year_end else None,
                "language": language,
                "pages_range": f"{min_pages}-{max_pages}" if min_pages or max_pages else None,
                "author": author_filter
            }
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la recherche: {str(e)}")

@router.post("/import")
async def import_from_open_library(
    import_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Importer un livre depuis Open Library"""
    ol_key = import_data.get("ol_key")
    category = import_data.get("category", "roman")
    
    # Valider la catégorie
    validated_category = validate_category(category)
    if not ol_key:
        raise HTTPException(status_code=400, detail="Clé Open Library ou données série requises")
    
    try:
        # Récupérer les détails du livre
        work_url = f"https://openlibrary.org{ol_key}.json"
        response = requests.get(work_url, timeout=10)
        response.raise_for_status()
        work_data = response.json()
        
        # Récupérer les éditions pour plus de détails
        editions_url = f"https://openlibrary.org{ol_key}/editions.json"
        editions_response = requests.get(editions_url, timeout=10)
        editions_data = editions_response.json() if editions_response.status_code == 200 else {"entries": []}
        
        # Extraire les informations principales
        title = work_data.get("title", "")
        authors = []
        if work_data.get("authors"):
            for author_ref in work_data["authors"]:
                author_key = author_ref.get("author", {}).get("key", "")
                if author_key:
                    author_response = requests.get(f"https://openlibrary.org{author_key}.json", timeout=5)
                    if author_response.status_code == 200:
                        author_data = author_response.json()
                        authors.append(author_data.get("name", ""))
        
        author_str = ", ".join(authors) if authors else ""
        
        # Extraire description
        description = ""
        if work_data.get("description"):
            if isinstance(work_data["description"], dict):
                description = work_data["description"].get("value", "")
            else:
                description = work_data["description"]
        
        # Extraire sujets
        subjects = work_data.get("subjects", [])
        
        # Récupérer des détails depuis la première édition
        first_edition = editions_data.get("entries", [{}])[0]
        
        # Créer le livre
        book_id = str(uuid.uuid4())
        book = {
            "id": book_id,
            "user_id": current_user["id"],
            "title": title,
            "author": author_str,
            "category": validated_category,
            "description": description,
            "genre": ", ".join(subjects[:3]) if subjects else "",
            "total_pages": first_edition.get("number_of_pages"),
            "publication_year": first_edition.get("publish_date"),
            "publisher": ", ".join(first_edition.get("publishers", [])) if first_edition.get("publishers") else "",
            "isbn": first_edition.get("isbn_13", [""])[0] if first_edition.get("isbn_13") else "",
            "cover_url": import_data.get("cover_url", "") or extract_cover_url(first_edition.get("covers", [None])[0]),
            "status": "to_read",
            "current_page": None,
            "rating": None,
            "review": "",
            "saga": "",
            "volume_number": None,
            "auto_added": False,
            "date_added": datetime.utcnow(),
            "date_started": None,
            "date_completed": None,
            "updated_at": datetime.utcnow()
        }
        
        books_collection.insert_one(book)
        book.pop("_id", None)
        
        return {
            "success": True,
            "message": "Livre importé avec succès",
            "book": book,
            "type": "book"
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'import: {str(e)}")

@router.get("/search-advanced")
async def search_open_library_advanced(
    q: str,
    category: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    sort: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Recherche avancée dans Open Library"""
    try:
        params = {
            "q": q,
            "limit": limit,
            "offset": offset,
            "fields": "key,title,author_name,first_publish_year,isbn,cover_i,subject,number_of_pages_median,publisher,language"
        }
        
        if sort:
            params["sort"] = sort
        
        response = requests.get("https://openlibrary.org/search.json", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        books = []
        for doc in data.get("docs", []):
            detected_category = detect_category_from_subjects(doc.get("subject", []))
            
            # Filtrer par catégorie si spécifiée
            if category and detected_category != category:
                continue
            
            book = {
                "ol_key": doc.get("key", ""),
                "title": doc.get("title", ""),
                "author": ", ".join(doc.get("author_name", [])) if doc.get("author_name") else "",
                "category": detected_category,
                "cover_url": extract_cover_url(doc.get("cover_i")),
                "first_publish_year": doc.get("first_publish_year"),
                "isbn": doc.get("isbn", [""])[0] if doc.get("isbn") else "",
                "subjects": doc.get("subject", [])[:5],
                "number_of_pages": doc.get("number_of_pages_median"),
                "publisher": ", ".join(doc.get("publisher", [])) if doc.get("publisher") else ""
            }
            books.append(book)
        
        return {
            "books": books,
            "total_found": data.get("numFound", 0),
            "offset": offset,
            "limit": limit,
            "has_more": offset + limit < data.get("numFound", 0)
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la recherche: {str(e)}")

@router.get("/search-isbn")
async def search_by_isbn(
    isbn: str,
    current_user: dict = Depends(get_current_user)
):
    """Rechercher un livre par ISBN"""
    try:
        response = requests.get(f"https://openlibrary.org/isbn/{isbn}.json", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Récupérer les détails du work
        work_key = data.get("works", [{}])[0].get("key", "")
        if work_key:
            work_response = requests.get(f"https://openlibrary.org{work_key}.json", timeout=10)
            work_data = work_response.json() if work_response.status_code == 200 else {}
        else:
            work_data = {}
        
        book = {
            "ol_key": work_key,
            "title": work_data.get("title", data.get("title", "")),
            "author": ", ".join([author.get("name", "") for author in data.get("authors", [])]),
            "category": detect_category_from_subjects(work_data.get("subjects", [])),
            "cover_url": extract_cover_url(data.get("covers", [None])[0]),
            "first_publish_year": data.get("publish_date"),
            "isbn": isbn,
            "subjects": work_data.get("subjects", [])[:5],
            "number_of_pages": data.get("number_of_pages"),
            "publisher": ", ".join(data.get("publishers", []))
        }
        
        return {"book": book}
        
    except requests.RequestException as e:
        raise HTTPException(status_code=404, detail=f"Livre non trouvé pour l'ISBN {isbn}")

@router.get("/search-author")
async def search_by_author(
    author: str,
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Rechercher des livres par auteur"""
    try:
        params = {
            "author": author,
            "limit": limit,
            "fields": "key,title,author_name,first_publish_year,isbn,cover_i,subject,number_of_pages_median,publisher"
        }
        
        response = requests.get("https://openlibrary.org/search.json", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        books = []
        for doc in data.get("docs", []):
            book = {
                "ol_key": doc.get("key", ""),
                "title": doc.get("title", ""),
                "author": ", ".join(doc.get("author_name", [])) if doc.get("author_name") else "",
                "category": detect_category_from_subjects(doc.get("subject", [])),
                "cover_url": extract_cover_url(doc.get("cover_i")),
                "first_publish_year": doc.get("first_publish_year"),
                "isbn": doc.get("isbn", [""])[0] if doc.get("isbn") else "",
                "subjects": doc.get("subject", [])[:5],
                "number_of_pages": doc.get("number_of_pages_median"),
                "publisher": ", ".join(doc.get("publisher", [])) if doc.get("publisher") else ""
            }
            books.append(book)
        
        return {
            "books": books,
            "total_found": data.get("numFound", 0),
            "author": author
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la recherche: {str(e)}")

@router.get("/author/{author_name}")
async def get_author_info(
    author_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupérer les informations d'un auteur depuis Open Library"""
    try:
        # Rechercher l'auteur dans Open Library
        search_url = f"https://openlibrary.org/search/authors.json"
        search_params = {"q": author_name, "limit": 1}
        
        response = requests.get(search_url, params=search_params, timeout=10)
        response.raise_for_status()
        search_data = response.json()
        
        if not search_data.get("docs"):
            return {"found": False, "message": "Auteur non trouvé"}
        
        # Récupérer les détails de l'auteur
        author_data = search_data["docs"][0]
        author_key = author_data.get("key", "")
        
        if author_key:
            # Récupérer les informations détaillées de l'auteur
            author_url = f"https://openlibrary.org{author_key}.json"
            author_response = requests.get(author_url, timeout=10)
            
            if author_response.status_code == 200:
                author_details = author_response.json()
                
                # Extraire la biographie
                bio = ""
                if author_details.get("bio"):
                    if isinstance(author_details["bio"], dict):
                        bio = author_details["bio"].get("value", "")
                    else:
                        bio = author_details["bio"]
                
                # Limiter la biographie à 300 caractères pour affichage
                if len(bio) > 300:
                    bio = bio[:300] + "..."
                
                # URL de la photo
                photo_url = ""
                if author_details.get("photos"):
                    photo_id = author_details["photos"][0]
                    photo_url = f"https://covers.openlibrary.org/a/id/{photo_id}-M.jpg"
                
                return {
                    "found": True,
                    "author": {
                        "name": author_details.get("name", author_name),
                        "bio": bio,
                        "photo_url": photo_url,
                        "birth_date": author_details.get("birth_date", ""),
                        "death_date": author_details.get("death_date", ""),
                        "alternate_names": author_details.get("alternate_names", []),
                        "work_count": author_data.get("work_count", 0),
                        "top_work": author_data.get("top_work", ""),
                        "ol_key": author_key
                    }
                }
        
        return {"found": False, "message": "Détails de l'auteur non disponibles"}
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des informations de l'auteur: {str(e)}")

@router.get("/recommendations")
async def get_recommendations(
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """Obtenir des recommandations basées sur la bibliothèque de l'utilisateur"""
    # Analyser les genres et auteurs préférés de l'utilisateur
    user_books = list(books_collection.find(
        {"user_id": current_user["id"], "status": "completed"},
        {"genre": 1, "author": 1, "category": 1}
    ))
    
    if not user_books:
        # Recommandations générales si pas de livres
        return await search_open_library("bestseller", limit=limit, current_user=current_user)
    
    # Extraire les genres et auteurs populaires
    genres = []
    authors = []
    categories = []
    
    for book in user_books:
        if book.get("genre"):
            genres.extend(book["genre"].split(", "))
        if book.get("author"):
            authors.append(book["author"])
        if book.get("category"):
            categories.append(book["category"])
    
    # Prendre les plus populaires
    popular_genre = max(set(genres), key=genres.count) if genres else "fiction"
    popular_category = max(set(categories), key=categories.count) if categories else "roman"
    
    # Rechercher des recommandations
    search_result = await search_open_library(
        popular_genre,
        limit=limit,
        current_user=current_user
    )
    
    return {
        "recommendations": search_result["books"],
        "based_on": {
            "genre": popular_genre,
            "category": popular_category,
            "user_books_count": len(user_books)
        }
    }