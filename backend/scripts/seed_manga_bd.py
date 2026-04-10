#!/usr/bin/env python3
"""
SEED MANGA + BD - BOOKTIME
Sources :
  - Jikan API v4 (MyAnimeList) → mangas  (gratuit, sans cle)
  - Google Books API            → BD franco-belge (sans cle pour 1000 req/j,
                                  avec cle GOOGLE_BOOKS_API_KEY pour 10000/j)

Usage :
    cd backend
    python scripts/seed_manga_bd.py             # manga + BD
    python scripts/seed_manga_bd.py --manga-only
    python scripts/seed_manga_bd.py --bd-only
    python scripts/seed_manga_bd.py --resume    # continue sans ecraser
    python scripts/seed_manga_bd.py --limit 50  # test rapide (50 manga)

Sortie : backend/data/manga_bd_cache.json
"""

import sys, os, time, json, argparse, requests
from pathlib import Path
from datetime import datetime

# ─── Config ───────────────────────────────────────────────────────────────────

JIKAN_BASE     = "https://api.jikan.moe/v4"
GBOOKS_BASE    = "https://www.googleapis.com/books/v1/volumes"
OUTPUT_FILE    = Path(__file__).parent.parent / "data" / "manga_bd_cache.json"

JIKAN_DELAY    = 0.4   # 0.4s entre appels (limite : 3/sec, 60/min)
GBOOKS_DELAY   = 0.5
GBOOKS_API_KEY = os.environ.get("GOOGLE_BOOKS_API_KEY", "")

# ─── Mangas : requêtes Jikan ──────────────────────────────────────────────────

MANGA_GENRES_JIKAN = [
    # id genre MyAnimeList → label
    (1,  "action"),
    (2,  "adventure"),
    (4,  "comedy"),
    (7,  "mystery"),
    (8,  "drama"),
    (10, "fantasy"),
    (14, "horror"),
    (18, "mecha"),
    (19, "music"),
    (22, "romance"),
    (24, "sci_fi"),
    (25, "sports"),
    (27, "shounen"),
    (42, "seinen"),
    (43, "josei"),
    (44, "shoujo"),
    (46, "award_winning"),
    (36, "slice_of_life"),
    (37, "supernatural"),
    (39, "thriller"),
    (40, "vampire"),
    (41, "video_game"),
]

# Types de manga à requêter
MANGA_TYPES = ["manga", "manhwa", "manhua", "one_shot", "novel", "doujin"]

# Requêtes textuelles supplémentaires (séries iconiques)
MANGA_QUERIES_JIKAN = [
    "one piece", "naruto", "dragon ball", "bleach", "attack on titan",
    "fullmetal alchemist", "death note", "my hero academia", "demon slayer",
    "jujutsu kaisen", "tokyo ghoul", "sword art online", "fairy tail",
    "hunter x hunter", "one punch man", "black clover", "boruto",
    "vinland saga", "berserk", "vagabond", "gantz", "akira",
    "slam dunk", "captain tsubasa", "haikyuu", "kuroko no basket",
    "nana", "fruits basket", "kimi ni todoke", "ouran high school",
    "sailor moon", "cardcaptor sakura", "magic knight rayearth",
    "saint seiya", "fist of the north star", "city hunter",
    "lupin iii", "golgo 13", "lone wolf and cub", "doraemon",
    "pokemon", "digimon", "yu-gi-oh", "beyblade",
    "initial d", "wangan midnight", "blue period", "blue lock",
    "chainsaw man", "spy x family", "made in abyss", "overlord",
    "re zero", "sword art online", "no game no life",
    "violet evergarden", "your lie in april",
]

# ─── BD : requêtes Google Books ───────────────────────────────────────────────

BD_QUERIES_GBOOKS = [
    # ── Séries franco-belges classiques ──────────────────────────────────────
    "Astérix", "Tintin", "Lucky Luke", "Spirou", "Gaston Lagaffe",
    "Les Schtroumpfs", "Blake et Mortimer", "Thorgal", "XIII",
    "Largo Winch", "Les Tuniques Bleues", "Boule et Bill",
    "Ric Hochet", "Clifton", "Marsupilami", "Titeuf", "Le Chat",
    "Cédric", "Kid Paddle", "Lanfeust de Troy", "Les Légendaires",
    "Blacksad", "Les Innommables", "Sillage", "Orbital",
    "L'Incal", "Chevalier Ardent", "Les 4 As", "Yoko Tsuno",
    "Papyrus", "Percevan", "Alix", "Corto Maltese",
    "Moebius", "Enki Bilal", "Druillet",
    "Johan et Pirlouit", "Cubitus", "Achille Talon",
    "Iznogoud", "Asterix Obelix", "Idefix", "Laureline",
    "Valerian", "Les Passagers du vent", "Comanche",
    "Zara", "Buddy Longway", "Jeremiah",
    "Durango", "Blueberry", "Lieutenant Blueberry",
    "Ric Rolland", "De cape et de crocs",
    "Donjon", "Lanfeust des Etoiles", "Trolls de Troy",
    "Aldebaran", "Betelgeuse", "Antares",
    "Les Mondes d'Aldebaran", "Leo dessinateur",
    "Requiem Chevalier Vampire", "Requiem vampire",
    "Le Troisième Testament", "Testament",
    "William Vance", "Jean Van Hamme",
    "Philippe Francq", "Hermann dessinateur",
    "Tibor dessinateur", "Manara dessinateur",
    "Milo Manara", "Hugo Pratt",
    "Fred Vargas bande dessinee", "Pennac bande dessinee",
    "Goscinny Uderzo", "Franquin",
    "Peyo Schtroumpfs", "Raymond Macherot",
    "Will Spirou", "Andre Franquin",
    "Berck dessinateur", "Greg dessinateur",
    # ── Comics US traduits ────────────────────────────────────────────────────
    "Batman comics francais", "Superman comics francais",
    "Spider-Man comics francais", "X-Men comics francais",
    "Avengers comics francais", "Iron Man comics francais",
    "Captain America comics francais", "Thor comics francais",
    "Hulk comics francais", "Daredevil comics francais",
    "Watchmen francais", "V for Vendetta",
    "Sin City francais", "300 comics",
    "Sandman Neil Gaiman", "Preacher comics",
    "Hellboy francais", "The Walking Dead francais",
    "Saga comics francais", "Maus francais",
    "Persepolis", "Fun Home",
    "Ghost World", "From Hell",
    "League Extraordinary Gentlemen",
    "Kingdom Come comics", "The Dark Knight Returns",
    "Year One Batman", "All Star Superman",
    # ── Editeurs francophones ────────────────────────────────────────────────
    "bande dessinee dargaud", "bande dessinee casterman",
    "bande dessinee glenat", "bande dessinee dupuis",
    "bande dessinee lombard", "bande dessinee delcourt",
    "bande dessinee soleil", "bande dessinee humanoides",
    "bande dessinee urban comics", "bande dessinee panini",
    "bande dessinee ankama", "bande dessinee bamboo",
    "bande dessinee paquet", "bande dessinee vents d'ouest",
    "bande dessinee futuropolis", "bande dessinee fluide glacial",
    "bande dessinee 12bis", "bande dessinee aire libre",
    "bande dessinee peppercarrot", "bande dessinee vent d ouest",
    # ── Genres génériques ────────────────────────────────────────────────────
    "bande dessinee franco belge", "bande dessinee humour",
    "bande dessinee aventure", "bande dessinee science fiction",
    "bande dessinee fantasy", "bande dessinee historique",
    "bande dessinee policier", "bande dessinee jeunesse",
    "bande dessinee romance", "bande dessinee horreur",
    "bande dessinee western", "bande dessinee guerre",
    "bande dessinee sport", "bande dessinee biographie",
    "bande dessinee documentaire", "bande dessinee autobiographie",
    "graphic novel francais", "roman graphique",
    "bande dessinee prix angouleme", "festival angouleme",
    "prix fauve angouleme", "fauve d or",
    "comics marvel francais", "comics dc francais",
    # ── Auteurs primés ───────────────────────────────────────────────────────
    "Art Spiegelman", "Chris Ware", "Daniel Clowes",
    "Charles Burns", "Joe Sacco", "Joe Matt",
    "Seth cartoonist", "Chester Brown",
    "Lewis Trondheim", "Joann Sfar",
    "Marjane Satrapi", "David B auteur bd",
    "Emmanuel Guibert", "Riad Sattouf",
    "Bastien Vives", "Cyril Pedrosa",
    "Nicolas de Crecy", "Frederik Peeters",
    "Christophe Blain", "Manu Larcenet",
    "Edmond Baudoin", "Baru dessinateur",
    "Benoit Sokal", "Pierre Christin",
    "Juan Diaz Canales", "Juanjo Guarnido",
]

# ─── Helpers ──────────────────────────────────────────────────────────────────

def log(msg):
    print(msg, flush=True)

def load_existing(path: Path) -> dict:
    """Charge le fichier existant et retourne {ol_key: book}."""
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            books = json.load(f)
        return {b.get("ol_key", b.get("title", "")): b for b in books if b.get("ol_key") or b.get("title")}
    except Exception:
        return {}

def save(path: Path, books: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, separators=(",", ":"))

def dedupe(new_books: list, existing: dict) -> tuple:
    added, skipped = [], 0
    seen = set(existing.keys())
    for b in new_books:
        key = b.get("ol_key") or b.get("title", "").lower()
        if key and key not in seen:
            seen.add(key)
            added.append(b)
        else:
            skipped += 1
    return added, skipped

# ─── Jikan : Manga ────────────────────────────────────────────────────────────

def jikan_manga_to_book(item: dict) -> dict | None:
    """Convertit une entrée Jikan en format BookTime."""
    title = item.get("title_english") or item.get("title") or ""
    if not title:
        return None
    authors = item.get("authors", [])
    author_str = ", ".join(a.get("name", "") for a in authors if a.get("name")) if authors else ""
    cover = (item.get("images") or {}).get("jpg", {}).get("image_url", "")
    genres = [g.get("name", "") for g in (item.get("genres") or []) + (item.get("themes") or [])]
    genre_str = ", ".join(genres[:3])
    score = item.get("score") or 0
    volumes = item.get("volumes") or 0
    return {
        "ol_key": f"jikan_manga_{item.get('mal_id', '')}",
        "title": title,
        "author": author_str,
        "category": "manga",
        "cover_url": cover,
        "description": (item.get("synopsis") or "")[:500],
        "genre": genre_str,
        "publication_year": str(item.get("published", {}).get("prop", {}).get("from", {}).get("year", "")) if item.get("published") else "",
        "total_pages": (volumes or 0) * 180,
        "popularity_score": round(score / 10, 3) if score else 0,
        "source": "jikan_myanimelist",
    }

def fetch_jikan_by_genre(genre_id: int, genre_label: str, pages: int = 8) -> list:
    books = []
    for page in range(1, pages + 1):
        url = f"{JIKAN_BASE}/manga?genres={genre_id}&order_by=popularity&sort=asc&page={page}&limit=25"
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 429:
                log(f"  [RATE LIMIT] genre {genre_label} page {page}, pause 2s...")
                time.sleep(2)
                r = requests.get(url, timeout=15)
            if not r.ok:
                break
            data = r.json()
            items = data.get("data", [])
            if not items:
                break
            for item in items:
                b = jikan_manga_to_book(item)
                if b:
                    books.append(b)
            if not data.get("pagination", {}).get("has_next_page", False):
                break
        except Exception as e:
            log(f"  [ERREUR] genre {genre_label} page {page}: {e}")
            break
        time.sleep(JIKAN_DELAY)
    return books

def fetch_jikan_top(pages: int = 40) -> list:
    """Top manga par popularité (toutes catégories)."""
    books = []
    for page in range(1, pages + 1):
        url = f"{JIKAN_BASE}/top/manga?page={page}&limit=25"
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 429:
                log(f"  [RATE LIMIT] top page {page}, pause 2s...")
                time.sleep(2)
                r = requests.get(url, timeout=15)
            if not r.ok:
                break
            data = r.json()
            items = data.get("data", [])
            if not items:
                break
            for item in items:
                b = jikan_manga_to_book(item)
                if b:
                    books.append(b)
            if not data.get("pagination", {}).get("has_next_page", False):
                break
        except Exception as e:
            log(f"  [ERREUR] top page {page}: {e}")
            break
        time.sleep(JIKAN_DELAY)
    return books

def fetch_jikan_search(query: str) -> list:
    books = []
    try:
        url = f"{JIKAN_BASE}/manga?q={requests.utils.quote(query)}&order_by=popularity&sort=asc&limit=25"
        r = requests.get(url, timeout=15)
        if r.status_code == 429:
            time.sleep(2)
            r = requests.get(url, timeout=15)
        if not r.ok:
            return []
        for item in r.json().get("data", []):
            b = jikan_manga_to_book(item)
            if b:
                books.append(b)
    except Exception:
        pass
    time.sleep(JIKAN_DELAY)
    return books

def fetch_jikan_type(manga_type: str, pages: int = 10) -> list:
    books = []
    for page in range(1, pages + 1):
        url = f"{JIKAN_BASE}/manga?type={manga_type}&order_by=popularity&sort=asc&page={page}&limit=25"
        try:
            r = requests.get(url, timeout=15)
            if r.status_code == 429:
                log(f"  [RATE LIMIT] type {manga_type} page {page}, pause 2s...")
                time.sleep(2)
                r = requests.get(url, timeout=15)
            if not r.ok:
                break
            data = r.json()
            items = data.get("data", [])
            if not items:
                break
            for item in items:
                b = jikan_manga_to_book(item)
                if b:
                    books.append(b)
            if not data.get("pagination", {}).get("has_next_page", False):
                break
        except Exception as e:
            log(f"  [ERREUR] type {manga_type} page {page}: {e}")
            break
        time.sleep(JIKAN_DELAY)
    return books

# ─── Google Books : BD ────────────────────────────────────────────────────────

def gbooks_item_to_book(item: dict) -> dict | None:
    info = item.get("volumeInfo", {})
    title = info.get("title", "")
    if not title:
        return None
    authors = info.get("authors", [])
    images = info.get("imageLinks", {})
    cover = images.get("thumbnail") or images.get("smallThumbnail") or ""
    # Forcer HTTPS
    if cover.startswith("http://"):
        cover = "https://" + cover[7:]
    categories = info.get("categories", [])
    # Détecter si c'est un manga (mots-clés Jap) pour éviter doublons
    cat_str = " ".join(categories).lower()
    title_lower = title.lower()
    is_manga = any(kw in cat_str or kw in title_lower for kw in ["manga", "manhwa", "anime", "japanese comic"])
    category = "manga" if is_manga else "bd"

    gb_id = item.get("id", "")
    published = info.get("publishedDate", "")
    return {
        "ol_key": f"gbooks_{gb_id}",
        "title": title,
        "author": ", ".join(authors),
        "category": category,
        "cover_url": cover,
        "description": (info.get("description") or "")[:500],
        "genre": ", ".join(categories[:2]),
        "publication_year": published[:4] if published else "",
        "total_pages": info.get("pageCount") or 0,
        "popularity_score": round((info.get("averageRating") or 0) / 5, 3),
        "source": "google_books",
        "isbn": (info.get("industryIdentifiers") or [{}])[0].get("identifier", ""),
    }

def fetch_gbooks(query: str, max_results: int = 40, lang: str = "fr") -> list:
    books = []
    start = 0
    params = {
        "q": query,
        "maxResults": min(max_results, 40),
        "startIndex": start,
        "printType": "books",
    }
    if lang:
        params["langRestrict"] = lang
    if GBOOKS_API_KEY:
        params["key"] = GBOOKS_API_KEY

    fetched = 0
    while fetched < max_results:
        params["startIndex"] = start
        params["maxResults"] = min(40, max_results - fetched)
        try:
            r = requests.get(GBOOKS_BASE, params=params, timeout=15)
            if r.status_code == 429:
                log(f"  [RATE LIMIT] Google Books, pause 3s...")
                time.sleep(3)
                continue
            if not r.ok:
                break
            data = r.json()
            items = data.get("items", [])
            if not items:
                break
            for item in items:
                b = gbooks_item_to_book(item)
                if b:
                    books.append(b)
            total = data.get("totalItems", 0)
            fetched += len(items)
            start += len(items)
            if start >= total or start >= max_results:
                break
        except Exception as e:
            log(f"  [ERREUR] Google Books query '{query}': {e}")
            break
        time.sleep(GBOOKS_DELAY)
    return books

# ─── Main ─────────────────────────────────────────────────────────────────────

def seed_manga(args, existing: dict) -> list:
    all_new = []
    log("\n=== PHASE 1 : MANGA via Jikan (MyAnimeList) ===")

    def _existing_now():
        return {**existing, **{b.get("ol_key"): b for b in all_new}}

    # Top manga global — jusqu'à 500 pages (12500 mangas)
    log("[1/4] Top manga par popularite (jusqu'a 500 pages)...")
    raw = fetch_jikan_top(pages=500)
    new, skip = dedupe(raw, _existing_now())
    all_new.extend(new)
    log(f"  Top: +{len(new)} mangas ({skip} doublons) — total: {len(all_new):,}")

    # Par genres — 80 pages chacun (2000 par genre)
    log(f"[2/4] Par genres ({len(MANGA_GENRES_JIKAN)} genres, 80 pages chacun)...")
    for gid, glabel in MANGA_GENRES_JIKAN:
        raw = fetch_jikan_by_genre(gid, glabel, pages=80)
        new, skip = dedupe(raw, _existing_now())
        all_new.extend(new)
        log(f"  Genre [{glabel}]: +{len(new)} ({skip} skip) — total: {len(all_new):,}")

    # Par type (manhwa, manhua, novel...) — 80 pages chacun
    log(f"[3/4] Par type manga ({len(MANGA_TYPES)} types, 80 pages)...")
    for mtype in MANGA_TYPES:
        raw = fetch_jikan_type(mtype, pages=80)
        new, skip = dedupe(raw, _existing_now())
        all_new.extend(new)
        log(f"  Type [{mtype}]: +{len(new)} ({skip} skip) — total: {len(all_new):,}")

    # Recherches textuelles
    log(f"[4/4] Recherches textuelles ({len(MANGA_QUERIES_JIKAN)} queries)...")
    for q in MANGA_QUERIES_JIKAN:
        raw = fetch_jikan_search(q)
        new, skip = dedupe(raw, _existing_now())
        all_new.extend(new)

    log(f"\n  Total manga collectes : {len(all_new):,}")
    return all_new

def seed_bd(args, existing: dict, already_collected: list) -> list:
    all_new = []
    log("\n=== PHASE 2 : BD via Google Books ===")
    combined_existing = {**existing, **{b.get("ol_key"): b for b in already_collected}}

    def _existing_now():
        return {**combined_existing, **{b.get("ol_key"): b for b in all_new}}

    for i, query in enumerate(BD_QUERIES_GBOOKS, 1):
        log(f"  [{i}/{len(BD_QUERIES_GBOOKS)}] '{query}'...")
        # Recherche en français (160 max) + sans restriction (80 max)
        raw  = fetch_gbooks(query, max_results=160, lang="fr")
        raw += fetch_gbooks(query, max_results=80,  lang="")
        new, skip = dedupe(raw, _existing_now())
        all_new.extend(new)
        log(f"      +{len(new)} BD ({skip} doublons) — total: {len(all_new):,}")

    log(f"\n  Total BD collectees : {len(all_new):,}")
    return all_new

def main():
    parser = argparse.ArgumentParser(description="Seed Manga + BD pour BookTime")
    parser.add_argument("--manga-only", action="store_true")
    parser.add_argument("--bd-only", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Ne pas ecraser le fichier existant")
    parser.add_argument("--limit", type=int, default=0, help="Limite de livres par phase (0=illimite)")
    args = parser.parse_args()

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Charger existant si --resume
    existing = load_existing(OUTPUT_FILE) if args.resume else {}
    log(f"Existant : {len(existing)} livres charges")

    collected = []

    if not args.bd_only:
        manga_books = seed_manga(args, existing)
        collected.extend(manga_books)
        # Sauvegarde intermédiaire
        all_books = list(existing.values()) + collected
        save(OUTPUT_FILE, all_books)
        log(f"\n[SAVE] {len(all_books)} livres sauvegardes -> {OUTPUT_FILE}")

    if not args.manga_only:
        bd_books = seed_bd(args, existing, collected)
        collected.extend(bd_books)

    # Sauvegarde finale
    all_books = list(existing.values()) + collected
    save(OUTPUT_FILE, all_books)

    cats = {"manga": 0, "bd": 0}
    for b in all_books:
        c = b.get("category", "")
        if c in cats:
            cats[c] += 1

    log(f"""
=== TERMINE ===
Total          : {len(all_books):,}
  Mangas       : {cats['manga']:,}
  BD           : {cats['bd']:,}
Fichier        : {OUTPUT_FILE}
""")

if __name__ == "__main__":
    main()
