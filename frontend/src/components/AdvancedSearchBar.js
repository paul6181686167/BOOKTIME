import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { 
  MagnifyingGlassIcon, 
  AdjustmentsHorizontalIcon,
  XMarkIcon,
  BookOpenIcon,
  UserIcon,
  TagIcon,
  GlobeAltIcon,
  ClockIcon,
  BookmarkIcon
} from '@heroicons/react/24/outline';

const AdvancedSearchBar = React.memo(({ 
  searchTerm, 
  onSearchChange, 
  books = [], 
  onOpenLibrarySearch,
  filters,
  onFiltersChange,
  className = '' 
}) => {
  const [showFilters, setShowFilters] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [recentSearches, setRecentSearches] = useState([]);
  // État local pour l'input pour éviter les re-rendus
  const [localSearchTerm, setLocalSearchTerm] = useState(searchTerm || '');

  const searchInputRef = useRef(null);
  const suggestionsRef = useRef(null);

  // Synchroniser l'état local avec la prop searchTerm
  useEffect(() => {
    if (searchTerm !== localSearchTerm) {
      setLocalSearchTerm(searchTerm || '');
    }
  }, [searchTerm, localSearchTerm]);

  // Fonction mémorisée pour gérer les changements d'input
  const handleInputChange = useCallback((e) => {
    const value = e.target.value;
    setLocalSearchTerm(value);
    onSearchChange(value);
  }, [onSearchChange]);

  // Charger les recherches récentes depuis localStorage
  useEffect(() => {
    const saved = localStorage.getItem('booktime-recent-searches');
    if (saved) {
      try {
        setRecentSearches(JSON.parse(saved));
      } catch (error) {
        console.error('Erreur lors du chargement des recherches récentes:', error);
      }
    }
  }, []);

  // Sauvegarder les recherches récentes (mémorisé)
  const saveRecentSearch = useCallback((term) => {
    if (!term.trim() || term.length < 2) return;
    
    const newRecentSearches = [
      term,
      ...recentSearches.filter(search => search !== term)
    ].slice(0, 5); // Garder seulement les 5 dernières
    
    setRecentSearches(newRecentSearches);
    localStorage.setItem('booktime-recent-searches', JSON.stringify(newRecentSearches));
  }, [recentSearches]);

  // Générer des suggestions basées sur la recherche et les livres existants (mémorisé)
  const memoizedSuggestions = useMemo(() => {
    if (!localSearchTerm || localSearchTerm.length < 2) {
      return [];
    }

    const term = localSearchTerm.toLowerCase();
    const bookSuggestions = [];
    const authorSuggestions = new Set();
    const sagaSuggestions = new Set();

    books.forEach(book => {
      // Suggestions de livres
      if (book.title.toLowerCase().includes(term)) {
        bookSuggestions.push({
          type: 'book',
          text: book.title,
          subtitle: `par ${book.author}`,
          icon: BookOpenIcon,
          data: book
        });
      }

      // Suggestions d'auteurs
      if (book.author.toLowerCase().includes(term)) {
        authorSuggestions.add({
          type: 'author',
          text: book.author,
          subtitle: 'Auteur',
          icon: UserIcon,
          data: book.author
        });
      }

      // Suggestions de sagas
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
      ...bookSuggestions.slice(0, 4),
      ...Array.from(authorSuggestions).slice(0, 2),
      ...Array.from(sagaSuggestions).slice(0, 2)
    ].slice(0, 6);

    return allSuggestions;
  }, [localSearchTerm, books]);

  // Mettre à jour les suggestions quand les suggestions mémorisées changent
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

  // Gérer les clics en dehors pour fermer les suggestions
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (suggestionsRef.current && !suggestionsRef.current.contains(event.target) &&
          searchInputRef.current && !searchInputRef.current.contains(event.target)) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Gérer les changements de filtres (mémorisé)
  const handleFilterChange = useCallback((key, value) => {
    onFiltersChange({ ...filters, [key]: value });
  }, [filters, onFiltersChange]);

  // Nettoyer tous les filtres (mémorisé)
  const clearAllFilters = useCallback(() => {
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
  }, [onFiltersChange]);

  // Compter les filtres actifs
  const activeFiltersCount = Object.values(filters || {}).filter(value => 
    value !== '' && value !== false
  ).length;

  const statusOptions = [
    { value: '', label: 'Tous les statuts' },
    { value: 'to_read', label: 'À lire', icon: '📚' },
    { value: 'reading', label: 'En cours', icon: '📖' },
    { value: 'completed', label: 'Terminés', icon: '✅' }
  ];

  const categoryOptions = [
    { value: '', label: 'Toutes les catégories' },
    { value: 'roman', label: 'Romans', icon: '📚' },
    { value: 'bd', label: 'Bande dessinée', icon: '🎨' },
    { value: 'manga', label: 'Mangas', icon: '🇯🇵' }
  ];

  const ratingOptions = [
    { value: '', label: 'Toutes les notes' },
    { value: '1', label: '1+ étoiles' },
    { value: '2', label: '2+ étoiles' },
    { value: '3', label: '3+ étoiles' },
    { value: '4', label: '4+ étoiles' },
    { value: '5', label: '5 étoiles' }
  ];

  return (
    <div className={`relative ${className}`}>
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
          onFocus={() => setShowSuggestions(true)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && localSearchTerm.trim()) {
              saveRecentSearch(localSearchTerm);
              setShowSuggestions(false);
            }
          }}
          className="block w-full pl-10 pr-20 py-3 border border-gray-300 dark:border-gray-600 rounded-lg leading-5 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-booktime-500 focus:border-booktime-500 transition-colors text-sm"
          placeholder="Rechercher par titre, auteur, saga, genre..."
        />

        {/* Boutons d'action dans la barre */}
        <div className="absolute inset-y-0 right-0 flex items-center space-x-1 pr-3">
          {/* Bouton Open Library */}
          <button
            onClick={onOpenLibrarySearch}
            className="p-1.5 text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-md transition-colors"
            title="Rechercher sur Open Library"
          >
            <GlobeAltIcon className="h-4 w-4" />
          </button>

          {/* Bouton filtres avec compteur */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`relative p-1.5 rounded-md transition-colors ${
              showFilters || activeFiltersCount > 0
                ? 'text-booktime-600 bg-booktime-50 dark:text-booktime-400 dark:bg-booktime-900/20'
                : 'text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'
            }`}
            title="Filtres avancés"
          >
            <AdjustmentsHorizontalIcon className="h-4 w-4" />
            {activeFiltersCount > 0 && (
              <span className="absolute -top-1 -right-1 h-4 w-4 bg-booktime-500 text-white text-xs rounded-full flex items-center justify-center">
                {activeFiltersCount}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Suggestions dropdown */}
      {showSuggestions && (suggestions.length > 0 || recentSearches.length > 0) && (
        <div
          ref={suggestionsRef}
          className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50 max-h-80 overflow-y-auto"
        >
          {/* Recherches récentes */}
          {recentSearches.length > 0 && !searchTerm && (
            <div className="p-3 border-b border-gray-100 dark:border-gray-700">
              <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                Recherches récentes
              </h4>
              <div className="space-y-1">
                {recentSearches.map((search, index) => (
                  <button
                    key={index}
                    onClick={() => {
                      onSearchChange(search);
                      setShowSuggestions(false);
                    }}
                    className="w-full text-left px-2 py-1 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 rounded flex items-center space-x-2"
                  >
                    <ClockIcon className="h-3 w-3 text-gray-400" />
                    <span>{search}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Suggestions */}
          {suggestions.length > 0 && (
            <div className="p-2">
              {suggestions.map((suggestion, index) => {
                const Icon = suggestion.icon;
                return (
                  <button
                    key={index}
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="w-full text-left px-3 py-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-md flex items-center space-x-3 transition-colors"
                  >
                    <Icon className="h-4 w-4 text-gray-400 dark:text-gray-500 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-gray-900 dark:text-white truncate">
                        {suggestion.text}
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">
                        {suggestion.subtitle}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Panneau de filtres */}
      {showFilters && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-40 p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-900 dark:text-white">
              Filtres avancés
            </h3>
            <div className="flex items-center space-x-2">
              {activeFiltersCount > 0 && (
                <button
                  onClick={clearAllFilters}
                  className="text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                >
                  Effacer tout
                </button>
              )}
              <button
                onClick={() => setShowFilters(false)}
                className="p-1 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
              >
                <XMarkIcon className="h-4 w-4" />
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Catégorie */}
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Catégorie
              </label>
              <select
                value={filters?.category || ''}
                onChange={(e) => handleFilterChange('category', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-booktime-500 focus:border-booktime-500"
              >
                {categoryOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.icon ? `${option.icon} ${option.label}` : option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Statut */}
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Statut
              </label>
              <select
                value={filters?.status || ''}
                onChange={(e) => handleFilterChange('status', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-booktime-500 focus:border-booktime-500"
              >
                {statusOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.icon ? `${option.icon} ${option.label}` : option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Note minimale */}
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Note minimale
              </label>
              <select
                value={filters?.minRating || ''}
                onChange={(e) => handleFilterChange('minRating', e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-booktime-500 focus:border-booktime-500"
              >
                {ratingOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Auteur */}
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Auteur
              </label>
              <input
                type="text"
                value={filters?.author || ''}
                onChange={(e) => handleFilterChange('author', e.target.value)}
                placeholder="Nom de l'auteur"
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-booktime-500 focus:border-booktime-500"
              />
            </div>

            {/* Saga */}
            <div>
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Saga
              </label>
              <input
                type="text"
                value={filters?.saga || ''}
                onChange={(e) => handleFilterChange('saga', e.target.value)}
                placeholder="Nom de la saga"
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-booktime-500 focus:border-booktime-500"
              />
            </div>

            {/* Année de publication */}
            <div className="md:col-span-1">
              <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                Année de publication
              </label>
              <div className="flex space-x-2">
                <input
                  type="number"
                  value={filters?.yearFrom || ''}
                  onChange={(e) => handleFilterChange('yearFrom', e.target.value)}
                  placeholder="De"
                  min="1800"
                  max="2030"
                  className="flex-1 px-2 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-booktime-500 focus:border-booktime-500"
                />
                <input
                  type="number"
                  value={filters?.yearTo || ''}
                  onChange={(e) => handleFilterChange('yearTo', e.target.value)}
                  placeholder="À"
                  min="1800"
                  max="2030"
                  className="flex-1 px-2 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-booktime-500 focus:border-booktime-500"
                />
              </div>
            </div>
          </div>

          {/* Options supplémentaires */}
          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={filters?.hasReview || false}
                onChange={(e) => handleFilterChange('hasReview', e.target.checked)}
                className="h-4 w-4 text-booktime-600 focus:ring-booktime-500 border-gray-300 dark:border-gray-600 rounded"
              />
              <span className="text-sm text-gray-700 dark:text-gray-300">
                Livres avec critique seulement
              </span>
            </label>
          </div>
        </div>
      )}

      {/* Effet de fermeture des filtres en cliquant ailleurs */}
      {showFilters && (
        <div
          className="fixed inset-0 z-30"
          onClick={() => setShowFilters(false)}
        />
      )}
    </div>
  );
});

export default AdvancedSearchBar;