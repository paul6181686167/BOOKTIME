// Imports
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import { toast, Toaster } from 'react-hot-toast';

// Context imports
import { ThemeProvider, useTheme } from './contexts/ThemeContext';
import { AuthProvider, useAuth } from './hooks/useAuth';

// Component imports
import LoginPage from './components/user/LoginPage';
import UnifiedSearchBar from './components/UnifiedSearchBar';
import BookDetailModal from './components/BookDetailModal';
import AuthorModal from './components/AuthorModal';
import SeriesCard from './components/SeriesCard';
import SeriesDetailModal from './components/SeriesDetailModal';
import SeriesDetailPage from './pages/SeriesDetailPage';
import RecommendationPage from './components/recommendations/RecommendationPage';
import OpenLibraryBookPage from './pages/OpenLibraryBookPage';
import ResetPasswordPage from './pages/ResetPasswordPage';
import ExportImportPage from './components/exportimport/ExportImportPage';
import ProfileModal from './components/common/ProfileModal';
import ExportImportModal from './components/export-import/ExportImportModal';
import SlidePanel from './components/SlidePanel';
import UpcomingPanel from './components/UpcomingPanel';
import DiscoverSection from './components/DiscoverSection';

// PHASE 3.3 - Composants Social
import SocialModal from './components/social/SocialModal';

// PHASE 3.4 - Recommandations Avancées IA
import AdvancedRecommendationsModal from './components/advanced-recommendations/AdvancedRecommendationsModal';

// PHASE 3.5 - Intégrations Externes
import IntegrationsModal from './components/integrations/IntegrationsModal';

// PHASE 2.4 - Monitoring et Analytics
import ErrorBoundary from './components/monitoring/ErrorBoundary';
import PerformanceWidget from './components/monitoring/PerformanceWidget';
// Service imports
import { bookService } from './services/bookService';
import * as seriesLibraryService from './services/seriesLibraryService';
import { seriesImageService } from './services/seriesImageService';

// Hook imports
import { useAdvancedSearch } from './hooks/useAdvancedSearch';
import { useGroupedSearch } from './hooks/useGroupedSearch';
import useBooks from './hooks/useBooks';
import useSeries from './hooks/useSeries';
import useSearch from './hooks/useSearch';
// PHASE C.1 - Hook unifié pour rafraîchissement optimisé
import useUnifiedContent from './hooks/useUnifiedContent';
import SearchOptimizer from './utils/searchOptimizer';
import { useAutoSeriesDetection } from './hooks/useAutoSeriesDetection';

// PHASE 2.4 - Monitoring et Analytics hooks
import usePerformanceMonitoring from './hooks/usePerformanceMonitoring';
import useUserAnalytics from './hooks/useUserAnalytics';

// Utils imports
import { getCategoryBadge } from './utils/helpers';
import { TAB_CONFIG } from './utils/constants';
import { API_BASE_URL } from './config/environment';


// Search components imports (Phase 1.1 - Step 3)
import { calculateRelevanceScore, getRelevanceLevel } from './components/search/RelevanceEngine';
import SearchLogic from './components/search/SearchLogic';

// Series components imports (Phase 1.1 - Step 4)
import SeriesActions from './components/series/SeriesActions';

// Books components imports (Phase 1.1 - Step 5 & 6)
import BookActions from './components/books/BookActions';
import BookGrid from './components/books/BookGrid';
import MobileBottomNav from './components/MobileBottomNav';
import MobileSearchOverlay from './components/MobileSearchOverlay';

import './App.css';
import './styles/optimized.css';

// Hook pour le tri des sections
const useSectionSort = () => {
  const [sortConfig, setSortConfig] = React.useState({ field: 'date_added', order: 'desc' });
  const sortBooks = React.useCallback((books) => {
    const sorted = [...books].sort((a, b) => {
      let va, vb;
      if (sortConfig.field === 'title') {
        va = (a.name || a.title || '').toLowerCase();
        vb = (b.name || b.title || '').toLowerCase();
      } else if (sortConfig.field === 'author') {
        va = (a.author || '').toLowerCase();
        vb = (b.author || '').toLowerCase();
      } else {
        va = new Date(a.date_added || a.updated_at || 0);
        vb = new Date(b.date_added || b.updated_at || 0);
      }
      if (va < vb) return sortConfig.order === 'asc' ? -1 : 1;
      if (va > vb) return sortConfig.order === 'asc' ? 1 : -1;
      return 0;
    });
    return sorted;
  }, [sortConfig]);
  return { sortConfig, setSortConfig, sortBooks };
};

// Composant de contrôles de tri
const SortControls = ({ sortConfig, setSortConfig }) => {
  const fields = [
    { key: 'date_added', label: 'Date' },
    { key: 'title',      label: 'Titre' },
    { key: 'author',     label: 'Auteur' },
  ];
  return (
    <div className="flex items-center gap-2 ml-4">
      <span className="text-xs text-gray-500 dark:text-gray-400">Trier par</span>
      {fields.map(f => (
        <button
          key={f.key}
          onClick={() => setSortConfig(prev =>
            prev.field === f.key
              ? { ...prev, order: prev.order === 'asc' ? 'desc' : 'asc' }
              : { field: f.key, order: 'asc' }
          )}
          className={`px-2 py-1 text-xs rounded transition-colors ${
            sortConfig.field === f.key
              ? 'bg-gray-800 dark:bg-gray-200 text-white dark:text-gray-900 font-medium'
              : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
          }`}
        >
          {f.label} {sortConfig.field === f.key ? (sortConfig.order === 'asc' ? '↑' : '↓') : ''}
        </button>
      ))}
    </div>
  );
};

// Composant compteur animé
const AnimatedCounter = ({ value, className }) => {
  const [displayed, setDisplayed] = React.useState(0);
  React.useEffect(() => {
    if (value === 0) { setDisplayed(0); return; }
    if (!value) return;
    let start = 0;
    const step = Math.ceil(value / 20);
    const timer = setInterval(() => {
      start += step;
      if (start >= value) { setDisplayed(value); clearInterval(timer); }
      else setDisplayed(start);
    }, 30);
    return () => clearInterval(timer);
  }, [value]);
  return <span className={className}>{displayed}</span>;
};

// Main App Content
function AppContent() {
  return (
    <Routes>
      <Route path="/" element={<MainApp />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route path="/series/:seriesName" element={<SeriesDetailPage />} />
      <Route path="/recommendations" element={<RecommendationPage />} />
      <Route path="/export-import" element={<ExportImportPage />} />
    </Routes>
  );
}

// Composant principal de l'application
function MainApp() {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  // États locaux pour l'UI
  const [activeTab, setActiveTab] = useState('roman');
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [showExportImportModal, setShowExportImportModal] = useState(false);
  const [showSocialModal, setShowSocialModal] = useState(false);
  const [showAdvancedRecommendationsModal, setShowAdvancedRecommendationsModal] = useState(false);
  const [showIntegrationsModal, setShowIntegrationsModal] = useState(false);
  const [showUpcomingPanel, setShowUpcomingPanel] = useState(false);
  const [showAuthorModal, setShowAuthorModal] = useState(false);
  const [selectedAuthor, setSelectedAuthor] = useState(null);
  // Mobile states
  const [mobileTab, setMobileTab] = useState('home');
  const [showMobileSearch, setShowMobileSearch] = useState(false);

  // PHASE 2.4 - Monitoring et Analytics
  const performanceMonitoring = usePerformanceMonitoring();
  const userAnalytics = useUserAnalytics();

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

  // Monitoring perf : dev uniquement (évite alertes / charge inutiles en prod)
  useEffect(() => {
    if (process.env.NODE_ENV === 'development') {
      performanceMonitoring.startMonitoring();
    }
    userAnalytics.startTracking();

    return () => {
      if (process.env.NODE_ENV === 'development') {
        performanceMonitoring.stopMonitoring();
      }
      userAnalytics.stopTracking();
    };
  }, []);

  // Keep-alive : ping le backend toutes les 4 min pour éviter la mise en veille Render
  useEffect(() => {
    const PING_INTERVAL = 4 * 60 * 1000; // 4 minutes
    const ping = () => fetch(`${API_BASE_URL}/ping`, { method: 'GET' }).catch(() => {});
    const id = setInterval(ping, PING_INTERVAL);
    return () => clearInterval(id);
  }, []);

  // PHASE C.1 - Hooks unifiés pour rafraîchissement optimisé
  const unifiedContent = useUnifiedContent();
  
  // Hooks personnalisés pour gérer les états (Phase 1.1 - Step 6)
  // CONSERVÉS pour compatibilité avec les modals et actions spécialisées
  const booksHook = useBooks();
  const seriesHook = useSeries();
  const searchHook = useSearch();
  
  // Hook de détection automatique des séries
  const { enhanceBookWithSeries, configure: configureAutoDetection } = useAutoSeriesDetection();

  // Hook de recherche avancée avec données unifiées
  const {
    filters,
    setFilters,
    filteredBooks,
    searchStats,
    clearSearch
  } = useAdvancedSearch(unifiedContent.books);

  // Hook de recherche groupée
  const {
    groupedResults,
    searchStats: groupedSearchStats,
  } = useGroupedSearch();

  // CORRECTION RCA DÉFINITIVE - Fonction backToLibrary définie APRÈS tous les hooks mais AVANT tous les useEffect
  const backToLibrary = useCallback(() => {
    // PHASE 2.4 - Analytics navigation
    if (userAnalytics) {
      userAnalytics.trackInteraction('back_to_library', 'button');
    }
    
    if (searchHook && clearSearch) {
      searchHook.backToLibrary(clearSearch);
    }
  }, [userAnalytics, searchHook, clearSearch]);

  // Gestionnaire unique pour l'événement backToLibrary (fusion des deux anciens listeners)
  useEffect(() => {
    const handleBackToLibrary = (event) => {
      const detail = event.detail || {};
      const { reason, seriesName, bookTitle, attempts, totalTime } = detail;

      if (reason === 'series_verified_success') {
        toast.success(`Série "${seriesName}" ajoutée avec succès !`);
      } else if (reason === 'book_verified_success') {
        toast.success(`Livre "${bookTitle}" ajouté avec succès !`);
      } else if (reason === 'series_verification_failed') {
        toast.error(`Série "${seriesName}" non trouvée après ${attempts} tentatives`);
        return; // Ne pas revenir en cas d'échec
      }

      backToLibrary();

      if (userAnalytics && detail) {
        userAnalytics.trackInteraction('auto_back_to_library', 'event', { reason });
      }
    };

    window.addEventListener('backToLibrary', handleBackToLibrary);
    return () => window.removeEventListener('backToLibrary', handleBackToLibrary);
  }, [backToLibrary, userAnalytics]);

  // FONCTION UTILITAIRE : Déterminer le badge de catégorie depuis un livre Open Library
  const getCategoryBadgeFromBook = (book) => {
    return getCategoryBadge(book);
  };

  // FONCTION AFFICHAGE UNIFIÉ : Mélange séries et livres individuels par date d'ajout
  // PHASE C.1 : Utiliser données unifiées pour créer l'affichage
  const createUnifiedDisplay = (booksList) => {
    // ✅ CORRECTION RCA - Filtrer les séries selon l'onglet actif
    const filteredSeries = (unifiedContent.userSeriesLibrary || []).filter(series => {
      const seriesCategory = series.category || 'roman';
      
      // Logique de filtrage identique à useAdvancedSearch
      if (activeTab === 'roman') {
        return seriesCategory === 'roman';
      } else if (activeTab === 'graphic_novels') {
        // Romans graphiques = BD + Manga
        return seriesCategory === 'bd' || seriesCategory === 'manga';
      }
      
      return true; // Fallback pour autres onglets
    });
    
    
    return BookActions.createUnifiedDisplay(booksList, getCategoryBadgeFromBook, filteredSeries, unifiedContent.readingPreferences || {});
  };

  // Fonction pour rechercher dans Open Library avec RECHERCHE GLOBALE (toutes catégories)
  const searchOpenLibrary = async (query) => {
    // PHASE 2.4 - Monitoring recherche
    const searchStartTime = Date.now();
    userAnalytics.trackSearch(query, 0, activeTab, 'openlibrary');
    
    await searchHook.searchOpenLibrary(query, {
      books: unifiedContent.books,
      getCategoryBadgeFromBook
    });

    // Mesure des performances de recherche
    const searchTime = Date.now() - searchStartTime;
    const resultCount = searchHook.openLibraryResults?.length || 0;
    performanceMonitoring.measureSearchPerformance(query, resultCount, searchTime);

    // Mise à jour analytics
    userAnalytics.trackSearch(query, resultCount, activeTab, 'openlibrary');
  };

  // Fonction pour ajouter un livre depuis Open Library
  // Mise à jour optimiste : UI instantanée + sync backend en arrière-plan
  const handleUpdateBookOptimistic = async (bookId, bookData) => {
    // 1. Mettre à jour l'UI immédiatement
    unifiedContent.setBooks(prev =>
      prev.map(b => b.id === bookId ? { ...b, ...bookData } : b)
    );
    // Mettre à jour aussi le livre sélectionné dans le modal
    if (booksHook.selectedBook?.id === bookId) {
      // le modal re-lit depuis selectedBook — on laisse handleUpdateBook le mettre à jour
    }
    // 2. Appeler l'API et rafraîchir en arrière-plan (sans bloquer l'UI)
    try {
      await booksHook.handleUpdateBook(bookId, bookData);
      // Rafraîchir unifiedContent après confirmation backend
      await unifiedContent.refreshAfterAdd('books');
    } catch (error) {
      // En cas d'erreur : recharger pour revenir à l'état réel
      await unifiedContent.refreshAfterAdd('books');
    }
  };

  const handleAddFromOpenLibrary = async (openLibraryBook) => {
    // PHASE 2.4 - Monitoring API
    const apiStartTime = Date.now();
    
    try {
      // CORRECTION RCA : Restaurer la compatibilité d'interface avec SearchLogic
      // Créer des wrappers compatibles avec l'ancienne signature
      const loadBooksWrapper = async () => {
        await unifiedContent.refreshAfterAdd('books');
        // Également rafraîchir les livres avec l'ancien hook pour compatibilité
        await booksHook.loadBooks();
      };
      
      const loadStatsWrapper = async () => {
        await unifiedContent.refreshAfterAdd('stats');
        // Également rafraîchir les stats avec l'ancien hook pour compatibilité
        await booksHook.loadStats();
      };
      
      await searchHook.handleAddFromOpenLibrary(openLibraryBook, {
        books: unifiedContent.books,
        activeTab,
        getCategoryBadgeFromBook,
        loadBooks: loadBooksWrapper,
        loadStats: loadStatsWrapper
      });

      // Mesure performance API
      const apiTime = Date.now() - apiStartTime;
      performanceMonitoring.measureApiResponse('add_from_openlibrary', apiStartTime, true);

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
    // CORRECTION RCA FINALE : Utiliser l'implémentation robuste de SeriesActions
    const apiStartTime = Date.now();
    
    try {
      
      // Utiliser l'implémentation complète et robuste de SeriesActions
      await SeriesActions.handleAddSeriesToLibrary(series, {
        setSeriesLibraryLoading: (loading) => {
          // Mettre à jour l'état de chargement si nécessaire
          console.log('📊 Chargement série:', loading);
        },
        loadUserSeriesLibrary: async () => {
          // ✅ CORRECTION : Utiliser le bon système d'état (unifiedContent)
          await unifiedContent.refreshAfterAdd('series');
          console.log('✅ [REFRESH] Série ajoutée - Interface synchronisée avec unifiedContent');
        }
      });
      
      // Fermer le modal
      seriesHook.closeSeriesModal();
      
      // Retour automatique à la bibliothèque avec clearSearch
      searchHook.backToLibrary(clearSearch);
      
      // Mesure performance API
      const apiTime = Date.now() - apiStartTime;
      performanceMonitoring.measureApiResponse('add_series_seriesactions', apiStartTime, true);

      // Analytics
      userAnalytics.trackSeriesInteraction('add_to_library_seriesactions', {
        name: series.name,
        category: series.category
      });
      
      
    } catch (error) {
      console.error('❌ [CORRECTION RCA] Erreur SeriesActions:', error);
      // L'erreur sera gérée par SeriesActions.handleAddSeriesToLibrary
      performanceMonitoring.measureApiResponse('add_series_seriesactions', apiStartTime, false);
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

  const handleAuthorClick = (author) => {
    // Analytics pour le clic sur auteur
    userAnalytics.trackInteraction('author_click', 'author_name', { authorName: author });
    
    // Fermer le modal livre s'il est ouvert
    if (booksHook.showBookModal) {
      booksHook.closeBookModal();
    }
    
    // Ouvrir le modal auteur
    setSelectedAuthor(author);
    setShowAuthorModal(true);
  };

  const handleCloseAuthorModal = () => {
    setShowAuthorModal(false);
    setSelectedAuthor(null);
    
    // Optionnellement, rouvrir le modal livre s'il y avait un livre sélectionné
    // (pour une expérience utilisateur plus fluide)
    if (booksHook.selectedBook) {
      // Petit délai pour éviter le conflit d'animation
      setTimeout(() => {
        booksHook.setShowBookModal(true);
      }, 100);
    }
  };

  // Gestion changement d'onglet avec analytics
  const handleTabChange = (newTab) => {
    // PHASE 2.4 - Analytics catégories
    userAnalytics.trackCategorySwitch(newTab);
    
    setActiveTab(newTab);
    localStorage.setItem('booktime_active_tab', newTab);
  };

  const handleMobileTabChange = (tab) => {
    setMobileTab(tab);
    if (tab === 'recommendations') {
      navigate('/recommendations');
    } else if (tab === 'upcoming') {
      setShowUpcomingPanel(true);
    } else if (tab === 'profile') {
      setShowProfileModal(true);
      // Revenir à home après fermeture
      setTimeout(() => setMobileTab('home'), 100);
    } else if (tab === 'home') {
      if (searchHook.isSearchMode) searchHook.clearSearch?.();
    }
  };

  // CORRECTION RCA - Synchronisation activeTab avec filters.category - MISE À JOUR SESSION 75
  useEffect(() => {
    // Nouvelle logique pour gérer le regroupement BD + Manga = Romans graphiques
    if (activeTab === 'graphic_novels') {
      // Pour Romans graphiques, on utilise un filtre spécial qui sera géré dans useAdvancedSearch
      setFilters(prev => ({ ...prev, category: 'graphic_novels' }));
    } else if (activeTab === 'upcoming') {
      // Pour l'onglet À venir, on utilise un filtre spécial (mais maintenant c'est un panneau)
      setFilters(prev => ({ ...prev, category: 'upcoming' }));
    } else {
      // Pour Romans, on applique le filtre normal
      setFilters(prev => ({ ...prev, category: activeTab }));
    }
  }, [activeTab]);

  // Listener backToLibrary fusionné avec le gestionnaire unique ci-dessus

  // Toast d'information si le backend est en veille (erreur au 1er chargement)
  useEffect(() => {
    if (unifiedContent.error && !unifiedContent.loading) {
      toast('Le serveur se réveille, patiente quelques secondes puis réessaie.', {
        icon: '⏳',
        duration: 6000,
        id: 'backend-wakeup' // éviter les doublons
      });
    }
  }, [unifiedContent.error, unifiedContent.loading]);

  // Chargement initial au montage du composant
  useEffect(() => {
    if (user) {
      // Les données sont automatiquement chargées par useUnifiedContent
      // Seul l'auto-enrichissement des images est conservé ici
      
      // 🎨 Auto-enrichissement des images de séries — 1 seule fois par session
      if (!sessionStorage.getItem('series-enrich-done')) {
        sessionStorage.setItem('series-enrich-done', 'true');
        seriesImageService.autoEnrichPopularSeries().then(result => {
          if (result) console.log('✅ Auto-enrichissement terminé:', result);
        }).catch(error => {
          console.warn('⚠️ Auto-enrichissement échoué (non critique):', error);
        });
      }
    }
  }, [user]);

  // Calculer les livres à afficher selon le mode
  // Tous les livres appartenant à une série sont groupés en carte série (bibliothèque ET recherche)
  const displayedBooks = useMemo(() => {
    if (searchHook.isSearchMode) {
      const rawBooks = (searchHook.openLibraryResults || []).filter(item => !item.isSeriesCard);
      return BookActions.createUnifiedDisplay(rawBooks, getCategoryBadgeFromBook, [], {});
    }
    return createUnifiedDisplay(filteredBooks || []);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchHook.isSearchMode, searchHook.openLibraryResults, filteredBooks, activeTab, unifiedContent.userSeriesLibrary]);

  const groupedBooks = useMemo(() => {
    if (searchHook.isSearchMode) {
      return { all: displayedBooks };
    }
    const groups = { reading: [], to_read: [], completed: [] };
    displayedBooks.forEach(book => {
      const status = book.status || 'to_read';
      (groups[status] || groups.to_read).push(book);
    });
    const sortGroup = (arr) => [...arr].sort((a, b) => {
      if (a.isSeriesCard && !b.isSeriesCard) return -1;
      if (!a.isSeriesCard && b.isSeriesCard) return 1;
      return new Date(b.date_added || b.updated_at || 0) - new Date(a.date_added || a.updated_at || 0);
    });
    Object.keys(groups).forEach(s => { groups[s] = sortGroup(groups[s]); });
    return groups;
  }, [displayedBooks, searchHook.isSearchMode]);
  const { sortConfig, setSortConfig, sortBooks } = useSectionSort();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
      {/* Mobile: overlay de recherche */}
      <MobileSearchOverlay
        isOpen={showMobileSearch}
        onClose={() => { setShowMobileSearch(false); setMobileTab('home'); }}
        searchTerm={searchHook.lastSearchTerm || ''}
        onSearchChange={searchHook.handleSearchTermChange}
        onSearch={(term) => {
          searchHook.handleSearchTermChange(term);
          searchOpenLibrary(term);
        }}
      />

      {/* Header desktop + mobile compact */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700 sticky top-0 z-30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Desktop header */}
          <div className="hidden md:flex justify-between items-center h-16">
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
                onClick={() => navigate('/recommendations')}
                className="flex items-center space-x-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors duration-200"
              >
                <span>Recommandations</span>
              </button>
              
              <button
                onClick={() => setShowProfileModal(true)}
                className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-full transition-colors duration-200"
              >
                {user?.email?.[0]?.toUpperCase() || '?'}{(user?.email?.[1] || '')?.toUpperCase() || ''}
              </button>
            </div>
          </div>

          {/* Mobile header */}
          <div className="flex md:hidden justify-between items-center h-12">
            <div className="flex items-center gap-2">
              <span className="text-xl">🐝</span>
              <h1 className="text-base font-bold text-gray-900 dark:text-white">BOOKTIME</h1>
            </div>
            <button
              onClick={() => setShowMobileSearch(true)}
              className="p-2 text-gray-500 dark:text-gray-400"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto pb-16 md:pb-0">
        <div className="px-4 sm:px-6 lg:px-8">
          {/* Mode recherche */}
          {searchHook.isSearchMode && (
            <div className="py-3 sm:py-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4 sm:mb-6">
                <div>
                  <h2 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">
                    Résultats pour "{searchHook.lastSearchTerm}"
                  </h2>
                  <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400">
                    {displayedBooks.length} résultat(s) trouvé(s)
                  </p>
                </div>
                <button
                  onClick={backToLibrary}
                  className="self-start sm:self-auto px-3 sm:px-4 py-1.5 sm:py-2 text-sm bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors duration-200"
                >
                  ← Retour
                </button>
              </div>
            </div>
          )}
          
          {/* Mode bibliothèque */}
          {!searchHook.isSearchMode && (
            <div className="py-3 sm:py-6">
              {/* Onglets de navigation */}
              <div className="flex justify-between items-center mb-4 sm:mb-6">
                {/* Onglets principaux : scroll horizontal sur mobile */}
                <div className="flex space-x-1 overflow-x-auto scrollbar-hide mobile-scroll-x pb-1 sm:pb-0 flex-1 mr-2">
                  {TAB_CONFIG.filter(tab => tab.key !== 'upcoming').map((tab) => (
                    <button
                      key={tab.key}
                      onClick={() => handleTabChange(tab.key)}
                      className={`flex-shrink-0 px-3 sm:px-4 py-2 rounded-lg font-medium transition-colors duration-200 text-sm sm:text-base ${
                        activeTab === tab.key
                          ? 'bg-green-600 text-white'
                          : 'bg-gray-200 hover:bg-gray-300 text-gray-700 dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-gray-300'
                      }`}
                    >
                      {tab.label}
                    </button>
                  ))}
                </div>
                
                {/* Bouton "À venir" — desktop uniquement (mobile = bottom nav) */}
                <button
                  onClick={() => setShowUpcomingPanel(true)}
                  className="hidden md:flex px-4 py-2 rounded-lg font-medium transition-colors duration-200 bg-purple-100 hover:bg-purple-200 text-purple-700 dark:bg-purple-900/20 dark:hover:bg-purple-800/30 dark:text-purple-300"
                >
                  <span>À venir</span>
                </button>
              </div>
              
              {/* Statistiques filtrées par onglet actif */}
              {!searchHook.isSearchMode && (() => {
                const completed = (groupedBooks.completed || []).length;
                const reading   = (groupedBooks.reading   || []).length;
                const toRead    = (groupedBooks.to_read   || []).length;
                const total     = completed + reading + toRead;
                return (
                  <div className="flex flex-wrap gap-2 sm:gap-3 mb-4 sm:mb-6">
                    {[
                      { value: total,     label: 'Total',    color: 'text-gray-700 dark:text-gray-200',     bg: 'bg-white dark:bg-gray-800',           border: 'border-gray-200 dark:border-gray-700'  },
                      { value: completed, label: 'Terminés', color: 'text-green-600 dark:text-green-400',   bg: 'bg-green-50 dark:bg-green-900/20',    border: 'border-green-200 dark:border-green-800' },
                      { value: reading,   label: 'En cours', color: 'text-blue-600 dark:text-blue-400',     bg: 'bg-blue-50 dark:bg-blue-900/20',      border: 'border-blue-200 dark:border-blue-800'   },
                      { value: toRead,    label: 'À lire',   color: 'text-orange-600 dark:text-orange-400', bg: 'bg-orange-50 dark:bg-orange-900/20',  border: 'border-orange-200 dark:border-orange-800'},
                    ].map((s, i) => (
                      <div key={s.label} className={`flex items-center gap-2 px-4 py-2 rounded-full border ${s.bg} ${s.border} shadow-sm section-appear`} style={{ animationDelay: `${i * 80}ms` }}>
                        <AnimatedCounter value={s.value} className={`text-xl font-bold ${s.color}`} />
                        <span className={`text-sm ${s.color} opacity-80`}>{s.label}</span>
                      </div>
                    ))}
                  </div>
                );
              })()}
            </div>
          )}
          
          {/* Affichage par sections de statut - MODIFICATION ORGANISATIONNELLE */}
          {!searchHook.isSearchMode && (
            <div className="space-y-6 sm:space-y-8">

              {/* Erreur de chargement */}
              {unifiedContent.error && !unifiedContent.loading && (
                <div className="flex items-center gap-3 rounded-lg border border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20 px-4 py-3 text-sm text-red-700 dark:text-red-300">
                  <span>⚠️</span>
                  <span>Impossible de charger ta bibliothèque. Vérifie ta connexion et <button className="underline font-medium" onClick={() => unifiedContent.loadUnifiedContent({ forceRefresh: true })}>réessaie</button>.</span>
                </div>
              )}

              {/* Skeleton de chargement initial */}
              {unifiedContent.loading && (
                <div className="grid grid-cols-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-2 sm:gap-5 p-2 sm:p-6">
                  {Array.from({ length: 12 }).map((_, i) => (
                    <div key={i} className="animate-pulse">
                      <div className="bg-gray-200 dark:bg-gray-700 rounded-lg aspect-[3/4] mb-2" />
                      <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded mb-1" />
                      <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-2/3" />
                    </div>
                  ))}
                </div>
              )}

              {/* Section EN COURS */}
              {!unifiedContent.loading && groupedBooks.reading && groupedBooks.reading.length > 0 && (
                <div className="section-appear">
                  <div className="flex items-center mb-3 sm:mb-4 flex-wrap gap-2">
                    <h2 className="text-base sm:text-xl font-semibold text-yellow-600 dark:text-yellow-400">
                      📖 En cours ({groupedBooks.reading.length})
                    </h2>
                    <SortControls sortConfig={sortConfig} setSortConfig={setSortConfig} />
                  </div>
                  <BookGrid
                    books={sortBooks(groupedBooks.reading)}
                    loading={false}
                    onItemClick={handleItemClick}
                    onAuthorClick={handleAuthorClick}
                    showEmptyState={false}
                  />
                </div>
              )}

              {/* Section À LIRE */}
              {!unifiedContent.loading && groupedBooks.to_read && groupedBooks.to_read.length > 0 && (
                <div className="section-appear" style={{ animationDelay: '80ms' }}>
                  <div className="flex items-center mb-4 flex-wrap gap-2">
                    <h2 className="text-xl font-semibold text-blue-600 dark:text-blue-400">
                      📌 À lire ({groupedBooks.to_read.length})
                    </h2>
                    <SortControls sortConfig={sortConfig} setSortConfig={setSortConfig} />
                  </div>
                  <BookGrid
                    books={sortBooks(groupedBooks.to_read)}
                    loading={false}
                    onItemClick={handleItemClick}
                    onAuthorClick={handleAuthorClick}
                    showEmptyState={false}
                  />
                </div>
              )}

              {/* Section TERMINÉ */}
              {!unifiedContent.loading && groupedBooks.completed && groupedBooks.completed.length > 0 && (
                <div className="section-appear" style={{ animationDelay: '160ms' }}>
                  <div className="flex items-center mb-4 flex-wrap gap-2">
                    <h2 className="text-xl font-semibold text-green-600 dark:text-green-400">
                      ✅ Terminé ({groupedBooks.completed.length})
                    </h2>
                    <SortControls sortConfig={sortConfig} setSortConfig={setSortConfig} />
                  </div>
                  <BookGrid
                    books={sortBooks(groupedBooks.completed)}
                    loading={false}
                    onItemClick={handleItemClick}
                    onAuthorClick={handleAuthorClick}
                    showEmptyState={false}
                  />
                </div>
              )}

              {/* Section Découvrir — toujours visible en bas pour découvrir plus */}
              {!unifiedContent.loading && ((groupedBooks.reading?.length || 0) + (groupedBooks.to_read?.length || 0) + (groupedBooks.completed?.length || 0)) < 10 && (
                <div className="section-appear mt-4 pt-6 border-t border-gray-100 dark:border-gray-800" style={{ animationDelay: '240ms' }}>
                  <DiscoverSection
                    activeCategory={activeTab}
                    userBooks={unifiedContent.books || []}
                    onBookAdded={() => unifiedContent.refreshAfterAdd('books')}
                  />
                </div>
              )}

              {/* Section Découvrir — affichée quand la bibliothèque est vide */}
              {!unifiedContent.loading &&
               (!groupedBooks.reading || groupedBooks.reading.length === 0) &&
               (!groupedBooks.to_read || groupedBooks.to_read.length === 0) &&
               (!groupedBooks.completed || groupedBooks.completed.length === 0) && (
                <div className="section-appear">
                  <div className="text-center py-8 mb-6">
                    <div className="text-5xl mb-3">📚</div>
                    <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-1">
                      Ta bibliothèque est vide
                    </h3>
                    <p className="text-gray-500 dark:text-gray-400 text-sm">
                      Découvre des livres populaires et ajoute-les à ta collection !
                    </p>
                  </div>
                  <DiscoverSection
                    activeCategory={activeTab}
                    userBooks={unifiedContent.books || []}
                    onBookAdded={() => unifiedContent.refreshAfterAdd('books')}
                  />
                </div>
              )}
            </div>
          )}

          {/* Mode recherche - Grille unique avec données unifiées */}
          {searchHook.isSearchMode && (
            <BookGrid
              books={displayedBooks}
              loading={unifiedContent.loading}
              onItemClick={handleItemClick}
              onAuthorClick={handleAuthorClick}
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
          onUpdate={handleUpdateBookOptimistic}
          onDelete={booksHook.handleDeleteBook}
          onAddFromOpenLibrary={handleAddFromOpenLibrary}
          onAuthorClick={handleAuthorClick}
        />
      )}
      
      {seriesHook.showSeriesModal && seriesHook.selectedSeries && (
        <SeriesDetailModal
          series={seriesHook.selectedSeries}
          isOpen={seriesHook.showSeriesModal}
          onClose={seriesHook.closeSeriesModal}
          onUpdate={() => unifiedContent.loadUnifiedContent({ forceRefresh: true })}
          onDelete={() => {
            seriesHook.closeSeriesModal();
            unifiedContent.loadUnifiedContent({ forceRefresh: true });
          }}
          onAddSeries={handleAddSeries}
          onAuthorClick={handleAuthorClick}
          userSeriesLibrary={unifiedContent.userSeriesLibrary || []}
        />
      )}
      
      {showAuthorModal && selectedAuthor && (
        <AuthorModal
          author={selectedAuthor}
          isOpen={showAuthorModal}
          onClose={handleCloseAuthorModal}
          userBooks={unifiedContent.books || []}
          onAddBook={async (bookData) => { await BookActions.addBook(bookData); await unifiedContent.refreshAfterAdd('books'); }}
          onOpenSeries={(series) => {
            seriesHook.setSelectedSeries(series);
            seriesHook.setShowSeriesModal(true);
          }}
          onAddSeries={async (series) => {
            await seriesHook.handleAddSeriesToLibrary(series);
            await unifiedContent.refreshAfterAdd('series');
          }}
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
              // PHASE C.2 : Utiliser rafraîchissement optimisé avec cache intelligent
              await unifiedContent.refreshAfterAdd('books', {
                expectNewItem: true,
                maxRetries: 2,
                retryDelay: 800
              });
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
              // PHASE C.2 : Utiliser rafraîchissement optimisé avec cache intelligent
              await unifiedContent.refreshAfterAdd('books', {
                expectNewItem: true,
                maxRetries: 2,
                retryDelay: 800
              });
            } catch (error) {
              console.error('Erreur lors de l\'ajout des livres:', error);
            }
          }}
        />
      )}
      
      {/* Toast notifications */}
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: { marginBottom: 'calc(4rem + env(safe-area-inset-bottom))' }
        }}
        containerStyle={{ bottom: 0 }}
      />
      
      {/* Panneau "À venir" */}
      <UpcomingPanel
        isOpen={showUpcomingPanel}
        onClose={() => setShowUpcomingPanel(false)}
        userBooks={unifiedContent.books || []}
      />
      
      {/* PHASE 2.4 - Performance Widget */}
      <PerformanceWidget position="bottom-right" isVisible={false} />

      {/* Navigation mobile bas d'écran */}
      <MobileBottomNav
        activeTab={mobileTab}
        onTabChange={handleMobileTabChange}
      />
    </div>
  );
}

// Main App Component
function App() {
  return (
    <Router future={{ 
      v7_startTransition: true,
      v7_relativeSplatPath: true 
    }}>
      <ThemeProvider>
        <AuthProvider>
          <ErrorBoundary>
            <Routes>
              <Route path="/" element={<AppWithAuth />} />
              <Route path="/reset-password" element={<ResetPasswordPage />} />
              <Route path="/recommendations" element={<RecommendationPage />} />
              <Route path="/series/:seriesId" element={<SeriesDetailPage />} />
              <Route path="/catalogue/*" element={<OpenLibraryBookPage />} />
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
