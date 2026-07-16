"""Test rapide -- verite terrain uniquement, sans collecte OL ni Wikidata."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from demo_pipeline_v2 import detect_v2, series_match, check_wikidata_v2, CACHE, cache_save

GROUND_TRUTH = [
    ("Harry Potter and the Philosopher's Stone",        "Harry Potter"),
    ("Harry Potter and the Chamber of Secrets",         "Harry Potter"),
    ("Harry Potter and the Prisoner of Azkaban",        "Harry Potter"),
    ("Harry Potter and the Goblet of Fire",             "Harry Potter"),
    ("Harry Potter and the Order of the Phoenix",       "Harry Potter"),
    ("Harry Potter and the Half-Blood Prince",          "Harry Potter"),
    ("Harry Potter and the Deathly Hallows",            "Harry Potter"),
    ("Harry Potter à l'école des sorciers",             "Harry Potter"),
    ("Harry Potter et la Chambre des Secrets",          "Harry Potter"),
    ("The Fellowship of the Ring",                      "Le Seigneur des Anneaux"),
    ("The Two Towers",                                  "Le Seigneur des Anneaux"),
    ("The Return of the King",                          "Le Seigneur des Anneaux"),
    ("La Communauté de l'Anneau",                       "Le Seigneur des Anneaux"),
    ("Les Deux Tours",                                  "Le Seigneur des Anneaux"),
    ("Le Retour du Roi",                                "Le Seigneur des Anneaux"),
    ("Red Rising",                                      "Red Rising"),
    ("Golden Son",                                      "Red Rising"),
    ("Morning Star",                                    "Red Rising"),
    ("Dune",                                            "Dune"),
    ("Dune Messiah",                                    "Dune"),
    ("Children of Dune",                                "Dune"),
    ("Le Messie de Dune",                               "Dune"),
    ("The Hunger Games",                                "Hunger Games"),
    ("Catching Fire",                                   "Hunger Games"),
    ("Mockingjay",                                      "Hunger Games"),
    ("A Game of Thrones",                               "Le Trône de Fer"),
    ("A Clash of Kings",                                "Le Trône de Fer"),
    ("A Storm of Swords",                               "Le Trône de Fer"),
    ("Le Trône de Fer",                                 "Le Trône de Fer"),
    ("The Last Wish",                                   "The Witcher"),
    ("Blood of Elves",                                  "The Witcher"),
    ("Le Dernier Vœu",                                  "The Witcher"),
    ("Foundation",                                      "Fondation"),
    ("Foundation and Empire",                           "Fondation"),
    ("Second Foundation",                               "Fondation"),
    ("The Name of the Wind",                            "Chronique du Tueur de Roi"),
    ("The Wise Man's Fear",                             "Chronique du Tueur de Roi"),
    ("The Lightning Thief",                             "Percy Jackson"),
    ("The Sea of Monsters",                             "Percy Jackson"),
    ("The Titan's Curse",                               "Percy Jackson"),
    ("The Battle of the Labyrinth",                     "Percy Jackson"),
    ("The Last Olympian",                               "Percy Jackson"),
    ("Le Voleur de Foudre",                             "Percy Jackson"),
    ("Twilight",                                        "Twilight"),
    ("New Moon",                                        "Twilight"),
    ("Eclipse",                                         "Twilight"),
    ("Breaking Dawn",                                   "Twilight"),
    ("Fascination",                                     "Twilight"),
    ("Divergent",                                       "Divergent"),
    ("Insurgent",                                       "Divergent"),
    ("Allegiant",                                       "Divergent"),
    ("Leviathan Wakes",                                 "The Expanse"),
    ("Caliban's War",                                   "The Expanse"),
    ("Abaddon's Gate",                                  "The Expanse"),
    ("Nemesis Games",                                   "The Expanse"),
    ("The Final Empire",                                "Mistborn"),
    ("The Well of Ascension",                           "Mistborn"),
    ("The Hero of Ages",                                "Mistborn"),
    ("The Way of Kings",                                "The Stormlight Archive"),
    ("Words of Radiance",                               "The Stormlight Archive"),
    ("Oathbringer",                                     "The Stormlight Archive"),
    ("Rhythm of War",                                   "The Stormlight Archive"),
    ("The Eye of the World",                            "La Roue du Temps"),
    ("The Great Hunt",                                  "La Roue du Temps"),
    ("The Dragon Reborn",                               "La Roue du Temps"),
    ("La Roue du Temps",                                "La Roue du Temps"),
    ("One Piece, Vol. 1",                               "One Piece"),
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
    ("Astérix le Gaulois",                              "Astérix"),
    ("Astérix et les Goths",                            "Astérix"),
    ("Tintin au Tibet",                                 "Tintin"),
    ("Tintin au pays des Soviets",                      "Tintin"),
    ("Lucky Luke - La Mine d'or de Dick Digger",        "Lucky Luke"),
    ("Spirou et Fantasio - Les Héritiers",              "Spirou et Fantasio"),
    ("Thorgal - La Magicienne Trahie",                  "Thorgal"),
    ("Blake et Mortimer - Le Secret de l'Espadon",      "Blake et Mortimer"),
    ("Largo Winch - L'Héritier",                        "Largo Winch"),
    # Faux positifs connus a corriger
    ("Pool of Twilight",                                None),
    ("A magic of twilight",                             None),
    ("Witchery",                                        None),
    ("The Man Who Was Thursday",                        None),
    # Standalones confirmes
    ("1984",                                            None),
    ("Animal Farm",                                     None),
    ("The Catcher in the Rye",                          None),
    ("To Kill a Mockingbird",                           None),
    ("Carrie",                                          None),
    ("The Shining",                                     None),
    ("The Running Man",                                 None),
    ("Fahrenheit 451",                                  None),
    ("Les Misérables",                                  None),
    ("Le Petit Prince",                                 None),
    ("Da Vinci Code",                                   None),
    ("Gone with the Wind",                              None),
]

print()
print("=" * 68)
print("  TEST RAPIDE V2 -- Verite terrain (sans Wikidata)")
print(f"  {len(GROUND_TRUTH)} livres")
print("=" * 68)

TP = FP = TN = FN = 0
fn_list = []
fp_list = []

for title, expected in GROUND_TRUTH:
    res = detect_v2(title, use_wikidata=False)
    detected = res["is_series"]
    name = res.get("series_name") or ""
    method = res.get("method", "")

    if expected is None:
        if not detected:
            TN += 1
        else:
            FP += 1
            fp_list.append(f"  [FP] \"{title}\" -> \"{name}\" [{method}]")
    else:
        if detected and series_match(name, expected):
            TP += 1
        else:
            FN += 1
            fn_list.append(f"  [FN] \"{title}\" -> attendu: {expected}  obtenu: {name or 'standalone'} [{method}]")

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

if fp_list:
    print(f"\n  Faux positifs ({len(fp_list)}) :")
    for x in fp_list: print(x)

if fn_list:
    print(f"\n  Faux negatifs ({len(fn_list)}) :")
    for x in fn_list: print(x)

print("\n" + "=" * 68)
