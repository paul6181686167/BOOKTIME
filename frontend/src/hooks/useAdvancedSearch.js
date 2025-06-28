import { useState, useMemo, useCallback, useEffect } from 'react';

export const useAdvancedSearch = (books = []) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState('');
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

  // Debounce pour la recherche - attendre 300ms après la dernière frappe
  useEffect(() => {
    const debounceTimer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
    }, 300);

    return () => clearTimeout(debounceTimer);
  }, [searchTerm]);

  // Logique de filtrage avancée utilisant le terme de recherche avec debounce
  const filteredBooks = useMemo(() => {
    if (!books || books.length === 0) return [];

    return books.filter(book => {
      // Filtrage par terme de recherche (avec debounce)
      if (debouncedSearchTerm) {
        const term = debouncedSearchTerm.toLowerCase();
        const matchesTitle = book.title?.toLowerCase().includes(term);
        const matchesAuthor = book.author?.toLowerCase().includes(term);
        const matchesSaga = book.saga?.toLowerCase().includes(term);
        const matchesDescription = book.description?.toLowerCase().includes(term);
        const matchesGenre = book.genre?.toLowerCase().includes(term);
        const matchesPublisher = book.publisher?.toLowerCase().includes(term);
        const matchesIsbn = book.isbn?.toLowerCase().includes(term);

        if (!matchesTitle && !matchesAuthor && !matchesSaga && !matchesDescription && !matchesGenre && !matchesPublisher && !matchesIsbn) {
          return false;
        }
      }

      // Filtrage par catégorie
      if (filters.category && book.category !== filters.category) {
        return false;
      }

      // Filtrage par statut
      if (filters.status && book.status !== filters.status) {
        return false;
      }

      // Filtrage par auteur
      if (filters.author && !book.author?.toLowerCase().includes(filters.author.toLowerCase())) {
        return false;
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
    const total = books.length;
    const filtered = filteredBooks.length;
    const hasActiveFilters = searchTerm !== '' || Object.values(filters).some(value => value !== '' && value !== false);
    
    return {
      total,
      filtered,
      hasActiveFilters,
      hiddenCount: hasActiveFilters ? total - filtered : 0
    };
  }, [books.length, filteredBooks.length, searchTerm, filters]);

  // Suggestions pour l'autocomplétion
  const getSearchSuggestions = (term) => {
    if (!term || term.length < 2) return [];

    const suggestions = new Set();
    const lowerTerm = term.toLowerCase();

    books.forEach(book => {
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