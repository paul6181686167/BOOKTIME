"""
PHASE 3.3 - Modèles de Données Sociales
Modèles pour fonctionnalités sociales et communautaires
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class PrivacyLevel(str, Enum):
    PUBLIC = "public"
    FRIENDS = "friends"
    PRIVATE = "private"


class ActivityType(str, Enum):
    BOOK_ADDED = "book_added"
    BOOK_COMPLETED = "book_completed"
    BOOK_RATED = "book_rated"
    BOOK_REVIEWED = "book_reviewed"
    LIST_CREATED = "list_created"
    LIST_SHARED = "list_shared"
    USER_FOLLOWED = "user_followed"
    RECOMMENDATION_MADE = "recommendation_made"


class NotificationType(str, Enum):
    NEW_FOLLOWER = "new_follower"
    BOOK_RECOMMENDED = "book_recommended"
    COMMENT_RECEIVED = "comment_received"
    LIST_SHARED = "list_shared"
    FRIEND_ACTIVITY = "friend_activity"


# Modèles de base
class UserProfile(BaseModel):
    """Profil utilisateur public/social"""
    user_id: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    privacy_level: PrivacyLevel = PrivacyLevel.PUBLIC
    show_reading_stats: bool = True
    show_current_reading: bool = True
    show_wishlist: bool = True
    followers_count: int = 0
    following_count: int = 0
    books_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Follow(BaseModel):
    """Relation de suivi entre utilisateurs"""
    id: str
    follower_id: str  # Utilisateur qui suit
    following_id: str  # Utilisateur suivi
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SocialActivity(BaseModel):
    """Activité sociale dans le feed"""
    id: str
    user_id: str
    activity_type: ActivityType
    content: Dict[str, Any]  # Contenu flexible selon le type d'activité
    privacy_level: PrivacyLevel = PrivacyLevel.PUBLIC
    likes_count: int = 0
    comments_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SocialComment(BaseModel):
    """Commentaire sur une activité ou un livre"""
    id: str
    user_id: str
    target_type: str  # "activity", "book", "list"
    target_id: str
    content: str
    parent_comment_id: Optional[str] = None  # Pour les réponses
    likes_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SocialLike(BaseModel):
    """Like sur une activité ou commentaire"""
    id: str
    user_id: str
    target_type: str  # "activity", "comment", "book"
    target_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BookList(BaseModel):
    """Liste de livres partageable"""
    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    privacy_level: PrivacyLevel = PrivacyLevel.PUBLIC
    is_collaborative: bool = False
    book_ids: List[str] = []
    collaborator_ids: List[str] = []  # Utilisateurs autorisés à modifier
    followers_count: int = 0
    likes_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class BookRecommendation(BaseModel):
    """Recommandation de livre entre utilisateurs"""
    id: str
    from_user_id: str
    to_user_id: str
    book_id: str
    message: Optional[str] = None
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class SocialNotification(BaseModel):
    """Notification sociale"""
    id: str
    user_id: str
    type: NotificationType
    title: str
    message: str
    data: Dict[str, Any] = {}  # Données contextuelles
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Modèles pour les requêtes API
class CreateProfileRequest(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    privacy_level: PrivacyLevel = PrivacyLevel.PUBLIC
    show_reading_stats: bool = True
    show_current_reading: bool = True
    show_wishlist: bool = True


class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    privacy_level: Optional[PrivacyLevel] = None
    show_reading_stats: Optional[bool] = None
    show_current_reading: Optional[bool] = None
    show_wishlist: Optional[bool] = None


class CreateActivityRequest(BaseModel):
    activity_type: ActivityType
    content: Dict[str, Any]
    privacy_level: PrivacyLevel = PrivacyLevel.PUBLIC


class CreateCommentRequest(BaseModel):
    content: str
    parent_comment_id: Optional[str] = None


class CreateListRequest(BaseModel):
    title: str
    description: Optional[str] = None
    privacy_level: PrivacyLevel = PrivacyLevel.PUBLIC
    is_collaborative: bool = False
    book_ids: List[str] = []


class UpdateListRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    privacy_level: Optional[PrivacyLevel] = None
    is_collaborative: Optional[bool] = None
    book_ids: Optional[List[str]] = None


class CreateRecommendationRequest(BaseModel):
    to_user_id: str
    book_id: str
    message: Optional[str] = None


# Modèles pour les réponses API
class ProfileResponse(BaseModel):
    user_id: str
    display_name: Optional[str]
    bio: Optional[str]
    avatar_url: Optional[str]
    location: Optional[str]
    website: Optional[str]
    followers_count: int
    following_count: int
    books_count: int
    is_following: bool = False  # Si l'utilisateur connecté suit ce profil
    can_follow: bool = True  # Si l'utilisateur connecté peut suivre ce profil
    reading_stats: Optional[Dict[str, Any]] = None
    current_reading: Optional[List[Dict[str, Any]]] = None
    recent_books: Optional[List[Dict[str, Any]]] = None
    created_at: datetime


class ActivityResponse(BaseModel):
    id: str
    user: Dict[str, Any]  # Infos utilisateur (nom, avatar)
    activity_type: ActivityType
    content: Dict[str, Any]
    privacy_level: PrivacyLevel
    likes_count: int
    comments_count: int
    is_liked: bool = False  # Si l'utilisateur connecté a liké
    can_comment: bool = True
    created_at: datetime


class FeedResponse(BaseModel):
    activities: List[ActivityResponse]
    total_count: int
    has_more: bool
    next_cursor: Optional[str] = None


class CommentResponse(BaseModel):
    id: str
    user: Dict[str, Any]  # Infos utilisateur
    content: str
    parent_comment_id: Optional[str]
    replies: List["CommentResponse"] = []
    likes_count: int
    is_liked: bool = False
    can_edit: bool = False
    can_delete: bool = False
    created_at: datetime
    updated_at: Optional[datetime]


class NotificationResponse(BaseModel):
    id: str
    type: NotificationType
    title: str
    message: str
    data: Dict[str, Any]
    is_read: bool
    created_at: datetime


# Permettre les références circulaires
CommentResponse.model_rebuild()