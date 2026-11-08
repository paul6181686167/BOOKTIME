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

# Environnement d'exécution
ENVIRONMENT = os.getenv("ENVIRONMENT", "").strip().lower()


def is_production() -> bool:
    """Vrai en production : ENVIRONMENT=production, ou plateforme Render (variable RENDER)."""
    env = os.getenv("ENVIRONMENT", "").strip().lower()
    return env == "production" or (env == "" and bool(os.getenv("RENDER")))


def is_development() -> bool:
    """Vrai seulement si l'environnement est explicitement un environnement de développement/test."""
    return os.getenv("ENVIRONMENT", "").strip().lower() in {"development", "dev", "local", "test", "testing"}


# Configuration JWT
# Source unique de la clé de signature (security/jwt.py, dependencies.py, utils/security.py
# l'importent d'ici). Sans SECRET_KEY : refus de démarrer en production, clé temporaire sinon.
import secrets as _secrets

_PLACEHOLDER_KEYS = {"", "your-secret-key-here-change-in-production", "changeme", "secret"}
_configured_secret = (os.getenv("SECRET_KEY") or "").strip()
if _configured_secret.lower() in _PLACEHOLDER_KEYS:
    if is_production():
        raise RuntimeError(
            "SECRET_KEY manquante (ou valeur par défaut) : refus de démarrer en production. "
            "Définis une clé secrète longue et aléatoire dans les variables d'environnement."
        )
    import logging as _logging

    _logging.getLogger("booktime").warning(
        "SECRET_KEY non définie : clé temporaire générée (les sessions sautent à chaque "
        "redémarrage). Définis SECRET_KEY, obligatoire en production."
    )
    SECRET_KEY = _secrets.token_hex(32)
else:
    SECRET_KEY = _configured_secret
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "86400"))  # 60 jours
REMEMBER_ME_EXPIRE_MINUTES = int(os.getenv("REMEMBER_ME_EXPIRE_MINUTES", "129600"))  # 90 jours
SESSION_EXPIRE_MINUTES = int(os.getenv("SESSION_EXPIRE_MINUTES", "1440"))  # 1 jour

# Configuration API
API_TITLE = "BookTime API"
API_DESCRIPTION = "Votre bibliothèque personnelle"
API_VERSION = "1.0.0"

# CORS : voir app/security/cors.py

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
VALID_STATUSES = ["to_read", "reading", "to_reread", "completed"]

# Configuration des langues
SUPPORTED_LANGUAGES = ["fr", "en", "es", "de", "it", "pt", "ru", "ja", "zh", "ko"]
DEFAULT_LANGUAGE = "fr"