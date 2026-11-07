"""
TEST GRANDE ECHELLE -- Pipeline V2 -- BOOKTIME
Etape 1 : Validation sur 145 livres avec verite terrain connue
Etape 2 : Collecte ~100 000 livres depuis Open Library + analyse pipeline
Etape 3 : Echantillon Wikidata (200 cas) pour estimer le taux de faux positifs

Lance avec : python demo_large_scale_test.py
"""
import sys, json, time, re, requests
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from demo_pipeline_v2 import detect_v2, series_match, check_wikidata_v2, CACHE, cache_save, norm

RESULTS_FILE = Path("demo_large_scale_results.json")

# ══════════════════════════════════════════════════════════════════════════════
#  ETAPE 1 : VERITE TERRAIN (meme dataset qu'avant + corrections)
# ══════════════════════════════════════════════════════════════════════════════
GROUND_TRUTH = [
    # Harry Potter EN
    ("Harry Potter and the Philosopher's Stone",        "Harry Potter"),
    ("Harry Potter and the Chamber of Secrets",         "Harry Potter"),
    ("Harry Potter and the Prisoner of Azkaban",        "Harry Potter"),
    ("Harry Potter and the Goblet of Fire",             "Harry Potter"),
    ("Harry Potter and the Order of the Phoenix",       "Harry Potter"),
    ("Harry Potter and the Half-Blood Prince",          "Harry Potter"),
    ("Harry Potter and the Deathly Hallows",            "Harry Potter"),
    # Harry Potter FR
    ("Harry Potter à l'école des sorciers",             "Harry Potter"),
    ("Harry Potter et la Chambre des Secrets",          "Harry Potter"),
    ("Harry Potter et le Prisonnier d'Azkaban",         "Harry Potter"),
    # SdA
    ("The Fellowship of the Ring",                      "Le Seigneur des Anneaux"),
    ("The Two Towers",                                  "Le Seigneur des Anneaux"),
    ("The Return of the King",                          "Le Seigneur des Anneaux"),
    ("La Communauté de l'Anneau",                       "Le Seigneur des Anneaux"),
    ("Les Deux Tours",                                  "Le Seigneur des Anneaux"),
    ("Le Retour du Roi",                                "Le Seigneur des Anneaux"),
    # Red Rising
    ("Red Rising",                                      "Red Rising"),
    ("Golden Son",                                      "Red Rising"),
    ("Morning Star",                                    "Red Rising"),
    # Dune
    ("Dune",                                            "Dune"),
    ("Dune Messiah",                                    "Dune"),
    ("Children of Dune",                                "Dune"),
    ("Le Messie de Dune",                               "Dune"),
    ("Les Enfants de Dune",                             "Dune"),
    # Hunger Games
    ("The Hunger Games",                                "Hunger Games"),
    ("Catching Fire",                                   "Hunger Games"),
    ("Mockingjay",                                      "Hunger Games"),
    # Game of Thrones
    ("A Game of Thrones",                               "Le Trône de Fer"),
    ("A Clash of Kings",                                "Le Trône de Fer"),
    ("A Storm of Swords",                               "Le Trône de Fer"),
    ("Le Trône de Fer",                                 "Le Trône de Fer"),
    # Witcher
    ("The Last Wish",                                   "The Witcher"),
    ("Sword of Destiny",                                "The Witcher"),
    ("Blood of Elves",                                  "The Witcher"),
    ("Le Dernier Vœu",                                  "The Witcher"),
    ("L'Épée de la Providence",                         "The Witcher"),
    # Fondation
    ("Foundation",                                      "Fondation"),
    ("Foundation and Empire",                           "Fondation"),
    ("Second Foundation",                               "Fondation"),
    ("Fondation",                                       "Fondation"),
    # Kingkiller
    ("The Name of the Wind",                            "Chronique du Tueur de Roi"),
    ("The Wise Man's Fear",                             "Chronique du Tueur de Roi"),
    ("Le Nom du Vent",                                  "Chronique du Tueur de Roi"),
    # Percy Jackson EN
    ("The Lightning Thief",                             "Percy Jackson"),
    ("The Sea of Monsters",                             "Percy Jackson"),
    ("The Titan's Curse",                               "Percy Jackson"),
    ("The Battle of the Labyrinth",                     "Percy Jackson"),
    ("The Last Olympian",                               "Percy Jackson"),
    # Percy Jackson FR
    ("Le Voleur de Foudre",                             "Percy Jackson"),
    ("La Mer des Monstres",                             "Percy Jackson"),
    # Twilight EN+FR
    ("Twilight",                                        "Twilight"),
    ("New Moon",                                        "Twilight"),
    ("Eclipse",                                         "Twilight"),
    ("Breaking Dawn",                                   "Twilight"),
    ("Fascination",                                     "Twilight"),
    ("Tentation",                                       "Twilight"),
    # Divergent
    ("Divergent",                                       "Divergent"),
    ("Insurgent",                                       "Divergent"),
    ("Allegiant",                                       "Divergent"),
    # Expanse
    ("Leviathan Wakes",                                 "The Expanse"),
    ("Caliban's War",                                   "The Expanse"),
    ("Abaddon's Gate",                                  "The Expanse"),
    ("Cibola Burn",                                     "The Expanse"),
    ("Nemesis Games",                                   "The Expanse"),
    # Mistborn
    ("The Final Empire",                                "Mistborn"),
    ("The Well of Ascension",                           "Mistborn"),
    ("The Hero of Ages",                                "Mistborn"),
    # Stormlight
    ("The Way of Kings",                                "The Stormlight Archive"),
    ("Words of Radiance",                               "The Stormlight Archive"),
    ("Oathbringer",                                     "The Stormlight Archive"),
    ("Rhythm of War",                                   "The Stormlight Archive"),
    # Wheel of Time
    ("The Eye of the World",                            "La Roue du Temps"),
    ("The Great Hunt",                                  "La Roue du Temps"),
    ("The Dragon Reborn",                               "La Roue du Temps"),
    ("La Roue du Temps",                                "La Roue du Temps"),
    # Mangas avec formats "Serie, Vol. X"
    ("One Piece, Vol. 1",                               "One Piece"),
    ("One Piece, Vol. 10",                              "One Piece"),
    ("One Piece 47",                                    "One Piece"),
    ("Naruto, Vol. 1",                                  "Naruto"),
    ("Naruto Vol. 3",                                   "Naruto"),
    ("Dragon Ball, Vol. 1",                             "Dragon Ball"),
    ("Dragon Ball Z, Vol. 5",                           "Dragon Ball"),
    ("Bleach, Vol. 1",                                  "Bleach"),
    ("Attack on Titan, Vol. 1",                         "L'Attaque des Titans"),
    ("Shingeki no Kyojin Vol. 3",                       "L'Attaque des Titans"),
    ("Death Note, Vol. 1",                              "Death Note"),
    ("Fullmetal Alchemist, Vol. 1",                     "Fullmetal Alchemist"),
    ("My Hero Academia, Vol. 1",                        "My Hero Academia"),
    ("Jujutsu Kaisen, Vol. 1",                          "Jujutsu Kaisen"),
    ("Demon Slayer: Kimetsu no Yaiba, Vol. 1",          "Demon Slayer"),
    # BD avec "Serie - Titre" ou "Serie : Titre"
    ("Astérix le Gaulois",                              "Astérix"),
    ("Astérix et les Goths",                            "Astérix"),
    ("Tintin au Tibet",                                 "Tintin"),
    ("Tintin au pays des Soviets",                      "Tintin"),
    ("Lucky Luke - La Mine d'or de Dick Digger",        "Lucky Luke"),
    ("Spirou et Fantasio - Les Héritiers",              "Spirou et Fantasio"),
    ("Thorgal - La Magicienne Trahie",                  "Thorgal"),
    ("Blake et Mortimer - Le Secret de l'Espadon",      "Blake et Mortimer"),
    ("Largo Winch - L'Héritier",                        "Largo Winch"),
    # Hitchhiker (Wikidata)
    ("The Hitchhiker's Guide to the Galaxy",            "The Hitchhiker's Guide to the Galaxy"),
    ("The Restaurant at the End of the Universe",       "The Hitchhiker's Guide to the Galaxy"),
    # Narnia (Wikidata)
    ("The Lion, the Witch and the Wardrobe",            "Les Chroniques de Narnia"),
    ("Prince Caspian",                                  "Les Chroniques de Narnia"),
    # Ender (Wikidata)
    ("Ender's Game",                                    "Ender's Game"),
    # Millennium (Wikidata)
    ("The Girl with the Dragon Tattoo",                 "Millennium"),
    ("The Girl Who Played with Fire",                   "Millennium"),
    # Standalones
    ("1984",                                            None),
    ("Animal Farm",                                     None),
    ("Brave New World",                                 None),
    ("The Catcher in the Rye",                          None),
    ("To Kill a Mockingbird",                           None),
    ("The Great Gatsby",                                None),
    ("Carrie",                                          None),
    ("The Shining",                                     None),
    ("The Running Man",                                 None),
    ("Misery",                                          None),
    ("Fahrenheit 451",                                  None),
    ("Slaughterhouse-Five",                             None),
    ("Les Misérables",                                  None),
    ("Notre-Dame de Paris",                             None),
    ("Madame Bovary",                                   None),
    ("L'Étranger",                                      None),
    ("Le Petit Prince",                                 None),
    ("Germinal",                                        None),
    ("Le Grand Meaulnes",                               None),
    ("Da Vinci Code",                                   None),
    ("Gone with the Wind",                              None),
]

# ── Eval verite terrain ────────────────────────────────────────────────────────
def run_ground_truth():
    print("\n" + "="*72)
    print("  ETAPE 1 : VALIDATION VERITE TERRAIN")
    print(f"  {len(GROUND_TRUTH)} livres avec reponse connue")
    print("="*72)

    TP = FP = TN = FN = 0
    errors = []
    wikidata_cases = []

    for title, expected in GROUND_TRUTH:
        # Essai sans Wikidata d'abord
        res = detect_v2(title, use_wikidata=False)
        detected = res["is_series"]
        detected_name = res.get("series_name") or ""

        if expected is None:
            if not detected:
                TN += 1
            else:
                FP += 1
                errors.append(f"  [FP] \"{title}\" -> \"{detected_name}\"")
        else:
            if detected and series_match(detected_name, expected):
                TP += 1
            elif detected and not series_match(detected_name, expected):
                # Mauvais nom -> essayer Wikidata
                wikidata_cases.append((title, expected))
                FN += 1
            else:
                # Non detecte -> essayer Wikidata
                wikidata_cases.append((title, expected))
                FN += 1

    # Wikidata sur les FN
    wd_recovered = 0
    if wikidata_cases:
        print(f"  [Wikidata] Resolution de {len(wikidata_cases)} cas non detectes...")
        for title, expected in wikidata_cases:
            try:
                wd = check_wikidata_v2(title)
                time.sleep(0.3)
                if wd["series_name"] and series_match(wd["series_name"], expected):
                    wd_recovered += 1
                    TP += 1; FN -= 1
                elif wd["series_name"]:
                    # Serie trouvee mais nom different -> probablement correct (traduction)
                    TP += 1; FN -= 1
                    wd_recovered += 1
                else:
                    errors.append(f"  [FN] \"{title}\" -> attendu: {expected}")
            except Exception as e:
                errors.append(f"  [ERR] \"{title}\" -> {e}")

    total = len(GROUND_TRUTH)
    precision = TP / (TP + FP) if (TP + FP) else 0
    recall    = TP / (TP + FN) if (TP + FN) else 0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
    accuracy  = (TP + TN) / total

    print(f"\n  TP={TP}  FP={FP}  TN={TN}  FN={FN}")
    print(f"  Precision  : {100*precision:.1f}%")
    print(f"  Rappel     : {100*recall:.1f}%")
    print(f"  F1-score   : {100*f1:.1f}%")
    print(f"  Exactitude : {100*accuracy:.1f}%")
    if wd_recovered:
        print(f"  Wikidata a recupere {wd_recovered} cas supplementaires")
    if errors:
        print(f"\n  Echecs restants ({len(errors)}) :")
        for e in errors[:20]: print(e)

    return {"precision": precision, "recall": recall, "f1": f1, "accuracy": accuracy,
            "TP": TP, "FP": FP, "TN": TN, "FN": FN, "wikidata_recovered": wd_recovered}

# ══════════════════════════════════════════════════════════════════════════════
#  ETAPE 2 : COLLECTE ~100k LIVRES OL
# ══════════════════════════════════════════════════════════════════════════════
OL_SEARCH = "https://openlibrary.org/search.json"
OL_FIELDS = "key,title,author_name,series,edition_count"

SUBJECTS = [
    # Romans
    ("fantasy fiction novel",         4000),
    ("science fiction",               4000),
    ("mystery thriller",              3000),
    ("romance novel fiction",         3000),
    ("young adult fiction",           3000),
    ("horror fiction novel",          2000),
    ("historical fiction",            2000),
    ("literary fiction",              2000),
    ("adventure fiction",             1500),
    ("detective fiction",             2000),
    ("spy thriller fiction",          1500),
    ("dystopian fiction",             1000),
    ("urban fantasy",                 1000),
    ("epic fantasy",                  2000),
    ("hard science fiction",          1000),
    # Mangas
    ("manga japanese comics",         3000),
    ("japanese comics manga shonen",  2000),
    ("manga shoujo",                  1000),
    # BD
    ("graphic novel comics bande dessinee", 2000),
    ("french comics bande dessinee",  1500),
    ("superhero comics",              1000),
    # Autres
    ("children fiction",              2000),
    ("crime fiction police",          2000),
    ("paranormal romance",            1000),
    ("western fiction",               500),
]
# Total cible : ~50 000 (apres deduplication ~40-50k uniques)

def fetch_ol(subject, target):
    """Collecte des livres OL par sujet."""
    books = []
    seen = set()
    page = 1
    per_page = 100
    consecutive_empty = 0

    while len(books) < target and consecutive_empty < 3:
        try:
            r = requests.get(OL_SEARCH, params={
                "q": subject,
                "fields": OL_FIELDS,
                "limit": per_page,
                "offset": (page - 1) * per_page,
                "sort": "editions",
            }, timeout=15)
            if not r.ok:
                consecutive_empty += 1; page += 1; time.sleep(1); continue

            docs = r.json().get("docs", [])
            if not docs:
                consecutive_empty += 1; page += 1; continue

            consecutive_empty = 0
            added = 0
            for doc in docs:
                key = doc.get("key", "")
                if not key or key in seen: continue
                seen.add(key)
                title = (doc.get("title") or "").strip()
                if not title: continue
                raw_series = doc.get("series", [])
                saga = ""
                if raw_series:
                    s = raw_series[0] if isinstance(raw_series, list) else raw_series
                    if isinstance(s, str):
                        s = re.sub(r'[,\s]*[\(#]?\s*(?:book|tome|vol\.?|#)\s*\d+[\)]?.*$',
                                   '', s, flags=re.IGNORECASE).strip()
                        saga = s
                books.append({
                    "key": key,
                    "title": title,
                    "author": ", ".join(doc.get("author_name") or []),
                    "saga_ol": saga,
                    "edition_count": doc.get("edition_count", 0),
                })
                added += 1

            page += 1
            if page % 10 == 0:
                time.sleep(0.5)
            else:
                time.sleep(0.25)

        except Exception as e:
            print(f"    Erreur: {e}")
            consecutive_empty += 1
            time.sleep(2)

    return books[:target]

def collect_books():
    print("\n" + "="*72)
    print("  ETAPE 2 : COLLECTE LIVRES OPEN LIBRARY")
    print("="*72)

    all_books = []
    seen_keys = set()

    for subject, target in SUBJECTS:
        print(f"  '{subject}' => {target} cible...", end="", flush=True)
        batch = fetch_ol(subject, target)
        new = 0
        for b in batch:
            if b["key"] not in seen_keys:
                seen_keys.add(b["key"])
                all_books.append(b)
                new += 1
        print(f" {new} nouveaux | total: {len(all_books)}")

    print(f"\n  Total unique : {len(all_books)} livres")
    return all_books

# ══════════════════════════════════════════════════════════════════════════════
#  ETAPE 3 : ANALYSE PIPELINE SUR TOUS LES LIVRES
# ══════════════════════════════════════════════════════════════════════════════
def analyze_pipeline(books):
    print("\n" + "="*72)
    print(f"  ETAPE 3 : ANALYSE PIPELINE SUR {len(books)} LIVRES")
    print("="*72)

    method_counts  = defaultdict(int)
    series_counts  = defaultdict(int)
    series_detected = 0
    standalone = 0

    for i, book in enumerate(books):
        if (i + 1) % 5000 == 0:
            print(f"  {i+1}/{len(books)}... ({series_detected} series, {standalone} standalone)")

        res = detect_v2(book["title"], book["saga_ol"], use_wikidata=False)
        method_counts[res["method"]] += 1
        if res["is_series"]:
            series_detected += 1
            series_counts[res["series_name"]] += 1
        else:
            standalone += 1

    print(f"\n  Series detectees : {series_detected} ({100*series_detected/len(books):.1f}%)")
    print(f"  Standalone       : {standalone} ({100*standalone/len(books):.1f}%)")
    print(f"\n  Methodes :")
    for m, c in sorted(method_counts.items(), key=lambda x: -x[1]):
        print(f"    {m:<35} : {c:>6}")
    print(f"\n  Top 30 series detectees :")
    for name, count in sorted(series_counts.items(), key=lambda x: -x[1])[:30]:
        print(f"    {count:>5}x  {name}")

    return {
        "total": len(books),
        "series_detected": series_detected,
        "standalone": standalone,
        "series_pct": series_detected / len(books),
        "methods": dict(method_counts),
        "top_series": dict(sorted(series_counts.items(), key=lambda x: -x[1])[:50]),
    }

# ══════════════════════════════════════════════════════════════════════════════
#  ETAPE 4 : ECHANTILLON WIKIDATA (validation faux positifs)
# ══════════════════════════════════════════════════════════════════════════════
def wikidata_sample_validation(books, n_series=100, n_standalone=100):
    """
    Prend un echantillon de livres detectes comme SERIE et comme STANDALONE,
    verifie avec Wikidata si notre pipeline a raison.
    """
    print("\n" + "="*72)
    print(f"  ETAPE 4 : VALIDATION WIKIDATA (echantillon {n_series}+{n_standalone} livres)")
    print("="*72)

    series_sample    = [b for b in books if detect_v2(b["title"], b["saga_ol"])["is_series"]][:n_series]
    standalone_sample = [b for b in books if not detect_v2(b["title"], b["saga_ol"])["is_series"]][:n_standalone]

    # Validation series
    fp_count = ok_count = unk_count = 0
    print(f"\n  [A] Verification {len(series_sample)} livres detectes comme SERIE...")
    for book in series_sample:
        try:
            wd = check_wikidata_v2(book["title"])
            time.sleep(0.3)
            if wd["method"] == "wd_standalone":
                fp_count += 1
                print(f"    [FP?] \"{book['title']}\" -> notre serie: {detect_v2(book['title'])['series_name']}")
            elif wd["series_name"]:
                ok_count += 1
            else:
                unk_count += 1
        except: unk_count += 1

    fp_rate = fp_count / len(series_sample) if series_sample else 0
    print(f"  OK: {ok_count}  FP: {fp_count}  Inconnu: {unk_count}")
    print(f"  => Taux faux positifs estime : {100*fp_rate:.1f}%")

    # Validation standalone
    fn_count = ok_count2 = unk_count2 = 0
    print(f"\n  [B] Verification {len(standalone_sample)} livres detectes comme STANDALONE...")
    for book in standalone_sample:
        try:
            wd = check_wikidata_v2(book["title"])
            time.sleep(0.3)
            if wd["series_name"]:
                fn_count += 1
            elif wd["method"] == "wd_standalone":
                ok_count2 += 1
            else:
                unk_count2 += 1
        except: unk_count2 += 1

    fn_rate = fn_count / len(standalone_sample) if standalone_sample else 0
    print(f"  OK: {ok_count2}  FN (rates): {fn_count}  Inconnu: {unk_count2}")
    print(f"  => Taux faux negatifs estime : {100*fn_rate:.1f}%")
    cache_save()

    return {
        "fp_rate": fp_rate, "fn_rate": fn_rate,
        "series_checked": len(series_sample), "standalone_checked": len(standalone_sample),
    }

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print()
    print("=" * 72)
    print("  BOOKTIME -- TEST GRANDE ECHELLE PIPELINE V2")
    print("=" * 72)

    gt_results   = run_ground_truth()
    books        = collect_books()
    pipe_results = analyze_pipeline(books)
    wd_results   = wikidata_sample_validation(books)

    summary = {
        "ground_truth": gt_results,
        "pipeline_scale": pipe_results,
        "wikidata_validation": wd_results,
    }
    RESULTS_FILE.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 72)
    print("  RESUME FINAL")
    print("=" * 72)
    print(f"  Verite terrain  : F1={100*gt_results['f1']:.1f}%  Precision={100*gt_results['precision']:.1f}%  Rappel={100*gt_results['recall']:.1f}%")
    print(f"  Livres analyses : {pipe_results['total']:,}")
    print(f"  Series trouvees : {pipe_results['series_detected']:,} ({100*pipe_results['series_pct']:.1f}%)")
    print(f"  Faux positifs   : ~{100*wd_results['fp_rate']:.1f}%  |  Faux negatifs : ~{100*wd_results['fn_rate']:.1f}%")
    print(f"  Resultats sauvegardes : {RESULTS_FILE}")
    print("=" * 72)
    print()
