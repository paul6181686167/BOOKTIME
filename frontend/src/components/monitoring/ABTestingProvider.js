import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

/**
 * PHASE 2.4 - MONITORING ET ANALYTICS
 * Provider pour A/B Testing et tests de performance comparatifs
 * Permet de tester différentes versions de composants et d'analyser les performances
 */

const ABTestingContext = createContext();

// Configuration des tests A/B disponibles
const DEFAULT_TESTS = {
  SEARCH_DEBOUNCE: {
    id: 'search_debounce',
    name: 'Délai de debounce pour la recherche',
    variants: {
      A: { debounceDelay: 300, description: 'Délai 300ms (standard)' },
      B: { debounceDelay: 500, description: 'Délai 500ms (plus lent)' },
      C: { debounceDelay: 150, description: 'Délai 150ms (plus rapide)' }
    },
    metrics: ['searchTime', 'userSatisfaction', 'serverLoad']
  },
  
  PAGINATION_SIZE: {
    id: 'pagination_size',
    name: 'Taille de pagination pour les livres',
    variants: {
      A: { pageSize: 20, description: '20 livres par page (standard)' },
      B: { pageSize: 30, description: '30 livres par page (plus)' },
      C: { pageSize: 15, description: '15 livres par page (moins)' }
    },
    metrics: ['loadTime', 'userEngagement', 'memoryUsage']
  },

  BOOK_CARD_LAYOUT: {
    id: 'book_card_layout',
    name: 'Disposition des cartes de livres',
    variants: {
      A: { layout: 'grid', columns: 'auto', description: 'Grille automatique' },
      B: { layout: 'grid', columns: 'fixed-4', description: 'Grille fixe 4 colonnes' },
      C: { layout: 'list', columns: 'single', description: 'Liste verticale' }
    },
    metrics: ['userEngagement', 'clickRate', 'visualSatisfaction']
  },

  SEARCH_SUGGESTIONS: {
    id: 'search_suggestions',
    name: 'Suggestions de recherche',
    variants: {
      A: { enabled: true, count: 5, description: '5 suggestions activées' },
      B: { enabled: true, count: 3, description: '3 suggestions activées' },
      C: { enabled: false, count: 0, description: 'Suggestions désactivées' }
    },
    metrics: ['searchSuccess', 'userSatisfaction', 'conversionRate']
  },

  THEME_DEFAULT: {
    id: 'theme_default',
    name: 'Thème par défaut',
    variants: {
      A: { theme: 'light', description: 'Thème clair par défaut' },
      B: { theme: 'dark', description: 'Thème sombre par défaut' },
      C: { theme: 'auto', description: 'Thème automatique (système)' }
    },
    metrics: ['userRetention', 'sessionDuration', 'themePreference']
  }
};

export const ABTestingProvider = ({ children, enabledTests = Object.keys(DEFAULT_TESTS) }) => {
  const [userVariants, setUserVariants] = useState({});
  const [testMetrics, setTestMetrics] = useState({});
  const [isInitialized, setIsInitialized] = useState(false);

  // Génération d'un ID utilisateur pour les tests (basé sur localStorage)
  const getUserId = useCallback(() => {
    let userId = localStorage.getItem('ab_test_user_id');
    if (!userId) {
      userId = `abtest_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      localStorage.setItem('ab_test_user_id', userId);
    }
    return userId;
  }, []);

  // Assignation d'un utilisateur à une variante (stable et reproductible)
  const assignVariant = useCallback((testId, variants) => {
    const userId = getUserId();
    const hash = simpleHash(userId + testId);
    const variantKeys = Object.keys(variants);
    const variantIndex = hash % variantKeys.length;
    
    return variantKeys[variantIndex];
  }, [getUserId]);

  // Fonction de hash simple pour répartition stable
  const simpleHash = (str) => {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash);
  };

  // Initialisation des tests A/B
  const initializeTests = useCallback(() => {
    const variants = {};
    const savedVariants = localStorage.getItem('ab_test_variants');
    
    // Restaurer les variantes sauvegardées si disponibles
    let existingVariants = {};
    if (savedVariants) {
      try {
        existingVariants = JSON.parse(savedVariants);
      } catch (error) {
        console.warn('Invalid saved A/B test variants:', error);
      }
    }

    // Assigner les variantes pour chaque test activé
    enabledTests.forEach(testId => {
      if (DEFAULT_TESTS[testId]) {
        const test = DEFAULT_TESTS[testId];
        
        // Utiliser la variante existante ou en assigner une nouvelle
        const variant = existingVariants[testId] || assignVariant(testId, test.variants);
        variants[testId] = variant;
        
        console.log(` A/B Test "${testId}": User assigned to variant "${variant}" - ${test.variants[variant]?.description}`);
      }
    });

    setUserVariants(variants);
    
    // Sauvegarder les variantes
    localStorage.setItem('ab_test_variants', JSON.stringify(variants));
    
    setIsInitialized(true);
  }, [enabledTests, assignVariant]);

  // Initialisation au montage
  useEffect(() => {
    initializeTests();
  }, [initializeTests]);

  // Obtenir la configuration d'un test
  const getTestConfig = useCallback((testId) => {
    if (!isInitialized || !userVariants[testId] || !DEFAULT_TESTS[testId]) {
      return null;
    }

    const test = DEFAULT_TESTS[testId];
    const variant = userVariants[testId];
    
    return {
      testId,
      variant,
      config: test.variants[variant],
      testInfo: {
        name: test.name,
        description: test.variants[variant]?.description,
        metrics: test.metrics
      }
    };
  }, [isInitialized, userVariants]);

  // Enregistrer une métrique pour un test
  const recordMetric = useCallback((testId, metricName, value, additionalData = {}) => {
    if (!isInitialized || !userVariants[testId]) {
      return;
    }

    const timestamp = Date.now();
    const userId = getUserId();
    const variant = userVariants[testId];

    const metricData = {
      testId,
      variant,
      metricName,
      value,
      timestamp,
      userId,
      ...additionalData
    };

    setTestMetrics(prev => ({
      ...prev,
      [testId]: {
        ...prev[testId],
        [metricName]: [...(prev[testId]?.[metricName] || []), metricData]
      }
    }));

    // Log pour debugging
    console.log(` A/B Test Metric: ${testId}.${metricName} = ${value} (variant: ${variant})`);

    // Sauvegarde localStorage
    const metricsKey = `ab_test_metrics_${testId}`;
    const existingMetrics = JSON.parse(localStorage.getItem(metricsKey) || '[]');
    existingMetrics.push(metricData);
    localStorage.setItem(metricsKey, JSON.stringify(existingMetrics));

  }, [isInitialized, userVariants, getUserId]);

  // Analyser les résultats d'un test (pour debugging)
  const analyzeTest = useCallback((testId) => {
    if (!DEFAULT_TESTS[testId]) {
      return null;
    }

    const test = DEFAULT_TESTS[testId];
    const metrics = testMetrics[testId] || {};
    
    const analysis = {
      testId,
      testName: test.name,
      currentVariant: userVariants[testId],
      metricsCollected: Object.keys(metrics),
      totalDataPoints: Object.values(metrics).reduce((sum, metricArray) => sum + metricArray.length, 0)
    };

    console.log(` A/B Test Analysis for "${testId}":`, analysis);
    return analysis;
  }, [testMetrics, userVariants]);

  // Export des données pour analyse externe
  const exportTestData = useCallback(() => {
    const exportData = {
      userId: getUserId(),
      userVariants,
      testMetrics,
      exportedAt: new Date().toISOString(),
      testsConfiguration: DEFAULT_TESTS
    };

    // Créer un fichier JSON téléchargeable
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `booktime_abtest_${getUserId()}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();

    console.log(' A/B Test data exported');
    return exportData;
  }, [getUserId, userVariants, testMetrics]);

  // Forcer la réassignation d'un test (pour debugging)
  const reassignTest = useCallback((testId) => {
    if (!DEFAULT_TESTS[testId]) {
      return;
    }

    const test = DEFAULT_TESTS[testId];
    const newVariant = assignVariant(testId + '_' + Date.now(), test.variants); // Force nouvelle assignation
    
    setUserVariants(prev => ({
      ...prev,
      [testId]: newVariant
    }));

    // Mise à jour localStorage
    const savedVariants = JSON.parse(localStorage.getItem('ab_test_variants') || '{}');
    savedVariants[testId] = newVariant;
    localStorage.setItem('ab_test_variants', JSON.stringify(savedVariants));

    console.log(` A/B Test "${testId}" reassigned to variant "${newVariant}"`);
  }, [assignVariant]);

  const contextValue = {
    isInitialized,
    userVariants,
    getTestConfig,
    recordMetric,
    analyzeTest,
    exportTestData,
    reassignTest,
    availableTests: DEFAULT_TESTS
  };

  // Exposure de l'API sur window pour debug (développement uniquement)
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      window.BookTimeABTesting = contextValue;
      console.log(' A/B Testing API available at window.BookTimeABTesting');
    }
  }, [contextValue]);

  return (
    <ABTestingContext.Provider value={contextValue}>
      {children}
    </ABTestingContext.Provider>
  );
};

// Hook pour utiliser le contexte A/B Testing
export const useABTesting = () => {
  const context = useContext(ABTestingContext);
  if (!context) {
    throw new Error('useABTesting must be used within an ABTestingProvider');
  }
  return context;
};

export default ABTestingProvider;