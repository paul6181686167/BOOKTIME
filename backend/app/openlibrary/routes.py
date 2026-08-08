from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import Optional
import asyncio
import logging
import uuid
import re as _re_global
import unicodedata
import requests
from ..database.connection import books_collection
from ..security.jwt import get_current_user
from ..utils.validation import validate_category
from ..utils.category_detect import detect_category_from_subjects
from ..utils.category_buffer import set_cached_category

logger = logging.getLogger("booktime.openlibrary")

# Au plus 2 recherches OL en parallèle : au-delà, les suggestions à la frappe
# saturaient le thread-pool asyncio et rendaient login /health injoignables.
_OL_SEARCH_SEM = asyncio.Semaphore(2)

def _normalize_query(s: str) -> str:
    """Supprime accents et ponctuation pour une recherche élargie"""
    no_accent = unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode('utf-8')
    return no_accent.strip()

router = APIRouter(prefix="/api/openlibrary", tags=["openlibrary"])

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

def _accent_score(s: str) -> int:
    return len(_re_global.findall(r"[àâäéèêëïîôùûüçœæ]", s or "", flags=_re_global.I))


def _find_french_edition_title(ol_key: str, timeout: float = 2.0) -> Optional[str]:
    """Titre d'une édition française Open Library pour un work (ex. /works/OL123W)."""
    if not ol_key:
        return None
    key = ol_key if ol_key.startswith("/") else f"/{ol_key}"
    if "/works/" not in key and key.startswith("/books/"):
        return None
    try:
        fr_resp = requests.get(
            f"https://openlibrary.org{key}/editions.json",
            params={"language": "fre", "limit": 8},
            timeout=timeout,
        )
        if not fr_resp.ok:
            return None
        best = None
        best_score = -1
        for entry in fr_resp.json().get("entries", []):
            langs = [l.get("key", "") for l in entry.get("languages", [])]
            title = (entry.get("title") or "").strip()
            if "/languages/fre" not in langs or not title:
                continue
            score = _accent_score(title) * 5 + (10 if entry.get("covers") else 0)
            if score > best_score:
                best_score = score
                best = title
        return best
    except Exception:
        return None


def _alias_french_title(title: str) -> Optional[str]:
    """Alias FR connus — retourne uniquement un titre qui « sonne » français."""
    try:
        from ..utils.book_synopsis import _FR_TITLE_ALIASES, _normalize_title
        import re as _re

        aliases = _FR_TITLE_ALIASES.get(_normalize_title(title) or "", ())
        fr_hint = _re.compile(
            r"[àâäéèêëïîôùûüçœæ]|^(le|la|les|l'|l’|un|une|des|du)\b",
            _re.I,
        )
        # 1) Alias clairement FR et différent du titre actuel
        for a in aliases:
            if a and a.lower() != (title or "").lower() and fr_hint.search(a):
                return a
        # 2) Si le titre actuel est déjà FR, ne pas le remplacer par un EN
        if fr_hint.search(title or ""):
            return None
        # 3) Sinon premier alias différent (dernier recours)
        for a in aliases:
            if a and a.lower() != (title or "").lower() and fr_hint.search(a):
                return a
    except Exception:
        pass
    return None


def _doc_to_book(doc: dict) -> dict:
    """Convertit un document OL en objet livre normalisé"""
    raw_series = doc.get("series", [])
    series_name = ""
    if raw_series:
        s = raw_series[0] if isinstance(raw_series, list) else raw_series
        vol_match = _re_global.search(r'\s*[#,]\s*\d+', s)
        series_name = s[:vol_match.start()].strip() if vol_match else s.strip()

    ol_title = doc.get("title", "")
    langs = doc.get("language", []) or []
    langs_l = [str(l).lower() for l in langs]

    # Titre FR dès que possible (alias connus, sinon édition fre plus tard en enrichissement)
    display_title = ol_title
    original_title = ol_title
    alias = _alias_french_title(ol_title)
    if alias:
        display_title = alias
        original_title = ol_title if ol_title != alias else ol_title
    elif "fre" in langs_l or any("fre" in x for x in langs_l):
        display_title = ol_title

    return {
        "ol_key": doc.get("key", ""),
        "title": display_title,
        "original_title": original_title if original_title != display_title else (
            ol_title if display_title != ol_title else None
        ),
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
        "title_fr": display_title if display_title != ol_title or "fre" in langs_l else None,
    }


def _search_open_library_sync(
    q: str,
    limit: int = 10,
    year_start: Optional[int] = None,
    year_end: Optional[int] = None,
    language: Optional[str] = None,
    min_pages: Optional[int] = None,
    max_pages: Optional[int] = None,
    author_filter: Optional[str] = None,
) -> dict:
    """Travail bloquant (HTTP Open Library) : toujours appeler via asyncio.to_thread.

    Un `async def` qui faisait `requests.get` gelait toute l'API dès qu'OL
    ramentait — y compris Wikidata et /health — d'où des recherches à 0 résultat.
    """
    import concurrent.futures

    empty = {
        "books": [],
        "total_found": 0,
        "source_unavailable": True,
        "filters_applied": {
            "year_range": f"{year_start}-{year_end}" if year_start or year_end else None,
            "language": language,
            "pages_range": f"{min_pages}-{max_pages}" if min_pages or max_pages else None,
            "author": author_filter,
        },
    }

    try:
        OL_URL = "https://openlibrary.org/search.json"
        fetch_limit = min(limit + 10, 50)
        # Suggestions (limit bas) : timeout court pour ne pas saturer le serveur
        # pendant la saisie. Recherche complète : un peu plus large.
        ol_timeout = 5 if limit <= 8 else 8

        q_norm = _normalize_query(q)
        queries = [q]
        if q_norm.lower() != q.lower():
            queries.append(q_norm)

        def _fetch(q_term):
            try:
                params = _build_ol_params(
                    q_term, fetch_limit, year_start, year_end, language, author_filter
                )
                r = requests.get(OL_URL, params=params, timeout=ol_timeout)
                if not r.ok:
                    return {"docs": [], "numFound": 0, "_failed": True}
                data = r.json()
                data["_failed"] = False
                return data
            except requests.RequestException as exc:
                logger.warning("OpenLibrary lent pour '%s': %s", q_term, exc)
                return {"docs": [], "numFound": 0, "_failed": True}

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(_fetch, qt) for qt in queries]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

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
        all_failed = bool(results) and all(r.get("_failed") for r in results)

        books = []
        for doc in merged_docs:
            if min_pages and doc.get("number_of_pages_median", 0) < min_pages:
                continue
            if max_pages and doc.get("number_of_pages_median", float("inf")) > max_pages:
                continue
            books.append(_doc_to_book(doc))

        books = books[:limit]

        # Enrichissement FR : uniquement sur la recherche « pleine », pas sur les
        # suggestions (limit bas) — chaque titre FR = un aller-retour OL de plus.
        if limit > 8 and books and not all_failed:

            def _enrich_fr(book: dict) -> dict:
                if book.get("title_fr") or "fre" in " ".join(book.get("available_languages") or []):
                    return book
                if (
                    book.get("title")
                    and book.get("original_title")
                    and book["title"] != book.get("original_title")
                ):
                    return book
                fr = _find_french_edition_title(book.get("ol_key") or "", timeout=1.2)
                if fr and fr.strip() and fr.strip().lower() != (book.get("title") or "").lower():
                    book["original_title"] = book.get("original_title") or book.get("title")
                    book["title"] = fr.strip()
                    book["title_fr"] = fr.strip()
                    langs = list(book.get("available_languages") or [])
                    if "fre" not in langs:
                        langs = ["fre"] + langs
                    book["available_languages"] = langs[:5]
                return book

            try:
                enrich_n = min(8, len(books))
                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                    enriched_head = list(pool.map(_enrich_fr, books[:enrich_n]))
                books = enriched_head + books[enrich_n:]
            except Exception as exc:
                logger.debug("Enrichissement titres FR search: %s", exc)

        return {
            "books": books,
            "total_found": total_found,
            "source_unavailable": all_failed,
            "filters_applied": {
                "year_range": f"{year_start}-{year_end}" if year_start or year_end else None,
                "language": language,
                "pages_range": f"{min_pages}-{max_pages}" if min_pages or max_pages else None,
                "author": author_filter,
            },
        }

    except requests.RequestException as e:
        logger.warning("OpenLibrary indisponible pour '%s': %s", q, e)
        return empty


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
):
    """
    Rechercher des livres dans Open Library (public — pas d'auth requise).
    Stratégie large : requête originale + version sans accents, fusionnées et dédupliquées.
    Retourne original_title pour que le front puisse l'afficher en sous-titre.
    """
    # Semaphore : évite que 10 suggestions empilent 10 threads bloqués sur OL
    # et rendent login/auth injoignables (thread-pool asyncio saturé).
    async with _OL_SEARCH_SEM:
        return await asyncio.to_thread(
            _search_open_library_sync,
            q,
            limit,
            year_start,
            year_end,
            language,
            min_pages,
            max_pages,
            author_filter,
        )


def _get_series_books_sync(name: str, author: Optional[str], limit: int) -> dict:
    """HTTP Open Library synchrone — à appeler via asyncio.to_thread uniquement."""
    import re as _re

    def normalize(s):
        return _re.sub(r'\s+', ' ', (s or '').lower().strip())

    name_norm = normalize(name)
    name_words = [w for w in name_norm.split() if len(w) >= 3]

    query = f'"{name}"'
    if author:
        query += f' author:"{author}"'

    params = {
        "q": query,
        "limit": limit,
        "fields": "key,title,author_name,first_publish_year,isbn,cover_i,subject,number_of_pages_median,series",
    }
    resp = requests.get("https://openlibrary.org/search.json", params=params, timeout=(3, 8))
    resp.raise_for_status()
    docs = resp.json().get("docs", [])

    if len(docs) < 3:
        params2 = dict(params)
        params2["q"] = f"{name}" + (f' author:"{author}"' if author else "")
        resp2 = requests.get("https://openlibrary.org/search.json", params=params2, timeout=(3, 8))
        if resp2.ok:
            seen_keys = {d.get("key") for d in docs}
            for d in resp2.json().get("docs", []):
                if d.get("key") not in seen_keys:
                    docs.append(d)
                    seen_keys.add(d.get("key"))

    def is_relevant(doc):
        title_norm = normalize(doc.get("title", ""))
        series_field = doc.get("series", [])
        series_str = normalize(series_field[0] if series_field else "")
        if series_str and any(w in series_str for w in name_words):
            return True
        if name_words and all(w in title_norm for w in name_words[:2]):
            return True
        return False

    relevant = [d for d in docs if is_relevant(d)] or docs

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

    books.sort(key=lambda b: b.get("first_publish_year") or 9999)
    return {"books": books, "series_name": name, "total": len(books)}


@router.get("/series-books")
async def get_series_books(
    name: str,
    author: Optional[str] = None,
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Récupère les volumes d'une série depuis Open Library (hors event loop)."""
    try:
        async with _OL_SEARCH_SEM:
            return await asyncio.to_thread(_get_series_books_sync, name, author, limit)
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Erreur OL: {str(e)}")


def _import_from_ol_sync(import_data: dict, user_id: str) -> dict:
    """Import OL côté thread : chemin rapide si le front envoie déjà titre/auteur/couverture.

    L'ancien flux enchaînait work + editions + N auteurs + synopsis (souvent >15 s)
    dans un `async def`, ce qui bloquait aussi le reste de l'API.
    """
    ol_key = import_data.get("ol_key") or ""
    if ol_key and not ol_key.startswith("/"):
        ol_key = f"/{ol_key}"

    validated_category = validate_category(import_data.get("category", "roman"))

    # Doublon rapide par ol_key (si déjà importé)
    if ol_key:
        existing = books_collection.find_one(
            {"user_id": user_id, "ol_key": ol_key}, {"id": 1, "title": 1}
        )
        if existing:
            existing.pop("_id", None)
            raise HTTPException(
                status_code=409,
                detail="Ce livre est déjà dans votre collection",
            )

    title = (
        import_data.get("title")
        or import_data.get("title_fr")
        or import_data.get("display_title")
        or ""
    ).strip()
    author_str = (import_data.get("author") or "").strip()
    original_title = (import_data.get("original_title") or "").strip() or None
    cover_url = (import_data.get("cover_url") or "").strip()
    isbn = (import_data.get("isbn") or "").strip()
    saga_name = (import_data.get("saga") or "").strip()
    volume_number = import_data.get("volume_number")
    description = (import_data.get("description") or "").strip()
    subjects: list = []
    total_pages = import_data.get("total_pages") or import_data.get("number_of_pages")
    publication_year = import_data.get("publication_year") or import_data.get("first_publish_year")
    publisher = import_data.get("publisher") or ""

    # Repli OL uniquement si métadonnées essentielles manquantes (timeout court)
    work_data = {}
    if ol_key and (not title or not author_str):
        try:
            resp = requests.get(f"https://openlibrary.org{ol_key}.json", timeout=4)
            if resp.ok:
                work_data = resp.json()
                if not title:
                    title = (work_data.get("title") or "").strip()
                if not original_title:
                    original_title = title or None
                if not author_str and work_data.get("authors"):
                    # Un seul auteur max — assez pour l'affichage, évite la cascade
                    author_key = (
                        work_data["authors"][0].get("author", {}) or {}
                    ).get("key", "")
                    if author_key:
                        ar = requests.get(
                            f"https://openlibrary.org{author_key}.json", timeout=3
                        )
                        if ar.ok:
                            author_str = ar.json().get("name", "") or ""
                subjects = work_data.get("subjects") or []
        except requests.RequestException as exc:
            logger.warning("Import OL: work indisponible pour %s: %s", ol_key, exc)

    if not title:
        raise HTTPException(status_code=400, detail="Titre manquant pour l'import")

    if not original_title:
        original_title = title
    if not title or title == original_title:
        alias = _alias_french_title(original_title)
        if alias:
            title = alias

    if subjects:
        detected = detect_category_from_subjects(subjects, title=title or original_title)
        if detected == "roman" and validated_category in ("bd", "manga"):
            validated_category = "roman"
        elif detected in ("bd", "manga"):
            validated_category = detected

    if not saga_name and work_data.get("series"):
        raw_series = work_data["series"][0] if isinstance(work_data["series"][0], str) else ""
        vol_match = _re_global.search(
            r"[,\s]+(vol\.?|tome|book|#)\s*(\d+)", raw_series, _re_global.IGNORECASE
        )
        if vol_match:
            if volume_number is None:
                volume_number = int(vol_match.group(2))
            saga_name = raw_series[: vol_match.start()].strip()
        else:
            saga_name = raw_series.strip()

    # Couverture de secours sans télécharger toute la liste d'éditions
    if not cover_url and ol_key:
        cover_url = f"https://covers.openlibrary.org/b/olid/{ol_key.split('/')[-1]}-M.jpg"

    book_id = str(uuid.uuid4())
    book = {
        "id": book_id,
        "user_id": user_id,
        "title": title,
        "original_title": original_title if original_title != title else None,
        "author": author_str,
        "category": validated_category,
        "description": description,
        "genre": ", ".join(subjects[:3]) if subjects else "",
        "total_pages": total_pages,
        "publication_year": publication_year,
        "publisher": publisher if isinstance(publisher, str) else "",
        "isbn": isbn,
        "cover_url": cover_url,
        "ol_key": ol_key or None,
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
        "updated_at": datetime.utcnow(),
    }

    books_collection.insert_one(book)
    book.pop("_id", None)

    try:
        set_cached_category(
            title,
            author_str,
            category=validated_category,
            source="openlibrary_import",
            meta={"ol_key": ol_key},
        )
    except Exception:
        pass

    return {
        "success": True,
        "message": "Livre importé avec succès",
        "book": book,
        "type": "book",
        "_needs_synopsis": not bool(description),
    }


def _fill_synopsis_sync(book_id: str, user_id: str, title: str, author: str, isbn: str, ol_key: str):
    try:
        from ..utils.book_synopsis import (
            fetch_book_synopsis,
            looks_english,
            is_usable_synopsis,
        )

        syn = fetch_book_synopsis(
            title=title,
            author=author,
            isbn=isbn or "",
            ol_key=ol_key or "",
            want_pages=False,
        )
        cand = (syn.get("description") or "").strip()
        if is_usable_synopsis(cand) and not looks_english(cand):
            books_collection.update_one(
                {"id": book_id, "user_id": user_id},
                {"$set": {"description": cand, "updated_at": datetime.utcnow()}},
            )
    except Exception as exc:
        logger.debug("Synopsis différé import fail: %s", exc)


@router.post("/import")
async def import_from_open_library(
    import_data: dict,
    current_user: dict = Depends(get_current_user),
):
    """Importer un livre depuis Open Library (chemin rapide si métadonnées fournies)."""
    ol_key = import_data.get("ol_key")
    if not ol_key and not import_data.get("title"):
        raise HTTPException(
            status_code=400, detail="Clé Open Library ou titre requis"
        )
    try:
        result = await asyncio.to_thread(
            _import_from_ol_sync, import_data, current_user["id"]
        )
    except HTTPException:
        raise
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'import: {str(e)}")

    # Synopsis après coup, hors chemin critique
    if result.pop("_needs_synopsis", False):
        book = result.get("book") or {}
        asyncio.create_task(
            asyncio.to_thread(
                _fill_synopsis_sync,
                book.get("id"),
                current_user["id"],
                book.get("title") or "",
                book.get("author") or "",
                book.get("isbn") or "",
                book.get("ol_key") or "",
            )
        )

    return result

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
    """Rechercher un livre par ISBN (scan mobile / saisie)."""
    clean = "".join(c for c in (isbn or "") if c.isdigit() or c.upper() == "X")
    if len(clean) not in (10, 13):
        raise HTTPException(status_code=400, detail="ISBN invalide (10 ou 13 caractères)")

    try:
        # 1) API books : auteurs + couverture plus fiables
        api_resp = requests.get(
            "https://openlibrary.org/api/books",
            params={
                "bibkeys": f"ISBN:{clean}",
                "jscmd": "data",
                "format": "json",
            },
            timeout=12,
        )
        if api_resp.status_code == 200:
            entry = (api_resp.json() or {}).get(f"ISBN:{clean}") or {}
            if entry.get("title"):
                authors = [
                    a.get("name", "")
                    for a in (entry.get("authors") or [])
                    if a.get("name")
                ]
                cover = (entry.get("cover") or {}).get("medium") or (
                    entry.get("cover") or {}
                ).get("large")
                subjects_raw = entry.get("subjects") or []
                subjects = [
                    s.get("name", s) if isinstance(s, dict) else str(s)
                    for s in subjects_raw[:8]
                ]
                identifiers = entry.get("identifiers") or {}
                ol_ids = identifiers.get("openlibrary") or []
                # Chercher une clé work via search ISBN
                ol_key = ""
                try:
                    sr = requests.get(
                        "https://openlibrary.org/search.json",
                        params={"isbn": clean, "limit": 1, "fields": "key,title"},
                        timeout=8,
                    )
                    if sr.status_code == 200:
                        docs = (sr.json() or {}).get("docs") or []
                        if docs:
                            ol_key = docs[0].get("key") or ""
                except requests.RequestException:
                    pass
                if not ol_key and ol_ids:
                    ol_key = f"/books/{ol_ids[0]}"

                return {
                    "book": {
                        "ol_key": ol_key,
                        "title": entry.get("title") or "",
                        "author": ", ".join(authors) or "Auteur inconnu",
                        "category": detect_category_from_subjects(subjects),
                        "cover_url": cover
                        or f"https://covers.openlibrary.org/b/isbn/{clean}-M.jpg",
                        "first_publish_year": (entry.get("publish_date") or "")[:4]
                        or None,
                        "isbn": clean,
                        "subjects": subjects[:5],
                        "number_of_pages": entry.get("number_of_pages"),
                        "total_pages": entry.get("number_of_pages"),
                        "publisher": ", ".join(
                            p.get("name", p) if isinstance(p, dict) else str(p)
                            for p in (entry.get("publishers") or [])
                        ),
                    }
                }

        # 2) Fallback /isbn/{id}.json
        response = requests.get(f"https://openlibrary.org/isbn/{clean}.json", timeout=12)
        response.raise_for_status()
        data = response.json()

        work_key = data.get("works", [{}])[0].get("key", "")
        work_data = {}
        if work_key:
            work_response = requests.get(
                f"https://openlibrary.org{work_key}.json", timeout=10
            )
            if work_response.status_code == 200:
                work_data = work_response.json()

        author_names = []
        for author in data.get("authors", []) or []:
            if author.get("name"):
                author_names.append(author["name"])
            elif author.get("key"):
                try:
                    ar = requests.get(
                        f"https://openlibrary.org{author['key']}.json", timeout=6
                    )
                    if ar.status_code == 200:
                        author_names.append(ar.json().get("name", ""))
                except requests.RequestException:
                    pass

        return {
            "book": {
                "ol_key": work_key,
                "title": work_data.get("title", data.get("title", "")),
                "author": ", ".join([n for n in author_names if n])
                or "Auteur inconnu",
                "category": detect_category_from_subjects(
                    work_data.get("subjects", [])
                ),
                "cover_url": extract_cover_url(data.get("covers", [None])[0])
                or f"https://covers.openlibrary.org/b/isbn/{clean}-M.jpg",
                "first_publish_year": data.get("publish_date"),
                "isbn": clean,
                "subjects": work_data.get("subjects", [])[:5],
                "number_of_pages": data.get("number_of_pages"),
                "total_pages": data.get("number_of_pages"),
                "publisher": ", ".join(data.get("publishers", [])),
            }
        }

    except HTTPException:
        raise
    except requests.RequestException:
        raise HTTPException(
            status_code=404, detail=f"Livre non trouvé pour l'ISBN {clean}"
        )

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