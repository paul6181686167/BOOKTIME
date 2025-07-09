from pymongo import MongoClient
from .config import MONGO_URL

# Client MongoDB
client = MongoClient(MONGO_URL)
db = client.booktime

# Collections
users_collection = db.users
books_collection = db.books
authors_collection = db.authors
series_library_collection = db.series_library