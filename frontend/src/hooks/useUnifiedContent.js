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
   * FONCTION RAFRAÎCHISSEMENT RAPIDE : Pour après ajout de livre/série
   * Recharge uniquement ce qui est nécessaire
   */
  const refreshAfterAdd = useCallback(async (type = 'both') => {
    console.log(`🔄 [PHASE C.1] Rafraîchissement rapide type: ${type}`);
    
    const options = {
      silent: true, // Pas de loading global pour éviter le flicker
      skipBooks: type === 'series',
      skipSeries: type === 'books',
      skipStats: false // Toujours recharger les stats
    };

    await loadUnifiedContent(options);
  }, [loadUnifiedContent]);

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