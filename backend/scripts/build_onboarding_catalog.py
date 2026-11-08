"""
Génère backend/data/onboarding_catalog.json à partir de
onboarding_catalog_data.py : résout une couverture (et la clé Open Library)
pour chaque oeuvre.

Usage (depuis le dossier backend) :
    python scripts/build_onboarding_catalog.py            # complète les couvertures manquantes
    python scripts/build_onboarding_catalog.py --rebuild  # tout recalculer

Les couvertures déjà résolues sont conservées d'un lancement à l'autre.
"""
import json
import re
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from onboarding_catalog_data import ROMANS, GRAPHIC  # noqa: E402

DATA_DIR = HERE.parent / "data"
OUT = DATA_DIR / "onboarding_catalog.json"
MANGA_CACHE = DATA_DIR / "manga_bd_cache.json"

STOPWORDS = {
    "le", "la", "les", "l", "un", "une", "des", "de", "du", "d", "et", "the", "of", "a", "an",
    "and", "au", "aux", "en", "dans", "sur", "ou",
}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def tokens(s: str) -> set:
    return {t for t in norm(s).split() if t not in STOPWORDS and len(t) > 1}


def slug(s: str) -> str:
    return norm(s).replace(" ", "-")[:80]


def first_author(author: str) -> str:
    return re.split(r"\s*(?:&|,| et )\s*", author)[0].strip()


def ol_search(title: str, author: str, lang: str | None):
    params = {
        "title": title,
        "author": first_author(author),
        "limit": 8,
        "fields": "key,title,cover_i,author_name,first_publish_year,"
                  "editions,editions.key,editions.title,editions.cover_i,editions.language",
    }
    if lang:
        params["language"] = lang
    url = "https://openlibrary.org/search.json?" + urllib.parse.urlencode(params)
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "BooktimeOnboardingBuilder/1.0"})
            with urllib.request.urlopen(req, timeout=25) as r:
                return json.loads(r.read().decode("utf-8")).get("docs", [])
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return []


def pick(docs, wanted_title: str, french_only: bool):
    """
    Choisit la meilleure couverture. En mode « français », seules les éditions
    françaises de l'oeuvre sont retenues (sinon on obtiendrait des couvertures
    anglaises ou espagnoles du même titre).
    """
    want = tokens(wanted_title)
    if not want:
        return None
    best = None
    for d in docs:
        if french_only:
            eds = [
                e for e in (d.get("editions") or {}).get("docs", [])
                if e.get("cover_i") and "fre" in (e.get("language") or [])
            ]
            # édition uniquement française d'abord
            eds.sort(key=lambda e: 0 if (e.get("language") or []) == ["fre"] else 1)
            cover = eds[0]["cover_i"] if eds else None
            title = (eds[0].get("title") if eds else None) or d.get("title", "")
            title = d.get("title", "") if not title else title
        else:
            cover = d.get("cover_i")
            title = d.get("title", "")
        if not cover:
            continue
        got = tokens(title) | tokens(d.get("title", ""))
        overlap = len(want & got) / len(want)
        if overlap >= 0.6 and (best is None or overlap > best[0]):
            best = (overlap, d, cover)
    return (best[1], best[2]) if best else None


def resolve_ol(title: str, author: str, orig: str | None):
    short = re.split(r"\s+:\s+", title)[0]
    attempts = [(title, "fre"), (title, None)]
    if short != title:
        attempts += [(short, "fre"), (short, None)]
    if orig:
        attempts += [(orig, None)]
        if orig.endswith(" Wool") is False and re.split(r"\s*:\s*", orig)[0] != orig:
            attempts += [(re.split(r"\s*:\s*", orig)[0], None)]
    for t, lang in attempts:
        found = pick(ol_search(t, author, lang), t, french_only=bool(lang))
        time.sleep(0.25)
        if found:
            doc, cover_i = found
            return {
                "cover_url": f"https://covers.openlibrary.org/b/id/{cover_i}-M.jpg",
                "ol_key": doc.get("key"),
            }
    return None


_manga_index = None


def manga_cover(title: str, orig: str | None):
    global _manga_index
    if _manga_index is None:
        _manga_index = {}
        if MANGA_CACHE.exists():
            for b in json.load(open(MANGA_CACHE, encoding="utf-8")):
                if b.get("category") == "manga" and b.get("cover_url") and b.get("source") == "jikan_myanimelist":
                    _manga_index.setdefault(norm(b["title"]), b["cover_url"])
    for t in (title, orig):
        if t and norm(t) in _manga_index:
            return {"cover_url": _manga_index[norm(t)], "ol_key": None}
    return None


def main():
    rebuild = "--rebuild" in sys.argv
    previous = {}
    if OUT.exists():
        for w in json.load(open(OUT, encoding="utf-8")).get("works", []):
            previous[w["id"]] = w

    entries = []
    for title, author, genre, orig in ROMANS:
        entries.append((title, author, genre, orig, "roman", "roman"))
    for title, author, genre, orig, cat in GRAPHIC:
        entries.append((title, author, genre, orig, cat, "graphic_novel"))

    works = []
    missing = 0
    for i, (title, author, genre, orig, cat, group) in enumerate(entries, 1):
        wid = f"{group}-{slug(title)}"
        old = previous.get(wid)
        cover = None
        if old and old.get("cover_url") and not rebuild:
            cover = {"cover_url": old["cover_url"], "ol_key": old.get("ol_key")}
        else:
            if cat == "manga":
                cover = manga_cover(title, orig)
            if cover is None:
                cover = resolve_ol(title, author, orig)
            if cover is None and cat != "manga":
                cover = manga_cover(title, orig)
        if cover is None and old and old.get("cover_url"):
            # la nouvelle résolution n'a rien trouvé : on garde l'ancienne couverture
            cover = {"cover_url": old["cover_url"], "ol_key": old.get("ol_key")}
        if cover is None:
            missing += 1
        works.append({
            "id": wid,
            "title": title,
            "author": author,
            "genre": genre,
            "category": cat,
            "group": group,
            "cover_url": (cover or {}).get("cover_url", ""),
            "ol_key": (cover or {}).get("ol_key"),
        })
        if i % 20 == 0:
            print(f"{i}/{len(entries)} (sans couverture : {missing})", flush=True)

    OUT.write_text(json.dumps({"version": 1, "works": works}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Terminé : {len(works)} oeuvres, {missing} sans couverture -> {OUT}")


if __name__ == "__main__":
    main()
