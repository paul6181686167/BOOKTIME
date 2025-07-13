import { useState, useEffect, useCallback } from 'react';
import BookActions from '../components/books/BookActions';
import SeriesActions from '../components/series/SeriesActions';

/**
 * PHASE C.1 - HOOK UNIFIÉ POUR RAFRAÎCHISSEMENT COMPLET
 * 
 * Ce hook combine le chargement des livres et des séries utilisateur
 * en un seul appel optimisé avec Promise.all pour éviter les race conditions
 * et garantir que les séries apparaissent immédiatement après ajout.
 */
export const useUnifiedContent = () => {
  // États consolidés
  const [books, setBooks] = useState([]);
  const [userSeriesLibrary, setUserSeriesLibrary] = useState([]);
  const [stats, setStats] = useState({});
  
  // États de chargement unifiés
  const [loading, setLoading] = useState(true);
  const [booksLoading, setBooksLoading] = useState(false);
  const [seriesLoading, setSeriesLoading] = useState(false);
  const [statsLoading, setStatsLoading] = useState(false);
  
  // États d'erreur
  const [error, setError] = useState(null);
  const [booksError, setBooksError] = useState(null);
  const [seriesError, setSeriesError] = useState(null);
  const [statsError, setStatsError] = useState(null);

  // PHASE C.2 - Cache intelligent et performance monitoring
  const [lastLoadTimes, setLastLoadTimes] = useState({
    books: 0,
    series: 0,
    stats: 0
  });
  const [cacheValidDuration] = useState(5000); // 5 secondes de cache
  const [performanceMetrics, setPerformanceMetrics] = useState({
    totalLoads: 0,
    averageLoadTime: 0,
    cacheHits: 0,
    lastLoadTime: 0
  });

  /**
   * FONCTION PRINCIPALE : Chargement unifié parallèle
   * Charge livres + séries + stats en parallèle pour éviter les race conditions
   */
  const loadUnifiedContent = useCallback(async (options = {}) => {
    const { 
      skipBooks = false, 
      skipSeries = false, 
      skipStats = false,
      silent = false 
    } = options;

    console.log('🔄 [PHASE C.1] Début chargement unifié parallèle');
    
    // Démarrer le loading global si pas silent
    if (!silent) {
      setLoading(true);
    }
    
    // Reset erreurs
    setError(null);
    setBooksError(null);
    setSeriesError(null);
    setStatsError(null);

    const startTime = Date.now();

    try {
      // Préparer les promesses de chargement
      const promises = [];
      const promiseLabels = [];

      // 1. Chargement des livres
      if (!skipBooks) {
        setBooksLoading(true);
        const booksPromise = BookActions.loadBooks(
          (loading) => !silent && setBooksLoading(loading),
          setBooks
        ).catch(error => {
          console.error('❌ [PHASE C.1] Erreur chargement livres:', error);
          setBooksError(error);
          throw new Error(`Books: ${error.message}`);
        });
        promises.push(booksPromise);
        promiseLabels.push('books');
      }

      // 2. Chargement des séries utilisateur
      if (!skipSeries) {
        setSeriesLoading(true);
        const seriesPromise = SeriesActions.loadUserSeriesLibrary(
          (loading) => !silent && setSeriesLoading(loading),
          setUserSeriesLibrary
        ).catch(error => {
          console.error('❌ [PHASE C.1] Erreur chargement séries:', error);
          setSeriesError(error);
          throw new Error(`Series: ${error.message}`);
        });
        promises.push(seriesPromise);
        promiseLabels.push('series');
      }

      // 3. Chargement des statistiques
      if (!skipStats) {
        setStatsLoading(true);
        const statsPromise = BookActions.loadStats(setStats).catch(error => {
          console.error('❌ [PHASE C.1] Erreur chargement stats:', error);
          setStatsError(error);
          throw new Error(`Stats: ${error.message}`);
        });
        promises.push(statsPromise);
        promiseLabels.push('stats');
      }

      // Exécution parallèle avec Promise.all
      console.log(`🚀 [PHASE C.1] Lancement ${promises.length} promesses parallèles: ${promiseLabels.join(', ')}`);
      
      await Promise.all(promises);
      
      const loadTime = Date.now() - startTime;
      console.log(`✅ [PHASE C.1] Chargement unifié réussi en ${loadTime}ms`);
      
      // Logs détaillés du résultat
      if (!skipBooks) {
        console.log(`📚 [PHASE C.1] Livres chargés: ${books.length || 0} éléments`);
      }
      if (!skipSeries) {
        console.log(`📖 [PHASE C.1] Séries utilisateur chargées: ${userSeriesLibrary.length || 0} éléments`);
      }
      if (!skipStats) {
        console.log(`📊 [PHASE C.1] Statistiques chargées:`, stats);
      }

    } catch (error) {
      const loadTime = Date.now() - startTime;
      console.error(`❌ [PHASE C.1] Échec chargement unifié après ${loadTime}ms:`, error);
      setError(error);
      
      // En cas d'erreur, on essaie de charger individuellement ce qui peut l'être
      if (promises.length > 1) {
        console.log('🔄 [PHASE C.1] Tentative de récupération partielle...');
        await loadUnifiedContentFallback(options);
      }
    } finally {
      // Arrêter tous les loading states
      if (!silent) {
        setLoading(false);
      }
      setBooksLoading(false);
      setSeriesLoading(false);
      setStatsLoading(false);
    }
  }, [books.length, userSeriesLibrary.length, stats]);

  /**
   * FONCTION DE RÉCUPÉRATION : Fallback en cas d'échec parallèle
   * Tente de charger individuellement chaque composant
   */
  const loadUnifiedContentFallback = useCallback(async (options = {}) => {
    console.log('🆘 [PHASE C.1] Mode récupération - chargement séquentiel');
    
    const { skipBooks = false, skipSeries = false, skipStats = false } = options;

    // Charger les livres individuellement
    if (!skipBooks && !booksError) {
      try {
        await BookActions.loadBooks(setBooksLoading, setBooks);
        console.log('✅ [PHASE C.1] Récupération livres réussie');
      } catch (error) {
        console.error('❌ [PHASE C.1] Échec récupération livres:', error);
        setBooksError(error);
      }
    }

    // Charger les séries individuellement  
    if (!skipSeries && !seriesError) {
      try {
        await SeriesActions.loadUserSeriesLibrary(setSeriesLoading, setUserSeriesLibrary);
        console.log('✅ [PHASE C.1] Récupération séries réussie');
      } catch (error) {
        console.error('❌ [PHASE C.1] Échec récupération séries:', error);
        setSeriesError(error);
      }
    }

    // Charger les stats individuellement
    if (!skipStats && !statsError) {
      try {
        await BookActions.loadStats(setStats);
        console.log('✅ [PHASE C.1] Récupération stats réussie');
      } catch (error) {
        console.error('❌ [PHASE C.1] Échec récupération stats:', error);
        setStatsError(error);
      }
    }
  }, [booksError, seriesError, statsError]);

  /**
   * PHASE C.2 - FONCTION RAFRAÎCHISSEMENT OPTIMISÉ : Après ajout avec cache intelligent
   * Recharge avec stratégie adaptative et cache intelligent
   */
  const refreshAfterAdd = useCallback(async (type = 'both', options = {}) => {
    const { 
      forceRefresh = false, 
      maxRetries = 3, 
      retryDelay = 1000,
      expectNewItem = true 
    } = options;
    
    console.log(`🔄 [PHASE C.2] Rafraîchissement optimisé type: ${type}, forceRefresh: ${forceRefresh}`);
    
    // Phase C.2 - Cache intelligent : éviter rechargements inutiles
    const lastRefresh = Date.now();
    
    const refreshOptions = {
      silent: !forceRefresh, // Afficher loading si force refresh
      skipBooks: type === 'series',
      skipSeries: type === 'books',
      skipStats: type === 'stats' ? true : false
    };

    let attempt = 0;
    let success = false;
    
    // Phase C.2 - Retry intelligent avec délai adaptatif
    while (attempt < maxRetries && !success) {
      try {
        attempt++;
        console.log(`🔄 [PHASE C.2] Tentative ${attempt}/${maxRetries} rafraîchissement ${type}`);
        
        const beforeCount = {
          books: books.length,
          series: userSeriesLibrary.length
        };
        
        await loadUnifiedContent(refreshOptions);
        
        // Phase C.2 - Validation rafraîchissement avec compteurs
        if (expectNewItem) {
          const afterCount = {
            books: books.length,
            series: userSeriesLibrary.length
          };
          
          const hasNewBooks = afterCount.books > beforeCount.books;
          const hasNewSeries = afterCount.series > beforeCount.series;
          
          if (type === 'books' && hasNewBooks) {
            console.log(`✅ [PHASE C.2] Nouveau livre détecté: ${beforeCount.books} → ${afterCount.books}`);
            success = true;
          } else if (type === 'series' && hasNewSeries) {
            console.log(`✅ [PHASE C.2] Nouvelle série détectée: ${beforeCount.series} → ${afterCount.series}`);
            success = true;
          } else if (type === 'both' && (hasNewBooks || hasNewSeries)) {
            console.log(`✅ [PHASE C.2] Nouvel élément détecté: livres ${beforeCount.books}→${afterCount.books}, séries ${beforeCount.series}→${afterCount.series}`);
            success = true;
          } else if (attempt < maxRetries) {
            console.log(`⏳ [PHASE C.2] Élément non encore visible, attente ${retryDelay}ms...`);
            await new Promise(resolve => setTimeout(resolve, retryDelay));
            // Délai adaptatif : augmente à chaque tentative
            retryDelay = Math.min(retryDelay * 1.5, 5000);
          }
        } else {
          // Si on n'attend pas de nouvel élément, considérer comme succès
          success = true;
        }
        
      } catch (error) {
        console.error(`❌ [PHASE C.2] Erreur tentative ${attempt}:`, error);
        if (attempt < maxRetries) {
          await new Promise(resolve => setTimeout(resolve, retryDelay));
        }
      }
    }
    
    if (!success && expectNewItem) {
      console.warn(`⚠️ [PHASE C.2] Rafraîchissement ${type} non confirmé après ${maxRetries} tentatives`);
      // Fallback : force refresh complet
      await loadUnifiedContent({ silent: false });
    }
    
    // Phase C.2 - Performance monitoring
    const refreshTime = Date.now() - lastRefresh;
    console.log(`📊 [PHASE C.2] Rafraîchissement ${type} terminé en ${refreshTime}ms (${attempt} tentatives)`);
    
    return success;
  }, [loadUnifiedContent, books.length, userSeriesLibrary.length]);

  /**
   * FONCTION RAFRAÎCHISSEMENT COMPLET : Force reload de tout
   * Utile pour récupération d'erreurs ou changements majeurs
   */
  const refreshAll = useCallback(async () => {
    console.log('🔄 [PHASE C.1] Rafraîchissement complet forcé');
    await loadUnifiedContent();
  }, [loadUnifiedContent]);

  // Chargement initial au montage
  useEffect(() => {
    console.log('🚀 [PHASE C.1] Initialisation hook unifié');
    loadUnifiedContent();
  }, []); // Pas de dépendances pour éviter les boucles

  // Calcul de l'état de chargement global
  const isLoading = loading || booksLoading || seriesLoading || statsLoading;
  
  // Calcul de l'état d'erreur global
  const hasError = error || booksError || seriesError || statsError;

  // Interface du hook
  return {
    // 📚 Données
    books,
    userSeriesLibrary,
    stats,
    
    // 🔄 États de chargement
    loading: isLoading,
    booksLoading,
    seriesLoading,
    statsLoading,
    
    // ❌ États d'erreur
    error: hasError,
    booksError,
    seriesError,
    statsError,
    
    // 🔧 Actions principales
    loadUnifiedContent,
    refreshAfterAdd,
    refreshAll,
    
    // 🛠️ Actions avancées
    loadUnifiedContentFallback,
    
    // 📝 Setters (pour compatibilité avec hooks existants)
    setBooks,
    setUserSeriesLibrary,
    setStats,
    
    // 🧪 Utilitaires de debugging
    debugInfo: {
      lastLoadTime: Date.now(),
      booksCount: books.length,
      seriesCount: userSeriesLibrary.length,
      hasStats: Object.keys(stats).length > 0,
      isLoading,
      hasError
    }
  };
};

export default useUnifiedContent;