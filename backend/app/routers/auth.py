from fastapi import APIRouter, Depends
from ..services.auth_service import AuthService
from ..models.common import UserAuth
from ..utils.security import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register")
async def register(user_data: UserAuth):
    """Enregistrer un nouvel utilisateur"""
    return AuthService.register_user(user_data)

@router.post("/login")
async def login(user_data: UserAuth):
    """Connecter un utilisateur"""
    return AuthService.login_user(user_data)

@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Obtenir les informations de l'utilisateur actuel"""
    return AuthService.get_user_profile(current_user["id"])