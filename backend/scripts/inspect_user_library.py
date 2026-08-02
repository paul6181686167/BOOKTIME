"""Inspecte la bibliothèque Mongo d'un utilisateur."""
from collections import Counter
from pymongo import MongoClient

UID = "f2cf159e-74b3-463c-8740-8126775acae2"
URI = (
    "mongodb+srv://berruyerpaul222_db_user:TggFAId06ZwWKEPC@"
    "booktime-prod.wnnbmls.mongodb.net/?retryWrites=true&w=majority"
)

db = MongoClient(URI, serverSelectionTimeoutMS=15000)["booktime"]
books = list(
    db.books.find(
        {"user_id": UID},
        {"_id": 0, "title": 1, "status": 1, "category": 1, "saga": 1},
    )
)
series = list(
    db.series_library.find(
        {"user_id": UID},
        {
            "_id": 0,
            "series_name": 1,
            "name": 1,
            "category": 1,
            "series_status": 1,
            "volumes": 1,
        },
    )
)

print("BOOKS", len(books))
for b in books:
    print(" -", b.get("title"), "|", b.get("status"), "|", b.get("category"))

print("SERIES", len(series))
print("series cats", dict(Counter((s.get("category") or "?") for s in series)))
empty = sum(1 for s in series if not (s.get("volumes") or []))
print("series with 0 volumes", empty)

for s in sorted(series, key=lambda x: (x.get("series_name") or x.get("name") or "")):
    name = s.get("series_name") or s.get("name")
    vols = s.get("volumes") or []
    print(
        "  S:",
        name,
        "|",
        s.get("category"),
        "| vols=",
        len(vols),
        "|",
        s.get("series_status"),
    )

print("users", list(db.users.find({}, {"_id": 0, "id": 1, "email": 1})))
