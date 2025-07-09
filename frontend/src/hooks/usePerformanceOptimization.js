// Phase 2.3 - Hook pour optimisations performance avancées
import { useCallback, useMemo, useRef, useEffect, useState } from 'react';

/**
 * Hook pour optimiser les re-rendus avec useMemo et useCallback
 */
export const useOptimizedState = (initialState, dependencies = []) => {
  const [state, setState] = useState(initialState);
  
  // Memoization de l'état si les dépendances n'ont pas changé
  const optimizedState = useMemo(() => state, dependencies);
  
  // Callback optimisé pour mettre à jour l'état
  const setOptimizedState = useCallback((newState) => {
    setState(newState);
  }, []);

  return [optimizedState, setOptimizedState];
};

/**
 * Hook pour throttling des fonctions (limitation de fréquence d'exécution)
 */
export const useThrottle = (callback, delay = 100) => {
  const lastExecTime = useRef(0);
  const timeoutRef = useRef(null);

  const throttledCallback = useCallback((...args) => {
    const now = Date.now();
    
    if (now - lastExecTime.current > delay) {
      // Exécuter immédiatement si le délai est écoulé
      callback(...args);
      lastExecTime.current = now;
    } else {
      // Programmer l'exécution pour plus tard
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      
      timeoutRef.current = setTimeout(() => {
        callback(...args);
        lastExecTime.current = Date.now();
      }, delay - (now - lastExecTime.current));
    }
  }, [callback, delay]);

  // Nettoyage au démontage
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return throttledCallback;
};

/**
 * Hook pour mesurer les performances de rendu
 */
export const usePerformanceMonitor = (componentName) => {
  const renderCount = useRef(0);
  const lastRenderTime = useRef(0);
  const [performanceData, setPerformanceData] = useState({
    renderCount: 0,
    averageRenderTime: 0,
    lastRenderTime: 0
  });

  useEffect(() => {
    const startTime = performance.now();
    renderCount.current += 1;
    
    // Mesurer le temps de rendu
    const measureRenderTime = () => {
      const endTime = performance.now();
      const renderTime = endTime - startTime;
      lastRenderTime.current = renderTime;
      
      setPerformanceData(prev => ({
        renderCount: renderCount.current,
        averageRenderTime: (prev.averageRenderTime * (renderCount.current - 1) + renderTime) / renderCount.current,
        lastRenderTime: renderTime
      }));
    };

    // Utiliser setTimeout pour mesurer après le rendu
    const timer = setTimeout(measureRenderTime, 0);
    
    return () => clearTimeout(timer);
  });

  // Logger les performances en mode développement
  useEffect(() => {
    if (process.env.NODE_ENV === 'development' && renderCount.current > 0) {
      console.log(`[Performance] ${componentName}:`, {
        renderCount: renderCount.current,
        lastRenderTime: lastRenderTime.current.toFixed(2) + 'ms',
        averageRenderTime: performanceData.averageRenderTime.toFixed(2) + 'ms'
      });
    }
  }, [componentName, performanceData]);

  return performanceData;
};

/**
 * Hook pour optimiser les grandes listes avec intersection observer
 */
export const useVirtualization = (itemCount, itemHeight, containerHeight) => {
  const [scrollTop, setScrollTop] = useState(0);
  const [isScrolling, setIsScrolling] = useState(false);
  const scrollingTimeoutRef = useRef(null);

  const visibleRange = useMemo(() => {
    const visibleCount = Math.ceil(containerHeight / itemHeight);
    const startIndex = Math.floor(scrollTop / itemHeight);
    const endIndex = Math.min(startIndex + visibleCount + 1, itemCount - 1);
    
    return {
      startIndex: Math.max(0, startIndex),
      endIndex: Math.max(0, endIndex),
      visibleCount
    };
  }, [scrollTop, itemHeight, containerHeight, itemCount]);

  const handleScroll = useCallback((e) => {
    const newScrollTop = e.target.scrollTop;
    setScrollTop(newScrollTop);
    setIsScrolling(true);

    // Détecter la fin du scroll
    if (scrollingTimeoutRef.current) {
      clearTimeout(scrollingTimeoutRef.current);
    }
    
    scrollingTimeoutRef.current = setTimeout(() => {
      setIsScrolling(false);
    }, 150);
  }, []);

  useEffect(() => {
    return () => {
      if (scrollingTimeoutRef.current) {
        clearTimeout(scrollingTimeoutRef.current);
      }
    };
  }, []);

  return {
    visibleRange,
    handleScroll,
    isScrolling,
    totalHeight: itemCount * itemHeight
  };
};

/**
 * Hook pour la mémorisation intelligente des résultats de calculs
 */
export const useSmartMemo = (computeFunction, dependencies, cacheSize = 10) => {
  const cacheRef = useRef(new Map());

  const result = useMemo(() => {
    // Créer une clé basée sur les dépendances
    const key = JSON.stringify(dependencies);
    
    // Vérifier si le résultat est déjà en cache
    if (cacheRef.current.has(key)) {
      return cacheRef.current.get(key);
    }

    // Calculer le nouveau résultat
    const newResult = computeFunction();
    
    // Ajouter au cache
    cacheRef.current.set(key, newResult);
    
    // Limiter la taille du cache
    if (cacheRef.current.size > cacheSize) {
      const firstKey = cacheRef.current.keys().next().value;
      cacheRef.current.delete(firstKey);
    }
    
    return newResult;
  }, dependencies);

  return result;
};

/**
 * Hook pour optimiser les requêtes API avec cache
 */
export const useOptimizedAPI = (apiFunction, dependencies = [], cacheTimeout = 5 * 60 * 1000) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const cacheRef = useRef(new Map());

  const fetchData = useCallback(async () => {
    const key = JSON.stringify(dependencies);
    const cachedData = cacheRef.current.get(key);
    
    // Vérifier si on a des données en cache et si elles sont encore valides
    if (cachedData && Date.now() - cachedData.timestamp < cacheTimeout) {
      setData(cachedData.data);
      return;
    }

    setLoading(true);
    setError(null);
    
    try {
      const result = await apiFunction();
      setData(result);
      
      // Mettre en cache
      cacheRef.current.set(key, {
        data: result,
        timestamp: Date.now()
      });
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [apiFunction, ...dependencies, cacheTimeout]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
};

export default {
  useOptimizedState,
  useThrottle,
  usePerformanceMonitor,
  useVirtualization,
  useSmartMemo,
  useOptimizedAPI
};