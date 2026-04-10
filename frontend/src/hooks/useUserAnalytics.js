import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * PHASE 2.4 - MONITORING ET ANALYTICS
 * Hook pour suivi du comportement utilisateur et analytics
 * Collecte des données d'usage pour améliorer l'expérience utilisateur
 */

const useUserAnalytics = () => {
  const [analytics, setAnalytics] = useState({
    sessionId: null,
    startTime: null,
    pageViews: [],
    interactions: [],
    searchQueries: [],
    booksInteractions: [],
    seriesInteractions: [],
    categoryPreferences: { roman: 0, bd: 0, manga: 0 },
    sessionDuration: 0,
    mostUsedFeatures: new Map()
  });

  const [isTracking, setIsTracking] = useState(false);
  const sessionRef = useRef(null);
  const analyticsRef = useRef(analytics);

  // Met à jour la référence des analytics
  useEffect(() => {
    analyticsRef.current = analytics;
  }, [analytics]);

  // Génération d'un ID de session unique
  const generateSessionId = useCallback(() => {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  // Démarrage du tracking
  const startTracking = useCallback(() => {
    const sessionId = generateSessionId();
    const startTime = Date.now();
    
    setAnalytics(prev => ({
      ...prev,
      sessionId,
      startTime
    }));
    
    setIsTracking(true);
    sessionRef.current = sessionId;
    
    console.log(`📈 User analytics tracking started - Session: ${sessionId}`);
    
    // Tracking de la page initiale
    trackPageView(window.location.pathname);
  }, [generateSessionId]);

  // Arrêt du tracking
  const stopTracking = useCallback(() => {
    if (isTracking) {
      const sessionDuration = Date.now() - analyticsRef.current.startTime;
      
      setAnalytics(prev => ({
        ...prev,
        sessionDuration
      }));
      
      setIsTracking(false);
      
      // Sauvegarde des données de session
      saveSessionData();
      
      console.log(`📈 User analytics tracking stopped - Duration: ${Math.round(sessionDuration / 1000)}s`);
    }
  }, [isTracking]);

  // Tracking des vues de page
  const trackPageView = useCallback((page, additionalData = {}) => {
    if (!isTracking) return;

    const pageView = {
      page,
      timestamp: Date.now(),
      sessionId: sessionRef.current,
      ...additionalData
    };

    setAnalytics(prev => ({
      ...prev,
      pageViews: [...prev.pageViews, pageView]
    }));

    console.log(`📄 Page view tracked: ${page}`);
  }, [isTracking]);

  // Tracking des interactions générales
  const trackInteraction = useCallback((action, element, additionalData = {}) => {
    if (!isTracking) return;

    const interaction = {
      action,
      element,
      timestamp: Date.now(),
      sessionId: sessionRef.current,
      ...additionalData
    };

    setAnalytics(prev => ({
      ...prev,
      interactions: [...prev.interactions, interaction],
      mostUsedFeatures: new Map(prev.mostUsedFeatures).set(action, (prev.mostUsedFeatures.get(action) || 0) + 1)
    }));

    console.log(`👆 Interaction tracked: ${action} on ${element}`);
  }, [isTracking]);

  // Tracking des requêtes de recherche
  const trackSearch = useCallback((query, resultCount, category = null, source = 'local') => {
    if (!isTracking) return;

    const searchQuery = {
      query,
      resultCount,
      category,
      source, // 'local' ou 'openlibrary'
      timestamp: Date.now(),
      sessionId: sessionRef.current
    };

    setAnalytics(prev => ({
      ...prev,
      searchQueries: [...prev.searchQueries, searchQuery]
    }));

    console.log(`🔍 Search tracked: "${query}" → ${resultCount} results (${source})`);
  }, [isTracking]);

  // Tracking des interactions avec les livres
  const trackBookInteraction = useCallback((action, bookData) => {
    if (!isTracking) return;

    const bookInteraction = {
      action, // 'view', 'add', 'update', 'delete', 'rate'
      bookId: bookData.id,
      title: bookData.title,
      author: bookData.author,
      category: bookData.category,
      timestamp: Date.now(),
      sessionId: sessionRef.current
    };

    setAnalytics(prev => ({
      ...prev,
      booksInteractions: [...prev.booksInteractions, bookInteraction],
      categoryPreferences: {
        ...prev.categoryPreferences,
        [bookData.category]: (prev.categoryPreferences[bookData.category] || 0) + 1
      }
    }));

    console.log(`📚 Book interaction tracked: ${action} - ${bookData.title}`);
  }, [isTracking]);

  // Tracking des interactions avec les séries
  const trackSeriesInteraction = useCallback((action, seriesData) => {
    if (!isTracking) return;

    const seriesInteraction = {
      action, // 'view', 'add_complete', 'toggle_volume'
      seriesName: seriesData.name || seriesData.series_name,
      category: seriesData.category,
      volumeCount: seriesData.volumes || seriesData.volumes_count,
      timestamp: Date.now(),
      sessionId: sessionRef.current
    };

    setAnalytics(prev => ({
      ...prev,
      seriesInteractions: [...prev.seriesInteractions, seriesInteraction],
      categoryPreferences: {
        ...prev.categoryPreferences,
        [seriesData.category]: (prev.categoryPreferences[seriesData.category] || 0) + 1
      }
    }));

    console.log(`📖 Series interaction tracked: ${action} - ${seriesData.name || seriesData.series_name}`);
  }, [isTracking]);

  // Tracking des préférences de catégories
  const trackCategorySwitch = useCallback((category) => {
    if (!isTracking) return;

    trackInteraction('category_switch', 'tab', { category });

    setAnalytics(prev => ({
      ...prev,
      categoryPreferences: {
        ...prev.categoryPreferences,
        [category]: (prev.categoryPreferences[category] || 0) + 1
      }
    }));

    console.log(`🏷️ Category switch tracked: ${category}`);
  }, [isTracking, trackInteraction]);

  // Génération d'un rapport d'analytics
  const getAnalyticsReport = useCallback(() => {
    const data = analyticsRef.current;
    const sessionDuration = isTracking ? Date.now() - data.startTime : data.sessionDuration;
    
    // Catégorie préférée
    const preferredCategory = Object.entries(data.categoryPreferences)
      .reduce((a, b) => data.categoryPreferences[a[0]] > data.categoryPreferences[b[0]] ? a : b, ['none', 0])[0];

    // Fonctionnalités les plus utilisées
    const topFeatures = Array.from(data.mostUsedFeatures.entries())
      .sort(([,a], [,b]) => b - a)
      .slice(0, 5);

    // Statistiques de recherche
    const searchStats = {
      totalSearches: data.searchQueries.length,
      averageResults: data.searchQueries.length > 0 
        ? Math.round(data.searchQueries.reduce((sum, search) => sum + search.resultCount, 0) / data.searchQueries.length)
        : 0,
      mostSearchedTerms: data.searchQueries
        .map(s => s.query.toLowerCase())
        .reduce((acc, term) => {
          acc[term] = (acc[term] || 0) + 1;
          return acc;
        }, {})
    };

    const report = {
      sessionId: data.sessionId,
      sessionDuration: Math.round(sessionDuration / 1000), // en secondes
      pageViews: data.pageViews.length,
      totalInteractions: data.interactions.length,
      interactionsPerMinute: Math.round((data.interactions.length / sessionDuration) * 60000),
      preferredCategory,
      categoryPreferences: data.categoryPreferences,
      topFeatures,
      searchStats,
      booksInteractions: data.booksInteractions.length,
      seriesInteractions: data.seriesInteractions.length,
      timestamp: new Date().toISOString()
    };

    console.log('📊 Analytics Report:', report);
    return report;
  }, [isTracking]);

  // Sauvegarde des données de session
  const saveSessionData = useCallback(() => {
    const report = getAnalyticsReport();
    const sessionData = {
      ...report,
      fullData: analyticsRef.current,
      savedAt: new Date().toISOString()
    };

    // Sauvegarde locale (en développement)
    localStorage.setItem(`analytics_${analyticsRef.current.sessionId}`, JSON.stringify(sessionData));

    // En production, envoyer au backend
    if (process.env.NODE_ENV === 'production') {
      fetch('/api/analytics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sessionData)
      }).catch(err => console.error('Failed to send analytics:', err));
    }

    console.log('💾 Analytics data saved');
  }, [getAnalyticsReport]);

  // Export des données analytics
  const exportAnalytics = useCallback(() => {
    const exportData = {
      ...getAnalyticsReport(),
      fullAnalytics: analyticsRef.current,
      exportedAt: new Date().toISOString()
    };

    // Créer un fichier JSON téléchargeable
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `booktime_analytics_${analyticsRef.current.sessionId}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();

    console.log('📥 Analytics data exported');
    return exportData;
  }, [getAnalyticsReport]);

  // Hook de nettoyage
  useEffect(() => {
    return () => {
      if (isTracking) {
        stopTracking();
      }
    };
  }, [isTracking, stopTracking]);

  return {
    analytics,
    isTracking,
    startTracking,
    stopTracking,
    trackPageView,
    trackInteraction,
    trackSearch,
    trackBookInteraction,
    trackSeriesInteraction,
    trackCategorySwitch,
    getAnalyticsReport,
    saveSessionData,
    exportAnalytics
  };
};

export default useUserAnalytics;