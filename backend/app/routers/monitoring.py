# Phase 2.4 : Routes de monitoring
"""
Routes FastAPI pour le monitoring et les métriques
"""

import json
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
from datetime import datetime
from ..monitoring.performance import performance_monitor, health_monitor
from ..auth.dependencies import get_current_user
from ..models.user import User

router = APIRouter()

@router.get("/monitoring/health")
async def get_health_status():
    """
    Endpoint de santé système
    
    Returns:
        Rapport de santé complet du système
    """
    try:
        health_report = health_monitor.get_full_health_report()
        
        # Détermination du code de statut HTTP
        if health_report['overall_status'] == 'unhealthy':
            raise HTTPException(status_code=503, detail=health_report)
        elif health_report['overall_status'] == 'degraded':
            # Status 200 mais avec avertissement
            health_report['warning'] = "Système en mode dégradé"
        
        return health_report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur vérification santé: {str(e)}")

@router.get("/monitoring/metrics")
async def get_performance_metrics(
    hours: int = 24,
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint de métriques de performance
    
    Args:
        hours: Nombre d'heures à inclure dans les métriques
        current_user: Utilisateur actuel (authentification requise)
        
    Returns:
        Métriques de performance détaillées
    """
    try:
        if hours < 1 or hours > 168:  # Max 1 semaine
            raise HTTPException(status_code=400, detail="Heures doit être entre 1 et 168")
        
        metrics = performance_monitor.get_metrics_summary(hours=hours)
        
        # Ajout d'informations contextuelles
        metrics['generated_at'] = datetime.now().isoformat()
        metrics['generated_by'] = current_user.id
        
        return metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération métriques: {str(e)}")

@router.get("/monitoring/performance-summary")
async def get_performance_summary():
    """
    Endpoint pour un résumé rapide des performances
    
    Returns:
        Résumé concis des métriques clés
    """
    try:
        metrics = performance_monitor.get_metrics_summary(hours=1)  # Dernière heure
        
        # Extraction des métriques clés
        summary = {
            'status': 'healthy' if metrics['summary']['error_count'] == 0 else 'degraded',
            'requests_last_hour': metrics['summary']['total_requests'],
            'avg_response_time': metrics['summary']['avg_response_time_ms'],
            'cache_hit_rate': metrics['summary']['cache_hit_rate'],
            'error_count': metrics['summary']['error_count'],
            'timestamp': datetime.now().isoformat()
        }
        
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur résumé performance: {str(e)}")

@router.get("/monitoring/alerts")
async def get_system_alerts():
    """
    Endpoint pour les alertes système
    
    Returns:
        Liste des alertes actives
    """
    try:
        alerts = []
        
        # Vérification des métriques récentes
        metrics = performance_monitor.get_metrics_summary(hours=1)
        
        # Alertes basées sur les seuils
        if metrics['summary']['avg_response_time_ms'] > 1000:
            alerts.append({
                'type': 'performance',
                'level': 'warning',
                'message': f"Temps de réponse élevé: {metrics['summary']['avg_response_time_ms']}ms",
                'timestamp': datetime.now().isoformat()
            })
        
        if metrics['summary']['cache_hit_rate'] < 50:
            alerts.append({
                'type': 'cache',
                'level': 'info',
                'message': f"Taux de cache faible: {metrics['summary']['cache_hit_rate']}%",
                'timestamp': datetime.now().isoformat()
            })
        
        if metrics['summary']['error_count'] > 0:
            alerts.append({
                'type': 'errors',
                'level': 'error',
                'message': f"{metrics['summary']['error_count']} erreurs détectées",
                'timestamp': datetime.now().isoformat()
            })
        
        return {
            'alerts': alerts,
            'total_alerts': len(alerts),
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération alertes: {str(e)}")