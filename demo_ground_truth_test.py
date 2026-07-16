"""
TEST AVEC VERITE TERRAIN -- Pipeline detection serie BOOKTIME
Dataset : ~400 livres avec reponse attendue connue
  - Livres de series connues (EN + FR, Romans / Mangas / BD / SF)
  - Livres standalone confirmes
  - Series hors base statique (testes via Wikidata)

Lance avec : python demo_ground_truth_test.py
"""
import sys, json, time, unicodedata, re, requests
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
from demo_pipeline import check_static, check_wikidata, CACHE, cache_save, normalize

def detect_fast(title, saga_ol=""):
    """Pipeline sans appel reseau (base statique + champ OL seulement)."""
    static = check_static(title, saga_ol)
    if static:
        return {"is_series": True, "series_name": static["series_name"],
                "volume": static.get("volume"), "method": static["method"]}
    if saga_ol:
        return {"is_series": True, "series_name": saga_ol,
                "volume": None, "method": "ol_saga_field"}
    return {"is_series": False, "series_name": None, "volume": None, "method": "standalone"}

# ══════════════════════════════════════════════════════════════════════════════
#  VERITE TERRAIN  (titre, serie_attendue_ou_None, source)
#  None = standalone confirme
# ══════════════════════════════════════════════════════════════════════════════
GROUND_TRUTH = [

    # ── HARRY POTTER (EN + FR) ────────────────────────────────────────────────
    ("Harry Potter and the Philosopher's Stone",        "Harry Potter", "static"),
    ("Harry Potter and the Chamber of Secrets",         "Harry Potter", "static"),
    ("Harry Potter and the Prisoner of Azkaban",        "Harry Potter", "static"),
    ("Harry Potter and the Goblet of Fire",             "Harry Potter", "static"),
    ("Harry Potter and the Order of the Phoenix",       "Harry Potter", "static"),
    ("Harry Potter and the Half-Blood Prince",          "Harry Potter", "static"),
    ("Harry Potter and the Deathly Hallows",            "Harry Potter", "static"),
    ("Harry Potter à l'école des sorciers",             "Harry Potter", "static"),
    ("Harry Potter et la Chambre des Secrets",          "Harry Potter", "static"),
    ("Harry Potter et le Prisonnier d'Azkaban",         "Harry Potter", "static"),

    # ── SEIGNEUR DES ANNEAUX ──────────────────────────────────────────────────
    ("The Fellowship of the Ring",                      "Le Seigneur des Anneaux", "static"),
    ("The Two Towers",                                  "Le Seigneur des Anneaux", "static"),
    ("The Return of the King",                          "Le Seigneur des Anneaux", "static"),
    ("La Communauté de l'Anneau",                       "Le Seigneur des Anneaux", "static"),
    ("Les Deux Tours",                                  "Le Seigneur des Anneaux", "static"),
    ("Le Retour du Roi",                                "Le Seigneur des Anneaux", "static"),

    # ── RED RISING ────────────────────────────────────────────────────────────
    ("Red Rising",                                      "Red Rising",  "static"),
    ("Golden Son",                                      "Red Rising",  "static"),
    ("Morning Star",                                    "Red Rising",  "static"),

    # ── DUNE ─────────────────────────────────────────────────────────────────
    ("Dune",                                            "Dune",        "static"),
    ("Dune Messiah",                                    "Dune",        "static"),
    ("Children of Dune",                                "Dune",        "static"),
    ("Le Messie de Dune",                               "Dune",        "static"),
    ("Les Enfants de Dune",                             "Dune",        "static"),

    # ── HUNGER GAMES ─────────────────────────────────────────────────────────
    ("The Hunger Games",                                "Hunger Games","static"),
    ("Catching Fire",                                   "Hunger Games","static"),
    ("Mockingjay",                                      "Hunger Games","static"),

    # ── GAME OF THRONES ──────────────────────────────────────────────────────
    ("A Game of Thrones",                               "Le Trône de Fer", "static"),
    ("A Clash of Kings",                                "Le Trône de Fer", "static"),
    ("A Storm of Swords",                               "Le Trône de Fer", "static"),
    ("Le Trône de Fer",                                 "Le Trône de Fer", "static"),
    ("Le Donjon Rouge",                                 "Le Trône de Fer", "static"),

    # ── WITCHER ──────────────────────────────────────────────────────────────
    ("The Last Wish",                                   "The Witcher", "static"),
    ("Sword of Destiny",                                "The Witcher", "static"),
    ("Blood of Elves",                                  "The Witcher", "static"),
    ("Le Dernier Vœu",                                  "The Witcher", "static"),
    ("L'Épée de la Providence",                         "The Witcher", "static"),
    ("Le Sang des Elfes",                               "The Witcher", "static"),

    # ── FONDATION (Asimov) ───────────────────────────────────────────────────
    ("Foundation",                                      "Fondation",   "static"),
    ("Foundation and Empire",                           "Fondation",   "static"),
    ("Second Foundation",                               "Fondation",   "static"),
    ("Fondation",                                       "Fondation",   "static"),
    ("Fondation et Empire",                             "Fondation",   "static"),
    ("Seconde Fondation",                               "Fondation",   "static"),

    # ── NAME OF THE WIND ─────────────────────────────────────────────────────
    ("The Name of the Wind",                            "Chronique du Tueur de Roi", "static"),
    ("The Wise Man's Fear",                             "Chronique du Tueur de Roi", "static"),
    ("Le Nom du Vent",                                  "Chronique du Tueur de Roi", "static"),
    ("La Peur du Sage",                                 "Chronique du Tueur de Roi", "static"),

    # ── PERCY JACKSON ────────────────────────────────────────────────────────
    ("The Lightning Thief",                             "Percy Jackson", "static"),
    ("The Sea of Monsters",                             "Percy Jackson", "static"),
    ("The Titan's Curse",                               "Percy Jackson", "static"),
    ("The Battle of the Labyrinth",                     "Percy Jackson", "static"),
    ("The Last Olympian",                               "Percy Jackson", "static"),
    ("Le Voleur de Foudre",                             "Percy Jackson", "static"),
    ("La Mer des Monstres",                             "Percy Jackson", "static"),

    # ── TWILIGHT ─────────────────────────────────────────────────────────────
    ("Twilight",                                        "Twilight",    "static"),
    ("New Moon",                                        "Twilight",    "static"),
    ("Eclipse",                                         "Twilight",    "static"),
    ("Breaking Dawn",                                   "Twilight",    "static"),
    ("Fascination",                                     "Twilight",    "static"),
    ("Tentation",                                       "Twilight",    "static"),

    # ── DIVERGENT ────────────────────────────────────────────────────────────
    ("Divergent",                                       "Divergent",   "static"),
    ("Insurgent",                                       "Divergent",   "static"),
    ("Allegiant",                                       "Divergent",   "static"),

    # ── THE EXPANSE ──────────────────────────────────────────────────────────
    ("Leviathan Wakes",                                 "The Expanse", "static"),
    ("Caliban's War",                                   "The Expanse", "static"),
    ("Abaddon's Gate",                                  "The Expanse", "static"),
    ("Cibola Burn",                                     "The Expanse", "static"),
    ("Nemesis Games",                                   "The Expanse", "static"),

    # ── MISTBORN ─────────────────────────────────────────────────────────────
    ("The Final Empire",                                "Mistborn",    "static"),
    ("The Well of Ascension",                           "Mistborn",    "static"),
    ("The Hero of Ages",                                "Mistborn",    "static"),

    # ── STORMLIGHT ARCHIVE ───────────────────────────────────────────────────
    ("The Way of Kings",                                "The Stormlight Archive", "static"),
    ("Words of Radiance",                               "The Stormlight Archive", "static"),
    ("Oathbringer",                                     "The Stormlight Archive", "static"),
    ("Rhythm of War",                                   "The Stormlight Archive", "static"),

    # ── WHEEL OF TIME ────────────────────────────────────────────────────────
    ("The Eye of the World",                            "La Roue du Temps", "static"),
    ("The Great Hunt",                                  "La Roue du Temps", "static"),
    ("The Dragon Reborn",                               "La Roue du Temps", "static"),
    ("La Roue du Temps",                                "La Roue du Temps", "static"),

    # ── MANGAS ───────────────────────────────────────────────────────────────
    ("One Piece, Vol. 1",                               "One Piece",   "static"),
    ("One Piece, Vol. 10",                              "One Piece",   "static"),
    ("One Piece 47",                                    "One Piece",   "static"),
    ("Naruto, Vol. 1",                                  "Naruto",      "static"),
    ("Naruto Vol. 3",                                   "Naruto",      "static"),
    ("Dragon Ball, Vol. 1",                             "Dragon Ball", "static"),
    ("Dragon Ball Z, Vol. 5",                           "Dragon Ball", "static"),
    ("Bleach, Vol. 1",                                  "Bleach",      "static"),
    ("Attack on Titan, Vol. 1",                         "L'Attaque des Titans", "static"),
    ("Shingeki no Kyojin Vol. 3",                       "L'Attaque des Titans", "static"),
    ("Death Note, Vol. 1",                              "Death Note",  "static"),
    ("Fullmetal Alchemist, Vol. 1",                     "Fullmetal Alchemist", "static"),
    ("My Hero Academia, Vol. 1",                        "My Hero Academia", "static"),
    ("Jujutsu Kaisen, Vol. 1",                          "Jujutsu Kaisen", "static"),
    ("Demon Slayer: Kimetsu no Yaiba, Vol. 1",          "Demon Slayer", "static"),

    # ── BD ────────────────────────────────────────────────────────────────────
    ("Astérix le Gaulois",                              "Astérix",     "static"),
    ("Astérix et les Goths",                            "Astérix",     "static"),
    ("Les Aventures de Tintin : Tintin au Tibet",       "Tintin",      "static"),
    ("Tintin au pays des Soviets",                      "Tintin",      "static"),
    ("Lucky Luke - La Mine d'or de Dick Digger",        "Lucky Luke",  "static"),
    ("Spirou et Fantasio - Les Héritiers",              "Spirou et Fantasio", "static"),
    ("Thorgal - La Magicienne Trahie",                  "Thorgal",     "static"),
    ("Blake et Mortimer - Le Secret de l'Espadon",      "Blake et Mortimer", "static"),
    ("Largo Winch - L'Héritier",                        "Largo Winch", "static"),

    # ── SERIES HORS BASE STATIQUE (test Wikidata) ────────────────────────────
    ("The Hitchhiker's Guide to the Galaxy",            "Hitchhiker's Guide", "wikidata"),
    ("The Restaurant at the End of the Universe",       "Hitchhiker's Guide", "wikidata"),
    ("A Wrinkle in Time",                               "Time Quintet",       "wikidata"),
    ("The Lion, the Witch and the Wardrobe",            "Chronicles of Narnia","wikidata"),
    ("Prince Caspian",                                  "Chronicles of Narnia","wikidata"),
    ("Ender's Game",                                    "Ender's Game",       "wikidata"),
    ("Speaker for the Dead",                            "Ender's Game",       "wikidata"),
    ("The Girl with the Dragon Tattoo",                 "Millennium",         "wikidata"),
    ("The Girl Who Played with Fire",                   "Millennium",         "wikidata"),
    ("Gone with the Wind",                              None,                  "wikidata"),  # standalone
    ("Neuromancer",                                     None,                  "wikidata"),  # standalone (ou Sprawl)

    # ── STANDALONES CONFIRMES ────────────────────────────────────────────────
    ("1984",                                            None, "standalone"),
    ("Animal Farm",                                     None, "standalone"),
    ("Brave New World",                                 None, "standalone"),
    ("The Catcher in the Rye",                          None, "standalone"),
    ("To Kill a Mockingbird",                           None, "standalone"),
    ("Of Mice and Men",                                 None, "standalone"),
    ("The Great Gatsby",                                None, "standalone"),
    ("Crime and Punishment",                            None, "standalone"),
    ("The Brothers Karamazov",                          None, "standalone"),
    ("Don Quixote",                                     None, "standalone"),
    ("Carrie",                                          None, "standalone"),
    ("The Shining",                                     None, "standalone"),
    ("The Running Man",                                 None, "standalone"),
    ("Misery",                                          None, "standalone"),
    ("It",                                              None, "standalone"),
    ("Fahrenheit 451",                                  None, "standalone"),
    ("Slaughterhouse-Five",                             None, "standalone"),
    ("The Old Man and the Sea",                         None, "standalone"),
    ("Lolita",                                          None, "standalone"),
    ("Les Misérables",                                  None, "standalone"),
    ("Notre-Dame de Paris",                             None, "standalone"),
    ("Madame Bovary",                                   None, "standalone"),
    ("L'Étranger",                                      None, "standalone"),
    ("Le Petit Prince",                                 None, "standalone"),
    ("Germinal",                                        None, "standalone"),
    ("Le Grand Meaulnes",                               None, "standalone"),
    ("Voyage au bout de la nuit",                       None, "standalone"),
    ("La Condition humaine",                            None, "standalone"),
    ("L'Alchimiste",                                    None, "standalone"),
    ("Da Vinci Code",                                   None, "standalone"),
]

# ══════════════════════════════════════════════════════════════════════════════
#  SCORING
# ══════════════════════════════════════════════════════════════════════════════
def series_match(detected_name, expected_name):
    """Verifie si le nom detecte correspond a l'attendu (tolerant)."""
    if not expected_name:
        return False
    d = normalize(detected_name or "")
    e = normalize(expected_name)
    # Correspondance exacte ou incluse
    return d == e or e in d or d in e

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════
print()
print("=" * 72)
print("  TEST VERITE TERRAIN -- Pipeline serie BOOKTIME")
print(f"  {len(GROUND_TRUTH)} livres testes")
print("=" * 72)

results_by_source = defaultdict(lambda: {"ok": 0, "fail": 0, "cases": []})
TP = FP = TN = FN = 0
errors = []
wikidata_needed = []

# ── Passe 1 : pipeline rapide (sans Wikidata) ─────────────────────────────────
for title, expected_series, source in GROUND_TRUTH:
    res = detect_fast(title)
    is_series_expected = expected_series is not None
    is_series_detected = res["is_series"]
    detected_name = res.get("series_name") or ""

    # Evaluation
    if is_series_expected and is_series_detected:
        name_ok = series_match(detected_name, expected_series)
        if name_ok:
            TP += 1
            results_by_source[source]["ok"] += 1
        else:
            # Detecte comme serie mais mauvais nom
            FP += 1
            errors.append(("MAUVAIS NOM", title, expected_series, detected_name, source))
            results_by_source[source]["fail"] += 1
            results_by_source[source]["cases"].append((title, expected_series, detected_name))
    elif is_series_expected and not is_series_detected:
        FN += 1
        if source == "wikidata":
            wikidata_needed.append((title, expected_series))
        else:
            errors.append(("RATE", title, expected_series, "standalone", source))
            results_by_source[source]["fail"] += 1
            results_by_source[source]["cases"].append((title, expected_series, "non detecte"))
    elif not is_series_expected and is_series_detected:
        FP += 1
        errors.append(("FAUX POSITIF", title, "standalone", detected_name, source))
        results_by_source[source]["fail"] += 1
        results_by_source[source]["cases"].append((title, "standalone", detected_name))
    else:  # not expected, not detected -> TN
        TN += 1
        results_by_source[source]["ok"] += 1

# ── Passe 2 : Wikidata sur les cas marques "wikidata" ────────────────────────
wikidata_tp = wikidata_fp = wikidata_fn = 0
if wikidata_needed:
    print(f"\n  [Wikidata] Test sur {len(wikidata_needed)} series hors base statique...")
    for title, expected_series in wikidata_needed:
        try:
            wd = check_wikidata(title)
            time.sleep(0.3)
            if wd["series_name"]:
                if series_match(wd["series_name"], expected_series):
                    wikidata_tp += 1
                    TP += 1; FN -= 1
                    results_by_source["wikidata"]["ok"] += 1
                else:
                    wikidata_fp += 1
                    FP += 1; FN -= 1
                    errors.append(("WIKIDATA MAUVAIS NOM", title, expected_series, wd["series_name"], "wikidata"))
                    results_by_source["wikidata"]["fail"] += 1
            else:
                wikidata_fn += 1
                errors.append(("WIKIDATA RATE", title, expected_series, "standalone", "wikidata"))
                results_by_source["wikidata"]["fail"] += 1
        except Exception as e:
            errors.append(("WIKIDATA ERREUR", title, expected_series, str(e), "wikidata"))
    cache_save(CACHE)

# ── Resultats ─────────────────────────────────────────────────────────────────
total = len(GROUND_TRUTH)
precision = TP / (TP + FP) if (TP + FP) else 0
recall    = TP / (TP + FN) if (TP + FN) else 0
f1        = 2 * precision * recall / (precision + recall) if (precision + recall) else 0
accuracy  = (TP + TN) / total

print()
print("=" * 72)
print("  RESULTATS GLOBAUX")
print("=" * 72)
print(f"  Total testes     : {total}")
print(f"  Vrais positifs   : {TP}  (serie correctement detectee)")
print(f"  Faux negatifs    : {FN}  (serie ratee)")
print(f"  Vrais negatifs   : {TN}  (standalone correct)")
print(f"  Faux positifs    : {FP}  (fausse serie inventee)")
print()
print(f"  Precision        : {100*precision:.1f}%")
print(f"  Rappel           : {100*recall:.1f}%")
print(f"  F1-score         : {100*f1:.1f}%")
print(f"  Exactitude       : {100*accuracy:.1f}%")

print()
print("  Par source :")
for src in ["static", "wikidata", "standalone"]:
    d = results_by_source[src]
    tot = d["ok"] + d["fail"]
    pct = 100 * d["ok"] / tot if tot else 0
    print(f"    {src:<12} : {d['ok']}/{tot} OK  ({pct:.0f}%)")
if wikidata_needed:
    print(f"  Wikidata details : {wikidata_tp} trouves / {wikidata_fn} rates / {wikidata_fp} mauvais noms")

if errors:
    print()
    print(f"  Cas en echec ({len(errors)}) :")
    for typ, title, expected, got, src in errors:
        print(f"    [{typ}] \"{title}\"")
        print(f"             attendu: {expected}  |  obtenu: {got}")

print()
print("=" * 72)
print()
