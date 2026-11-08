from contextlib import asynccontextmanager
import asyncio
import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from datetime import datetime, timezone
from .db_config import Database

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ping immédiat au cold start ; Wikidata + catalogue 50k se préchargent ensuite."""
    def _warm_indexes():
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
        try:
            from .catalog import expanded as expanded_fiches
            from .series_verification import curated as curated_mod

            st = expanded_fiches.stats()
            curated_mod.ensure_loaded()
            logger.info(
                "Catalogue 50k prêt : %s séries, %s tomes",
                st.get("series"),
                st.get("books"),
            )
        except Exception as exc:
            logger.warning("Préchargement catalogue ignoré : %s", exc)

    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _warm_indexes)

    # Index MongoDB (idempotent, en tâche de fond) : sans eux chaque requête par user_id
    # parcourt toute la collection.
    try:
        from .database.indexes import ensure_indexes

        loop.run_in_executor(None, ensure_indexes)
    except Exception as exc:
        logger.warning("Création des index ignorée : %s", exc)

    # Démarrage du job planifié "prochaines sorties" (rafraîchissement + notifications).
    try:
        from .upcoming.scheduler import start_scheduler

        start_scheduler()
    except Exception as exc:
        logger.warning("Scheduler prochaines sorties non démarré : %s", exc)

    try:
        from .catalog.daily_scheduler import start_daily_scheduler

        start_daily_scheduler()
    except Exception as exc:
        logger.warning("Scheduler fiches quotidiennes non démarré : %s", exc)

    try:
        yield
    finally:
        try:
            from .upcoming.scheduler import shutdown_scheduler

            shutdown_scheduler()
        except Exception:
            pass
        try:
            from .catalog.daily_scheduler import shutdown_daily_scheduler

            shutdown_daily_scheduler()
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

# Import du router monitoring (Phase 2.4)
from .monitoring.routes import router as monitoring_router
# Import du router recommendations (Phase 3.1)
from .recommendations.routes import router as recommendations_router
# Import du router export/import (Phase 3.2)
from .export_import.routes import router as export_import_router
# Import du router social (Phase 3.3)
from .social.routes import router as social_router
from .friends.routes import router as friends_router
from .admin.routes import router as admin_router
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
from .user_collections.routes import router as user_collections_router
from .external_ratings.routes import router as external_ratings_router

app = FastAPI(
    title="BookTime API",
    description="Votre bibliothèque personnelle",
    lifespan=lifespan,
)

# CORS : liste d'origines explicite + prévisualisations de ton compte Vercel (voir security/cors.py)
import os
from .config import is_development
from .security.cors import (
    ALLOWED_HEADERS,
    ALLOWED_METHODS,
    cors_headers_for,
    get_cors_origins,
    get_origin_regex,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_origin_regex=get_origin_regex(),
    allow_credentials=True,
    allow_methods=ALLOWED_METHODS,
    allow_headers=ALLOWED_HEADERS,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": jsonable_encoder(exc.errors())},
        headers=cors_headers_for(request.headers.get("origin")),
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    headers = cors_headers_for(request.headers.get("origin"))
    headers.update(getattr(exc, "headers", None) or {})
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers,
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.getLogger("booktime").error("Unhandled error: %s", exc, exc_info=exc)
    # Détail de l'exception montré seulement en développement explicite (ENVIRONMENT=development)
    detail = str(exc) if is_development() else "Une erreur interne est survenue. Réessaie dans un instant."
    return JSONResponse(
        status_code=500,
        content={"detail": detail},
        headers=cors_headers_for(request.headers.get("origin")),
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
    now = datetime.now(timezone.utc).isoformat()
    environment = os.environ.get("ENVIRONMENT", "development")

    if database.is_mock_mode():
        # Base en mémoire : les données ne survivent pas à un redémarrage. En production ce
        # mode est refusé au démarrage ; ailleurs on le signale clairement (statut 200 conservé
        # pour les tests et le développement local).
        return {
            "status": "ok",
            "database": "mock_in_memory",
            "timestamp": now,
            "environment": environment,
            "version": "1.0.0",
            "warning": "Base MongoDB simulée en mémoire : données non persistantes",
        }

    try:
        # ping Mongo hors de la boucle : un ping sync bloquait autrement toute l'API
        await asyncio.to_thread(client.admin.command, "ping")
        return {
            "status": "ok",
            "database": "connected",
            "timestamp": now,
            "environment": environment,
            "version": "1.0.0",
        }
    except Exception as e:
        logger.error("Health check : MongoDB injoignable : %s", e)
        raise HTTPException(status_code=503, detail="Base de données indisponible")


# Enregistrement des routers
app.include_router(auth_router)
app.include_router(books_router)
app.include_router(series_router)
app.include_router(sagas_router)
app.include_router(openlibrary_router)
app.include_router(library_router)
app.include_router(stats_router)
app.include_router(authors_router)
app.include_router(monitoring_router)
app.include_router(recommendations_router)  # Phase 3.1
app.include_router(export_import_router)  # Phase 3.2
app.include_router(social_router)  # Phase 3.3
app.include_router(friends_router)
app.include_router(admin_router)
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
app.include_router(user_collections_router)  # Collections synchronisées
app.include_router(external_ratings_router)  # Notes d'autres sites

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)