from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
import uuid

# Configuration
SECRET_KEY = "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Modèles Pydantic
class UserAuth(BaseModel):
    first_name: str
    last_name: str

# Créer l'application
app = FastAPI(title="BookTime API Minimal", description="Version minimale pour tester l'authentification")

# Fonction pour créer un token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Routes
@app.get("/")
async def read_root():
    return {"message": "BookTime API Minimal - Test d'authentification"}

# Routes d'authentification
@app.post("/api/auth/register")
async def register(user_data: UserAuth):
    # Simuler la création d'un utilisateur
    user_id = str(uuid.uuid4())
    
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

@app.post("/api/auth/login")
async def login(user_data: UserAuth):
    # Simuler la connexion d'un utilisateur
    user_id = str(uuid.uuid4())
    
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

@app.get("/api/auth/me")
async def get_me():
    return {"message": "This is a test endpoint"}
