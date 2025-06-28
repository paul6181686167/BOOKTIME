import { useState, useCallback, useEffect } from 'react';

export const useGroupedSearch = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');
  const [groupedResults, setGroupedResults] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchStats, setSearchStats] = useState({
    total_books: 0,
    total_sagas: 0,
    search_term: ''
  });

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  // Debounce pour la recherche - attendre 300ms après la dernière frappe
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
    }, 300);

    return () => clearTimeout(debounceTimer);
  }, [searchTerm]);

  // Fonction pour recherche groupée via API
  const performGroupedSearch = useCallback(async (term, category = '') => {
    if (!term || term.length < 2) {
      setGroupedResults([]);
      setSearchStats({ total_books: 0, total_sagas: 0, search_term: '' });
      return;
    }

    try {
      setIsLoading(true);
      const token = localStorage.getItem('token');
      const params = new URLSearchParams({
        q: term,
        ...(category && { category })
      });

      const response = await fetch(`${backendUrl}/api/books/search-grouped?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setGroupedResults(data.results || []);
        setSearchStats({
          total_books: data.total_books || 0,
          total_sagas: data.total_sagas || 0,
          search_term: data.search_term || term
        });
      } else {
        setGroupedResults([]);
        setSearchStats({ total_books: 0, total_sagas: 0, search_term: term });
      }
    } catch (error) {
      console.error('Erreur lors de la recherche groupée:', error);
      setGroupedResults([]);
      setSearchStats({ total_books: 0, total_sagas: 0, search_term: term });
    } finally {
      setIsLoading(false);
    }
  }, [backendUrl]);

  // Déclencher la recherche groupée quand le terme change
  useEffect(() => {
    if (debouncedSearchTerm && debouncedSearchTerm.length >= 2) {
      performGroupedSearch(debouncedSearchTerm);
    } else {
      setGroupedResults([]);
      setSearchStats({ total_books: 0, total_sagas: 0, search_term: '' });
    }
  }, [debouncedSearchTerm, performGroupedSearch]);

  // Fonction pour nettoyer la recherche
  const clearSearch = useCallback(() => {
    setSearchTerm('');
    setGroupedResults([]);
    setSearchStats({ total_books: 0, total_sagas: 0, search_term: '' });
  }, []);

  return {
    searchTerm,
    setSearchTerm,
    groupedResults,
    isLoading,
    searchStats,
    clearSearch,
    hasResults: groupedResults.length > 0
  };
};