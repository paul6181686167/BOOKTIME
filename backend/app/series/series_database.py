"""
Base de données de séries pour la détection backend.
Source de vérité synchronisée avec seriesDatabaseExtended.js (frontend).
Clés : name, authors, keywords, variations, exclusions, volume_titles, category
"""

SERIES_DATABASE = {
    # ═══════════════════ ROMANS ═══════════════════
    "harry_potter": {
        "name": "Harry Potter", "category": "roman",
        "authors": ["J.K. Rowling"],
        "keywords": ["harry potter", "poudlard", "hogwarts", "sorcier", "wizard", "voldemort", "hermione", "ron weasley"],
        "variations": ["harry potter", "hp", "potter"],
        "exclusions": ["fantastic beasts", "cursed child", "quidditch", "beedle", "hogwarts legacy"],
        "volume_titles": {
            1: "harry potter et l ecole des sorciers",
            2: "harry potter et la chambre des secrets",
            3: "harry potter et le prisonnier d azkaban",
            4: "harry potter et la coupe de feu",
            5: "harry potter et l ordre du phenix",
            6: "harry potter et le prince de sang mele",
            7: "harry potter et les reliques de la mort",
        },
    },
    "seigneur_anneaux": {
        "name": "Le Seigneur des Anneaux", "category": "roman",
        "authors": ["J.R.R. Tolkien"],
        "keywords": ["seigneur des anneaux", "lord of the rings", "tolkien", "frodon", "gandalf", "anneau unique", "mordor"],
        "variations": ["seigneur des anneaux", "lord of the rings", "lotr", "sda"],
        "exclusions": ["hobbit", "silmarillion", "rings of power", "unfinished tales"],
        "volume_titles": {
            1: "la communaute de l anneau",
            2: "les deux tours",
            3: "le retour du roi",
        },
    },
    "game_of_thrones": {
        "name": "Le Trône de Fer", "category": "roman",
        "authors": ["George R.R. Martin"],
        "keywords": ["game of thrones", "trone de fer", "westeros", "stark", "lannister", "targaryen", "ice and fire"],
        "variations": ["game of thrones", "trone de fer", "song of ice and fire", "asoiaf", "got"],
        "exclusions": ["house of dragon", "fire and blood", "world of ice"],
        "volume_titles": {
            1: "le trone de fer", 2: "le donjon rouge", 3: "la bataille des rois",
            4: "l ombre malefique", 5: "l invincible forteresse",
        },
    },
    "dune": {
        "name": "Dune", "category": "roman",
        "authors": ["Frank Herbert"],
        "keywords": ["dune", "arrakis", "paul atreides", "muad dib", "epice", "spice", "fremen", "desert"],
        "variations": ["dune", "cycles dune", "cycle de dune"],
        "exclusions": ["brian herbert", "kevin anderson", "prequel"],
        "volume_titles": {
            1: "dune", 2: "le messie de dune", 3: "les enfants de dune",
            4: "l empereur dieu de dune", 5: "les hereques de dune", 6: "la maison des meres",
        },
    },
    "fondation": {
        "name": "Fondation", "category": "roman",
        "authors": ["Isaac Asimov"],
        "keywords": ["fondation", "foundation", "asimov", "psychohistoire", "hari seldon", "empire galactique", "trantor"],
        "variations": ["fondation", "foundation", "cycle fondation"],
        "exclusions": ["robot", "empire series"],
        "volume_titles": {
            1: "fondation", 2: "fondation et empire", 3: "seconde fondation",
            4: "le bord de la fondation", 5: "fondation et terre", 6: "prelude a fondation", 7: "vers fondation",
        },
    },
    "witcher": {
        "name": "The Witcher", "category": "roman",
        "authors": ["Andrzej Sapkowski"],
        "keywords": ["witcher", "sorceleur", "geralt", "geralt de riv", "ciri", "yennefer", "sapkowski", "rivia"],
        "variations": ["witcher", "sorceleur", "geralt"],
        "exclusions": ["jeu video", "netflix"],
        "volume_titles": {
            1: "le dernier voeu", 2: "l epee de la providence", 3: "le sang des elfes",
            4: "le temps du mepris", 5: "le bapteme du feu", 6: "la tour aux alouettes",
            7: "la dame du lac", 8: "saisons des orages",
        },
    },
    "roue_du_temps": {
        "name": "La Roue du Temps", "category": "roman",
        "authors": ["Robert Jordan", "Brandon Sanderson"],
        "keywords": ["roue du temps", "wheel of time", "rand al thor", "aes sedai", "egwene", "jordan", "sanderson"],
        "variations": ["roue du temps", "wheel of time", "wot"],
        "exclusions": ["prequel"],
        "volume_titles": {},
    },
    "red_rising": {
        "name": "Red Rising", "category": "roman",
        "authors": ["Pierce Brown"],
        "keywords": ["red rising", "darrow", "pierce brown", "mars", "golds", "reds", "howler"],
        "variations": ["red rising", "red rising trilogy"],
        "exclusions": ["iron gold", "dark age", "light bringer", "red god"],
        "volume_titles": {1: "red rising", 2: "golden son", 3: "morning star"},
    },
    "iron_gold": {
        "name": "Iron Gold", "category": "roman",
        "authors": ["Pierce Brown"],
        "keywords": ["iron gold", "dark age", "light bringer", "red god", "lysander", "pierce brown"],
        "variations": ["iron gold", "red rising iron gold"],
        "exclusions": ["red rising", "golden son", "morning star"],
        "volume_titles": {1: "iron gold", 2: "dark age", 3: "light bringer", 4: "red god"},
    },
    "hunger_games": {
        "name": "Hunger Games", "category": "roman",
        "authors": ["Suzanne Collins"],
        "keywords": ["hunger games", "katniss", "panem", "mockingjay", "dystopia", "peeta"],
        "variations": ["hunger games", "jeux de la faim"],
        "exclusions": ["ballad songbirds"],
        "volume_titles": {1: "hunger games", 2: "l embrasement", 3: "la revolte"},
    },
    "divergent": {
        "name": "Divergent", "category": "roman",
        "authors": ["Veronica Roth"],
        "keywords": ["divergent", "tris", "four", "dauntless", "factions"],
        "variations": ["divergent", "divergente"],
        "exclusions": ["four collection"],
        "volume_titles": {1: "divergent", 2: "l insurrection", 3: "l alliee"},
    },
    "percy_jackson": {
        "name": "Percy Jackson", "category": "roman",
        "authors": ["Rick Riordan"],
        "keywords": ["percy jackson", "demi dieu", "olympe", "riordan", "poseidon", "athena"],
        "variations": ["percy jackson", "percy", "olympians"],
        "exclusions": ["heroes of olympus", "kane chronicles", "magnus chase", "trials apollo"],
        "volume_titles": {
            1: "le voleur de foudre", 2: "la mer des monstres",
            3: "le sort du titan", 4: "la bataille du labyrinthe", 5: "le dernier olympien",
        },
    },
    "twilight": {
        "name": "Twilight", "category": "roman",
        "authors": ["Stephenie Meyer"],
        "keywords": ["twilight", "bella", "edward cullen", "vampire", "werewolf", "forks"],
        "variations": ["twilight", "fascination", "crepuscule"],
        "exclusions": ["midnight sun", "bree tanner"],
        "volume_titles": {1: "fascination", 2: "tentation", 3: "hesitation", 4: "revelation"},
    },
    "discworld": {
        "name": "Les Annales du Disque-Monde", "category": "roman",
        "authors": ["Terry Pratchett"],
        "keywords": ["discworld", "disque monde", "pratchett", "rincewind", "ankh morpork", "vetinari"],
        "variations": ["discworld", "disque monde", "disque-monde", "annales"],
        "exclusions": [],
        "volume_titles": {},
    },
    "sherlock_holmes": {
        "name": "Sherlock Holmes", "category": "roman",
        "authors": ["Arthur Conan Doyle"],
        "keywords": ["sherlock holmes", "watson", "baker street", "moriarty", "conan doyle"],
        "variations": ["sherlock holmes", "sherlock", "holmes"],
        "exclusions": ["adaptations", "pastiches"],
        "volume_titles": {},
    },
    "maze_runner": {
        "name": "Le Labyrinthe", "category": "roman",
        "authors": ["James Dashner"],
        "keywords": ["maze runner", "labyrinthe", "thomas", "wicked", "blocards"],
        "variations": ["maze runner", "labyrinthe"],
        "exclusions": ["fever code"],
        "volume_titles": {1: "le labyrinthe", 2: "la ronce", 3: "le remede"},
    },
    "expanse": {
        "name": "The Expanse", "category": "roman",
        "authors": ["James S.A. Corey"],
        "keywords": ["expanse", "holden", "leviathan", "belter", "rocinante", "protomolecule"],
        "variations": ["expanse", "the expanse"],
        "exclusions": [],
        "volume_titles": {
            1: "leviathan wakes", 2: "caliban s war", 3: "abaddon s gate",
            4: "cibola burn", 5: "nemesis games", 6: "babylon s ashes",
            7: "persepolis rising", 8: "tiamat s wrath", 9: "leviathan falls",
        },
    },
    "mistborn": {
        "name": "Mistborn", "category": "roman",
        "authors": ["Brandon Sanderson"],
        "keywords": ["mistborn", "sanderson", "allomancy", "vin", "kelsier", "scadrial", "elend"],
        "variations": ["mistborn", "brume d acier"],
        "exclusions": ["stormlight", "way of kings"],
        "volume_titles": {
            1: "the final empire", 2: "the well of ascension", 3: "the hero of ages",
        },
    },
    "stormlight": {
        "name": "The Stormlight Archive", "category": "roman",
        "authors": ["Brandon Sanderson"],
        "keywords": ["stormlight", "kaladin", "shallan", "dalinar", "roshar", "sanderson"],
        "variations": ["stormlight archive", "stormlight"],
        "exclusions": ["mistborn"],
        "volume_titles": {
            1: "the way of kings", 2: "words of radiance",
            3: "oathbringer", 4: "rhythm of war",
        },
    },
    "nombre_vent": {
        "name": "Le Nom du Vent", "category": "roman",
        "authors": ["Patrick Rothfuss"],
        "keywords": ["nom du vent", "name of the wind", "kvothe", "rothfuss", "kingkiller"],
        "variations": ["nom du vent", "name of the wind", "kingkiller chronicle"],
        "exclusions": [],
        "volume_titles": {1: "le nom du vent", 2: "la peur du sage"},
    },
    # ═══════════════════ MANGAS ═══════════════════
    "one_piece": {
        "name": "One Piece", "category": "manga",
        "authors": ["Eiichiro Oda"],
        "keywords": ["one piece", "luffy", "pirates", "chapeau de paille", "grand line", "nakama"],
        "variations": ["one piece"],
        "exclusions": [],
        "volume_titles": {},
    },
    "naruto": {
        "name": "Naruto", "category": "manga",
        "authors": ["Masashi Kishimoto"],
        "keywords": ["naruto", "ninja", "konoha", "sasuke", "hokage", "akatsuki", "jutsu"],
        "variations": ["naruto", "boruto"],
        "exclusions": ["boruto standalone"],
        "volume_titles": {},
    },
    "dragon_ball": {
        "name": "Dragon Ball", "category": "manga",
        "authors": ["Akira Toriyama"],
        "keywords": ["dragon ball", "goku", "saiyan", "kamehameha", "vegeta", "gohan", "frieza"],
        "variations": ["dragon ball", "dragon ball z", "dragon ball super", "dbz"],
        "exclusions": [],
        "volume_titles": {},
    },
    "bleach": {
        "name": "Bleach", "category": "manga",
        "authors": ["Tite Kubo"],
        "keywords": ["bleach", "ichigo", "shinigami", "soul society", "hollow", "kubo"],
        "variations": ["bleach"],
        "exclusions": [],
        "volume_titles": {},
    },
    "attack_titan": {
        "name": "L'Attaque des Titans", "category": "manga",
        "authors": ["Hajime Isayama"],
        "keywords": ["attack on titan", "attaque des titans", "eren", "levi", "isayama", "titan", "shingeki"],
        "variations": ["attack on titan", "attaque des titans", "shingeki no kyojin"],
        "exclusions": [],
        "volume_titles": {},
    },
    "demon_slayer": {
        "name": "Demon Slayer", "category": "manga",
        "authors": ["Koyoharu Gotouge"],
        "keywords": ["demon slayer", "kimetsu no yaiba", "tanjiro", "nezuko", "hashira"],
        "variations": ["demon slayer", "kimetsu no yaiba"],
        "exclusions": [],
        "volume_titles": {},
    },
    "fullmetal": {
        "name": "Fullmetal Alchemist", "category": "manga",
        "authors": ["Hiromu Arakawa"],
        "keywords": ["fullmetal alchemist", "edward elric", "alphonse", "alchemy", "fma"],
        "variations": ["fullmetal alchemist", "fma", "frere de metal"],
        "exclusions": [],
        "volume_titles": {},
    },
    "death_note": {
        "name": "Death Note", "category": "manga",
        "authors": ["Tsugumi Ohba", "Takeshi Obata"],
        "keywords": ["death note", "light yagami", "ryuk", "kira", "l lawliet"],
        "variations": ["death note"],
        "exclusions": [],
        "volume_titles": {},
    },
    "jujutsu": {
        "name": "Jujutsu Kaisen", "category": "manga",
        "authors": ["Gege Akutami"],
        "keywords": ["jujutsu kaisen", "yuji itadori", "gojo satoru", "curse", "sukuna"],
        "variations": ["jujutsu kaisen", "jjk"],
        "exclusions": [],
        "volume_titles": {},
    },
    "my_hero": {
        "name": "My Hero Academia", "category": "manga",
        "authors": ["Kohei Horikoshi"],
        "keywords": ["my hero academia", "boku no hero", "izuku midoriya", "deku", "all might", "quirk"],
        "variations": ["my hero academia", "boku no hero academia", "bnha", "mha"],
        "exclusions": [],
        "volume_titles": {},
    },
    # ═══════════════════ BD ═══════════════════
    "asterix": {
        "name": "Astérix", "category": "bd",
        "authors": ["René Goscinny", "Albert Uderzo", "Jean-Yves Ferri"],
        "keywords": ["asterix", "asterix", "obelix", "gaulois", "potion magique", "village gaulois"],
        "variations": ["asterix", "asterix"],
        "exclusions": [],
        "volume_titles": {},
    },
    "tintin": {
        "name": "Tintin", "category": "bd",
        "authors": ["Hergé"],
        "keywords": ["tintin", "milou", "capitaine haddock", "tournesol", "dupont", "dupond", "herge"],
        "variations": ["tintin", "les aventures de tintin"],
        "exclusions": [],
        "volume_titles": {},
    },
    "lucky_luke": {
        "name": "Lucky Luke", "category": "bd",
        "authors": ["Morris", "René Goscinny"],
        "keywords": ["lucky luke", "jolly jumper", "dalton", "cowboy", "far west"],
        "variations": ["lucky luke"],
        "exclusions": [],
        "volume_titles": {},
    },
    "spirou": {
        "name": "Spirou et Fantasio", "category": "bd",
        "authors": ["André Franquin"],
        "keywords": ["spirou", "fantasio", "marsupilami", "franquin"],
        "variations": ["spirou", "spirou et fantasio"],
        "exclusions": [],
        "volume_titles": {},
    },
    "largo_winch": {
        "name": "Largo Winch", "category": "bd",
        "authors": ["Jean Van Hamme", "Philippe Francq"],
        "keywords": ["largo winch", "winch", "groupe w", "milliardaire"],
        "variations": ["largo winch"],
        "exclusions": [],
        "volume_titles": {},
    },
    "blake_mortimer": {
        "name": "Blake et Mortimer", "category": "bd",
        "authors": ["Edgar P. Jacobs"],
        "keywords": ["blake et mortimer", "blake", "mortimer", "jacobs"],
        "variations": ["blake et mortimer", "blake mortimer"],
        "exclusions": [],
        "volume_titles": {},
    },
    "thorgal": {
        "name": "Thorgal", "category": "bd",
        "authors": ["Jean Van Hamme", "Grzegorz Rosiński"],
        "keywords": ["thorgal", "aaricia", "viking", "nordique", "rosinski"],
        "variations": ["thorgal"],
        "exclusions": [],
        "volume_titles": {},
    },
}


def normalize_for_detect(s: str) -> str:
    """Normalise une chaîne pour la détection : minuscules, sans accents, sans ponctuation."""
    import unicodedata
    import re
    s = unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode('utf-8')
    s = re.sub(r"[''`\-]", ' ', s)
    s = re.sub(r"[^a-z0-9\s]", '', s.lower())
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def detect_series_from_database(title: str, author: str = "") -> list:
    """
    Détecte les séries correspondantes depuis SERIES_DATABASE.
    Retourne une liste de {series_name, confidence, volume_number} triée par confiance.
    """
    title_norm = normalize_for_detect(title)
    author_norm = normalize_for_detect(author)
    results = []

    for key, series in SERIES_DATABASE.items():
        confidence = 0
        volume_number = None

        # 1. Nom de série dans le titre (poids fort)
        name_norm = normalize_for_detect(series["name"])
        if name_norm in title_norm:
            confidence += 80

        # 2. Variations
        for var in series.get("variations", []):
            var_norm = normalize_for_detect(var)
            if var_norm in title_norm:
                confidence = max(confidence, 75)
                break

        # 3. Titres de volumes exacts
        for num, vol_title in series.get("volume_titles", {}).items():
            if normalize_for_detect(vol_title) == title_norm:
                confidence = max(confidence, 95)
                volume_number = int(num)
                break

        # 4. Auteur (signal complémentaire, pas suffisant seul)
        if author_norm:
            for auth in series.get("authors", []):
                if normalize_for_detect(auth) in author_norm or author_norm in normalize_for_detect(auth):
                    confidence += 20
                    break

        # 5. Mots-clés dans le titre
        kw_hits = sum(1 for kw in series.get("keywords", []) if kw in title_norm)
        confidence += kw_hits * 10

        # 6. Exclusions : annuler si le titre correspond à une exclusion
        for excl in series.get("exclusions", []):
            if normalize_for_detect(excl) in title_norm:
                confidence = 0
                break

        # Seuil minimal + confidence uniquement auteur insuffisante
        if confidence >= 40 and not (confidence == 20):  # 20 = seulement auteur
            results.append({
                "series_name": series["name"],
                "confidence": min(confidence, 100),
                "volume_number": volume_number,
                "category": series.get("category", "roman"),
            })

    return sorted(results, key=lambda x: x["confidence"], reverse=True)
