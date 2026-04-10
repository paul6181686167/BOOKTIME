// Phase 2.3 - Barre de recherche optimisée avec debouncing
import React, { memo, useCallback, useMemo } from 'react';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { useDebounce, useDebouncedCallback } from '../../hooks/useDebounce';

/**
 * Barre de recherche optimisée avec debouncing et memoization
 */
const OptimizedUnifiedSearchBar = memo(({
  onSearch,
  onTermChange,
  isSearchMode = false,
  searchLoading = false,
  lastSearchTerm = "",
  placeholder = "Rechercher un livre, auteur, série...",
  debounceDelay = 300,
  className = ""
}) => {
  // Debouncing de la recherche
  const debouncedSearch = useDebouncedCallback((query) => {
    if (query.trim()) {
      onSearch(query.trim());
    }
  }, debounceDelay);

  // Gestionnaire de changement de texte optimisé
  const handleInputChange = useCallback((e) => {
    const value = e.target.value;
    
    // Mise à jour immédiate de l'affichage
    onTermChange(value);
    
    // Recherche debouncée
    if (value.trim()) {
      debouncedSearch(value);
    }
  }, [onTermChange, debouncedSearch]);

  // Gestionnaire de soumission du formulaire
  const handleSubmit = useCallback((e) => {
    e.preventDefault();
    const query = e.target.query.value.trim();
    if (query) {
      onSearch(query);
    }
  }, [onSearch]);

  // Gestionnaire de la touche Entrée
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const query = e.target.value.trim();
      if (query) {
        onSearch(query);
      }
    }
  }, [onSearch]);

  // Memoization du placeholder selon le mode
  const dynamicPlaceholder = useMemo(() => {
    if (isSearchMode) {
      return "Modifier la recherche...";
    }
    return placeholder;
  }, [isSearchMode, placeholder]);

  // Memoization des styles
  const containerClasses = useMemo(() => {
    return `relative ${className}`;
  }, [className]);

  const inputClasses = useMemo(() => {
    return `
      w-full pl-10 pr-4 py-2 
      bg-gray-100 dark:bg-gray-700 
      border border-gray-300 dark:border-gray-600 
      rounded-lg 
      text-gray-900 dark:text-white 
      placeholder-gray-500 dark:placeholder-gray-400
      focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent
      transition-colors duration-200
    `.replace(/\s+/g, ' ').trim();
  }, []);

  return (
    <div className={containerClasses}>
      <form onSubmit={handleSubmit} className="relative">
        {/* Icône de recherche */}
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          {searchLoading ? (
            <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-green-500"></div>
          ) : (
            <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
          )}
        </div>

        {/* Champ de recherche */}
        <input
          type="text"
          name="query"
          value={lastSearchTerm}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder={dynamicPlaceholder}
          className={inputClasses}
          autoComplete="off"
          disabled={searchLoading}
        />

        {/* Indicateur de mode recherche */}
        {isSearchMode && (
          <div className="absolute inset-y-0 right-0 flex items-center pr-3">
            <span className="inline-flex items-center px-2 py-1 text-xs font-medium bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 rounded-full">
              Mode recherche
            </span>
          </div>
        )}
      </form>

      {/* Suggestions de recherche (si nécessaire) */}
      {lastSearchTerm && !isSearchMode && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50 max-h-48 overflow-y-auto">
          {/* Ici on pourrait ajouter des suggestions basées sur l'historique */}
          <div className="px-3 py-2 text-sm text-gray-500 dark:text-gray-400">
            Appuyez sur Entrée pour rechercher "{lastSearchTerm}"
          </div>
        </div>
      )}
    </div>
  );
});

OptimizedUnifiedSearchBar.displayName = 'OptimizedUnifiedSearchBar';

export default OptimizedUnifiedSearchBar;

// Hook pour optimiser l'état de recherche
export const useOptimizedSearch = (initialTerm = "") => {
  const [searchTerm, setSearchTerm] = React.useState(initialTerm);
  const [isSearchMode, setIsSearchMode] = React.useState(false);
  const [loading, setLoading] = React.useState(false);
  const [results, setResults] = React.useState([]);

  // Debouncing du terme de recherche
  const debouncedSearchTerm = useDebounce(searchTerm, 300);

  // Fonction de recherche optimisée
  const performSearch = useCallback(async (query) => {
    if (!query.trim()) return;

    setLoading(true);
    setIsSearchMode(true);
    
    try {
      // Ici on appellerait l'API de recherche
      // const results = await searchAPI(query);
      // setResults(results);
      
      // Simulation
      await new Promise(resolve => setTimeout(resolve, 500));
      setResults([]);
    } catch (error) {
      console.error('Erreur de recherche:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Effet pour la recherche automatique
  React.useEffect(() => {
    if (debouncedSearchTerm && debouncedSearchTerm.trim()) {
      performSearch(debouncedSearchTerm);
    }
  }, [debouncedSearchTerm, performSearch]);

  // Fonction pour quitter le mode recherche
  const exitSearchMode = useCallback(() => {
    setIsSearchMode(false);
    setSearchTerm("");
    setResults([]);
  }, []);

  return {
    searchTerm,
    setSearchTerm,
    isSearchMode,
    loading,
    results,
    performSearch,
    exitSearchMode,
    debouncedSearchTerm
  };
};