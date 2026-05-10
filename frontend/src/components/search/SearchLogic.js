/**
 * SEARCH LOGIC - Module de logique de recherche pour BOOKTIME
 * 
 * Fonctionnalités :
 * - Recherche globale Open Library
 * - Détection automatique de propriété des livres
 * - Génération de badges catégorie automatiques
 * - Tri intelligent des résultats avec priorité séries
 * - Gestion ajout depuis Open Library avec placement intelligent
 * 
 * Extrait d'App.js dans le cadre de la Phase 1.1 - Frontend Modularisation
 */

import { toast } from 'react-hot-toast';
import SearchOptimizer from '../../utils/searchOptimizer';
import { calculateRelevanceScore, getRelevanceLevel } from './RelevanceEngine';
import { AutoSeriesDetector } from '../../hooks/useAutoSeriesDetection';
import SeriesDetector from '../../utils/seriesDetector';
import { API_BASE_URL } from '../../config/environment';
import { EXTENDED_SERIES_DATABASE } from '../../utils/seriesDatabaseExtended';

// Index plat : titre de tome (lowercase) → { seriesKey, seriesData, volumeNumber }
const buildVolumeTitleIndex = () => {
  const index = {};
  for (const category of Object.values(EXTENDED_SERIES_DATABASE)) {
    for (const [key, s] of Object.entries(category)) {
      if (!s.volume_titles) continue;
      for (const [num, title] of Object.entries(s.volume_titles)) {
        index[title.toLowerCase().trim()] = { seriesKey: key, seriesData: s, volumeNumber: Number(num) };
      }
    }
  }
  return index;
};
const VOLUME_TITLE_INDEX = buildVolumeTitleIndex();

// FONCTION PRINCIPALE DE RECHERCHE OPEN LIBRARY
export const searchOpenLibrary = async (query, {
  books, 
  setSearchLoading, 
  setIsSearchMode, 
  setLastSearchTerm, 
  setOpenLibraryResults,
  generateSeriesCardsForSearch,
  getCategoryBadgeFromBook
}) => {
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
    const backendUrl = API_BASE_URL;
    
    // RECHERCHE GLOBALE : pas de filtre par catégorie, 40 résultats (double-pass OL côté backend)
    const response = await fetch(`${backendUrl}/api/openlibrary/search?q=${encodeURIComponent(query)}&limit=40`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    if (response.ok) {
      const data = await response.json();

      // ── 1. Dédoublonnage par ol_key ──────────────────────────────────────
      const seen = new Set();
      const uniqueBooks = (data.books || []).filter(b => {
        if (!b.ol_key || seen.has(b.ol_key)) return false;
        seen.add(b.ol_key);
        return true;
      });

      // ── 2. Enrichir chaque livre (ownership + badge) ─────────────────────
      const enriched = uniqueBooks.map(book => {
        const categoryBadge = getCategoryBadgeFromBook(book);
        return {
          ...book,
          isFromOpenLibrary: true,
          isOwned: detectBookOwnership(book, books),
          id: `ol_${book.ol_key}`,
          categoryBadge,
          category: book.category || categoryBadge.key || 'roman',
        };
      });

      // ── 3. Détection de séries depuis les résultats OL ───────────────────
      // Stratégie 1 (priorité) : champ `saga` renvoyé par Open Library
      // Stratégie 2 (fallback) : plusieurs livres du même auteur avec mots du query

      const olSeriesCards = [];
      const olSeriesBookIds = new Set();

      // -- Stratégie 1 : grouper par champ saga (source OL fiable) --
      const sagaGroups = {};
      enriched.forEach(book => {
        if (!book.saga) return;
        // Normaliser le nom de saga pour regrouper "Red Rising #1" et "Red Rising #2"
        const key = book.saga.toLowerCase().trim();
        if (!sagaGroups[key]) sagaGroups[key] = { name: book.saga, author: book.author, books: [], category: book.category };
        sagaGroups[key].books.push(book);
      });

      Object.values(sagaGroups).forEach(group => {
        if (group.books.length < 1) return; // même 1 livre suffit si OL le dit dans une série
        group.books.forEach(b => olSeriesBookIds.add(b.ol_key));
        olSeriesCards.push({
          isSeriesCard: true,
          id: `series_ol_${group.name.toLowerCase().replace(/\s+/g, '_')}`,
          name: group.name,
          author: group.author,
          category: group.category,
          cover_url: group.books.find(b => b.cover_url)?.cover_url || null,
          totalBooks: group.books.length,
          books: group.books,
          description: `Série de ${group.books.length} livre(s) de ${group.author}`,
          relevanceScore: 100000,
          fromOpenLibrary: true,
        });
      });

      // -- Stratégie 2 (fallback) : auteur + mots du query pour les livres sans saga --
      const noSagaBooks = enriched.filter(b => !olSeriesBookIds.has(b.ol_key));
      const authorGroups = {};
      noSagaBooks.forEach(book => {
        if (!book.author) return;
        const key = book.author.toLowerCase().trim();
        if (!authorGroups[key]) authorGroups[key] = { author: book.author, books: [], category: book.category };
        authorGroups[key].books.push(book);
      });

      const queryWords = query.toLowerCase().split(/\s+/).filter(w => w.length >= 3);
      Object.values(authorGroups).forEach(group => {
        if (group.books.length < 2) return;
        const matchingBooks = queryWords.length > 0
          ? group.books.filter(b => queryWords.some(w => b.title.toLowerCase().includes(w)))
          : group.books;
        if (matchingBooks.length < 2) return;

        const seriesName = queryWords.length > 0 ? query.trim() : group.author;
        matchingBooks.forEach(b => olSeriesBookIds.add(b.ol_key));

        olSeriesCards.push({
          isSeriesCard: true,
          id: `series_author_${seriesName.toLowerCase().replace(/\s+/g, '_')}`,
          name: seriesName,
          author: group.author,
          category: group.category,
          cover_url: matchingBooks.find(b => b.cover_url)?.cover_url || null,
          totalBooks: matchingBooks.length,
          books: matchingBooks,
          description: `Série de ${matchingBooks.length} livres de ${group.author}`,
          relevanceScore: 90000,
          fromOpenLibrary: true,
        });
      });

      // ── 4. Regroupement des livres orphelins par la base statique ────────
      // Si un titre correspond exactement à un volume d'une série connue → carte série
      const staticFromOrphans = {};
      enriched.forEach(book => {
        if (olSeriesBookIds.has(book.ol_key)) return;
        const match = VOLUME_TITLE_INDEX[book.title?.toLowerCase().trim()];
        if (!match) return;
        const { seriesKey, seriesData } = match;
        if (!staticFromOrphans[seriesKey]) {
          staticFromOrphans[seriesKey] = {
            isSeriesCard: true,
            id: `series_static_${seriesKey}`,
            name: seriesData.name,
            author: book.author,
            category: seriesData.category || book.category,
            cover_url: book.cover_url || null,
            totalBooks: seriesData.volumes || 1,
            books: [],
            description: seriesData.description || '',
            relevanceScore: 95000,
            fromStaticDB: true,
          };
        }
        staticFromOrphans[seriesKey].books.push(book);
        olSeriesBookIds.add(book.ol_key);
      });

      // ── 5. Séries de la base statique (legacy query-based) ──────────────
      const staticSeriesCards = generateSeriesCardsForSearch(query, data.books);

      // ── 6. Livres individuels (hors séries détectées) ────────────────────
      const standaloneBooks = enriched.filter(b => !olSeriesBookIds.has(b.ol_key));

      // ── 7. Fusion + tri : séries d'abord, puis livres ───────────────────
      const allSeriesNames = new Set(olSeriesCards.map(c => c.name.toLowerCase()));

      // Cartes depuis la base statique (orphelins reconnus)
      const orphanSeriesCards = Object.values(staticFromOrphans).filter(
        c => !allSeriesNames.has(c.name.toLowerCase())
      );
      orphanSeriesCards.forEach(c => allSeriesNames.add(c.name.toLowerCase()));

      // Cartes legacy (query-based) — dédoublonner
      const dedupedStatic = staticSeriesCards.filter(
        c => !allSeriesNames.has((c.name || '').toLowerCase())
      );

      const finalResults = [
        ...olSeriesCards,
        ...orphanSeriesCards,
        ...dedupedStatic,
        ...standaloneBooks,
      ];

      setOpenLibraryResults(finalResults);
      toast.success(
        `${standaloneBooks.length} livre(s)` +
        (olSeriesCards.length > 0 ? ` + ${olSeriesCards.length} série(s) détectée(s)` : '') +
        ` trouvé(s)`
      );
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

// DÉTECTION DE PROPRIÉTÉ D'UN LIVRE
const detectBookOwnership = (book, books) => {
  return books.some(localBook => {
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
};

// Fonction verifyAndDisplayBook déplacée et consolidée dans l'export ci-dessous

// AJOUT INTELLIGENT : Placement automatique dans le bon onglet selon la catégorie
export const handleAddFromOpenLibrary = async (openLibraryBook, {
  books,
  addingBooks,
  setAddingBooks,
  activeTab,
  getCategoryBadgeFromBook,
  loadBooks,
  loadStats,
  setOpenLibraryResults
}) => {
  // Empêcher les clics multiples sur le même livre
  if (addingBooks.has(openLibraryBook.ol_key)) {
    return; // Si le livre est déjà en cours d'ajout, ne rien faire
  }

  try {
    // Marquer le livre comme en cours d'ajout
    setAddingBooks(prev => new Set([...prev, openLibraryBook.ol_key]));
    
    const token = localStorage.getItem('token');
    const backendUrl = API_BASE_URL;
    
    // PLACEMENT INTELLIGENT : Déterminer la catégorie automatiquement via le badge
    const categoryBadge = openLibraryBook.categoryBadge || getCategoryBadgeFromBook(openLibraryBook);
    let targetCategory = categoryBadge.key; // Utiliser la catégorie détectée par le badge
    
    // Validation : s'assurer que la catégorie est valide
    if (!targetCategory || !['roman', 'bd', 'manga'].includes(targetCategory)) {
      // Si pas de catégorie ou catégorie invalide, utiliser l'onglet actuel par défaut
      targetCategory = activeTab;
    }
    
    // 🔍 DÉTECTION AUTOMATIQUE DE SÉRIE
    console.log('🔍 DÉTECTION AUTOMATIQUE: Analyse du livre pour séries...');
    const autoDetector = new AutoSeriesDetector();
    
    // Préparer les données du livre pour la détection
    const bookData = {
      title: openLibraryBook.title,
      author: openLibraryBook.author,
      category: targetCategory,
      cover_url: openLibraryBook.cover_url || "",
      ol_key: openLibraryBook.ol_key
    };
    
    // Lancer la détection automatique
    const enhancedBookData = await autoDetector.detectAndEnhanceBook(bookData);
    
    // Utiliser les données enrichies pour l'import
    const response = await fetch(`${backendUrl}/api/openlibrary/import`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        ol_key: openLibraryBook.ol_key,
        category: targetCategory,
        cover_url: openLibraryBook.cover_url || "",
        original_title: openLibraryBook.original_title || openLibraryBook.title || null,
        saga: enhancedBookData.saga || null,
        volume_number: enhancedBookData.volume_number || null,
        auto_detected_series: enhancedBookData.auto_detected_series || false,
        detection_confidence: enhancedBookData.detection_confidence || null
      })
    });

    if (response.ok) {
      // Message de succès immédiat
      const categoryLabels = {
        'roman': 'Roman',
        'bd': 'BD',
        'manga': 'Manga'
      };
      toast.success(`"${openLibraryBook.title}" ajouté avec succès ! 📚`, {
        duration: 2000
      });
      
      // Rafraîchir la bibliothèque
      if (loadStats) {
        await Promise.all([loadBooks(), loadStats()]);
      } else {
        await loadBooks();
      }

      // Déclencher immédiatement le retour à la bibliothèque (import confirmé par response.ok)
      window.dispatchEvent(new CustomEvent('backToLibrary', {
        detail: {
          reason: 'book_added_success',
          bookTitle: openLibraryBook.title,
          targetCategory,
        }
      }));
      
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

// NAVIGATION ET UTILITAIRES DE RECHERCHE

// Fonction pour revenir à la bibliothèque locale
export const backToLibrary = (setIsSearchMode, setOpenLibraryResults, setLastSearchTerm, clearSearch) => {
  setIsSearchMode(false);
  setOpenLibraryResults([]);
  setLastSearchTerm('');
  clearSearch();
};

// Gestionnaires de clics sur éléments

// Gestionnaire de clic sur série pour afficher la fiche dédiée
export const handleSeriesClick = (series, setSelectedSeries, setShowSeriesModal) => {
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
export const handleBookClick = (book, setSelectedBook, setShowBookModal) => {
  setSelectedBook(book);
  setShowBookModal(true);
};

// Gestionnaire de clic conditionnel (livre ou série)
export const handleItemClick = (item, setSelectedSeries, setShowSeriesModal, setSelectedBook, setShowBookModal) => {
  if (item.isSeriesCard) {
    handleSeriesClick(item, setSelectedSeries, setShowSeriesModal);
  } else {
    handleBookClick(item, setSelectedBook, setShowBookModal);
  }
};



/**
 * PHASE C.1 - SYSTÈME VÉRIFICATION SÉRIE UNIFIÉ
 * Vérification intelligente avec retry progressif pour garantir l'affichage
 * des séries après ajout/complétion avec système de fallback
 */
export const verifyAndDisplaySeries = async (seriesName, targetCategory, userSeriesLibrary, loadUserSeriesLibrary) => {
  const maxAttempts = 3;
  const baseDelayMs = 500;
  
  console.log(`🔍 [PHASE C.1] Vérification série: "${seriesName}" en catégorie "${targetCategory}"`);
  
  const startTime = Date.now();
  
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      console.log(`📚 [PHASE C.1] Tentative ${attempt}/${maxAttempts} - Chargement séries...`);
      
      // Charger séries fraîches depuis le serveur
      await loadUserSeriesLibrary();
      
      // Vérifier présence série avec critères stricts
      const seriesFound = userSeriesLibrary.some(series => 
        series.series_name?.toLowerCase().trim() === seriesName.toLowerCase().trim() && 
        series.category === targetCategory
      );
      
      if (seriesFound) {
        const totalTime = Date.now() - startTime;
        console.log(`✅ [PHASE C.1] Série trouvée après ${attempt} tentative(s) en ${totalTime}ms`);
        
        // Déclencher retour bibliothèque avec succès
        const backToLibraryEvent = new CustomEvent('backToLibrary', {
          detail: { 
            reason: 'series_verified_success',
            seriesName,
            targetCategory,
            attempts: attempt,
            totalTime
          }
        });
        window.dispatchEvent(backToLibraryEvent);
        
        return { success: true, attempts: attempt, totalTime };
      }
      
      // Délai progressif avant retry
      if (attempt < maxAttempts) {
        const delayMs = baseDelayMs * attempt;
        console.log(`⏳ [PHASE C.1] Série non trouvée, retry dans ${delayMs}ms...`);
        await new Promise(resolve => setTimeout(resolve, delayMs));
      }
      
    } catch (error) {
      console.error(`❌ [PHASE C.1] Tentative ${attempt} échouée:`, error);
      if (attempt < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 300));
      }
    }
  }
  
  // Échec après toutes les tentatives
  const totalTime = Date.now() - startTime;
  console.error(`❌ [PHASE C.1] Série non trouvée après ${maxAttempts} tentatives en ${totalTime}ms`);
  
  // Fallback : Déclencher retour bibliothèque avec échec
  const backToLibraryEvent = new CustomEvent('backToLibrary', {
    detail: { 
      reason: 'series_verification_failed',
      seriesName,
      targetCategory,
      attempts: maxAttempts,
      totalTime
    }
  });
  window.dispatchEvent(backToLibraryEvent);
  
  return { success: false, attempts: maxAttempts, totalTime };
};

/**
 * PHASE C.1 - SYSTÈME VÉRIFICATION LIVRE UNIFIÉ
 * Version adaptée pour livres individuels avec même logique de retry
 */
export const verifyAndDisplayBook = async (bookTitle, targetCategory, books, loadBooks, loadStats = null) => {
  const maxAttempts = 3;
  const baseDelayMs = 500;
  const timeoutMs = 5000; // Timeout global 5s
  
  console.log(`🔍 [PHASE C.1] Vérification livre: "${bookTitle}" en catégorie "${targetCategory}"`);
  
  const startTime = Date.now();
  
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      console.log(`📚 [PHASE C.1] Tentative ${attempt}/${maxAttempts} - Chargement données...`);
      
      // Charger données fraîches (loadStats optionnel pour compatibilité)
      if (loadStats) {
        await Promise.all([loadBooks(), loadStats()]);
      } else {
        await loadBooks();
      }
      
      // Vérifier présence livre - correspondance partielle pour gérer les titres longs d'Open Library
      const bookTitleNorm = bookTitle.toLowerCase().trim();
      const bookFound = books.some(book => {
        const storedTitle = book.title?.toLowerCase().trim() || '';
        const titleMatch = storedTitle === bookTitleNorm ||
          storedTitle.includes(bookTitleNorm) ||
          bookTitleNorm.includes(storedTitle.substring(0, Math.min(storedTitle.length, 20)));
        return titleMatch && book.category === targetCategory;
      });
      
      if (bookFound) {
        const totalTime = Date.now() - startTime;
        console.log(`✅ [PHASE C.1] Livre trouvé après ${attempt} tentative(s) en ${totalTime}ms`);
        
        // Déclencher retour bibliothèque avec succès
        const backToLibraryEvent = new CustomEvent('backToLibrary', {
          detail: { 
            reason: 'book_verified_success',
            bookTitle,
            targetCategory,
            attempts: attempt,
            totalTime
          }
        });
        window.dispatchEvent(backToLibraryEvent);
        
        return { success: true, attempts: attempt, totalTime };
      }
      
      // Délai progressif avant retry (500ms, 1000ms, 1500ms)
      if (attempt < maxAttempts) {
        const delayMs = baseDelayMs * attempt;
        console.log(`⏳ [PHASE C.1] Livre non trouvé, retry dans ${delayMs}ms...`);
        await new Promise(resolve => setTimeout(resolve, delayMs));
      }
      
      // Vérification timeout global
      if (Date.now() - startTime > timeoutMs) {
        console.warn('⚠️ [PHASE C.1] Timeout global atteint, abandon verification');
        break;
      }
      
    } catch (error) {
      console.error(`❌ [PHASE C.1] Tentative ${attempt} échouée:`, error);
      
      // En cas d'erreur, délai plus court avant retry
      if (attempt < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, 300));
      }
    }
  }
  
  // Échec après toutes les tentatives
  const totalTime = Date.now() - startTime;
  console.error(`❌ [PHASE C.1] Livre non trouvé après ${maxAttempts} tentatives en ${totalTime}ms`);
  
  // Fallback UX : notification avec action manuelle
  toast.error(
    `Livre "${bookTitle}" ajouté avec succès mais non visible. Actualisez la page ou vérifiez l'onglet ${targetCategory}.`,
    {
      duration: 8000,
      action: {
        label: 'Actualiser',
        onClick: () => window.location.reload()
      }
    }
  );
  
  return { success: false, attempts: maxAttempts, totalTime };
};

export default {
  searchOpenLibrary,
  handleAddFromOpenLibrary,
  backToLibrary,
  handleSeriesClick,
  handleBookClick,
  calculateRelevanceScore,
  getRelevanceLevel,
  verifyAndDisplayBook,
  verifyAndDisplaySeries  // Phase C.1 - Nouvelle fonction
};