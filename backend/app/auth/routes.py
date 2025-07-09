from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta
import uuid
from ..models.user import UserAuth
from ..database.connection import users_collection
from ..security.jwt import create_access_token, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register")
async def register(user_data: UserAuth):
    """Enregistrer un nouveau utilisateur"""
    # Vérifier si l'utilisateur existe déjà
    existing_user = users_collection.find_one({
        "first_name": user_data.first_name, 
        "last_name": user_data.last_name
    })
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Un utilisateur avec ce nom existe déjà"
        )
    
    # Créer un nouvel utilisateur
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "created_at": datetime.utcnow()
    }
    
    users_collection.insert_one(user)
    
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

@router.post("/login")
async def login(user_data: UserAuth):
    """Connexion d'un utilisateur"""
    user = users_collection.find_one({
        "first_name": user_data.first_name,
        "last_name": user_data.last_name
    }, {"_id": 0})
    
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Utilisateur non trouvé"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["id"]}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Obtenir les informations de l'utilisateur actuel"""
    return current_user