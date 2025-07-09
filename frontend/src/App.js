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

// Service imports
import { bookService } from './services/bookService';
import * as seriesLibraryService from './services/seriesLibraryService';

// Hook imports
import { useAdvancedSearch } from './hooks/useAdvancedSearch';
import { useGroupedSearch } from './hooks/useGroupedSearch';
import SearchOptimizer from './utils/searchOptimizer';

import './App.css';

// LoginModal Component (removed - now using LoginPage component)

// Profile Modal Component
function ProfileModal({ isOpen, onClose }) {
  const { user, logout } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isOpen) {
      loadStats();
    }
  }, [isOpen]);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await bookService.getStats();
      setStats(data);
    } catch (error) {
      console.error('Erreur lors du chargement des statistiques:', error);
      toast.error('Erreur lors du chargement des statistiques');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    onClose();
    toast.success('Déconnexion réussie');
  };

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-md max-h-[80vh] flex flex-col">
        <div className="flex-shrink-0 p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">Profil</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {user?.first_name} {user?.last_name}
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              ✕
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
              📊 Mes Statistiques
            </h3>
            
            {loading ? (
              <div className="space-y-2">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="h-3 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
                ))}
              </div>
            ) : (
              <div className="space-y-3">
                <div className="grid grid-cols-3 gap-2">
                  <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 text-center">
                    <div className="text-lg font-bold text-blue-600 dark:text-blue-400">
                      {stats.total_books || 0}
                    </div>
                    <div className="text-xs text-blue-600 dark:text-blue-400">Total</div>
                  </div>
                  <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 text-center">
                    <div className="text-lg font-bold text-green-600 dark:text-green-400">
                      {stats.completed_books || 0}
                    </div>
                    <div className="text-xs text-green-600 dark:text-green-400">Terminés</div>
                  </div>
                  <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-3 text-center">
                    <div className="text-lg font-bold text-orange-600 dark:text-orange-400">
                      {stats.reading_books || 0}
                    </div>
                    <div className="text-xs text-orange-600 dark:text-orange-400">En cours</div>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
              ⚙️ Paramètres
            </h3>
            
            <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
              <div>
                <span className="font-medium text-gray-900 dark:text-white text-sm">Mode sombre</span>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Basculer entre thème clair et sombre
                </p>
              </div>
              <button
                onClick={toggleTheme}
                className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                  isDark ? 'bg-blue-600' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${
                    isDark ? 'translate-x-5' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        <div className="flex-shrink-0 p-4 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={handleLogout}
            className="w-full bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg transition-colors text-sm"
          >
            Se déconnecter
          </button>
        </div>
      </div>
    </div>
  );
}

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
    try {
      setLoading(true);
      // Charger tous les livres sans distinction de mode d'affichage
      const data = await bookService.getBooks();
      setBooks(data);
    } catch (error) {
      console.error('Erreur lors du chargement des livres:', error);
      toast.error('Erreur lors du chargement des livres');
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const data = await bookService.getStats();
      setStats(data);
    } catch (error) {
      console.error('Erreur lors du chargement des statistiques:', error);
    }
  };

  // Fonction pour rechercher des séries
  const searchSeries = async (query) => {
    if (!query || query.trim().length < 2) return [];
    
    try {
      const token = localStorage.getItem('token');
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const response = await fetch(`${backendUrl}/api/series/search?q=${encodeURIComponent(query)}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        return data.series.map(series => ({
          ...series,
          isSeriesCard: true,
          isFromSearch: true
        }));
      }
      return [];
    } catch (error) {
      console.error('Erreur recherche séries:', error);
      return [];
    }
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
    const seriesGroups = {};
    const standaloneBooks = [];
    const unifiedItems = [];

    // 1. Identifier les séries et livres standalone
    booksList.forEach(book => {
      if (book.saga && book.saga.trim()) {
        const seriesKey = book.saga.toLowerCase().trim();
        if (!seriesGroups[seriesKey]) {
          seriesGroups[seriesKey] = {
            id: `unified-series-${seriesKey}`,
            isSeriesCard: true,
            isUnifiedSeries: true, // Marqueur pour série unifiée
            name: book.saga,
            title: book.saga,
            author: book.author,
            category: book.category,
            books: [],
            totalBooks: 0,
            completedBooks: 0,
            readingBooks: 0,
            toReadBooks: 0,
            cover_url: book.cover_url,
            progressPercent: 0,
            earliestDate: book.date_added || book.updated_at || new Date().toISOString() // Pour tri par date
          };
        }
        
        seriesGroups[seriesKey].books.push(book);
        seriesGroups[seriesKey].totalBooks += 1;
        
        // Mettre à jour la date la plus ancienne de la série
        const bookDate = book.date_added || book.updated_at || new Date().toISOString();
        if (bookDate < seriesGroups[seriesKey].earliestDate) {
          seriesGroups[seriesKey].earliestDate = bookDate;
        }
        
        // Compter les statuts
        switch (book.status) {
          case 'completed':
            seriesGroups[seriesKey].completedBooks += 1;
            break;
          case 'reading':
            seriesGroups[seriesKey].readingBooks += 1;
            break;
          case 'to_read':
            seriesGroups[seriesKey].toReadBooks += 1;
            break;
        }
        
        // Calculer le pourcentage de progression
        seriesGroups[seriesKey].progressPercent = Math.round(
          (seriesGroups[seriesKey].completedBooks / seriesGroups[seriesKey].totalBooks) * 100
        );
      } else {
        // Livre standalone (sans série)
        standaloneBooks.push({
          ...book,
          sortDate: book.date_added || book.updated_at || new Date().toISOString(),
          // Ajouter badge de catégorie pour cohérence avec fiches de recherche
          categoryBadge: getCategoryBadgeFromBook(book)
        });
      }
    });

    // 2. Convertir les séries en items avec date de tri
    const seriesItems = Object.values(seriesGroups).map(series => ({
      ...series,
      sortDate: series.earliestDate
    }));

    // 3. Combiner séries et livres standalone
    const allItems = [...seriesItems, ...standaloneBooks];

    // 4. Trier par date d'ajout (plus récent en premier)
    allItems.sort((a, b) => {
      const dateA = new Date(a.sortDate);
      const dateB = new Date(b.sortDate);
      return dateB - dateA; // Ordre décroissant (plus récent en premier)
    });

    return allItems;
  };

  // FONCTION BIBLIOTHÈQUE OBSOLÈTE : Remplacée par createUnifiedDisplay pour affichage unifié
  const groupBooksIntoSeries = (booksList) => {
    const seriesGroups = {};
    const standaloneBooks = [];

    booksList.forEach(book => {
      if (book.saga && book.saga.trim()) {
        const seriesKey = book.saga.toLowerCase().trim();
        if (!seriesGroups[seriesKey]) {
          seriesGroups[seriesKey] = {
            id: `library-series-${seriesKey}`,
            isSeriesCard: true,
            isLibrarySeries: true, // Marqueur pour série de bibliothèque
            name: book.saga,
            title: book.saga,
            author: book.author,
            category: book.category,
            books: [],
            totalBooks: 0,
            completedBooks: 0,
            readingBooks: 0,
            toReadBooks: 0,
            cover_url: book.cover_url, // Utiliser la couverture du premier livre
            // Progression
            progressPercent: 0
          };
        }
        
        seriesGroups[seriesKey].books.push(book);
        seriesGroups[seriesKey].totalBooks += 1;
        
        // Compter les statuts
        switch (book.status) {
          case 'completed':
            seriesGroups[seriesKey].completedBooks += 1;
            break;
          case 'reading':
            seriesGroups[seriesKey].readingBooks += 1;
            break;
          case 'to_read':
            seriesGroups[seriesKey].toReadBooks += 1;
            break;
        }
        
        // Calculer le pourcentage de progression
        seriesGroups[seriesKey].progressPercent = Math.round(
          (seriesGroups[seriesKey].completedBooks / seriesGroups[seriesKey].totalBooks) * 100
        );
      } else {
        // Livre standalone (sans série)
        standaloneBooks.push(book);
      }
    });

    // Convertir les groupes en tableau et trier par nombre de livres
    const seriesCards = Object.values(seriesGroups).sort((a, b) => b.totalBooks - a.totalBooks);
    
    return [...seriesCards, ...standaloneBooks];
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
  const searchOpenLibrary = async (query) => {
    console.log('🚀 searchOpenLibrary GLOBALE appelée avec:', query);
    if (!query.trim()) {
      console.log('❌ Recherche annulée: query vide');
      return;
    }
    
    try {
      console.log('✅ Début de la recherche globale Open Library (toutes catégories)');
      setSearchLoading(true);
      setIsSearchMode(true);
      setLastSearchTerm(query);
      
      const token = localStorage.getItem('token');
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      // RECHERCHE GLOBALE : pas de filtre par catégorie, recherche dans TOUTES les catégories
      const response = await fetch(`${backendUrl}/api/openlibrary/search?q=${encodeURIComponent(query)}&limit=40`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        
        // Générer automatiquement les cartes séries basées sur le terme de recherche
        const seriesCards = generateSeriesCardsForSearch(query, data.books).map(card => ({
          ...card,
          onAddToLibrary: handleAddSeriesToLibrary // Ajouter la callback pour le bouton
        }));
        
        // AJOUT DES BADGES CATÉGORIE : Marquer les livres avec leur catégorie et badge
        const resultsWithOwnership = data.books.map(book => {
          const isOwned = books.some(localBook => {
            // Normaliser les titres et auteurs pour la comparaison
            const normalizeString = (str) => {
              if (!str) return '';
              return str.toLowerCase()
                .trim()
                .replace(/[^\w\s]/g, '') // Supprimer la ponctuation
                .replace(/\s+/g, ' '); // Normaliser les espaces
            };
            
            const localTitle = normalizeString(localBook.title);
            const localAuthor = normalizeString(localBook.author);
            const openLibTitle = normalizeString(book.title);
            const openLibAuthor = normalizeString(book.author);
            
            // Vérification par ol_key d'abord (plus précise)
            if (localBook.ol_key && book.ol_key && localBook.ol_key === book.ol_key) {
              return true;
            }
            
            // Vérification par ISBN si disponible
            if (localBook.isbn && book.isbn && 
                localBook.isbn.replace(/[-\s]/g, '') === book.isbn.replace(/[-\s]/g, '')) {
              return true;
            }
            
            // Vérification par titre et auteur (comparaison exacte)
            if (localTitle === openLibTitle && localAuthor === openLibAuthor) {
              return true;
            }
            
            // Vérification par titre et auteur (comparaison flexible)
            // Le titre de Open Library doit contenir le titre local OU vice versa
            const titleMatch = (localTitle.includes(openLibTitle) || openLibTitle.includes(localTitle)) && 
                              (localTitle.length > 3 && openLibTitle.length > 3); // Éviter les correspondances trop courtes
            
            // L'auteur doit correspondre exactement ou l'un doit contenir l'autre
            const authorMatch = localAuthor === openLibAuthor || 
                               (localAuthor.includes(openLibAuthor) && openLibAuthor.length > 3) ||
                               (openLibAuthor.includes(localAuthor) && localAuthor.length > 3);
            
            return titleMatch && authorMatch;
          });
          
          // BADGES CATÉGORIE AUTOMATIQUES : Ajouter badge selon la catégorie détectée
          const categoryBadge = getCategoryBadgeFromBook(book);
          
          return {
            ...book,
            isFromOpenLibrary: true,
            isOwned: isOwned,
            id: `ol_${book.ol_key}`,
            // Badge catégorie pour affichage visuel
            categoryBadge: categoryBadge,
            // S'assurer que la catégorie est bien définie pour le placement intelligent
            category: book.category || categoryBadge.key || 'roman' // Défaut roman si non détecté
          };
        });
        
        // ALGORITHME DE TRI PRIORITAIRE OPTIMISÉ : Garantir fiches séries EN PREMIER avec scores 100000+
        const allResults = [...seriesCards, ...resultsWithOwnership];
        
        // TRI FINAL AVEC PRIORITÉ ABSOLUE DES SÉRIES selon les consignes du CHANGELOG
        // 1) Séries officielles (100000+) par pertinence
        // 2) Séries bibliothèque (90000+) par pertinence  
        // 3) Livres Open Library très pertinents (scores variables)
        // 4) Livres bibliothèque utilisateur (scores variables)
        const sortedResults = SearchOptimizer.applySuperiorSeriesPrioritySort(allResults);
        
        console.log('🎯 PRIORITÉ SÉRIES - Tri final appliqué:');
        sortedResults.slice(0, 5).forEach((item, index) => {
          console.log(`${index + 1}. ${item.isSeriesCard ? '📚 SÉRIE' : '📖 LIVRE'}: ${item.title || item.name} - Score: ${item.relevanceScore || item.confidence || 0}`);
        });
        
        // Stocker les résultats triés avec priorité absolue aux fiches séries
        setOpenLibraryResults(sortedResults);
        toast.success(`${data.books.length} livres trouvés${seriesCards.length > 0 ? ` + ${seriesCards.length} série(s) détectée(s) EN PREMIER` : ''}`);
      } else {
        toast.error('Erreur lors de la recherche Open Library');
      }
    } catch (error) {
      console.error('Erreur recherche Open Library:', error);
      toast.error('Erreur lors de la recherche Open Library');
    } finally {
      setSearchLoading(false);
    }
  };

  // Gestionnaire stable pour éviter les re-rendus excessifs
  const handleSearchTermChange = useCallback((term) => {
    setLastSearchTerm(term);
  }, []);

  // Fonction pour revenir à la bibliothèque locale
  const backToLibrary = () => {
    setIsSearchMode(false);
    setOpenLibraryResults([]);
    setLastSearchTerm('');
    clearSearch();
  };

  // AJOUT INTELLIGENT : Placement automatique dans le bon onglet selon la catégorie
  const handleAddFromOpenLibrary = async (openLibraryBook) => {
    // Empêcher les clics multiples sur le même livre
    if (addingBooks.has(openLibraryBook.ol_key)) {
      return; // Si le livre est déjà en cours d'ajout, ne rien faire
    }

    try {
      // Marquer le livre comme en cours d'ajout
      setAddingBooks(prev => new Set([...prev, openLibraryBook.ol_key]));
      
      const token = localStorage.getItem('token');
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      // PLACEMENT INTELLIGENT : Déterminer la catégorie automatiquement via le badge
      const categoryBadge = openLibraryBook.categoryBadge || getCategoryBadgeFromBook(openLibraryBook);
      let targetCategory = categoryBadge.key; // Utiliser la catégorie détectée par le badge
      
      // Validation : s'assurer que la catégorie est valide
      if (!targetCategory || !['roman', 'bd', 'manga'].includes(targetCategory)) {
        // Si pas de catégorie ou catégorie invalide, utiliser l'onglet actuel par défaut
        targetCategory = activeTab;
      }
      
      const response = await fetch(`${backendUrl}/api/openlibrary/import`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ol_key: openLibraryBook.ol_key,
          category: targetCategory
        })
      });

      if (response.ok) {
        await loadBooks();
        await loadStats();
        
        // Message de succès avec indication de l'onglet
        const categoryLabels = {
          'roman': 'Roman',
          'bd': 'BD',
          'manga': 'Manga'
        };
        toast.success(`"${openLibraryBook.title}" ajouté à l'onglet ${categoryLabels[targetCategory]} !`);
        
        // Mettre à jour le statut de possession dans les résultats
        setOpenLibraryResults(prev => 
          prev.map(book => 
            book.ol_key === openLibraryBook.ol_key 
              ? { ...book, isOwned: true }
              : book
          )
        );
      } else {
        const error = await response.json();
        if (response.status === 409) {
          toast.error('Ce livre est déjà dans votre collection');
          // Marquer le livre comme possédé même si l'ajout a échoué pour cause de doublon
          setOpenLibraryResults(prev => 
            prev.map(book => 
              book.ol_key === openLibraryBook.ol_key 
                ? { ...book, isOwned: true }
                : book
            )
          );
        } else {
          toast.error(error.detail || 'Erreur lors de l\'ajout du livre');
        }
      }
    } catch (error) {
      console.error('Erreur ajout livre:', error);
      toast.error('Erreur lors de l\'ajout du livre');
    } finally {
      // Retirer le livre de la liste des livres en cours d'ajout
      setAddingBooks(prev => {
        const newSet = new Set(prev);
        newSet.delete(openLibraryBook.ol_key);
        return newSet;
      });
    }
  };

  // Gestionnaire de clic sur série pour afficher la fiche dédiée
  const handleSeriesClick = (series) => {
    if (series.isLibrarySeries) {
      // Série de bibliothèque : créer une fiche dédiée locale
      // Pour l'instant, on peut montrer une modal avec les livres de la série
      setSelectedSeries(series);
      setShowSeriesModal(true);
    } else {
      // Série Open Library : naviguer vers la page dédiée
      const navigate = window.location.pathname !== '/' ? 
        (path) => window.location.href = path : 
        (path) => window.history.pushState({}, '', path);
      navigate(`/series/${encodeURIComponent(series.name)}`);
    }
  };

  // Gestionnaire de clic sur livre
  const handleBookClick = (book) => {
    setSelectedBook(book);
    setShowBookModal(true);
  };

  // Gestionnaire de clic conditionnel (livre ou série)
  const handleItemClick = (item) => {
    if (item.isSeriesCard) {
      handleSeriesClick(item);
    } else {
      handleBookClick(item);
    }
  };

  const handleUpdateBook = async (bookId, bookData) => {
    try {
      const updatedBook = await bookService.updateBook(bookId, bookData);
      await loadBooks();
      await loadStats();
      
      // Mettre à jour le livre sélectionné avec les nouvelles données
      setSelectedBook(updatedBook);
      
      toast.success('Livre mis à jour !');
    } catch (error) {
      console.error('Erreur lors de la mise à jour du livre:', error);
      toast.error('Erreur lors de la mise à jour du statut');
    }
  };

  const handleDeleteBook = async (bookId) => {
    try {
      await bookService.deleteBook(bookId);
      await loadBooks();
      await loadStats();
      setSelectedBook(null);
      setShowBookModal(false);
      toast.success('Livre supprimé !');
    } catch (error) {
      console.error('Erreur lors de la suppression du livre:', error);
      toast.error('Erreur lors de la suppression du livre');
    }
  };

  // ============================================================================
  // GESTION DES SÉRIES EN BIBLIOTHÈQUE
  // ============================================================================

  // Charger les séries de la bibliothèque utilisateur
  const loadUserSeriesLibrary = async () => {
    try {
      setSeriesLibraryLoading(true);
      const token = localStorage.getItem('token');
      const result = await seriesLibraryService.getUserSeriesLibrary(token);
      setUserSeriesLibrary(result.series || []);
    } catch (error) {
      console.error('Erreur chargement séries bibliothèque:', error);
      toast.error('Erreur lors du chargement des séries');
    } finally {
      setSeriesLibraryLoading(false);
    }
  };

  // Ajouter une série complète à la bibliothèque avec enrichissement automatique
  const handleAddSeriesToLibrary = async (seriesData) => {
    try {
      setSeriesLibraryLoading(true);
      const token = localStorage.getItem('token');
      
      console.log('🚀 Ajout série à la bibliothèque:', seriesData);
      
      // Importer le référentiel étendu
      const { EXTENDED_SERIES_DATABASE } = await import('./utils/seriesDatabaseExtended.js');
      
      // Générer les volumes avec titres depuis le référentiel
      const volumes = seriesLibraryService.generateVolumesList(seriesData, EXTENDED_SERIES_DATABASE);
      
      console.log('📚 Volumes générés:', volumes);
      
      // Enrichissement automatique des métadonnées
      const enrichedMetadata = await enrichSeriesMetadata(seriesData);
      
      console.log('✨ Métadonnées enrichies:', enrichedMetadata);
      
      // Préparer les données de la série avec toutes les métadonnées
      const seriesPayload = {
        series_name: seriesData.name,
        authors: seriesData.authors || [seriesData.author || 'Auteur inconnu'],
        category: seriesData.category || 'roman',
        total_volumes: volumes.length,
        volumes: volumes,
        description_fr: enrichedMetadata.description_fr,
        cover_image_url: enrichedMetadata.cover_image_url,
        first_published: enrichedMetadata.first_published || seriesData.first_published || '',
        last_published: enrichedMetadata.last_published || '',
        publisher: enrichedMetadata.publisher || '',
        series_status: 'to_read'
      };
      
      console.log('📋 Payload final:', seriesPayload);
      
      // Appel API pour ajouter la série
      const result = await seriesLibraryService.addSeriesToLibrary(seriesPayload, token);
      
      if (result.success) {
        // Recharger la bibliothèque des séries
        await loadUserSeriesLibrary();
        
        // Message de succès détaillé
        toast.success(
          `✅ Série "${seriesData.name}" ajoutée avec ${volumes.length} tome${volumes.length > 1 ? 's' : ''} !`,
          { duration: 4000 }
        );
        
        console.log('✅ Série ajoutée avec succès:', result);
      }
    } catch (error) {
      console.error('❌ Erreur ajout série:', error);
      
      // Gestion des erreurs spécifiques
      if (error.message.includes('409')) {
        toast.error('Cette série est déjà dans votre bibliothèque');
      } else if (error.message.includes('400')) {
        toast.error('Données de série invalides');
      } else {
        toast.error('❌ Erreur lors de l\'ajout de la série');
      }
    } finally {
      setSeriesLibraryLoading(false);
    }
  };

  // Fonction d'enrichissement automatique des métadonnées
  const enrichSeriesMetadata = async (seriesData) => {
    try {
      console.log('🔍 Enrichissement métadonnées pour:', seriesData.name);
      
      // 1. Récupérer une image représentative avec vision_expert_agent
      let cover_image_url = '';
      try {
        const imageTask = `
PROBLEM_STATEMENT: Image de couverture pour fiche série "${seriesData.name}" dans bibliothèque de tracking de livres
SEARCH_KEYWORDS: ${seriesData.name}, book series, cover art
COUNT: 1
`;
        
        // Utiliser vision_expert_agent pour récupérer une image de qualité
        try {
          // Pour le moment, utiliser l'image par défaut
          // TODO: Intégrer vision_expert_agent quand disponible
          cover_image_url = '/default-series-cover.jpg';
          
          console.log('🖼️ Image par défaut utilisée (vision_expert_agent non disponible)');
        } catch (error) {
          console.warn('⚠️ Erreur vision_expert_agent:', error);
          cover_image_url = '/default-series-cover.jpg';
        }
        
        console.log('🖼️ Image récupérée:', cover_image_url);
      } catch (error) {
        console.warn('⚠️ Erreur récupération image:', error);
        cover_image_url = '/default-series-cover.jpg';
      }
      
      // 2. Générer une description française enrichie
      let description_fr = '';
      try {
        if (seriesData.description) {
          description_fr = seriesData.description;
        } else {
          // Générer une description basique
          const categoryText = {
            'roman': 'roman',
            'bd': 'bande dessinée', 
            'manga': 'manga'
          };
          
          const authorText = seriesData.authors?.length 
            ? ` par ${seriesData.authors.join(', ')}`
            : seriesData.author ? ` par ${seriesData.author}` : '';
          
          const volumeText = seriesData.volumes 
            ? ` Comprend ${seriesData.volumes} tome${seriesData.volumes > 1 ? 's' : ''}.`
            : '';
          
          description_fr = `Série de ${categoryText[seriesData.category] || 'livres'} populaire${authorText}.${volumeText}`;
        }
        
        console.log('📝 Description générée:', description_fr);
      } catch (error) {
        console.warn('⚠️ Erreur génération description:', error);
        description_fr = `Série ${seriesData.category || 'populaire'}.`;
      }
      
      return {
        cover_image_url,
        description_fr,
        first_published: seriesData.first_published || '',
        last_published: '',
        publisher: ''
      };
      
    } catch (error) {
      console.error('❌ Erreur enrichissement métadonnées:', error);
      
      // Fallback sûr
      return {
        cover_image_url: '/default-series-cover.jpg',
        description_fr: `Série ${seriesData.category || 'populaire'}.`,
        first_published: '',
        last_published: '',
        publisher: ''
      };
    }
  };

  // Mettre à jour le statut d'un tome
  const handleUpdateVolumeStatus = async (seriesId, volumeNumber, isRead) => {
    try {
      const token = localStorage.getItem('token');
      const result = await seriesLibraryService.toggleVolumeStatus(seriesId, volumeNumber, isRead, token);
      
      if (result.success) {
        // Mettre à jour l'état local
        setUserSeriesLibrary(prev => 
          prev.map(series => 
            series.id === seriesId 
              ? {
                  ...series,
                  volumes: series.volumes.map(vol => 
                    vol.volume_number === volumeNumber 
                      ? { ...vol, is_read: isRead, date_read: isRead ? new Date().toISOString() : null }
                      : vol
                  ),
                  completion_percentage: result.completion_percentage,
                  series_status: result.series_status
                }
              : series
          )
        );
        
        toast.success(`Tome ${volumeNumber} marqué comme ${isRead ? 'lu' : 'non lu'}`);
      }
    } catch (error) {
      console.error('Erreur mise à jour tome:', error);
      toast.error('Erreur lors de la mise à jour du tome');
    }
  };

  // Mettre à jour le statut global d'une série
  const handleUpdateSeriesStatus = async (seriesId, newStatus) => {
    try {
      const token = localStorage.getItem('token');
      const result = await seriesLibraryService.updateSeriesStatus(seriesId, newStatus, token);
      
      if (result.success) {
        // Mettre à jour l'état local
        setUserSeriesLibrary(prev => 
          prev.map(series => 
            series.id === seriesId 
              ? { ...series, series_status: newStatus }
              : series
          )
        );
        
        const statusLabels = {
          'to_read': 'À lire',
          'reading': 'En cours',
          'completed': 'Terminé'
        };
        toast.success(`Statut mis à jour : ${statusLabels[newStatus]}`);
      }
    } catch (error) {
      console.error('Erreur mise à jour statut série:', error);
      toast.error('Erreur lors de la mise à jour du statut');
    }
  };

  // Supprimer une série de la bibliothèque
  const handleDeleteSeriesFromLibrary = async (seriesId) => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer cette série de votre bibliothèque ?')) {
      return;
    }
    
    try {
      const token = localStorage.getItem('token');
      const result = await seriesLibraryService.deleteSeriesFromLibrary(seriesId, token);
      
      if (result.success) {
        setUserSeriesLibrary(prev => prev.filter(series => series.id !== seriesId));
        toast.success('Série supprimée de votre bibliothèque');
      }
    } catch (error) {
      console.error('Erreur suppression série:', error);
      toast.error('Erreur lors de la suppression de la série');
    }
  };

  // Charger les séries au montage du composant
  useEffect(() => {
    if (user) {
      loadUserSeriesLibrary();
    }
  }, [user]);

  // ============================================================================
  // FIN GESTION DES SÉRIES EN BIBLIOTHÈQUE
  // ============================================================================

  // Fonction intelligente de calcul de la pertinence basée sur la popularité et la détection de séries
  const calculateRelevanceScore = (book, searchTerm) => {
    if (!searchTerm || !searchTerm.trim()) return 0;
    
    const term = searchTerm.toLowerCase().trim();
    const termWords = term.split(/\s+/).filter(word => word.length > 1);
    
    // Normalisation des champs de recherche
    const title = (book.title || '').toLowerCase();
    const author = (book.author || '').toLowerCase();
    const saga = (book.saga || '').toLowerCase();
    
    let score = 0;
    
    // === DÉTECTION INTELLIGENTE DES SÉRIES POPULAIRES ===
    
    // Mapping complet des séries populaires avec leurs variations et auteurs
    const seriesMapping = {
      // === ROMANS FANTASY/SF ===
      'harry potter': {
        score: 18000,
        category: 'roman',
        keywords: ['harry', 'potter', 'hogwarts', 'sorcier', 'wizard', 'poudlard', 'voldemort', 'hermione', 'ron', 'dumbledore'],
        authors: ['j.k. rowling', 'jk rowling', 'rowling'],
        variations: ['harry potter', 'école des sorciers', 'chambre des secrets', 'prisonnier d\'azkaban', 'coupe de feu', 'ordre du phénix', 'prince de sang-mêlé', 'reliques de la mort'],
        volumes: 7,
        language: ['fr', 'en']
      },
      'seigneur des anneaux': {
        score: 18000,
        category: 'roman',
        keywords: ['anneau', 'communauté', 'deux tours', 'retour du roi', 'terre du milieu', 'middle earth', 'hobbit', 'frodo', 'gandalf', 'aragorn', 'legolas', 'gimli'],
        authors: ['j.r.r. tolkien', 'jrr tolkien', 'tolkien'],
        variations: ['seigneur des anneaux', 'lord of the rings', 'communauté de l\'anneau', 'fellowship', 'deux tours', 'two towers', 'retour du roi', 'return of the king', 'hobbit'],
        volumes: 3,
        language: ['fr', 'en']
      },
      'game of thrones': {
        score: 16000,
        category: 'roman',
        keywords: ['game of thrones', 'trône de fer', 'westeros', 'jon snow', 'daenerys', 'tyrion', 'stark', 'lannister', 'targaryen'],
        authors: ['george r.r. martin', 'george martin', 'martin'],
        variations: ['game of thrones', 'trône de fer', 'song of ice and fire', 'chanson de glace et de feu'],
        volumes: 5,
        language: ['fr', 'en']
      },
      'witcher': {
        score: 15000,
        category: 'roman',
        keywords: ['witcher', 'sorceleur', 'geralt', 'rivia', 'ciri', 'yennefer', 'triss'],
        authors: ['andrzej sapkowski', 'sapkowski'],
        variations: ['witcher', 'sorceleur', 'geralt de rivia'],
        volumes: 8,
        language: ['fr', 'en', 'pl']
      },
      'dune': {
        score: 16000,
        category: 'roman',
        keywords: ['dune', 'arrakis', 'paul atreides', 'fremen', 'spice', 'épice', 'muad\'dib'],
        authors: ['frank herbert', 'herbert'],
        variations: ['dune', 'cycle de dune'],
        volumes: 6,
        language: ['fr', 'en']
      },

      // === MANGAS ===
      'one piece': {
        score: 18000,
        category: 'manga',
        keywords: ['one piece', 'luffy', 'zoro', 'sanji', 'pirates', 'chapeau de paille', 'grand line', 'nami', 'usopp', 'chopper'],
        authors: ['eiichiro oda', 'oda'],
        variations: ['one piece'],
        volumes: 100,
        language: ['fr', 'en', 'jp']
      },
      'naruto': {
        score: 17000,
        category: 'manga',
        keywords: ['naruto', 'sasuke', 'sakura', 'kakashi', 'ninja', 'konoha', 'sharingan', 'hokage', 'boruto'],
        authors: ['masashi kishimoto', 'kishimoto'],
        variations: ['naruto', 'boruto'],
        volumes: 72,
        language: ['fr', 'en', 'jp']
      },
      'dragon ball': {
        score: 17000,
        category: 'manga',
        keywords: ['dragon ball', 'goku', 'vegeta', 'kamehameha', 'saiyan', 'piccolo', 'gohan', 'frieza', 'cell'],
        authors: ['akira toriyama', 'toriyama'],
        variations: ['dragon ball', 'dragonball', 'dragon ball z', 'dragon ball super'],
        volumes: 42,
        language: ['fr', 'en', 'jp']
      },
      'attack on titan': {
        score: 16000,
        category: 'manga',
        keywords: ['attack on titan', 'attaque des titans', 'eren', 'mikasa', 'armin', 'titans', 'murs', 'shingeki no kyojin'],
        authors: ['hajime isayama', 'isayama'],
        variations: ['attack on titan', 'attaque des titans', 'shingeki no kyojin'],
        volumes: 34,
        language: ['fr', 'en', 'jp']
      },
      'death note': {
        score: 15000,
        category: 'manga',
        keywords: ['death note', 'light', 'l', 'kira', 'ryuk', 'shinigami', 'yagami'],
        authors: ['tsugumi ohba', 'takeshi obata', 'ohba', 'obata'],
        variations: ['death note'],
        volumes: 12,
        language: ['fr', 'en', 'jp']
      },
      'bleach': {
        score: 15000,
        category: 'manga',
        keywords: ['bleach', 'ichigo', 'rukia', 'shinigami', 'hollow', 'soul society', 'zanpakuto'],
        authors: ['tite kubo', 'kubo'],
        variations: ['bleach'],
        volumes: 74,
        language: ['fr', 'en', 'jp']
      },
      'fullmetal alchemist': {
        score: 15000,
        category: 'manga',
        keywords: ['fullmetal alchemist', 'edward elric', 'alphonse', 'alchemy', 'alchimie', 'philosopher stone'],
        authors: ['hiromu arakawa', 'arakawa'],
        variations: ['fullmetal alchemist', 'full metal alchemist'],
        volumes: 27,
        language: ['fr', 'en', 'jp']
      },
      'demon slayer': {
        score: 16000,
        category: 'manga',
        keywords: ['demon slayer', 'kimetsu no yaiba', 'tanjiro', 'nezuko', 'demons', 'hashira'],
        authors: ['koyoharu gotouge', 'gotouge'],
        variations: ['demon slayer', 'kimetsu no yaiba'],
        volumes: 23,
        language: ['fr', 'en', 'jp']
      },
      'my hero academia': {
        score: 15000,
        category: 'manga',
        keywords: ['my hero academia', 'boku no hero', 'midoriya', 'deku', 'quirk', 'all might', 'bakugo'],
        authors: ['kohei horikoshi', 'horikoshi'],
        variations: ['my hero academia', 'boku no hero academia'],
        volumes: 35,
        language: ['fr', 'en', 'jp']
      },

      // === BANDES DESSINÉES ===
      'astérix': {
        score: 18000,
        category: 'bd',
        keywords: ['astérix', 'asterix', 'obélix', 'obelix', 'gaulois', 'potion magique', 'panoramix', 'idéfix'],
        authors: ['rené goscinny', 'albert uderzo', 'goscinny', 'uderzo'],
        variations: ['astérix', 'asterix'],
        volumes: 39,
        language: ['fr', 'en']
      },
      'tintin': {
        score: 18000,
        category: 'bd',
        keywords: ['tintin', 'milou', 'capitaine haddock', 'tournesol', 'dupont', 'dupond', 'mille sabords'],
        authors: ['hergé', 'herge'],
        variations: ['tintin', 'aventures de tintin'],
        volumes: 24,
        language: ['fr', 'en']
      },
      'gaston lagaffe': {
        score: 15000,
        category: 'bd',
        keywords: ['gaston', 'lagaffe', 'spirou', 'fantasio', 'prunelle', 'longtarin'],
        authors: ['andré franquin', 'franquin'],
        variations: ['gaston lagaffe', 'gaston'],
        volumes: 19,
        language: ['fr']
      },
      'lucky luke': {
        score: 15000,
        category: 'bd',
        keywords: ['lucky luke', 'dalton', 'jolly jumper', 'rantanplan', 'cowboy', 'western'],
        authors: ['morris', 'rené goscinny', 'goscinny'],
        variations: ['lucky luke'],
        volumes: 70,
        language: ['fr', 'en']
      },
      'spirou': {
        score: 15000,
        category: 'bd',
        keywords: ['spirou', 'fantasio', 'marsupilami', 'spip', 'zorglub', 'champignac'],
        authors: ['andré franquin', 'franquin', 'rob-vel'],
        variations: ['spirou et fantasio', 'spirou'],
        volumes: 55,
        language: ['fr']
      },
      'thorgal': {
        score: 14000,
        category: 'bd',
        keywords: ['thorgal', 'aaricia', 'jolan', 'louve', 'viking', 'nordique'],
        authors: ['jean van hamme', 'grzegorz rosinski', 'van hamme', 'rosinski'],
        variations: ['thorgal'],
        volumes: 38,
        language: ['fr']
      },
      'xiii': {
        score: 14000,
        category: 'bd',
        keywords: ['xiii', 'treize', 'jason fly', 'conspiracy', 'conspiration'],
        authors: ['jean van hamme', 'william vance', 'van hamme', 'vance'],
        variations: ['xiii', 'treize'],
        volumes: 27,
        language: ['fr', 'en']
      },
      'blake et mortimer': {
        score: 14000,
        category: 'bd',
        keywords: ['blake', 'mortimer', 'francis blake', 'philip mortimer', 'jacobs'],
        authors: ['edgar p. jacobs', 'jacobs'],
        variations: ['blake et mortimer', 'blake mortimer'],
        volumes: 27,
        language: ['fr', 'en']
      },

      // === COMICS AMÉRICAINS ===
      'batman': {
        score: 16000,
        category: 'bd',
        keywords: ['batman', 'bruce wayne', 'gotham', 'joker', 'robin', 'alfred', 'dark knight'],
        authors: ['dc comics', 'bob kane', 'bill finger'],
        variations: ['batman', 'dark knight', 'chevalier noir'],
        volumes: 1000,
        language: ['fr', 'en']
      },
      'superman': {
        score: 16000,
        category: 'bd',
        keywords: ['superman', 'clark kent', 'metropolis', 'lois lane', 'lex luthor', 'kryptonite'],
        authors: ['dc comics', 'jerry siegel', 'joe shuster'],
        variations: ['superman', 'man of steel'],
        volumes: 1000,
        language: ['fr', 'en']
      },
      'spider-man': {
        score: 16000,
        category: 'bd',
        keywords: ['spider-man', 'spiderman', 'peter parker', 'new york', 'web', 'toile'],
        authors: ['marvel comics', 'stan lee', 'steve ditko'],
        variations: ['spider-man', 'spiderman', 'amazing spider-man'],
        volumes: 1000,
        language: ['fr', 'en']
      },
      'x-men': {
        score: 15000,
        category: 'bd',
        keywords: ['x-men', 'wolverine', 'cyclops', 'storm', 'xavier', 'magneto', 'mutants'],
        authors: ['marvel comics', 'stan lee', 'jack kirby'],
        variations: ['x-men', 'uncanny x-men'],
        volumes: 1000,
        language: ['fr', 'en']
      },
      'walking dead': {
        score: 15000,
        category: 'bd',
        keywords: ['walking dead', 'rick grimes', 'zombies', 'walkers', 'apocalypse'],
        authors: ['robert kirkman', 'kirkman'],
        variations: ['walking dead'],
        volumes: 193,
        language: ['fr', 'en']
      },

      // === ROMANS POLICIERS ===
      'sherlock holmes': {
        score: 16000,
        category: 'roman',
        keywords: ['sherlock holmes', 'watson', 'baker street', 'moriarty', 'london', 'detective'],
        authors: ['arthur conan doyle', 'conan doyle', 'doyle'],
        variations: ['sherlock holmes', 'adventures of sherlock holmes'],
        volumes: 60,
        language: ['fr', 'en']
      },
      'hercule poirot': {
        score: 15000,
        category: 'roman',
        keywords: ['hercule poirot', 'agatha christie', 'orient express', 'nil', 'belgian', 'detective'],
        authors: ['agatha christie', 'christie'],
        variations: ['hercule poirot', 'poirot'],
        volumes: 39,
        language: ['fr', 'en']
      },
      'san antonio': {
        score: 14000,
        category: 'roman',
        keywords: ['san antonio', 'bérurier', 'pinaud', 'police', 'commissaire'],
        authors: ['frédéric dard', 'dard'],
        variations: ['san antonio', 'san-antonio'],
        volumes: 175,
        language: ['fr']
      }
    };
    
    // Fonction pour détecter si un livre appartient à une série populaire
    function detectSeries(searchQuery) {
      const query = searchQuery.toLowerCase();
      
      for (const [seriesName, seriesData] of Object.entries(seriesMapping)) {
        // Vérification directe du nom de série dans la requête
        if (query.includes(seriesName)) {
          return { series: seriesName, data: seriesData, confidence: 'high' };
        }
        
        // Vérification des variations
        for (const variation of seriesData.variations) {
          if (query.includes(variation)) {
            return { series: seriesName, data: seriesData, confidence: 'high' };
          }
        }
      }
      
      return null;
    }
    
    // Fonction pour vérifier si un livre correspond à une série
    function isBookInSeries(book, seriesName, seriesData) {
      const bookTitle = (book.title || '').toLowerCase();
      const bookAuthor = (book.author || '').toLowerCase();
      const bookSaga = (book.saga || '').toLowerCase();
      const bookCategory = (book.category || '').toLowerCase();
      
      let confidence = 0;
      
      // Vérification par saga (le plus fiable)
      if (bookSaga.includes(seriesName) || seriesData.variations.some(v => bookSaga.includes(v))) {
        confidence += 100;
      }
      
      // Vérification par auteur (très fiable pour les séries uniques)
      if (seriesData.authors.some(author => bookAuthor.includes(author))) {
        confidence += 90;
      }
      
      // Bonus pour correspondance de catégorie
      if (seriesData.category && bookCategory === seriesData.category) {
        confidence += 20;
      }
      
      // Vérification par mots-clés dans le titre
      let keywordMatches = 0;
      seriesData.keywords.forEach(keyword => {
        if (bookTitle.includes(keyword)) {
          keywordMatches++;
        }
      });
      
      if (keywordMatches > 0) {
        confidence += keywordMatches * 25; // Réduction du score pour éviter les faux positifs
      }
      
      // Vérification par variations dans le titre (très importante)
      seriesData.variations.forEach(variation => {
        if (bookTitle.includes(variation)) {
          confidence += 70;
        }
      });
      
      // Bonus pour titre exact ou quasi-exact
      if (seriesData.variations.some(variation => bookTitle === variation || bookTitle.startsWith(variation))) {
        confidence += 50;
      }
      
      // Vérification des langues supportées
      if (seriesData.language && book.language) {
        if (seriesData.language.includes(book.language)) {
          confidence += 10;
        }
      }
      
      return confidence;
    }
    
    // === CALCUL DE SCORE PRINCIPAL ===
    
    // Détecter si la recherche concerne une série populaire
    const detectedSeries = detectSeries(term);
    
    let matchScore = 0;
    let popularityBonus = 0;
    
    if (detectedSeries) {
      const { series, data } = detectedSeries;
      
      // Vérifier si ce livre appartient à la série recherchée
      const seriesConfidence = isBookInSeries(book, series, data);
      
      if (seriesConfidence >= 100) {
        // Livre confirmé de la série (par saga ou auteur + mots-clés)
        popularityBonus = data.score;
        matchScore = 40000; // Score très élevé pour les vrais livres de la série
      } else if (seriesConfidence >= 80) {
        // Livre probable de la série
        popularityBonus = data.score * 0.8;
        matchScore = 30000;
      } else if (seriesConfidence >= 50) {
        // Livre possible de la série
        popularityBonus = data.score * 0.5;
        matchScore = 20000;
      }
    }
    
    // === CORRESPONDANCES EXACTES CLASSIQUES ===
    
    // Si pas de série détectée ou score faible, utiliser la correspondance classique
    if (matchScore < 20000) {
      // Correspondance exacte complète
      if (title === term) {
        matchScore = Math.max(matchScore, 35000);
      }
      // Correspondance de séquence complète
      else if (title.includes(term)) {
        if (title.startsWith(term)) {
          matchScore = Math.max(matchScore, 25000);
        } else {
          matchScore = Math.max(matchScore, 18000);
        }
      }
      // Multi-mots : tous les mots présents
      else if (termWords.length > 1) {
        let wordsFound = 0;
        termWords.forEach(word => {
          if (title.includes(word)) wordsFound++;
        });
        
        const completeness = wordsFound / termWords.length;
        if (completeness === 1) {
          matchScore = Math.max(matchScore, 15000); // Tous les mots trouvés
        } else if (completeness >= 0.8) {
          matchScore = Math.max(matchScore, 12000); // 80%+ des mots
        } else if (completeness >= 0.6) {
          matchScore = Math.max(matchScore, 8000);  // 60%+ des mots
        } else if (completeness >= 0.4) {
          matchScore = Math.max(matchScore, 5000);  // 40%+ des mots
        }
      }
      // Mot simple
      else {
        if (title.startsWith(term)) {
          matchScore = Math.max(matchScore, 8000);
        } else if (title.includes(` ${term} `) || title.includes(`${term} `) || title.includes(` ${term}`)) {
          matchScore = Math.max(matchScore, 6000); // Mot entier
        } else if (title.includes(term)) {
          matchScore = Math.max(matchScore, 4000); // Contient le mot
        }
      }
    }
    
    // Correspondances dans l'auteur
    if (author.includes(term)) {
      if (author === term) {
        matchScore += 10000;
      } else if (author.startsWith(term)) {
        matchScore += 6000;
      } else {
        matchScore += 3000;
      }
    }
    
    // Correspondances dans la saga
    if (saga && saga.includes(term)) {
      if (saga === term) {
        matchScore += 8000;
      } else if (saga.startsWith(term)) {
        matchScore += 5000;
      } else {
        matchScore += 2000;
      }
    }
    
    // === BONUS GÉNÉRAUX ===
    
    // Séries génériquement populaires (fallback) - Version étendue
    const generalPopularKeywords = [
      // Comics/BD supplémentaires
      'wolverine', 'deadpool', 'iron man', 'captain america', 'hulk', 'thor', 'avengers',
      'wonder woman', 'flash', 'green lantern', 'aquaman', 'justice league',
      'sandman', 'watchmen', 'v for vendetta', 'hellboy', 'spawn',
      
      // Mangas supplémentaires
      'one punch man', 'tokyo ghoul', 'fairy tail', 'black clover', 'jujutsu kaisen',
      'chainsaw man', 'mob psycho', 'hunter x hunter', 'yu yu hakusho',
      'cowboy bebop', 'akira', 'ghost in the shell', 'evangelion',
      
      // Romans supplémentaires
      'percy jackson', 'twilight', 'hunger games', 'divergent', 'maze runner',
      'outlander', 'fifty shades', 'dark tower', 'foundation', 'hyperion',
      'mistborn', 'wheel of time', 'chronicles of narnia', 'his dark materials',
      
      // BD franco-belges supplémentaires
      'largo winch', 'blacksad', 'corto maltese', 'lanfeust', 'trolls de troy',
      'donjon', 'dungeon', 'bone', 'fables', 'saga', 'invincible',
      
      // Classiques
      'james bond', 'indiana jones', 'conan', 'tarzan', 'flash gordon',
      'buck rogers', 'phantom', 'prince valiant', 'dick tracy'
    ];
    
    if (!detectedSeries) {
      const titleAndSaga = `${title} ${saga} ${author}`.toLowerCase();
      for (const keyword of generalPopularKeywords) {
        if (titleAndSaga.includes(keyword) || term.includes(keyword)) {
          popularityBonus += 8000;
          break;
        }
      }
    }
    
    // Bonus pour livres récents
    if (book.first_publish_year) {
      const year = book.first_publish_year;
      if (year >= 2020) popularityBonus += 1000;
      else if (year >= 2015) popularityBonus += 800;
      else if (year >= 2010) popularityBonus += 600;
      else if (year >= 2000) popularityBonus += 400;
      else if (year >= 1990) popularityBonus += 200;
    }
    
    // Bonus pour métadonnées de qualité
    if (book.cover_url) popularityBonus += 500;
    if (book.number_of_pages && book.number_of_pages >= 100 && book.number_of_pages <= 800) {
      popularityBonus += 300;
    }
    
    // === BONUS POUR LIVRES LOCAUX ===
    
    let localBonus = 0;
    if (!book.isFromOpenLibrary) {
      localBonus = 3000; // Bonus pour livres possédés
    } else if (book.isFromOpenLibrary && book.isOwned) {
      localBonus = 1500;
    }
    
    // === CALCUL FINAL ===
    
    score = matchScore + popularityBonus + localBonus;
    
    // Malus pour livres sans métadonnées importantes
    if (!book.author || book.author.trim() === '') score -= 2000;
    if (!book.title || book.title.trim() === '') score -= 3000;
    
    return Math.max(0, Math.round(score));
  };

  // Fonction pour obtenir le niveau de pertinence d'un livre
  const getRelevanceLevel = (score) => {
    if (score >= 800) return { level: 'excellent', label: 'Très pertinent', color: 'bg-green-500', icon: '🎯' };
    if (score >= 400) return { level: 'good', label: 'Pertinent', color: 'bg-blue-500', icon: '✨' };
    if (score >= 100) return { level: 'moderate', label: 'Moyennement pertinent', color: 'bg-yellow-500', icon: '👁️' };
    if (score >= 50) return { level: 'low', label: 'Peu pertinent', color: 'bg-orange-500', icon: '🔍' };
    return { level: 'minimal', label: 'Faiblement pertinent', color: 'bg-gray-500', icon: '📄' };
  };

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
        [
          // Ajouter les séries de la bibliothèque utilisateur
          ...userSeriesLibrary
            .filter(series => series.category === activeTab)
            .map(series => ({
              ...series,
              isSeriesCard: true,
              isLibrarySeries: true,
              id: `library-series-${series.id}`,
              name: series.series_name,
              title: series.series_name,
              author: series.authors.join(', '),
              totalBooks: series.total_volumes,
              completedBooks: series.volumes.filter(v => v.is_read).length,
              progressPercent: series.completion_percentage,
              sortDate: series.date_added
            })),
          // Ajouter les livres individuels (sans série) après filtrage
          ...createUnifiedDisplay(filteredBooks.filter(book => book.category === activeTab && !book.isSeriesCard))
        ]
        .sort((a, b) => {
          // Trier par date d'ajout (plus récent en premier)
          const dateA = new Date(a.sortDate || a.date_added || a.updated_at || new Date().toISOString());
          const dateB = new Date(b.sortDate || b.date_added || b.updated_at || new Date().toISOString());
          return dateB - dateA;
        });

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
          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 h-64 animate-pulse">
                  <div className="flex space-x-4">
                    <div className="w-16 h-24 bg-gray-200 dark:bg-gray-700 rounded"></div>
                    <div className="flex-1 space-y-3">
                      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                      <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                      <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-5/6"></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {displayedBooks.length > 0 ? (
                displayedBooks.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => handleItemClick(item)}
                    className="cursor-pointer bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow"
                  >
                    {item.isSeriesCard ? (
                      <SeriesCard
                        series={item}
                        onClick={() => handleItemClick(item)}
                        isOwned={item.isLibrarySeries || item.isOwned}
                        showProgress={item.isLibrarySeries}
                        progressInfo={item.isLibrarySeries ? {
                          completed: item.completedBooks,
                          total: item.totalBooks
                        } : null}
                        showAddButton={!item.isLibrarySeries && !item.isOwned}
                        onAddToLibrary={item.isLibrarySeries ? null : handleAddSeriesToLibrary}
                        onUpdateVolume={item.isLibrarySeries ? handleUpdateVolumeStatus : null}
                        onUpdateStatus={item.isLibrarySeries ? handleUpdateSeriesStatus : null}
                        onDelete={item.isLibrarySeries ? handleDeleteSeriesFromLibrary : null}
                        context={item.isLibrarySeries ? "library" : "search"}
                      />
                    ) : (
                      <div className="p-4">
                        {/* Badges toujours visibles pour cohérence */}
                        <div className="flex justify-between mb-2">
                          {item.relevanceInfo && (
                            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium text-white ${item.relevanceInfo.color}`}>
                              {item.relevanceInfo.icon} {item.relevanceInfo.label}
                            </span>
                          )}
                          {item.categoryBadge && (
                            <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${item.categoryBadge.class}`}>
                              {item.categoryBadge.emoji} {item.categoryBadge.text}
                            </span>
                          )}
                        </div>
                        
                        <div className="flex items-start space-x-4">
                          <div className="w-16 h-24 bg-gray-100 dark:bg-gray-700 rounded flex-shrink-0 overflow-hidden">
                            {item.cover_url ? (
                              <img 
                                src={item.cover_url} 
                                alt={item.title}
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center">
                                <span className="text-gray-400 text-2xl">📖</span>
                              </div>
                            )}
                          </div>
                          
                          <div className="flex-1 min-w-0">
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1 line-clamp-2">
                              {item.title}
                            </h3>
                            
                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                              {item.author}
                            </p>
                            
                            <div className="flex flex-wrap gap-2">
                              {item.saga && (
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-300">
                                  📖 {item.saga}
                                  {item.volume_number && ` - T.${item.volume_number}`}
                                </span>
                              )}
                              
                              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                item.status === 'completed' 
                                  ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300' 
                                  : item.status === 'reading'
                                    ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300'
                                    : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                              }`}>
                                {item.status === 'completed' ? 'Terminé' : 
                                 item.status === 'reading' ? 'En cours' : 'À lire'}
                              </span>
                              
                              {/* Badge Open Library */}
                              {item.isFromOpenLibrary && (
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300">
                                  {item.isOwned ? '✓ Possédé' : '+ Ajouter'}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="col-span-full text-center py-12">
                  <div className="mx-auto w-24 h-24 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
                    <span className="text-4xl">📚</span>
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    {isSearchMode 
                      ? `Aucun résultat pour "${lastSearchTerm}"` 
                      : 'Aucun livre dans cette catégorie'}
                  </h3>
                  <p className="text-gray-500 dark:text-gray-400">
                    {isSearchMode 
                      ? 'Essayez avec un autre terme de recherche' 
                      : 'Ajoutez des livres pour commencer votre collection'}
                  </p>
                </div>
              )}
            </div>
          )}
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