"""Enrichissement jaquette + résumé réel pour les fiches catalogue."""
from __future__ import annotations

import logging
import os
import re
from typing import Any

logger = logging.getLogger("booktime.catalog_media")

_TEMPLATE_BLURB = re.compile(
    r"^« .+ » est (le tome \d+ de la série|un (roman|manga|livre|bande dessinée))\b",
    re.I | re.S,
)

# Budgets à 0 par défaut (tests / import) — activés via reset_budgets() dans l'ingest.
_synopsis_budget = 0
_cover_lookup_budget = 0


def reset_budgets(*, synopsis: int | None = None, covers: int | None = None) -> None:
    global _synopsis_budget, _cover_lookup_budget
    if synopsis is not None:
        _synopsis_budget = max(0, int(synopsis))
    else:
        _synopsis_budget = _env_int("CATALOG_SYNOPSIS_LOOKUPS", 120, 0, 2000)
    if covers is not None:
        _cover_lookup_budget = max(0, int(covers))
    else:
        _cover_lookup_budget = _env_int("CATALOG_COVER_LOOKUPS", 200, 0, 2000)


def _env_int(name: str, default: int, lo: int, hi: int) -> int:
    try:
        v = int((os.getenv(name) or str(default)).strip())
    except Exception:
        v = default
    return max(lo, min(hi, v))


def is_template_blurb(text: str | None) -> bool:
    t = (text or "").strip()
    if not t:
        return True
    if _TEMPLATE_BLURB.match(t):
        return True
    # Anciens blurbs courts type « Titre » est un roman de X (genre, langue, année).
    if len(t) < 160 and " est un " in t and t.endswith("."):
        return True
    if len(t) < 180 and " est le tome " in t:
        return True
    return False


def primary_description(doc: dict[str, Any]) -> str:
    d = (doc.get("description") or "").strip()
    if d:
        return d
    details = doc.get("volume_details")
    if isinstance(details, dict):
        for key in sorted(details, key=lambda k: int(k) if str(k).isdigit() else 0):
            block = details.get(key) or {}
            if isinstance(block, dict):
                t = (block.get("description") or "").strip()
                if t:
                    return t
    return ""


def has_real_synopsis(doc: dict[str, Any]) -> bool:
    from app.utils.book_synopsis import is_usable_synopsis

    text = primary_description(doc)
    if not text or is_template_blurb(text):
        return False
    return is_usable_synopsis(text)


def _works_from_doc(doc: dict[str, Any]) -> list[dict[str, Any]]:
    details = doc.get("volume_details") if isinstance(doc.get("volume_details"), dict) else {}
    titles = doc.get("volume_titles") if isinstance(doc.get("volume_titles"), dict) else {}
    works: list[dict[str, Any]] = []
    for vn in sorted(details, key=lambda k: int(k) if str(k).isdigit() else 0):
        d = details.get(vn) or {}
        if not isinstance(d, dict):
            continue
        works.append(
            {
                "title": titles.get(vn) or doc.get("name") or "",
                "author": d.get("author") or ((doc.get("authors") or [""])[0] if doc.get("authors") else ""),
                "isbn": d.get("isbn") or "",
                "ol_key": d.get("ol_key") or "",
                "title_en": (doc.get("volume_titles_en") or {}).get(vn)
                if isinstance(doc.get("volume_titles_en"), dict)
                else "",
            }
        )
    if not works:
        authors = [a for a in (doc.get("authors") or []) if a]
        works = [
            {
                "title": doc.get("name") or "",
                "author": authors[0] if authors else "",
                "isbn": "",
                "ol_key": "",
            }
        ]
    return works


def _wiki_extract(title: str) -> str:
    """Extrait Wikipédia court (FR puis EN) — un seul essai par langue."""
    import requests
    from urllib.parse import quote

    headers = {"User-Agent": "BooktimeCatalog/1.0 (catalog enrichment)"}
    for lang in ("fr", "en"):
        slug = quote((title or "").strip().replace(" ", "_"))
        if not slug:
            continue
        url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{slug}"
        try:
            r = requests.get(url, timeout=6, headers=headers)
            if r.status_code != 200:
                continue
            extract = (r.json().get("extract") or "").strip()
            if len(extract) >= 60:
                return extract
        except Exception:
            continue
    return ""


def fetch_synopsis(
    *,
    title: str = "",
    author: str = "",
    isbn: str = "",
    ol_key: str = "",
    heavy: bool = False,
    prefer_back_cover: bool = True,
) -> tuple[str, str]:
    """Retourne (texte, source) ou ('', '').

    Priorité : 4ᵉ de couverture (Google Books / OL ISBN) → description OL work
    → Wikipédia → pipeline GB/FR complet si `heavy=True`.
    """
    global _synopsis_budget
    if _synopsis_budget <= 0:
        return "", ""
    _synopsis_budget -= 1
    try:
        from app.utils.book_synopsis import (
            _ol_key_from_search,
            _ol_work_description_only,
            fetch_back_cover_by_isbn,
            is_usable_synopsis,
        )

        # 1) Vrai texte de 4ᵉ (édition ISBN) — le plus proche du dos du livre
        if prefer_back_cover and (isbn or "").strip():
            bc, bsrc = fetch_back_cover_by_isbn(isbn)
            if is_usable_synopsis(bc) and not is_template_blurb(bc):
                return bc, bsrc or "back_cover"

        key = (ol_key or "").strip()
        if key and not key.startswith("/"):
            if key.startswith("OL") and key.endswith("W"):
                key = f"/works/{key}"
        if not key or "works/" not in key:
            key = _ol_key_from_search(title, author, language=None) or ""
        if key:
            ol_text = (_ol_work_description_only(key) or "").strip()
            if is_usable_synopsis(ol_text) and not is_template_blurb(ol_text):
                return ol_text, "openlibrary"

        wiki = _wiki_extract(title)
        if is_usable_synopsis(wiki) and not is_template_blurb(wiki):
            return wiki, "wikipedia"

        if heavy or prefer_back_cover:
            from app.utils.book_synopsis import fetch_book_synopsis

            got = fetch_book_synopsis(
                title=title or "",
                author=author or "",
                isbn=isbn or "",
                ol_key=key or ol_key or "",
                want_pages=False,
            )
            text = ((got or {}).get("description") or "").strip()
            src = (got or {}).get("source") or ""
            if is_usable_synopsis(text) and not is_template_blurb(text):
                return text, str(src)
    except Exception as exc:
        logger.debug("synopsis fail %s / %s : %s", title, author, exc)
    return "", ""


def apply_synopsis(doc: dict[str, Any], text: str, source: str = "") -> bool:
    text = (text or "").strip()
    if not text:
        return False
    doc["description"] = text
    if source:
        doc["summary_source"] = source
    doc["needs_summary"] = False
    details = doc.get("volume_details")
    if isinstance(details, dict) and details:
        # Tome 1 = résumé réel ; les autres gardent leur texte s'il est déjà réel
        first_key = sorted(details, key=lambda k: int(k) if str(k).isdigit() else 0)[0]
        block = details.get(first_key)
        if isinstance(block, dict):
            block["description"] = text
        for key, block in details.items():
            if key == first_key or not isinstance(block, dict):
                continue
            if is_template_blurb(block.get("description")):
                # ne pas dupliquer le même synopsis sur tous les tomes
                continue
    return True


def apply_cover(doc: dict[str, Any], cover: str) -> bool:
    from .daily_ingest import usable_cover

    cover = usable_cover(cover)
    if not cover:
        return False
    doc["cover_url"] = cover
    doc["needs_cover"] = False
    details = doc.get("volume_details")
    if isinstance(details, dict):
        for block in details.values():
            if isinstance(block, dict) and not usable_cover(block.get("cover_url")):
                block["cover_url"] = cover
    return True


def enrich_doc_media(doc: dict[str, Any], *, want_cover: bool = True, want_summary: bool = True) -> dict[str, bool]:
    """Complète jaquette et/ou résumé sur une fiche existante. Mutates doc."""
    from . import daily_pending
    from .daily_ingest import usable_cover, wiki_cover

    out = {"cover": False, "summary": False}
    works = _works_from_doc(doc)
    w0 = works[0] if works else {}

    if want_cover and not usable_cover(doc.get("cover_url")):
        global _cover_lookup_budget
        if _cover_lookup_budget > 0:
            _cover_lookup_budget -= 1
            cand = {
                "qid": doc.get("qid"),
                "name": doc.get("name"),
                "name_en": doc.get("name_en"),
                "author": w0.get("author") or "",
                "cover_url": doc.get("cover_url") or "",
                "isbn": w0.get("isbn") or "",
                "ol_key": w0.get("ol_key") or "",
            }
            daily_pending.enrich_work_candidate(cand, works)
            cover = usable_cover(cand.get("cover_url")) or wiki_cover(
                doc.get("name") or "", doc.get("name_en")
            )
            if apply_cover(doc, cover):
                out["cover"] = True
        doc.setdefault("needs_cover", not bool(usable_cover(doc.get("cover_url"))))
    elif usable_cover(doc.get("cover_url")):
        doc["needs_cover"] = False

    if want_summary and not has_real_synopsis(doc):
        authors = doc.get("authors") or []
        author = ""
        if isinstance(authors, list) and authors:
            author = str(authors[0] or "")
        author = author or w0.get("author") or ""
        isbn = (
            w0.get("isbn")
            or doc.get("isbn")
            or ""
        )
        ol_key = w0.get("ol_key") or doc.get("key") or ""
        qid = str(doc.get("qid") or "")
        if not ol_key and qid.startswith("OL") and qid.endswith("W"):
            ol_key = f"/works/{qid}"
        text, src = fetch_synopsis(
            title=w0.get("title") or doc.get("name") or "",
            author=author,
            isbn=isbn or "",
            ol_key=ol_key or "",
            heavy=True,
            prefer_back_cover=True,
        )
        if apply_synopsis(doc, text, src):
            out["summary"] = True
        else:
            doc["needs_summary"] = True
    elif has_real_synopsis(doc):
        doc["needs_summary"] = False

    return out


def mirror_to_sqlite(doc: dict[str, Any], *, synced: int = 0) -> None:
    try:
        from . import local_catalog_sqlite as local_cat

        if not local_cat.enabled():
            return
        local_cat.upsert_series([doc], synced=synced)
    except Exception as exc:
        logger.debug("mirror sqlite: %s", exc)

