# Dépendances partagées pour BOOKTIME
import jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import SECRET_KEY, ALGORITHM
from .database import users_collection
from .models.user import UserResponse

# Security
security = HTTPBearer()

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Crée un token JWT"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """Vérifie un token JWT"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Récupère l'utilisateur actuel depuis le token"""
    token = credentials.credentials
    user_id = verify_token(token)
    
    # Récupérer l'utilisateur dans la base de données
    user = users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse(**user)

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Récupère l'ID de l'utilisateur actuel (version légère)"""
    token = credentials.credentials
    return verify_token(token)

def validate_category(category: str):
    """Valide une catégorie"""
    from .config import VALID_CATEGORIES
    if category and category.lower() not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category must be one of: {', '.join(VALID_CATEGORIES)}"
        )
    return category.lower() if category else None

def validate_status(status_value: str):
    """Valide un statut"""
    from .config import VALID_STATUSES
    if status_value and status_value.lower() not in VALID_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Status must be one of: {', '.join(VALID_STATUSES)}"
        )
    return status_value.lower() if status_value else None

def validate_pagination(page: int = 1, limit: int = 10):
    """Valide les paramètres de pagination"""
    from .config import MAX_LIMIT
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be greater than 0"
        )
    if limit < 1 or limit > MAX_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Limit must be between 1 and {MAX_LIMIT}"
        )
    return page, limit

def get_pagination_params(page: int = 1, limit: int = 10):
    """Récupère les paramètres de pagination validés"""
    page, limit = validate_pagination(page, limit)
    offset = (page - 1) * limit
    return {
        "page": page,
        "limit": limit,
        "offset": offset,
        "skip": offset
    }

def handle_database_error(error: Exception):
    """Gère les erreurs de base de données"""
    error_message = str(error)
    if "duplicate key error" in error_message.lower():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resource already exists"
        )
    elif "not found" in error_message.lower():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resource not found"
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        )

def require_user_permission(user_id: str, resource_user_id: str):
    """Vérifie que l'utilisateur a les permissions pour accéder à la ressource"""
    if user_id != resource_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this resource"
        )

def normalize_search_term(term: str):
    """Normalise un terme de recherche"""
    if not term:
        return ""
    return term.strip().lower()

def build_search_query(term: str, fields: list):
    """Construit une requête de recherche MongoDB"""
    if not term:
        return {}
    
    normalized_term = normalize_search_term(term)
    
    # Recherche par expression régulière insensible à la casse
    search_patterns = []
    for field in fields:
        search_patterns.append({
            field: {"$regex": normalized_term, "$options": "i"}
        })
    
    return {"$or": search_patterns}

def calculate_offset(page: int, limit: int):
    """Calcule l'offset pour la pagination"""
    return (page - 1) * limit

def build_pagination_response(total: int, page: int, limit: int):
    """Construit les métadonnées de pagination"""
    total_pages = (total + limit - 1) // limit
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1
    }