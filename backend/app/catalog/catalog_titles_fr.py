"""Résolution de titres français pour le catalogue (hors ingest quotidien)."""
from __future__ import annotations

import logging
import re
import time
from typing import Any
from urllib.parse import quote

import requests

logger = logging.getLogger("booktime.catalog_titles_fr")

UA = {"User-Agent": "BooktimeTitleFr/1.0 (catalog; local backfill)"}
_FR_HINT = re.compile(
    r"[àâäéèêëïîôùûüçœæ]|(^|\b)(le|la|les|l'|l’|un|une|des|du)\b",
    re.I,
)
_SESSION = requests.Session()
_SESSION.headers.update(UA)


def looks_french(text: str | None) -> bool:
    return bool(_FR_HINT.search((text or "").strip()))


def needs_french_title(doc: dict[str, Any]) -> bool:
    """True si le titre affiché n'a pas l'air français."""
    name = (doc.get("name") or "").strip()
    if not name:
        return False
    if doc.get("title_fr") and looks_french(str(doc.get("title_fr"))):
        # déjà résolu
        if name == str(doc.get("title_fr")).strip():
            return False
    if looks_french(name):
        return False
    lang = str(doc.get("language") or "").lower()
    if lang.startswith("fr"):
        # langue FR mais titre sans indices — quand même tenter si name_en == name
        name_en = (doc.get("name_en") or "").strip()
        if name_en and name_en != name:
            return False
    return True


def alias_french_title(title: str) -> str:
    try:
        from app.utils.book_synopsis import _FR_TITLE_ALIASES, _normalize_title

        aliases = _FR_TITLE_ALIASES.get(_normalize_title(title) or "", ())
        for a in aliases:
            if a and a.strip() and a.strip().lower() != (title or "").lower() and looks_french(a):
                return a.strip()
    except Exception:
        pass
    return ""


def wikidata_labels_fr(qids: list[str]) -> dict[str, tuple[str, str]]:
    """qid -> (label_fr, label_en). Lots de 50."""
    out: dict[str, tuple[str, str]] = {}
    clean = [q for q in qids if q and q.startswith("Q") and q[1:].isdigit()]
    for i in range(0, len(clean), 50):
        batch = clean[i : i + 50]
        try:
            r = _SESSION.get(
                "https://www.wikidata.org/w/api.php",
                params={
                    "action": "wbgetentities",
                    "ids": "|".join(batch),
                    "props": "labels",
                    "languages": "fr|en",
                    "format": "json",
                },
                timeout=45,
            )
            if r.status_code != 200:
                time.sleep(1.5)
                continue
            entities = (r.json() or {}).get("entities") or {}
            for qid in batch:
                ent = entities.get(qid) or {}
                labels = ent.get("labels") or {}
                fr = ((labels.get("fr") or {}).get("value") or "").strip()
                en = ((labels.get("en") or {}).get("value") or "").strip()
                if fr:
                    out[qid] = (fr, en)
        except Exception as exc:
            logger.debug("wbgetentities: %s", exc)
            time.sleep(2)
        time.sleep(0.15)
    return out


def wikidata_fr_from_olid(olid: str) -> str:
    """P648 Open Library ID → label FR Wikidata."""
    key = (olid or "").strip()
    if key.startswith("/works/"):
        key = key.rsplit("/", 1)[-1]
    if not key.startswith("OL"):
        return ""
    try:
        r = _SESSION.get(
            "https://www.wikidata.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": f"haswbstatement:P648={key}",
                "srnamespace": "0",
                "srlimit": "1",
                "format": "json",
            },
            timeout=20,
        )
        if r.status_code != 200:
            return ""
        hits = ((r.json() or {}).get("query") or {}).get("search") or []
        if not hits:
            return ""
        # title is often "Q123" for item namespace? Actually display title; pageid better via title
        title = hits[0].get("title") or ""
        # Wikidata item pages are Q-ids
        qid = title if title.startswith("Q") else ""
        if not qid:
            # sometimes "Q42" in snippet — fallback parse
            m = re.search(r"\bQ\d+\b", str(hits[0]))
            qid = m.group(0) if m else ""
        if not qid:
            return ""
        got = wikidata_labels_fr([qid])
        fr = (got.get(qid) or ("", ""))[0]
        return fr if looks_french(fr) else fr
    except Exception as exc:
        logger.debug("WD P648 %s: %s", key, exc)
    return ""


def openlibrary_french_title(olid: str) -> str:
    """Titre d'une édition française Open Library pour une œuvre OL…W."""
    key = (olid or "").strip()
    if not key:
        return ""
    if key.startswith("/works/"):
        work_path = key
    elif key.startswith("OL") and key.endswith("W"):
        work_path = f"/works/{key}"
    elif key.startswith("OL") and key.endswith("M"):
        try:
            br = _SESSION.get(f"https://openlibrary.org/books/{key}.json", timeout=15)
            if br.status_code != 200:
                return ""
            works = (br.json() or {}).get("works") or []
            if not works:
                return ""
            wkey = works[0].get("key") if isinstance(works[0], dict) else ""
            if not wkey:
                return ""
            work_path = wkey if wkey.startswith("/") else f"/works/{wkey}"
        except Exception:
            return ""
    else:
        return ""

    for attempt in range(3):
        try:
            r = _SESSION.get(
                f"https://openlibrary.org{work_path}/editions.json",
                params={"limit": 25},
                timeout=20,
            )
            if r.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            if r.status_code != 200:
                return ""
            for ed in (r.json() or {}).get("entries") or []:
                langs = ed.get("languages") or []
                lang_keys = []
                for x in langs:
                    if isinstance(x, dict):
                        lang_keys.append(str(x.get("key") or ""))
                    else:
                        lang_keys.append(str(x))
                if not any("fre" in k for k in lang_keys):
                    continue
                title = (ed.get("title") or "").strip()
                if title and looks_french(title):
                    return title
            return ""
        except Exception as exc:
            logger.debug("OL editions %s: %s", key, exc)
            time.sleep(1.5 * (attempt + 1))
    return ""


def wikipedia_fr_title_from_en(title: str) -> str:
    """Langlink Wikipédia EN → titre d'article FR (souvent le titre FR de l'œuvre)."""
    t = (title or "").strip()
    if not t:
        return ""
    try:
        r = _SESSION.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "titles": t,
                "prop": "langlinks",
                "lllang": "fr",
                "format": "json",
                "redirects": 1,
            },
            timeout=15,
        )
        if r.status_code != 200:
            return ""
        pages = ((r.json() or {}).get("query") or {}).get("pages") or {}
        for page in pages.values():
            for ll in page.get("langlinks") or []:
                fr = (ll.get("*") or "").strip()
                # Enlever suffixe genre "(roman)" etc. parfois utile de garder
                if fr and fr.lower() != t.lower():
                    # nettoyer disambiguation
                    fr2 = re.sub(r"\s*\([^)]*(roman|novel|livre|film)[^)]*\)\s*$", "", fr, flags=re.I).strip()
                    return fr2 or fr
    except Exception as exc:
        logger.debug("wiki langlink: %s", exc)
    return ""


def resolve_french_title(doc: dict[str, Any]) -> tuple[str, str]:
    """Retourne (titre_fr, source) ou ('', '')."""
    name = (doc.get("name") or "").strip()
    qid = (doc.get("qid") or doc.get("wikidata_qid") or "").strip()

    alias = alias_french_title(name)
    if alias:
        return alias, "alias"

    if qid.startswith("Q") and qid[1:].isdigit():
        got = wikidata_labels_fr([qid])
        if qid in got:
            fr, en = got[qid]
            if fr and fr.lower() != name.lower():
                return fr, "wikidata"
            if fr and looks_french(fr):
                return fr, "wikidata"

    if qid.startswith("OL"):
        fr = openlibrary_french_title(qid)
        if fr and (looks_french(fr) or fr.lower() != name.lower()):
            if looks_french(fr) or fr != name:
                # n'accepter un titre identique non-FR que si vraiment édition FR
                if looks_french(fr) and fr.lower() != name.lower():
                    return fr, "openlibrary_edition"
                if looks_french(fr):
                    return fr, "openlibrary_edition"

    # Wikipédia langlinks (EN → FR)
    fr = wikipedia_fr_title_from_en(name)
    if fr and looks_french(fr) and fr.lower() != name.lower():
        return fr, "wikipedia_langlink"
    name_en = (doc.get("name_en") or "").strip()
    if name_en and name_en != name:
        fr = wikipedia_fr_title_from_en(name_en)
        if fr and looks_french(fr) and fr.lower() != name.lower():
            return fr, "wikipedia_langlink"

    return "", ""


def apply_french_title(doc: dict[str, Any], title_fr: str, source: str = "") -> bool:
    """Applique le titre FR sur la fiche (garde l'ancien dans name_en)."""
    fr = (title_fr or "").strip()
    if not fr:
        return False
    old = (doc.get("name") or "").strip()
    if not old:
        doc["name"] = fr
        doc["title_fr"] = fr
        if source:
            doc["title_fr_source"] = source
        return True
    if fr.lower() == old.lower():
        doc["title_fr"] = fr
        if source:
            doc["title_fr_source"] = source
        return False
    if not (doc.get("name_en") or "").strip():
        doc["name_en"] = old
    doc["name"] = fr
    doc["title_fr"] = fr
    if source:
        doc["title_fr_source"] = source
    # aligne tome 1 si c'était le même titre
    details = doc.get("volume_titles")
    if isinstance(details, dict):
        for k, v in list(details.items()):
            if str(v).strip() == old:
                details[k] = fr
    vd = doc.get("volume_details")
    if isinstance(vd, dict):
        # rien d'obligatoire sur description
        pass
    try:
        from app.static_wikidata.service import norm_title

        doc["name_norm"] = norm_title(fr)
    except Exception:
        pass
    return True
