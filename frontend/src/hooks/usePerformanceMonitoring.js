import { useState, useEffect, useCallback, useRef } from 'react';
import logger from '../utils/logger';

/**
 * PHASE 2.4 - MONITORING ET ANALYTICS
 * Hook pour monitoring des performances en temps réel
 * Surveille les métriques de performance et l'expérience utilisateur
 */

const usePerformanceMonitoring = () => {
  const [metrics, setMetrics] = useState({
    loadTime: 0,
    renderTime: 0,
    memoryUsage: 0,
    responseTime: 0,
    errorCount: 0,
    interactionCount: 0,
    searchPerformance: [],
    apiCallsCount: 0
  });

  const [isMonitoring, setIsMonitoring] = useState(false);
  const metricsRef = useRef(metrics);
  const startTimeRef = useRef(Date.now());

  // Met à jour la référence des métriques
  useEffect(() => {
    metricsRef.current = metrics;
  }, [metrics]);

  // Mesure du temps de chargement initial
  const measureLoadTime = useCallback(() => {
    if (typeof window !== 'undefined' && window.performance) {
      const navigation = window.performance.getEntriesByType('navigation')[0];
      if (navigation) {
        const loadTime = navigation.loadEventEnd - navigation.loadEventStart;
        
        setMetrics(prev => ({
          ...prev,
          loadTime: Math.round(loadTime)
        }));
      }
    }
  }, []);

  // Mesure du temps de rendu d'un composant
  const measureRenderTime = useCallback((componentName, startTime) => {
    const endTime = Date.now();
    const renderTime = endTime - startTime;
    
    logger.debug(` Render time for ${componentName}: ${renderTime}ms`);
    
    setMetrics(prev => ({
      ...prev,
      renderTime: renderTime
    }));

    return renderTime;
  }, []);

  // Mesure de l'utilisation mémoire
  const measureMemoryUsage = useCallback(() => {
    if (typeof window !== 'undefined' && window.performance && window.performance.memory) {
      const memory = window.performance.memory;
      const usedJSHeapSize = memory.usedJSHeapSize;
      const totalJSHeapSize = memory.totalJSHeapSize;
      const usagePercentage = (usedJSHeapSize / totalJSHeapSize) * 100;
      
      setMetrics(prev => ({
        ...prev,
        memoryUsage: Math.round(usagePercentage)
      }));

      // Alerte si utilisation mémoire > 80%
      if (usagePercentage > 80) {
        logger.warn(' High memory usage detected:', usagePercentage.toFixed(1) + '%');
      }

      return usagePercentage;
    }
    return 0;
  }, []);

  // Mesure du temps de réponse d'une API
  const measureApiResponse = useCallback((apiName, startTime, success = true) => {
    const endTime = Date.now();
    const responseTime = endTime - startTime;
    
    logger.debug(` API ${apiName} response time: ${responseTime}ms (${success ? 'success' : 'error'})`);
    
    setMetrics(prev => ({
      ...prev,
      responseTime: responseTime,
      apiCallsCount: prev.apiCallsCount + 1,
      errorCount: success ? prev.errorCount : prev.errorCount + 1
    }));

    // Alerte si temps de réponse > 3 secondes
    if (responseTime > 3000) {
      logger.warn(` Slow API response: ${apiName} took ${responseTime}ms`);
    }

    return responseTime;
  }, []);

  // Mesure des performances de recherche
  const measureSearchPerformance = useCallback((searchTerm, resultCount, searchTime) => {
    const searchMetric = {
      term: searchTerm,
      resultCount: resultCount,
      searchTime: searchTime,
      timestamp: Date.now()
    };

    setMetrics(prev => ({
      ...prev,
      searchPerformance: [...prev.searchPerformance.slice(-9), searchMetric] // Garde les 10 dernières recherches
    }));

    logger.debug(` Search performance: "${searchTerm}" → ${resultCount} results in ${searchTime}ms`);

    return searchMetric;
  }, []);

  // Compteur d'interactions utilisateur
  const trackInteraction = useCallback((interactionType) => {
    setMetrics(prev => ({
      ...prev,
      interactionCount: prev.interactionCount + 1
    }));

    logger.debug(` User interaction: ${interactionType} (total: ${metricsRef.current.interactionCount + 1})`);
  }, []);

  // Démarrage du monitoring
  const startMonitoring = useCallback(() => {
    setIsMonitoring(true);
    startTimeRef.current = Date.now();
    
    // Mesures initiales
    measureLoadTime();
    measureMemoryUsage();

    // Monitoring périodique de la mémoire
    const memoryInterval = setInterval(() => {
      if (isMonitoring) {
        measureMemoryUsage();
      }
    }, 30000); // Toutes les 30 secondes

    logger.debug(' Performance monitoring started');

    return () => {
      clearInterval(memoryInterval);
    };
  }, [measureLoadTime, measureMemoryUsage, isMonitoring]);

  // Arrêt du monitoring
  const stopMonitoring = useCallback(() => {
    setIsMonitoring(false);
    logger.debug(' Performance monitoring stopped');
  }, []);

  // Génération d'un rapport de performance
  const getPerformanceReport = useCallback(() => {
    const sessionDuration = Date.now() - startTimeRef.current;
    
    const report = {
      sessionDuration: Math.round(sessionDuration / 1000), // en secondes
      metrics: metricsRef.current,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      averageSearchTime: metricsRef.current.searchPerformance.length > 0 
        ? Math.round(metricsRef.current.searchPerformance.reduce((sum, search) => sum + search.searchTime, 0) / metricsRef.current.searchPerformance.length)
        : 0,
      interactionsPerMinute: Math.round((metricsRef.current.interactionCount / sessionDuration) * 60000)
    };

    logger.debug(' Performance Report:', report);
    return report;
  }, []);

  // Export des métriques (localStorage pour développement)
  const exportMetrics = useCallback(() => {
    const report = getPerformanceReport();
    const exportData = {
      ...report,
      exportedAt: new Date().toISOString()
    };

    localStorage.setItem(`performance_${Date.now()}`, JSON.stringify(exportData));
    logger.debug(' Performance metrics exported to localStorage');
    
    return exportData;
  }, [getPerformanceReport]);

  // Hook de nettoyage
  useEffect(() => {
    return () => {
      if (isMonitoring) {
        stopMonitoring();
      }
    };
  }, [isMonitoring, stopMonitoring]);

  return {
    metrics,
    isMonitoring,
    measureRenderTime,
    measureMemoryUsage,
    measureApiResponse,
    measureSearchPerformance,
    trackInteraction,
    startMonitoring,
    stopMonitoring,
    getPerformanceReport,
    exportMetrics
  };
};

export default usePerformanceMonitoring;