# Modèles utilisateur pour BOOKTIME
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class UserAuth(BaseModel):
    """Modèle pour l'authentification utilisateur"""
    first_name: str = Field(..., min_length=1, max_length=50, description="Prénom de l'utilisateur")
    last_name: str = Field(..., min_length=1, max_length=50, description="Nom de l'utilisateur")

class UserCreate(UserAuth):
    """Modèle pour la création d'utilisateur"""
    pass

class UserUpdate(BaseModel):
    """Modèle pour la mise à jour d'utilisateur"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)

class UserResponse(BaseModel):
    """Modèle pour la réponse utilisateur"""
    id: str
    first_name: str
    last_name: str
    date_created: datetime
    
    class Config:
        from_attributes = True

class LoginResponse(BaseModel):
    """Modèle pour la réponse de connexion"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse