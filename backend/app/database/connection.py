"""
Connexion MongoDB - Délègue à db_config pour supporter le mode MOCK (RAILWAY_MONGODB_MOCK=true).
Quand MongoDB Atlas est inaccessible (SSL), le mode MOCK permet l'inscription et la navigation.
"""
from ..db_config import (
    database,
    users_collection,
    books_collection,
    authors_collection,
    series_library_collection,
)
client = database.client
db = database.db
