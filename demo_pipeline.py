"""
DEMO PIPELINE COMPLET -- Detection de serie BOOKTIME
Architecture en 3 couches :
  1. Base statique locale  (EXTENDED_SERIES_DATABASE simplifie)
  2. Wikidata              (fallback, mis en cache)
  3. Champ saga OL         (deja disponible dans les resultats OL)

Aucune modification de l'appli. Lance avec : python demo_pipeline.py
"""
import sys, requests, time, json, unicodedata, re
from pathlib import Path

# ─── Cache fichier local (simule MongoDB) ─────────────────────────────────────
CACHE_FILE = Path("demo_series_cache.json")

def cache_load():
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    return {}

def cache_save(data):
    CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

CACHE = cache_load()

# ─── Base statique (extrait de EXTENDED_SERIES_DATABASE) ──────────────────────
# Format : { "nom_normalise": { name, volume_titles: {titre_normalise: num}, variations } }
STATIC_DB = {
    "harry potter": {
        "name": "Harry Potter",
        "volumes": {"harry potter a lecole des sorciers": 1, "harry potter et la chambre des secrets": 2,
                    "harry potter et le prisonnier dazkaban": 3, "harry potter et la coupe de feu": 4,
                    "harry potter et lordre du phenix": 5, "harry potter et le prince de sang mele": 6,
                    "harry potter et les reliques de la mort": 7,
                    "harry potter and the philosophers stone": 1, "harry potter and the chamber of secrets": 2,
                    "harry potter and the prisoner of azkaban": 3, "harry potter and the goblet of fire": 4,
                    "harry potter and the order of the phoenix": 5, "harry potter and the half blood prince": 6,
                    "harry potter and the deathly hallows": 7},
        "keywords": ["harry potter", "poudlard", "hogwarts", "voldemort"],
        "variations": ["harry potter", "hp"],
    },
    "le seigneur des anneaux": {
        "name": "Le Seigneur des Anneaux",
        "volumes": {"la communaute de lanneau": 1, "the fellowship of the ring": 1,
                    "les deux tours": 2, "the two towers": 2,
                    "le retour du roi": 3, "the return of the king": 3},
        "keywords": ["seigneur des anneaux", "lord of the rings", "tolkien", "frodon"],
        "variations": ["lord of the rings", "lotr", "sda"],
    },
    "red rising": {
        "name": "Red Rising",
        "volumes": {"red rising": 1, "golden son": 2, "morning star": 3},
        "keywords": ["red rising", "darrow", "pierce brown"],
        "variations": ["red rising trilogy"],
    },
    "dune": {
        "name": "Dune",
        "volumes": {"dune": 1, "le messie de dune": 2, "les enfants de dune": 3,
                    "dune messiah": 2, "children of dune": 3},
        "keywords": ["arrakis", "paul atreides", "fremen", "epice", "spice"],
        "variations": ["cycle de dune"],
    },
    "hunger games": {
        "name": "Hunger Games",
        "volumes": {"hunger games": 1, "the hunger games": 1, "embrasement": 2,
                    "catching fire": 2, "revolte": 3, "mockingjay": 3},
        "keywords": ["katniss", "panem", "mockingjay"],
        "variations": ["jeux de la faim"],
    },
    "chronique du tueur de roi": {
        "name": "Chronique du Tueur de Roi",
        "volumes": {"the name of the wind": 1, "le nom du vent": 1,
                    "the wise mans fear": 2, "la peur du sage": 2},
        "keywords": ["kvothe", "rothfuss", "kingkiller"],
        "variations": ["name of the wind", "kingkiller chronicle"],
    },
    "fondation": {
        "name": "Fondation",
        "volumes": {"fondation": 1, "foundation": 1, "fondation et empire": 2,
                    "foundation and empire": 2, "seconde fondation": 3, "second foundation": 3},
        "keywords": ["asimov", "psychohistoire", "hari seldon", "seldon"],
        "variations": ["foundation", "cycle fondation"],
    },
    "witcher": {
        "name": "The Witcher",
        "volumes": {"the last wish": 1, "le dernier voeu": 1, "sword of destiny": 2,
                    "lepee de la providence": 2, "blood of elves": 3, "le sang des elfes": 3},
        "keywords": ["geralt", "witcher", "sorceleur", "ciri"],
        "variations": ["sorceleur", "geralt of rivia"],
    },
    "game of thrones": {
        "name": "Le Trône de Fer",
        "volumes": {"a game of thrones": 1, "le trone de fer": 1,
                    "a clash of kings": 2, "le donjon rouge": 2,
                    "a storm of swords": 3, "la bataille des rois": 3},
        "keywords": ["westeros", "stark", "lannister", "targaryen", "ice and fire"],
        "variations": ["song of ice and fire", "asoiaf", "trone de fer"],
    },
    "one piece": {
        "name": "One Piece",
        "volumes": {},
        "keywords": ["luffy", "pirates", "chapeau de paille", "nakama"],
        "variations": [],
    },
}

def normalize(s):
    """Minuscules, sans accents, sans ponctuation."""
    s = unicodedata.normalize("NFD", s or "").encode("ascii", "ignore").decode()
    s = re.sub(r"[''`\-]", " ", s.lower())
    s = re.sub(r"[^a-z0-9\s]", "", s)
    return re.sub(r"\s+", " ", s).strip()

# ─── Couche 1 : base statique ──────────────────────────────────────────────────
def check_static(title, saga_field=""):
    """Verifie si le livre est dans la base statique locale."""
    t = normalize(title)
    s = normalize(saga_field)

    # Si on a deja un champ saga (vient d'OL) → cherche dans la base
    if s:
        for key, data in STATIC_DB.items():
            if s in normalize(data["name"]) or normalize(data["name"]) in s:
                return {"series_name": data["name"], "volume": None, "method": "saga_field"}
            for var in data.get("variations", []):
                if normalize(var) == s:
                    return {"series_name": data["name"], "volume": None, "method": "saga_field"}

    # Cherche le titre exact dans les volumes
    for key, data in STATIC_DB.items():
        vol_num = data.get("volumes", {}).get(t)
        if vol_num is not None:
            return {"series_name": data["name"], "volume": vol_num, "method": "volume_title"}

    # Cherche le nom de serie dans le titre
    for key, data in STATIC_DB.items():
        if key in t:
            return {"series_name": data["name"], "volume": None, "method": "series_name_in_title"}
        for var in data.get("variations", []):
            if normalize(var) in t:
                return {"series_name": data["name"], "volume": None, "method": "variation"}

    # Cherche par mots-cles (au moins 2 mots-cles presents)
    for key, data in STATIC_DB.items():
        hits = sum(1 for kw in data.get("keywords", []) if normalize(kw) in t)
        if hits >= 2:
            return {"series_name": data["name"], "volume": None, "method": f"keywords({hits})"}

    return None

# ─── Couche 2 : Wikidata ───────────────────────────────────────────────────────
HEADERS = {"User-Agent": "BooktimeDemo/1.0"}

def wikidata_search(title):
    r = requests.get("https://www.wikidata.org/w/api.php", params={
        "action": "wbsearchentities", "search": title,
        "language": "en", "type": "item", "limit": 5, "format": "json",
    }, headers=HEADERS, timeout=10)
    return r.json().get("search", []) if r.ok else []

def wikidata_entity(qid):
    r = requests.get(f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json",
                     headers=HEADERS, timeout=10)
    if not r.ok:
        return None
    return r.json().get("entities", {}).get(qid)

def is_book(candidate, entity):
    desc = (candidate.get("description") or "").lower()
    if any(k in desc for k in ["novel", "book", "manga", "comic", "roman", "fiction", "fantasy", "series"]):
        return True
    p31_types = {"Q7725634", "Q571", "Q8274", "Q2831984", "Q47461344", "Q277759", "Q1266946"}
    for c in (entity or {}).get("claims", {}).get("P31", []):
        if c.get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id") in p31_types:
            return True
    return False

def get_entity_label(entity, langs=("fr", "en")):
    labels = entity.get("labels", {})
    for lang in langs:
        if lang in labels:
            return labels[lang]["value"]
    return None

def check_wikidata(title):
    """Interroge Wikidata et retourne les infos de serie si trouvees."""
    cache_key = normalize(title)
    if cache_key in CACHE:
        return CACHE[cache_key]

    variants = [title]
    if not title.lower().startswith("the "):
        variants.append("The " + title)

    for variant in variants:
        candidates = wikidata_search(variant)
        for candidate in candidates[:4]:
            qid = candidate["id"]
            entity = wikidata_entity(qid)
            time.sleep(0.15)
            if not entity or not is_book(candidate, entity):
                continue

            series_claims = entity.get("claims", {}).get("P179", [])
            if not series_claims:
                result = {"series_name": None, "volume": None, "method": "wikidata_standalone"}
                CACHE[cache_key] = result
                cache_save(CACHE)
                return result

            series_qid = series_claims[0].get("mainsnak", {}).get("datavalue", {}).get("value", {}).get("id")
            volume = None
            for q in series_claims[0].get("qualifiers", {}).get("P1545", []):
                volume = q.get("datavalue", {}).get("value")
                break

            # Recupere le nom de la serie
            series_entity = wikidata_entity(series_qid)
            time.sleep(0.15)
            series_name = get_entity_label(series_entity, ("fr", "en")) if series_entity else series_qid

            result = {"series_name": series_name, "volume": volume, "method": "wikidata_series"}
            CACHE[cache_key] = result
            cache_save(CACHE)
            return result

    result = {"series_name": None, "volume": None, "method": "wikidata_not_found"}
    CACHE[cache_key] = result
    cache_save(CACHE)
    return result

# ─── Pipeline complet ──────────────────────────────────────────────────────────
def detect(title, author="", saga_from_ol=""):
    """
    Pipeline complet de detection de serie.
    Retourne : { series_name, volume, method, is_standalone }
    """
    # Etape 1 : base statique
    static = check_static(title, saga_from_ol)
    if static:
        return {**static, "is_standalone": False}

    # Etape 2 : Wikidata (avec cache)
    wd = check_wikidata(title)
    if wd["series_name"]:
        return {"series_name": wd["series_name"], "volume": wd["volume"],
                "method": wd["method"], "is_standalone": False}

    # Etape 3 : standalone confirme
    return {"series_name": None, "volume": None,
            "method": wd["method"], "is_standalone": True}

# ─── Cas de test ──────────────────────────────────────────────────────────────
TESTS = [
    # (titre, auteur, saga_OL, resultat_attendu)
    ("The Fellowship of the Ring",              "Tolkien",        "",             "SdA tome 1"),
    ("Golden Son",                              "Pierce Brown",   "Red Rising",   "Red Rising tome 2"),
    ("Harry Potter and the Chamber of Secrets", "J.K. Rowling",  "",             "HP tome 2"),
    ("The Running Man",                         "Stephen King",   "",             "STANDALONE"),
    ("Dune",                                    "Frank Herbert",  "",             "Dune tome 1"),
    ("Morning Star",                            "Pierce Brown",   "Red Rising",   "Red Rising tome 3"),
    ("The Name of the Wind",                    "Rothfuss",       "",             "Kingkiller tome 1"),
    ("1984",                                    "Orwell",         "",             "STANDALONE"),
    ("The Hunger Games",                        "S. Collins",     "",             "Hunger Games tome 1"),
    ("Fondation",                               "Asimov",         "",             "Fondation tome 1"),
    ("Le Dernier Voeu",                         "Sapkowski",      "",             "Witcher tome 1"),
    ("A Game of Thrones",                       "G.R.R. Martin",  "",             "Trone de Fer tome 1"),
    ("Carrie",                                  "Stephen King",   "",             "STANDALONE"),
    ("Le Grand Meaulnes",                       "Alain-Fournier", "",             "STANDALONE"),
]

print()
print("=" * 72)
print("  DEMO PIPELINE -- Detection serie BOOKTIME  (cache: demo_series_cache.json)")
print("=" * 72)

ok_count = 0
for title, author, saga_ol, expected in TESTS:
    res = detect(title, author, saga_ol)
    if res["is_standalone"]:
        label = "STANDALONE"
        vol_str = ""
    else:
        label = res["series_name"] or "?"
        vol_str = f"  tome {res['volume']}" if res.get("volume") else ""

    correct = (expected == "STANDALONE" and res["is_standalone"]) or \
              (expected != "STANDALONE" and not res["is_standalone"])
    icon = "OK" if correct else "!!"
    ok_count += 1 if correct else 0

    print(f"  [{icon}] \"{title}\"")
    print(f"        attendu  : {expected}")
    print(f"        resultat : {label}{vol_str}  [{res['method']}]")

print()
print(f"  Score : {ok_count}/{len(TESTS)}  --  cache: {len(CACHE)} entrees sauvegardees")
print("=" * 72)
print()
print("  Relancez le script : les resultats Wikidata seront instantanes (cache).")
print()
