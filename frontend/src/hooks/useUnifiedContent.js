import { useState, useEffect, useCallback } from 'react';
import BookActions from '../components/books/BookActions';
import SeriesActions from '../components/series/SeriesActions';
import { API_BASE_URL } from '../config/environment';
import { scheduleLibraryMetaEnrichment } from '../services/libraryMetaEnrichment';

export const useUnifiedContent = () => {
  const [books, setBooks] = useState([]);
  const [userSeriesLibrary, setUserSeriesLibrary] = useState([]);
  const [readingPreferences, setReadingPreferences] = useState({});
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Cache par type pour éviter les rechargements inutiles
  const [lastLoadTimes, setLastLoadTimes] = useState({ books: 0, series: 0, stats: 0 });
  const CACHE_DURATION = 5000; // 5 secondes

  const shouldRefresh = useCallback((type, forceRefresh = false) => {
    if (forceRefresh) return true;
    return Date.now() - (lastLoadTimes[type] || 0) > CACHE_DURATION;
  }, [lastLoadTimes]);

  const loadUnifiedContent = useCallback(async (options = {}) => {
    const {
      skipBooks = false,
      skipSeries = false,
      skipStats = false,
      silent = false,
      forceRefresh = false
    } = options;

    const doBooks = !skipBooks && shouldRefresh('books', forceRefresh);
    const doSeries = !skipSeries && shouldRefresh('series', forceRefresh);
    const doStats = !skipStats && shouldRefresh('stats', forceRefresh);

    if (!doBooks && !doSeries && !doStats) return;

    if (!silent) setLoading(true);
    setError(null);

    const promises = [];

    if (doBooks) {
      promises.push(
        BookActions.loadBooks(() => {}, setBooks)
          .then(() => setLastLoadTimes(prev => ({ ...prev, books: Date.now() })))
          .catch(err => { throw new Error(`Books: ${err.message}`); })
      );
    }

    if (doSeries) {
      promises.push(
        SeriesActions.loadUserSeriesLibrary(() => {}, setUserSeriesLibrary)
          .then(() => setLastLoadTimes(prev => ({ ...prev, series: Date.now() })))
          .catch(err => { throw new Error(`Series: ${err.message}`); })
      );
    }

    if (doStats) {
      promises.push(
        BookActions.loadStats(setStats)
          .then(() => setLastLoadTimes(prev => ({ ...prev, stats: Date.now() })))
          .catch(err => { throw new Error(`Stats: ${err.message}`); })
      );
    }

    // Préférences de lecture
    promises.push(
      fetch(`${API_BASE_URL || ''}/api/series/reading-preferences`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      })
        .then(r => r.ok ? r.json() : { preferences: {} })
        .then(data => setReadingPreferences(data.preferences || {}))
        .catch(() => setReadingPreferences({}))
    );

    try {
      await Promise.all(promises);
    } catch (err) {
      setError(err);
      // Fallback séquentiel
      try {
        if (!skipBooks) await BookActions.loadBooks(() => {}, setBooks).catch(() => {});
        if (!skipSeries) await SeriesActions.loadUserSeriesLibrary(() => {}, setUserSeriesLibrary).catch(() => {});
        if (!skipStats) await BookActions.loadStats(setStats).catch(() => {});
      } catch (_) {}
    } finally {
      if (!silent) setLoading(false);
    }
  }, [shouldRefresh]);

  const refreshAfterAdd = useCallback(async (type = 'both', options = {}) => {
    const { maxRetries = 2, retryDelay = 1000 } = options;
    const refreshOptions = {
      forceRefresh: true,
      silent: false,
      skipBooks: type === 'series',
      skipSeries: type === 'books',
      skipStats: true
    };
    for (let i = 0; i < maxRetries; i++) {
      await loadUnifiedContent(refreshOptions);
      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, retryDelay));
      }
    }
  }, [loadUnifiedContent]);

  const refreshAll = useCallback(async () => {
    await loadUnifiedContent({ forceRefresh: true });
  }, [loadUnifiedContent]);

  useEffect(() => {
    loadUnifiedContent();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Résumé + pages en arrière-plan (sans clic sur la vignette)
  useEffect(() => {
    if (loading) return;
    if (!books.length && !userSeriesLibrary.length) return;
    return scheduleLibraryMetaEnrichment({
      books,
      userSeriesLibrary,
      setBooks,
      setUserSeriesLibrary,
    });
  }, [loading, books, userSeriesLibrary]);

  return {
    books,
    userSeriesLibrary,
    readingPreferences,
    stats,
    loading,
    error,
    loadUnifiedContent,
    refreshAfterAdd,
    refreshAll,
    setBooks,
    setUserSeriesLibrary,
    setStats,
  };
};

export default useUnifiedContent;
