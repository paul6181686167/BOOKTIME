"""
DEMO Wikidata -- Detection de serie pour BOOKTIME
Utilise l'API REST Wikidata (pas SPARQL) pour eviter les timeouts.
Lance avec : python demo_wikidata.py
"""
import sys, os
import requests, time

SEARCH_URL  = "https://www.wikidata.org/w/api.php"
ENTITY_URL  = "https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
LABEL_URL   = "https://www.wikidata.org/w/api.php"
HEADERS     = {"User-Agent": "BooktimeDemo/1.0"}

P_SERIES    = "P179"   # part of the series
P_ORDINAL   = "P1545"  # series ordinal (volume number)

TEST_BOOKS = [
    {"title": "The Fellowship of the Ring",              "author": "J.R.R. Tolkien",   "expected": "SdA tome 1"},
    {"title": "Golden Son",                              "author": "Pierce Brown",      "expected": "Red Rising tome 2"},
    {"title": "Harry Potter and the Chamber of Secrets", "author": "J.K. Rowling",     "expected": "Harry Potter tome 2"},
    {"title": "The Running Man",                         "author": "Stephen King",      "expected": "standalone"},
    {"title": "Dune",                                    "author": "Frank Herbert",     "expected": "Dune tome 1"},
    {"title": "Morning Star",                            "author": "Pierce Brown",      "expected": "Red Rising tome 3"},
    {"title": "The Name of the Wind",                    "author": "Patrick Rothfuss",  "expected": "Kingkiller tome 1"},
    {"title": "1984",                                    "author": "George Orwell",     "expected": "standalone"},
    {"title": "Hunger Games",                            "author": "Suzanne Collins",   "expected": "Hunger Games tome 1"},
]


def search_entity(title):
    """Cherche une entite Wikidata par titre, retourne la liste de candidats."""
    r = requests.get(SEARCH_URL, params={
        "action": "wbsearchentities",
        "search": title,
        "language": "en",
        "type": "item",
        "limit": 5,
        "format": "json",
    }, headers=HEADERS, timeout=10)
    if not r.ok:
        return []
    return r.json().get("search", [])


def get_entity_data(qid):
    """Recupere les donnees completes d'une entite Wikidata."""
    r = requests.get(ENTITY_URL.format(qid=qid), headers=HEADERS, timeout=10)
    if not r.ok:
        return None
    data = r.json()
    return data.get("entities", {}).get(qid)


def get_label(qid, lang="fr"):
    """Recupere le label d'un QID dans la langue demandee."""
    # Essaie d'abord via entity data (plus fiable)
    entity = get_entity_data(qid)
    if entity:
        labels = entity.get("labels", {})
        for l in [lang, "en", "fr"]:
            if l in labels:
                return labels[l]["value"]
    # Fallback via wbgetentities
    r = requests.get(LABEL_URL, params={
        "action": "wbgetentities",
        "ids": qid,
        "props": "labels",
        "languages": f"{lang}|en|fr",
        "format": "json",
    }, headers=HEADERS, timeout=8)
    if not r.ok:
        return qid
    ent = r.json().get("entities", {}).get(qid, {})
    labels = ent.get("labels", {})
    for l in [lang, "en", "fr"]:
        if l in labels:
            return labels[l]["value"]
    return qid


def extract_series_info(entity):
    """Extrait P179 (serie) et P1545 (numero) depuis les claims d'une entite."""
    claims = entity.get("claims", {})
    series_claims = claims.get(P_SERIES, [])
    if not series_claims:
        return None, None
    # Prend la premiere serie
    series_claim = series_claims[0]
    series_qid = series_claim.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id")
    # Cherche le numero de volume dans les qualifiers
    volume = None
    qualifiers = series_claim.get("qualifiers", {})
    ordinal_claims = qualifiers.get(P_ORDINAL, [])
    if ordinal_claims:
        volume = ordinal_claims[0].get("datavalue", {}).get("value")
    return series_qid, volume


def is_book_entity(candidate, entity):
    """Verifie que l'entite est bien un livre (heuristique sur la description)."""
    desc = (candidate.get("description") or "").lower()
    book_kw = ["novel", "book", "manga", "comic", "roman", "livre",
               "fantasy", "fiction", "story", "series", "science", "short"]
    if any(k in desc for k in book_kw):
        return True
    # Verifie P31 (instance of) : Q7725634=literary work, Q571=book, Q8274=manga
    claims = entity.get("claims", {}) if entity else {}
    p31 = claims.get("P31", [])
    book_types = {"Q7725634", "Q571", "Q8274", "Q2831984", "Q47461344",
                  "Q277759", "Q1266946", "Q3331189", "Q7366"}
    for c in p31:
        val = c.get("mainsnak", {}).get("datavalue", {}).get("value", {})
        if isinstance(val, dict) and val.get("id") in book_types:
            return True
    return False


def detect_series(title):
    # Essaie le titre original puis avec "The " en prefixe si pas de resultat
    variants = [title]
    if not title.lower().startswith("the "):
        variants.append("The " + title)
    if title.lower().startswith("the "):
        variants.append(title[4:])  # essaie sans "The"

    candidates = []
    for variant in variants:
        candidates = search_entity(variant)
        if candidates:
            break
    if not candidates:
        return {"status": "not_found"}

    for candidate in candidates[:5]:
        qid = candidate["id"]
        entity = get_entity_data(qid)
        time.sleep(0.2)
        if not entity:
            continue
        if not is_book_entity(candidate, entity):
            continue

        series_qid, volume = extract_series_info(entity)
        if series_qid:
            series_name = get_label(series_qid, "fr")
            time.sleep(0.2)
            return {
                "status": "series",
                "book_label": candidate.get("label", title),
                "book_qid": qid,
                "series_name": series_name,
                "series_qid": series_qid,
                "volume": volume,
            }
        else:
            return {
                "status": "standalone",
                "book_label": candidate.get("label", title),
                "book_qid": qid,
            }

    return {"status": "not_found"}


# ── Execution ──────────────────────────────────────────────────────────────────
print()
print("=" * 70)
print("  DEMO WIKIDATA -- Detection de serie BOOKTIME")
print("=" * 70)

ok = err = standalone = series_ok = 0
for book in TEST_BOOKS:
    print(f"\n>>> \"{book['title']}\" -- {book['author']}")
    print(f"    Attendu  : {book['expected']}")
    try:
        res = detect_series(book["title"])
        if res["status"] == "series":
            vol = f", tome {res['volume']}" if res.get("volume") else ""
            print(f"    Wikidata : SERIE -- \"{res['series_name']}\"{vol}  (livre QID: {res['book_qid']})")
            series_ok += 1
        elif res["status"] == "standalone":
            print(f"    Wikidata : STANDALONE -- \"{res['book_label']}\"  (QID: {res['book_qid']})")
            standalone += 1
        else:
            print(f"    Wikidata : NON TROUVE")
            err += 1
        ok += 1
    except Exception as e:
        print(f"    ERREUR   : {e}")
        err += 1
    time.sleep(0.3)

print()
print("=" * 70)
print(f"  Resultat : {ok}/{len(TEST_BOOKS)} traites | {series_ok} series | {standalone} standalone | {err} erreurs")
print("=" * 70)
print()
