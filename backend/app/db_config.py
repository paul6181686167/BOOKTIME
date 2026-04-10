# Connexion MongoDB centralisée pour BOOKTIME
from pymongo import MongoClient
from .config import MONGO_URL, DATABASE_NAME, COLLECTIONS


class _MockDb:
    """Base mock : retourne MockCollection pour tout accès (db.books, db.users, etc.)"""

    def __getattr__(self, name):
        return MockCollection(name)


class _MockClient:
    """Client mock avec attribut booktime pour client.booktime"""

    def __init__(self):
        self.booktime = _MockDb()

    def __getitem__(self, name):
        return _MockDb()


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
        """Initialise la connexion MongoDB - lit MONGO_URL depuis os.environ au runtime"""
        import os

        # Lire MONGO_URL depuis os.environ au moment de la connexion (pas depuis config.py)
        # Cela permet à start_render.py d'injecter la bonne URL avant l'import de l'app
        mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017/booktime")
        db_name = os.environ.get("DATABASE_NAME", DATABASE_NAME)

        print(f"[DB] MONGO_URL utilisee: {mongo_url[:60]}...")
        print(f"[DB] RAILWAY_MONGODB_MOCK={os.environ.get('RAILWAY_MONGODB_MOCK', 'non defini')}")

        if os.environ.get("RAILWAY_MONGODB_MOCK", "").lower() == "true":
            print("[MOCK] MODE MOCK ACTIVE - Pas de connexion MongoDB reelle")
            self._client = _MockClient()
            self._db = _MockDb()
            return

        try:
            # Tentative 1 : connexion simple (cas normal Atlas)
            try:
                self._client = MongoClient(
                    mongo_url,
                    serverSelectionTimeoutMS=20000,
                    connectTimeoutMS=20000,
                )
                self._client.admin.command('ping')
                self._db = self._client[db_name]
                print(f"[OK] Connected to MongoDB: {db_name}")
                return
            except Exception as e1:
                print(f"[WARN] Tentative 1 echouee: {e1}")

            # Tentative 2 : avec tlsAllowInvalidCertificates
            try:
                self._client = MongoClient(
                    mongo_url,
                    serverSelectionTimeoutMS=20000,
                    connectTimeoutMS=20000,
                    tlsAllowInvalidCertificates=True,
                )
                self._client.admin.command('ping')
                self._db = self._client[db_name]
                print(f"[OK] Connected to MongoDB (TLS relaxed): {db_name}")
                return
            except Exception as e2:
                print(f"[WARN] Tentative 2 echouee: {e2}")

        except Exception as e:
            print(f"[ERR] Erreur connexion MongoDB: {e}")

        # Fallback : mode mock
        print("[MOCK] ACTIVATION MODE MOCK - impossible de joindre MongoDB")
        os.environ["RAILWAY_MONGODB_MOCK"] = "true"
        self._client = _MockClient()
        self._db = _MockDb()
    
    @property
    def client(self):
        """Retourne le client MongoDB"""
        return self._client
    
    @property
    def db(self):
        """Retourne la base de données"""
        return self._db
    
    def is_mock_mode(self):
        """Vérifie si on est en mode mock Railway"""
        import os
        return os.environ.get("RAILWAY_MONGODB_MOCK") == "true"
    
    @property
    def users_collection(self):
        """Retourne la collection users"""
        if self.is_mock_mode():
            return MockCollection("users")
        return self._db[COLLECTIONS["users"]]
    
    @property
    def books_collection(self):
        """Retourne la collection books"""
        if self.is_mock_mode():
            return MockCollection("books")
        return self._db[COLLECTIONS["books"]]
    
    @property
    def authors_collection(self):
        """Retourne la collection authors"""
        if self.is_mock_mode():
            return MockCollection("authors")
        return self._db[COLLECTIONS["authors"]]
    
    @property
    def series_library_collection(self):
        """Retourne la collection series_library"""
        if self.is_mock_mode():
            return MockCollection("series_library")
        return self._db[COLLECTIONS["series_library"]]

# Stockage en mémoire pour le mode MOCK - persiste les données pendant la session serveur
_mock_storage = {"users": [], "books": [], "authors": [], "series_library": []}


def _doc_matches(doc, query):
    """Vérifie si un doc correspond au filtre MongoDB simplifié (user_id, $or, $regex, $exists)"""
    if not query:
        return True
    for k, v in query.items():
        if k == "$or":
            if not isinstance(v, list) or not any(_doc_matches(doc, q) for q in v):
                return False
        elif k == "$and":
            if not isinstance(v, list) or not all(_doc_matches(doc, q) for q in v):
                return False
        elif isinstance(v, dict):
            if "$regex" in v:
                import re
                val = doc.get(k) or ""
                if not isinstance(val, str):
                    return False
                flags = re.IGNORECASE if v.get("$options") == "i" else 0
                if not re.search(v["$regex"], val, flags=flags):
                    return False
            elif "$exists" in v:
                has_key = k in doc and doc[k] is not None
                if v["$exists"] != has_key:
                    return False
            elif "$in" in v:
                if doc.get(k) not in v["$in"]:
                    return False
            else:
                if doc.get(k) != v:
                    return False
        elif doc.get(k) != v:
            return False
    return True


class MockCursor:
    """Curseur mock compatible avec l'interface MongoDB pour .sort().skip().limit()"""
    def __init__(self, items):
        self._items = list(items)
        self._sort_spec = None
        self._skip_n = 0
        self._limit_n = None

    def sort(self, key_or_list, direction=None):
        """Accepte .sort([(key, dir)]) ou .sort(key, direction) comme pymongo"""
        if direction is not None:
            self._sort_spec = [(key_or_list, direction)]
        elif isinstance(key_or_list, str):
            self._sort_spec = [(key_or_list, 1)]
        else:
            self._sort_spec = key_or_list
        return self

    def skip(self, n):
        self._skip_n = n
        return self

    def limit(self, n):
        self._limit_n = n
        return self

    def __iter__(self):
        items = self._items
        if self._sort_spec:
            for key, direction in (self._sort_spec or []):
                reverse = direction == -1
                items = sorted(items, key=lambda d: d.get(key) or "", reverse=reverse)
        if self._skip_n:
            items = items[self._skip_n:]
        if self._limit_n is not None:
            items = items[: self._limit_n]
        return iter(items)


class MockCollection:
    """Collection MongoDB mock - users persistés en mémoire pour auth"""
    def __init__(self, name):
        self.name = name
        if name not in _mock_storage:
            _mock_storage[name] = []

    def _get_store(self):
        return _mock_storage.get(self.name, [])

    def find(self, query=None, *args, **kwargs):
        """Mock find - retourne MockCursor pour .sort().skip().limit()"""
        store = self._get_store()
        if not query:
            return MockCursor(list(store))
        return MockCursor([d for d in store if _doc_matches(d, query)])

    def find_one(self, query=None, projection=None, *args, **kwargs):
        """Mock find_one - retourne le premier doc correspondant, respecte projection"""
        store = self._get_store()
        for d in store:
            if _doc_matches(d, query or {}):
                exclude = {"_id"}
                if projection and isinstance(projection, dict) and projection.get("password_hash") == 0:
                    exclude.add("password_hash")
                return {k: v for k, v in d.items() if k not in exclude}
        return None

    def insert_one(self, document):
        """Mock insert_one - persiste en mémoire pour users"""
        import uuid
        doc = dict(document)
        if "id" not in doc:
            doc["id"] = str(uuid.uuid4())
        _mock_storage.setdefault(self.name, []).append(doc)
        return type('MockResult', (), {'inserted_id': doc.get("id", str(uuid.uuid4()))})()
        
    def update_one(self, filter, update, upsert=False, **kwargs):
        """Mock update_one - persiste en mémoire (pour reading-preferences)"""
        store = self._get_store()
        update_spec = update or {}
        set_values = update_spec.get("$set", {})
        set_on_insert = update_spec.get("$setOnInsert", {})

        for i, doc in enumerate(store):
            if _doc_matches(doc, filter):
                for k, v in set_values.items():
                    doc[k] = v
                return type('MockResult', (), {'modified_count': 1, 'matched_count': 1, 'upserted_id': None})()

        if upsert:
            new_doc = {**filter, **set_on_insert, **set_values}
            if "id" not in new_doc:
                import uuid
                new_doc["id"] = str(uuid.uuid4())
            store.append(new_doc)
            return type('MockResult', (), {'modified_count': 0, 'matched_count': 0, 'upserted_id': new_doc.get("id")})()

        return type('MockResult', (), {'modified_count': 0, 'matched_count': 0, 'upserted_id': None})()
        
    def delete_one(self, *args, **kwargs):
        """Mock delete_one - simule suppression"""
        return type('MockResult', (), {'deleted_count': 1})()
        
    def count_documents(self, query=None, *args, **kwargs):
        """Mock count_documents - compte les docs correspondant au filtre"""
        store = self._get_store()
        if not query:
            return len(store)
        return sum(1 for d in store if _doc_matches(d, query))

    def distinct(self, *args, **kwargs):
        """Mock distinct - retourne liste vide"""
        return []

    def aggregate(self, *args, **kwargs):
        """Mock aggregate - retourne liste vide"""
        return []

    def create_index(self, *args, **kwargs):
        """Mock create_index - no-op"""
        pass


# Instance globale de la base de données
database = Database()

# Raccourcis pour les collections
users_collection = database.users_collection
books_collection = database.books_collection
authors_collection = database.authors_collection
series_library_collection = database.series_library_collection