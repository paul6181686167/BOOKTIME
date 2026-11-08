"""Enrichit une fiche bibliothèque avec le noyau curé (50 000 + overlay riche)."""
from __future__ import annotations

from typing import Any

from ..series_verification.curated import curated_to_source_rows, match_curated
from ..series_verification.consensus import normalize_title_key


def _blank(v: Any) -> bool:
    return v is None or (isinstance(v, str) and not str(v).strip())


def _is_generic_volume_title(title: str, series_name: str) -> bool:
    t = (title or "").strip()
    if not t:
        return True
    if t.lower().startswith("tome "):
        return True
    sn = (series_name or "").strip()
    if sn and t.lower().startswith(sn.lower()) and "tome" in t.lower():
        return True
    return False


def _is_generic_series_description(desc: str) -> bool:
    d = (desc or "").strip()
    if not d:
        return True
    return d.startswith("Série de ") or d.startswith("Série roman") or d.startswith("Série manga")


def _volume_number_for_title(entry: dict[str, Any], title: str) -> int | None:
    q = normalize_title_key(title or "")
    if not q or len(q) < 4:
        return None
    for row in entry.get("volume_titles") or []:
        if not isinstance(row, dict):
            continue
        tn = normalize_title_key(row.get("title") or "")
        if not tn:
            continue
        if tn == q or (len(q) >= 6 and (q in tn or tn in q)):
            try:
                return int(row.get("volume_number"))
            except (TypeError, ValueError):
                return None
    return None


def _details_for(entry: dict[str, Any], volume_number: int | None) -> dict[str, Any]:
    details = entry.get("volume_details") or {}
    if volume_number is None:
        return {}
    raw = details.get(str(volume_number)) or details.get(volume_number) or {}
    return raw if isinstance(raw, dict) else {}


def hydrate_series_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Complète une série à insérer en bibliothèque à partir du noyau curé."""
    out = dict(data or {})
    name = (out.get("series_name") or out.get("name") or "").strip()
    if not name:
        return out
    authors = list(out.get("authors") or [])
    author = authors[0] if authors else out.get("author")
    entry = match_curated(name, author) or match_curated(name)
    if not entry:
        return out

    out["series_name"] = entry.get("name") or name
    out["name"] = out["series_name"]
    if not authors and entry.get("authors"):
        out["authors"] = list(entry["authors"])
    if _blank(out.get("author")) and (out.get("authors") or [None])[0]:
        out["author"] = out["authors"][0]
    if _blank(out.get("category")) and entry.get("category"):
        out["category"] = entry["category"]
    if _blank(out.get("publisher")):
        out["publisher"] = entry.get("publisher") or ""
    if _blank(out.get("cover_image_url")):
        out["cover_image_url"] = entry.get("cover_url") or out.get("cover_url") or ""
    if _blank(out.get("first_published")) and entry.get("first_published"):
        out["first_published"] = str(entry["first_published"])
    if _blank(out.get("genre")):
        out["genre"] = entry.get("genre") or ""
    if _blank(out.get("language")):
        out["language"] = entry.get("language") or ""
    if _blank(out.get("wikidata_qid")):
        out["wikidata_qid"] = entry.get("wikidata_qid") or ""

    curated_rows = curated_to_source_rows(entry)
    incoming = [v for v in (out.get("volumes") or []) if isinstance(v, dict)]
    titled_incoming = sum(
        1 for v in incoming if not _is_generic_volume_title(v.get("volume_title") or "", out["series_name"])
    )
    if curated_rows and (not incoming or titled_incoming < max(2, len(curated_rows) // 3) or len(incoming) < len(curated_rows)):
        prev = {}
        for v in incoming:
            try:
                prev[int(v.get("volume_number"))] = v
            except (TypeError, ValueError):
                continue
        new_vols = []
        for row in curated_rows:
            n = int(row["volume_number"])
            old = prev.get(n) or {}
            details = _details_for(entry, n)
            title = (row.get("title") or "").strip() or old.get("volume_title") or f"{out['series_name']} - Tome {n}"
            item = {
                "volume_number": n,
                "volume_title": title,
                "is_read": bool(old.get("is_read")),
                "date_read": old.get("date_read"),
                "rating": old.get("rating"),
                "review": old.get("review"),
            }
            if details.get("cover_url"):
                item["cover_url"] = details["cover_url"]
            if details.get("isbn"):
                item["isbn"] = details["isbn"]
            if details.get("published_year"):
                item["published_year"] = details["published_year"]
            if details.get("ol_key"):
                item["ol_key"] = details["ol_key"]
            if details.get("author"):
                item["author"] = details["author"]
            if details.get("genre"):
                item["genre"] = details["genre"]
            if details.get("language"):
                item["language"] = details["language"]
            if details.get("description"):
                item["description"] = details["description"]
            if details.get("pages"):
                item["pages"] = details["pages"]
                item["total_pages"] = details["pages"]
            new_vols.append(item)
        out["volumes"] = new_vols
        out["total_volumes"] = len(new_vols)
        if _blank(out.get("cover_image_url")) and new_vols:
            out["cover_image_url"] = new_vols[0].get("cover_url") or ""

    if _is_generic_series_description(out.get("description_fr") or ""):
        bits = [
            entry.get("genre"),
            entry.get("language"),
            f"{out.get('total_volumes') or len(out.get('volumes') or [])} tome(s)",
        ]
        out["description_fr"] = " · ".join(str(b) for b in bits if b)

    out["curated_source"] = entry.get("source") or "curated_core"
    return out


def hydrate_book_dict(book: dict[str, Any]) -> dict[str, Any]:
    """Complète un livre importé s'il appartient au noyau curé."""
    out = dict(book or {})
    title = (out.get("title") or out.get("display_title") or "").strip()
    saga = (out.get("saga") or "").strip()
    author = out.get("author")
    entry = None
    if saga:
        entry = match_curated(saga, author) or match_curated(saga)
    if entry is None and title:
        entry = match_curated(title, author) or match_curated(title)
    if not entry:
        return out

    out["saga"] = entry.get("name") or saga or title
    vol_n = out.get("volume_number")
    try:
        vol_n = int(vol_n) if vol_n not in (None, "") else None
    except (TypeError, ValueError):
        vol_n = None
    if vol_n is None:
        vol_n = _volume_number_for_title(entry, title)
        if vol_n:
            out["volume_number"] = vol_n
    details = _details_for(entry, vol_n)
    if _blank(out.get("author")) and (entry.get("authors") or [None])[0]:
        out["author"] = entry["authors"][0]
    if _blank(out.get("publisher")):
        out["publisher"] = details.get("publisher") or entry.get("publisher") or ""
    if _blank(out.get("genre")):
        out["genre"] = entry.get("genre") or ""
    if _blank(out.get("cover_url")):
        out["cover_url"] = details.get("cover_url") or entry.get("cover_url") or ""
    if _blank(out.get("isbn")) and details.get("isbn"):
        out["isbn"] = details["isbn"]
    if not out.get("publication_year") and details.get("published_year"):
        out["publication_year"] = details["published_year"]
    if not (out.get("total_pages") or 0) and details.get("pages"):
        out["total_pages"] = details["pages"]
    if _blank(out.get("description")) and details.get("description"):
        out["description"] = details["description"]
    if _blank(out.get("language")) and entry.get("language"):
        lang = entry["language"]
        out["language"] = "fr" if lang == "français" else lang
    if _blank(out.get("category")) and entry.get("category"):
        out["category"] = entry["category"]
    if details.get("ol_key") and _blank(out.get("ol_key")):
        out["ol_key"] = details["ol_key"]
    out["wikidata_qid"] = out.get("wikidata_qid") or entry.get("wikidata_qid")
    out["curated_source"] = entry.get("source") or "curated_core"
    return out
