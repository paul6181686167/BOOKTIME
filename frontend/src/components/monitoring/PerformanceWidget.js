import React, { useState, useEffect } from 'react';
import usePerformanceMonitoring from '../../hooks/usePerformanceMonitoring';

/**
 * PHASE 2.4 - MONITORING ET ANALYTICS
 * Widget de monitoring des performances en temps réel
 * Affichage compact des métriques importantes
 */

const PerformanceWidget = ({ position = 'bottom-right', isVisible = true }) => {
  const {
    metrics,
    isMonitoring,
    startMonitoring,
    stopMonitoring,
    getPerformanceReport,
    exportMetrics
  } = usePerformanceMonitoring();

  const [isExpanded, setIsExpanded] = useState(false);
  const [showAlert, setShowAlert] = useState(false);

  // Démarrage automatique du monitoring
  useEffect(() => {
    if (!isMonitoring) {
      startMonitoring();
    }

    return () => {
      if (isMonitoring) {
        stopMonitoring();
      }
    };
  }, []);

  // Surveillance des métriques critiques
  useEffect(() => {
    const hasIssues = metrics.memoryUsage > 80 || metrics.responseTime > 3000 || metrics.errorCount > 0;
    setShowAlert(hasIssues);
  }, [metrics.memoryUsage, metrics.responseTime, metrics.errorCount]);

  if (!isVisible) return null;

  const getPositionClasses = () => {
    switch (position) {
      case 'top-left': return 'top-4 left-4';
      case 'top-right': return 'top-4 right-4';
      case 'bottom-left': return 'bottom-4 left-4';
      case 'bottom-right': return 'bottom-4 right-4';
      default: return 'bottom-4 right-4';
    }
  };

  const getStatusColor = (value, thresholds) => {
    if (value <= thresholds.good) return 'text-green-600 dark:text-green-400';
    if (value <= thresholds.warning) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const formatTime = (ms) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  return (
    <div className={`fixed ${getPositionClasses()} z-50`}>
      {/* Widget principal */}
      <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 transition-all duration-300 ${
        isExpanded ? 'w-80' : 'w-16'
      }`}>
        
        {/* Header avec toggle */}
        <div 
          className="flex items-center justify-between p-3 cursor-pointer"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <div className="flex items-center space-x-2">
            {/* Indicateur de statut */}
            <div className={`w-3 h-3 rounded-full ${
              showAlert ? 'bg-red-500 animate-pulse' : 
              isMonitoring ? 'bg-green-500' : 'bg-gray-400'
            }`} />
            
            {isExpanded && (
              <span className="text-sm font-medium text-gray-900 dark:text-white">
                Performance
              </span>
            )}
          </div>
          
          {isExpanded && (
            <svg 
              className={`w-4 h-4 text-gray-500 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          )}
        </div>

        {/* Contenu détaillé */}
        {isExpanded && (
          <div className="px-3 pb-3 space-y-3">
            {/* Métriques principales */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              {/* Mémoire */}
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-2">
                <div className="text-gray-600 dark:text-gray-400 mb-1">Mémoire</div>
                <div className={`font-mono ${getStatusColor(metrics.memoryUsage, { good: 50, warning: 75 })}`}>
                  {metrics.memoryUsage}%
                </div>
              </div>

              {/* Temps de réponse */}
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-2">
                <div className="text-gray-600 dark:text-gray-400 mb-1">API</div>
                <div className={`font-mono ${getStatusColor(metrics.responseTime, { good: 1000, warning: 2000 })}`}>
                  {formatTime(metrics.responseTime)}
                </div>
              </div>

              {/* Erreurs */}
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-2">
                <div className="text-gray-600 dark:text-gray-400 mb-1">Erreurs</div>
                <div className={`font-mono ${metrics.errorCount > 0 ? 'text-red-600 dark:text-red-400' : 'text-green-600 dark:text-green-400'}`}>
                  {metrics.errorCount}
                </div>
              </div>

              {/* Interactions */}
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-2">
                <div className="text-gray-600 dark:text-gray-400 mb-1">Actions</div>
                <div className="font-mono text-blue-600 dark:text-blue-400">
                  {metrics.interactionCount}
                </div>
              </div>
            </div>

            {/* Performance de recherche */}
            {metrics.searchPerformance.length > 0 && (
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-2">
                <div className="text-gray-600 dark:text-gray-400 mb-1 text-xs">Dernière recherche</div>
                <div className="text-xs">
                  <div className="text-gray-900 dark:text-white font-medium truncate">
                    "{metrics.searchPerformance[metrics.searchPerformance.length - 1]?.term}"
                  </div>
                  <div className="text-gray-600 dark:text-gray-400">
                    {metrics.searchPerformance[metrics.searchPerformance.length - 1]?.resultCount} résultats • {' '}
                    {formatTime(metrics.searchPerformance[metrics.searchPerformance.length - 1]?.searchTime)}
                  </div>
                </div>
              </div>
            )}

            {/* Actions */}
            <div className="flex space-x-2">
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  exportMetrics();
                }}
                className="flex-1 px-2 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors duration-200"
              >
                Export
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  console.log(getPerformanceReport());
                }}
                className="flex-1 px-2 py-1 text-xs bg-gray-600 hover:bg-gray-700 text-white rounded transition-colors duration-200"
              >
                Rapport
              </button>
            </div>

            {/* Alerte de performance */}
            {showAlert && (
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-2">
                <div className="text-red-800 dark:text-red-200 text-xs font-medium">
                  ⚠️ Problème de performance détecté
                </div>
                <div className="text-red-600 dark:text-red-400 text-xs mt-1">
                  {metrics.memoryUsage > 80 && 'Utilisation mémoire élevée. '}
                  {metrics.responseTime > 3000 && 'Temps de réponse lent. '}
                  {metrics.errorCount > 0 && `${metrics.errorCount} erreur(s) détectée(s).`}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default PerformanceWidget;