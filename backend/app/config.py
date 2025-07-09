# Configuration centralisée pour BOOKTIME Backend
import os
from dotenv import load_dotenv

# Chargement des variables d'environnement
load_dotenv()

# Configuration MongoDB
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/booktime")

# Configuration JWT
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
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

# Configuration de pagination
DEFAULT_LIMIT = 10
MAX_LIMIT = 100
DEFAULT_OFFSET = 0

# Configuration des catégories
VALID_CATEGORIES = ["roman", "bd", "manga"]
VALID_STATUSES = ["to_read", "reading", "completed"]

# Configuration des langues
SUPPORTED_LANGUAGES = ["fr", "en", "es", "de", "it", "pt", "ru", "ja", "zh", "ko"]
DEFAULT_LANGUAGE = "fr"