from contextlib import asynccontextmanager
import asyncio
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime, timezone
from .db_config import Database

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Précharge l'index Wikidata statique au démarrage (évite 10–15 s au 1er clic)."""
    def _warm_wikidata():
        try:
            from .static_wikidata import service

            service.ensure_loaded()
            st = service.status()
            logger.info(
                "Wikidata statique prêt : %s séries, standalone=%s",
                st.get("series_count"),
                st.get("standalone_count"),
            )
        except Exception as exc:
            logger.warning("Préchargement Wikidata ignoré : %s", exc)

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _warm_wikidata)

    # Démarrage du job planifié "prochaines sorties" (rafraîchissement + notifications).
    try:
        from .upcoming.scheduler import start_scheduler

        start_scheduler()
    except Exception as exc:
        logger.warning("Scheduler prochaines sorties non démarré : %s", exc)

    try:
        yield
    finally:
        try:
            from .upcoming.scheduler import shutdown_scheduler

            shutdown_scheduler()
        except Exception:
            pass

# Utiliser le système de connexion avancé avec SSL fallbacks
database = Database()
client = database.client

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
# Import du router recommendations avancées (Phase 3.4)
from .recommendations.advanced_routes import router as advanced_recommendations_router
# Import du router intégrations externes (Phase 3.5)
from .integrations.routes import router as integrations_router
# Import du router Wikipedia (Session 87.5)
from .wikipedia.routes import router as wikipedia_router
# Import du router Wikidata (Session 87.12)
from .wikidata.routes import router as wikidata_router
# Import du router Chapters (Session 87.26 - Phase 1 + 2 terminées)
from .chapters.routes import router as chapters_router
# Import du router Catalogue global (seed + découverte)
from .catalog.routes import router as catalog_router
from .static_wikidata.routes import router as static_wikidata_router
from .google_books.routes import router as google_books_router
from .series_verification.routes import router as series_verification_router
# Import du router Prochaines sorties (agrégat prochains tomes + manga + watchlist)
from .upcoming.routes import router as upcoming_router
# Import des routers Notifications + Réglages (V3 prochaines sorties)
from .notifications.routes import router as notifications_router
from .settings.routes import router as settings_router
from .community.routes import router as community_router

app = FastAPI(
    title="BookTime API",
    description="Votre bibliothèque personnelle",
    lifespan=lifespan,
)

# Configuration CORS Production
import os
from typing import List

# URLs autorisées pour CORS - Configuration Production
def get_cors_origins() -> List[str]:
    """Configuration CORS dynamique selon environnement"""
    cors_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        # Accès LAN (autre PC sur le même Wi-Fi)
        "http://192.168.1.167:3000",
        # Application Android (Capacitor) : la WebView sert le bundle depuis
        # https://localhost et envoie cette origine sur chaque requête.
        "https://localhost",
        "http://localhost",
        "capacitor://localhost",
        # Vercel deployments
        "https://booktime-sg59.vercel.app",
        "https://booktime-sg59-git-main-paul6181686167s-projects.vercel.app",
        "https://booktime.vercel.app",
        "https://1571571761761571.vercel.app",
        "https://1571571761761571-git-main-paul6181686167s-projects.vercel.app",
        "https://changelog-reader-9.preview.emergentagent.com",
    ]

    # Accepter tous les sous-domaines *.vercel.app de paul6181686167
    env_origins = os.environ.get("CORS_ORIGINS", "")
    if env_origins:
        cors_origins.extend([origin.strip() for origin in env_origins.split(",")])

    return cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

def _cors_headers(origin: str = None) -> dict:
    """Headers CORS pour les reponses d'erreur - ne renvoie pas d'origine si non autorisée"""
    origins = get_cors_origins()
    if origin and origin in origins:
        allow_origin = origin
    elif not origin:
        allow_origin = origins[0] if origins else "http://localhost:3000"
    else:
        # Origine non autorisée : ne pas exposer un header CORS permissif
        return {}
    return {
        "Access-Control-Allow-Origin": allow_origin,
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "*",
        "Access-Control-Allow-Headers": "*",
    }

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
        headers=_cors_headers(request.headers.get("origin")),
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail} if isinstance(exc.detail, str) else {"detail": exc.detail},
        headers=_cors_headers(request.headers.get("origin")),
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback, logging
    logging.getLogger("booktime").error(f"Unhandled error: {exc}\n{traceback.format_exc()}")
    is_dev = os.environ.get("ENVIRONMENT", "development") == "development"
    detail = str(exc) if is_dev else "Une erreur interne est survenue. Réessaie dans un instant."
    return JSONResponse(
        status_code=500,
        content={"detail": detail},
        headers=_cors_headers(request.headers.get("origin")),
    )

# Routes de base
@app.get("/")
async def read_root():
    return {"message": "BookTime API - Version modulaire avec authentification"}

@app.api_route("/ping", methods=["GET", "HEAD"])
@app.api_route("/api/ping", methods=["GET", "HEAD"])
async def ping():
    """
    Réveil Render / monitoring HTTP sans toucher la base.
    Utiliser cette URL dans UptimeRobot (pas /health) : réponse 200 immédiate même au cold start.
    Accepte GET et HEAD : UptimeRobot utilise HEAD par défaut, ce qui renverrait
    sinon un 405 Method Not Allowed (endpoint GET only).
    """
    return {"ok": True, "ts": datetime.now(timezone.utc).isoformat()}


@app.api_route("/health", methods=["GET", "HEAD"])
@app.api_route("/api/health", methods=["GET", "HEAD"])
async def health():
    """Health check complet (MongoDB) — pour diagnostics, pas pour ping fréquent.
    Accepte GET et HEAD (UptimeRobot utilise HEAD par défaut, sinon 405)."""
    import os
    
    # Vérifier mode mock Railway
    if os.environ.get("RAILWAY_MONGODB_MOCK") == "true":
        return {
            "status": "ok", 
            "database": "mock_mode_railway", 
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "environment": os.environ.get("ENVIRONMENT", "production"),
            "version": "1.0.0",
            "warning": "Running in Railway Mock Mode - No real database connection"
        }
    
    try:
        client.admin.command('ping')
        return {
            "status": "ok", 
            "database": "connected", 
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "environment": os.environ.get("ENVIRONMENT", "development"),
            "version": "1.0.0"
        }
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
app.include_router(social_router)  # Phase 3.3
app.include_router(advanced_recommendations_router)  # Phase 3.4
app.include_router(integrations_router)  # Phase 3.5
app.include_router(wikipedia_router)  # Session 87.5
app.include_router(wikidata_router)    # Session 87.12
app.include_router(chapters_router)    # Session 87.26 - Système chapitres individuels ✅
app.include_router(catalog_router)    # Catalogue global livres populaires
app.include_router(static_wikidata_router)  # Export statique Wikidata (séries + standalone)
app.include_router(google_books_router)  # Google Books (3e source métadonnées)
app.include_router(series_verification_router)  # Vérification croisée tomes (WD + OL + GB)
app.include_router(upcoming_router)  # Prochaines sorties (prochains tomes + manga + watchlist)
app.include_router(notifications_router)  # Notifications in-app
app.include_router(settings_router)  # Réglages (préférences de notification)
app.include_router(community_router)  # Avis / notes de la communauté

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)