from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional
from datetime import datetime

class UserAuth(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserCreate(BaseModel):
    """Modèle pour création d'utilisateur"""
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    """Modèle de réponse utilisateur"""
    id: str
    email: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class LoginResponse(BaseModel):
    """Modèle de réponse pour login"""
    access_token: str
    token_type: str
    user: UserResponse

class User(BaseModel):
    """Modèle utilisateur pour les endpoints protégés"""
    id: str
    email: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)