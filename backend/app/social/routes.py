"""
PHASE 3.3 - Routes API Fonctionnalités Sociales
Endpoints pour toutes les fonctionnalités sociales et communautaires
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from datetime import datetime

from ..security.jwt import get_current_user
from .service import social_service
from .models import (
    CreateProfileRequest, UpdateProfileRequest, CreateActivityRequest,
    CreateCommentRequest, CreateListRequest, UpdateListRequest,
    CreateRecommendationRequest, ActivityType, PrivacyLevel
)

router = APIRouter(prefix="/api/social", tags=["social"])


# === ROUTES PROFILS ===

@router.post("/profile")
async def create_profile(
    profile_data: CreateProfileRequest,
    current_user: dict = Depends(get_current_user)
):
    """Crée ou met à jour le profil social de l'utilisateur"""
    try:
        user_id = current_user.get("id")
        
        # Créer ou récupérer le profil
        profile = await social_service.create_or_get_profile(
            user_id=user_id,
            display_name=profile_data.display_name
        )
        
        # Mettre à jour avec les nouvelles données
        if any([profile_data.bio, profile_data.location, profile_data.website]):
            updates = {}
            if profile_data.bio is not None:
                updates["bio"] = profile_data.bio
            if profile_data.location is not None:
                updates["location"] = profile_data.location
            if profile_data.website is not None:
                updates["website"] = profile_data.website
            if profile_data.privacy_level is not None:
                updates["privacy_level"] = profile_data.privacy_level
            if profile_data.show_reading_stats is not None:
                updates["show_reading_stats"] = profile_data.show_reading_stats
            if profile_data.show_current_reading is not None:
                updates["show_current_reading"] = profile_data.show_current_reading
            if profile_data.show_wishlist is not None:
                updates["show_wishlist"] = profile_data.show_wishlist
            
            if updates:
                profile = await social_service.update_profile(user_id, updates)
        
        return {"success": True, "profile": profile.dict()}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profile/{user_id}")
async def get_profile(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupère le profil public d'un utilisateur"""
    try:
        viewer_id = current_user.get("id")
        profile = await social_service.get_profile_with_stats(user_id, viewer_id)
        
        return profile.dict()
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/profile")
async def update_profile(
    profile_updates: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user)
):
    """Met à jour le profil de l'utilisateur connecté"""
    try:
        user_id = current_user.get("id")
        
        # Préparer les mises à jour
        updates = {}
        for field, value in profile_updates.dict(exclude_unset=True).items():
            if value is not None:
                updates[field] = value
        
        if not updates:
            raise HTTPException(status_code=400, detail="Aucune donnée à mettre à jour")
        
        profile = await social_service.update_profile(user_id, updates)
        
        return {"success": True, "profile": profile.dict()}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === ROUTES FOLLOWS ===

@router.post("/follow/{user_id}")
async def follow_user(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Suivre un utilisateur"""
    try:
        follower_id = current_user.get("id")
        result = await social_service.follow_user(follower_id, user_id)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/follow/{user_id}")
async def unfollow_user(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Arrêter de suivre un utilisateur"""
    try:
        follower_id = current_user.get("id")
        result = await social_service.unfollow_user(follower_id, user_id)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/followers/{user_id}")
async def get_followers(
    user_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """Récupère la liste des followers d'un utilisateur"""
    try:
        followers = await social_service.get_followers(user_id, limit, offset)
        
        return {
            "followers": followers,
            "total_count": len(followers),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/following/{user_id}")
async def get_following(
    user_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """Récupère la liste des utilisateurs suivis"""
    try:
        following = await social_service.get_following(user_id, limit, offset)
        
        return {
            "following": following,
            "total_count": len(following),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === ROUTES ACTIVITÉS ===

@router.post("/activity")
async def create_activity(
    activity_data: CreateActivityRequest,
    current_user: dict = Depends(get_current_user)
):
    """Crée une nouvelle activité sociale"""
    try:
        user_id = current_user.get("id")
        
        activity = await social_service.create_activity(
            user_id=user_id,
            activity_type=activity_data.activity_type,
            content=activity_data.content,
            privacy_level=activity_data.privacy_level
        )
        
        return {"success": True, "activity": activity.dict()}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feed")
async def get_feed(
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """Récupère le feed social de l'utilisateur"""
    try:
        user_id = current_user.get("id")
        feed = await social_service.get_user_feed(user_id, limit, offset)
        
        return feed.dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activity/{activity_id}")
async def get_activity(
    activity_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Récupère une activité spécifique"""
    try:
        # TODO: Implémenter la récupération d'activité individuelle
        return {"message": "Fonctionnalité à implémenter"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === ROUTES NOTIFICATIONS ===

@router.get("/notifications")
async def get_notifications(
    limit: int = Query(20, ge=1, le=50),
    unread_only: bool = Query(False),
    current_user: dict = Depends(get_current_user)
):
    """Récupère les notifications de l'utilisateur"""
    try:
        user_id = current_user.get("id")
        notifications = await social_service.get_user_notifications(user_id, limit, unread_only)
        
        return {
            "notifications": [notif.dict() for notif in notifications],
            "total_count": len(notifications),
            "unread_only": unread_only
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Marque une notification comme lue"""
    try:
        user_id = current_user.get("id")
        result = await social_service.mark_notification_read(user_id, notification_id)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/notifications/read-all")
async def mark_all_notifications_read(
    current_user: dict = Depends(get_current_user)
):
    """Marque toutes les notifications comme lues"""
    try:
        # TODO: Implémenter le marquage en masse
        return {"success": True, "message": "Toutes les notifications marquées comme lues"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === ROUTES RECHERCHE SOCIALE ===

@router.get("/search/users")
async def search_users(
    q: str = Query(..., min_length=2, description="Terme de recherche"),
    limit: int = Query(20, ge=1, le=50),
    current_user: dict = Depends(get_current_user)
):
    """Recherche d'utilisateurs"""
    try:
        # TODO: Implémenter la recherche d'utilisateurs
        return {
            "users": [],
            "total_count": 0,
            "query": q,
            "message": "Recherche d'utilisateurs à implémenter"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === ROUTES STATISTIQUES SOCIALES ===

@router.get("/stats")
async def get_social_stats(
    current_user: dict = Depends(get_current_user)
):
    """Récupère les statistiques sociales de l'utilisateur"""
    try:
        user_id = current_user.get("id")
        
        # TODO: Implémenter les statistiques sociales complètes
        stats = {
            "followers_count": 0,
            "following_count": 0,
            "activities_count": 0,
            "likes_received": 0,
            "comments_received": 0,
            "recommendations_sent": 0,
            "recommendations_received": 0
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === ROUTES D'ADMINISTRATION ===

@router.get("/admin/users")
async def get_all_users(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user)
):
    """Récupère la liste de tous les utilisateurs (admin)"""
    try:
        # TODO: Ajouter vérification admin
        # TODO: Implémenter liste des utilisateurs
        return {
            "users": [],
            "message": "Fonctionnalité admin à implémenter"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === ROUTES UTILITAIRES ===

@router.get("/health")
async def social_health_check():
    """Vérification de santé du module social"""
    try:
        # Test de connexion à la base
        await social_service._ensure_indexes()
        
        return {
            "status": "ok",
            "module": "social",
            "features": [
                "profiles",
                "follows", 
                "activities",
                "notifications",
                "feed"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur module social: {str(e)}")