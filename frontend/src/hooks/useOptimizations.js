// Phase 2.3 : Optimisation Frontend - Lazy Loading et Mémorisation
// Hooks React optimisés pour les performances

import { useState, useEffect, useCallback, useMemo, useRef } from 'react';

// Configuration des optimisations
const PAGINATION_CONFIG = {
  DEFAULT_LIMIT: 20,
  MAX_LIMIT: 100,
  CACHE_TTL: 5 * 60 * 1000, // 5 minutes
  DEBOUNCE_DELAY: 300,
  INFINITE_SCROLL_THRESHOLD: 200
};

// Hook pour la pagination avec cache
export const usePaginatedBooks = (filters = {}) => {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({
    total: 0,
    limit: PAGINATION_CONFIG.DEFAULT_LIMIT,
    offset: 0,
    hasNext: false,
    hasPrevious: false
  });

  // Cache en mémoire pour les requêtes
  const cacheRef = useRef(new Map());

  // Génération de clé de cache
  const generateCacheKey = useCallback((filters, limit, offset) => {
    return JSON.stringify({ filters, limit, offset });
  }, []);

  // Fonction de récupération des livres avec cache
  const fetchBooks = useCallback(async (newFilters = {}, newOffset = 0, append = false) => {
    const cacheKey = generateCacheKey(newFilters, pagination.limit, newOffset);
    
    // Vérification du cache
    const cached = cacheRef.current.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < PAGINATION_CONFIG.CACHE_TTL) {
      setBooks(append ? [...books, ...cached.data.items] : cached.data.items);
      setPagination(prev => ({
        ...prev,
        total: cached.data.total,
        offset: newOffset,
        hasNext: cached.data.has_next,
        hasPrevious: cached.data.has_previous
      }));
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams({
        limit: pagination.limit.toString(),
        offset: newOffset.toString(),
        ...newFilters
      });

      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/books/paginated?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      // Mise en cache
      cacheRef.current.set(cacheKey, {
        data,
        timestamp: Date.now()
      });

      setBooks(append ? [...books, ...data.items] : data.items);
      setPagination(prev => ({
        ...prev,
        total: data.total,
        offset: newOffset,
        hasNext: data.has_next,
        hasPrevious: data.has_previous
      }));

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [books, pagination.limit, generateCacheKey]);

  // Chargement de la page suivante
  const loadNextPage = useCallback(() => {
    if (!pagination.hasNext || loading) return;
    fetchBooks(filters, pagination.offset + pagination.limit, true);
  }, [fetchBooks, filters, pagination.hasNext, pagination.offset, pagination.limit, loading]);

  // Chargement de la page précédente
  const loadPreviousPage = useCallback(() => {
    if (!pagination.hasPrevious || loading) return;
    const newOffset = Math.max(0, pagination.offset - pagination.limit);
    fetchBooks(filters, newOffset, false);
  }, [fetchBooks, filters, pagination.hasPrevious, pagination.offset, pagination.limit, loading]);

  // Rechargement avec nouveaux filtres
  const reloadWithFilters = useCallback((newFilters) => {
    fetchBooks(newFilters, 0, false);
  }, [fetchBooks]);

  // Invalidation du cache
  const invalidateCache = useCallback(() => {
    cacheRef.current.clear();
  }, []);

  return {
    books,
    loading,
    error,
    pagination,
    loadNextPage,
    loadPreviousPage,
    reloadWithFilters,
    invalidateCache
  };
};

// Hook pour les suggestions de recherche avec debounce
export const useSearchSuggestions = (debounceDelay = PAGINATION_CONFIG.DEBOUNCE_DELAY) => {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Cache pour les suggestions
  const suggestionsCache = useRef(new Map());
  const debounceTimer = useRef(null);

  const fetchSuggestions = useCallback(async (query) => {
    if (!query || query.length < 2) {
      setSuggestions([]);
      return;
    }

    // Vérification du cache
    const cached = suggestionsCache.current.get(query);
    if (cached && Date.now() - cached.timestamp < PAGINATION_CONFIG.CACHE_TTL) {
      setSuggestions(cached.data);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/search/suggestions?q=${encodeURIComponent(query)}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        }
      );

      if (!response.ok) {
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      // Mise en cache
      suggestionsCache.current.set(query, {
        data: data.suggestions,
        timestamp: Date.now()
      });

      setSuggestions(data.suggestions);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const debouncedFetch = useCallback((query) => {
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    debounceTimer.current = setTimeout(() => {
      fetchSuggestions(query);
    }, debounceDelay);
  }, [fetchSuggestions, debounceDelay]);

  // Nettoyage du timer au démontage
  useEffect(() => {
    return () => {
      if (debounceTimer.current) {
        clearTimeout(debounceTimer.current);
      }
    };
  }, []);

  return {
    suggestions,
    loading,
    error,
    fetchSuggestions: debouncedFetch
  };
};

// Hook pour le scroll infini
export const useInfiniteScroll = (loadMore, hasMore) => {
  const [isFetching, setIsFetching] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      if (
        window.innerHeight + document.documentElement.scrollTop !==
        document.documentElement.offsetHeight
      ) {
        return;
      }

      if (hasMore && !isFetching) {
        setIsFetching(true);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [hasMore, isFetching]);

  useEffect(() => {
    if (!isFetching) return;

    const fetchMoreData = async () => {
      await loadMore();
      setIsFetching(false);
    };

    fetchMoreData();
  }, [isFetching, loadMore]);

  return [isFetching, setIsFetching];
};

// Hook pour la mémorisation des statistiques
export const useStatsMemo = (user) => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Mémorisation des statistiques calculées
  const memoizedStats = useMemo(() => {
    if (!stats) return null;

    return {
      totalBooks: stats.total_books || 0,
      completedBooks: stats.completed_books || 0,
      readingBooks: stats.reading_books || 0,
      toReadBooks: stats.to_read_books || 0,
      completionRate: stats.total_books > 0 ? 
        Math.round((stats.completed_books / stats.total_books) * 100) : 0,
      categories: stats.categories || {},
      topAuthors: Object.entries(stats.categories || {})
        .sort(([,a], [,b]) => b - a)
        .slice(0, 5)
    };
  }, [stats]);

  const fetchStats = useCallback(async () => {
    if (!user) return;

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/stats`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setStats(data);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  return {
    stats: memoizedStats,
    loading,
    error,
    refetch: fetchStats
  };
};

// Hook pour l'optimisation des re-rendus
export const useOptimizedCallback = (callback, dependencies) => {
  return useCallback(callback, dependencies);
};

// Hook pour l'optimisation des valeurs calculées
export const useOptimizedMemo = (factory, dependencies) => {
  return useMemo(factory, dependencies);
};

// Hook pour la gestion du cache global
export const useGlobalCache = () => {
  const cacheRef = useRef(new Map());

  const set = useCallback((key, value, ttl = PAGINATION_CONFIG.CACHE_TTL) => {
    cacheRef.current.set(key, {
      value,
      timestamp: Date.now(),
      ttl
    });
  }, []);

  const get = useCallback((key) => {
    const cached = cacheRef.current.get(key);
    if (!cached) return null;

    if (Date.now() - cached.timestamp > cached.ttl) {
      cacheRef.current.delete(key);
      return null;
    }

    return cached.value;
  }, []);

  const clear = useCallback(() => {
    cacheRef.current.clear();
  }, []);

  const remove = useCallback((key) => {
    cacheRef.current.delete(key);
  }, []);

  return { set, get, clear, remove };
};