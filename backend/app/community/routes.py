"""
Avis de la communauté : moyenne des notes + liste d'avis publics
agrégés sur les mêmes livres (ol_key / isbn / titre+auteur).
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query

from ..database.connection import books_collection, series_library_collection, db
from ..security.jwt import get_current_user

router = APIRouter(prefix="/api/community", tags=["community"])


def _norm_isbn(isbn: Optional[str]) -> str:
    return re.sub(r"[^0-9Xx]", "", (isbn or "").strip())


def _norm_text(value: Optional[str]) -> str:
    s = (value or "").lower().strip()
    s = re.sub(r"[^\w\s]", " ", s, flags=re.UNICODE)
    return re.sub(r"\s+", " ", s).strip()


def _escape_regex(value: str) -> str:
    return re.escape(value)


def _build_book_match(
    ol_key: Optional[str],
    isbn: Optional[str],
    title: Optional[str],
    author: Optional[str],
) -> Optional[Dict[str, Any]]:
    clauses: List[Dict[str, Any]] = []

    ol = (ol_key or "").strip()
    if ol:
        variants = {ol, ol.lstrip("/")}
        if not ol.startswith("/"):
            variants.add(f"/{ol}")
        clauses.append({"ol_key": {"$in": list(variants)}})
        # Parfois stocké sans préfixe works/
        if "works/" in ol:
            short = ol.split("works/")[-1]
            clauses.append({"ol_key": {"$regex": f"{_escape_regex(short)}$"}})

    isbn_n = _norm_isbn(isbn)
    if len(isbn_n) >= 10:
        # Tolère tirets / espaces côté documents stockés
        loose = r"[\s\-]*".join(_escape_regex(c) for c in isbn_n)
        clauses.append({"isbn": {"$regex": f"^{loose}$", "$options": "i"}})

    t = _norm_text(title)
    a = _norm_text(author)
    if t and len(t) >= 3:
        title_re = _escape_regex(t).replace("\\ ", "\\s+")
        title_clause: Dict[str, Any] = {
            "title": {"$regex": f"^{title_re}$", "$options": "i"}
        }
        if a and a not in ("auteur inconnu", "unknown"):
            author_re = _escape_regex(a.split(",")[0].strip()).replace("\\ ", "\\s+")
            title_clause = {
                "$and": [
                    title_clause,
                    {"author": {"$regex": author_re, "$options": "i"}},
                ]
            }
        clauses.append(title_clause)

    if not clauses:
        return None
    return {"$or": clauses}


def _is_profile_public(profile: Optional[dict]) -> bool:
    if not profile:
        return True
    level = (profile.get("privacy_level") or "public").lower()
    return level == "public"


def _display_name(profile: Optional[dict], user: Optional[dict], user_id: str) -> str:
    if profile and profile.get("display_name"):
        return str(profile["display_name"]).strip()
    if user and user.get("email"):
        return str(user["email"]).split("@")[0]
    return f"Lecteur {user_id[:6]}"


def _collect_from_books(match: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
    cursor = books_collection.find(
        {
            "$and": [
                match,
                {
                    "$or": [
                        {"rating": {"$gt": 0}},
                        {
                            "review": {
                                "$exists": True,
                                "$type": "string",
                                "$ne": "",
                            }
                        },
                    ]
                },
            ]
        },
        {
            "_id": 0,
            "user_id": 1,
            "rating": 1,
            "review": 1,
            "title": 1,
            "author": 1,
            "date_completed": 1,
            "updated_at": 1,
            "created_at": 1,
        },
    ).limit(max(limit * 3, 60))

    rows = []
    for doc in cursor:
        rating = doc.get("rating") or 0
        try:
            rating = int(rating)
        except (TypeError, ValueError):
            rating = 0
        review = (doc.get("review") or "").strip()
        if rating <= 0 and not review:
            continue
        rows.append(
            {
                "user_id": doc.get("user_id"),
                "rating": rating if rating > 0 else None,
                "review": review,
                "source": "book",
                "date": doc.get("date_completed")
                or doc.get("updated_at")
                or doc.get("created_at"),
            }
        )
    return rows


def _collect_from_series_library(
    title: Optional[str], author: Optional[str], limit: int
) -> List[Dict[str, Any]]:
    """Livres individuels stockés en series_library (rétrogradés)."""
    t = _norm_text(title)
    if not t or len(t) < 3:
        return []
    title_re = _escape_regex(t).replace("\\ ", "\\s+")
    query: Dict[str, Any] = {
        "$and": [
            {
                "$or": [
                    {"series_name": {"$regex": f"^{title_re}$", "$options": "i"}},
                    {"name": {"$regex": f"^{title_re}$", "$options": "i"}},
                ]
            },
            {
                "$or": [
                    {"rating": {"$gt": 0}},
                    {"review": {"$exists": True, "$type": "string", "$ne": ""}},
                ]
            },
        ]
    }

    a = _norm_text(author)
    cursor = series_library_collection.find(
        query,
        {
            "_id": 0,
            "user_id": 1,
            "rating": 1,
            "review": 1,
            "authors": 1,
            "author": 1,
            "updated_at": 1,
            "created_at": 1,
        },
    ).limit(max(limit * 2, 40))

    rows = []
    for doc in cursor:
        if a and a not in ("auteur inconnu", "unknown"):
            authors = doc.get("authors") or []
            author_field = (doc.get("author") or "").lower()
            joined = " ".join(authors).lower() if isinstance(authors, list) else ""
            token = a.split(",")[0]
            if token not in joined and token not in author_field:
                continue
        rating = doc.get("rating") or 0
        try:
            rating = int(rating)
        except (TypeError, ValueError):
            rating = 0
        review = (doc.get("review") or "").strip()
        if rating <= 0 and not review:
            continue
        rows.append(
            {
                "user_id": doc.get("user_id"),
                "rating": rating if rating > 0 else None,
                "review": review,
                "source": "series_library",
                "date": doc.get("updated_at") or doc.get("created_at"),
            }
        )
    return rows


@router.get("/books/reviews")
async def get_community_book_reviews(
    ol_key: Optional[str] = Query(None),
    isbn: Optional[str] = Query(None),
    title: Optional[str] = Query(None),
    author: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user),
):
    """Moyenne des notes et avis publics pour un livre."""
    match = _build_book_match(ol_key, isbn, title, author)
    rows: List[Dict[str, Any]] = []
    if match:
        rows.extend(_collect_from_books(match, limit))
    rows.extend(_collect_from_series_library(title, author, limit))

    # Enrichir profils / filtrer private
    user_ids = list({r["user_id"] for r in rows if r.get("user_id")})
    profiles = {}
    users = {}
    if user_ids:
        for p in db.user_profiles.find(
            {"user_id": {"$in": user_ids}},
            {"_id": 0, "user_id": 1, "display_name": 1, "privacy_level": 1, "avatar_url": 1},
        ):
            profiles[p["user_id"]] = p
        for u in db.users.find(
            {"id": {"$in": user_ids}},
            {"_id": 0, "id": 1, "email": 1},
        ):
            users[u["id"]] = u

    public_rows = []
    for r in rows:
        uid = r.get("user_id")
        if not uid:
            continue
        profile = profiles.get(uid)
        if not _is_profile_public(profile):
            continue
        public_rows.append(r)

    # Un avis par utilisateur (le plus récent / avec texte prioritaire)
    by_user: Dict[str, Dict[str, Any]] = {}
    for r in public_rows:
        uid = r["user_id"]
        prev = by_user.get(uid)
        if not prev:
            by_user[uid] = r
            continue
        prev_has = bool(prev.get("review"))
        new_has = bool(r.get("review"))
        if new_has and not prev_has:
            by_user[uid] = r
        elif new_has == prev_has:
            # garder rating le plus élevé si égal
            if (r.get("rating") or 0) > (prev.get("rating") or 0):
                by_user[uid] = r

    merged = list(by_user.values())
    ratings = [r["rating"] for r in merged if r.get("rating") and r["rating"] > 0]
    average = round(sum(ratings) / len(ratings), 1) if ratings else None

    # Avis avec texte d'abord, puis notes seules
    with_text = [r for r in merged if r.get("review")]
    with_text.sort(key=lambda x: (x.get("date") or ""), reverse=True)
    reviews_out = []
    for r in with_text[:limit]:
        uid = r["user_id"]
        profile = profiles.get(uid)
        user = users.get(uid)
        date_val = r.get("date")
        if hasattr(date_val, "isoformat"):
            date_val = date_val.isoformat()
        reviews_out.append(
            {
                "user_id": uid,
                "display_name": _display_name(profile, user, uid),
                "avatar_url": (profile or {}).get("avatar_url"),
                "rating": r.get("rating"),
                "review": r.get("review"),
                "date": date_val,
                "is_mine": uid == current_user.get("id"),
            }
        )

    return {
        "average_rating": average,
        "ratings_count": len(ratings),
        "reviews_count": len(with_text),
        "reviews": reviews_out,
    }
