import { useState, useCallback } from 'react';
import SearchLogic from '../components/search/SearchLogic';
import SearchOptimizer from '../utils/searchOptimizer';

// Hook personnalisé pour gérer l'état de recherche
export const useSearch = () => {
  const [openLibraryResults, setOpenLibraryResults] = useState([]);
  const [detectedSeries, setDetectedSeries] = useState([]);
  const [isSearchMode, setIsSearchMode] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [lastSearchTerm, setLastSearchTerm] = useState('');
  const [addingBooks, setAddingBooks] = useState(new Set());

  // Fonction pour créer les cartes séries à partir des résultats détectés
  const createSeriesCards = (detectedSeries) => {
    return detectedSeries.map(detected => ({
      id: `series_${detected.series.name.toLowerCase().replace(/\s+/g, '_')}`,
      name: detected.series.name,
      author: detected.series.authors?.join(', ') || 'Auteur inconnu',
      category: detected.series.category,
      description: detected.series.description,
      volumes: detected.series.volumes,
      first_published: detected.series.first_published,
      status: detected.series.status,
      confidence: detected.confidence,
      match_reasons: detected.match_reasons,
      isSeriesCard: true,
      relevanceScore: detected.confidence,
      relevanceInfo: { 
        level: 'prioritaire', 
        label: detected.matchType === 'exact_match' ? 'Série (correspondance exacte)' : 
               detected.matchType === 'fuzzy_match' ? 'Série (correspondance approximative)' : 'Série détectée',
        color: 'bg-purple-600', 
        icon: '📚' 
      }
    }));
  };

  // Fonction pour générer les cartes séries avec algorithme avancé
  const generateSeriesCardsForSearch = (query, books) => {
    console.log('🚀 OPTIMISATION RECHERCHE - Génération cartes séries avec algorithme avancé');
    
    const startTime = performance.now();
    const seriesCards = SearchOptimizer.generateSeriesCardsForSearch(query, books);
    const detectionTime = performance.now() - startTime;
    
    const metrics = SearchOptimizer.getSearchMetrics(query, seriesCards, detectionTime);
    console.log('📊 Métriques de recherche:', metrics);
    
    if (seriesCards.length > 0) {
      console.log(`✅ ${seriesCards.length} série(s) détectée(s) avec scores prioritaires 100000+`);
      seriesCards.forEach(card => {
        console.log(`📚 ${card.name} - Score: ${card.confidence} - Type: ${card.matchType}`);
      });
    } else {
      console.log('ℹ️ Aucune série officielle détectée pour cette recherche');
    }
    
    return seriesCards;
  };

  // Fonction pour rechercher dans Open Library
  const searchOpenLibrary = async (query, dependencies) => {
    await SearchLogic.searchOpenLibrary(query, {
      books: dependencies.books,
      setSearchLoading,
      setIsSearchMode,
      setLastSearchTerm,
      setOpenLibraryResults,
      generateSeriesCardsForSearch,
      handleAddSeriesToLibrary: dependencies.handleAddSeriesToLibrary,
      getCategoryBadgeFromBook: dependencies.getCategoryBadgeFromBook
    });
  };

  // Fonction pour ajouter un livre depuis Open Library
  const handleAddFromOpenLibrary = async (openLibraryBook, dependencies) => {
    await SearchLogic.handleAddFromOpenLibrary(openLibraryBook, {
      books: dependencies.books,
      addingBooks,
      setAddingBooks,
      activeTab: dependencies.activeTab,
      getCategoryBadgeFromBook: dependencies.getCategoryBadgeFromBook,
      loadBooks: dependencies.loadBooks,
      loadStats: dependencies.loadStats,
      setOpenLibraryResults
    });
  };

  // Gestionnaire de clic sur série
  const handleSeriesClick = (series, seriesActions) => {
    SearchLogic.handleSeriesClick(series, seriesActions.setSelectedSeries, seriesActions.setShowSeriesModal);
  };

  // Gestionnaire stable pour éviter les re-rendus excessifs
  const handleSearchTermChange = useCallback((term) => {
    setLastSearchTerm(term);
  }, []);

  // Fonction pour retourner à la bibliothèque
  const backToLibrary = (clearSearch) => {
    SearchLogic.backToLibrary(setIsSearchMode, setOpenLibraryResults, setLastSearchTerm, clearSearch);
  };

  return {
    // États
    openLibraryResults,
    detectedSeries,
    isSearchMode,
    searchLoading,
    lastSearchTerm,
    addingBooks,
    
    // Actions
    createSeriesCards,
    generateSeriesCardsForSearch,
    searchOpenLibrary,
    handleAddFromOpenLibrary,
    handleSeriesClick,
    handleSearchTermChange,
    backToLibrary,
    
    // Setters (pour compatibilité)
    setOpenLibraryResults,
    setDetectedSeries,
    setIsSearchMode,
    setSearchLoading,
    setLastSearchTerm,
    setAddingBooks
  };
};

export default useSearch;
