# Configuration centralisee pour BOOKTIME Backend
import os
from pathlib import Path
from dotenv import load_dotenv

# Charger .env depuis le dossier backend (parent de app/)
_backend_dir = Path(__file__).resolve().parent.parent
_env_path = _backend_dir / ".env"
_env_local_path = _backend_dir / ".env.local"
load_dotenv(_env_path)
if _env_local_path.is_file():
    load_dotenv(_env_local_path, override=True)
load_dotenv()  # fallback cwd

# Configuration MongoDB
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/booktime")

# Configuration JWT
import secrets as _secrets
_default_secret = _secrets.token_hex(32)  # généré aléatoirement si non défini
SECRET_KEY = os.getenv("SECRET_KEY") or _default_secret
if not os.getenv("SECRET_KEY"):
    import logging as _logging
    _logging.getLogger("booktime").warning(
        "SECRET_KEY non définie dans .env — clé temporaire générée. "
        "Définissez SECRET_KEY pour la production !"
    )
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Configuration API
API_TITLE = "BookTime API"
API_DESCRIPTION = "Votre bibliothèque personnelle"
API_VERSION = "1.0.0"

# Configuration CORS
CORS_ORIGINS = ["*"]
CORS_CREDENTIALS = True
CORS_METHODS = ["*"]
CORS_HEADERS = ["*"]

# Configuration des bases de données
DATABASE_NAME = "booktime"
COLLECTIONS = {
    "users": "users",
    "books": "books",
    "authors": "authors",
    "series_library": "series_library"
}

# Configuration Open Library
OPEN_LIBRARY_BASE_URL = "https://openlibrary.org"
OPEN_LIBRARY_SEARCH_URL = f"{OPEN_LIBRARY_BASE_URL}/search.json"
OPEN_LIBRARY_COVERS_URL = "https://covers.openlibrary.org/b"

# Google Books API (3e source métadonnées — clé dans .env)
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY", "").strip()

# Configuration de pagination
DEFAULT_LIMIT = 10
MAX_LIMIT = 100
DEFAULT_OFFSET = 0

# Export statique Wikidata (généré à la racine BOOKTIME-main par extract_wikidata_series / post_extract)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WIKIDATA_SERIES_DB_PATH = Path(os.getenv("WIKIDATA_SERIES_DB_PATH", str(_REPO_ROOT / "wikidata_series_db.json")))
WIKIDATA_STANDALONE_CACHE_PATH = Path(
    os.getenv("WIKIDATA_STANDALONE_CACHE_PATH", str(_REPO_ROOT / "popular_standalone_books.json"))
)

# Configuration des catégories
VALID_CATEGORIES = ["roman", "bd", "manga"]
VALID_STATUSES = ["to_read", "reading", "completed"]

# Configuration des langues
SUPPORTED_LANGUAGES = ["fr", "en", "es", "de", "it", "pt", "ru", "ja", "zh", "ko"]
DEFAULT_LANGUAGE = "fr"