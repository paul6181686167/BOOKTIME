import { useState, useMemo, useCallback, useEffect } from 'react';

export const useAdvancedSearch = (books = []) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');
  const [groupedResults, setGroupedResults] = useState([]);
  const [isGroupedSearch, setIsGroupedSearch] = useState(false);
  const [filters, setFilters] = useState({
    category: '',
    status: '',
    author: '',
    saga: '',
    yearFrom: '',
    yearTo: '',
    minRating: '',
    hasReview: false
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
      setIsGroupedSearch(false);
      return;
    }

    try {
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
        setIsGroupedSearch(true);
      } else {
        setGroupedResults([]);
        setIsGroupedSearch(false);
      }
    } catch (error) {
      console.error('Erreur lors de la recherche groupée:', error);
      setGroupedResults([]);
      setIsGroupedSearch(false);
    }
  }, [backendUrl]);

  // Déclencher la recherche groupée quand le terme change
  useEffect(() => {
    if (debouncedSearchTerm && debouncedSearchTerm.length >= 2) {
      performGroupedSearch(debouncedSearchTerm, filters.category);
    } else {
      setGroupedResults([]);
      setIsGroupedSearch(false);
    }
  }, [debouncedSearchTerm, filters.category, performGroupedSearch]);

  // Logique de filtrage classique (utilisée quand pas de recherche groupée active)
  const filteredBooks = useMemo(() => {
    // Vérification renforcée : s'assurer que books est toujours un array
    if (!books || !Array.isArray(books) || books.length === 0) {
      return [];
    }

    return books.filter(book => {
      // Filtrage par terme de recherche (avec debounce)
      if (debouncedSearchTerm) {
        const term = debouncedSearchTerm.toLowerCase();
        const matchesTitle = book.title?.toLowerCase().includes(term);
        const matchesAuthor = book.author?.toLowerCase().includes(term);
        const matchesAuthors = book.authors?.some(author => author?.toLowerCase().includes(term)); // 🔍 NOUVEAU: Recherche dans tous les auteurs
        const matchesSaga = book.saga?.toLowerCase().includes(term);
        const matchesDescription = book.description?.toLowerCase().includes(term);
        const matchesGenre = book.genre?.toLowerCase().includes(term);
        const matchesPublisher = book.publisher?.toLowerCase().includes(term);
        const matchesIsbn = book.isbn?.toLowerCase().includes(term);

        if (!matchesTitle && !matchesAuthor && !matchesAuthors && !matchesSaga && !matchesDescription && !matchesGenre && !matchesPublisher && !matchesIsbn) {
          return false;
        }
      }

      // Filtrage par catégorie - MISE À JOUR SESSION 75 : Support Romans graphiques (BD + Manga)
      if (filters.category) {
        if (filters.category === 'graphic_novels') {
          // Pour Romans graphiques, inclure BD et Manga
          if (book.category !== 'bd' && book.category !== 'manga') {
            return false;
          }
        } else {
          // Pour les autres catégories, filtrage normal
          if (book.category !== filters.category) {
            return false;
          }
        }
      }

      // Filtrage par statut
      if (filters.status && book.status !== filters.status) {
        return false;
      }

      // Filtrage par auteur - 🔍 CORRECTION: Support des cartes de série avec multiple auteurs
      if (filters.author) {
        const authorFilter = filters.author.toLowerCase();
        const matchesMainAuthor = book.author?.toLowerCase().includes(authorFilter);
        const matchesAuthorsArray = book.authors?.some(author => author?.toLowerCase().includes(authorFilter));
        
        if (!matchesMainAuthor && !matchesAuthorsArray) {
          return false;
        }
      }

      // Filtrage par saga
      if (filters.saga && !book.saga?.toLowerCase().includes(filters.saga.toLowerCase())) {
        return false;
      }

      // Filtrage par année
      if (filters.yearFrom && book.publication_year && book.publication_year < parseInt(filters.yearFrom)) {
        return false;
      }
      if (filters.yearTo && book.publication_year && book.publication_year > parseInt(filters.yearTo)) {
        return false;
      }

      // Filtrage par note minimale
      if (filters.minRating && (!book.rating || book.rating < parseInt(filters.minRating))) {
        return false;
      }

      // Filtrage par présence de critique
      if (filters.hasReview && (!book.review || book.review.trim() === '')) {
        return false;
      }

      return true;
    });
  }, [books, debouncedSearchTerm, filters]);

  // Statistiques de recherche
  const searchStats = useMemo(() => {
    // Vérification renforcée pour books
    const booksArray = Array.isArray(books) ? books : [];
    const filteredBooksArray = Array.isArray(filteredBooks) ? filteredBooks : [];
    
    const total = booksArray.length;
    const filtered = filteredBooksArray.length;
    const hasActiveFilters = searchTerm !== '' || Object.values(filters).some(value => value !== '' && value !== false);
    
    return {
      total,
      filtered,
      hasActiveFilters,
      hiddenCount: hasActiveFilters ? total - filtered : 0
    };
  }, [books, filteredBooks, searchTerm, filters]);

  // Suggestions pour l'autocomplétion
  const getSearchSuggestions = (term) => {
    if (!term || term.length < 2) return [];
    
    // Vérification renforcée pour books
    const booksArray = Array.isArray(books) ? books : [];
    if (booksArray.length === 0) return [];

    const suggestions = new Set();
    const lowerTerm = term.toLowerCase();

    booksArray.forEach(book => {
      // Suggestions de titres
      if (book.title?.toLowerCase().includes(lowerTerm)) {
        suggestions.add({
          type: 'title',
          value: book.title,
          category: 'Livres'
        });
      }

      // Suggestions d'auteurs
      if (book.author?.toLowerCase().includes(lowerTerm)) {
        suggestions.add({
          type: 'author',
          value: book.author,
          category: 'Auteurs'
        });
      }

      // Suggestions de sagas
      if (book.saga?.toLowerCase().includes(lowerTerm)) {
        suggestions.add({
          type: 'saga',
          value: book.saga,
          category: 'Sagas'
        });
      }

      // Suggestions de genres
      if (book.genre) {
        book.genre.forEach(genre => {
          if (genre.toLowerCase().includes(lowerTerm)) {
            suggestions.add({
              type: 'genre',
              value: genre,
              category: 'Genres'
            });
          }
        });
      }
    });

    return Array.from(suggestions).slice(0, 8);
  };

  // Fonction pour nettoyer la recherche
  const clearSearch = () => {
    setSearchTerm('');
    setFilters({
      category: '',
      status: '',
      author: '',
      saga: '',
      yearFrom: '',
      yearTo: '',
      minRating: '',
      hasReview: false
    });
  };

  // Fonction pour appliquer un filtre rapide
  const applyQuickFilter = (type, value) => {
    switch (type) {
      case 'category':
        setFilters(prev => ({ ...prev, category: value }));
        break;
      case 'status':
        setFilters(prev => ({ ...prev, status: value }));
        break;
      case 'author':
        setFilters(prev => ({ ...prev, author: value }));
        setSearchTerm('');
        break;
      case 'saga':
        setFilters(prev => ({ ...prev, saga: value }));
        setSearchTerm('');
        break;
      default:
        setSearchTerm(value);
    }
  };

  return {
    searchTerm,
    setSearchTerm,
    filters,
    setFilters,
    filteredBooks,
    searchStats,
    getSearchSuggestions,
    clearSearch,
    applyQuickFilter
  };
};