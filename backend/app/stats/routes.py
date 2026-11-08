from fastapi import APIRouter, Depends
from datetime import datetime
from collections import defaultdict
from ..database.connection import books_collection
from ..security.jwt import get_current_user
from app.utils.timeutils import utcnow

router = APIRouter(prefix="/api/stats", tags=["stats"])


def _positive_int(value) -> int:
    try:
        n = int(float(value))
    except (TypeError, ValueError):
        return 0
    return n if n > 0 else 0

@router.get("")
def get_stats(current_user: dict = Depends(get_current_user)):
    """Obtenir les statistiques de l'utilisateur"""
    user_filter = {"user_id": current_user["id"]}
    
    total_books = books_collection.count_documents(user_filter)
    completed_books = books_collection.count_documents({**user_filter, "status": "completed"})
    reading_books = books_collection.count_documents({**user_filter, "status": "reading"})
    to_read_books = books_collection.count_documents({**user_filter, "status": "to_read"})
    to_reread_books = books_collection.count_documents({**user_filter, "status": "to_reread"})
    
    roman_count = books_collection.count_documents({**user_filter, "category": "roman"})
    bd_count = books_collection.count_documents({**user_filter, "category": "bd"})
    manga_count = books_collection.count_documents({**user_filter, "category": "manga"})
    
    authors = books_collection.distinct("author", user_filter)
    authors_count = len([a for a in authors if a])
    
    sagas = books_collection.distinct("saga", {**user_filter, "saga": {"$ne": ""}})
    sagas_count = len(sagas)
    
    auto_added_count = books_collection.count_documents({**user_filter, "auto_added": True})

    # Livres terminés cette année
    current_year = utcnow().year
    # Un livre « à relire » a déjà été terminé : il compte comme lu (pages, temps, année, calendrier).
    completed_all = list(books_collection.find({**user_filter, "status": {"$in": ["completed", "to_reread"]}}))
    completion_dates = defaultdict(int)
    total_pages_read = 0
    completed_this_year = 0

    # Livres en cours : on compte les pages déjà lues
    for book in books_collection.find({**user_filter, "status": "reading"}, {"current_page": 1, "total_pages": 1}):
        current = _positive_int(book.get("current_page"))
        total = _positive_int(book.get("total_pages"))
        total_pages_read += min(current, total) if total else current

    for book in completed_all:
        # Pages lues
        total_pages_read += _positive_int(book.get("total_pages"))

        # Livres cochés « déjà lus » à l'inscription : lus avant Booktime, donc ni dans
        # l'objectif de l'année ni dans le calendrier (ils restent comptés comme terminés)
        if book.get("added_via") == "onboarding" and not book.get("date_completed"):
            continue

        # Date de complétion. Un livre « à relire » n'a pas de repli sur la date de mise à jour
        # (elle date du moment où on l'a remis à relire, pas de sa lecture).
        if book.get("status") == "to_reread":
            date_completed = book.get("date_completed")
        else:
            date_completed = book.get("date_completed") or book.get("updated_at") or book.get("date_added")
        if date_completed:
            if hasattr(date_completed, 'year'):
                dt = date_completed
            else:
                try:
                    dt = datetime.fromisoformat(str(date_completed).replace("Z", "+00:00"))
                except Exception:
                    dt = None
            if dt:
                if dt.year == current_year:
                    completed_this_year += 1
                day_key = dt.strftime("%Y-%m-%d")
                completion_dates[day_key] += 1

    # Temps de lecture estimé : 250 mots/min, 300 mots/page → 1.2 min/page
    reading_hours_estimated = round((total_pages_read * 1.2) / 60)

    # Note moyenne sur les livres notés
    rated_books = list(books_collection.find({**user_filter, "rating": {"$gt": 0}}))
    avg_rating = round(sum(b.get("rating", 0) for b in rated_books) / len(rated_books), 1) if rated_books else 0

    # Genres préférés (top 3)
    from collections import Counter
    all_books_list = list(books_collection.find(user_filter, {"genre": 1}))
    genre_counts: Counter = Counter()
    for b in all_books_list:
        g = (b.get("genre") or "").strip()
        if g:
            genre_counts[g] += 1
    top_genres = [{"genre": g, "count": c} for g, c in genre_counts.most_common(5)]

    return {
        "total_books": total_books,
        "completed_books": completed_books,
        "reading_books": reading_books,
        "to_read_books": to_read_books,
        "to_reread_books": to_reread_books,
        "completed_this_year": completed_this_year,
        "total_pages_read": total_pages_read,
        "reading_hours_estimated": reading_hours_estimated,
        "avg_rating": avg_rating,
        "top_genres": top_genres,
        "completion_dates": dict(completion_dates),
        "categories": {
            "roman": roman_count,
            "bd": bd_count,
            "manga": manga_count
        },
        "authors_count": authors_count,
        "sagas_count": sagas_count,
        "auto_added_count": auto_added_count
    }