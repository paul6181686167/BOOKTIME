# Connexion MongoDB centralisée pour BOOKTIME
from pymongo import MongoClient
from .config import MONGO_URL, DATABASE_NAME, COLLECTIONS

class Database:
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialise la connexion MongoDB"""
        try:
            self._client = MongoClient(MONGO_URL)
            self._db = self._client[DATABASE_NAME]
            print(f"✅ Connected to MongoDB: {DATABASE_NAME}")
        except Exception as e:
            print(f"❌ Error connecting to MongoDB: {e}")
            raise
    
    @property
    def client(self):
        """Retourne le client MongoDB"""
        return self._client
    
    @property
    def db(self):
        """Retourne la base de données"""
        return self._db
    
    @property
    def users_collection(self):
        """Retourne la collection users"""
        return self._db[COLLECTIONS["users"]]
    
    @property
    def books_collection(self):
        """Retourne la collection books"""
        return self._db[COLLECTIONS["books"]]
    
    @property
    def authors_collection(self):
        """Retourne la collection authors"""
        return self._db[COLLECTIONS["authors"]]
    
    @property
    def series_library_collection(self):
        """Retourne la collection series_library"""
        return self._db[COLLECTIONS["series_library"]]
    
    def close(self):
        """Ferme la connexion MongoDB"""
        if self._client:
            self._client.close()
            print("✅ MongoDB connection closed")

# Instance globale de la base de données
database = Database()

# Raccourcis pour les collections
users_collection = database.users_collection
books_collection = database.books_collection
authors_collection = database.authors_collection
series_library_collection = database.series_library_collection