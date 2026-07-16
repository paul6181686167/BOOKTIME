"""
PIPELINE V2 -- Detection de serie BOOKTIME (version corrigee et etendue)
Corrections vs V1 :
  1. Base statique etendue : 60+ series EN+FR (romans, mangas, BD, SF, polar)
  2. Detection "nom serie contenu dans titre" avec nettoyage Vol/# 
  3. Format "Serie - Titre album" (BD)
  4. series_match multilingue (insensible aux traductions)
  5. Wikidata avec cache persistent
"""
import re, unicodedata, json, requests, time
from pathlib import Path

# ── Cache Wikidata ─────────────────────────────────────────────────────────────
CACHE_FILE = Path("demo_series_cache_v2.json")
CACHE = json.loads(CACHE_FILE.read_text(encoding="utf-8")) if CACHE_FILE.exists() else {}

def cache_save():
    CACHE_FILE.write_text(json.dumps(CACHE, ensure_ascii=False, indent=2), encoding="utf-8")

# ── Normalisation ──────────────────────────────────────────────────────────────
def norm(s):
    """Minuscules, sans accents, sans ponctuation, sans articles ni prepositions."""
    s = s or ""
    # Ligatures et caracteres speciaux avant NFD
    _ligatures = {"œ": "oe", "æ": "ae", "ø": "o", "ß": "ss", "þ": "th", "ð": "d"}
    for src, dst in _ligatures.items():
        s = s.replace(src, dst).replace(src.upper(), dst)
    # "'s" → "s" (possessif anglais) avant de retirer toutes les apostrophes
    s = re.sub(r"'s\b", "s", s, flags=re.IGNORECASE)
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[''`\-]", " ", s.lower())
    s = re.sub(r"[^a-z0-9\s]", "", s)
    # Articles + prepositions FR et EN + particule japonaise "no"
    s = re.sub(r"\b(le|la|les|l|the|a|an|de|du|des|un|une|of|in|to|for|on|at|by|with|and|et|au|aux|no)\b", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def strip_volume_suffix(s):
    """Retire les suffixes de volume : ', Vol. 3', ' #5', ' Book 2', ' Tome 3', etc."""
    s = re.sub(r"[,\s]*[\(]?\s*(?:vol\.?|volume|book|tome|t\.?|part|ch\.?|chapter|#)\s*[\d]+[\)]?.*$",
               "", s, flags=re.IGNORECASE).strip()
    return s

def series_match(detected, expected):
    """Correspondance tolerante entre deux noms de serie (multilingue)."""
    if not detected or not expected:
        return False
    d, e = norm(detected), norm(expected)
    if d == e or e in d or d in e:
        return True
    # Tolerance supplementaire : tous les mots de 4+ lettres de l'un dans l'autre
    words_d = set(w for w in d.split() if len(w) >= 4)
    words_e = set(w for w in e.split() if len(w) >= 4)
    if words_d and words_e and len(words_d & words_e) >= min(1, len(words_e) - 1):
        return True
    return False

# ══════════════════════════════════════════════════════════════════════════════
#  BASE STATIQUE ETENDUE (60+ series)
#  Cles : nom normalise de la serie
#  Chaque entree :
#    name       : nom d'affichage
#    vol_titles : {titre_normalise: numero} -- titres exacts de volumes
#    aliases    : [noms alternatifs de la serie, normalises]
#    keywords   : mots distinctifs (au moins 2 requis)
#    excl       : mots qui invalident la detection
# ══════════════════════════════════════════════════════════════════════════════
_S = [
    # ── ROMANS FANTASY / SF ───────────────────────────────────────────────────
    {
        "name": "Harry Potter",
        "aliases": ["harry potter", "hp", "hogwarts saga"],
        "vol_titles": {
            "harry potter philosophers stone": 1, "harry potter sorcerers stone": 1,
            "harry potter ecole des sorciers": 1, "harry potter chamber secrets": 2,
            "harry potter chambre secrets": 2, "harry potter prisoner azkaban": 3,
            "harry potter prisonnier azkaban": 3, "harry potter goblet fire": 4,
            "harry potter coupe feu": 4, "harry potter order phoenix": 5,
            "harry potter ordre phenix": 5, "harry potter half blood prince": 6,
            "harry potter prince sang mele": 6, "harry potter deathly hallows": 7,
            "harry potter reliques mort": 7,
        },
        "keywords": ["hogwarts", "hermione", "voldemort", "poudlard", "dumbledore"],
        "excl": ["fantastic beasts", "cursed child", "quidditch"],
    },
    {
        "name": "Le Seigneur des Anneaux",
        "aliases": ["seigneur anneaux", "lord rings", "lotr", "lord of the rings"],
        "vol_titles": {
            "fellowship ring": 1, "communaute anneau": 1,
            "two towers": 2, "deux tours": 2,
            "return king": 3, "retour roi": 3,
        },
        "keywords": ["tolkien", "frodon", "gandalf", "mordor", "anneau unique"],
        "excl": ["hobbit", "silmarillion", "rings of power"],
    },
    {
        "name": "Red Rising",
        "aliases": ["red rising"],
        "vol_titles": {"red rising": 1, "golden son": 2, "morning star": 3},
        "keywords": ["darrow", "pierce brown", "golds", "reds", "howler"],
        "excl": ["iron gold", "dark age", "light bringer"],
    },
    {
        "name": "Iron Gold",
        "aliases": ["iron gold"],
        "vol_titles": {"iron gold": 1, "dark age": 2, "light bringer": 3, "red god": 4},
        "keywords": ["lysander", "pierce brown", "lyria"],
        "excl": ["red rising", "golden son", "morning star"],
    },
    {
        "name": "Dune",
        "aliases": ["dune", "cycles dune"],
        "vol_titles": {
            "dune": 1, "dune messiah": 2, "messie dune": 2,
            "children dune": 3, "enfants dune": 3,
            "god emperor dune": 4, "emperor dieu dune": 4,
            "heretics dune": 5, "heretiques dune": 5,
            "chapterhouse dune": 6, "maison meres": 6,
        },
        "keywords": ["arrakis", "paul atreides", "fremen", "spice", "epice", "muad dib"],
        "excl": ["brian herbert", "kevin anderson"],
    },
    {
        "name": "Le Trône de Fer",
        "aliases": ["game thrones", "trone fer", "song ice fire", "asoiaf"],
        "vol_titles": {
            "game thrones": 1, "trone fer": 1,
            "clash kings": 2, "donjon rouge": 2,
            "storm swords": 3, "bataille rois": 3,
            "feast crows": 4, "festin corbeaux": 4,
            "dance dragons": 5, "danse dragons": 5,
        },
        "keywords": ["westeros", "stark", "lannister", "targaryen", "cersei", "daenerys"],
        "excl": ["house dragon", "fire blood"],
    },
    {
        "name": "Hunger Games",
        "aliases": ["hunger games", "jeux faim"],
        "vol_titles": {
            "hunger games": 1, "catching fire": 2, "embrasement": 2,
            "mockingjay": 3, "revolte": 3,
        },
        "keywords": ["katniss", "panem", "peeta", "district"],
        "excl": ["ballad songbirds"],
    },
    {
        "name": "The Witcher",
        "aliases": ["witcher", "sorceleur"],
        "vol_titles": {
            "last wish": 1, "dernier voeu": 1,
            "sword destiny": 2, "epee providence": 2,
            "blood elves": 3, "sang elfes": 3,
            "time contempt": 4, "temps mepris": 4,
            "baptism fire": 5, "bapteme feu": 5,
            "tower swallows": 6, "tour alouettes": 6,
            "lady lake": 7, "dame lac": 7,
            "season storms": 8, "saisons orages": 8,
        },
        "keywords": ["geralt", "ciri", "yennefer", "sorceleur", "rivia"],
        "excl": ["netflix", "jeu video"],
    },
    {
        "name": "Fondation",
        "aliases": ["foundation", "fondation", "cycle fondation"],
        "vol_titles": {
            "foundation": 1, "fondation": 1,
            "foundation empire": 2, "fondation empire": 2,
            "second foundation": 3, "seconde fondation": 3,
            "edge foundation": 4, "bord fondation": 4,
            "foundation earth": 5, "fondation terre": 5,
            "prelude foundation": 6, "prelude fondation": 6,
            "forward foundation": 7, "vers fondation": 7,
        },
        "keywords": ["asimov", "psychohistoire", "hari seldon", "trantor"],
        "excl": [],
    },
    {
        "name": "Chronique du Tueur de Roi",
        "aliases": ["name wind", "nom vent", "kingkiller chronicle"],
        "vol_titles": {
            "name wind": 1, "nom vent": 1,
            "wise mans fear": 2, "peur sage": 2,
        },
        "keywords": ["kvothe", "rothfuss", "university", "chandrian"],
        "excl": [],
    },
    {
        "name": "Percy Jackson",
        "aliases": ["percy jackson", "percy olympians"],
        "vol_titles": {
            "lightning thief": 1, "voleur foudre": 1,
            "sea monsters": 2, "mer monstres": 2,
            "titans curse": 3, "titan s curse": 3, "sort titan": 3,
            "battle labyrinth": 4, "bataille labyrinthe": 4,
            "last olympian": 5, "dernier olympien": 5,
            "lightning thief percy jackson": 1,
        },
        "keywords": ["percy", "annabeth", "poseidon", "olympe", "camp half blood", "grover"],
        "excl": ["heroes olympus", "kane chronicles", "magnus chase", "trials apollo"],
    },
    {
        "name": "Twilight",
        "aliases": ["twilight", "fascination", "crepuscule"],
        "vol_titles": {
            "twilight": 1, "fascination": 1,
            "new moon": 2, "tentation": 2,
            "eclipse": 3, "hesitation": 3,
            "breaking dawn": 4, "revelation": 4,
        },
        "keywords": ["bella", "edward cullen", "vampire", "forks", "cullen"],
        "excl": ["midnight sun", "bree tanner"],
    },
    {
        "name": "Divergent",
        "aliases": ["divergent", "divergente"],
        "vol_titles": {
            "divergent": 1, "insurgent": 2, "insurrection": 2,
            "allegiant": 3, "alliee": 3,
        },
        "keywords": ["tris", "four", "dauntless", "factions", "abnegation"],
        "excl": ["four collection"],
    },
    {
        "name": "The Maze Runner",
        "aliases": ["maze runner", "labyrinthe"],
        "vol_titles": {
            "maze runner": 1, "labyrinthe": 1,
            "scorch trials": 2, "ronce": 2,
            "death cure": 3, "remede": 3,
        },
        "keywords": ["thomas", "wicked", "gladers", "glade", "newt"],
        "excl": ["fever code"],
    },
    {
        "name": "The Expanse",
        "aliases": ["expanse"],
        "vol_titles": {
            "leviathan wakes": 1,
            "calibans war": 2, "caliban war": 2, "caliban s war": 2,
            "abaddons gate": 3, "abaddon gate": 3, "abaddon s gate": 3,
            "cibola burn": 4,
            "nemesis games": 5, "babylon ashes": 6,
            "persepolis rising": 7, "tiamats wrath": 8,
            "leviathan falls": 9,
        },
        "keywords": ["holden", "rocinante", "belter", "protomolecule", "james corey"],
        "excl": [],
    },
    {
        "name": "Mistborn",
        "aliases": ["mistborn"],
        "vol_titles": {
            "final empire": 1, "well ascension": 2, "hero ages": 3,
            "alloy law": 4, "shadows self": 5, "bands mourning": 6,
        },
        "keywords": ["allomancy", "sanderson", "vin", "kelsier", "scadrial"],
        "excl": ["stormlight"],
    },
    {
        "name": "The Stormlight Archive",
        "aliases": ["stormlight archive", "stormlight"],
        "vol_titles": {
            "way kings": 1, "words radiance": 2,
            "oathbringer": 3, "rhythm war": 4, "wind light": 5,
        },
        "keywords": ["kaladin", "shallan", "dalinar", "roshar", "highstorm", "spren"],
        "excl": ["mistborn"],
    },
    {
        "name": "La Roue du Temps",
        "aliases": ["wheel time", "roue temps", "wot"],
        "vol_titles": {
            "eye world": 1, "great hunt": 2, "dragon reborn": 3,
            "shadow rising": 4, "fires heaven": 5, "lord chaos": 6,
            "crown swords": 7, "path daggers": 8, "winters heart": 9,
            "crossroads twilight": 10, "knife dreams": 11,
            "gathering storm": 12, "towers midnight": 13, "memory light": 14,
            "roue temps": 1, "oeil monde": 1,
        },
        "keywords": ["rand al thor", "aes sedai", "egwene", "robert jordan", "perrin"],
        "excl": [],
    },
    {
        "name": "Discworld",
        "aliases": ["discworld", "disque monde", "annales disque monde"],
        "vol_titles": {},
        "keywords": ["pratchett", "ankh morpork", "rincewind", "vetinari", "death"],
        "excl": [],
    },
    {
        "name": "The Hitchhiker's Guide to the Galaxy",
        "aliases": ["hitchhiker guide galaxy", "guide voyageur galactique", "h2g2"],
        "vol_titles": {
            "hitchhikers guide galaxy": 1, "guide voyageur galactique": 1,
            "restaurant end universe": 2, "restaurant bout univers": 2,
            "life universe everything": 3, "so long thanks fish": 4,
            "mostly harmless": 5,
        },
        "keywords": ["adams", "arthur dent", "ford prefect", "zaphod", "42"],
        "excl": [],
    },
    {
        "name": "Les Chroniques de Narnia",
        "aliases": ["chronicles narnia", "chroniques narnia", "narnia"],
        "vol_titles": {
            "lion witch wardrobe": 1, "lion sorciere armoire": 1,
            "prince caspian": 2,
            "voyage dawn treader": 3, "navigateur aurore": 3,
            "silver chair": 4, "fauteuil argent": 4,
            "horse boy": 5, "cheval garcon": 5,
            "magicians nephew": 6, "neveu magicien": 6,
            "last battle": 7, "derniere bataille": 7,
        },
        "keywords": ["aslan", "lewis", "narnia", "wardrobe", "pevensie"],
        "excl": [],
    },
    {
        "name": "Ender's Game",
        "aliases": ["enders game", "cycle ender"],
        "vol_titles": {
            "enders game": 1, "jeu ender": 1,
            "speaker dead": 2, "porte parole morts": 2,
            "xenocide": 3, "children mind": 4,
        },
        "keywords": ["ender", "wiggin", "orson scott card", "buggers", "formics"],
        "excl": [],
    },
    {
        "name": "Millennium",
        "aliases": ["millennium", "millenium", "stieg larsson"],
        "vol_titles": {
            "girl dragon tattoo": 1, "hommes qui aimaient femmes": 1,
            "girl played fire": 2, "fille jouait feu": 2,
            "girl kicked hornets nest": 3, "reine dans palais courants air": 3,
        },
        "keywords": ["lisbeth salander", "blomkvist", "larsson", "dragon tattoo"],
        "excl": [],
    },
    {
        "name": "Sherlock Holmes",
        "aliases": ["sherlock holmes"],
        "vol_titles": {
            "study scarlet": 1, "etude ecarlate": 1,
            "sign four": 2, "signe quatre": 2,
            "hound baskervilles": 3, "chien baskervilles": 3,
        },
        "keywords": ["holmes", "watson", "baker street", "moriarty", "conan doyle"],
        "excl": ["adaptations", "pastiche"],
    },
    {
        "name": "Hercule Poirot",
        "aliases": ["hercule poirot", "poirot"],
        "vol_titles": {},
        "keywords": ["poirot", "agatha christie", "cellules grises", "hastings"],
        "excl": ["miss marple"],
    },
    {
        "name": "Miss Marple",
        "aliases": ["miss marple"],
        "vol_titles": {},
        "keywords": ["miss marple", "agatha christie", "st mary mead"],
        "excl": ["poirot"],
    },
    # ── SF / THRILLER ─────────────────────────────────────────────────────────
    {
        "name": "Jack Ryan",
        "aliases": ["jack ryan", "tom clancy"],
        "vol_titles": {
            "hunt red october": 1, "chasse octobre rouge": 1,
            "red storm rising": 2, "tempete rouge": 2,
            "patriot games": 3, "jeux patriotes": 3,
        },
        "keywords": ["clancy", "cia", "ryan", "submarine", "hunt october"],
        "excl": [],
    },
    {
        "name": "James Bond",
        "aliases": ["james bond", "007"],
        "vol_titles": {
            "casino royale": 1, "live let die": 2, "moonraker": 3,
            "diamonds forever": 4, "russia love": 5,
        },
        "keywords": ["bond", "007", "mi6", "fleming", "mi5", "q branch"],
        "excl": [],
    },
    # ── MANGAS ───────────────────────────────────────────────────────────────
    {
        "name": "One Piece",
        "aliases": ["one piece"],
        "vol_titles": {},
        "keywords": ["luffy", "pirates", "chapeau paille", "grand line", "nakama", "oda"],
        "excl": [],
    },
    {
        "name": "Naruto",
        "aliases": ["naruto"],
        "vol_titles": {},
        "keywords": ["naruto", "ninja", "konoha", "sasuke", "hokage", "akatsuki"],
        "excl": ["boruto"],
    },
    {
        "name": "Dragon Ball",
        "aliases": ["dragon ball", "dragonball", "dbz", "dragon ball z", "dragon ball super"],
        "vol_titles": {},
        "keywords": ["goku", "saiyan", "kamehameha", "vegeta", "gohan", "toriyama"],
        "excl": [],
    },
    {
        "name": "Bleach",
        "aliases": ["bleach"],
        "vol_titles": {},
        "keywords": ["ichigo", "shinigami", "soul society", "hollow", "kubo"],
        "excl": [],
    },
    {
        "name": "L'Attaque des Titans",
        "aliases": ["attack titan", "attaque titans", "shingeki kyojin"],
        "vol_titles": {},
        "keywords": ["eren", "levi", "titan", "isayama", "wall", "survey corps"],
        "excl": [],
    },
    {
        "name": "Death Note",
        "aliases": ["death note"],
        "vol_titles": {},
        "keywords": ["light yagami", "ryuk", "kira", "lawliet", "shinigami notebook"],
        "excl": [],
    },
    {
        "name": "Fullmetal Alchemist",
        "aliases": ["fullmetal alchemist", "frere metal", "fma"],
        "vol_titles": {},
        "keywords": ["edward elric", "alphonse", "alchemy", "homunculus", "arakawa"],
        "excl": [],
    },
    {
        "name": "My Hero Academia",
        "aliases": ["my hero academia", "boku hero academia", "bnha", "mha"],
        "vol_titles": {},
        "keywords": ["izuku midoriya", "deku", "all might", "quirk", "horikoshi"],
        "excl": [],
    },
    {
        "name": "Jujutsu Kaisen",
        "aliases": ["jujutsu kaisen", "jjk"],
        "vol_titles": {},
        "keywords": ["yuji itadori", "gojo satoru", "curse", "sukuna", "akutami"],
        "excl": [],
    },
    {
        "name": "Demon Slayer",
        "aliases": ["demon slayer", "kimetsu yaiba"],
        "vol_titles": {},
        "keywords": ["tanjiro", "nezuko", "hashira", "demon", "gotouge"],
        "excl": [],
    },
    {
        "name": "Sword Art Online",
        "aliases": ["sword art online", "sao"],
        "vol_titles": {},
        "keywords": ["kirito", "asuna", "aincrad", "vrmmorpg", "kawahara"],
        "excl": [],
    },
    {
        "name": "Tokyo Ghoul",
        "aliases": ["tokyo ghoul"],
        "vol_titles": {},
        "keywords": ["kaneki", "ghoul", "ccg", "ishida", "tokyo"],
        "excl": [],
    },
    # ── BD ────────────────────────────────────────────────────────────────────
    {
        "name": "Astérix",
        "aliases": ["asterix", "asterix"],
        "vol_titles": {
            "asterix gaulois": 1, "asterix goths": 3, "asterix gladiateur": 4,
            "asterix jeux olympiques": 12, "asterix barde": 5,
        },
        "keywords": ["obelix", "gaulois", "potion magique", "cacofonix", "abraracourcix"],
        "excl": [],
    },
    {
        "name": "Tintin",
        "aliases": ["tintin", "aventures tintin"],
        "vol_titles": {
            "tintin soviets": 1, "tintin tibet": 20,
            "tintin congo": 2, "temple soleil": 14,
            "tintin amerique": 3, "affaire tournesol": 18,
        },
        "keywords": ["milou", "capitaine haddock", "tournesol", "dupont", "dupond", "herge"],
        "excl": [],
    },
    {
        "name": "Lucky Luke",
        "aliases": ["lucky luke"],
        "vol_titles": {},
        "keywords": ["jolly jumper", "dalton", "cowboy", "lucky luke", "morris"],
        "excl": [],
    },
    {
        "name": "Spirou et Fantasio",
        "aliases": ["spirou fantasio", "spirou"],
        "vol_titles": {},
        "keywords": ["spirou", "fantasio", "marsupilami", "franquin", "groom"],
        "excl": [],
    },
    {
        "name": "Thorgal",
        "aliases": ["thorgal"],
        "vol_titles": {},
        "keywords": ["thorgal", "aaricia", "viking", "rosinski", "van hamme"],
        "excl": [],
    },
    {
        "name": "Blake et Mortimer",
        "aliases": ["blake mortimer", "blake et mortimer"],
        "vol_titles": {},
        "keywords": ["blake", "mortimer", "jacobs", "espadon", "yellow mark"],
        "excl": [],
    },
    {
        "name": "Largo Winch",
        "aliases": ["largo winch"],
        "vol_titles": {},
        "keywords": ["largo winch", "groupe w", "milliardaire", "francq"],
        "excl": [],
    },
    {
        "name": "XIII",
        "aliases": ["xiii"],
        "vol_titles": {},
        "keywords": ["xiii", "vance", "van hamme", "tatouage", "amnesia"],
        "excl": [],
    },
    {
        "name": "Les Fourmis",
        "aliases": ["fourmis", "werber fourmis"],
        "vol_titles": {
            "fourmis": 1, "jour fourmis": 2, "revolution fourmis": 3,
        },
        "keywords": ["bernard werber", "fourmis", "103683", "insecte"],
        "excl": [],
    },
]

# ── Construction de l'index ────────────────────────────────────────────────────
SERIES_INDEX = {}  # cle_normalisee -> series_data
ALIAS_INDEX  = {}  # alias_normalise -> series_data
KEYWORD_INDEX = {} # keyword -> [series_data, ...]

for s in _S:
    key = norm(s["name"])
    SERIES_INDEX[key] = s
    for alias in s["aliases"]:
        ALIAS_INDEX[norm(alias)] = s
    for kw in s["keywords"]:
        KEYWORD_INDEX.setdefault(norm(kw), []).append(s)

# ══════════════════════════════════════════════════════════════════════════════
#  DETECTION STATIQUE
# ══════════════════════════════════════════════════════════════════════════════
def check_static_v2(title: str, saga_ol: str = "") -> dict | None:
    """
    Detecte la serie d'un livre via la base statique.
    Strategies dans l'ordre :
      A. Champ saga OL exact
      B. Titre exact de volume
      C. Alias de serie dans le titre nettoye
      D. Nom de serie dans le titre nettoye
      E. Mots-cles distinctifs (>= 2)
    """
    t_raw  = norm(title)
    t_clean = norm(strip_volume_suffix(title))  # titre sans "Vol. 3", "Book 2", etc.

    # ── A. Saga OL ────────────────────────────────────────────────────────────
    if saga_ol:
        s_ol = norm(saga_ol)
        for key, s in {**SERIES_INDEX, **ALIAS_INDEX}.items():
            if series_match(s["name"], saga_ol):
                if not _is_excluded(t_raw, s):
                    return {"series_name": s["name"], "volume": None, "method": "ol_saga"}

    # ── B. Titre exact de volume ───────────────────────────────────────────────
    for key, s in SERIES_INDEX.items():
        for vol_title, vol_num in s.get("vol_titles", {}).items():
            if norm(vol_title) == t_raw or norm(vol_title) == t_clean:
                if not _is_excluded(t_raw, s):
                    return {"series_name": s["name"], "volume": vol_num, "method": "vol_title"}

    # ── C. Alias dans le titre ────────────────────────────────────────────────
    # Regle : l'alias doit etre au DEBUT du titre normalise, suivi d'un espace ou de rien
    # Evite "pool of twilight" → Twilight, "witchery" → Witcher
    for alias, s in ALIAS_INDEX.items():
        if _starts_with_token(t_clean, alias) or _starts_with_token(t_raw, alias):
            if not _is_excluded(t_raw, s):
                return {"series_name": s["name"], "volume": None, "method": "alias_in_title"}

    # ── D. Nom de serie dans le titre ─────────────────────────────────────────
    for key, s in SERIES_INDEX.items():
        if _starts_with_token(t_clean, key) or _starts_with_token(t_raw, key):
            if not _is_excluded(t_raw, s):
                return {"series_name": s["name"], "volume": None, "method": "name_in_title"}

    # ── E. Mots-cles (>= 2 requis, sauf serie a 1 mot-cle tres specifique) ────
    hits = {}
    for kw, series_list in KEYWORD_INDEX.items():
        if kw in t_raw:
            for s in series_list:
                hits.setdefault(s["name"], {"s": s, "count": 0})["count"] += 1
    for sname, h in hits.items():
        if h["count"] >= 2 and not _is_excluded(t_raw, h["s"]):
            return {"series_name": sname, "volume": None, "method": f"keywords({h['count']})"}

    return None

def _starts_with_token(text: str, prefix: str) -> bool:
    """
    Verifie que 'text' commence par 'prefix' et que le caractere suivant
    est un espace ou la fin de chaine (evite les faux positifs par sous-chaine).
    Ex: 'witchery'.startswith('witcher') mais le char suivant est 'y' → False
        'witcher vol 3'.startswith('witcher') et char suivant est ' ' → True
    """
    if not prefix:
        return False
    if text == prefix:
        return True
    if text.startswith(prefix) and (len(text) == len(prefix) or text[len(prefix)] == " "):
        return True
    return False


def _is_excluded(title_norm: str, series_data: dict) -> bool:
    return any(norm(e) in title_norm for e in series_data.get("excl", []))

# ══════════════════════════════════════════════════════════════════════════════
#  DETECTION WIKIDATA
# ══════════════════════════════════════════════════════════════════════════════
HEADERS = {"User-Agent": "BooktimePipelineV2/1.0"}

def _wd_search(title):
    r = requests.get("https://www.wikidata.org/w/api.php", params={
        "action": "wbsearchentities", "search": title,
        "language": "en", "type": "item", "limit": 5, "format": "json",
    }, headers=HEADERS, timeout=10)
    return r.json().get("search", []) if r.ok else []

def _wd_entity(qid):
    r = requests.get(f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json",
                     headers=HEADERS, timeout=10)
    if not r.ok:
        return None
    return r.json().get("entities", {}).get(qid)

def _is_book(candidate, entity):
    desc = (candidate.get("description") or "").lower()
    if any(k in desc for k in ["novel","book","manga","comic","roman","fiction","fantasy","series","light novel"]):
        return True
    p31_types = {"Q7725634","Q571","Q8274","Q2831984","Q47461344","Q277759","Q1266946","Q3331189"}
    for c in (entity or {}).get("claims", {}).get("P31", []):
        if c.get("mainsnak",{}).get("datavalue",{}).get("value",{}).get("id") in p31_types:
            return True
    return False

def _get_label(entity, langs=("fr","en")):
    labels = (entity or {}).get("labels", {})
    for l in langs:
        if l in labels:
            return labels[l]["value"]
    return None

def check_wikidata_v2(title: str) -> dict:
    """Interroge Wikidata avec cache. Retourne {series_name, volume, method}."""
    key = norm(title)
    if key in CACHE:
        return CACHE[key]

    variants = [title]
    if not title.lower().startswith("the "):
        variants.append("The " + title)

    for variant in variants:
        candidates = _wd_search(variant)
        for candidate in candidates[:4]:
            qid = candidate["id"]
            entity = _wd_entity(qid)
            time.sleep(0.15)
            if not entity or not _is_book(candidate, entity):
                continue
            p179 = entity.get("claims", {}).get("P179", [])
            if not p179:
                result = {"series_name": None, "volume": None, "method": "wd_standalone"}
                CACHE[key] = result; cache_save(); return result
            series_qid = p179[0].get("mainsnak",{}).get("datavalue",{}).get("value",{}).get("id")
            volume = None
            for q in p179[0].get("qualifiers", {}).get("P1545", []):
                volume = q.get("datavalue", {}).get("value"); break
            series_entity = _wd_entity(series_qid)
            time.sleep(0.15)
            series_name = _get_label(series_entity, ("fr","en")) if series_entity else series_qid
            result = {"series_name": series_name, "volume": volume, "method": "wd_series"}
            CACHE[key] = result; cache_save(); return result

    result = {"series_name": None, "volume": None, "method": "wd_not_found"}
    CACHE[key] = result; cache_save(); return result

# ══════════════════════════════════════════════════════════════════════════════
#  PIPELINE COMPLET
# ══════════════════════════════════════════════════════════════════════════════
def detect_v2(title: str, saga_ol: str = "", use_wikidata: bool = False) -> dict:
    """
    Pipeline complet V2.
    Returns: {is_series, series_name, volume, method}
    """
    # 1. Base statique
    static = check_static_v2(title, saga_ol)
    if static:
        return {"is_series": True, **static}

    # 2. Wikidata (optionnel, lent)
    if use_wikidata:
        wd = check_wikidata_v2(title)
        if wd["series_name"]:
            return {"is_series": True, "series_name": wd["series_name"],
                    "volume": wd["volume"], "method": wd["method"]}
        return {"is_series": False, "series_name": None, "volume": None, "method": wd["method"]}

    return {"is_series": False, "series_name": None, "volume": None, "method": "standalone"}
