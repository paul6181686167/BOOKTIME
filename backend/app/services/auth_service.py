# Service d'authentification pour BOOKTIME
import uuid
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from ..database import users_collection
from ..models.user import UserAuth, UserCreate, UserResponse, LoginResponse
from ..dependencies import create_access_token
from ..config import ACCESS_TOKEN_EXPIRE_MINUTES

class AuthService:
    
    @staticmethod
    def register_user(user_data: UserCreate) -> LoginResponse:
        """Enregistre un nouvel utilisateur"""
        # Vérifier si l'utilisateur existe déjà
        existing_user = users_collection.find_one({
            "first_name": user_data.first_name,
            "last_name": user_data.last_name
        })
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists"
            )
        
        # Créer le nouvel utilisateur
        user_id = str(uuid.uuid4())
        user_doc = {
            "id": user_id,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "date_created": datetime.now()
        }
        
        try:
            users_collection.insert_one(user_doc)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        # Créer le token d'accès
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_id}, 
            expires_delta=access_token_expires
        )
        
        user_response = UserResponse(**user_doc)
        return LoginResponse(
            access_token=access_token,
            user=user_response
        )
    
    @staticmethod
    def login_user(user_data: UserAuth) -> LoginResponse:
        """Connecte un utilisateur existant"""
        # Trouver l'utilisateur
        user = users_collection.find_one({
            "first_name": user_data.first_name,
            "last_name": user_data.last_name
        })
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )
        
        # Créer le token d'accès
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["id"]}, 
            expires_delta=access_token_expires
        )
        
        user_response = UserResponse(**user)
        return LoginResponse(
            access_token=access_token,
            user=user_response
        )
    
    @staticmethod
    def get_user_by_id(user_id: str) -> UserResponse:
        """Récupère un utilisateur par son ID"""
        user = users_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return UserResponse(**user)
    
    @staticmethod
    def update_user(user_id: str, update_data: dict) -> UserResponse:
        """Met à jour un utilisateur"""
        # Supprimer les champs vides
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields to update"
            )
        
        # Vérifier si l'utilisateur existe
        user = users_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Mettre à jour l'utilisateur
        try:
            users_collection.update_one(
                {"id": user_id},
                {"$set": update_data}
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update user"
            )
        
        # Récupérer l'utilisateur mis à jour
        updated_user = users_collection.find_one({"id": user_id})
        return UserResponse(**updated_user)
    
    @staticmethod
    def delete_user(user_id: str) -> dict:
        """Supprime un utilisateur"""
        # Vérifier si l'utilisateur existe
        user = users_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Supprimer l'utilisateur
        try:
            result = users_collection.delete_one({"id": user_id})
            if result.deleted_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user"
            )
        
        return {"message": "User deleted successfully"}
    
    @staticmethod
    def validate_user_exists(user_id: str) -> bool:
        """Vérifie si un utilisateur existe"""
        user = users_collection.find_one({"id": user_id})
        return user is not None

# Instance du service
auth_service = AuthService()