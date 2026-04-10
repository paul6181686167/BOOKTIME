"""
PHASE 3.3 - Service Fonctionnalités Sociales
Service principal pour la gestion des interactions sociales
"""
import uuid
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass

from ..database.connection import client
from .models import (
    UserProfile, Follow, SocialActivity, SocialComment, SocialLike,
    BookList, BookRecommendation, SocialNotification,
    ActivityType, NotificationType, PrivacyLevel,
    ProfileResponse, ActivityResponse, FeedResponse, CommentResponse, NotificationResponse
)

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SocialService:
    """Service principal pour les fonctionnalités sociales"""
    
    def __init__(self):
        self.db = client.booktime
        self.profiles_collection = self.db.user_profiles
        self.follows_collection = self.db.follows
        self.activities_collection = self.db.social_activities
        self.comments_collection = self.db.social_comments
        self.likes_collection = self.db.social_likes
        self.lists_collection = self.db.book_lists
        self.recommendations_collection = self.db.book_recommendations
        self.notifications_collection = self.db.social_notifications
        
        # Index pour performance
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Crée les index MongoDB pour optimiser les performances"""
        try:
            # Index pour les profils
            self.profiles_collection.create_index("user_id", unique=True)
            
            # Index pour les follows
            self.follows_collection.create_index([("follower_id", 1), ("following_id", 1)], unique=True)
            self.follows_collection.create_index("follower_id")
            self.follows_collection.create_index("following_id")
            
            # Index pour les activités
            self.activities_collection.create_index([("user_id", 1), ("created_at", -1)])
            self.activities_collection.create_index("created_at")
            self.activities_collection.create_index("activity_type")
            
            # Index pour les commentaires
            self.comments_collection.create_index([("target_type", 1), ("target_id", 1)])
            self.comments_collection.create_index("user_id")
            
            # Index pour les likes
            self.likes_collection.create_index([("user_id", 1), ("target_type", 1), ("target_id", 1)], unique=True)
            
            # Index pour les notifications
            self.notifications_collection.create_index([("user_id", 1), ("created_at", -1)])
            self.notifications_collection.create_index([("user_id", 1), ("is_read", 1)])
            
            logger.info("Index sociaux créés avec succès")
            return True
        except Exception as e:
            logger.warning(f"Erreur lors de la création des index: {str(e)}")
            return False
    
    # === GESTION DES PROFILS ===
    
    async def create_or_get_profile(self, user_id: str, display_name: str = None) -> UserProfile:
        """Crée ou récupère le profil utilisateur"""
        try:
            # Vérifier si le profil existe déjà
            existing_profile = self.profiles_collection.find_one({"user_id": user_id})
            
            if existing_profile:
                existing_profile['_id'] = str(existing_profile['_id'])
                return UserProfile(**existing_profile)
            
            # Créer un nouveau profil
            profile_data = {
                "user_id": user_id,
                "display_name": display_name,
                "bio": None,
                "avatar_url": None,
                "location": None,
                "website": None,
                "privacy_level": PrivacyLevel.PUBLIC,
                "show_reading_stats": True,
                "show_current_reading": True,
                "show_wishlist": True,
                "followers_count": 0,
                "following_count": 0,
                "books_count": 0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = self.profiles_collection.insert_one(profile_data)
            profile_data['_id'] = str(result.inserted_id)
            
            return UserProfile(**profile_data)
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du profil: {str(e)}")
            raise Exception(f"Erreur lors de la création du profil: {str(e)}")
    
    async def update_profile(self, user_id: str, updates: Dict[str, Any]) -> UserProfile:
        """Met à jour le profil utilisateur"""
        try:
            updates["updated_at"] = datetime.utcnow()
            
            result = self.profiles_collection.update_one(
                {"user_id": user_id},
                {"$set": updates}
            )
            
            if result.matched_count == 0:
                raise Exception("Profil non trouvé")
            
            updated_profile = self.profiles_collection.find_one({"user_id": user_id})
            updated_profile['_id'] = str(updated_profile['_id'])
            
            return UserProfile(**updated_profile)
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du profil: {str(e)}")
            raise Exception(f"Erreur lors de la mise à jour du profil: {str(e)}")
    
    async def get_profile_with_stats(self, user_id: str, viewer_id: str = None) -> ProfileResponse:
        """Récupère le profil avec statistiques et état de suivi"""
        try:
            # Récupérer le profil
            profile_data = self.profiles_collection.find_one({"user_id": user_id})
            
            if not profile_data:
                raise Exception("Profil non trouvé")
            
            # Calculer les statistiques de livres
            books_count = self.db.books.count_documents({"user_id": user_id})
            
            # Vérifier si le viewer suit ce profil
            is_following = False
            can_follow = True
            
            if viewer_id and viewer_id != user_id:
                follow_exists = self.follows_collection.find_one({
                    "follower_id": viewer_id,
                    "following_id": user_id
                })
                is_following = follow_exists is not None
            elif viewer_id == user_id:
                can_follow = False  # On ne peut pas se suivre soi-même
            
            # Statistiques de lecture (si autorisées)
            reading_stats = None
            current_reading = None
            recent_books = None
            
            if profile_data.get("show_reading_stats", True):
                stats = await self._get_user_reading_stats(user_id)
                reading_stats = stats
            
            if profile_data.get("show_current_reading", True):
                current_books = list(self.db.books.find({
                    "user_id": user_id,
                    "status": "reading"
                }).limit(3))
                
                current_reading = [{
                    "id": book.get("id"),
                    "title": book.get("title"),
                    "author": book.get("author"),
                    "cover_url": book.get("cover_url"),
                    "progress": (book.get("current_page", 0) / book.get("total_pages", 1)) * 100 if book.get("total_pages", 0) > 0 else 0
                } for book in current_books]
            
            # Livres récents
            recent_books_raw = list(self.db.books.find({
                "user_id": user_id,
                "status": "completed"
            }).sort("date_completed", -1).limit(6))
            
            recent_books = [{
                "id": book.get("id"),
                "title": book.get("title"),
                "author": book.get("author"),
                "cover_url": book.get("cover_url"),
                "rating": book.get("rating"),
                "date_completed": book.get("date_completed")
            } for book in recent_books_raw]
            
            return ProfileResponse(
                user_id=profile_data["user_id"],
                display_name=profile_data.get("display_name"),
                bio=profile_data.get("bio"),
                avatar_url=profile_data.get("avatar_url"),
                location=profile_data.get("location"),
                website=profile_data.get("website"),
                followers_count=profile_data.get("followers_count", 0),
                following_count=profile_data.get("following_count", 0),
                books_count=books_count,
                is_following=is_following,
                can_follow=can_follow,
                reading_stats=reading_stats,
                current_reading=current_reading,
                recent_books=recent_books,
                created_at=profile_data["created_at"]
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du profil: {str(e)}")
            raise Exception(f"Erreur lors de la récupération du profil: {str(e)}")
    
    async def _get_user_reading_stats(self, user_id: str) -> Dict[str, Any]:
        """Calcule les statistiques de lecture d'un utilisateur"""
        try:
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {
                    "_id": None,
                    "total_books": {"$sum": 1},
                    "completed_books": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}},
                    "reading_books": {"$sum": {"$cond": [{"$eq": ["$status", "reading"]}, 1, 0]}},
                    "to_read_books": {"$sum": {"$cond": [{"$eq": ["$status", "to_read"]}, 1, 0]}},
                    "total_pages": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, "$total_pages", 0]}},
                    "avg_rating": {"$avg": {"$cond": [{"$gt": ["$rating", 0]}, "$rating", None]}},
                    "books_by_category": {"$push": "$category"}
                }}
            ]
            
            result = list(self.db.books.aggregate(pipeline))
            
            if not result:
                return {
                    "total_books": 0,
                    "completed_books": 0,
                    "reading_books": 0,
                    "to_read_books": 0,
                    "total_pages": 0,
                    "avg_rating": 0,
                    "categories": {}
                }
            
            stats = result[0]
            
            # Compter les livres par catégorie
            categories = {}
            for category in stats.get("books_by_category", []):
                categories[category] = categories.get(category, 0) + 1
            
            return {
                "total_books": stats.get("total_books", 0),
                "completed_books": stats.get("completed_books", 0),
                "reading_books": stats.get("reading_books", 0),
                "to_read_books": stats.get("to_read_books", 0),
                "total_pages": stats.get("total_pages", 0),
                "avg_rating": round(stats.get("avg_rating", 0), 1) if stats.get("avg_rating") else 0,
                "categories": categories
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques: {str(e)}")
            return {}
    
    # === GESTION DES FOLLOWS ===
    
    async def follow_user(self, follower_id: str, following_id: str) -> Dict[str, Any]:
        """Un utilisateur suit un autre utilisateur"""
        try:
            if follower_id == following_id:
                raise Exception("Impossible de se suivre soi-même")
            
            # Vérifier si le follow existe déjà
            existing_follow = self.follows_collection.find_one({
                "follower_id": follower_id,
                "following_id": following_id
            })
            
            if existing_follow:
                raise Exception("Vous suivez déjà cet utilisateur")
            
            # Créer le follow
            follow_data = {
                "id": str(uuid.uuid4()),
                "follower_id": follower_id,
                "following_id": following_id,
                "created_at": datetime.utcnow()
            }
            
            self.follows_collection.insert_one(follow_data)
            
            # Mettre à jour les compteurs
            await self._update_follow_counts(follower_id, following_id)
            
            # Créer une notification
            await self._create_notification(
                user_id=following_id,
                type=NotificationType.NEW_FOLLOWER,
                title="Nouveau follower",
                message="Quelqu'un vous suit maintenant",
                data={"follower_id": follower_id}
            )
            
            # Créer une activité
            await self.create_activity(
                user_id=follower_id,
                activity_type=ActivityType.USER_FOLLOWED,
                content={
                    "followed_user_id": following_id
                },
                privacy_level=PrivacyLevel.PUBLIC
            )
            
            return {"success": True, "message": "Utilisateur suivi avec succès"}
            
        except Exception as e:
            logger.error(f"Erreur lors du follow: {str(e)}")
            raise Exception(f"Erreur lors du follow: {str(e)}")
    
    async def unfollow_user(self, follower_id: str, following_id: str) -> Dict[str, Any]:
        """Un utilisateur arrête de suivre un autre utilisateur"""
        try:
            result = self.follows_collection.delete_one({
                "follower_id": follower_id,
                "following_id": following_id
            })
            
            if result.deleted_count == 0:
                raise Exception("Follow introuvable")
            
            # Mettre à jour les compteurs
            await self._update_follow_counts(follower_id, following_id)
            
            return {"success": True, "message": "Utilisateur non suivi"}
            
        except Exception as e:
            logger.error(f"Erreur lors de l'unfollow: {str(e)}")
            raise Exception(f"Erreur lors de l'unfollow: {str(e)}")
    
    async def _update_follow_counts(self, follower_id: str, following_id: str):
        """Met à jour les compteurs de followers/following"""
        try:
            # Compter les followers de following_id
            followers_count = self.follows_collection.count_documents({"following_id": following_id})
            self.profiles_collection.update_one(
                {"user_id": following_id},
                {"$set": {"followers_count": followers_count}}
            )
            
            # Compter les following de follower_id
            following_count = self.follows_collection.count_documents({"follower_id": follower_id})
            self.profiles_collection.update_one(
                {"user_id": follower_id},
                {"$set": {"following_count": following_count}}
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des compteurs: {str(e)}")
    
    async def get_followers(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Récupère la liste des followers d'un utilisateur"""
        try:
            pipeline = [
                {"$match": {"following_id": user_id}},
                {"$lookup": {
                    "from": "user_profiles",
                    "localField": "follower_id",
                    "foreignField": "user_id",
                    "as": "profile"
                }},
                {"$unwind": "$profile"},
                {"$sort": {"created_at": -1}},
                {"$skip": offset},
                {"$limit": limit},
                {"$project": {
                    "user_id": "$follower_id",
                    "display_name": "$profile.display_name",
                    "avatar_url": "$profile.avatar_url",
                    "followers_count": "$profile.followers_count",
                    "books_count": "$profile.books_count",
                    "followed_at": "$created_at"
                }}
            ]
            
            return list(self.follows_collection.aggregate(pipeline))
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des followers: {str(e)}")
            return []
    
    async def get_following(self, user_id: str, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Récupère la liste des utilisateurs suivis"""
        try:
            pipeline = [
                {"$match": {"follower_id": user_id}},
                {"$lookup": {
                    "from": "user_profiles",
                    "localField": "following_id",
                    "foreignField": "user_id",
                    "as": "profile"
                }},
                {"$unwind": "$profile"},
                {"$sort": {"created_at": -1}},
                {"$skip": offset},
                {"$limit": limit},
                {"$project": {
                    "user_id": "$following_id",
                    "display_name": "$profile.display_name",
                    "avatar_url": "$profile.avatar_url",
                    "followers_count": "$profile.followers_count",
                    "books_count": "$profile.books_count",
                    "followed_at": "$created_at"
                }}
            ]
            
            return list(self.follows_collection.aggregate(pipeline))
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des following: {str(e)}")
            return []
    
    # === GESTION DES ACTIVITÉS ===
    
    async def create_activity(self, user_id: str, activity_type: ActivityType, 
                            content: Dict[str, Any], privacy_level: PrivacyLevel = PrivacyLevel.PUBLIC) -> SocialActivity:
        """Crée une nouvelle activité sociale"""
        try:
            activity_data = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "activity_type": activity_type,
                "content": content,
                "privacy_level": privacy_level,
                "likes_count": 0,
                "comments_count": 0,
                "created_at": datetime.utcnow()
            }
            
            self.activities_collection.insert_one(activity_data)
            activity_data['_id'] = str(activity_data['_id']) if '_id' in activity_data else None
            
            return SocialActivity(**activity_data)
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de l'activité: {str(e)}")
            raise Exception(f"Erreur lors de la création de l'activité: {str(e)}")
    
    async def get_user_feed(self, user_id: str, limit: int = 20, offset: int = 0) -> FeedResponse:
        """Récupère le feed social d'un utilisateur"""
        try:
            # Récupérer les utilisateurs suivis
            following_users = [doc["following_id"] for doc in self.follows_collection.find({"follower_id": user_id})]
            following_users.append(user_id)  # Inclure ses propres activités
            
            # Récupérer les activités
            activities_cursor = self.activities_collection.find({
                "user_id": {"$in": following_users},
                "privacy_level": {"$in": [PrivacyLevel.PUBLIC, PrivacyLevel.FRIENDS]}
            }).sort("created_at", -1).skip(offset).limit(limit)
            
            activities = []
            for activity in activities_cursor:
                # Récupérer les infos utilisateur
                user_profile = self.profiles_collection.find_one({"user_id": activity["user_id"]})
                user_info = {
                    "user_id": activity["user_id"],
                    "display_name": user_profile.get("display_name") if user_profile else "Utilisateur",
                    "avatar_url": user_profile.get("avatar_url") if user_profile else None
                }
                
                # Vérifier si l'utilisateur a liké cette activité
                is_liked = self.likes_collection.find_one({
                    "user_id": user_id,
                    "target_type": "activity",
                    "target_id": activity["id"]
                }) is not None
                
                activities.append(ActivityResponse(
                    id=activity["id"],
                    user=user_info,
                    activity_type=activity["activity_type"],
                    content=activity["content"],
                    privacy_level=activity["privacy_level"],
                    likes_count=activity.get("likes_count", 0),
                    comments_count=activity.get("comments_count", 0),
                    is_liked=is_liked,
                    can_comment=True,
                    created_at=activity["created_at"]
                ))
            
            # Compter le total
            total_count = self.activities_collection.count_documents({
                "user_id": {"$in": following_users},
                "privacy_level": {"$in": [PrivacyLevel.PUBLIC, PrivacyLevel.FRIENDS]}
            })
            
            has_more = (offset + limit) < total_count
            
            return FeedResponse(
                activities=activities,
                total_count=total_count,
                has_more=has_more,
                next_cursor=str(offset + limit) if has_more else None
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du feed: {str(e)}")
            raise Exception(f"Erreur lors de la récupération du feed: {str(e)}")
    
    # === NOTIFICATIONS ===
    
    async def _create_notification(self, user_id: str, type: NotificationType, 
                                 title: str, message: str, data: Dict[str, Any] = None) -> SocialNotification:
        """Crée une notification"""
        try:
            notification_data = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "type": type,
                "title": title,
                "message": message,
                "data": data or {},
                "is_read": False,
                "created_at": datetime.utcnow()
            }
            
            self.notifications_collection.insert_one(notification_data)
            notification_data['_id'] = str(notification_data['_id']) if '_id' in notification_data else None
            
            return SocialNotification(**notification_data)
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de la notification: {str(e)}")
            raise Exception(f"Erreur lors de la création de la notification: {str(e)}")
    
    async def get_user_notifications(self, user_id: str, limit: int = 20, unread_only: bool = False) -> List[NotificationResponse]:
        """Récupère les notifications d'un utilisateur"""
        try:
            query = {"user_id": user_id}
            if unread_only:
                query["is_read"] = False
            
            notifications_cursor = self.notifications_collection.find(query).sort("created_at", -1).limit(limit)
            
            notifications = []
            for notif in notifications_cursor:
                notifications.append(NotificationResponse(
                    id=notif["id"],
                    type=notif["type"],
                    title=notif["title"],
                    message=notif["message"],
                    data=notif["data"],
                    is_read=notif["is_read"],
                    created_at=notif["created_at"]
                ))
            
            return notifications
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des notifications: {str(e)}")
            return []
    
    async def mark_notification_read(self, user_id: str, notification_id: str) -> Dict[str, Any]:
        """Marque une notification comme lue"""
        try:
            result = self.notifications_collection.update_one(
                {"id": notification_id, "user_id": user_id},
                {"$set": {"is_read": True}}
            )
            
            if result.modified_count == 0:
                raise Exception("Notification non trouvée")
            
            return {"success": True, "message": "Notification marquée comme lue"}
            
        except Exception as e:
            logger.error(f"Erreur lors du marquage de la notification: {str(e)}")
            raise Exception(f"Erreur lors du marquage de la notification: {str(e)}")


# Instance globale du service
social_service = SocialService()