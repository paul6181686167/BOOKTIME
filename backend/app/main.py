from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import CORS_ORIGINS
from .routers import auth, books

# Créer l'application FastAPI
app = FastAPI(title="BookTime API", description="Votre bibliothèque personnelle")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routers
app.include_router(auth.router)
app.include_router(books.router)

# Endpoint de santé
@app.get("/health")
async def health_check():
    """Vérifier l'état de l'API"""
    from datetime import datetime
    return {
        "status": "ok",
        "database": "connected",
        "timestamp": datetime.utcnow().isoformat()
    }

# Root endpoint
@app.get("/")
async def root():
    """Endpoint racine"""
    return {"message": "BookTime API - Votre bibliothèque personnelle"}