from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class UserAuth(BaseModel):
    first_name: str
    last_name: str

class User(BaseModel):
    """Modèle utilisateur pour les endpoints protégés"""
    id: str
    first_name: str
    last_name: str
    created_at: Optional[datetime] = None
    
    class Config:
        # Permet la création depuis dict MongoDB
        from_attributes = True