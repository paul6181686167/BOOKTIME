"""
Recherche d'un livre par ISBN, avec plusieurs sources en cascade.

Open Library connaît mal les éditions françaises récentes : on enchaîne donc
Open Library, Google Books (si une clé est configurée), puis le catalogue de la BnF.
"""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)

_UA = {"User-Agent": "Booktime/1.0 (isbn)"}
_DC = "{http://purl.org/dc/elements/1.1/}"


def clean_isbn(raw: str) -> str:
    return "".join(c for c in (raw or "") if c.isdigit() or c.upper() == "X").upper()


def is_valid_isbn(isbn: str) -> bool:
    """Vérifie la longueur et la clé de contrôle (ISBN-10 ou ISBN-13)."""
    if len(isbn) == 13 and isbn.isdigit():
        total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(isbn[:12]))
        return (10 - total % 10) % 10 == int(isbn[12])
    if len(isbn) == 10 and isbn[:9].isdigit() and (isbn[9].isdigit() or isbn[9] == "X"):
        total = sum(int(d) * (10 - i) for i, d in enumerate(isbn[:9]))
        total += 10 if isbn[9] == "X" else int(isbn[9])
        return total % 11 == 0
    return False


def isbn10_to_13(isbn10: str) -> str:
    core = "978" + isbn10[:9]
    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(core))
    return core + str((10 - total % 10) % 10)


def isbn13_to_10(isbn13: str) -> str:
    if not isbn13.startswith("978"):
        return ""
    core = isbn13[3:12]
    total = sum(int(d) * (10 - i) for i, d in enumerate(core))
    check = (11 - total % 11) % 11
    return core + ("X" if check == 10 else str(check))


def isbn_variants(isbn: str) -> list[str]:
    """ISBN saisi + sa version 10/13 : certaines bases n'indexent qu'une des deux."""
    out = [isbn]
    try:
        if len(isbn) == 10 and isbn[:9].isdigit():
            out.append(isbn10_to_13(isbn))
        elif len(isbn) == 13 and isbn.isdigit():
            alt = isbn13_to_10(isbn)
            if alt:
                out.append(alt)
    except ValueError:
        pass
    return out


def _book(
    *,
    isbn: str,
    title: str,
    author: str = "",
    cover_url: str = "",
    publisher: str = "",
    year: Any = None,
    pages: Any = None,
    subjects: Optional[list] = None,
    ol_key: str = "",
    description: str = "",
    source: str = "",
    category: str = "roman",
) -> dict[str, Any]:
    try:
        pages_i = int(pages) if pages else None
    except (TypeError, ValueError):
        pages_i = None
    return {
        "ol_key": ol_key,
        "title": title.strip(),
        "author": author.strip() or "Auteur inconnu",
        "category": category,
        # Vide si inconnue : lookup_book_by_isbn cherche ensuite une couverture réelle
        "cover_url": (cover_url or "").replace("http://", "https://"),
        "first_publish_year": year,
        "isbn": isbn,
        "subjects": (subjects or [])[:5],
        "number_of_pages": pages_i,
        "total_pages": pages_i,
        "publisher": publisher,
        "description": description,
        "source": source,
    }


# ── Open Library ───────────────────────────────────────────────────────────

def _from_open_library(isbn: str, detect_category) -> Optional[dict]:
    try:
        resp = requests.get(
            "https://openlibrary.org/api/books",
            params={"bibkeys": f"ISBN:{isbn}", "jscmd": "data", "format": "json"},
            timeout=10,
            headers=_UA,
        )
        if resp.status_code != 200:
            return None
        entry = (resp.json() or {}).get(f"ISBN:{isbn}") or {}
        if not entry.get("title"):
            return None
        authors = [a.get("name", "") for a in (entry.get("authors") or []) if a.get("name")]
        cover = (entry.get("cover") or {}).get("medium") or (entry.get("cover") or {}).get("large")
        subjects = [
            s.get("name", s) if isinstance(s, dict) else str(s)
            for s in (entry.get("subjects") or [])[:8]
        ]
        ol_key = ""
        try:
            sr = requests.get(
                "https://openlibrary.org/search.json",
                params={"isbn": isbn, "limit": 1, "fields": "key,title"},
                timeout=8,
                headers=_UA,
            )
            if sr.status_code == 200:
                docs = (sr.json() or {}).get("docs") or []
                if docs:
                    ol_key = docs[0].get("key") or ""
        except requests.RequestException:
            pass
        if not ol_key:
            ids = (entry.get("identifiers") or {}).get("openlibrary") or []
            if ids:
                ol_key = f"/books/{ids[0]}"
        return _book(
            isbn=isbn,
            title=entry.get("title") or "",
            author=", ".join(authors),
            cover_url=cover or "",
            publisher=", ".join(
                p.get("name", p) if isinstance(p, dict) else str(p)
                for p in (entry.get("publishers") or [])
            ),
            year=(entry.get("publish_date") or "")[-4:] or None,
            pages=entry.get("number_of_pages"),
            subjects=subjects,
            ol_key=ol_key,
            source="openlibrary",
            category=detect_category(subjects),
        )
    except (requests.RequestException, ValueError) as exc:
        logger.debug("ISBN OL api/books échec %s: %s", isbn, exc)
        return None


def _from_open_library_edition(isbn: str, detect_category) -> Optional[dict]:
    try:
        resp = requests.get(f"https://openlibrary.org/isbn/{isbn}.json", timeout=10, headers=_UA)
        if resp.status_code != 200:
            return None
        data = resp.json() or {}
        title = data.get("title") or ""
        if not title:
            return None
        work_key = (data.get("works") or [{}])[0].get("key", "")
        work = {}
        if work_key:
            wr = requests.get(f"https://openlibrary.org{work_key}.json", timeout=8, headers=_UA)
            if wr.status_code == 200:
                work = wr.json() or {}
        names = []
        for author in data.get("authors") or []:
            if not author.get("key"):
                continue
            try:
                ar = requests.get(f"https://openlibrary.org{author['key']}.json", timeout=6, headers=_UA)
                if ar.status_code == 200:
                    names.append(ar.json().get("name", ""))
            except requests.RequestException:
                pass
        covers = data.get("covers") or []
        cover = f"https://covers.openlibrary.org/b/id/{covers[0]}-M.jpg" if covers else ""
        subjects = work.get("subjects") or []
        return _book(
            isbn=isbn,
            title=work.get("title") or title,
            author=", ".join(n for n in names if n),
            cover_url=cover,
            publisher=", ".join(data.get("publishers") or []),
            year=(data.get("publish_date") or "")[-4:] or None,
            pages=data.get("number_of_pages"),
            subjects=subjects,
            ol_key=work_key,
            source="openlibrary",
            category=detect_category(subjects),
        )
    except (requests.RequestException, ValueError) as exc:
        logger.debug("ISBN OL isbn.json échec %s: %s", isbn, exc)
        return None


# ── Google Books ───────────────────────────────────────────────────────────

def _from_google_books(isbn: str, detect_category) -> Optional[dict]:
    try:
        from ..google_books import service as gb

        if not gb.is_enabled():
            return None
        result = gb.lookup_isbn(isbn, max_results=3)
        items = result.get("items") or []
        if not items:
            return None
        it = items[0]
        title = (it.get("title") or "").strip()
        if not title:
            return None
        sub = (it.get("subtitle") or "").strip()
        thumb = (it.get("thumbnail") or "").replace("http://", "https://")
        return _book(
            isbn=isbn,
            title=title,
            author=", ".join(it.get("authors") or []),
            cover_url=thumb,
            publisher=it.get("publisher") or "",
            year=str(it.get("published_date") or "")[:4] or None,
            pages=it.get("page_count"),
            subjects=it.get("categories") or [],
            description=(it.get("description") or "")[:2000] or sub,
            source="google_books",
            category=gb.infer_book_category_from_google_item(it),
        )
    except Exception as exc:  # pragma: no cover - API externe
        logger.debug("ISBN Google Books échec %s: %s", isbn, exc)
        return None


# ── BnF ────────────────────────────────────────────────────────────────────

def _bnf_text(node: Optional[ET.Element]) -> str:
    return (node.text or "").strip() if node is not None else ""


def _clean_bnf_title(raw: str) -> str:
    # « Memory / Arnaud Delalande » → « Memory »
    title = raw.split(" / ")[0].strip()
    return re.sub(r"\s+\[[^\]]*\]$", "", title)


def _clean_bnf_author(raw: str) -> str:
    # « Delalande, Arnaud (1971-....). Auteur du texte » → « Arnaud Delalande »
    name = re.sub(r"\s*\([^)]*\)", "", raw)
    name = name.split(". ")[0].strip().rstrip(".")
    if "," in name:
        last, first = [p.strip() for p in name.split(",", 1)]
        name = f"{first} {last}".strip()
    return name


def _from_bnf(isbn: str) -> Optional[dict]:
    try:
        resp = requests.get(
            "https://catalogue.bnf.fr/api/SRU",
            params={
                "version": "1.2",
                "operation": "searchRetrieve",
                "query": f'bib.isbn adj "{isbn}"',
                "recordSchema": "dublincore",
                "maximumRecords": "1",
            },
            timeout=10,
            headers=_UA,
        )
        if resp.status_code != 200:
            return None
        root = ET.fromstring(resp.content)
        dc = root.find(".//{http://www.openarchives.org/OAI/2.0/oai_dc/}dc")
        if dc is None:
            return None
        title = _clean_bnf_title(_bnf_text(dc.find(f"{_DC}title")))
        if not title:
            return None
        creators = [_clean_bnf_author(_bnf_text(c)) for c in dc.findall(f"{_DC}creator")]
        creators = [c for c in creators if c]
        publisher = re.sub(r"\s*\([^)]*\)$", "", _bnf_text(dc.find(f"{_DC}publisher")))
        date = _bnf_text(dc.find(f"{_DC}date"))
        pages = None
        for fmt in dc.findall(f"{_DC}format"):
            m = re.search(r"(\d{2,5})\s*p\.", _bnf_text(fmt))
            if m:
                pages = int(m.group(1))
                break
        return _book(
            isbn=isbn,
            title=title,
            author=creators[0] if creators else "",
            publisher=publisher,
            year=date[:4] if date[:4].isdigit() else None,
            pages=pages,
            source="bnf",
        )
    except (requests.RequestException, ET.ParseError, ValueError) as exc:
        logger.debug("ISBN BnF échec %s: %s", isbn, exc)
        return None


# ── Couverture ─────────────────────────────────────────────────────────────

def _is_real_image(url: str) -> bool:
    """Vrai si l'adresse renvoie bien une image (Open Library répond 404 avec default=false)."""
    try:
        resp = requests.get(url, timeout=5, headers=_UA, stream=True, allow_redirects=True)
        try:
            ctype = (resp.headers.get("Content-Type") or "").lower()
            return resp.status_code == 200 and ctype.startswith("image/")
        finally:
            resp.close()
    except requests.RequestException:
        return False


def find_cover(found: dict, variants: list[str]) -> str:
    """Couverture réellement disponible : celle de la source, sinon Open Library, sinon Google Books."""
    current = (found.get("cover_url") or "").strip()
    if current:
        return current
    for variant in variants:
        url = f"https://covers.openlibrary.org/b/isbn/{variant}-M.jpg?default=false"
        if _is_real_image(url):
            return url
    if found.get("source") != "google_books":
        for variant in variants:
            google = _from_google_books(variant, lambda _subjects: "roman")
            thumb = (google or {}).get("cover_url") or ""
            if thumb:
                return thumb
    return ""


def lookup_book_by_isbn(isbn: str, detect_category) -> Optional[dict]:
    """Renvoie le meilleur résultat parmi les sources, ou None."""
    clean = clean_isbn(isbn)
    variants = isbn_variants(clean)
    found: Optional[dict] = None

    for variant in variants:
        found = _from_open_library(variant, detect_category)
        if found:
            break
    if not found:
        for variant in variants:
            found = _from_open_library_edition(variant, detect_category)
            if found:
                break
    if not found:
        for variant in variants:
            found = _from_google_books(variant, detect_category)
            if found:
                break
    if not found:
        for variant in variants:
            found = _from_bnf(variant)
            if found:
                break

    if not found:
        return None
    found["isbn"] = clean
    # Complète auteur / pages / éditeur manquants avec la BnF (très complète pour le français)
    if found.get("source") != "bnf" and (
        found.get("author") in ("", "Auteur inconnu") or not found.get("total_pages")
    ):
        extra = None
        for variant in variants:
            extra = _from_bnf(variant)
            if extra:
                break
        if extra:
            if found.get("author") in ("", "Auteur inconnu") and extra.get("author") != "Auteur inconnu":
                found["author"] = extra["author"]
            if not found.get("total_pages") and extra.get("total_pages"):
                found["total_pages"] = extra["total_pages"]
                found["number_of_pages"] = extra["total_pages"]
            if not found.get("publisher") and extra.get("publisher"):
                found["publisher"] = extra["publisher"]
    found["cover_url"] = find_cover(found, variants)
    return found
