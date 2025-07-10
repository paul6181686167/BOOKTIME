"""
PHASE 3.5 - Routes API pour Intégrations Externes
Endpoints pour intégrations tierces et services externes
"""
from fastapi import APIRouter, HTTPException, Depends, Query, File, UploadFile, Form
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from ..security.jwt import get_current_user
from .goodreads_service import goodreads_service
from .google_books_service import google_books_service
from .librarything_service import librarything_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/integrations", tags=["external_integrations"])

# === GOODREADS INTEGRATION ===

@router.post("/goodreads/import")
async def import_goodreads_csv(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Importe un export CSV de Goodreads
    
    Args:
        file: Fichier CSV d'export Goodreads
        current_user: Utilisateur connecté
        
    Returns:
        Dict avec résultats d'import
    """
    try:
        # Vérifier le format du fichier
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Le fichier doit être un CSV")
        
        # Lire le contenu
        csv_content = await file.read()
        csv_text = csv_content.decode('utf-8')
        
        # Parser le CSV Goodreads
        goodreads_books = await goodreads_service.parse_goodreads_export(csv_text)
        
        if not goodreads_books:
            raise HTTPException(status_code=400, detail="Aucun livre trouvé dans le CSV")
        
        # Convertir au format BookTime
        booktime_books = await goodreads_service.convert_to_booktime_format(goodreads_books)
        
        # Statistiques
        stats = {
            'total_books': len(goodreads_books),
            'converted_books': len(booktime_books),
            'categories': {},
            'statuses': {}
        }
        
        for book in booktime_books:
            category = book.get('category', 'unknown')
            status = book.get('status', 'unknown')
            
            stats['categories'][category] = stats['categories'].get(category, 0) + 1
            stats['statuses'][status] = stats['statuses'].get(status, 0) + 1
        
        return {
            "success": True,
            "message": f"Import Goodreads terminé: {len(booktime_books)} livres convertis",
            "data": {
                "books": booktime_books,
                "statistics": stats,
                "import_source": "goodreads_csv"
            },
            "imported_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing Goodreads CSV: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'import Goodreads: {str(e)}"
        )

# === GOOGLE BOOKS INTEGRATION ===

@router.get("/google-books/search")
async def search_google_books(
    query: str = Query(..., description="Terme de recherche"),
    max_results: int = Query(20, ge=1, le=40, description="Nombre maximum de résultats"),
    current_user: dict = Depends(get_current_user)
):
    """
    Rechercher des livres sur Google Books
    
    Args:
        query: Terme de recherche
        max_results: Nombre maximum de résultats
        current_user: Utilisateur connecté
        
    Returns:
        Dict avec résultats de recherche
    """
    try:
        books = await google_books_service.search_books(query, max_results)
        
        return {
            "success": True,
            "message": f"Recherche Google Books terminée: {len(books)} livres trouvés",
            "data": {
                "books": books,
                "query": query,
                "results_count": len(books),
                "source": "google_books"
            },
            "searched_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error searching Google Books: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la recherche Google Books: {str(e)}"
        )

@router.get("/google-books/details/{volume_id}")
async def get_google_book_details(
    volume_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Récupérer les détails d'un livre Google Books
    
    Args:
        volume_id: ID du volume Google Books
        current_user: Utilisateur connecté
        
    Returns:
        Dict avec détails du livre
    """
    try:
        book = await google_books_service.get_book_details(volume_id)
        
        if not book:
            raise HTTPException(status_code=404, detail="Livre non trouvé sur Google Books")
        
        return {
            "success": True,
            "message": "Détails du livre Google Books récupérés",
            "data": {
                "book": book,
                "source": "google_books"
            },
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Google Books details: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des détails: {str(e)}"
        )

# === LIBRARYTHING INTEGRATION ===

@router.get("/librarything/recommendations")
async def get_librarything_recommendations(
    isbn: str = Query(..., description="ISBN du livre"),
    current_user: dict = Depends(get_current_user)
):
    """
    Récupérer les recommandations LibraryThing pour un livre
    
    Args:
        isbn: ISBN du livre
        current_user: Utilisateur connecté
        
    Returns:
        Dict avec recommandations
    """
    try:
        recommendations = await librarything_service.get_book_recommendations(isbn)
        
        return {
            "success": True,
            "message": f"Recommandations LibraryThing: {len(recommendations)} livres trouvés",
            "data": {
                "recommendations": recommendations,
                "source_isbn": isbn,
                "source": "librarything"
            },
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting LibraryThing recommendations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des recommandations: {str(e)}"
        )

@router.get("/librarything/tags")
async def get_librarything_tags(
    isbn: str = Query(..., description="ISBN du livre"),
    current_user: dict = Depends(get_current_user)
):
    """
    Récupérer les tags LibraryThing pour un livre
    
    Args:
        isbn: ISBN du livre
        current_user: Utilisateur connecté
        
    Returns:
        Dict avec tags
    """
    try:
        tags = await librarything_service.get_book_tags(isbn)
        
        return {
            "success": True,
            "message": f"Tags LibraryThing: {len(tags)} tags trouvés",
            "data": {
                "tags": tags,
                "source_isbn": isbn,
                "source": "librarything"
            },
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting LibraryThing tags: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des tags: {str(e)}"
        )

# === INTÉGRATIONS COMBINÉES ===

@router.get("/combined-search")
async def combined_external_search(
    query: str = Query(..., description="Terme de recherche"),
    sources: str = Query("google_books", description="Sources séparées par virgule (google_books,openlibrary)"),
    max_results_per_source: int = Query(10, ge=1, le=20, description="Résultats max par source"),
    current_user: dict = Depends(get_current_user)
):
    """
    Recherche combinée sur plusieurs sources externes
    
    Args:
        query: Terme de recherche
        sources: Sources à utiliser
        max_results_per_source: Nombre max de résultats par source
        current_user: Utilisateur connecté
        
    Returns:
        Dict avec résultats combinés
    """
    try:
        source_list = [s.strip() for s in sources.split(',')]
        combined_results = []
        
        # Google Books
        if 'google_books' in source_list:
            google_books = await google_books_service.search_books(query, max_results_per_source)
            combined_results.extend(google_books)
        
        # TODO: Ajouter d'autres sources externes
        
        # Déduplication basée sur ISBN ou titre
        unique_results = []
        seen_books = set()
        
        for book in combined_results:
            # Clé unique basée sur ISBN ou titre+auteur
            isbn = book.get('isbn', '') or book.get('isbn13', '')
            title_author = f"{book.get('title', '').lower()}-{book.get('author', '').lower()}"
            
            unique_key = isbn if isbn else title_author
            
            if unique_key not in seen_books:
                seen_books.add(unique_key)
                unique_results.append(book)
        
        return {
            "success": True,
            "message": f"Recherche combinée terminée: {len(unique_results)} livres uniques",
            "data": {
                "books": unique_results,
                "query": query,
                "sources_used": source_list,
                "total_results": len(combined_results),
                "unique_results": len(unique_results),
                "deduplication_applied": len(combined_results) > len(unique_results)
            },
            "searched_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in combined search: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la recherche combinée: {str(e)}"
        )

# === STATISTIQUES ET CONFIGURATION ===

@router.get("/stats")
async def get_integrations_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    Récupérer les statistiques des intégrations externes
    
    Args:
        current_user: Utilisateur connecté
        
    Returns:
        Dict avec statistiques
    """
    try:
        # TODO: Implémenter vraies statistiques depuis la base de données
        stats = {
            "supported_integrations": [
                {
                    "name": "Goodreads",
                    "type": "import",
                    "description": "Import CSV d'export Goodreads",
                    "supported_formats": ["csv"],
                    "status": "active"
                },
                {
                    "name": "Google Books",
                    "type": "search",
                    "description": "Recherche dans la base Google Books",
                    "supported_formats": ["api"],
                    "status": "active"
                },
                {
                    "name": "LibraryThing",
                    "type": "recommendations",
                    "description": "Recommandations et tags",
                    "supported_formats": ["api"],
                    "status": "active"
                }
            ],
            "usage_stats": {
                "goodreads_imports": 0,
                "google_searches": 0,
                "librarything_requests": 0
            }
        }
        
        return {
            "success": True,
            "data": stats,
            "retrieved_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting integrations stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des statistiques: {str(e)}"
        )

@router.get("/health")
async def integrations_health():
    """Vérification de santé du module intégrations externes"""
    try:
        health_status = {
            "status": "ok",
            "module": "external_integrations",
            "services": {
                "goodreads_service": "available",
                "google_books_service": "available",
                "librarything_service": "available"
            },
            "features": [
                "goodreads_csv_import",
                "google_books_search",
                "librarything_recommendations",
                "combined_search",
                "deduplication"
            ],
            "supported_formats": [
                "csv",
                "api",
                "xml",
                "json"
            ]
        }
        
        return health_status
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur module intégrations externes: {str(e)}"
        )