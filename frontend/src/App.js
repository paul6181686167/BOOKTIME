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
import ProfileModal from './components/common/ProfileModal';

// Service imports
import { bookService } from './services/bookService';
import * as seriesLibraryService from './services/seriesLibraryService';

// Hook imports
import { useAdvancedSearch } from './hooks/useAdvancedSearch';
import { useGroupedSearch } from './hooks/useGroupedSearch';
import SearchOptimizer from './utils/searchOptimizer';

// Search components imports (Phase 1.1 - Step 3)
import { calculateRelevanceScore, getRelevanceLevel } from './components/search/RelevanceEngine';
import SearchLogic from './components/search/SearchLogic';

// Series components imports (Phase 1.1 - Step 4)
import SeriesActions from './components/series/SeriesActions';
import SeriesGrid, { mergeSeriesAndBooks } from './components/series/SeriesGrid';

// Books components imports (Phase 1.1 - Step 5)
import BookActions from './components/books/BookActions';

import './App.css';

// LoginModal Component (removed - now using LoginPage component)

// Profile Modal Component (moved to components/common/ProfileModal.js)

// Main App Content
function AppContent() {
  return (
    <Routes>
      <Route path="/" element={<MainApp />} />
      <Route path="/series/:seriesName" element={<SeriesDetailPage />} />
    </Routes>
  );
}

// Composant principal de l'application
function MainApp() {
  const { user } = useAuth();
  const [books, setBooks] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('roman');
  const [showProfileModal, setShowProfileModal] = useState(false);

  const [selectedBook, setSelectedBook] = useState(null);
  const [showBookModal, setShowBookModal] = useState(false);

  // États pour la recherche Open Library
  const [openLibraryResults, setOpenLibraryResults] = useState([]);
  const [detectedSeries, setDetectedSeries] = useState([]);
  const [isSearchMode, setIsSearchMode] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [lastSearchTerm, setLastSearchTerm] = useState('');
  // SUPPRESSION VIEWMODE : Plus de toggle livre/série - affichage unifié
  const [addingBooks, setAddingBooks] = useState(new Set()); // Suivi des livres en cours d'ajout

  // État pour les séries simplifiées
  const [selectedSeries, setSelectedSeries] = useState(null);
  const [showSeriesDetail, setShowSeriesDetail] = useState(false);
  const [showSeriesModal, setShowSeriesModal] = useState(false);

  // États pour les séries en bibliothèque
  const [userSeriesLibrary, setUserSeriesLibrary] = useState([]);
  const [seriesLibraryLoading, setSeriesLibraryLoading] = useState(false);

  // Hook de recherche avancée
  const {
    filters,
    setFilters,
    filteredBooks,
    searchStats,
    clearSearch
  } = useAdvancedSearch(books);

  // Hook de recherche groupée
  const {
    groupedResults,
    searchStats: groupedSearchStats,
  } = useGroupedSearch();

  // AFFICHAGE UNIFIÉ : Plus besoin de paramètre viewMode - simplifié
  const loadBooks = async () => {
    await BookActions.loadBooks(setLoading, setBooks);
  };

  const loadStats = async () => {
    await BookActions.loadStats(setStats);
  };

  // Fonction pour rechercher des séries
  const searchSeries = async (query) => {
    return await BookActions.searchSeries(query);
  };

  // Fonction modifiée pour la recherche Open Library incluant les séries

  // Fonction pour créer les cartes séries à partir des résultats détectés avec scoring prioritaire optimisé
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
      // SCORING PRIORITAIRE : Les séries ont déjà des scores 100000+, on garde ce score
      relevanceScore: detected.confidence, // Utilise directement le score prioritaire (100000+)
      relevanceInfo: { 
        level: 'prioritaire', 
        label: detected.matchType === 'exact_match' ? 'Série (correspondance exacte)' : 
               detected.matchType === 'fuzzy_match' ? 'Série (correspondance approximative)' : 'Série détectée',
        color: 'bg-purple-600', 
        icon: '📚' 
      }
    }));
  };

  // FONCTION UTILITAIRE : Déterminer le badge de catégorie depuis un livre Open Library
  const getCategoryBadgeFromBook = (book) => {
    // Si la catégorie est déjà définie dans le livre
    if (book.category) {
      switch (book.category.toLowerCase()) {
        case 'roman':
          return { key: 'roman', text: 'Roman', class: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300', emoji: '📚' };
        case 'bd':
          return { key: 'bd', text: 'BD', class: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300', emoji: '🎨' };
        case 'manga':
          return { key: 'manga', text: 'Manga', class: 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-300', emoji: '🇯🇵' };
      }
    }
    
    // Sinon, détecter automatiquement basé sur le titre et la description
    const title = (book.title || '').toLowerCase();
    const description = (book.description || '').toLowerCase();
    const subjects = (book.subjects || []).join(' ').toLowerCase();
    const allText = `${title} ${description} ${subjects}`;
    
    // Détection Manga
    if (allText.includes('manga') || allText.includes('japonais') || allText.includes('japan') || 
        allText.includes('anime') || allText.includes('otaku') || allText.includes('shonen') || 
        allText.includes('shojo') || allText.includes('seinen') || allText.includes('josei')) {
      return { key: 'manga', text: 'Manga', class: 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-300', emoji: '🇯🇵' };
    }
    
    // Détection BD
    if (allText.includes('bande dessinée') || allText.includes('comic') || allText.includes('comics') || 
        allText.includes('graphic novel') || allText.includes('bd') || allText.includes('illustration') ||
        allText.includes('dessins') || allText.includes('album')) {
      return { key: 'bd', text: 'BD', class: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300', emoji: '🎨' };
    }
    
    // Par défaut : Roman
    return { key: 'roman', text: 'Roman', class: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300', emoji: '📚' };
  };

  // FONCTION AFFICHAGE UNIFIÉ : Mélange séries et livres individuels par date d'ajout
  const createUnifiedDisplay = (booksList) => {
    return BookActions.createUnifiedDisplay(booksList, getCategoryBadgeFromBook);
  };

  // FONCTION OPTIMISÉE : Génération cartes séries avec algorithme avancé et scoring prioritaire
  const generateSeriesCardsForSearch = (query, books) => {
    console.log('🚀 OPTIMISATION RECHERCHE - Génération cartes séries avec algorithme avancé');
    
    // Utiliser le nouvel optimiseur de recherche avec scoring prioritaire 100000+
    const startTime = performance.now();
    const seriesCards = SearchOptimizer.generateSeriesCardsForSearch(query, books);
    const detectionTime = performance.now() - startTime;
    
    // Logging des métriques pour monitoring
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

  // Fonction pour rechercher dans Open Library avec RECHERCHE GLOBALE (toutes catégories)
  // Fonction searchOpenLibrary déplacée vers SearchLogic.js (Phase 1.1 - Step 3)
  const searchOpenLibrary = async (query) => {
    await SearchLogic.searchOpenLibrary(query, {
      books,
      setSearchLoading,
      setIsSearchMode,
      setLastSearchTerm,
      setOpenLibraryResults,
      generateSeriesCardsForSearch,
      handleAddSeriesToLibrary,
      getCategoryBadgeFromBook
    });
  };

  // Gestionnaire stable pour éviter les re-rendus excessifs
  const handleSearchTermChange = useCallback((term) => {
    setLastSearchTerm(term);
  }, []);

  // Fonction backToLibrary déplacée vers SearchLogic.js (Phase 1.1 - Step 3)
  const backToLibrary = () => {
    SearchLogic.backToLibrary(setIsSearchMode, setOpenLibraryResults, setLastSearchTerm, clearSearch);
  };

  // Fonction handleAddFromOpenLibrary déplacée vers SearchLogic.js (Phase 1.1 - Step 3)
  const handleAddFromOpenLibrary = async (openLibraryBook) => {
    await SearchLogic.handleAddFromOpenLibrary(openLibraryBook, {
      books,
      addingBooks,
      setAddingBooks,
      activeTab,
      getCategoryBadgeFromBook,
      loadBooks,
      loadStats,
      setOpenLibraryResults
    });
  };

  // Gestionnaires de clic déplacés vers SearchLogic.js (Phase 1.1 - Step 3)
  const handleSeriesClick = (series) => {
    SearchLogic.handleSeriesClick(series, setSelectedSeries, setShowSeriesModal);
  };

  const handleBookClick = (book) => {
    BookActions.handleBookClick(book, setSelectedBook, setShowBookModal);
  };

  const handleItemClick = (item) => {
    BookActions.handleItemClick(item, {
      setSelectedSeries,
      setShowSeriesModal,
      setSelectedBook,
      setShowBookModal
    });
  };

  const handleUpdateBook = async (bookId, bookData) => {
    await BookActions.handleUpdateBook(bookId, bookData, {
      setSelectedBook,
      loadBooks,
      loadStats
    });
  };

  const handleDeleteBook = async (bookId) => {
    await BookActions.handleDeleteBook(bookId, {
      setSelectedBook,
      setShowBookModal,
      loadBooks,
      loadStats
    });
  };

  // ============================================================================
  // GESTION DES SÉRIES EN BIBLIOTHÈQUE - EXTRACTED TO SeriesActions.js
  // ============================================================================

  // Charger les séries de la bibliothèque utilisateur
  const loadUserSeriesLibrary = async () => {
    await SeriesActions.loadUserSeriesLibrary(setSeriesLibraryLoading, setUserSeriesLibrary);
  };

  // Ajouter une série complète à la bibliothèque avec enrichissement automatique
  const handleAddSeriesToLibrary = async (seriesData) => {
    await SeriesActions.handleAddSeriesToLibrary(seriesData, {
      setSeriesLibraryLoading,
      loadUserSeriesLibrary
    });
  };

  // Mettre à jour le statut d'un tome
  const handleUpdateVolumeStatus = async (seriesId, volumeNumber, isRead) => {
    await SeriesActions.handleUpdateVolumeStatus(seriesId, volumeNumber, isRead, setUserSeriesLibrary);
  };

  // Mettre à jour le statut global d'une série
  const handleUpdateSeriesStatus = async (seriesId, newStatus) => {
    await SeriesActions.handleUpdateSeriesStatus(seriesId, newStatus, setUserSeriesLibrary);
  };

  // Supprimer une série de la bibliothèque
  const handleDeleteSeriesFromLibrary = async (seriesId) => {
    await SeriesActions.handleDeleteSeriesFromLibrary(seriesId, setUserSeriesLibrary);
  };

  // ============================================================================
  // FIN GESTION DES SÉRIES EN BIBLIOTHÈQUE
  // ============================================================================

  // Fonctions calculateRelevanceScore et getRelevanceLevel déplacées vers RelevanceEngine.js (Phase 1.1 - Step 3)
  // Voir /app/frontend/src/components/search/RelevanceEngine.js pour le moteur de pertinence complet

  // AFFICHAGE INTELLIGENT : Recherche vs Bibliothèque avec regroupement séries
  const displayedBooks = isSearchMode 
    ? [
        // RECHERCHE GLOBALE : Combiner TOUS les livres (toutes catégories)
        ...books.filter(book => {
          if (!lastSearchTerm) return false;
          const term = lastSearchTerm.toLowerCase();
          return (
            (book.title || '').toLowerCase().includes(term) ||
            (book.author || '').toLowerCase().includes(term) ||
            (book.saga || '').toLowerCase().includes(term)
          );
        }).map(book => ({ ...book, isFromOpenLibrary: false, isOwned: true })),
        ...openLibraryResults // Tous les livres Open Library (contient déjà les cartes séries)
      ].map(book => ({
        ...book,
        relevanceScore: calculateRelevanceScore(book, lastSearchTerm),
        relevanceInfo: getRelevanceLevel(calculateRelevanceScore(book, lastSearchTerm))
      }))
      .sort((a, b) => {
        // 1. PRIORITÉ ABSOLUE : Les cartes séries en PREMIER
        if (a.isSeriesCard && !b.isSeriesCard) {
          return -1; // a (série) avant b (livre)
        }
        if (!a.isSeriesCard && b.isSeriesCard) {
          return 1; // b (série) avant a (livre)
        }
        
        // 2. Entre séries : trier par score de pertinence
        if (a.isSeriesCard && b.isSeriesCard) {
          return b.relevanceScore - a.relevanceScore;
        }
        
        // 3. Entre livres : trier par score de pertinence décroissant
        if (a.relevanceScore !== b.relevanceScore) {
          return b.relevanceScore - a.relevanceScore;
        }
        
        // 4. En cas d'égalité de score, prioriser les livres locaux
        if (a.isFromOpenLibrary !== b.isFromOpenLibrary) {
          return a.isFromOpenLibrary ? 1 : -1;
        }
        
        // 5. Pour les livres Open Library, prioriser ceux déjà possédés
        if (a.isFromOpenLibrary && b.isFromOpenLibrary) {
          if (a.isOwned !== b.isOwned) {
            return a.isOwned ? -1 : 1;
          }
        }
        
        // 6. Trier par qualité des métadonnées (livres avec plus d'infos en premier)
        const qualityScoreA = (a.cover_url ? 10 : 0) + (a.description?.length > 100 ? 5 : 0) + (a.first_publish_year ? 3 : 0);
        const qualityScoreB = (b.cover_url ? 10 : 0) + (b.description?.length > 100 ? 5 : 0) + (b.first_publish_year ? 3 : 0);
        
        if (qualityScoreA !== qualityScoreB) {
          return qualityScoreB - qualityScoreA;
        }
        
        // 7. Trier par année de publication (plus récent en premier pour les livres de qualité égale)
        if (a.first_publish_year && b.first_publish_year) {
          return b.first_publish_year - a.first_publish_year;
        }
        
        // 8. Finalement, trier par titre alphabétique
        return (a.title || '').localeCompare(b.title || '', 'fr', { numeric: true });
      })
      // Filtrer les résultats avec un score minimum pour éviter le bruit
      .filter(book => !lastSearchTerm || book.relevanceScore >= 10)
    : // BIBLIOTHÈQUE UNIFIÉE : Séries et livres individuels mélangés par date d'ajout
        mergeSeriesAndBooks(userSeriesLibrary, filteredBooks, activeTab);

  // Header Component avec barre de recherche unifiée
  const Header = () => (
    <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          <div className="flex items-center space-x-6">
            {/* Logo */}
            <div className="flex items-center space-x-3 text-2xl font-bold text-green-600 dark:text-green-400">
              <div className="w-10 h-10 bg-green-600 rounded-lg flex items-center justify-center text-white text-xl">
                🐝
              </div>
              BookTime
            </div>
            
            {/* Barre de recherche unifiée compacte */}
            <UnifiedSearchBar
              searchTerm={lastSearchTerm}
              onSearchChange={handleSearchTermChange}
              onOpenLibrarySearch={searchOpenLibrary}
              books={books}
              filters={filters}
              onFiltersChange={setFilters}
              isCompact={true}
            />
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowProfileModal(true)}
              className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors"
            >
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-medium text-sm">
                {user?.first_name?.charAt(0).toUpperCase()}{user?.last_name?.charAt(0).toUpperCase()}
              </div>
              <span>Profil</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );

  // Tab Navigation Component avec toggle Vue Livres/Séries
  const TabNavigation = () => (
    <div className="mb-6">
      <div className="border-b border-gray-200 dark:border-gray-700">
        <div className="flex justify-between items-center">
          <nav className="-mb-px flex space-x-12">
            {[
              { key: 'roman', label: 'Roman' },
              { key: 'bd', label: 'Bande Dessinée' },
              { key: 'manga', label: 'Manga' }
            ].map((category) => (
              <button
                key={category.key}
                onClick={() => setActiveTab(category.key)}
                className={`py-3 px-2 border-b-2 font-medium text-lg ${
                  activeTab === category.key
                    ? 'border-green-500 text-green-600 dark:text-green-400'
                    : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                {category.label}
              </button>
            ))}
          </nav>
          
          {/* SUPPRESSION TOGGLE : Plus de toggle Vue Livres/Séries - affichage unifié */}
        </div>
      </div>
    </div>
  );

  // Chargement initial des livres et statistiques
  useEffect(() => {
    if (user) {
      loadBooks();
      loadStats();
      loadUserSeriesLibrary(); // Charger aussi les séries de la bibliothèque
    }
  }, [user]); // SUPPRESSION VIEWMODE des dépendances

  // Rechargement des livres quand l'onglet change
  useEffect(() => {
    if (user) {
      loadBooks();
      loadUserSeriesLibrary(); // Recharger aussi les séries quand l'onglet change
    }
  }, [activeTab]); // SUPPRESSION VIEWMODE des dépendances

  // Rendu principal
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Contenu principal */}
        <div className="space-y-8">
          {/* Navigation par onglets */}
          {!isSearchMode && <TabNavigation />}
          
          {/* Bouton Retour à la bibliothèque (en mode recherche) */}
          {isSearchMode && (
            <div className="mb-6">
              <button
                onClick={backToLibrary}
                className="inline-flex items-center px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                ← Retour à ma bibliothèque
              </button>
            </div>
          )}
          
          {/* Statistiques de recherche (en mode recherche) */}
          {isSearchMode && (
            <div className="mb-6">
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                <h3 className="text-sm font-medium text-blue-900 dark:text-blue-200 mb-2">
                  📊 Résultats pour "{lastSearchTerm}"
                </h3>
                <div className="flex flex-wrap gap-4 text-sm text-blue-700 dark:text-blue-300">
                  <span>
                    {books.filter(book => {
                      const term = lastSearchTerm.toLowerCase();
                      return (
                        (book.title || '').toLowerCase().includes(term) ||
                        (book.author || '').toLowerCase().includes(term) ||
                        (book.saga || '').toLowerCase().includes(term)
                      );
                    }).length} dans ma bibliothèque
                  </span>
                  <span>
                    {openLibraryResults.filter(book => !book.isSeriesCard).length} sur Open Library
                  </span>
                  {openLibraryResults.some(book => book.isSeriesCard) && (
                    <span>
                      {openLibraryResults.filter(book => book.isSeriesCard).length} série(s) détectée(s)
                    </span>
                  )}
                </div>
                <div className="mt-2 text-sm text-blue-700 dark:text-blue-300 font-medium">
                  Résultats classés par pertinence
                </div>
                {displayedBooks.some(book => book.relevanceScore >= 30000) && (
                  <div className="mt-1 text-xs text-green-600 dark:text-green-400">
                    Correspondances exactes trouvées
                  </div>
                )}
              </div>
            </div>
          )}
          
          {/* Grille de livres/séries */}
          <SeriesGrid
            displayedBooks={displayedBooks}
            loading={loading}
            handleItemClick={handleItemClick}
            handleAddSeriesToLibrary={handleAddSeriesToLibrary}
            handleUpdateVolumeStatus={handleUpdateVolumeStatus}
            handleUpdateSeriesStatus={handleUpdateSeriesStatus}
            handleDeleteSeriesFromLibrary={handleDeleteSeriesFromLibrary}
          />
        </div>
      </main>
      
      {/* Modals */}
      {showBookModal && selectedBook && (
        <BookDetailModal
          book={selectedBook}
          isOpen={showBookModal}
          onClose={() => {
            setSelectedBook(null);
            setShowBookModal(false);
          }}
          onUpdate={handleUpdateBook}
          onDelete={handleDeleteBook}
          onAddFromOpenLibrary={handleAddFromOpenLibrary}
        />
      )}
      
      {showSeriesModal && selectedSeries && (
        <SeriesDetailModal
          series={selectedSeries}
          isOpen={showSeriesModal}
          onClose={() => {
            setSelectedSeries(null);
            setShowSeriesModal(false);
          }}
          onUpdate={loadBooks}
        />
      )}
      
      {showProfileModal && (
        <ProfileModal
          isOpen={showProfileModal}
          onClose={() => setShowProfileModal(false)}
        />
      )}
      
      {/* Toast notifications */}
      <Toaster position="bottom-right" />
    </div>
  );
}

// Main App Component
function App() {
  return (
    <Router>
      <ThemeProvider>
        <AuthProvider>
          <AppWithAuth />
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