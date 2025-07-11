// Imports
import React, { useState, useEffect, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { toast, Toaster } from 'react-hot-toast';

// Context imports
import { ThemeProvider, useTheme } from './contexts/ThemeContext';
import { AuthProvider, useAuth } from './hooks/useAuth';

// Component imports
import LoginPage from './components/user/LoginPage';
import UnifiedSearchBar from './components/UnifiedSearchBar';
import BookDetailModal from './components/BookDetailModal';
import SeriesCard from './components/SeriesCard';
import SeriesDetailModal from './components/SeriesDetailModal';
import SeriesDetailPage from './pages/SeriesDetailPage';
import RecommendationPage from './components/recommendations/RecommendationPage';
import ExportImportPage from './components/exportimport/ExportImportPage';
import ProfileModal from './components/common/ProfileModal';
import ExportImportModal from './components/export-import/ExportImportModal';

// PHASE 3.3 - Composants Social
import SocialModal from './components/social/SocialModal';

// PHASE 3.4 - Recommandations Avancées IA
import AdvancedRecommendationsModal from './components/advanced-recommendations/AdvancedRecommendationsModal';

// PHASE 3.5 - Intégrations Externes
import IntegrationsModal from './components/integrations/IntegrationsModal';

// PHASE 2.4 - Monitoring et Analytics
import ErrorBoundary from './components/monitoring/ErrorBoundary';
import PerformanceWidget from './components/monitoring/PerformanceWidget';
import AlertSystem from './components/monitoring/AlertSystem';

// Service imports
import { bookService } from './services/bookService';
import * as seriesLibraryService from './services/seriesLibraryService';

// Hook imports
import { useAdvancedSearch } from './hooks/useAdvancedSearch';
import { useGroupedSearch } from './hooks/useGroupedSearch';
import useBooks from './hooks/useBooks';
import useSeries from './hooks/useSeries';
import useSearch from './hooks/useSearch';
import SearchOptimizer from './utils/searchOptimizer';

// PHASE 2.4 - Monitoring et Analytics hooks
import usePerformanceMonitoring from './hooks/usePerformanceMonitoring';
import useUserAnalytics from './hooks/useUserAnalytics';

// Utils imports
import { getCategoryBadge } from './utils/helpers';
import { TAB_CONFIG } from './utils/constants';

// Search components imports (Phase 1.1 - Step 3)
import { calculateRelevanceScore, getRelevanceLevel } from './components/search/RelevanceEngine';
import SearchLogic from './components/search/SearchLogic';

// Series components imports (Phase 1.1 - Step 4)
import SeriesActions from './components/series/SeriesActions';

// Books components imports (Phase 1.1 - Step 5 & 6)
import BookActions from './components/books/BookActions';
import BookGrid from './components/books/BookGrid';

import './App.css';

// Main App Content
function AppContent() {
  return (
    <Routes>
      <Route path="/" element={<MainApp />} />
      <Route path="/series/:seriesName" element={<SeriesDetailPage />} />
      <Route path="/recommendations" element={<RecommendationPage />} />
      <Route path="/export-import" element={<ExportImportPage />} />
    </Routes>
  );
}

// Composant principal de l'application
function MainApp() {
  const { user } = useAuth();
  
  // États locaux pour l'UI
  const [activeTab, setActiveTab] = useState('roman');
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [showExportImportModal, setShowExportImportModal] = useState(false);
  const [showSocialModal, setShowSocialModal] = useState(false);
  const [showAdvancedRecommendationsModal, setShowAdvancedRecommendationsModal] = useState(false);
  const [showIntegrationsModal, setShowIntegrationsModal] = useState(false);

  // PHASE 2.4 - Monitoring et Analytics
  const performanceMonitoring = usePerformanceMonitoring();
  const userAnalytics = useUserAnalytics();
  const alertSystem = AlertSystem({ isActive: true });

  // Gestionnaire d'événements pour l'export/import
  useEffect(() => {
    const handleOpenExportImport = () => {
      setShowExportImportModal(true);
    };

    window.addEventListener('openExportImport', handleOpenExportImport);
    return () => {
      window.removeEventListener('openExportImport', handleOpenExportImport);
    };
  }, []);

  // Gestionnaire d'événements pour le social
  useEffect(() => {
    const handleOpenSocial = () => {
      setShowSocialModal(true);
    };

    window.addEventListener('openSocial', handleOpenSocial);
    return () => {
      window.removeEventListener('openSocial', handleOpenSocial);
    };
  }, []);

  // Gestionnaire d'événements pour les recommandations avancées
  useEffect(() => {
    const handleOpenAdvancedRecommendations = () => {
      setShowAdvancedRecommendationsModal(true);
    };

    window.addEventListener('openAdvancedRecommendations', handleOpenAdvancedRecommendations);
    return () => {
      window.removeEventListener('openAdvancedRecommendations', handleOpenAdvancedRecommendations);
    };
  }, []);

  // Gestionnaire d'événements pour les intégrations
  useEffect(() => {
    const handleOpenIntegrations = () => {
      setShowIntegrationsModal(true);
    };

    window.addEventListener('openIntegrations', handleOpenIntegrations);
    return () => {
      window.removeEventListener('openIntegrations', handleOpenIntegrations);
    };
  }, []);

  // CORRECTION ERREUR - Fonction backToLibrary définie avant les useEffect qui l'utilisent
  const backToLibrary = () => {
    // PHASE 2.4 - Analytics navigation
    userAnalytics.trackInteraction('back_to_library', 'button');
    
    searchHook.backToLibrary(clearSearch);
  };

  // CORRECTION RCA - Gestionnaire d'événements pour retour automatique vers bibliothèque
  useEffect(() => {
    const handleBackToLibrary = (event) => {
      console.log('🎯 CORRECTION RCA: Retour automatique vers bibliothèque déclenché', event.detail);
      // Appeler la fonction de retour à la bibliothèque
      backToLibrary();
      
      // Analytics pour tracking de la correction
      if (userAnalytics && event.detail) {
        userAnalytics.trackInteraction('auto_back_to_library', 'correction_rca', {
          reason: event.detail.reason,
          targetCategory: event.detail.targetCategory,
          bookTitle: event.detail.bookTitle
        });
      }
    };

    window.addEventListener('backToLibrary', handleBackToLibrary);
    return () => {
      window.removeEventListener('backToLibrary', handleBackToLibrary);
    };
  }, [backToLibrary, userAnalytics]);

  // Démarrage automatique du monitoring
  useEffect(() => {
    performanceMonitoring.startMonitoring();
    userAnalytics.startTracking();
    
    return () => {
      performanceMonitoring.stopMonitoring();
      userAnalytics.stopTracking();
    };
  }, []);

  // Hooks personnalisés pour gérer les états (Phase 1.1 - Step 6)
  const booksHook = useBooks();
  const seriesHook = useSeries();
  const searchHook = useSearch();

  // Hook de recherche avancée
  const {
    filters,
    setFilters,
    filteredBooks,
    searchStats,
    clearSearch
  } = useAdvancedSearch(booksHook.books);

  // Hook de recherche groupée
  const {
    groupedResults,
    searchStats: groupedSearchStats,
  } = useGroupedSearch();

  // FONCTION UTILITAIRE : Déterminer le badge de catégorie depuis un livre Open Library
  const getCategoryBadgeFromBook = (book) => {
    return getCategoryBadge(book);
  };

  // FONCTION AFFICHAGE UNIFIÉ : Mélange séries et livres individuels par date d'ajout
  const createUnifiedDisplay = (booksList) => {
    return BookActions.createUnifiedDisplay(booksList, getCategoryBadgeFromBook);
  };

  // Fonction pour rechercher dans Open Library avec RECHERCHE GLOBALE (toutes catégories)
  const searchOpenLibrary = async (query) => {
    // PHASE 2.4 - Monitoring recherche
    const searchStartTime = Date.now();
    userAnalytics.trackSearch(query, 0, activeTab, 'openlibrary');
    
    await searchHook.searchOpenLibrary(query, {
      books: booksHook.books,
      getCategoryBadgeFromBook
    });

    // Mesure des performances de recherche
    const searchTime = Date.now() - searchStartTime;
    const resultCount = searchHook.openLibraryResults?.length || 0;
    performanceMonitoring.measureSearchPerformance(query, resultCount, searchTime);
    alertSystem.checkSearchPerformance(searchTime, resultCount);
    
    // Mise à jour analytics
    userAnalytics.trackSearch(query, resultCount, activeTab, 'openlibrary');
  };

  // Fonction pour ajouter un livre depuis Open Library
  const handleAddFromOpenLibrary = async (openLibraryBook) => {
    // PHASE 2.4 - Monitoring API
    const apiStartTime = Date.now();
    
    try {
      await searchHook.handleAddFromOpenLibrary(openLibraryBook, {
        books: booksHook.books,
        activeTab,
        getCategoryBadgeFromBook,
        loadBooks: booksHook.loadBooks,
        loadStats: booksHook.loadStats
      });

      // Mesure performance API
      const apiTime = Date.now() - apiStartTime;
      performanceMonitoring.measureApiResponse('add_from_openlibrary', apiStartTime, true);
      alertSystem.checkResponseTime('add_from_openlibrary', apiTime);
      
      // Analytics
      userAnalytics.trackBookInteraction('add_from_openlibrary', {
        title: openLibraryBook.title,
        category: openLibraryBook.categoryBadge?.key || 'unknown'
      });
      
    } catch (error) {
      console.error('Error adding book:', error);
      performanceMonitoring.measureApiResponse('add_from_openlibrary', apiStartTime, false);
    }
  };

  // Fonction pour ajouter une série à la bibliothèque
  const handleAddSeries = async (series) => {
    // PHASE 2.4 - Monitoring API
    const apiStartTime = Date.now();
    
    try {
      const token = localStorage.getItem('token');
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      // Créer un livre "série" avec statut "À lire"
      const seriesBook = {
        title: series.name,
        author: series.author || 'Auteur inconnu',
        category: series.category || 'roman',
        description: `Collection ${series.name} - ${series.total_volumes || 0} tome(s)`,
        saga: series.name,
        volume_number: null, // Pas de numéro de tome car c'est la série entière
        status: 'to_read', // Statut par défaut "À lire"
        cover_url: series.cover_url || '',
        total_pages: null,
        is_series: true // Marquer comme série
      };

      const response = await fetch(`${backendUrl}/api/books`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(seriesBook)
      });

      if (response.ok) {
        // Message de succès
        toast.success(`Série "${series.name}" ajoutée à votre bibliothèque ! 📚`, {
          duration: 2000
        });
        
        // Fermer le modal
        seriesHook.closeSeriesModal();
        
        // ✅ SOLUTION ROBUSTE OPTION C : Utiliser verifyAndDisplayBook pour les séries
        // Même logique que pour les livres individuels avec retry intelligent
        console.log('🔍 [SÉRIE] Vérification et affichage série ajoutée:', series.name);
        
        const result = await searchHook.verifyAndDisplayBook(
          series.name,
          series.category || 'roman',
          booksHook.books,
          booksHook.loadBooks,
          booksHook.loadStats
        );
        
        // Analytics de performance
        console.log('📊 [SÉRIE] Performance metrics:', {
          seriesName: series.name,
          category: series.category,
          success: result.success,
          attempts: result.attempts,
          totalTime: result.totalTime
        });
        
        // Mesure performance API
        const apiTime = Date.now() - apiStartTime;
        performanceMonitoring.measureApiResponse('add_series', apiStartTime, true);
        alertSystem.checkResponseTime('add_series', apiTime);
        
        // Analytics
        userAnalytics.trackSeriesInteraction('add_to_library', {
          name: series.name,
          category: series.category
        });
        
      } else {
        const error = await response.json();
        toast.error(`Erreur : ${error.detail || 'Impossible d\'ajouter la série'}`);
        performanceMonitoring.measureApiResponse('add_series', apiStartTime, false);
      }
    } catch (error) {
      console.error('Error adding series:', error);
      toast.error('Erreur lors de l\'ajout de la série');
      performanceMonitoring.measureApiResponse('add_series', apiStartTime, false);
    }
  };

  // Gestionnaires de clic
  const handleSeriesClick = (series) => {
    // PHASE 2.4 - Analytics séries
    userAnalytics.trackSeriesInteraction('view', series);
    userAnalytics.trackInteraction('series_click', 'series_card', { seriesName: series.name });
    
    searchHook.handleSeriesClick(series, seriesHook);
  };

  const handleItemClick = (item) => {
    // PHASE 2.4 - Analytics éléments
    if (item.type === 'book') {
      userAnalytics.trackBookInteraction('view', item);
      userAnalytics.trackInteraction('book_click', 'book_card', { bookTitle: item.title });
    } else if (item.type === 'series') {
      userAnalytics.trackSeriesInteraction('view', item);
      userAnalytics.trackInteraction('series_click', 'series_card', { seriesName: item.name });
    }
    
    booksHook.handleItemClick(item, seriesHook);
  };

  // Gestion changement d'onglet avec analytics
  const handleTabChange = (newTab) => {
    // PHASE 2.4 - Analytics catégories
    userAnalytics.trackCategorySwitch(newTab);
    
    setActiveTab(newTab);
  };

  // CORRECTION RCA - Synchronisation activeTab avec filters.category
  useEffect(() => {
    setFilters(prev => ({ ...prev, category: activeTab }));
  }, [activeTab]);

  // Chargement initial au montage du composant
  useEffect(() => {
    if (user) {
      seriesHook.loadUserSeriesLibrary();
    }
  }, [user]);

  // Calculer les livres à afficher selon le mode
  const displayedBooks = searchHook.isSearchMode 
    ? searchHook.openLibraryResults 
    : createUnifiedDisplay(filteredBooks);

  // MODIFICATION ORGANISATIONNELLE : Grouper les livres par statut pour affichage en sections
  const groupBooksByStatus = (books) => {
    if (searchHook.isSearchMode) {
      // En mode recherche, pas de groupement par statut
      return { all: books };
    }

    const groups = {
      reading: [],    // EN COURS
      to_read: [],    // À LIRE  
      completed: []   // TERMINÉ
    };

    books.forEach(book => {
      const status = book.status || 'to_read';
      if (groups[status]) {
        groups[status].push(book);
      } else {
        groups.to_read.push(book); // Statut inconnu → À lire par défaut
      }
    });

    // Trier chaque groupe : vignettes séries d'abord, puis livres individuels
    const sortGroup = (groupArray) => {
      return groupArray.sort((a, b) => {
        // Vignettes séries en premier
        if (a.isSeriesCard && !b.isSeriesCard) return -1;
        if (!a.isSeriesCard && b.isSeriesCard) return 1;
        
        // Si même type, trier par date d'ajout (plus récent d'abord)
        const dateA = new Date(a.date_added || a.updated_at || 0);
        const dateB = new Date(b.date_added || b.updated_at || 0);
        return dateB - dateA;
      });
    };

    // Appliquer le tri à chaque groupe
    Object.keys(groups).forEach(status => {
      groups[status] = sortGroup(groups[status]);
    });

    return groups;
  };

  const groupedBooks = groupBooksByStatus(displayedBooks);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex-shrink-0 flex items-center">
              <span className="text-2xl">🐝</span>
              <h1 className="ml-2 text-xl font-bold text-gray-900 dark:text-white">BOOKTIME</h1>
            </div>
            
            {/* Barre de recherche centrale */}
            <div className="flex-1 max-w-2xl mx-8">
              <UnifiedSearchBar 
                searchTerm={searchHook.lastSearchTerm || ''}
                onSearchChange={searchHook.handleSearchTermChange}
                books={booksHook.books || []}
                onOpenLibrarySearch={searchOpenLibrary}
                filters={filters || {}}
                onFiltersChange={setFilters}
                isCompact={true}
              />
            </div>
            
            {/* Profil et navigation */}
            <div className="flex-shrink-0 flex items-center space-x-4">
              <button
                onClick={() => window.location.href = '/recommendations'}
                className="flex items-center space-x-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors duration-200"
              >
                <span>🔮</span>
                <span className="hidden sm:inline">Recommandations</span>
              </button>
              
              <button
                onClick={() => window.location.href = '/export-import'}
                className="flex items-center space-x-2 px-3 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors duration-200"
              >
                <span>📤</span>
                <span className="hidden sm:inline">Export/Import</span>
              </button>
              
              <button
                onClick={() => setShowProfileModal(true)}
                className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-full transition-colors duration-200"
              >
                {user?.first_name?.[0]?.toUpperCase()}{user?.last_name?.[0]?.toUpperCase()}
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto">
        <div className="px-4 sm:px-6 lg:px-8">
          {/* Mode recherche */}
          {searchHook.isSearchMode && (
            <div className="py-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Résultats pour "{searchHook.lastSearchTerm}"
                  </h2>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {displayedBooks.length} résultat(s) trouvé(s)
                  </p>
                </div>
                <button
                  onClick={backToLibrary}
                  className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors duration-200"
                >
                  ← Retour à ma bibliothèque
                </button>
              </div>
            </div>
          )}
          
          {/* Mode bibliothèque */}
          {!searchHook.isSearchMode && (
            <div className="py-6">
              {/* Onglets de navigation */}
              <div className="flex space-x-1 mb-6">
                {TAB_CONFIG.map((tab) => (
                  <button
                    key={tab.key}
                    onClick={() => handleTabChange(tab.key)}
                    className={`px-4 py-2 rounded-lg font-medium transition-colors duration-200 ${
                      activeTab === tab.key
                        ? 'bg-green-600 text-white'
                        : 'bg-gray-200 hover:bg-gray-300 text-gray-700 dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-gray-300'
                    }`}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
              
              {/* Statistiques */}
              {booksHook.stats && Object.keys(booksHook.stats).length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                  <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm">
                    <div className="text-2xl font-bold text-green-600">{booksHook.stats.total_books || 0}</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Total livres</div>
                  </div>
                  <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm">
                    <div className="text-2xl font-bold text-blue-600">{booksHook.stats.completed_books || 0}</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">Terminés</div>
                  </div>
                  <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm">
                    <div className="text-2xl font-bold text-yellow-600">{booksHook.stats.reading_books || 0}</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">En cours</div>
                  </div>
                  <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm">
                    <div className="text-2xl font-bold text-gray-600">{booksHook.stats.to_read_books || 0}</div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">À lire</div>
                  </div>
                </div>
              )}
            </div>
          )}
          
          {/* Affichage par sections de statut - MODIFICATION ORGANISATIONNELLE */}
          {!searchHook.isSearchMode && (
            <div className="space-y-8">
              {/* Section EN COURS - Vignettes séries + livres individuels mélangés */}
              {groupedBooks.reading && groupedBooks.reading.length > 0 && (
                <div>
                  <div className="flex items-center mb-4">
                    <h2 className="text-xl font-semibold text-yellow-600 dark:text-yellow-400">
                      En cours ({groupedBooks.reading.length})
                    </h2>
                  </div>
                  <BookGrid
                    books={groupedBooks.reading}
                    loading={false}
                    onItemClick={handleItemClick}
                    showEmptyState={false}
                  />
                </div>
              )}

              {/* Section À LIRE - Vignettes séries + livres individuels mélangés */}
              {groupedBooks.to_read && groupedBooks.to_read.length > 0 && (
                <div>
                  <div className="flex items-center mb-4">
                    <h2 className="text-xl font-semibold text-blue-600 dark:text-blue-400">
                      À lire ({groupedBooks.to_read.length})
                    </h2>
                  </div>
                  <BookGrid
                    books={groupedBooks.to_read}
                    loading={false}
                    onItemClick={handleItemClick}
                    showEmptyState={false}
                  />
                </div>
              )}

              {/* Section TERMINÉ - Vignettes séries + livres individuels mélangés */}
              {groupedBooks.completed && groupedBooks.completed.length > 0 && (
                <div>
                  <div className="flex items-center mb-4">
                    <h2 className="text-xl font-semibold text-green-600 dark:text-green-400">
                      Terminé ({groupedBooks.completed.length})
                    </h2>
                  </div>
                  <BookGrid
                    books={groupedBooks.completed}
                    loading={false}
                    onItemClick={handleItemClick}
                    showEmptyState={false}
                  />
                </div>
              )}

              {/* État vide si aucun livre */}
              {(!groupedBooks.reading || groupedBooks.reading.length === 0) &&
               (!groupedBooks.to_read || groupedBooks.to_read.length === 0) &&
               (!groupedBooks.completed || groupedBooks.completed.length === 0) && (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">📚</div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    Aucun livre dans votre bibliothèque
                  </h3>
                  <p className="text-gray-500 dark:text-gray-400">
                    Commencez par ajouter quelques livres à votre collection !
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Mode recherche - Grille unique */}
          {searchHook.isSearchMode && (
            <BookGrid
              books={displayedBooks}
              loading={booksHook.loading}
              onItemClick={handleItemClick}
              showEmptyState={true}
            />
          )}
        </div>
      </main>
      
      {/* Modals */}
      {booksHook.showBookModal && booksHook.selectedBook && (
        <BookDetailModal
          book={booksHook.selectedBook}
          isOpen={booksHook.showBookModal}
          onClose={booksHook.closeBookModal}
          onUpdate={booksHook.handleUpdateBook}
          onDelete={booksHook.handleDeleteBook}
          onAddFromOpenLibrary={handleAddFromOpenLibrary}
        />
      )}
      
      {seriesHook.showSeriesModal && seriesHook.selectedSeries && (
        <SeriesDetailModal
          series={seriesHook.selectedSeries}
          isOpen={seriesHook.showSeriesModal}
          onClose={seriesHook.closeSeriesModal}
          onUpdate={booksHook.loadBooks}
          onAddSeries={handleAddSeries}
        />
      )}
      
      {showProfileModal && (
        <ProfileModal
          isOpen={showProfileModal}
          onClose={() => setShowProfileModal(false)}
        />
      )}
      
      {showExportImportModal && (
        <ExportImportModal
          isOpen={showExportImportModal}
          onClose={() => setShowExportImportModal(false)}
          backendUrl={process.env.REACT_APP_BACKEND_URL}
          token={localStorage.getItem('token')}
        />
      )}
      
      {showSocialModal && (
        <SocialModal
          isOpen={showSocialModal}
          onClose={() => setShowSocialModal(false)}
          currentUser={user}
        />
      )}
      
      {/* PHASE 3.4 - Modal Recommandations Avancées */}
      {showAdvancedRecommendationsModal && (
        <AdvancedRecommendationsModal
          isOpen={showAdvancedRecommendationsModal}
          onClose={() => setShowAdvancedRecommendationsModal(false)}
          onAddBook={async (bookData) => {
            try {
              await BookActions.addBook(bookData);
              setActiveTab(bookData.category || 'roman');
              await booksHook.loadBooks();
            } catch (error) {
              console.error('Erreur lors de l\'ajout du livre:', error);
            }
          }}
        />
      )}
      
      {/* PHASE 3.5 - Modal Intégrations Externes */}
      {showIntegrationsModal && (
        <IntegrationsModal
          isOpen={showIntegrationsModal}
          onClose={() => setShowIntegrationsModal(false)}
          onAddBooks={async (booksArray) => {
            try {
              for (const bookData of booksArray) {
                await BookActions.addBook(bookData);
              }
              await booksHook.loadBooks();
            } catch (error) {
              console.error('Erreur lors de l\'ajout des livres:', error);
            }
          }}
        />
      )}
      
      {/* Toast notifications */}
      <Toaster position="bottom-right" />
      
      {/* PHASE 2.4 - Performance Widget */}
      <PerformanceWidget 
        position="bottom-right" 
        isVisible={process.env.NODE_ENV === 'development'} 
      />
    </div>
  );
}

// Main App Component
function App() {
  return (
    <Router>
      <ThemeProvider>
        <AuthProvider>
          <ErrorBoundary>
            <Routes>
              <Route path="/" element={<AppWithAuth />} />
              <Route path="/recommendations" element={<RecommendationPage />} />
              <Route path="/series/:seriesId" element={<SeriesDetailPage />} />
            </Routes>
          </ErrorBoundary>
        </AuthProvider>
      </ThemeProvider>
    </Router>
  );
}

// App with Auth Wrapper
function AppWithAuth() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-green-500"></div>
      </div>
    );
  }

  return user ? <AppContent /> : <LoginPage />;
}

export default App;
