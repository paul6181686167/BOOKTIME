"""
Vérifie la catégorie d'un livre via recherche Open Library, puis mémorise le résultat.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Optional

import requests

from .category_buffer import get_cached_category, set_cached_category
from .category_detect import detect_category_from_subjects, coerce_category

logger = logging.getLogger("booktime.category_verify")

_OL_SEARCH = "https://openlibrary.org/search.json"
_TIMEOUT = 12


def _pick_best_doc(docs: list[dict], title: str, author: str) -> Optional[dict]:
    if not docs:
        return None
    title_l = (title or "").strip().lower()
    author_l = (author or "").strip().lower()
    best, best_score = None, -10**9
    for doc in docs[:8]:
        score = 0
        dt = (doc.get("title") or "").lower()
        if title_l and dt == title_l:
            score += 5
        elif title_l and title_l in dt:
            score += 3
        elif title_l and dt and (dt in title_l or title_l.split(":")[0].strip() in dt):
            score += 2
        authors = [a.lower() for a in (doc.get("author_name") or []) if a]
        if author_l and any(author_l in a or a in author_l for a in authors):
            score += 3
        # Légère pénalité rayon comics secondaire (adaptations de romans)
        subjects = doc.get("subject") or []
        sub_blob = " ".join(str(s) for s in subjects).lower()
        shelf_secondary = (
            "comics & graphic novels" in sub_blob or "comic books, strips" in sub_blob
        )
        cat = detect_category_from_subjects(subjects, title=doc.get("title") or title)
        if shelf_secondary and cat == "roman":
            score -= 1
        if score > best_score:
            best, best_score = doc, score
    return best or docs[0]


def verify_category_via_search(
    title: str,
    author: str = "",
    *,
    force: bool = False,
    current_category: Optional[str] = None,
) -> dict[str, Any]:
    """
    Retourne {category, source, from_cache, subjects_sample}.
    Utilise la mémoire tampon sauf si force=True.
    """
    title = (title or "").strip()
    author = (author or "").strip()
    if not title:
        return {
            "category": coerce_category(current_category),
            "source": "empty",
            "from_cache": False,
        }

    if not force:
        cached = get_cached_category(title, author)
        if cached:
            return {"category": cached, "source": "buffer", "from_cache": True}

    category = coerce_category(current_category)
    source = "fallback"
    subjects_sample: list[str] = []

    try:
        q = title if not author else f"{title} {author}"
        resp = requests.get(
            _OL_SEARCH,
            params={
                "q": q,
                "limit": 5,
                "fields": "key,title,author_name,subject",
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        docs = resp.json().get("docs") or []
        best = _pick_best_doc(docs, title, author)
        if best:
            subjects = best.get("subject") or []
            subjects_sample = [str(s) for s in subjects[:12]]
            category = detect_category_from_subjects(
                subjects, title=best.get("title") or title
            )
            source = "openlibrary"
        else:
            # Pas de notice OL : ne pas conserver un bd/manga douteux
            category = detect_category_from_subjects([], title=title)
            source = "heuristic_local"
    except Exception as exc:
        logger.warning("Vérif catégorie OL échouée pour %r: %s", title, exc)
        category = detect_category_from_subjects([], title=title)
        source = "heuristic_local"

    set_cached_category(
        title,
        author,
        category=category,
        source=source,
        meta={"subjects_sample": subjects_sample},
    )
    return {
        "category": category,
        "source": source,
        "from_cache": False,
        "subjects_sample": subjects_sample,
    }


def reclassify_books(
    books: list[dict],
    *,
    only_suspicious: bool = True,
    max_workers: int = 4,
    force: bool = False,
) -> dict[str, Any]:
    """
    Pour chaque livre, vérifie la catégorie (recherche + tampon) et propose/applique
    les corrections. Retourne un rapport ; n'écrit pas en base (appelant le fait).
    """
    to_check: list[dict] = []
    for book in books:
        cat = coerce_category(book.get("category"))
        if only_suspicious and cat not in ("bd", "manga"):
            continue
        to_check.append(book)

    updates: list[dict] = []
    unchanged = 0

    def _one(book: dict) -> Optional[dict]:
        title = book.get("title") or ""
        author = book.get("author") or ""
        old = coerce_category(book.get("category"))
        result = verify_category_via_search(
            title, author, force=force, current_category=old
        )
        new = result["category"]
        if new != old:
            return {
                "id": book.get("id"),
                "title": title,
                "author": author,
                "old_category": old,
                "new_category": new,
                "source": result.get("source"),
                "from_cache": result.get("from_cache"),
            }
        return None

    if not to_check:
        return {"checked": 0, "updated": [], "unchanged": 0}

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_one, b): b for b in to_check}
        for fut in as_completed(futures):
            try:
                change = fut.result()
            except Exception as exc:
                logger.warning("reclassify item failed: %s", exc)
                continue
            if change:
                updates.append(change)
            else:
                unchanged += 1

    return {
        "checked": len(to_check),
        "updated": updates,
        "unchanged": unchanged,
    }
