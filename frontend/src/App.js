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