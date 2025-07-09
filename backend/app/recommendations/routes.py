from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import aiohttp
from collections import Counter
import logging

from ..auth.dependencies import get_current_user
from ..database.connection import db

# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])

# === MODELS PYDANTIC ===

class RecommendationItem(BaseModel):
    ol_key: str
    title: str
    author: str
    category: str
    cover_url: Optional[str] = None
    description: Optional[str] = None
    reason: str
    confidence_score: float
    publication_year: Optional[int] = None
    publisher: Optional[str] = None

class RecommendationsResponse(BaseModel):
    recommendations: List[RecommendationItem]
    total_count: int
    algorithm_version: str
    generated_at: str
    user_profile: Dict[str, Any]

class UserProfile(BaseModel):
    favorite_authors: List[Dict[str, Any]]
    favorite_categories: List[Dict[str, Any]]
    favorite_genres: List[Dict[str, Any]]
    completed_series: List[str]
    reading_patterns: Dict[str, Any]
    total_books: int

# === ALGORITHME DE RECOMMANDATIONS ===

class RecommendationEngine:
    def __init__(self):
        self.version = "1.0.0"
        self.base_url = "https://openlibrary.org"
        
    async def analyze_user_profile(self, user_id: str) -> UserProfile:
        """
        Analyse le profil utilisateur pour extraire les préférences
        """
        try:
            # Récupération des livres de l'utilisateur
            books_cursor = db.books.find({"user_id": user_id})
            books = await books_cursor.to_list(length=None)
            
            if not books:
                return UserProfile(
                    favorite_authors=[],
                    favorite_categories=[],
                    favorite_genres=[],
                    completed_series=[],
                    reading_patterns={},
                    total_books=0
                )
            
            # Analyse des auteurs préférés
            authors = [book.get("author", "").strip() for book in books if book.get("author")]
            author_counts = Counter(authors)
            favorite_authors = [
                {"name": author, "count": count, "avg_rating": self._get_avg_rating(books, author)}
                for author, count in author_counts.most_common(10)
            ]
            
            # Analyse des catégories préférées
            categories = [book.get("category", "").strip() for book in books if book.get("category")]
            category_counts = Counter(categories)
            favorite_categories = [
                {"name": category, "count": count, "completion_rate": self._get_completion_rate(books, category)}
                for category, count in category_counts.most_common()
            ]
            
            # Analyse des genres préférés
            genres = []
            for book in books:
                if book.get("genre"):
                    genres.extend([g.strip() for g in book["genre"].split(",")])
            genre_counts = Counter(genres)
            favorite_genres = [
                {"name": genre, "count": count}
                for genre, count in genre_counts.most_common(20)
            ]
            
            # Séries complétées
            completed_series = []
            saga_books = {}
            for book in books:
                if book.get("saga") and book.get("status") == "completed":
                    saga = book["saga"]
                    if saga not in saga_books:
                        saga_books[saga] = []
                    saga_books[saga].append(book)
            
            for saga, saga_book_list in saga_books.items():
                if len(saga_book_list) >= 3:  # Considérer comme série si 3+ livres
                    completed_series.append(saga)
            
            # Patterns de lecture
            reading_patterns = {
                "avg_rating": sum(book.get("rating", 0) for book in books if book.get("rating")) / max(len([b for b in books if b.get("rating")]), 1),
                "completion_rate": len([b for b in books if b.get("status") == "completed"]) / len(books),
                "series_preference": len([b for b in books if b.get("saga")]) / len(books),
                "recent_activity": len([b for b in books if self._is_recent(b.get("date_added"))]) / len(books)
            }
            
            return UserProfile(
                favorite_authors=favorite_authors,
                favorite_categories=favorite_categories,
                favorite_genres=favorite_genres,
                completed_series=completed_series,
                reading_patterns=reading_patterns,
                total_books=len(books)
            )
            
        except Exception as e:
            logger.error(f"Error analyzing user profile: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to analyze user profile")
    
    def _get_avg_rating(self, books: List[Dict], author: str) -> float:
        """Calcule la note moyenne pour un auteur"""
        author_books = [b for b in books if b.get("author") == author and b.get("rating")]
        if not author_books:
            return 0.0
        return sum(b["rating"] for b in author_books) / len(author_books)
    
    def _get_completion_rate(self, books: List[Dict], category: str) -> float:
        """Calcule le taux de completion pour une catégorie"""
        category_books = [b for b in books if b.get("category") == category]
        if not category_books:
            return 0.0
        completed = len([b for b in category_books if b.get("status") == "completed"])
        return completed / len(category_books)
    
    def _is_recent(self, date_added) -> bool:
        """Vérifie si un livre a été ajouté récemment (30 derniers jours)"""
        if not date_added:
            return False
        try:
            from datetime import datetime, timedelta
            if isinstance(date_added, str):
                date_added = datetime.fromisoformat(date_added.replace('Z', '+00:00'))
            return (datetime.now() - date_added).days <= 30
        except:
            return False
    
    async def search_openlibrary(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Recherche dans Open Library avec gestion d'erreurs
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/search.json"
                params = {
                    "q": query,
                    "limit": limit,
                    "fields": "key,title,author_name,first_publish_year,publisher,cover_i,subject"
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("docs", [])
                    else:
                        logger.warning(f"OpenLibrary API returned status {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error searching OpenLibrary: {str(e)}")
            return []
    
    def _categorize_book(self, book_data: Dict) -> str:
        """
        Catégorise automatiquement un livre basé sur ses sujets
        """
        subjects = book_data.get("subject", [])
        if not subjects:
            return "roman"
        
        subjects_str = " ".join(subjects).lower()
        
        # Détection BD
        bd_keywords = ["comic", "comics", "graphic novel", "bande dessinée", "bd", "strip"]
        if any(keyword in subjects_str for keyword in bd_keywords):
            return "bd"
        
        # Détection Manga
        manga_keywords = ["manga", "japanese comics", "manhwa", "manhua"]
        if any(keyword in subjects_str for keyword in manga_keywords):
            return "manga"
        
        # Par défaut : roman
        return "roman"
    
    def _get_cover_url(self, book_data: Dict) -> Optional[str]:
        """
        Génère l'URL de couverture depuis les données OpenLibrary
        """
        cover_id = book_data.get("cover_i")
        if cover_id:
            return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
        return None
    
    async def generate_author_recommendations(self, user_profile: UserProfile, limit: int = 5) -> List[RecommendationItem]:
        """
        Génère des recommandations basées sur les auteurs préférés
        """
        recommendations = []
        
        for author_data in user_profile.favorite_authors[:3]:  # Top 3 auteurs
            author_name = author_data["name"]
            
            # Recherche d'autres livres du même auteur
            books_data = await self.search_openlibrary(f"author:{author_name}", limit=5)
            
            for book_data in books_data[:2]:  # Max 2 livres par auteur
                try:
                    recommendation = RecommendationItem(
                        ol_key=book_data.get("key", "").replace("/works/", ""),
                        title=book_data.get("title", ""),
                        author=", ".join(book_data.get("author_name", [])),
                        category=self._categorize_book(book_data),
                        cover_url=self._get_cover_url(book_data),
                        reason=f"Recommandé car vous avez aimé {author_data['count']} livre(s) de {author_name}",
                        confidence_score=0.8 + (author_data["avg_rating"] / 5) * 0.2,
                        publication_year=book_data.get("first_publish_year"),
                        publisher=", ".join(book_data.get("publisher", [])[:2])
                    )
                    recommendations.append(recommendation)
                    
                    if len(recommendations) >= limit:
                        break
                        
                except Exception as e:
                    logger.error(f"Error processing author recommendation: {str(e)}")
                    continue
            
            if len(recommendations) >= limit:
                break
        
        return recommendations
    
    async def generate_genre_recommendations(self, user_profile: UserProfile, limit: int = 5) -> List[RecommendationItem]:
        """
        Génère des recommandations basées sur les genres préférés
        """
        recommendations = []
        
        for genre_data in user_profile.favorite_genres[:5]:  # Top 5 genres
            genre_name = genre_data["name"]
            
            # Recherche de livres dans ce genre
            books_data = await self.search_openlibrary(f"subject:{genre_name}", limit=3)
            
            for book_data in books_data[:1]:  # Max 1 livre par genre
                try:
                    recommendation = RecommendationItem(
                        ol_key=book_data.get("key", "").replace("/works/", ""),
                        title=book_data.get("title", ""),
                        author=", ".join(book_data.get("author_name", [])),
                        category=self._categorize_book(book_data),
                        cover_url=self._get_cover_url(book_data),
                        reason=f"Recommandé car vous lisez souvent le genre '{genre_name}' ({genre_data['count']} livres)",
                        confidence_score=0.6 + (genre_data["count"] / user_profile.total_books) * 0.4,
                        publication_year=book_data.get("first_publish_year"),
                        publisher=", ".join(book_data.get("publisher", [])[:2])
                    )
                    recommendations.append(recommendation)
                    
                    if len(recommendations) >= limit:
                        break
                        
                except Exception as e:
                    logger.error(f"Error processing genre recommendation: {str(e)}")
                    continue
            
            if len(recommendations) >= limit:
                break
        
        return recommendations
    
    async def generate_series_recommendations(self, user_profile: UserProfile, limit: int = 3) -> List[RecommendationItem]:
        """
        Génère des recommandations basées sur les séries complétées
        """
        recommendations = []
        
        for completed_series in user_profile.completed_series[:3]:  # Top 3 séries complétées
            # Recherche de séries similaires
            similar_keywords = ["series", "saga", "collection", "volume"]
            query = f"{completed_series} {' '.join(similar_keywords)}"
            
            books_data = await self.search_openlibrary(query, limit=2)
            
            for book_data in books_data[:1]:  # Max 1 recommandation par série
                try:
                    recommendation = RecommendationItem(
                        ol_key=book_data.get("key", "").replace("/works/", ""),
                        title=book_data.get("title", ""),
                        author=", ".join(book_data.get("author_name", [])),
                        category=self._categorize_book(book_data),
                        cover_url=self._get_cover_url(book_data),
                        reason=f"Recommandé car vous avez complété la série '{completed_series}'",
                        confidence_score=0.7,
                        publication_year=book_data.get("first_publish_year"),
                        publisher=", ".join(book_data.get("publisher", [])[:2])
                    )
                    recommendations.append(recommendation)
                    
                    if len(recommendations) >= limit:
                        break
                        
                except Exception as e:
                    logger.error(f"Error processing series recommendation: {str(e)}")
                    continue
            
            if len(recommendations) >= limit:
                break
        
        return recommendations

# Instance globale de l'engine
recommendation_engine = RecommendationEngine()

# === ENDPOINTS ===

@router.get("/", response_model=RecommendationsResponse)
async def get_recommendations(
    limit: int = 20,
    category: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    """
    PHASE 3.1 - Génère des recommandations personnalisées pour l'utilisateur
    Analyse le profil utilisateur et propose des livres pertinents
    """
    try:
        user_id = current_user["id"]
        
        # Analyse du profil utilisateur
        user_profile = await recommendation_engine.analyze_user_profile(user_id)
        
        if user_profile.total_books == 0:
            # Utilisateur sans livres : recommandations génériques
            generic_recommendations = await _get_generic_recommendations(limit)
            return RecommendationsResponse(
                recommendations=generic_recommendations,
                total_count=len(generic_recommendations),
                algorithm_version=recommendation_engine.version,
                generated_at=datetime.utcnow().isoformat(),
                user_profile=user_profile.dict()
            )
        
        # Génération des recommandations par type
        author_recs = await recommendation_engine.generate_author_recommendations(user_profile, limit=limit//2)
        genre_recs = await recommendation_engine.generate_genre_recommendations(user_profile, limit=limit//3)
        series_recs = await recommendation_engine.generate_series_recommendations(user_profile, limit=limit//4)
        
        # Combinaison et tri par score de confiance
        all_recommendations = author_recs + genre_recs + series_recs
        all_recommendations.sort(key=lambda x: x.confidence_score, reverse=True)
        
        # Filtrage par catégorie si spécifiée
        if category:
            all_recommendations = [r for r in all_recommendations if r.category == category]
        
        # Limitation finale
        final_recommendations = all_recommendations[:limit]
        
        return RecommendationsResponse(
            recommendations=final_recommendations,
            total_count=len(final_recommendations),
            algorithm_version=recommendation_engine.version,
            generated_at=datetime.utcnow().isoformat(),
            user_profile=user_profile.dict()
        )
        
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")

@router.get("/profile")
async def get_user_profile(current_user: Dict = Depends(get_current_user)):
    """
    PHASE 3.1 - Retourne le profil d'analyse utilisateur
    """
    try:
        user_id = current_user["id"]
        user_profile = await recommendation_engine.analyze_user_profile(user_id)
        
        return {
            "user_profile": user_profile.dict(),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user profile")

async def _get_generic_recommendations(limit: int) -> List[RecommendationItem]:
    """
    Recommandations génériques pour nouveaux utilisateurs
    """
    generic_books = [
        {
            "title": "Harry Potter à l'école des sorciers",
            "author": "J.K. Rowling",
            "category": "roman",
            "reason": "Classique populaire recommandé pour débuter"
        },
        {
            "title": "Astérix le Gaulois",
            "author": "René Goscinny, Albert Uderzo",
            "category": "bd",
            "reason": "BD française emblématique"
        },
        {
            "title": "One Piece",
            "author": "Eiichiro Oda",
            "category": "manga",
            "reason": "Manga d'aventure très populaire"
        }
    ]
    
    recommendations = []
    for book in generic_books[:limit]:
        rec = RecommendationItem(
            ol_key=f"generic_{book['title'].replace(' ', '_')}",
            title=book["title"],
            author=book["author"],
            category=book["category"],
            reason=book["reason"],
            confidence_score=0.5
        )
        recommendations.append(rec)
    
    return recommendations