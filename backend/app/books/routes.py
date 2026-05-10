from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime
from typing import Optional
import uuid
import re
from ..models.book import BookCreate, BookUpdate
from ..database.connection import books_collection
from ..security.jwt import get_current_user
from ..utils.validation import validate_category
from ..services.pagination import PaginatedResponse, pagination_service

router = APIRouter(prefix="/api/books", tags=["books"])

# Genres typiques des romans (indiquent qu'un livre n'est PAS une BD/manga)
_ROMAN_GENRE_KEYWORDS = [
    'fantasy', 'fiction', 'roman', 'novel', 'science fiction', 'sf', 'thriller',
    'mystery', 'adventure', 'horror', 'historical', 'biography', 'detective',
    'literature', 'young adult', 'children', 'epic', 'dystopia', 'littérature',
    'policier', 'fantastique', 'horreur', 'aventure', 'historique', 'biographie',
    'science-fiction', 'conte', 'jeunesse',
]

# Mots-clés qui indiquent clairement une BD ou un manga dans le titre/genre
_BD_MANGA_KEYWORDS = [
    'manga', 'comic', 'bande dessinée', 'bd', 'manhwa', 'manhua', 'anime',
    'graphic novel', 'comics',
]

def _auto_fix_book_categories(user_id: str):
    """
    Corrige automatiquement les catégories de livres mal détectées.
    Un livre classé 'bd' ou 'manga' dont le genre indique un roman est recorrigé en 'roman'.
    Un livre classé 'roman' dont le genre indique clairement BD/manga est recorrigé.
    """
    try:
        all_books = list(books_collection.find({"user_id": user_id}))
        for book in all_books:
            current_cat = book.get("category", "roman")
            genre = (book.get("genre") or "").lower()
            title = (book.get("title") or "").lower()
            saga = (book.get("saga") or "").lower()
            combined = f"{genre} {title} {saga}"

            if current_cat in ("bd", "manga"):
                # Vérifier si le genre suggère clairement un roman
                has_roman_genre = any(kw in genre for kw in _ROMAN_GENRE_KEYWORDS)
                has_bd_manga_marker = any(kw in combined for kw in _BD_MANGA_KEYWORDS)

                # Corriger si : genre indique un roman OU aucun marqueur BD/manga n'existe
                should_fix = (has_roman_genre or not genre) and not has_bd_manga_marker
                if should_fix:
                    books_collection.update_one(
                        {"id": book.get("id"), "user_id": user_id},
                        {"$set": {"category": "roman"}}
                    )
    except Exception:
        pass  # Silencieux pour ne pas bloquer le chargement

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
        # Mode mock : requête directe en mémoire
        if database.is_mock_mode():
            # Auto-correction des catégories mal détectées (ex: livres illustrés classés en BD)
            _auto_fix_book_categories(current_user["id"])

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
    
    search_term = q.strip().lower()
    filter_dict = {"user_id": current_user["id"]}
    
    if category:
        filter_dict["category"] = category
    
    # Recherche dans tous les champs pertinents
    search_filter = {
        "$or": [
            {"title": {"$regex": re.escape(search_term), "$options": "i"}},
            {"author": {"$regex": re.escape(search_term), "$options": "i"}},
            {"saga": {"$regex": re.escape(search_term), "$options": "i"}},
            {"description": {"$regex": re.escape(search_term), "$options": "i"}},
            {"genre": {"$regex": re.escape(search_term), "$options": "i"}},
            {"publisher": {"$regex": re.escape(search_term), "$options": "i"}}
        ]
    }
    
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

@router.post("/{book_id}/enrich")
async def enrich_book(book_id: str, current_user: dict = Depends(get_current_user)):
    """Enrichir un livre avec les métadonnées Open Library (couverture, description, genres)"""
    import httpx

    book = books_collection.find_one({"id": book_id, "user_id": current_user["id"]}, {"_id": 0})
    if not book:
        raise HTTPException(status_code=404, detail="Livre non trouvé")

    isbn = book.get("isbn") or ""
    title = book.get("title") or ""
    author = book.get("author") or ""

    enriched = {}

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
                    if cover_ids.get("large"):
                        enriched["cover_url"] = cover_ids["large"]
                    elif cover_ids.get("medium"):
                        enriched["cover_url"] = cover_ids["medium"]
                    if ol_data.get("description"):
                        desc = ol_data["description"]
                        enriched["description"] = desc if isinstance(desc, str) else desc.get("value", "")
                    subjects = [s.get("name", "") for s in ol_data.get("subjects", [])[:5]]
                    if subjects:
                        enriched["genres"] = subjects

            if not enriched and title:
                q = f"{title} {author}".strip()
                search_url = f"https://openlibrary.org/search.json?q={q}&limit=1&fields=cover_i,description,subject"
                r = await client.get(search_url)
                if r.status_code == 200:
                    docs = r.json().get("docs", [])
                    if docs:
                        doc = docs[0]
                        if doc.get("cover_i"):
                            enriched["cover_url"] = f"https://covers.openlibrary.org/b/id/{doc['cover_i']}-L.jpg"
                        if doc.get("subject"):
                            enriched["genres"] = doc["subject"][:5]

    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erreur Open Library : {str(e)}")

    if not enriched:
        return {"message": "Aucune donnée supplémentaire trouvée sur Open Library", "book": book}

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