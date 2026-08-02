from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime
from typing import Optional
import uuid
import re
import logging
from ..models.book import BookCreate, BookUpdate
from ..database.connection import books_collection
from ..security.jwt import get_current_user
from ..utils.validation import validate_category
from ..utils.category_buffer import get_cached_category, buffer_stats
from ..utils.category_verify import reclassify_books
from ..services.pagination import PaginatedResponse, pagination_service

router = APIRouter(prefix="/api/books", tags=["books"])
_logger = logging.getLogger("booktime.books")


def _apply_category_updates(user_id: str, updates: list) -> int:
    """Applique les changements de catégorie en base."""
    applied = 0
    for u in updates:
        book_id = u.get("id")
        new_cat = u.get("new_category")
        if not book_id or not new_cat:
            continue
        result = books_collection.update_one(
            {"id": book_id, "user_id": user_id},
            {"$set": {"category": new_cat, "category_verified": True}},
        )
        if getattr(result, "modified_count", 0) or getattr(result, "matched_count", 0):
            applied += 1
    return applied


def _auto_fix_book_categories(
    user_id: str, *, with_search: bool = True, force: bool = False
) -> dict:
    """
    Corrige les catégories bd/manga suspectes :
    1) mémoire tampon (titre+auteur)
    2) sinon recherche Open Library + sauvegarde tampon
    """
    report = {"checked": 0, "updated": [], "unchanged": 0, "from_buffer_only": 0}
    try:
        all_books = list(books_collection.find({"user_id": user_id}))
        candidates = [
            b
            for b in all_books
            if b.get("category") in ("bd", "manga")
            and (force or not b.get("category_verified"))
        ]

        # 1) Corrections immédiates depuis le tampon (sans réseau), sauf force
        buffer_updates = []
        need_search = []
        for book in candidates:
            if force:
                need_search.append(book)
                continue
            cached = get_cached_category(book.get("title") or "", book.get("author") or "")
            if cached and cached != book.get("category"):
                buffer_updates.append(
                    {
                        "id": book.get("id"),
                        "title": book.get("title"),
                        "author": book.get("author"),
                        "old_category": book.get("category"),
                        "new_category": cached,
                        "source": "buffer",
                        "from_cache": True,
                    }
                )
            elif cached and cached == book.get("category"):
                books_collection.update_one(
                    {"id": book.get("id"), "user_id": user_id},
                    {"$set": {"category_verified": True}},
                )
            else:
                need_search.append(book)

        if buffer_updates:
            _apply_category_updates(user_id, buffer_updates)
            report["from_buffer_only"] = len(buffer_updates)
            report["updated"].extend(buffer_updates)

        # 2) Recherche OL pour le reste + écriture tampon
        if with_search and need_search:
            search_report = reclassify_books(
                need_search, only_suspicious=True, force=force
            )
            report["checked"] = search_report.get("checked", 0) + len(buffer_updates)
            report["unchanged"] = search_report.get("unchanged", 0)
            search_updates = search_report.get("updated") or []
            if search_updates:
                _apply_category_updates(user_id, search_updates)
                report["updated"].extend(search_updates)
            for book in need_search:
                books_collection.update_one(
                    {"id": book.get("id"), "user_id": user_id},
                    {"$set": {"category_verified": True}},
                )
        else:
            report["checked"] = len(buffer_updates) + len(need_search)
    except Exception as exc:
        _logger.warning("Auto-fix catégories: %s", exc)
    return report

@router.get("", response_model=PaginatedResponse)
async def get_books(
    category: Optional[str] = None,
    status: Optional[str] = None,
    view_mode: Optional[str] = "books",  # "books" ou "series"
    limit: int = Query(10, ge=1, le=100, description="Nombre d'éléments par page"),
    offset: int = Query(0, ge=0, description="Décalage pour la pagination"),
    sort_by: str = Query("date_added", description="Champ de tri"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Ordre de tri"),
    current_user: dict = Depends(get_current_user)
):
    """
    Route mise à jour avec pagination optimisée par les indexes MongoDB.
    Utilise les indexes stratégiques créés en Phase 2.1.
    """
    # Si le mode série est demandé, déléguer aux séries avec pagination
    if view_mode == "series":
        from ..series.routes import get_library_series_paginated
        return await get_library_series_paginated(
            category=category,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
            current_user=current_user
        )
    
    # Mode livres avec pagination optimisée
    try:
        result = pagination_service.get_paginated_books(
            user_id=current_user["id"],
            category=category,
            status=status,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
            exclude_series=True  # Exclure livres faisant partie d'une série
        )
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération livres: {str(e)}")

@router.get("/all")
async def get_all_books(
    category: Optional[str] = None,
    status: Optional[str] = None,
    author: Optional[str] = None,
    saga: Optional[str] = None,
    limit: int = Query(20, ge=1, le=1000, description="Nombre d'éléments par page"),
    offset: int = Query(0, ge=0, description="Décalage pour la pagination"),
    sort_by: str = Query("date_added", description="Champ de tri"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Ordre de tri"),
    current_user: dict = Depends(get_current_user)
):
    """
    Récupérer TOUS les livres avec pagination et filtres avancés.
    """
    import logging
    logger = logging.getLogger(__name__)
    try:
        from ..db_config import database
        # Reclassement prudent des bd/manga suspects (recherche OL + mémoire tampon)
        _auto_fix_book_categories(current_user["id"], with_search=True)
        _auto_fix_series_categories(current_user["id"], force=False)

        # Mode mock : requête directe en mémoire
        if database.is_mock_mode():
            query = {"user_id": current_user["id"]}
            if category:
                query["category"] = category
            if status:
                query["status"] = status
            cursor = books_collection.find(query)
            docs = list(cursor)
            for b in docs:
                b.pop("_id", None)
                # Convertir datetime en string pour la sérialisation JSON
                for k, v in list(b.items()):
                    if hasattr(v, 'isoformat'):
                        b[k] = v.isoformat()
            return {
                "items": docs,
                "total": len(docs),
                "limit": limit,
                "offset": 0,
                "has_next": False,
                "has_previous": False,
                "next_offset": None,
                "previous_offset": None,
            }
        # Mode réel MongoDB
        result = pagination_service.get_paginated_books(
            user_id=current_user["id"],
            category=category,
            status=status,
            author=author,
            saga=saga,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
            exclude_series=False
        )
        return result
    except Exception as e:
        import traceback
        logger.error(f"Erreur get_all_books: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Erreur récupération livres: {str(e)}")


def _auto_fix_series_categories(user_id: str, *, force: bool = False) -> dict:
    """Même logique pour les séries de la bibliothèque."""
    from ..database.connection import series_library_collection
    from ..utils.category_verify import verify_category_via_search

    report = {"checked": 0, "updated": []}
    try:
        series = list(series_library_collection.find({"user_id": user_id}))
        for s in series:
            if not force and s.get("category_verified"):
                continue
            if not force and s.get("category") not in ("bd", "manga"):
                continue
            name = s.get("name") or s.get("series_name") or s.get("title") or ""
            author = s.get("author") or ""
            if isinstance(author, list):
                author = ", ".join(str(a) for a in author)
            old = s.get("category") or "roman"
            result = verify_category_via_search(
                name, author, force=force, current_category=old
            )
            new = result["category"]
            report["checked"] += 1
            filt = {"id": s["id"]} if s.get("id") else {"_id": s.get("_id")}
            series_library_collection.update_one(
                filt,
                {"$set": {"category": new, "category_verified": True}},
            )
            if new != old:
                report["updated"].append(
                    {
                        "id": s.get("id"),
                        "title": name,
                        "old_category": old,
                        "new_category": new,
                        "source": result.get("source"),
                    }
                )
    except Exception as exc:
        _logger.warning("Auto-fix séries: %s", exc)
    return report


@router.post("/reclassify-categories")
async def reclassify_categories(
    force: bool = Query(False, description="Ignore le tampon et re-recherche Open Library"),
    current_user: dict = Depends(get_current_user),
):
    """
    Relance une recherche pour chaque livre/série classé bd/manga, mémorise
    le résultat dans la mémoire tampon, et corrige la bibliothèque.
    """
    report = _auto_fix_book_categories(
        current_user["id"], with_search=True, force=force
    )
    series_report = _auto_fix_series_categories(current_user["id"], force=force)
    report["series"] = series_report
    report["buffer"] = buffer_stats()
    return report

@router.get("/search-grouped")
async def search_books_grouped(
    q: str,
    category: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Recherche de livres avec regroupement intelligent par saga - SÉRIE FIRST
    """
    if not q or len(q.strip()) < 2:
        return {"results": [], "total_books": 0, "total_sagas": 0, "search_term": q}
    
    import unicodedata

    def _normalize(s: str) -> str:
        """Supprime les accents pour la recherche élargie"""
        return unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode('utf-8').lower()

    search_term = q.strip().lower()
    search_term_norm = _normalize(search_term)  # version sans accents
    filter_dict = {"user_id": current_user["id"]}

    if category:
        filter_dict["category"] = category

    def _regex_clause(field: str, term: str):
        return {field: {"$regex": re.escape(term), "$options": "i"}}

    # Termes de recherche : avec accents (original) + sans accents (élargi)
    terms = list({search_term, search_term_norm})  # dédupliqué

    or_clauses = []
    for term in terms:
        for field in ["title", "original_title", "author", "saga", "genre", "publisher"]:
            or_clauses.append(_regex_clause(field, term))

    search_filter = {"$or": or_clauses}
    
    # Combiner les filtres
    final_filter = {"$and": [filter_dict, search_filter]}
    
    # Récupérer les livres correspondants (plafond de sécurité pour éviter la surcharge mémoire)
    matching_books = list(books_collection.find(final_filter, {"_id": 0}).limit(500))
    
    # 🆕 AMÉLIORATION : Grouper par saga ET par auteur en privilégiant les séries
    saga_groups = {}
    author_groups = {}
    isolated_books = []
    
    for book in matching_books:
        saga = book.get("saga", "").strip()
        author = book.get("author", "").strip()
        
        if saga:
            # Grouper par saga
            if saga not in saga_groups:
                saga_groups[saga] = []
            saga_groups[saga].append(book)
        elif author:
            # Grouper par auteur si pas de saga
            if author not in author_groups:
                author_groups[author] = []
            author_groups[author].append(book)
        else:
            isolated_books.append(book)
    
    # Construire les résultats avec les séries en premier
    results = []
    
    # 1. Ajouter les séries comme entités uniques (priorité absolue)
    for saga_name, saga_books in saga_groups.items():
        saga_books_sorted = sorted(saga_books, key=lambda b: b.get("volume_number", 0))
        
        # Calculer la progression de la série
        total_books = len(saga_books)
        completed_books = len([b for b in saga_books if b.get("status") == "completed"])
        reading_books = len([b for b in saga_books if b.get("status") == "reading"])
        
        # Prendre les infos de base du premier livre
        first_book = saga_books_sorted[0]
        
        series_entity = {
            "id": f"series_{saga_name.replace(' ', '_').lower()}",
            "type": "series",
            "title": saga_name,
            "author": first_book.get("author"),
            "category": first_book.get("category"),
            "description": first_book.get("description", ""),
            "cover_url": first_book.get("cover_url", ""),
            "genre": first_book.get("genre", ""),
            "total_books": total_books,
            "completed_books": completed_books,
            "reading_books": reading_books,
            "progress_percentage": round((completed_books / total_books) * 100) if total_books > 0 else 0,
            "books": saga_books_sorted,
            "date_added": min(b.get("date_added", datetime.utcnow()) for b in saga_books),
            "last_updated": max(b.get("updated_at", b.get("date_added", datetime.utcnow())) for b in saga_books)
        }
        
        results.append(series_entity)
    
    # 🆕 2. Ajouter les groupes d'auteurs (si plus de 1 livre par auteur)
    for author_name, author_books in author_groups.items():
        if len(author_books) > 1:  # Seulement si plusieurs livres du même auteur
            author_books_sorted = sorted(author_books, key=lambda b: b.get("date_added", datetime.utcnow()))
            
            # Calculer la progression par auteur
            total_books = len(author_books)
            completed_books = len([b for b in author_books if b.get("status") == "completed"])
            reading_books = len([b for b in author_books if b.get("status") == "reading"])
            
            # Prendre les infos de base du premier livre
            first_book = author_books_sorted[0]
            
            author_series_entity = {
                "id": f"author_{author_name.replace(' ', '_').lower()}",
                "type": "author_series",
                "title": f"Livres de {author_name}",
                "author": author_name,
                "category": first_book.get("category"),
                "description": f"Collection de {total_books} livre(s) de {author_name}",
                "cover_url": first_book.get("cover_url", ""),
                "genre": first_book.get("genre", ""),
                "total_books": total_books,
                "completed_books": completed_books,
                "reading_books": reading_books,
                "progress_percentage": round((completed_books / total_books) * 100) if total_books > 0 else 0,
                "books": author_books_sorted,
                "date_added": min(b.get("date_added", datetime.utcnow()) for b in author_books),
                "last_updated": max(b.get("updated_at", b.get("date_added", datetime.utcnow())) for b in author_books)
            }
            
            results.append(author_series_entity)
        else:
            # Livre unique d'un auteur, ajouter comme livre isolé
            isolated_books.extend(author_books)
    
    # 3. Ajouter les livres isolés
    for book in isolated_books:
        book["type"] = "book"
        results.append(book)
    
    # Trier les résultats par date de dernière mise à jour
    results.sort(key=lambda x: x.get("last_updated", x.get("date_added", datetime.utcnow())), reverse=True)
    
    return {
        "results": results,
        "total_books": len(matching_books),
        "total_sagas": len(saga_groups),
        "total_author_series": len([author for author, books in author_groups.items() if len(books) > 1]),
        "search_term": q,
        "grouped_by_saga": True,
        "series_first": True
    }

@router.get("/resolve-pages")
async def resolve_french_paperback_pages(
    title: str = Query(..., min_length=1),
    author: str = Query(""),
    isbn: str = Query(""),
    ol_key: str = Query(""),
    current_user: dict = Depends(get_current_user),
):
    """
    Résout le nombre de pages de l'édition poche FR (sans id livre).
    Utile pour les fiches issues de series_library.
    """
    from ..utils.book_synopsis import fetch_french_paperback_pages

    hit = fetch_french_paperback_pages(
        title=title,
        author=author,
        isbn=isbn,
        ol_key=ol_key,
    )
    if not hit or not hit.get("pages"):
        return {"pages": None, "source": "none", "found": False}
    return {
        "pages": int(hit["pages"]),
        "source": hit.get("source") or "fr_poche",
        "publisher": hit.get("publisher"),
        "isbn": hit.get("isbn"),
        "found": True,
    }


@router.get("/resolve-synopsis")
async def resolve_book_synopsis(
    title: str = Query(..., min_length=1),
    author: str = Query(""),
    isbn: str = Query(""),
    ol_key: str = Query(""),
    current_user: dict = Depends(get_current_user),
):
    """
    Résout résumé + pages sans id livre (séries rétrogradées / livres sans fiche books).
    """
    from ..utils.book_synopsis import fetch_book_synopsis, is_usable_synopsis

    result = fetch_book_synopsis(
        title=title,
        author=author,
        isbn=isbn,
        ol_key=ol_key,
    )
    description = (result.get("description") or "").strip()
    if not is_usable_synopsis(description):
        description = ""
    pages = result.get("pages")
    try:
        pages = int(pages) if pages is not None else None
        if pages is not None and pages <= 0:
            pages = None
    except (TypeError, ValueError):
        pages = None
    return {
        "description": description,
        "pages": pages,
        "source": result.get("source") or "none",
        "ol_key": result.get("ol_key") or ol_key or None,
        "found": bool(description or pages),
    }


@router.get("/{book_id}")
async def get_book(book_id: str, current_user: dict = Depends(get_current_user)):
    """Obtenir un livre par son ID"""
    book = books_collection.find_one({
        "id": book_id, 
        "user_id": current_user["id"]
    }, {"_id": 0})
    
    if not book:
        raise HTTPException(status_code=404, detail="Livre non trouvé")
    
    return book

@router.post("")
async def create_book(book_data: BookCreate, current_user: dict = Depends(get_current_user)):
    """Créer un nouveau livre"""
    # Valider la catégorie
    validated_category = validate_category(book_data.category)
    
    book_id = str(uuid.uuid4())
    book = {
        "id": book_id,
        "user_id": current_user["id"],
        **book_data.model_dump(),
        "category": validated_category,
        "date_added": datetime.utcnow(),
        "date_started": None,
        "date_completed": None
    }
    
    # Définir les dates selon le statut
    if book_data.status == "reading":
        book["date_started"] = datetime.utcnow()
    elif book_data.status == "completed":
        book["date_started"] = datetime.utcnow()
        book["date_completed"] = datetime.utcnow()
    
    try:
        books_collection.insert_one(book)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création du livre : {str(e)}")
    book.pop("_id", None)
    return book

@router.put("/{book_id}")
async def update_book(
    book_id: str, 
    book_update: BookUpdate, 
    current_user: dict = Depends(get_current_user)
):
    """Mettre à jour un livre"""
    book = books_collection.find_one({
        "id": book_id, 
        "user_id": current_user["id"]
    })
    
    if not book:
        raise HTTPException(status_code=404, detail="Livre non trouvé")
    
    update_data = book_update.model_dump(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    # Gérer les changements de statut
    if "status" in update_data:
        current_status = book.get("status")
        new_status = update_data["status"]
        
        if current_status != "reading" and new_status == "reading":
            update_data["date_started"] = datetime.utcnow()
        elif current_status != "completed" and new_status == "completed":
            if not book.get("date_started"):
                update_data["date_started"] = datetime.utcnow()
            update_data["date_completed"] = datetime.utcnow()
    
    books_collection.update_one(
        {"id": book_id, "user_id": current_user["id"]},
        {"$set": update_data}
    )
    
    updated_book = books_collection.find_one({
        "id": book_id, 
        "user_id": current_user["id"]
    }, {"_id": 0})
    
    return updated_book

@router.get("/{book_id}/synopsis")
async def get_book_synopsis(
    book_id: str,
    persist: bool = Query(True, description="Sauvegarder le résumé sur le livre"),
    current_user: dict = Depends(get_current_user),
):
    """
    Résumé / 4ᵉ de couverture (Google Books prioritaire, puis Open Library).
    Persiste la description sur le livre si elle était vide.
    """
    from ..utils.book_synopsis import fetch_book_synopsis, is_usable_synopsis

    book = books_collection.find_one(
        {"id": book_id, "user_id": current_user["id"]}, {"_id": 0}
    )
    if not book:
        raise HTTPException(status_code=404, detail="Livre non trouvé")

    existing_desc = (book.get("description") or "").strip()
    if not is_usable_synopsis(existing_desc):
        existing_desc = ""
    existing_pages = book.get("total_pages")
    has_pages = isinstance(existing_pages, (int, float)) and int(existing_pages) > 0

    if existing_desc and has_pages:
        return {
            "description": existing_desc,
            "pages": int(existing_pages),
            "source": "stored",
            "persisted": False,
            "book_id": book_id,
        }

    result = fetch_book_synopsis(
        title=book.get("title") or "",
        author=book.get("author") or "",
        isbn=book.get("isbn") or book.get("isbn13") or "",
        ol_key=book.get("ol_key") or "",
    )
    fetched_desc = (result.get("description") or "").strip()
    if not is_usable_synopsis(fetched_desc):
        fetched_desc = ""
    description = existing_desc or fetched_desc
    pages = int(existing_pages) if has_pages else result.get("pages")
    if pages is not None:
        try:
            pages = int(pages)
            if pages <= 0:
                pages = None
        except (TypeError, ValueError):
            pages = None

    persisted = False
    patch = {}
    if persist:
        if description and not existing_desc:
            patch["description"] = description
        if pages and not has_pages:
            patch["total_pages"] = pages
        if result.get("ol_key") and not book.get("ol_key"):
            patch["ol_key"] = result["ol_key"]
        if patch:
            patch["updated_at"] = datetime.utcnow()
            books_collection.update_one(
                {"id": book_id, "user_id": current_user["id"]},
                {"$set": patch},
            )
            persisted = True

    return {
        "description": description,
        "pages": pages,
        "source": result.get("source") or ("stored" if existing_desc else "none"),
        "persisted": persisted,
        "book_id": book_id,
        "ol_key": result.get("ol_key") or book.get("ol_key"),
    }


@router.post("/{book_id}/enrich")
async def enrich_book(book_id: str, current_user: dict = Depends(get_current_user)):
    """Enrichir un livre avec couverture, description (4ᵉ) et genres."""
    import httpx
    from ..utils.book_synopsis import fetch_book_synopsis

    book = books_collection.find_one({"id": book_id, "user_id": current_user["id"]}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Livre non trouvé")

    isbn = book.get("isbn") or ""
    title = book.get("title") or ""
    author = book.get("author") or ""

    enriched = {}

    # Résumé / 4ᵉ de couverture (GB + OL)
    if not (book.get("description") or "").strip():
        syn = fetch_book_synopsis(
            title=title,
            author=author,
            isbn=isbn or book.get("isbn13") or "",
            ol_key=book.get("ol_key") or "",
        )
        if syn.get("description"):
            enriched["description"] = syn["description"]
        if syn.get("ol_key") and not book.get("ol_key"):
            enriched["ol_key"] = syn["ol_key"]

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            # Chercher par ISBN d'abord, puis par titre/auteur
            if isbn:
                ol_url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&jscmd=data&format=json"
                r = await client.get(ol_url)
                if r.status_code == 200:
                    data = r.json()
                    ol_data = data.get(f"ISBN:{isbn}", {})
                    cover_ids = ol_data.get("cover", {})
                    if cover_ids.get("large") and not book.get("cover_url"):
                        enriched["cover_url"] = cover_ids["large"]
                    elif cover_ids.get("medium") and not book.get("cover_url"):
                        enriched["cover_url"] = cover_ids["medium"]
                    subjects = [
                        (s if isinstance(s, str) else s.get("name", ""))
                        for s in ol_data.get("subjects", [])[:5]
                    ]
                    if subjects:
                        enriched["genres"] = subjects

            if title and ("cover_url" not in enriched or "genres" not in enriched):
                q = f"{title} {author}".strip()
                r = await client.get(
                    "https://openlibrary.org/search.json",
                    params={"q": q, "limit": 1, "fields": "cover_i,subject,key"}
                )
                if r.status_code == 200:
                    docs = r.json().get("docs", [])
                    if docs:
                        doc = docs[0]
                        if doc.get("cover_i") and not book.get("cover_url") and "cover_url" not in enriched:
                            enriched["cover_url"] = f"https://covers.openlibrary.org/b/id/{doc['cover_i']}-L.jpg"
                        if doc.get("subject") and "genres" not in enriched:
                            enriched["genres"] = doc["subject"][:5]

    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erreur enrichissement : {str(e)}")

    if not enriched:
        return {"message": "Aucune donnée supplémentaire trouvée", "book": book}

    enriched["updated_at"] = datetime.utcnow()
    books_collection.update_one({"id": book_id, "user_id": current_user["id"]}, {"$set": enriched})
    updated = books_collection.find_one({"id": book_id, "user_id": current_user["id"]}, {"_id": 0})
    return {"message": "Livre enrichi avec succès", "book": updated}


@router.delete("/{book_id}")
async def delete_book(book_id: str, current_user: dict = Depends(get_current_user)):
    """Supprimer un livre - recherche par champ 'id' ou '_id' pour la compatibilité"""
    user_id = current_user["id"]

    # Tentative 1 : champ "id" (format standard UUID)
    result = books_collection.delete_one({"id": book_id, "user_id": user_id})

    # Tentative 2 : champ "_id" en string si le livre a été créé sans champ id explicite
    if result.deleted_count == 0:
        from bson import ObjectId
        try:
            oid = ObjectId(book_id)
            result = books_collection.delete_one({"_id": oid, "user_id": user_id})
        except Exception:
            pass

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Livre non trouvé dans ta bibliothèque")

    return {"message": "Livre retiré avec succès"}