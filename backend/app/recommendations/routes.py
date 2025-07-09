"""
PHASE 3.1 - Système de Recommandations - Routes API
Endpoints pour les recommandations personnalisées
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from datetime import datetime

from ..security.jwt import get_current_user
from .service import RecommendationService

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])

# Instance du service
recommendation_service = RecommendationService()

@router.get("/personalized")
async def get_personalized_recommendations(
    current_user: dict = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=50, description="Nombre de recommandations"),
    category: Optional[str] = Query(None, description="Filtrer par catégorie"),
    refresh: bool = Query(False, description="Forcer la régénération")
):
    """
    Récupère les recommandations personnalisées pour l'utilisateur connecté
    
    Args:
        current_user: Utilisateur connecté
        limit: Nombre maximum de recommandations
        category: Filtrer par catégorie (optionnel)
        refresh: Forcer la régénération du cache
        
    Returns:
        Dict contenant les recommandations et métadonnées
    """
    try:
        user_id = current_user.get("user_id")
        
        # Génération des recommandations
        recommendations = await recommendation_service.get_personalized_recommendations(
            user_id=user_id,
            limit=limit
        )
        
        # Filtrage par catégorie si demandé
        if category:
            filtered_recs = []
            for rec in recommendations.get('recommendations', []):
                if rec.get('category') == category:
                    filtered_recs.append(rec)
            recommendations['recommendations'] = filtered_recs[:limit]
            recommendations['filtered_by'] = category
        
        return {
            "success": True,
            "data": recommendations,
            "count": len(recommendations.get('recommendations', [])),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération des recommandations: {str(e)}"
        )

@router.get("/popular")
async def get_popular_recommendations(
    limit: int = Query(10, ge=1, le=50, description="Nombre de recommandations"),
    category: Optional[str] = Query(None, description="Filtrer par catégorie")
):
    """
    Récupère les recommandations populaires (sans authentification)
    
    Args:
        limit: Nombre maximum de recommandations
        category: Filtrer par catégorie (optionnel)
        
    Returns:
        Dict contenant les recommandations populaires
    """
    try:
        recommendations = await recommendation_service._get_popular_recommendations(limit)
        
        # Filtrage par catégorie si demandé
        if category:
            filtered_recs = []
            for rec in recommendations.get('recommendations', []):
                if rec.get('category') == category:
                    filtered_recs.append(rec)
            recommendations['recommendations'] = filtered_recs[:limit]
            recommendations['filtered_by'] = category
        
        return {
            "success": True,
            "data": recommendations,
            "count": len(recommendations.get('recommendations', [])),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des recommandations populaires: {str(e)}"
        )

@router.get("/by-author/{author_name}")
async def get_recommendations_by_author(
    author_name: str,
    current_user: dict = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=50, description="Nombre de recommandations")
):
    """
    Récupère les recommandations basées sur un auteur spécifique
    
    Args:
        author_name: Nom de l'auteur
        current_user: Utilisateur connecté
        limit: Nombre maximum de recommandations
        
    Returns:
        Dict contenant les recommandations de l'auteur
    """
    try:
        user_id = current_user.get("user_id")
        
        # Créer un profil utilisateur factice centré sur cet auteur
        fake_profile = {
            'has_books': True,
            'favorite_authors': [author_name],
            'favorite_categories': ['roman'],
            'high_rated_books': [],
            'completed_books': []
        }
        
        # Générer des recommandations basées sur cet auteur
        author_recommendations = await recommendation_service._recommend_by_authors(
            fake_profile, limit
        )
        
        formatted_recs = [
            recommendation_service._format_recommendation(rec) 
            for rec in author_recommendations
        ]
        
        return {
            "success": True,
            "data": {
                "recommendations": formatted_recs,
                "author": author_name,
                "count": len(formatted_recs)
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des recommandations par auteur: {str(e)}"
        )

@router.get("/by-category/{category}")
async def get_recommendations_by_category(
    category: str,
    current_user: dict = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=50, description="Nombre de recommandations")
):
    """
    Récupère les recommandations basées sur une catégorie spécifique
    
    Args:
        category: Catégorie (roman, bd, manga)
        current_user: Utilisateur connecté
        limit: Nombre maximum de recommandations
        
    Returns:
        Dict contenant les recommandations de la catégorie
    """
    try:
        user_id = current_user.get("user_id")
        
        # Créer un profil utilisateur factice centré sur cette catégorie
        fake_profile = {
            'has_books': True,
            'favorite_authors': [],
            'favorite_categories': [category],
            'high_rated_books': [],
            'completed_books': []
        }
        
        # Générer des recommandations basées sur cette catégorie
        category_recommendations = await recommendation_service._recommend_by_categories(
            fake_profile, limit
        )
        
        formatted_recs = [
            recommendation_service._format_recommendation(rec) 
            for rec in category_recommendations
        ]
        
        return {
            "success": True,
            "data": {
                "recommendations": formatted_recs,
                "category": category,
                "count": len(formatted_recs)
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des recommandations par catégorie: {str(e)}"
        )

@router.get("/user-profile")
async def get_user_profile(
    current_user: dict = Depends(get_current_user)
):
    """
    Récupère le profil utilisateur utilisé pour les recommandations
    
    Args:
        current_user: Utilisateur connecté
        
    Returns:
        Dict contenant le profil utilisateur
    """
    try:
        user_id = current_user.get("user_id")
        
        # Analyser la bibliothèque utilisateur
        user_profile = await recommendation_service._analyze_user_library(user_id)
        
        return {
            "success": True,
            "data": user_profile,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération du profil utilisateur: {str(e)}"
        )

@router.post("/feedback")
async def submit_recommendation_feedback(
    recommendation_id: str,
    feedback: str,  # 'like', 'dislike', 'added_to_library', 'not_interested'
    current_user: dict = Depends(get_current_user)
):
    """
    Permet à l'utilisateur de donner un feedback sur une recommandation
    
    Args:
        recommendation_id: ID de la recommandation
        feedback: Type de feedback
        current_user: Utilisateur connecté
        
    Returns:
        Dict confirmant l'enregistrement du feedback
    """
    try:
        user_id = current_user.get("user_id")
        
        # Enregistrer le feedback dans la base de données
        feedback_data = {
            "user_id": user_id,
            "recommendation_id": recommendation_id,
            "feedback": feedback,
            "timestamp": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }
        
        # Insérer dans la collection feedback
        recommendation_service.db.recommendation_feedback.insert_one(feedback_data)
        
        return {
            "success": True,
            "message": "Feedback enregistré avec succès",
            "data": {
                "recommendation_id": recommendation_id,
                "feedback": feedback,
                "user_id": user_id
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'enregistrement du feedback: {str(e)}"
        )

@router.get("/stats")
async def get_recommendation_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    Récupère les statistiques des recommandations pour l'utilisateur
    
    Args:
        current_user: Utilisateur connecté
        
    Returns:
        Dict contenant les statistiques
    """
    try:
        user_id = current_user.get("user_id")
        
        # Compter les feedbacks par type
        feedback_stats = {}
        feedback_types = ['like', 'dislike', 'added_to_library', 'not_interested']
        
        for feedback_type in feedback_types:
            count = recommendation_service.db.recommendation_feedback.count_documents({
                "user_id": user_id,
                "feedback": feedback_type
            })
            feedback_stats[feedback_type] = count
        
        # Statistiques générales
        total_feedback = sum(feedback_stats.values())
        total_recommendations = recommendation_service.db.recommendation_feedback.count_documents({
            "user_id": user_id
        })
        
        return {
            "success": True,
            "data": {
                "feedback_stats": feedback_stats,
                "total_feedback": total_feedback,
                "total_recommendations": total_recommendations,
                "engagement_rate": (total_feedback / total_recommendations * 100) if total_recommendations > 0 else 0
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des statistiques: {str(e)}"
        )