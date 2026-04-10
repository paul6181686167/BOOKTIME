import React, { useState, useEffect, useCallback } from 'react';
import { toast } from 'react-hot-toast';

/**
 * PHASE 2.4 - MONITORING ET ANALYTICS
 * Système d'alertes pour notifications de problèmes de performance
 * Surveille les métriques et déclenche des alertes automatiques
 */

const AlertSystem = ({ 
  thresholds = {
    memoryUsage: 80,        // Pourcentage d'utilisation mémoire
    responseTime: 3000,     // Temps de réponse en ms
    errorRate: 5,           // Nombre d'erreurs par minute
    loadTime: 5000,         // Temps de chargement en ms
    searchTime: 2000        // Temps de recherche en ms
  },
  isActive = true 
}) => {
  const [alerts, setAlerts] = useState([]);
  const [alertHistory, setAlertHistory] = useState([]);

  // Types d'alertes disponibles
  const ALERT_TYPES = {
    MEMORY: 'memory',
    PERFORMANCE: 'performance', 
    ERROR: 'error',
    NETWORK: 'network',
    USER_EXPERIENCE: 'ux'
  };

  // Niveaux de sévérité
  const SEVERITY_LEVELS = {
    LOW: 'low',
    MEDIUM: 'medium',
    HIGH: 'high',
    CRITICAL: 'critical'
  };

  // Génération d'une alerte
  const generateAlert = useCallback((type, severity, message, details = {}) => {
    const alert = {
      id: `alert_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type,
      severity,
      message,
      details,
      timestamp: Date.now(),
      acknowledged: false
    };

    setAlerts(prev => [...prev, alert]);
    setAlertHistory(prev => [...prev, alert]);

    // Notification toast selon la sévérité
    const toastConfig = {
      duration: severity === SEVERITY_LEVELS.CRITICAL ? 10000 : 5000,
      style: {
        background: getSeverityColor(severity),
        color: 'white',
      },
    };

    toast(`⚠️ ${message}`, toastConfig);

    console.warn(`🚨 ALERT [${severity.toUpperCase()}] ${type}: ${message}`, details);

    return alert;
  }, []);

  // Couleur selon la sévérité
  const getSeverityColor = (severity) => {
    switch (severity) {
      case SEVERITY_LEVELS.LOW: return '#3b82f6';      // Bleu
      case SEVERITY_LEVELS.MEDIUM: return '#f59e0b';   // Orange
      case SEVERITY_LEVELS.HIGH: return '#ef4444';     // Rouge
      case SEVERITY_LEVELS.CRITICAL: return '#7c2d12'; // Rouge foncé
      default: return '#6b7280';                       // Gris
    }
  };

  // Surveillance de l'utilisation mémoire
  const checkMemoryUsage = useCallback(() => {
    if (typeof window !== 'undefined' && window.performance && window.performance.memory) {
      const memory = window.performance.memory;
      const usedJSHeapSize = memory.usedJSHeapSize;
      const totalJSHeapSize = memory.totalJSHeapSize;
      const usagePercentage = (usedJSHeapSize / totalJSHeapSize) * 100;

      if (usagePercentage > thresholds.memoryUsage) {
        const severity = usagePercentage > 95 ? SEVERITY_LEVELS.CRITICAL :
                        usagePercentage > 90 ? SEVERITY_LEVELS.HIGH : SEVERITY_LEVELS.MEDIUM;

        generateAlert(
          ALERT_TYPES.MEMORY,
          severity,
          `Utilisation mémoire élevée: ${usagePercentage.toFixed(1)}%`,
          {
            usagePercentage: usagePercentage.toFixed(1),
            usedMB: Math.round(usedJSHeapSize / 1024 / 1024),
            totalMB: Math.round(totalJSHeapSize / 1024 / 1024),
            threshold: thresholds.memoryUsage
          }
        );
      }
    }
  }, [thresholds.memoryUsage, generateAlert]);

  // Surveillance des temps de réponse
  const checkResponseTime = useCallback((apiName, responseTime) => {
    if (responseTime > thresholds.responseTime) {
      const severity = responseTime > 10000 ? SEVERITY_LEVELS.CRITICAL :
                      responseTime > 5000 ? SEVERITY_LEVELS.HIGH : SEVERITY_LEVELS.MEDIUM;

      generateAlert(
        ALERT_TYPES.PERFORMANCE,
        severity,
        `Temps de réponse lent: ${apiName} (${responseTime}ms)`,
        {
          apiName,
          responseTime,
          threshold: thresholds.responseTime
        }
      );
    }
  }, [thresholds.responseTime, generateAlert]);

  // Surveillance des erreurs
  const checkErrorRate = useCallback((errorCount, timeWindow = 60000) => {
    const errorsPerMinute = (errorCount / timeWindow) * 60000;
    
    if (errorsPerMinute > thresholds.errorRate) {
      const severity = errorsPerMinute > 20 ? SEVERITY_LEVELS.CRITICAL :
                      errorsPerMinute > 10 ? SEVERITY_LEVELS.HIGH : SEVERITY_LEVELS.MEDIUM;

      generateAlert(
        ALERT_TYPES.ERROR,
        severity,
        `Taux d'erreur élevé: ${errorsPerMinute.toFixed(1)} erreurs/min`,
        {
          errorCount,
          errorsPerMinute: errorsPerMinute.toFixed(1),
          threshold: thresholds.errorRate,
          timeWindow
        }
      );
    }
  }, [thresholds.errorRate, generateAlert]);

  // Surveillance du temps de chargement
  const checkLoadTime = useCallback((loadTime) => {
    if (loadTime > thresholds.loadTime) {
      const severity = loadTime > 15000 ? SEVERITY_LEVELS.CRITICAL :
                      loadTime > 10000 ? SEVERITY_LEVELS.HIGH : SEVERITY_LEVELS.MEDIUM;

      generateAlert(
        ALERT_TYPES.PERFORMANCE,
        severity,
        `Temps de chargement lent: ${(loadTime / 1000).toFixed(1)}s`,
        {
          loadTime,
          loadTimeSeconds: (loadTime / 1000).toFixed(1),
          threshold: thresholds.loadTime
        }
      );
    }
  }, [thresholds.loadTime, generateAlert]);

  // Surveillance des performances de recherche
  const checkSearchPerformance = useCallback((searchTime, resultCount) => {
    if (searchTime > thresholds.searchTime) {
      const severity = searchTime > 5000 ? SEVERITY_LEVELS.HIGH : SEVERITY_LEVELS.MEDIUM;

      generateAlert(
        ALERT_TYPES.USER_EXPERIENCE,
        severity,
        `Recherche lente: ${searchTime}ms pour ${resultCount} résultats`,
        {
          searchTime,
          resultCount,
          threshold: thresholds.searchTime
        }
      );
    }
  }, [thresholds.searchTime, generateAlert]);

  // Détection de problèmes réseau
  const checkNetworkIssues = useCallback(() => {
    if (typeof navigator !== 'undefined' && navigator.connection) {
      const connection = navigator.connection;
      
      // Connexion lente détectée
      if (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g') {
        generateAlert(
          ALERT_TYPES.NETWORK,
          SEVERITY_LEVELS.MEDIUM,
          `Connexion lente détectée: ${connection.effectiveType}`,
          {
            effectiveType: connection.effectiveType,
            downlink: connection.downlink,
            rtt: connection.rtt
          }
        );
      }

      // Connexion économie de données
      if (connection.saveData) {
        generateAlert(
          ALERT_TYPES.NETWORK,
          SEVERITY_LEVELS.LOW,
          'Mode économie de données activé',
          {
            saveData: connection.saveData,
            suggestion: 'Réduire la qualité des images et optimiser les requêtes'
          }
        );
      }
    }
  }, [generateAlert]);

  // Acquittement d'une alerte
  const acknowledgeAlert = useCallback((alertId) => {
    setAlerts(prev => prev.filter(alert => alert.id !== alertId));
  }, []);

  // Acquittement de toutes les alertes
  const acknowledgeAllAlerts = useCallback(() => {
    setAlerts([]);
  }, []);

  // Nettoyage de l'historique
  const clearHistory = useCallback(() => {
    setAlertHistory([]);
  }, []);

  // Export de l'historique des alertes
  const exportAlertHistory = useCallback(() => {
    const exportData = {
      alerts: alertHistory,
      thresholds,
      exportedAt: new Date().toISOString(),
      summary: {
        totalAlerts: alertHistory.length,
        criticalAlerts: alertHistory.filter(a => a.severity === SEVERITY_LEVELS.CRITICAL).length,
        highAlerts: alertHistory.filter(a => a.severity === SEVERITY_LEVELS.HIGH).length,
        mediumAlerts: alertHistory.filter(a => a.severity === SEVERITY_LEVELS.MEDIUM).length,
        lowAlerts: alertHistory.filter(a => a.severity === SEVERITY_LEVELS.LOW).length,
        alertsByType: {
          memory: alertHistory.filter(a => a.type === ALERT_TYPES.MEMORY).length,
          performance: alertHistory.filter(a => a.type === ALERT_TYPES.PERFORMANCE).length,
          error: alertHistory.filter(a => a.type === ALERT_TYPES.ERROR).length,
          network: alertHistory.filter(a => a.type === ALERT_TYPES.NETWORK).length,
          ux: alertHistory.filter(a => a.type === ALERT_TYPES.USER_EXPERIENCE).length
        }
      }
    };

    localStorage.setItem(`alerts_${Date.now()}`, JSON.stringify(exportData));
    console.log('💾 Alert history exported to localStorage');
    
    return exportData;
  }, [alertHistory, thresholds]);

  // Surveillance périodique
  useEffect(() => {
    if (!isActive) return;

    const monitoringInterval = setInterval(() => {
      checkMemoryUsage();
      checkNetworkIssues();
    }, 30000); // Toutes les 30 secondes

    return () => clearInterval(monitoringInterval);
  }, [isActive, checkMemoryUsage, checkNetworkIssues]);

  // Interface publique pour les composants externes
  const alertAPI = {
    checkResponseTime,
    checkErrorRate,
    checkLoadTime,
    checkSearchPerformance,
    generateAlert,
    acknowledgeAlert,
    acknowledgeAllAlerts,
    clearHistory,
    exportAlertHistory,
    alerts,
    alertHistory,
    ALERT_TYPES,
    SEVERITY_LEVELS
  };

  // Exposure de l'API sur window pour debug (développement uniquement)
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      window.BookTimeAlerts = alertAPI;
      console.log('🚨 Alert System API available at window.BookTimeAlerts');
    }
  }, [alertAPI]);

  return alertAPI;
};

export default AlertSystem;