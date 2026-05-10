from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import Optional
import uuid
import re as _re_global
import unicodedata
import requests
from ..database.connection import books_collection
from ..security.jwt import get_current_user
from ..utils.validation import validate_category

def _normalize_query(s: str) -> str:
    """Supprime accents et ponctuation pour une recherche élargie"""
    no_accent = unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode('utf-8')
    return no_accent.strip()

router = APIRouter(prefix="/api/openlibrary", tags=["openlibrary"])

def detect_category_from_subjects(subjects):
    """Détecter la catégorie d'un livre à partir de ses sujets"""
    if not subjects:
        return "roman"
    
    subjects_str = " ".join(subjects).lower()
    
    # Détection manga - uniquement mots-clés très spécifiques aux mangas
    manga_keywords = ["manga", "japanese comics", "manhwa", "manhua", "anime"]
    if any(keyword in subjects_str for keyword in manga_keywords):
        return "manga"
    
    # Détection BD - mots-clés spécifiques aux bandes dessinées
    # Note: "illustration" retiré car trop générique (livres illustrés comme The Hobbit)
    # Note: "graphic novel" retiré des manga_keywords (c'est une BD, pas un manga)
    bd_keywords = ["comic book", "comic strip", "bande dessinee", "bande dessinée", "fumetti", "comics"]
    if any(keyword in subjects_str for keyword in bd_keywords):
        return "bd"
    
    # "graphic novel" seul = BD (mais seulement si c'est clairement le genre principal)
    if "graphic novel" in subjects_str and "fiction" not in subjects_str and "fantasy" not in subjects_str:
        return "bd"
    
    # Par défaut: roman
    return "roman"

def extract_cover_url(cover_i):
    """Extraire l'URL de couverture depuis l'ID de couverture"""
    if cover_i:
        return f"https://covers.openlibrary.org/b/id/{cover_i}-M.jpg"
    return ""

def _build_ol_params(q_term: str, limit: int, year_start, year_end, language, author_filter) -> dict:
    """Construit les paramètres d'une requête Open Library"""
    query_parts = [q_term]
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
    return {
        "q": " AND ".join(query_parts),
        "limit": limit,
        "fields": "key,title,author_name,first_publish_year,isbn,cover_i,subject,number_of_pages_median,publisher,language,series"
    }

def _doc_to_book(doc: dict) -> dict:
    """Convertit un document OL en objet livre normalisé"""
    raw_series = doc.get("series", [])
    series_name = ""
    if raw_series:
        s = raw_series[0] if isinstance(raw_series, list) else raw_series
        vol_match = _re_global.search(r'\s*[#,]\s*\d+', s)
        series_name = s[:vol_match.start()].strip() if vol_match else s.strip()

    ol_title = doc.get("title", "")

    # Détecter si le titre semble être dans une langue non-latine (japonais, coréen, etc.)
    # ou si c'est clairement anglais → on le stocke comme original_title
    langs = doc.get("language", [])
    is_original_english = "eng" in langs if langs else False

    return {
        "ol_key": doc.get("key", ""),
        "title": ol_title,
        "original_title": ol_title,  # conservé tel quel ; sera écrasé si on trouve la trad FR
        "author": ", ".join(doc.get("author_name", [])) if doc.get("author_name") else "",
        "category": detect_category_from_subjects(doc.get("subject", [])),
        "cover_url": extract_cover_url(doc.get("cover_i")),
        "first_publish_year": doc.get("first_publish_year"),
        "isbn": doc.get("isbn", [""])[0] if doc.get("isbn") else "",
        "subjects": doc.get("subject", [])[:5],
        "number_of_pages": doc.get("number_of_pages_median"),
        "publisher": ", ".join(doc.get("publisher", [])) if doc.get("publisher") else "",
        "saga": series_name,
        "available_languages": langs[:5] if langs else [],
    }


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
    """
    Rechercher des livres dans Open Library.
    Stratégie large : requête originale + version sans accents, fusionnées et dédupliquées.
    Retourne original_title pour que le front puisse l'afficher en sous-titre.
    """
    try:
        import concurrent.futures
        OL_URL = "https://openlibrary.org/search.json"
        fetch_limit = min(limit + 10, 50)  # marge légère sans surcharger

        # ── Requêtes parallèles : terme original + version sans accents ───────
        q_norm = _normalize_query(q)
        queries = [q]
        if q_norm.lower() != q.lower():
            queries.append(q_norm)

        def _fetch(q_term):
            params = _build_ol_params(q_term, fetch_limit, year_start, year_end, language, author_filter)
            r = requests.get(OL_URL, params=params, timeout=8)
            return r.json() if r.ok else {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(_fetch, qt) for qt in queries]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # ── Fusion et dédoublonnage par ol_key ──────────────────────────────
        seen_keys = set()
        merged_docs = []
        for data in results:
            for doc in data.get("docs", []):
                key = doc.get("key", "")
                if not key or key in seen_keys:
                    continue
                seen_keys.add(key)
                merged_docs.append(doc)

        total_found = max((r.get("numFound", 0) for r in results), default=0)

        # ── Filtrage pages + construction objets livres ──────────────────────
        books = []
        for doc in merged_docs:
            if min_pages and doc.get("number_of_pages_median", 0) < min_pages:
                continue
            if max_pages and doc.get("number_of_pages_median", float('inf')) > max_pages:
                continue
            books.append(_doc_to_book(doc))

        return {
            "books": books[:limit],
            "total_found": total_found,
            "filters_applied": {
                "year_range": f"{year_start}-{year_end}" if year_start or year_end else None,
                "language": language,
                "pages_range": f"{min_pages}-{max_pages}" if min_pages or max_pages else None,
                "author": author_filter
            }
        }

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la recherche: {str(e)}")


@router.get("/series-books")
async def get_series_books(
    name: str,
    author: Optional[str] = None,
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Récupère tous les volumes d'une série depuis Open Library."""
    import re as _re

    def normalize(s):
        return _re.sub(r'\s+', ' ', (s or '').lower().strip())

    name_norm = normalize(name)
    # Mots significatifs du nom de série (longueur ≥ 3)
    name_words = [w for w in name_norm.split() if len(w) >= 3]

    try:
        # Requête 1 : chercher le nom exact de la série
        query = f'"{name}"'
        if author:
            query += f' author:"{author}"'

        params = {
            "q": query,
            "limit": limit,
            "fields": "key,title,author_name,first_publish_year,isbn,cover_i,subject,number_of_pages_median,series"
        }
        resp = requests.get("https://openlibrary.org/search.json", params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        docs = data.get("docs", [])

        # Requête 2 (fallback) : si peu de résultats, chercher sans guillemets
        if len(docs) < 3:
            params2 = dict(params)
            params2["q"] = f"{name}" + (f' author:"{author}"' if author else "")
            resp2 = requests.get("https://openlibrary.org/search.json", params=params2, timeout=10)
            if resp2.ok:
                docs2 = resp2.json().get("docs", [])
                seen_keys = {d.get("key") for d in docs}
                for d in docs2:
                    if d.get("key") not in seen_keys:
                        docs.append(d)
                        seen_keys.add(d.get("key"))

        # Filtrer : garder les livres dont le titre contient des mots-clés de la série
        def is_relevant(doc):
            title_norm = normalize(doc.get("title", ""))
            series_field = doc.get("series", [])
            series_str = normalize(series_field[0] if series_field else "")
            # Appartient à la série si : series field match OU titre contient les mots clés
            if series_str and any(w in series_str for w in name_words):
                return True
            if name_words and all(w in title_norm for w in name_words[:2]):
                return True
            return False

        relevant = [d for d in docs if is_relevant(d)]
        if not relevant:
            relevant = docs  # garder tout si rien ne passe le filtre

        books = []
        seen = set()
        for doc in relevant:
            key = doc.get("key", "")
            if key in seen:
                continue
            seen.add(key)

            raw_series = doc.get("series", [])
            series_name = ""
            if raw_series:
                s = raw_series[0] if isinstance(raw_series, list) else raw_series
                vol_match = _re.search(r'\s*[#,]\s*\d+', s)
                series_name = s[:vol_match.start()].strip() if vol_match else s.strip()

            books.append({
                "ol_key": key,
                "title": doc.get("title", ""),
                "author": ", ".join(doc.get("author_name", [])) if doc.get("author_name") else (author or ""),
                "cover_url": extract_cover_url(doc.get("cover_i")),
                "first_publish_year": doc.get("first_publish_year"),
                "saga": series_name or name,
                "category": detect_category_from_subjects(doc.get("subject", [])),
            })

        # Trier par année de publication
        books.sort(key=lambda b: b.get("first_publish_year") or 9999)

        return {"books": books, "series_name": name, "total": len(books)}

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Erreur OL: {str(e)}")


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
        
        # Titre original depuis OL (langue d'origine du work)
        original_title = import_data.get("original_title") or work_data.get("title", "")
        title = original_title  # par défaut = titre original

        # Chercher éditions FR en parallèle avec la récupération des auteurs (timeout court)
        import concurrent.futures as _cf

        def _find_fr_title():
            try:
                fr_resp = requests.get(
                    f"https://openlibrary.org{ol_key}/editions.json",
                    params={"language": "fre", "limit": 5},
                    timeout=3
                )
                if fr_resp.ok:
                    for entry in fr_resp.json().get("entries", []):
                        langs = [l.get("key", "") for l in entry.get("languages", [])]
                        if "/languages/fre" in langs and entry.get("title"):
                            return entry["title"]
            except Exception:
                pass
            return None

        # Lancer en tâche de fond (non bloquant, on récupère après les auteurs)
        _fr_executor = _cf.ThreadPoolExecutor(max_workers=1)
        _fr_future = _fr_executor.submit(_find_fr_title)

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

        # Extraire la série depuis OL (champ "series" du work ou titre tomeN)
        series_list = work_data.get("series", [])
        saga_name = ""
        volume_number = None
        if series_list:
            # OL renvoie souvent "Harry Potter, Vol. 1" — on extrait nom + tome
            raw_series = series_list[0] if isinstance(series_list[0], str) else ""
            import re as _re
            vol_match = _re.search(r'[,\s]+(vol\.?|tome|book|#)\s*(\d+)', raw_series, _re.IGNORECASE)
            if vol_match:
                volume_number = int(vol_match.group(2))
                saga_name = raw_series[:vol_match.start()].strip()
            else:
                saga_name = raw_series.strip()
        # Récupérer volume depuis import_data s'il est fourni explicitement
        if import_data.get("volume_number"):
            volume_number = import_data["volume_number"]
        if import_data.get("saga"):
            saga_name = import_data["saga"]

        # Récupérer le titre français (attendu max 1s supplémentaire, car lancé en parallèle)
        try:
            fr_title = _fr_future.result(timeout=1)
            if fr_title:
                title = fr_title
        except Exception:
            pass
        finally:
            _fr_executor.shutdown(wait=False)

        # Récupérer des détails depuis la première édition
        first_edition = editions_data.get("entries", [{}])[0]

        # Créer le livre
        book_id = str(uuid.uuid4())
        book = {
            "id": book_id,
            "user_id": current_user["id"],
            "title": title,
            "original_title": original_title if original_title != title else None,
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
            "saga": saga_name,
            "volume_number": volume_number,
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
    author_name: str
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
            # S'assurer que l'author_key est formaté correctement
            if not author_key.startswith("/authors/"):
                author_key = f"/authors/{author_key}"
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

@router.get("/author/{author_name}/works")
async def get_author_works(
    author_name: str,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Récupérer toutes les œuvres d'un auteur depuis OpenLibrary"""
    try:
        # 1. Récupérer les livres de l'auteur depuis la bibliothèque personnelle
        user_books = list(books_collection.find(
            {
                "user_id": current_user["id"],
                "author": {"$regex": author_name, "$options": "i"}
            }
        ))
        
        # 2. Récupérer les œuvres depuis OpenLibrary
        params = {
            "author": author_name,
            "limit": limit,
            "fields": "key,title,author_name,first_publish_year,isbn,cover_i,subject,number_of_pages_median,publisher,series"
        }
        
        response = requests.get("https://openlibrary.org/search.json", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Grouper les livres par série et créer la structure
        series_books = {}
        individual_books = []
        
        for doc in data.get("docs", []):
            book_title = doc.get("title", "")
            series_info = doc.get("series", [])
            
            # Créer l'objet livre
            book_data = {
                "title": book_title,
                "year": doc.get("first_publish_year"),
                "isbn": doc.get("isbn", [""])[0] if doc.get("isbn") else "",
                "cover_url": extract_cover_url(doc.get("cover_i")),
                "publisher": ", ".join(doc.get("publisher", [])) if doc.get("publisher") else "",
                "pages": doc.get("number_of_pages_median"),
                "category": detect_category_from_subjects(doc.get("subject", [])),
                "source": "openlibrary"
            }
            
            # Vérifier si ce livre est dans la bibliothèque personnelle
            matching_book = None
            for user_book in user_books:
                if (user_book.get("title", "").lower() == book_title.lower() or 
                    (user_book.get("isbn") and user_book.get("isbn") == book_data.get("isbn"))):
                    matching_book = user_book
                    break
            
            if matching_book:
                book_data["status"] = matching_book.get("status", "to_read")
                book_data["volume_number"] = matching_book.get("volume_number")
                book_data["in_library"] = True
            else:
                book_data["in_library"] = False
            
            if series_info:
                # Livre fait partie d'une série
                series_name = series_info[0] if isinstance(series_info, list) else series_info
                if series_name not in series_books:
                    series_books[series_name] = {
                        "name": series_name,
                        "books": [],
                        "source": "openlibrary"
                    }
                series_books[series_name]["books"].append(book_data)
            else:
                # Livre individuel
                individual_books.append(book_data)
        
        # Convertir les séries en liste
        series_list = []
        for series_name, series_data in series_books.items():
            # Trier les livres par année
            series_data["books"].sort(key=lambda x: x.get("year", 0) or 0)
            series_list.append(series_data)
        
        # Trier les livres individuels par année (plus récents d'abord)
        individual_books.sort(key=lambda x: x.get("year", 0) or 0, reverse=True)
        
        # Compter le total
        total_books = sum(len(s["books"]) for s in series_list) + len(individual_books)
        
        return {
            "found": True,
            "author": author_name,
            "total_books": total_books,
            "series": series_list,
            "individual_books": individual_books,
            "sources": {"openlibrary": total_books, "library": len(user_books)}
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la recherche: {str(e)}")

@router.get("/book/{work_key:path}")
async def get_book_detail(
    work_key: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Fiche complète d'un livre Open Library.
    work_key peut être 'works/OL12345W' (sans le / initial, ajouté automatiquement)
    ou une clé source externe comme 'jikan_manga_123' / 'gbooks_xyz'.
    """
    # ── Sources externes (Jikan / Google Books) ────────────────────────────────
    if work_key.startswith("jikan_") or work_key.startswith("gbooks_"):
        # Chercher dans le cache manga/BD local
        from pathlib import Path as _Path
        import json as _json
        cache_path = _Path(__file__).resolve().parent.parent.parent / "data" / "manga_bd_cache.json"
        if cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    all_books = _json.load(f)
                match = next((b for b in all_books if b.get("ol_key") == work_key), None)
                if match:
                    return {**match, "in_user_library": False, "source": match.get("source", "external")}
            except Exception:
                pass
        raise HTTPException(status_code=404, detail="Livre non trouvé dans le catalogue")

    # ── Open Library ───────────────────────────────────────────────────────────
    # Ajouter le / initial si absent
    ol_key = work_key if work_key.startswith("/") else f"/{work_key}"

    try:
        # Récupérer les données du work
        work_url = f"https://openlibrary.org{ol_key}.json"
        resp = requests.get(work_url, timeout=10)
        if not resp.ok:
            raise HTTPException(status_code=404, detail="Livre non trouvé sur Open Library")
        work_data = resp.json()

        # Auteurs
        authors = []
        for author_ref in work_data.get("authors", []):
            ak = author_ref.get("author", {}).get("key") or author_ref.get("key", "")
            if ak:
                try:
                    ar = requests.get(f"https://openlibrary.org{ak}.json", timeout=5)
                    if ar.ok:
                        authors.append(ar.json().get("name", ""))
                except Exception:
                    pass

        # Description
        raw_desc = work_data.get("description", "")
        description = raw_desc.get("value", raw_desc) if isinstance(raw_desc, dict) else raw_desc

        # Couverture
        covers = work_data.get("covers", [])
        cover_url = f"https://covers.openlibrary.org/b/id/{covers[0]}-L.jpg" if covers and covers[0] > 0 else ""

        # Sujets
        subjects = work_data.get("subjects", [])

        # Vérifier si dans la bibliothèque de l'utilisateur
        in_library = books_collection.count_documents({
            "user_id": current_user["id"],
            "$or": [{"ol_key": ol_key}, {"ol_key": work_key}]
        }) > 0

        return {
            "ol_key": ol_key,
            "title": work_data.get("title", ""),
            "author": ", ".join(a for a in authors if a),
            "description": description,
            "subjects": subjects[:10],
            "cover_url": cover_url,
            "category": detect_category_from_subjects(subjects),
            "in_user_library": in_library,
            "source": "openlibrary",
            "ol_url": f"https://openlibrary.org{ol_key}",
        }
    except HTTPException:
        raise
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Open Library inaccessible: {str(e)}")


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