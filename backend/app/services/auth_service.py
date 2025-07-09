from fastapi import HTTPException, status
from datetime import datetime, timedelta
from ..database import users_collection
from ..utils.security import create_access_token, generate_user_id
from ..models.common import UserAuth
from ..config import ACCESS_TOKEN_EXPIRE_MINUTES

class AuthService:
    
    @staticmethod
    def register_user(user_data: UserAuth):
        """Enregistrer un nouvel utilisateur"""
        # Vérifier si l'utilisateur existe déjà
        existing_user = users_collection.find_one({
            "first_name": user_data.first_name,
            "last_name": user_data.last_name
        })
        
        if existing_user:
            # Utilisateur existant, connecter
            user_id = existing_user["id"]
        else:
            # Nouvel utilisateur, créer
            user_id = generate_user_id()
            user_doc = {
                "id": user_id,
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
                "created_at": datetime.utcnow()
            }
            users_collection.insert_one(user_doc)
        
        # Créer le token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_id}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "first_name": user_data.first_name,
                "last_name": user_data.last_name
            }
        }
    
    @staticmethod
    def login_user(user_data: UserAuth):
        """Connecter un utilisateur existant"""
        user = users_collection.find_one({
            "first_name": user_data.first_name,
            "last_name": user_data.last_name
        })
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur non trouvé"
            )
        
        # Créer le token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["id"]}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "first_name": user["first_name"],
                "last_name": user["last_name"]
            }
        }
    
    @staticmethod
    def get_user_profile(user_id: str):
        """Obtenir le profil utilisateur"""
        user = users_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur non trouvé"
            )
        
        return {
            "id": user["id"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "created_at": user.get("created_at")
        }