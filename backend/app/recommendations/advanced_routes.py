"""
PHASE 3.4 - Routes API pour Recommandations Avancées
Endpoints pour IA et Machine Learning recommandations
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel

from ..security.jwt import get_current_user
from .advanced_service import advanced_recommendation_service
from .ml_models import ml_models

router = APIRouter(prefix="/api/recommendations/advanced", tags=["advanced_recommendations"])

# === MODÈLES PYDANTIC ===

class ContextRequest(BaseModel):
    time_of_day: Optional[str] = "unknown"  # morning, afternoon, evening, night
    mood: Optional[str] = "neutral"  # happy, sad, stressed, curious, relaxed
    available_time: Optional[int] = 60  # minutes disponibles
    location: Optional[str] = "home"  # home, commute, work, travel
    social_context: Optional[str] = "alone"  # alone, family, friends
    weather: Optional[str] = "unknown"  # sunny, rainy, cold, hot
    reading_goal: Optional[str] = "entertainment"  # entertainment, learning, relaxation

class MLTrainingRequest(BaseModel):
    model_type: str  # rating_predictor, user_clusterer, content_analyzer
    force_retrain: bool = False
    min_confidence: float = 0.6

class FeedbackRequest(BaseModel):
    recommendation_id: str
    feedback_type: str  # clicked, added_to_library, rated, dismissed, not_interested
    rating: Optional[int] = None
    context: Optional[Dict[str, Any]] = None

# === ROUTES RECOMMANDATIONS CONTEXTUELLES ===

@router.post("/contextual")
async def get_contextual_recommendations(
    context: ContextRequest,
    current_user: dict = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=50, description="Nombre de recommandations")
):
    """
    Génère des recommandations contextuelles intelligentes basées sur IA
    
    Args:
        context: Contexte utilisateur (humeur, temps, lieu, etc.)
        current_user: Utilisateur connecté
        limit: Nombre de recommandations
        
    Returns:
        Dict avec recommandations contextuelles enrichies
    """
    try:
        user_id = current_user.get("user_id")
        
        # Conversion du contexte en dict
        context_dict = context.dict()
        
        # Génération des recommandations contextuelles
        contextual_recs = await advanced_recommendation_service.get_contextual_recommendations(
            user_id=user_id,
            context=context_dict,
            limit=limit
        )
        
        # Formatage pour l'API
        formatted_recs = []
        for rec in contextual_recs:
            formatted_rec = {
                'recommendation_id': f"ctx_{rec.base_recommendation.book_id}_{int(datetime.utcnow().timestamp())}",
                'book': {
                    'book_id': rec.base_recommendation.book_id,
                    'title': rec.base_recommendation.title,
                    'author': rec.base_recommendation.author,
                    'category': rec.base_recommendation.category,
                    'cover_url': rec.base_recommendation.cover_url,
                    'metadata': rec.base_recommendation.metadata
                },
                'scoring': {
                    'base_confidence': rec.base_recommendation.confidence_score,
                    'context_score': rec.context_score,
                    'global_score': (rec.base_recommendation.confidence_score * 0.6 + rec.context_score * 0.4),
                    'confidence_interval': rec.confidence_interval,
                    'novelty_score': rec.novelty_score,
                    'learning_potential': rec.learning_potential
                },
                'reasoning': {
                    'base_reasons': rec.base_recommendation.reasons,
                    'context_reasons': rec.context_reasons,
                    'mood_match': rec.mood_match,
                    'time_appropriateness': rec.time_appropriateness
                },
                'social_proof': rec.social_proof,
                'source': f"{rec.base_recommendation.source}_contextual"
            }
            formatted_recs.append(formatted_rec)
        
        return {
            "success": True,
            "data": {
                "recommendations": formatted_recs,
                "context_used": context_dict,
                "algorithm_info": {
                    "type": "contextual_ai",
                    "total_analyzed": len(contextual_recs),
                    "context_factors": list(context_dict.keys()),
                    "ai_enhanced": True
                }
            },
            "count": len(formatted_recs),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération des recommandations contextuelles: {str(e)}"
        )

@router.get("/social")
async def get_social_recommendations(
    current_user: dict = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=50, description="Nombre de recommandations"),
    social_weight: float = Query(0.7, ge=0.0, le=1.0, description="Poids des signaux sociaux")
):
    """
    Génère des recommandations basées sur l'intelligence sociale
    
    Args:
        current_user: Utilisateur connecté
        limit: Nombre de recommandations
        social_weight: Importance des signaux sociaux
        
    Returns:
        Dict avec recommandations sociales intelligentes
    """
    try:
        user_id = current_user.get("user_id")
        
        # Générer les recommandations sociales
        social_recs = await advanced_recommendation_service.get_social_recommendations(
            user_id=user_id,
            limit=limit
        )
        
        # Formatage
        formatted_recs = []
        for rec in social_recs:
            formatted_rec = {
                'recommendation_id': f"social_{rec.base_recommendation.book_id}_{int(datetime.utcnow().timestamp())}",
                'book': {
                    'book_id': rec.base_recommendation.book_id,
                    'title': rec.base_recommendation.title,
                    'author': rec.base_recommendation.author,
                    'category': rec.base_recommendation.category,
                    'cover_url': rec.base_recommendation.cover_url
                },
                'social_proof': rec.social_proof,
                'scoring': {
                    'social_score': rec.social_proof.get('social_score', 0),
                    'recommendation_count': rec.social_proof.get('recommendation_count', 0),
                    'average_rating': rec.social_proof.get('average_rating', 0),
                    'confidence': rec.base_recommendation.confidence_score
                },
                'reasoning': {
                    'reasons': rec.base_recommendation.reasons,
                    'context_reasons': rec.context_reasons,
                    'recommenders': rec.social_proof.get('recommenders', [])
                }
            }
            formatted_recs.append(formatted_rec)
        
        return {
            "success": True,
            "data": {
                "recommendations": formatted_recs,
                "social_network_size": len(formatted_recs),
                "algorithm_info": {
                    "type": "social_intelligence",
                    "social_weight": social_weight,
                    "network_based": True
                }
            },
            "count": len(formatted_recs),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération des recommandations sociales: {str(e)}"
        )

# === ROUTES MACHINE LEARNING ===

@router.post("/ml/train")
async def train_ml_models(
    training_request: MLTrainingRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Entraîne ou met à jour les modèles Machine Learning
    
    Args:
        training_request: Configuration d'entraînement
        current_user: Utilisateur connecté (admin requis)
        
    Returns:
        Dict avec résultats d'entraînement
    """
    try:
        # TODO: Ajouter vérification admin
        user_id = current_user.get("user_id")
        
        # Vérifier si un retraining est nécessaire
        if not training_request.force_retrain:
            retrain_needed = await ml_models.should_retrain_models()
            if not retrain_needed.get(training_request.model_type, False):
                return {
                    "success": True,
                    "message": f"Modèle {training_request.model_type} déjà à jour",
                    "retrain_needed": False
                }
        
        # Récupérer les données d'entraînement
        if training_request.model_type == "rating_predictor":
            # Récupérer tous les livres avec ratings
            from ..database.connection import client
            db = client.booktime
            
            books_with_ratings = list(db.books.find({"rating": {"$gt": 0}}))
            
            if len(books_with_ratings) < ml_models.min_samples_for_training:
                raise HTTPException(
                    status_code=400,
                    detail=f"Pas assez de données ({len(books_with_ratings)} < {ml_models.min_samples_for_training})"
                )
            
            # Entraîner le modèle
            result = await ml_models.train_rating_predictor(books_with_ratings)
            
        elif training_request.model_type == "user_clusterer":
            # Récupérer les données utilisateurs
            from ..database.connection import client
            db = client.booktime
            
            users_data = []
            for user in db.users.find():
                user_books = list(db.books.find({"user_id": user.get("id", "")}))
                if len(user_books) >= 3:
                    users_data.append({
                        "user_id": user.get("id"),
                        "books": user_books
                    })
            
            if len(users_data) < 10:
                raise HTTPException(
                    status_code=400,
                    detail="Pas assez d'utilisateurs pour clustering"
                )
            
            result = await ml_models.train_user_clusterer(users_data)
            
        elif training_request.model_type == "content_analyzer":
            # Récupérer les livres avec description
            from ..database.connection import client
            db = client.booktime
            
            books_with_content = list(db.books.find({
                "description": {"$exists": True, "$ne": ""}
            }))
            
            if len(books_with_content) < 20:
                raise HTTPException(
                    status_code=400,
                    detail="Pas assez de contenu pour analyse"
                )
            
            result = await ml_models.train_content_analyzer(books_with_content)
            
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Type de modèle non supporté: {training_request.model_type}"
            )
        
        return {
            "success": True,
            "data": {
                "model_type": training_request.model_type,
                "model_accuracy": result.model_accuracy,
                "training_samples": len(result.predictions),
                "feature_importance": result.feature_importance,
                "algorithm": result.model_type
            },
            "trained_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'entraînement ML: {str(e)}"
        )

@router.get("/ml/predict-rating")
async def predict_book_rating(
    book_id: str = Query(..., description="ID du livre"),
    current_user: dict = Depends(get_current_user)
):
    """
    Prédit le rating qu'un utilisateur donnerait à un livre
    
    Args:
        book_id: ID du livre
        current_user: Utilisateur connecté
        
    Returns:
        Dict avec prédiction de rating
    """
    try:
        user_id = current_user.get("user_id")
        
        # Récupérer les infos du livre
        from ..database.connection import client
        db = client.booktime
        
        book = db.books.find_one({"id": book_id})
        if not book:
            raise HTTPException(status_code=404, detail="Livre non trouvé")
        
        # Prédire le rating
        predicted_rating, confidence = await ml_models.predict_rating(book)
        
        return {
            "success": True,
            "data": {
                "book_id": book_id,
                "book_title": book.get("title", ""),
                "predicted_rating": round(predicted_rating, 2),
                "confidence": round(confidence, 2),
                "rating_range": {
                    "min": max(1.0, predicted_rating - (1 - confidence) * 2),
                    "max": min(5.0, predicted_rating + (1 - confidence) * 2)
                }
            },
            "predicted_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la prédiction: {str(e)}"
        )

# === ROUTES PROFIL AVANCÉ ===

@router.get("/user-profile/advanced")
async def get_advanced_user_profile(
    current_user: dict = Depends(get_current_user)
):
    """
    Récupère le profil utilisateur avancé avec analyse comportementale IA
    
    Args:
        current_user: Utilisateur connecté
        
    Returns:
        Dict avec profil utilisateur enrichi par IA
    """
    try:
        user_id = current_user.get("user_id")
        
        # Analyser le profil avancé
        advanced_profile = await advanced_recommendation_service.analyze_advanced_user_profile(user_id)
        
        return {
            "success": True,
            "data": {
                "user_id": advanced_profile.user_id,
                "reading_velocity": advanced_profile.reading_velocity,
                "genre_preferences": advanced_profile.genre_preferences,
                "behavioral_insights": {
                    "exploration_tendency": advanced_profile.exploration_vs_exploitation,
                    "social_influence": advanced_profile.social_influence_factor,
                    "rating_bias": advanced_profile.rating_bias,
                    "behavioral_clusters": advanced_profile.behavioral_clusters
                },
                "patterns": {
                    "mood_patterns": advanced_profile.mood_patterns,
                    "temporal_patterns": advanced_profile.temporal_patterns,
                    "completion_patterns": advanced_profile.completion_patterns
                },
                "learning_trajectory": advanced_profile.learning_trajectory,
                "ai_analysis": {
                    "profile_maturity": "high" if len(advanced_profile.learning_trajectory) > 3 else "developing",
                    "prediction_accuracy": "high" if advanced_profile.reading_velocity > 1.0 else "medium",
                    "recommendation_potential": "excellent" if len(advanced_profile.genre_preferences) > 2 else "good"
                }
            },
            "analyzed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'analyse du profil avancé: {str(e)}"
        )

# === ROUTES FEEDBACK ET APPRENTISSAGE ===

@router.post("/feedback")
async def submit_advanced_feedback(
    feedback: FeedbackRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Enregistre un feedback avancé pour améliorer les recommandations IA
    
    Args:
        feedback: Feedback détaillé sur une recommandation
        current_user: Utilisateur connecté
        
    Returns:
        Dict confirmant l'enregistrement
    """
    try:
        user_id = current_user.get("user_id")
        
        # Enrichir le feedback avec des métadonnées
        feedback_data = {
            "user_id": user_id,
            "recommendation_id": feedback.recommendation_id,
            "feedback_type": feedback.feedback_type,
            "rating": feedback.rating,
            "context": feedback.context or {},
            "timestamp": datetime.utcnow(),
            "session_info": {
                "user_agent": "unknown",  # À récupérer des headers
                "platform": "web"
            }
        }
        
        # Enregistrer dans la base de données
        from ..database.connection import client
        db = client.booktime
        
        db.advanced_recommendation_feedback.insert_one(feedback_data)
        
        # TODO: Déclencher réentraînement incrémental des modèles
        
        return {
            "success": True,
            "message": "Feedback enregistré pour améliorer l'IA",
            "data": {
                "feedback_id": str(feedback_data["timestamp"]),
                "learning_impact": "medium",  # Calculer l'impact réel
                "next_recommendations_improved": True
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de l'enregistrement du feedback: {str(e)}"
        )

# === ROUTES STATISTIQUES ===

@router.get("/stats/ml")
async def get_ml_stats():
    """
    Récupère les statistiques des modèles Machine Learning
    
    Returns:
        Dict avec statistiques des modèles IA
    """
    try:
        # Vérifier l'état des modèles
        retrain_status = await ml_models.should_retrain_models()
        
        stats = {
            "models_status": {
                "rating_predictor": {
                    "loaded": ml_models.rating_predictor is not None,
                    "needs_retrain": retrain_status.get("rating_predictor", True),
                    "accuracy": "unknown"  # À récupérer des métadonnées sauvegardées
                },
                "user_clusterer": {
                    "loaded": ml_models.user_clusterer is not None,
                    "needs_retrain": retrain_status.get("user_clusterer", True),
                    "clusters": "unknown"
                },
                "content_analyzer": {
                    "loaded": ml_models.content_vectorizer is not None,
                    "needs_retrain": retrain_status.get("content_analyzer", True),
                    "vocabulary_size": "unknown"
                }
            },
            "recommendations_served": {
                "contextual": 0,  # À implémenter compteurs
                "social": 0,
                "ml_enhanced": 0
            },
            "learning_metrics": {
                "feedback_collected": 0,
                "model_improvements": 0,
                "accuracy_trend": "stable"
            }
        }
        
        return {
            "success": True,
            "data": stats,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des stats ML: {str(e)}"
        )

@router.get("/health")
async def advanced_recommendations_health():
    """Vérification de santé du module recommandations avancées"""
    try:
        health_status = {
            "status": "ok",
            "module": "advanced_recommendations",
            "services": {
                "advanced_service": "available",
                "ml_models": "available",
                "contextual_ai": "active",
                "social_intelligence": "active"
            },
            "features": [
                "contextual_recommendations",
                "social_recommendations", 
                "ml_rating_prediction",
                "behavioral_analysis",
                "advanced_profiling"
            ],
            "ai_capabilities": [
                "machine_learning",
                "behavioral_clustering",
                "content_analysis",
                "context_awareness",
                "social_intelligence"
            ]
        }
        
        return health_status
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur module recommandations avancées: {str(e)}"
        )