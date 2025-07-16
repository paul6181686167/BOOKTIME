"""
Routes API Wikidata pour BOOKTIME
Endpoints pour séries, livres et auteurs avec données structurées
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

from .service import wikidata_service
from .models import (
    WikidataAuthorResponse, WikidataSeriesResponse, WikidataSeriesSearchResponse,
    WikidataTestResponse
)

router = APIRouter(prefix="/api/wikidata", tags=["wikidata"])

logger = logging.getLogger(__name__)

@router.get("/author/{author_name}/series", response_model=WikidataAuthorResponse)
async def get_author_series(author_name: str):
    """
    Récupère les séries ET livres individuels d'un auteur depuis Wikidata
    Données structurées avec métadonnées enrichies - VERSION COMPLÈTE
    """
    try:
        logger.info(f"🔍 Recherche œuvres complètes Wikidata pour: {author_name}")
        
        # Récupérer les séries de l'auteur (VERSION ÉLARGIE)
        series_result = await wikidata_service.get_author_series(author_name)
        
        # Récupérer les livres individuels de l'auteur (NOUVEAU)
        individual_books = await wikidata_service.get_author_individual_books(author_name)
        
        # Combiner les résultats
        total_items = len(series_result.series) + len(individual_books) if series_result.found else len(individual_books)
        
        if total_items > 0:
            logger.info(f"✅ {len(series_result.series)} séries + {len(individual_books)} livres individuels trouvés pour {author_name}")
            
            # Convertir les livres individuels au format attendu
            individual_books_formatted = []
            for book in individual_books:
                individual_books_formatted.append({
                    "title": book.title,
                    "publication_date": book.publication_date,
                    "genre": book.genre,
                    "isbn": book.isbn,
                    "publisher": book.publisher,
                    "description": book.description,
                    "book_type": getattr(book, 'book_type', 'literary work'),
                    "source": "wikidata"
                })
            
            return {
                "found": True,
                "source": "wikidata",
                "query_time": series_result.query_time,
                "results_count": total_items,
                "series": series_result.series,
                "individual_books": individual_books_formatted,
                "total_series": len(series_result.series),
                "total_individual_books": len(individual_books)
            }
        else:
            logger.warning(f"❌ Aucune œuvre trouvée pour {author_name}")
            return {
                "found": False,
                "source": "wikidata",
                "query_time": series_result.query_time,
                "results_count": 0,
                "series": [],
                "individual_books": [],
                "total_series": 0,
                "total_individual_books": 0
            }
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des œuvres pour {author_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des œuvres: {str(e)}"
        )

@router.get("/series/{series_id}/books", response_model=WikidataSeriesResponse)
async def get_series_books(series_id: str):
    """
    Récupère les livres d'une série depuis Wikidata
    Données structurées avec volumes, dates et métadonnées
    """
    try:
        logger.info(f"📚 Recherche livres série Wikidata: {series_id}")
        
        # Valider l'ID Wikidata
        if not series_id.startswith('Q'):
            raise HTTPException(
                status_code=400,
                detail="ID série invalide. Doit commencer par 'Q' (ex: Q8337)"
            )
        
        # Récupérer les livres de la série
        result = await wikidata_service.get_series_books(series_id)
        
        if result.found:
            logger.info(f"✅ {result.results_count} livres trouvés pour série {series_id}")
        else:
            logger.warning(f"❌ Aucun livre trouvé pour série {series_id}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des livres pour série {series_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des livres: {str(e)}"
        )

@router.get("/series/{series_id}/info")
async def get_series_info(series_id: str):
    """
    Récupère les informations complètes d'une série
    Métadonnées détaillées et statistiques
    """
    try:
        logger.info(f"ℹ️ Informations série Wikidata: {series_id}")
        
        # Valider l'ID Wikidata
        if not series_id.startswith('Q'):
            raise HTTPException(
                status_code=400,
                detail="ID série invalide. Doit commencer par 'Q' (ex: Q8337)"
            )
        
        # Récupérer les informations et livres en parallèle
        books_result = await wikidata_service.get_series_books(series_id)
        
        if not books_result.found:
            return {
                "found": False,
                "message": f"Série {series_id} non trouvée"
            }
        
        # Calculer les statistiques
        books = books_result.books
        volumes_count = len(books)
        
        # Extraire les années de publication
        years = [book.publication_date for book in books if book.publication_date]
        start_year = min(years) if years else None
        latest_year = max(years) if years else None
        
        # Extraire les genres
        genres = list(set([book.genre for book in books if book.genre]))
        
        # Construire la réponse
        series_info = {
            "found": True,
            "series_id": series_id,
            "volumes_count": volumes_count,
            "start_year": start_year,
            "latest_year": latest_year,
            "genres": genres,
            "books": books,
            "query_time": books_result.query_time
        }
        
        logger.info(f"✅ Informations série {series_id}: {volumes_count} volumes")
        return series_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des informations pour série {series_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des informations: {str(e)}"
        )

@router.get("/search/series", response_model=WikidataSeriesSearchResponse)
async def search_series(
    q: str = Query(..., description="Terme de recherche"),
    limit: int = Query(20, ge=1, le=50, description="Nombre maximum de résultats")
):
    """
    Recherche des séries par nom
    Recherche dans les entités séries de Wikidata
    """
    try:
        logger.info(f"🔍 Recherche séries Wikidata: '{q}' (limite: {limit})")
        
        # Rechercher les séries
        result = await wikidata_service.search_series(q, limit)
        
        if result.found:
            logger.info(f"✅ {result.results_count} séries trouvées pour '{q}'")
        else:
            logger.warning(f"❌ Aucune série trouvée pour '{q}'")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la recherche de séries '{q}': {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la recherche: {str(e)}"
        )

@router.get("/author/{author_name}/info")
async def get_author_info(author_name: str):
    """
    Récupère les informations détaillées d'un auteur
    Métadonnées biographiques et statistiques
    """
    try:
        logger.info(f"👤 Informations auteur Wikidata: {author_name}")
        
        # Récupérer les informations de l'auteur
        author_info = await wikidata_service.get_author_info(author_name)
        
        if not author_info:
            return {
                "found": False,
                "message": f"Auteur '{author_name}' non trouvé sur Wikidata"
            }
        
        # Récupérer également les séries
        series_result = await wikidata_service.get_author_series(author_name)
        
        # Enrichir avec les comptages
        author_info.series_count = len(series_result.series) if series_result.found else 0
        
        return {
            "found": True,
            "source": "wikidata",
            "author": author_info,
            "series": series_result.series if series_result.found else []
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des informations pour {author_name}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des informations: {str(e)}"
        )

@router.get("/test/{author_name}", response_model=WikidataTestResponse)
async def test_wikidata_connection(author_name: str = "rowling"):
    """
    Test de connexion et requête Wikidata
    Endpoint de développement pour vérifier le service
    """
    try:
        logger.info(f"🧪 Test connexion Wikidata avec: {author_name}")
        
        # Tester la connexion
        test_result = await wikidata_service.test_connection(author_name)
        
        return WikidataTestResponse(
            success=test_result.get("success", False),
            query=test_result.get("query", ""),
            results=test_result.get("results", []),
            processed_results=test_result.get("processed_results", {}),
            execution_time=test_result.get("execution_time", 0.0),
            error=test_result.get("error")
        )
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test Wikidata: {str(e)}")
        return WikidataTestResponse(
            success=False,
            query="",
            results=[],
            processed_results={},
            execution_time=0.0,
            error=str(e)
        )

@router.get("/author/{author_name}/works")
async def get_author_works(author_name: str):
    """
    DEPRECATED: Utiliser /author/{author_name}/series à la place
    Récupère les séries ET les livres individuels d'un auteur depuis Wikidata
    """
    return await get_author_series(author_name)

@router.get("/stats")
async def get_wikidata_stats():
    """
    Statistiques du service Wikidata
    Cache, performance et utilisation
    """
    try:
        cache_stats = {
            "cache_size": len(wikidata_service.cache),
            "cache_ttl": wikidata_service.cache_ttl,
            "request_delay": wikidata_service.request_delay,
            "last_request": wikidata_service.last_request_time
        }
        
        return {
            "service_status": "operational",
            "sparql_endpoint": wikidata_service.sparql_endpoint,
            "cache_stats": cache_stats,
            "features": [
                "Series detection",
                "Author information",
                "Book metadata",
                "SPARQL queries",
                "Intelligent caching"
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la récupération des statistiques: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des statistiques: {str(e)}"
        )