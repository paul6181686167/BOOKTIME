from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration MongoDB
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/booktime")

# Client MongoDB
client = MongoClient(MONGO_URL)
db = client.booktime

# Collections
users_collection = db.users
books_collection = db.books
authors_collection = db.authors
series_library_collection = db.series_library