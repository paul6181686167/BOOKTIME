import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { 
  MagnifyingGlassIcon, 
  AdjustmentsHorizontalIcon,
  XMarkIcon,
  BookOpenIcon,
  UserIcon,
  ClockIcon,
  BookmarkIcon
} from '@heroicons/react/24/outline';

const UnifiedSearchBar = React.memo(({ 
  searchTerm, 
  onSearchChange, 
  books = [], 
  onOpenLibrarySearch,
  filters,
  onFiltersChange,
  className = '',
  isCompact = false // Mode compact pour le header
}) => {
  const navigate = useNavigate();
  const [showFilters, setShowFilters] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [recentSearches, setRecentSearches] = useState([]);
  const [universalResults, setUniversalResults] = useState([]);
  const [localSearchTerm, setLocalSearchTerm] = useState(searchTerm || '');

  const searchInputRef = useRef(null);
  const suggestionsRef = useRef(null);
  const filtersRef = useRef(null);
  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  // Synchroniser l'état local avec la prop searchTerm seulement quand elle change
  useEffect(() => {
    setLocalSearchTerm(searchTerm || '');
  }, [searchTerm]);

  // Charger les recherches récentes
  useEffect(() => {
    const saved = localStorage.getItem('booktime-recent-searches');
    if (saved) {
      try {
        setRecentSearches(JSON.parse(saved));
      } catch (e) {
        console.error('Erreur lors du chargement des recherches récentes:', e);
      }
    }
  }, []);

  // Recherche universelle Open Library uniquement sur demande explicite
  const searchUniversal = useCallback(async (query) => {
    if (!query.trim() || query.length < 3) {
      setUniversalResults([]);
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${backendUrl}/api/openlibrary/search?q=${encodeURIComponent(query)}&limit=5`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setUniversalResults(data.books.slice(0, 3));
      }
    } catch (error) {
      console.error('Erreur recherche universelle:', error);
    }
  }, [backendUrl]);

  // Supprimer le débounce automatique - la recherche se fait uniquement sur Entrée
  // useEffect(() => {
  //   const timer = setTimeout(() => {
  //     if (localSearchTerm && showSuggestions) {
  //       searchUniversal(localSearchTerm);
  //     }
  //   }, 500);
  //
  //   return () => clearTimeout(timer);
  // }, [localSearchTerm, showSuggestions, searchUniversal]);

  // Sauvegarder les recherches récentes
  const saveRecentSearch = useCallback((term) => {
    if (!term.trim() || term.length < 2) return;
    
    const newRecentSearches = [
      term,
      ...recentSearches.filter(search => search !== term)
    ].slice(0, 5);
    
    setRecentSearches(newRecentSearches);
    localStorage.setItem('booktime-recent-searches', JSON.stringify(newRecentSearches));
  }, [recentSearches]);

  // Gérer les changements d'input
  const handleInputChange = useCallback((e) => {
    const value = e.target.value;
    setLocalSearchTerm(value);
    onSearchChange(value); // Remettre la synchronisation pour permettre l'écriture
    
    if (value.length >= 2) {
      setShowSuggestions(true);
    } else {
      setShowSuggestions(false);
    }
  }, [onSearchChange]);

  // Déclencher la recherche
  const triggerSearch = useCallback(() => {
    const searchTerm = localSearchTerm.trim();
    if (searchTerm) {
      console.log('🔍 Déclenchement recherche avec:', searchTerm);
      alert('🔍 Recherche déclenchée avec: ' + searchTerm); // Alert temporaire pour debug
      saveRecentSearch(searchTerm);
      onOpenLibrarySearch(searchTerm);
      setShowSuggestions(false);
      // Ne pas effacer le terme de recherche pour que l'utilisateur puisse voir ce qu'il a cherché
    } else {
      console.log('⚠️ Terme de recherche vide, pas de recherche lancée');
      alert('⚠️ Terme de recherche vide!'); // Alert temporaire pour debug
    }
  }, [localSearchTerm, saveRecentSearch, onOpenLibrarySearch]);

  // Générer les suggestions locales
  const memoizedSuggestions = useMemo(() => {
    if (!localSearchTerm || localSearchTerm.length < 2) return [];

    const term = localSearchTerm.toLowerCase();
    const bookSuggestions = [];
    const authorSuggestions = new Set();
    const sagaSuggestions = new Set();

    books.forEach(book => {
      if (book.title && book.title.toLowerCase().includes(term)) {
        bookSuggestions.push({
          type: 'book',
          text: book.title,
          subtitle: `par ${book.author}`,
          icon: BookOpenIcon,
          data: book
        });
      }

      if (book.author && book.author.toLowerCase().includes(term)) {
        authorSuggestions.add({
          type: 'author',
          text: book.author,
          subtitle: 'Auteur',
          icon: UserIcon,
          data: book.author
        });
      }

      if (book.saga && book.saga.toLowerCase().includes(term)) {
        sagaSuggestions.add({
          type: 'saga',
          text: book.saga,
          subtitle: 'Saga',
          icon: BookmarkIcon,
          data: book.saga
        });
      }
    });

    const allSuggestions = [
      ...bookSuggestions.slice(0, 3),
      ...Array.from(authorSuggestions).slice(0, 2),
      ...Array.from(sagaSuggestions).slice(0, 2)
    ].slice(0, 5);

    return allSuggestions;
  }, [localSearchTerm, books]);

  useEffect(() => {
    setSuggestions(memoizedSuggestions);
  }, [memoizedSuggestions]);

  // Gérer la sélection d'une suggestion
  const handleSuggestionClick = (suggestion) => {
    if (suggestion.type === 'book') {
      onSearchChange(suggestion.text);
    } else if (suggestion.type === 'author') {
      onFiltersChange({ ...filters, author: suggestion.data });
      onSearchChange('');
    } else if (suggestion.type === 'saga') {
      onFiltersChange({ ...filters, saga: suggestion.data });
      onSearchChange('');
    }
    
    saveRecentSearch(suggestion.text);
    setShowSuggestions(false);
  };

  // Gérer la sélection d'un résultat universel
  const handleUniversalResultClick = (result) => {
    setLocalSearchTerm(result.title);
    onSearchChange(result.title);
    triggerSearch();
  };

  // Gérer les clics en dehors
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(event.target) &&
          searchInputRef.current && !searchInputRef.current.contains(event.target) &&
          filtersRef.current && !filtersRef.current.contains(event.target)) {
        setShowSuggestions(false);
        setShowFilters(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Effacer la recherche et les filtres
  const clearSearch = useCallback(() => {
    setLocalSearchTerm('');
    onSearchChange('');
    onFiltersChange({
      category: '',
      status: '',
      author: '',
      saga: '',
      yearFrom: '',
      yearTo: '',
      minRating: '',
      hasReview: false
    });
    setShowSuggestions(false);
    setShowFilters(false);
  }, [onSearchChange, onFiltersChange]);

  // Compter les filtres actifs
  const activeFiltersCount = Object.values(filters || {}).filter(value => 
    value !== '' && value !== false
  ).length;

  const hasActiveSearch = localSearchTerm || activeFiltersCount > 0;

  // Classes CSS basées sur le mode compact
  const inputClasses = isCompact 
    ? "block w-full pl-10 pr-16 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-green-500 focus:border-green-500 text-sm"
    : "block w-full pl-10 pr-20 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-green-500 focus:border-green-500 text-sm";

  const containerClasses = isCompact 
    ? "relative flex-1 max-w-lg"
    : "relative w-full max-w-2xl mx-auto";

  return (
    <div className={`${containerClasses} ${className}`}>
      {/* Barre de recherche principale */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <MagnifyingGlassIcon className="h-5 w-5 text-gray-400 dark:text-gray-500" />
        </div>
        
        <input
          ref={searchInputRef}
          type="text"
          value={localSearchTerm}
          onChange={handleInputChange}
          onFocus={() => {
            if (localSearchTerm.length >= 2) {
              setShowSuggestions(true);
            }
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              triggerSearch();
            } else if (e.key === 'Escape') {
              setShowSuggestions(false);
              setShowFilters(false);
            }
          }}
          className={inputClasses}
          placeholder={isCompact ? "Rechercher..." : "Rechercher par titre, auteur, saga..."}
        />

        {/* Boutons d'action */}
        <div className="absolute inset-y-0 right-0 flex items-center space-x-1 pr-3">
          {/* Bouton Effacer */}
          {hasActiveSearch && (
            <button
              onClick={clearSearch}
              className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
              title="Effacer la recherche"
            >
              <XMarkIcon className="h-4 w-4" />
            </button>
          )}

          {/* Bouton Filtres (seulement en mode non-compact) */}
          {!isCompact && (
            <button
              ref={filtersRef}
              onClick={() => setShowFilters(!showFilters)}
              className={`p-1 transition-colors relative ${
                showFilters || activeFiltersCount > 0
                  ? 'text-green-600 dark:text-green-400'
                  : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-300'
              }`}
              title="Filtres avancés"
            >
              <AdjustmentsHorizontalIcon className="h-4 w-4" />
              {activeFiltersCount > 0 && (
                <span className="absolute -top-1 -right-1 bg-green-500 text-white text-xs rounded-full h-4 w-4 flex items-center justify-center text-[10px]">
                  {activeFiltersCount}
                </span>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Dropdown de suggestions */}
      {showSuggestions && (suggestions.length > 0 || recentSearches.length > 0 || universalResults.length > 0) && (
        <div
          ref={suggestionsRef}
          className="absolute z-50 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg max-h-96 overflow-y-auto"
        >
          {/* Suggestions locales */}
          {suggestions.length > 0 && (
            <div className="p-2">
              <div className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2 px-2">
                Dans votre bibliothèque
              </div>
              {suggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="w-full flex items-center space-x-3 px-2 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
                >
                  <suggestion.icon className="h-4 w-4 text-gray-400" />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {suggestion.text}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                      {suggestion.subtitle}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Résultats Open Library */}
          {universalResults.length > 0 && (
            <div className="border-t border-gray-200 dark:border-gray-700 p-2">
              <div className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2 px-2 flex items-center">
                Suggestions de livres
              </div>
              {universalResults.map((result, index) => (
                <button
                  key={index}
                  onClick={() => handleUniversalResultClick(result)}
                  className="w-full flex items-center space-x-3 px-2 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
                >
                  <BookOpenIcon className="h-4 w-4 text-blue-500" />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {result.title}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                      par {result.author}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}

          {/* Recherches récentes */}
          {recentSearches.length > 0 && suggestions.length === 0 && (
            <div className="p-2">
              <div className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2 px-2">
                Recherches récentes
              </div>
              {recentSearches.map((search, index) => (
                <button
                  key={index}
                  onClick={() => {
                    setLocalSearchTerm(search);
                    onSearchChange(search);
                    triggerSearch();
                  }}
                  className="w-full flex items-center space-x-3 px-2 py-2 text-left hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
                >
                  <ClockIcon className="h-4 w-4 text-gray-400" />
                  <div className="text-sm text-gray-900 dark:text-white">
                    {search}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Panel de filtres avancés (seulement en mode non-compact) */}
      {!isCompact && showFilters && (
        <div className="absolute z-40 w-full mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Filtre Catégorie */}
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Catégorie
              </label>
              <select
                value={filters?.category || ''}
                onChange={(e) => onFiltersChange({ ...filters, category: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">Toutes</option>
                <option value="roman">Romans</option>
                <option value="bd">Bande dessinée</option>
                <option value="manga">Mangas</option>
              </select>
            </div>

            {/* Filtre Statut */}
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Statut
              </label>
              <select
                value={filters?.status || ''}
                onChange={(e) => onFiltersChange({ ...filters, status: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="">Tous</option>
                <option value="to_read">À lire</option>
                <option value="reading">En cours</option>
                <option value="completed">Terminés</option>
              </select>
            </div>

            {/* Filtre Auteur */}
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Auteur
              </label>
              <input
                type="text"
                value={filters?.author || ''}
                onChange={(e) => onFiltersChange({ ...filters, author: e.target.value })}
                placeholder="Nom de l'auteur..."
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400"
              />
            </div>
          </div>

          {/* Boutons d'action des filtres */}
          <div className="mt-4 flex justify-between items-center">
            <button
              onClick={() => onFiltersChange({
                category: '',
                status: '',
                author: '',
                saga: '',
                yearFrom: '',
                yearTo: '',
                minRating: '',
                hasReview: false
              })}
              className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              Effacer tous les filtres
            </button>
            
            <button
              onClick={() => setShowFilters(false)}
              className="px-3 py-1 text-sm bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
            >
              Appliquer
            </button>
          </div>
        </div>
      )}
    </div>
  );
});

export default UnifiedSearchBar;