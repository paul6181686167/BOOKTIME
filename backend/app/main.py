from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from .database.connection import client

# Import des routers
from .auth.routes import router as auth_router
from .books.routes import router as books_router
from .series.routes import router as series_router
from .sagas.routes import router as sagas_router
from .openlibrary.routes import router as openlibrary_router
from .library.routes import router as library_router
from .stats.routes import router as stats_router
from .authors.routes import router as authors_router

# Import du router optimisé
from .routers.optimized_books import router as optimized_books_router
# Import du router pagination (Phase 2.2)
from .routers.pagination import router as pagination_router
# Import du router monitoring (Phase 2.4)
from .monitoring.routes import router as monitoring_router
# Import du router recommendations (Phase 3.1)
from .recommendations.routes import router as recommendations_router
# Import du router export/import (Phase 3.2)
from .export_import.routes import router as export_import_router
# Import du router social (Phase 3.3)
from .social.routes import router as social_router

app = FastAPI(title="BookTime API", description="Votre bibliothèque personnelle")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes de base
@app.get("/")
async def read_root():
    return {"message": "BookTime API - Version modulaire avec authentification"}

@app.get("/health")
async def health():
    try:
        client.admin.command('ping')
        return {"status": "ok", "database": "connected", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

# Enregistrement des routers
app.include_router(auth_router)
app.include_router(books_router)
app.include_router(series_router)
app.include_router(sagas_router)
app.include_router(openlibrary_router)
app.include_router(library_router)
app.include_router(stats_router)
app.include_router(authors_router)
app.include_router(optimized_books_router)
app.include_router(pagination_router)
app.include_router(monitoring_router)
app.include_router(recommendations_router)  # Phase 3.1
app.include_router(export_import_router)  # Phase 3.2

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)