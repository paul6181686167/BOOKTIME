#!/usr/bin/env python3
"""
SEED CATALOG - BOOKTIME  (version massive)
Cible : 20 000 - 50 000 livres depuis Open Library

Strategie :
  1. Subjects API  (jusqu'a 1000 livres / sujet)
  2. Search API    (100 / requete, paginee)
  3. 200+ auteurs populaires

Usage :
    cd backend
    python scripts/seed_catalog.py --json-only          # recommande en local
    python scripts/seed_catalog.py --json-only --resume # continue sans ecraser
    python scripts/seed_catalog.py --json-only --limit 20  # test rapide
"""

import sys, os, time, json, argparse, requests, re
from pathlib import Path
from datetime import datetime
from collections import Counter

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

try:
    from pymongo import MongoClient, UpdateOne
    from pymongo.errors import BulkWriteError
    PYMONGO_OK = True
except ImportError:
    PYMONGO_OK = False

MONGO_URL    = os.environ.get("MONGO_URL", "mongodb://localhost:27017/booktime")
OL_SEARCH    = "https://openlibrary.org/search.json"
OL_SUBJECTS  = "https://openlibrary.org/subjects/{subject}.json"
COVERS_URL   = "https://covers.openlibrary.org/b/id/{cid}-M.jpg"
JSON_OUTPUT  = Path(__file__).parent.parent / "data" / "catalog_cache.json"

DELAY_S      = 0.4   # secondes entre requetes
SEARCH_LIMIT = 100   # max par requete search
SUBJ_LIMIT   = 1000  # max par requete subjects

# ─────────────────────────────────────────────────────────────────────────────
# 1. SUBJECTS API  (le plus efficace : 1000 livres / appel)
# ─────────────────────────────────────────────────────────────────────────────

SUBJECTS = [
    # ── Fiction générale ─────────────────────────────────────────────────────
    "fiction", "literary_fiction", "short_stories", "anthologies",
    "romance_novels", "love_stories", "epistolary_fiction",
    "historical_fiction", "war_stories", "political_fiction",
    "dystopian_fiction", "utopian_fiction", "philosophical_fiction",
    "psychological_fiction", "social_fiction", "satirical_fiction",
    "picaresque_literature", "absurdist_fiction", "black_humor",
    "magical_realism", "surrealist_fiction", "experimental_fiction",
    "metafiction", "stream_of_consciousness", "noir_fiction",
    "gothic_fiction", "southern_gothic", "cozy_mysteries",
    "hardboiled_fiction", "police_procedural",

    # ── Genres populaires ────────────────────────────────────────────────────
    "mystery_fiction", "detective_fiction", "crime_fiction",
    "thriller", "spy_stories", "legal_thrillers", "medical_thrillers",
    "psychological_thriller", "financial_thrillers", "techno_thrillers",
    "horror_fiction", "ghost_stories", "occult_fiction",
    "supernatural_fiction", "paranormal_fiction", "dark_fiction",
    "science_fiction", "space_opera", "cyberpunk", "steampunk",
    "time_travel", "alternate_history", "post_apocalyptic_fiction",
    "hard_science_fiction", "soft_science_fiction", "biopunk",
    "solarpunk", "climate_fiction", "first_contact_fiction",
    "generation_ship", "space_colonization", "transhumanism_fiction",
    "fantasy_fiction", "epic_fantasy", "dark_fantasy", "urban_fantasy",
    "high_fantasy", "low_fantasy", "grimdark_fiction",
    "portal_fantasy", "sword_and_sorcery", "heroic_fantasy",
    "fairy_tales", "folklore", "mythology", "fables",
    "legends", "arthurian_romances", "norse_mythology_fiction",
    "adventure_fiction", "action_fiction", "survival_fiction",
    "western_fiction", "nautical_fiction", "war_fiction",
    "military_fiction", "sea_stories", "jungle_fiction",
    "heist_fiction", "caper_fiction",

    # ── Romance sous-genres ──────────────────────────────────────────────────
    "romance_fiction", "romantic_suspense", "paranormal_romance",
    "contemporary_romance", "erotic_fiction", "new_adult_fiction",
    "regency_romance", "historical_romance", "western_romance",
    "military_romance", "billionaire_romance",

    # ── Littérature jeunesse / YA ────────────────────────────────────────────
    "young_adult_fiction", "childrens_literature",
    "juvenile_fiction", "coming_of_age_stories",
    "school_stories", "bildungsroman", "middle_grade_fiction",
    "picture_books", "childrens_poetry", "fairy_stories",
    "boys_stories", "girls_stories", "adventure_stories_for_children",

    # ── Non-fiction ──────────────────────────────────────────────────────────
    "biography", "autobiography", "memoirs", "diaries",
    "history", "world_history", "french_history", "american_history",
    "ancient_history", "medieval_history", "modern_history",
    "military_history", "social_history", "economic_history",
    "political_history", "cultural_history", "art_history",
    "philosophy", "ethics", "logic", "epistemology",
    "existentialism", "stoicism", "buddhist_philosophy",
    "political_science", "political_philosophy", "democracy",
    "psychology", "self_help", "personal_development",
    "cognitive_science", "social_psychology", "behavioral_economics",
    "business", "economics", "entrepreneurship", "finance",
    "management", "leadership", "marketing", "investing",
    "science", "popular_science", "natural_history", "physics",
    "chemistry", "biology", "astronomy", "mathematics",
    "computer_science", "technology", "artificial_intelligence",
    "medicine", "health", "nutrition", "neuroscience",
    "travel_writing", "essays", "literary_criticism",
    "journalism", "true_crime", "investigative_journalism",
    "nature_writing", "ecology", "environment",
    "education", "pedagogy", "linguistics", "language_learning",
    "religion", "spirituality", "theology", "mysticism",
    "mythology_and_folklore", "occultism", "new_age",
    "art", "painting", "sculpture", "photography_art",
    "music", "film", "theater", "dance",
    "architecture", "design", "fashion",
    "sports", "football", "basketball", "tennis",
    "cooking_recipes", "baking", "gastronomy", "wine",
    "gardening", "home_improvement", "crafts",
    "parenting", "family", "relationships",

    # ── BD / Comics / Manga ──────────────────────────────────────────────────
    "comic_books_strips", "graphic_novels", "bande_dessinee",
    "manga", "superheroes", "american_comics",
    "underground_comics", "alternative_comics", "webcomics",
    "manga_for_children", "manga_for_adults",
    "superhero_comics", "horror_comics", "romance_comics",
    "science_fiction_comics",

    # ── Littérature par langue / pays ────────────────────────────────────────
    "french_fiction", "french_literature", "francophone_literature",
    "english_fiction", "american_fiction", "british_fiction",
    "japanese_fiction", "german_fiction", "spanish_fiction",
    "italian_fiction", "russian_literature", "latin_american_fiction",
    "african_fiction", "canadian_fiction", "australian_fiction",
    "irish_fiction", "scottish_fiction", "swedish_fiction",
    "norwegian_fiction", "danish_fiction", "dutch_fiction",
    "polish_fiction", "czech_fiction", "hungarian_fiction",
    "greek_fiction", "portuguese_fiction", "brazilian_fiction",
    "mexican_fiction", "argentinian_fiction", "colombian_fiction",
    "chinese_fiction", "korean_fiction", "indian_fiction",
    "arabic_fiction", "israeli_fiction", "turkish_fiction",
    "iranian_fiction", "south_african_fiction",
    "nigerian_fiction", "kenyan_fiction", "egyptian_fiction",
    "new_zealand_fiction", "caribbean_fiction",

    # ── Périodes historiques ─────────────────────────────────────────────────
    "ancient_fiction", "medieval_fiction", "renaissance_fiction",
    "18th_century_fiction", "19th_century_fiction",
    "victorian_fiction", "edwardian_fiction",
    "world_war_1_fiction", "world_war_2_fiction",
    "cold_war_fiction", "20th_century_fiction",
    "21st_century_fiction",

    # ── Thèmes spécifiques ───────────────────────────────────────────────────
    "vampires", "werewolves", "witches", "dragons", "zombies",
    "robots", "artificial_intelligence_fiction", "androids",
    "aliens", "extraterrestrial_life", "ufos",
    "serial_killers", "serial_murderers",
    "addiction_fiction", "drug_fiction", "alcoholism_fiction",
    "mental_illness_fiction", "depression_fiction",
    "lgbtq_fiction", "gay_fiction", "lesbian_fiction",
    "feminist_fiction", "womens_fiction", "chick_lit",
    "race_fiction", "immigration_fiction", "diaspora_fiction",
    "prison_fiction", "war_crimes", "genocide_fiction",
    "dystopia", "utopia", "totalitarianism",
    "religion_fiction", "spiritual_fiction", "christian_fiction",
    "amish_romance", "inspirational_fiction",
    "medical_fiction", "hospital_fiction", "doctor_fiction",
    "legal_fiction", "courtroom_drama", "lawyer_fiction",
    "academic_fiction", "campus_fiction",
    "food_fiction", "culinary_fiction", "chef_fiction",
    "sports_fiction", "baseball_fiction", "soccer_fiction",
    "music_fiction", "rock_music_fiction", "jazz_fiction",
    "art_fiction", "artist_fiction", "painter_fiction",
    "mystery_and_detective_stories", "cozy_mystery",
    "amateur_detective", "private_investigator_fiction",
    "heists", "capers", "espionage",
    "haunted_houses", "ghosts_fiction",
    "time_loop", "parallel_worlds", "multiverse",
    "lost_worlds", "hollow_earth_fiction",
    "treasure_hunts", "buried_treasure_fiction",
    "shipwrecks", "desert_island_fiction",
    "end_of_the_world", "apocalyptic_fiction",
    "pandemic_fiction", "plague_fiction",
    "nature_fiction", "wilderness_fiction",
    "horses_fiction", "dog_fiction", "cat_fiction",
    "fairy_godmother", "gnomes", "elves", "dwarves",
    "pirates", "privateers", "buccaneers",
    "knights", "chivalry", "tournaments",
    "samurai", "ninja", "japanese_historical_fiction",
    "viking_fiction", "celtic_fiction",
    "native_american_fiction", "aboriginal_fiction",

    # ── Formats ──────────────────────────────────────────────────────────────
    "novellas", "novelettes", "flash_fiction",
    "epistolary_novels", "diary_novels", "frame_stories",
    "unreliable_narrators", "multiple_perspectives",

    # ── Classiques ───────────────────────────────────────────────────────────
    "classics", "world_classics", "western_canon",
    "penguin_classics", "oxford_world_classics",
    "19th_century_american_literature", "19th_century_english_literature",
    "modernist_literature", "postmodern_literature",
    "beat_generation", "lost_generation",
    "harlem_renaissance", "southern_literature",

    # ── Prix et listes ───────────────────────────────────────────────────────
    "booker_prize", "pulitzer_prize", "national_book_award",
    "hugo_award", "nebula_award", "world_fantasy_award",
    "edgar_award", "man_booker_prize", "nobel_prize_literature",
    "bestsellers", "new_york_times_bestseller",

    # ── Jeunesse détaillée ───────────────────────────────────────────────────
    "picture_books_for_children", "early_readers",
    "chapter_books", "middle_grade", "teen_fiction",
    "young_adult_romance", "young_adult_fantasy",
    "young_adult_science_fiction", "young_adult_horror",
    "young_adult_mystery",

    # ── Sciences humaines ────────────────────────────────────────────────────
    "sociology", "anthropology", "archeology",
    "gender_studies", "cultural_studies", "media_studies",
    "communication", "rhetoric", "semiotics",
    "geography", "urban_studies", "environmental_studies",
    "law", "jurisprudence", "constitutional_law",
    "international_relations", "diplomacy", "geopolitics",

    # ── Pratique ────────────────────────────────────────────────────────────
    "how_to_books", "reference_books", "encyclopedias",
    "dictionaries", "almanacs", "atlases",
    "textbooks", "study_guides", "workbooks",
    "cookbooks", "recipe_books", "health_cookbooks",
    "travel_guides", "guidebooks", "phrasebooks",
    "art_instruction", "drawing_books", "painting_books",
    "photography", "film_making", "music_instruction",
    "programming_books", "web_development", "data_science",
    "fitness", "yoga", "meditation", "mindfulness",
]

# ─────────────────────────────────────────────────────────────────────────────
# 2. SEARCH API paginee (auteurs + themes)
# ─────────────────────────────────────────────────────────────────────────────

# Format : (label, params_sans_offset_limit)
SEARCH_QUERIES = []

# Auteurs massifs (plusieurs pages)
AUTHORS_BIG = [
    # ── Francophone ──────────────────────────────────────────────────────────
    "Maxime Chattam", "Marc Levy", "Guillaume Musso", "Harlan Coben",
    "Michel Bussi", "Fred Vargas", "Pierre Lemaitre", "Amelie Nothomb",
    "Bernard Werber", "Virginie Grimaldi", "Joel Dicker", "Franck Thilliez",
    "Karine Giebel", "Cyril Massarotto", "Anna Gavalda",
    "Katherine Pancol", "Isabelle Autissier", "Tatiana de Rosnay",
    "Romain Gary", "Patrick Modiano", "Michel Houellebecq",
    "Marguerite Yourcenar", "Simone de Beauvoir", "Albert Camus",
    "Jean-Paul Sartre", "Marcel Proust", "Victor Hugo", "Emile Zola",
    "Gustave Flaubert", "Stendhal", "Honore de Balzac", "Alexandre Dumas",
    "Jules Verne", "Guy de Maupassant", "Anatole France",
    "Voltaire", "Moliere", "Jean Racine", "Pierre Corneille",
    "Henri Troyat", "Jean d Ormesson", "Erik Orsenna",
    "Michel Tournier", "Le Clezio", "Patrick Grainville",
    "Sylvain Tesson", "Alexandre Jardin", "Gilles Legardinier",
    "Pierre Milon", "Jean-Christophe Grange", "Sylvie Granotier",
    "Dominique Manotti", "Jean-Luc Bizien",
    "Rene Goscinny", "Frederic Dard", "San-Antonio",
    "Jean-Bernard Pouy", "Didier Daeninckx", "Daniel Pennac",
    "Tonino Benacquista", "Jean-Claude Izzo", "Philippe Claudel",
    "Eric-Emmanuel Schmitt", "Marc-Edouard Nabe", "Jean Echenoz",
    "Patrick Chamoiseau", "Maryse Conde", "Edouard Glissant",
    "Ahmadou Kourouma", "Alain Mabanckou", "Abdourahman Waberi",
    "Yasmina Khadra", "Tahar Ben Jelloun", "Amin Maalouf",
    "Andrei Makine", "Milan Kundera", "Ismail Kadare",
    "Muriel Barbery", "Laurent Gaudé", "Mathias Enard",
    "Leila Slimani", "Kamel Daoud", "Karin Fossum",
    "Camille Pascal", "Pierre Ducrozet", "Yannick Haenel",
    "Emmanuel Carrere", "Tanguy Viel", "Lydie Salvayre",
    "Marie NDiaye", "Christine Angot", "Annie Ernaux",
    "Delphine de Vigan", "Virginie Despentes", "Lionel Shriver translated",
    "Henri Loevenbruck", "Michel Pagel", "Xavier-Marie Bonnot",
    "Herve Commere", "Caryl Ferey", "Pierre Pevel",
    "Jean-Luc Bizien", "Olivier Truc", "Sandrine Collette",
    "Sophie Chauveau", "Corinne Royer", "Isabelle Carré",

    # ── Thriller / policier anglo-saxon ──────────────────────────────────────
    "Stephen King", "Dean Koontz", "James Patterson",
    "John Grisham", "Tom Clancy", "Lee Child",
    "Vince Flynn", "Brad Thor", "Daniel Silva",
    "Ken Follett", "Jeffrey Archer", "Frederick Forsyth",
    "John le Carre", "Ian Fleming", "Alistair MacLean",
    "Wilbur Smith", "Clive Cussler", "Matthew Reilly",
    "Dan Brown", "Michael Crichton", "Robin Cook",
    "Patricia Cornwell", "Karin Slaughter", "Tess Gerritsen",
    "Lisa Gardner", "Jeffery Deaver", "Thomas Harris",
    "Stieg Larsson", "Jo Nesbo", "Henning Mankell",
    "Camilla Lackberg", "Jussi Adler-Olsen", "Anne Holt",
    "Agatha Christie", "Arthur Conan Doyle", "Ruth Rendell",
    "P.D. James", "Ian Rankin", "Peter James", "Simon Kernick",
    "Linwood Barclay", "Peter Robinson", "Stuart MacBride",
    "Val McDermid", "Reginald Hill", "Colin Dexter",
    "Robert Crais", "Michael Connelly", "James Ellroy",
    "Dennis Lehane", "George Pelecanos", "Laura Lippman",
    "Harlan Coben", "Lisa Scottoline", "Scott Turow",
    "David Baldacci", "Vince Flynn", "Mark Greaney",
    "Barry Eisler", "Mark Mills", "C.J. Box",
    "Nevada Barr", "Tony Hillerman", "Craig Johnson",
    "Steve Berry", "Douglas Preston", "Lincoln Child",
    "Preston Child", "James Rollins", "Kyle Mills",
    "Andrew Gross", "Ridley Pearson", "John Sandford",
    "Nevada Barr", "Nevada Barr",
    "Kate Atkinson", "Sophie Hannah", "Elly Griffiths",
    "Ann Cleeves", "M.C. Beaton", "Alexander McCall Smith",
    "Alan Bradley", "Louise Penny", "Donna Leon",
    "Andrea Camilleri", "Cara Black", "Martin Walker",

    # ── Romance / Feelgood ───────────────────────────────────────────────────
    "Nicholas Sparks", "Jojo Moyes", "Sophie Kinsella",
    "Cecelia Ahern", "Marian Keyes", "Rosamunde Pilcher",
    "Maeve Binchy", "Colleen Hoover", "Emily Henry",
    "Taylor Jenkins Reid", "Kristin Hannah",
    "Debbie Macomber", "Nora Roberts", "Linda Howard",
    "Danielle Steel", "LaVyrle Spencer", "Judith McNaught",
    "Lisa Kleypas", "Julia Quinn", "Eloisa James",
    "Loretta Chase", "Courtney Milan", "Talia Hibbert",
    "Kennedy Ryan", "Penelope Douglas", "Ana Huang",
    "Elena Armas", "Ali Hazelwood", "Helen Hoang",
    "Abby Jimenez", "Rachel Lynn Solomon", "Christina Lauren",
    "Penny Reid", "Lucy Score", "Meghan March",
    "J.T. Geissinger", "Tarryn Fisher", "Katee Robert",
    "Sarah MacLean", "Tessa Dare", "Evie Dunmore",
    "Meredith Duran", "Elizabeth Hoyt", "Grace Burrowes",

    # ── Fantasy / SF ─────────────────────────────────────────────────────────
    "J.K. Rowling", "George R.R. Martin", "Brandon Sanderson",
    "Patrick Rothfuss", "Robin Hobb", "Terry Pratchett",
    "Neil Gaiman", "Ursula K. Le Guin", "Lois McMaster Bujold",
    "Joe Abercrombie", "Scott Lynch", "Brent Weeks",
    "Brian McClellan", "Michael J. Sullivan", "Anthony Ryan",
    "Peter V. Brett", "Andrzej Sapkowski",
    "Tolkien", "C.S. Lewis", "Frank Herbert", "Isaac Asimov",
    "Arthur C. Clarke", "Philip K. Dick", "Ray Bradbury",
    "Robert Heinlein", "Orson Scott Card", "Vernor Vinge",
    "Kim Stanley Robinson", "Peter F. Hamilton",
    "Alastair Reynolds", "Iain M. Banks", "Charles Stross",
    "William Gibson", "Neal Stephenson", "Greg Bear",
    "David Brin", "Larry Niven", "Joe Haldeman",
    "Dan Simmons", "Greg Egan", "Ted Chiang",
    "N.K. Jemisin", "Octavia Butler", "Samuel R. Delany",
    "LeVar Burton", "Nnedi Okofor", "Tade Thompson",
    "Becky Chambers", "Ann Leckie", "Mary Robinette Kowal",
    "Naomi Novik", "Seanan McGuire", "T. Kingfisher",
    "Adrian Tchaikovsky", "Peter Watts", "Robert Charles Wilson",
    "Michael Moorcock", "Roger Zelazny", "Fritz Leiber",
    "Glen Cook", "Steven Erikson", "Ian Cameron Esslemont",
    "R. Scott Bakker", "Mark Lawrence", "Michael J. Fletcher",
    "Brian Staveley", "Django Wexler", "Sam Sykes",
    "Ari Marmell", "Kevin Hearne", "Jim Butcher",
    "Patricia Briggs", "Ilona Andrews", "Charlaine Harris",
    "Kim Harrison", "Simon R. Green", "Mike Carey",
    "Ben Aaronovitch", "Charles de Lint", "Emma Bull",
    "Terri Windling", "Ellen Datlow",
    "Michael Marshall Smith", "China Mieville",
    "Jeff VanderMeer", "Paul Tremblay", "Josh Malerman",
    "Grady Hendrix", "Stephen Graham Jones", "Victor LaValle",
    "Carmen Maria Machado", "Kelly Link",

    # ── YA ───────────────────────────────────────────────────────────────────
    "Suzanne Collins", "Veronica Roth", "Rick Riordan",
    "John Green", "Rainbow Rowell", "Sarah J. Maas",
    "Cassandra Clare", "Richelle Mead", "Stephenie Meyer",
    "Holly Black", "Leigh Bardugo", "Victoria Aveyard",
    "Marissa Meyer", "Amy Plum", "Laini Taylor",
    "Garth Nix", "Philip Pullman", "Tamora Pierce",
    "Rae Carson", "Maggie Stiefvater", "Ally Condie",
    "Lauren Oliver", "Kiera Cass", "Tahereh Mafi",
    "Marie Lu", "Pittacus Lore", "James Dashner",
    "Scott Westerfeld", "Carrie Ryan", "Kendare Blake",
    "Soman Chainani", "Roshani Chokshi", "Sabaa Tahir",
    "Tomi Adeyemi", "Angie Thomas", "Elizabeth Acevedo",
    "Jason Reynolds", "Nic Stone", "Adam Silvera",
    "Benjamin Alire Saenz", "Nicola Yoon",

    # ── Classiques monde ─────────────────────────────────────────────────────
    "Fyodor Dostoevsky", "Leo Tolstoy", "Anton Chekhov",
    "Ivan Turgenev", "Nikolai Gogol", "Ivan Goncharov",
    "Franz Kafka", "Thomas Mann", "Hermann Hesse",
    "Bertolt Brecht", "Heinrich Boll", "Gunter Grass",
    "Stefan Zweig", "Robert Musil", "Arthur Schnitzler",
    "Gabriel Garcia Marquez", "Jorge Luis Borges",
    "Mario Vargas Llosa", "Pablo Neruda", "Julio Cortazar",
    "Isabel Allende", "Laura Esquivel", "Carlos Fuentes",
    "Umberto Eco", "Italo Calvino", "Alberto Moravia",
    "Pier Paolo Pasolini", "Leonardo Sciascia",
    "Naguib Mahfouz", "Tayeb Salih", "Alaa Al Aswany",
    "Chinua Achebe", "Wole Soyinka", "Ngugi wa Thiong o",
    "Bessie Head", "Ben Okri", "Chimamanda Ngozi Adichie",
    "Haruki Murakami", "Yukio Mishima", "Kobo Abe",
    "Soseki Natsume", "Yasunari Kawabata", "Junichiro Tanizaki",
    "Mo Yan", "Yu Hua", "Su Tong", "Can Xue",
    "Kenzaburo Oe", "Banana Yoshimoto", "Ryu Murakami",
    "Jose Saramago", "Eca de Queiros", "Fernando Pessoa",
    "Javier Marias", "Eduardo Mendoza", "Arturo Perez-Reverte",
    "Orhan Pamuk", "Yashar Kemal",
    "Amos Oz", "David Grossman", "A.B. Yehoshua",
    "Nikos Kazantzakis", "Petros Markaris",

    # ── Manga auteurs ────────────────────────────────────────────────────────
    "Eiichiro Oda", "Masashi Kishimoto", "Tite Kubo",
    "Akira Toriyama", "Hirohiko Araki", "Kentaro Miura",
    "Hajime Isayama", "Koyoharu Gotouge", "Gege Akutami",
    "Kohei Horikoshi", "Yoshihiro Togashi", "Naoki Urasawa",
    "Rumiko Takahashi", "Go Nagai", "Osamu Tezuka",
    "Hiro Mashima", "Tsugumi Ohba", "Takeshi Obata",
    "Yuki Tabata", "Tatsuki Fujimoto", "Makoto Yukimura",
    "Kaiu Shirai", "Posuka Demizu", "Yusei Matsui",
    "Daisuke Ashihara", "Kenta Shinohara", "Noriyuki Konishi",
    "Hidekaz Himaruya", "Natsuki Takaya",

    # ── BD auteurs ───────────────────────────────────────────────────────────
    "Goscinny", "Uderzo", "Herge", "Franquin",
    "Morris", "Peyo", "Jean Van Hamme", "William Vance",
    "Jean Dufaux", "Enrico Marini", "Hermann",
    "Yves Sente", "Andre Juillard", "Jean-Claude Meziere",
    "Pierre Christin", "Moebius", "Philippe Druillet",
    "Bourgeon", "Juanjo Guarnido", "Juan Diaz Canales",
    "Frank Miller", "Alan Moore", "Neil Gaiman comics",
    "Grant Morrison", "Warren Ellis", "Garth Ennis",
    "Brian K. Vaughan", "Ed Brubaker", "Matt Fraction",

    # ── Auteurs prolifiques populaires ───────────────────────────────────────
    "Barbara Cartland", "Danielle Steel", "Nora Roberts",
    "Louis L Amour", "Zane Grey", "Max Brand",
    "Edgar Rice Burroughs", "H. Rider Haggard",
    "Alexandre Dumas fils", "Eugene Sue",
    "Charles Dickens", "William Thackeray", "Anthony Trollope",
    "George Eliot", "Thomas Hardy", "Henry James",
    "Edith Wharton", "Theodore Dreiser", "Sinclair Lewis",
    "John Steinbeck", "Ernest Hemingway", "William Faulkner",
    "F. Scott Fitzgerald", "Thomas Wolfe", "Erskine Caldwell",
    "Upton Sinclair", "Jack London", "Willa Cather",
    "Sherwood Anderson", "Thornton Wilder",
    "Norman Mailer", "Saul Bellow", "Philip Roth",
    "John Updike", "Don DeLillo", "Thomas Pynchon",
    "Cormac McCarthy", "Toni Morrison", "Alice Walker",
    "Maya Angelou", "James Baldwin", "Ralph Ellison",
    "Richard Wright", "Zora Neale Hurston",
    "Kurt Vonnegut", "Joseph Heller", "Ken Kesey",
    "Jack Kerouac", "Allen Ginsberg", "William S. Burroughs",
    "Tom Wolfe", "Hunter S. Thompson",
    "Joan Didion", "Truman Capote", "Gore Vidal",
    "John Irving", "Anne Tyler", "Barbara Kingsolver",
    "Jonathan Franzen", "Jeffrey Eugenides", "Donna Tartt",
    "Cynthia Ozick", "E.L. Doctorow", "John Cheever",
    "Raymond Carver", "Richard Ford", "Denis Johnson",
    "Paul Auster", "Jonathan Lethem", "Michael Chabon",
    "Zadie Smith", "Ian McEwan", "Martin Amis",
    "Julian Barnes", "A.S. Byatt", "Kazuo Ishiguro",
    "Salman Rushdie", "Timothy Mo", "Hanif Kureishi",
    "Nick Hornby", "Douglas Coupland", "Nick Hornby",
]

for author in AUTHORS_BIG:
    SEARCH_QUERIES.append((
        f"Auteur: {author}",
        {"author": author, "sort": "editions"},
        6   # 6 pages × 100 = 600 livres max par auteur
    ))

# Themes / mots-cles supplementaires (1-2 pages)
THEME_QUERIES = [
    ("Prix Nobel litterature", {"q": "prix nobel litterature", "sort": "editions"}),
    ("Booker Prize", {"q": "booker prize winner fiction", "sort": "editions"}),
    ("Prix Pulitzer fiction", {"q": "pulitzer prize fiction", "sort": "editions"}),
    ("Roman graphique adulte", {"q": "roman graphique adulte bande dessinee", "language": "fre"}),
    ("Manga shonen", {"q": "manga shonen jump", "subject": "manga"}),
    ("Manga shojo", {"q": "manga shojo romance"}),
    ("Manga seinen", {"q": "manga seinen adult"}),
    ("One Piece", {"q": "One Piece Oda manga tome"}),
    ("Naruto manga", {"q": "Naruto Kishimoto manga"}),
    ("Dragon Ball", {"q": "Dragon Ball Toriyama"}),
    ("Attack on Titan", {"q": "Attack Titan Hajime Isayama"}),
    ("Demon Slayer", {"q": "Demon Slayer Kimetsu no Yaiba"}),
    ("Jujutsu Kaisen", {"q": "Jujutsu Kaisen Gege"}),
    ("My Hero Academia", {"q": "My Hero Academia Boku"}),
    ("Hunter x Hunter", {"q": "Hunter Hunter Yoshihiro"}),
    ("Fullmetal Alchemist", {"q": "Fullmetal Alchemist Arakawa"}),
    ("Bleach manga", {"q": "Bleach Kubo manga"}),
    ("Fairy Tail manga", {"q": "Fairy Tail Hiro Mashima"}),
    ("Tokyo Ghoul", {"q": "Tokyo Ghoul Ishida"}),
    ("Chainsaw Man", {"q": "Chainsaw Man Tatsuki Fujimoto"}),
    ("Vinland Saga", {"q": "Vinland Saga Makoto Yukimura"}),
    ("Astérix BD", {"q": "Asterix Goscinny Uderzo"}),
    ("Tintin BD", {"q": "Tintin Herge bande dessinee"}),
    ("Lucky Luke", {"q": "Lucky Luke Morris bande dessinee"}),
    ("XIII BD", {"q": "XIII Van Hamme bande dessinee"}),
    ("Largo Winch BD", {"q": "Largo Winch bande dessinee"}),
    ("Spirou BD", {"q": "Spirou Fantasio bande dessinee"}),
    ("Thorgal BD", {"q": "Thorgal bande dessinee"}),
    ("Les Legendaires", {"q": "Legendaires bande dessinee"}),
    ("Blacksad", {"q": "Blacksad Juan Diaz Canales"}),
    ("BD Lanfeust", {"q": "Lanfeust Troy bande dessinee"}),
    ("Schtroumpfs", {"q": "Schtroumpfs Peyo bande dessinee"}),
    ("Blake Mortimer", {"q": "Blake Mortimer Edgar Jacobs"}),
    ("Harry Potter", {"q": "Harry Potter Rowling"}),
    ("Hunger Games", {"q": "Hunger Games Suzanne Collins"}),
    ("Divergent", {"q": "Divergent Veronica Roth"}),
    ("Percy Jackson", {"q": "Percy Jackson Rick Riordan"}),
    ("Dune Herbert", {"q": "Dune Frank Herbert science fiction"}),
    ("Seigneur Anneaux", {"q": "Lord Rings Tolkien"}),
    ("Game of Thrones", {"q": "Song Ice Fire George Martin"}),
    ("Witcher", {"q": "Witcher Sapkowski roman"}),
    ("Mistborn", {"q": "Mistborn Brandon Sanderson"}),
    ("Roue du Temps", {"q": "Wheel Time Robert Jordan"}),
    ("Foundation Asimov", {"q": "Foundation Isaac Asimov"}),
    ("Outlander", {"q": "Outlander Diana Gabaldon"}),
    ("A la croisee des mondes", {"q": "His Dark Materials Philip Pullman"}),
    ("SAS Gerard de Villiers", {"q": "SAS Gerard de Villiers roman"}),
    ("Millenium Larsson", {"q": "Millenium Stieg Larsson"}),
    ("Maupassant contes", {"q": "Maupassant contes nouvelles"}),
    ("Zola Rougon-Macquart", {"q": "Zola Rougon Macquart"}),
    ("Balzac comedie humaine", {"q": "Balzac Comedie Humaine"}),
    ("Dumas musketeers", {"q": "Dumas trois mousquetaires"}),
    ("Jules Verne voyages", {"q": "Jules Verne voyages extraordinaires"}),
    ("Hugo miserables", {"q": "Victor Hugo miserables roman"}),
    ("Flaubert", {"q": "Gustave Flaubert roman"}),
    ("Stendhal rouge noir", {"q": "Stendhal rouge noir roman"}),
    ("Proust recherche", {"q": "Proust recherche temps perdu"}),
    ("Camus roman", {"q": "Albert Camus roman etranger"}),
    ("Sartre roman", {"q": "Jean-Paul Sartre roman nausee"}),
    ("Simone de Beauvoir", {"q": "Simone de Beauvoir roman"}),
    ("San Antonio Dard", {"q": "San Antonio Frederic Dard"}),
    ("Romans lesbos", {"q": "roman historique moyen age"}),
    ("Policier nordique", {"q": "nordic noir crime fiction"}),
    ("Roman epistolaire", {"q": "roman epistolaire lettres"}),
    ("Autobiographie francaise", {"q": "autobiographie memoires france"}),
    ("Essai philosophique", {"q": "essai philosophie contemporain"}),
    ("Science popularisation", {"q": "science vulgarisation populaire"}),
    ("Biographie artiste", {"q": "biographie artiste peintre musicien"}),
    ("Roman africain", {"q": "roman africain litterature"}),
    ("Litterature japonaise", {"q": "litterature japonaise roman traduit"}),
    ("Roman americain contemporain", {"q": "american contemporary fiction bestseller"}),
    ("British fiction classics", {"q": "british classic fiction 19th century"}),
    ("Roman dystopique", {"q": "dystopia dystopian novel"}),
    ("Space opera", {"q": "space opera science fiction"}),
    ("Thriller medical", {"q": "medical thriller hospital doctor"}),
    ("Thriller juridique", {"q": "legal thriller lawyer courtroom"}),
    ("Roman espionnage", {"q": "spy thriller espionage"}),
    ("Western roman", {"q": "western cowboy frontier fiction"}),
    ("Roman historique medieval", {"q": "historical fiction medieval knight"}),
    ("Roman historique Egypt", {"q": "historical fiction ancient egypt rome"}),
    ("Roman policier anglais", {"q": "british detective mystery cozy"}),
    ("Regency romance", {"q": "regency romance historical"}),
    ("Dark romance", {"q": "dark romance contemporary adult"}),
    ("Romantasy", {"q": "romantasy fantasy romance fae"}),
    ("BookTok", {"q": "booktok popular romance contemporary fiction"}),
    ("Prix des Libraires", {"q": "prix des libraires roman"}),
    ("Prix Femina", {"q": "prix femina roman"}),
    ("Prix Medicis", {"q": "prix medicis roman"}),
    ("Litterature quebecoise", {"q": "litterature quebecoise roman"}),
    ("Litterature belge", {"q": "litterature belge roman"}),
    ("Roman suisse", {"q": "litterature suisse roman"}),
    ("Roman maghrebin", {"q": "roman maghrebin algerien marocain"}),
]

for label, params in THEME_QUERIES:
    SEARCH_QUERIES.append((label, params, 2))

# ─────────────────────────────────────────────────────────────────────────────
# Categorie detection
# ─────────────────────────────────────────────────────────────────────────────

MANGA_KW = {"manga","japanese comic","manhwa","manhua","anime","shonen","shojo","seinen","josei"}
BD_KW    = {"comic book","comic strip","bande dessinee","bande dessinee","fumetti",
             "bandes dessinees","graphic novel","comics","bd","franco-belge"}

def detect_category(subjects, title=""):
    txt = " ".join(subjects).lower() + " " + title.lower()
    if any(k in txt for k in MANGA_KW): return "manga"
    if any(k in txt for k in BD_KW):   return "bd"
    return "roman"

# ─────────────────────────────────────────────────────────────────────────────
# Fetchers
# ─────────────────────────────────────────────────────────────────────────────

FIELDS = ("key,title,author_name,cover_i,subject,first_publish_year,"
          "edition_count,isbn,want_to_read_count,already_read_count,"
          "currently_reading_count,language")

def fetch_search(params, offset=0):
    p = {"fields": FIELDS, "offset": offset, **params}
    try:
        r = requests.get(OL_SEARCH, params=p, timeout=15)
        r.raise_for_status()
        return r.json().get("docs", [])
    except Exception as e:
        print(f"  [WARN] search error: {e!s:.80}")
        return []

def fetch_subject(subject):
    url = OL_SUBJECTS.format(subject=subject)
    try:
        r = requests.get(url, params={"limit": SUBJ_LIMIT}, timeout=20)
        r.raise_for_status()
        return r.json().get("works", [])
    except Exception as e:
        print(f"  [WARN] subject error ({subject}): {e!s:.80}")
        return []

def process_search_doc(doc):
    title = doc.get("title","").strip()
    if not title or len(title) < 2: return None
    ol_key = doc.get("key","")
    if not ol_key: return None
    authors = doc.get("author_name") or []
    cover_i = doc.get("cover_i")
    subjects = doc.get("subject") or []
    isbn_list = doc.get("isbn") or []
    return {
        "ol_key": ol_key,
        "title": title,
        "author": authors[0] if authors else "Auteur inconnu",
        "authors": authors[:3],
        "category": detect_category(subjects, title),
        "cover_url": COVERS_URL.format(cid=cover_i) if cover_i else "",
        "subjects": subjects[:8],
        "first_publish_year": doc.get("first_publish_year"),
        "isbn": isbn_list[0] if isbn_list else "",
        "edition_count": doc.get("edition_count", 0),
        "popularity_score": (
            (doc.get("want_to_read_count") or 0)
            + (doc.get("already_read_count") or 0) * 2
            + (doc.get("currently_reading_count") or 0)
        ),
        "language": ((doc.get("language") or ["und"])[0]),
        "indexed_at": datetime.now().isoformat(),
    }

def process_subject_doc(work):
    title = (work.get("title") or "").strip()
    if not title or len(title) < 2: return None
    ol_key = work.get("key","")
    if not ol_key: return None
    authors = [a.get("name","") for a in (work.get("authors") or []) if a.get("name")]
    cover_id = work.get("cover_id") or (work.get("covers") or [None])[0]
    subjects = work.get("subjects") or []
    return {
        "ol_key": ol_key,
        "title": title,
        "author": authors[0] if authors else "Auteur inconnu",
        "authors": authors[:3],
        "category": detect_category(subjects, title),
        "cover_url": COVERS_URL.format(cid=cover_id) if cover_id else "",
        "subjects": subjects[:8],
        "first_publish_year": None,
        "isbn": "",
        "edition_count": 0,
        "popularity_score": 0,
        "language": "und",
        "indexed_at": datetime.now().isoformat(),
    }

# ─────────────────────────────────────────────────────────────────────────────
# MongoDB helpers
# ─────────────────────────────────────────────────────────────────────────────

def try_connect_mongo(url):
    if not PYMONGO_OK: return None
    try:
        import ssl, certifi
        configs = [
            {},
            {"tlsAllowInvalidCertificates": True},
            {"tls": True, "tlsCAFile": certifi.where()},
            {"tls": True, "tlsAllowInvalidCertificates": True},
        ]
        urls = [url]
        if "mongodb+srv://" in url:
            sep = "&" if "?" in url else "?"
            urls.append(f"{url}{sep}tlsAllowInvalidCertificates=true")
        for u in urls:
            for opts in configs:
                try:
                    c = MongoClient(u, serverSelectionTimeoutMS=8000, connectTimeoutMS=8000, **opts)
                    c.admin.command("ping")
                    return c
                except Exception:
                    pass
    except Exception:
        pass
    return None

# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-only", action="store_true")
    parser.add_argument("--resume",    action="store_true", help="Ne pas ecraser, ajouter au cache existant")
    parser.add_argument("--limit",     type=int, default=0, help="Nb max de blocs (0=tout)")
    parser.add_argument("--dry-run",   action="store_true")
    parser.add_argument("--no-subjects", action="store_true", help="Sauter les subjects API")
    parser.add_argument("--no-search",   action="store_true", help="Sauter les search queries")
    args = parser.parse_args()

    print("=== BOOKTIME Seed Catalog (MASSIVE) ===")
    print()

    # ── Connexion ────────────────────────────────────────────────────────────
    mongo_client = None
    catalog      = None
    use_json     = args.json_only or args.dry_run

    if not use_json:
        print("[INFO] Connexion MongoDB...")
        mongo_client = try_connect_mongo(MONGO_URL)
        if mongo_client:
            print("[OK] MongoDB connecte")
            db      = mongo_client.booktime
            catalog = db.books_catalog
            catalog.create_index("ol_key", unique=True)
            catalog.create_index("category")
            catalog.create_index("popularity_score")
            catalog.create_index([("title","text"),("author","text")])
            existing = set(catalog.distinct("ol_key"))
            print(f"[INFO] {len(existing)} livres deja en base")
        else:
            print("[WARN] MongoDB inaccessible, fallback JSON")
            use_json = True

    # ── Cache JSON ───────────────────────────────────────────────────────────
    all_books = []
    existing  = set()
    if use_json:
        if args.resume and JSON_OUTPUT.exists():
            try:
                with open(JSON_OUTPUT, "r", encoding="utf-8") as f:
                    all_books = json.load(f)
                existing = {b["ol_key"] for b in all_books}
                print(f"[INFO] Resume : {len(all_books)} livres deja dans le cache")
            except Exception:
                pass
        print(f"[INFO] Mode JSON : {JSON_OUTPUT}")
    print()

    total_added = 0

    def save_progress():
        if use_json and not args.dry_run:
            JSON_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            with open(JSON_OUTPUT, "w", encoding="utf-8") as f:
                json.dump(all_books, f, ensure_ascii=False, indent=2)

    def flush_batch(processed):
        nonlocal total_added
        if not processed: return 0
        new_books = [b for b in processed if b["ol_key"] not in existing]
        if not new_books: return 0
        for b in new_books:
            existing.add(b["ol_key"])
        if args.dry_run:
            total_added += len(new_books)
            return len(new_books)
        if catalog is not None:
            ops = [UpdateOne({"ol_key": b["ol_key"]}, {"$setOnInsert": b}, upsert=True) for b in new_books]
            try:
                res = catalog.bulk_write(ops, ordered=False)
                added = res.upserted_count
            except Exception:
                added = len(new_books)
        else:
            all_books.extend(new_books)
            added = len(new_books)
        total_added += added
        return added

    # ── Phase 1 : Subjects API ────────────────────────────────────────────────
    if not args.no_subjects:
        subjects = SUBJECTS if not args.limit else SUBJECTS[:args.limit]
        print(f"[PHASE 1] Subjects API ({len(subjects)} sujets, {SUBJ_LIMIT} livres max/sujet)")
        for i, subject in enumerate(subjects, 1):
            works = fetch_subject(subject)
            processed = [r for r in (process_subject_doc(w) for w in works) if r]
            added = flush_batch(processed)
            print(f"  [{i:03d}/{len(subjects):03d}] {subject}: {added} nouveaux ({len(works)} recus, total={len(all_books) if use_json else total_added})")
            if i % 10 == 0:
                save_progress()
                print(f"  [SAVE] Sauvegarde intermediaire ({total_added} ajoutes au total)")
            time.sleep(DELAY_S)
        save_progress()
        print(f"\n[PHASE 1] Terminee : {total_added} livres ajoutes\n")

    # ── Phase 2 : Search queries ──────────────────────────────────────────────
    if not args.no_search:
        queries = SEARCH_QUERIES if not args.limit else SEARCH_QUERIES[:args.limit]
        print(f"[PHASE 2] Search queries ({len(queries)} requetes)")
        for i, (label, params, pages) in enumerate(queries, 1):
            q_added = 0
            for page in range(pages):
                docs = fetch_search(params, offset=page * SEARCH_LIMIT)
                processed = [r for r in (process_search_doc(d) for d in docs) if r]
                q_added += flush_batch(processed)
                time.sleep(DELAY_S)
                if not docs or len(docs) < SEARCH_LIMIT:
                    break
            print(f"  [{i:04d}/{len(queries):04d}] {label}: {q_added} nouveaux (total={len(all_books) if use_json else total_added})")
            if i % 20 == 0:
                save_progress()
                print(f"  [SAVE] Sauvegarde ({total_added} ajoutes au total)")
        save_progress()
        print(f"\n[PHASE 2] Terminee : {total_added} livres ajoutes au total\n")

    # ── Bilan ─────────────────────────────────────────────────────────────────
    print("=" * 60)
    print(f"[OK] TERMINE  -  {total_added} nouveaux livres ajoutes")
    if use_json and not args.dry_run:
        cats = Counter(b.get("category","roman") for b in all_books)
        print(f"[OK] Total JSON : {len(all_books)} livres")
        for cat, n in cats.most_common():
            print(f"     {cat.upper():<8}: {n:>6}")
    elif catalog:
        total = catalog.count_documents({})
        print(f"[OK] Total MongoDB : {total}")
    print()
    print("[OK] Redemarrez le backend pour charger le nouveau catalogue !")

if __name__ == "__main__":
    main()
