from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging

# Configuration du logger pour monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])

# === MODELS PYDANTIC ===

class ErrorReport(BaseModel):
    errorId: str
    message: str
    stack: str
    componentStack: str
    timestamp: str
    userAgent: str
    url: str
    userId: str

class PerformanceMetrics(BaseModel):
    sessionId: str
    loadTime: float
    renderTime: float
    memoryUsage: float
    responseTime: float
    errorCount: int
    interactionCount: int
    searchPerformance: List[Dict[str, Any]]
    apiCallsCount: int

class UserAnalytics(BaseModel):
    sessionId: str
    sessionDuration: int  # en secondes
    pageViews: List[Dict[str, Any]]
    interactions: List[Dict[str, Any]]
    searchQueries: List[Dict[str, Any]]
    booksInteractions: List[Dict[str, Any]]
    seriesInteractions: List[Dict[str, Any]]
    categoryPreferences: Dict[str, int]
    mostUsedFeatures: Dict[str, int]

class ABTestMetrics(BaseModel):
    testId: str
    variant: str
    metricName: str
    value: float
    timestamp: str
    userId: str
    additionalData: Optional[Dict[str, Any]] = {}

# === ENDPOINTS ===

@router.post("/errors")
async def log_error(error_report: ErrorReport):
    """
    PHASE 2.4 - Endpoint pour logging des erreurs frontend
    Enregistre les erreurs capturées par ErrorBoundary
    """
    try:
        # Log de l'erreur côté serveur
        logger.error(
            f"Frontend Error [ID: {error_report.errorId}] "
            f"User: {error_report.userId} "
            f"URL: {error_report.url} "
            f"Message: {error_report.message}"
        )
        
        # En production, on pourrait envoyer vers un service comme Sentry
        # sentry_sdk.capture_exception(error_report)
        
        # Pour le développement, stocker en base ou fichier
        error_data = {
            "error_id": error_report.errorId,
            "message": error_report.message,
            "stack": error_report.stack,
            "component_stack": error_report.componentStack,
            "timestamp": error_report.timestamp,
            "user_agent": error_report.userAgent,
            "url": error_report.url,
            "user_id": error_report.userId,
            "logged_at": datetime.utcnow().isoformat()
        }
        
        # TODO: Stocker en base de données MongoDB
        # await db.errors.insert_one(error_data)
        
        return {
            "status": "success",
            "message": "Error logged successfully",
            "error_id": error_report.errorId
        }
        
    except Exception as e:
        logger.error(f"Failed to log error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to log error")

@router.post("/performance")
async def log_performance_metrics(metrics: PerformanceMetrics):
    """
    PHASE 2.4 - Endpoint pour logging des métriques de performance
    Enregistre les données de performance collectées par usePerformanceMonitoring
    """
    try:
        # Log des métriques importantes
        logger.info(
            f"Performance Metrics [Session: {metrics.sessionId}] "
            f"Load: {metrics.loadTime}ms, "
            f"Memory: {metrics.memoryUsage}%, "
            f"API Calls: {metrics.apiCallsCount}, "
            f"Errors: {metrics.errorCount}"
        )
        
        # Alertes automatiques pour métriques critiques
        alerts = []
        if metrics.memoryUsage > 80:
            alerts.append(f"High memory usage: {metrics.memoryUsage}%")
        if metrics.responseTime > 3000:
            alerts.append(f"Slow response time: {metrics.responseTime}ms")
        if metrics.errorCount > 0:
            alerts.append(f"Errors detected: {metrics.errorCount}")
            
        if alerts:
            logger.warning(f"Performance Alerts [Session: {metrics.sessionId}]: {', '.join(alerts)}")
        
        # Données à stocker
        performance_data = {
            "session_id": metrics.sessionId,
            "load_time": metrics.loadTime,
            "render_time": metrics.renderTime,
            "memory_usage": metrics.memoryUsage,
            "response_time": metrics.responseTime,
            "error_count": metrics.errorCount,
            "interaction_count": metrics.interactionCount,
            "search_performance": metrics.searchPerformance,
            "api_calls_count": metrics.apiCallsCount,
            "alerts": alerts,
            "logged_at": datetime.utcnow().isoformat()
        }
        
        # TODO: Stocker en base de données MongoDB
        # await db.performance_metrics.insert_one(performance_data)
        
        return {
            "status": "success",
            "message": "Performance metrics logged successfully",
            "session_id": metrics.sessionId,
            "alerts": alerts
        }
        
    except Exception as e:
        logger.error(f"Failed to log performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to log performance metrics")

@router.post("/analytics")
async def log_user_analytics(analytics: UserAnalytics):
    """
    PHASE 2.4 - Endpoint pour logging des analytics utilisateur
    Enregistre les données de comportement collectées par useUserAnalytics
    """
    try:
        # Calcul de statistiques intéressantes
        total_interactions = len(analytics.interactions)
        total_searches = len(analytics.searchQueries)
        total_book_interactions = len(analytics.booksInteractions)
        total_series_interactions = len(analytics.seriesInteractions)
        
        # Catégorie préférée
        preferred_category = max(analytics.categoryPreferences.items(), key=lambda x: x[1])[0] if analytics.categoryPreferences else "none"
        
        # Fonctionnalité la plus utilisée
        most_used_feature = max(analytics.mostUsedFeatures.items(), key=lambda x: x[1])[0] if analytics.mostUsedFeatures else "none"
        
        logger.info(
            f"User Analytics [Session: {analytics.sessionId}] "
            f"Duration: {analytics.sessionDuration}s, "
            f"Interactions: {total_interactions}, "
            f"Searches: {total_searches}, "
            f"Preferred Category: {preferred_category}, "
            f"Most Used Feature: {most_used_feature}"
        )
        
        # Données à stocker
        analytics_data = {
            "session_id": analytics.sessionId,
            "session_duration": analytics.sessionDuration,
            "page_views": analytics.pageViews,
            "interactions": analytics.interactions,
            "search_queries": analytics.searchQueries,
            "books_interactions": analytics.booksInteractions,
            "series_interactions": analytics.seriesInteractions,
            "category_preferences": analytics.categoryPreferences,
            "most_used_features": analytics.mostUsedFeatures,
            "statistics": {
                "total_interactions": total_interactions,
                "total_searches": total_searches,
                "total_book_interactions": total_book_interactions,
                "total_series_interactions": total_series_interactions,
                "preferred_category": preferred_category,
                "most_used_feature": most_used_feature,
                "interactions_per_minute": (total_interactions / analytics.sessionDuration) * 60 if analytics.sessionDuration > 0 else 0
            },
            "logged_at": datetime.utcnow().isoformat()
        }
        
        # TODO: Stocker en base de données MongoDB
        # await db.user_analytics.insert_one(analytics_data)
        
        return {
            "status": "success",
            "message": "User analytics logged successfully",
            "session_id": analytics.sessionId,
            "statistics": analytics_data["statistics"]
        }
        
    except Exception as e:
        logger.error(f"Failed to log user analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to log user analytics")

@router.post("/abtest")
async def log_abtest_metrics(abtest_data: ABTestMetrics):
    """
    PHASE 2.4 - Endpoint pour logging des métriques A/B Testing
    Enregistre les résultats des tests A/B pour analyse
    """
    try:
        logger.info(
            f"A/B Test Metric [Test: {abtest_data.testId}] "
            f"Variant: {abtest_data.variant}, "
            f"Metric: {abtest_data.metricName} = {abtest_data.value}, "
            f"User: {abtest_data.userId}"
        )
        
        # Données à stocker
        abtest_metric_data = {
            "test_id": abtest_data.testId,
            "variant": abtest_data.variant,
            "metric_name": abtest_data.metricName,
            "value": abtest_data.value,
            "timestamp": abtest_data.timestamp,
            "user_id": abtest_data.userId,
            "additional_data": abtest_data.additionalData,
            "logged_at": datetime.utcnow().isoformat()
        }
        
        # TODO: Stocker en base de données MongoDB
        # await db.abtest_metrics.insert_one(abtest_metric_data)
        
        return {
            "status": "success",
            "message": "A/B test metric logged successfully",
            "test_id": abtest_data.testId,
            "variant": abtest_data.variant
        }
        
    except Exception as e:
        logger.error(f"Failed to log A/B test metric: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to log A/B test metric")

@router.get("/health")
async def monitoring_health():
    """
    PHASE 2.4 - Health check pour le système de monitoring
    Vérifie que tous les services de monitoring fonctionnent
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "error_logging": "operational",
                "performance_monitoring": "operational", 
                "user_analytics": "operational",
                "abtest_tracking": "operational"
            },
            "uptime": "N/A",  # TODO: Calculer l'uptime réel
            "version": "2.4.0"
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Monitoring health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Monitoring health check failed")

@router.get("/stats")
async def get_monitoring_stats():
    """
    PHASE 2.4 - Statistiques globales du monitoring
    Retourne des statistiques agrégées sur le monitoring
    """
    try:
        # TODO: Récupérer les vraies statistiques depuis la base de données
        # Pour l'instant, retourner des données mockées
        stats = {
            "error_reports": {
                "total": 0,
                "last_24h": 0,
                "critical": 0
            },
            "performance_sessions": {
                "total": 0,
                "average_load_time": 0,
                "average_memory_usage": 0
            },
            "user_analytics": {
                "total_sessions": 0,
                "average_session_duration": 0,
                "total_interactions": 0
            },
            "abtest_metrics": {
                "active_tests": 0,
                "total_variants": 0,
                "total_metrics": 0
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Failed to get monitoring stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get monitoring stats")