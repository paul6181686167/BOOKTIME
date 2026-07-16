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
import { displayBookTitleFrFirst, mergeOpenLibraryBooksByVolume } from '../../utils/openLibraryBookDisplay';
import { openStaticWikidataSeriesModal } from '../../utils/openStaticWikidataSeries';
import {
  dedupeWikidataStaticSeriesOverOpenLibrary,
  dedupeSeriesCardsByName,
  inferCategoryFromWikidataSearchEntry,
} from '../../utils/searchSourcePipeline';
import {
  attributeBookToSeries,
  attachBookToQuerySeries,
  buildWikidataSeriesMatcher,
  enrichWikidataCardFromCurated,
  findCuratedSeriesByQuery,
  resolveSeriesTotalBooks,
} from '../../utils/seriesAttribution';

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

    const wdPromise = fetch(
      `${backendUrl}/api/static-wikidata/series/search?q=${encodeURIComponent(query.trim())}&limit=10`,
      { headers: { Authorization: `Bearer ${token}` } }
    )
      .then((r) => (r.ok ? r.json() : null))
      .catch(() => null);
    
    // RECHERCHE GLOBALE : pas de filtre par catégorie, 40 résultats (double-pass OL côté backend)
    const response = await fetch(`${backendUrl}/api/openlibrary/search?q=${encodeURIComponent(query)}&limit=40`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });

    // ── Wikidata statique : cartes "spotlight" + matcher (indépendant du succès OL) ──
    // Les cartes Wikidata/curées doivent s'afficher même si Open Library échoue ou renvoie [].
    let wikidataSpotlight = [];
    let wikidataMatcher = () => null;
    try {
      let wdData = await wdPromise;
      let rows = wdData?.results || [];
      let fromSearch = rows.length > 0;
      if (!rows.length) {
        const topR = await fetch(
          `${backendUrl}/api/static-wikidata/series/top/by-popularity?limit=4`,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        if (topR.ok) {
          wdData = await topR.json();
          rows = wdData?.results || [];
          fromSearch = false;
        }
      }
      // Le matcher ne s'appuie que sur les vraies correspondances de recherche
      // (pas sur les tendances génériques) pour ne pas rattacher des livres au hasard.
      wikidataMatcher = buildWikidataSeriesMatcher(fromSearch ? rows : []);
      wikidataSpotlight = (rows || []).map((entry, i) => {
        const name = entry.name_fr || entry.name || entry.name_en || entry.label || entry.qid;
        // Auteur + nombre de tomes faisant autorité depuis le référentiel curé (par nom).
        const curated = enrichWikidataCardFromCurated(name, {
          author: entry.author_label || entry.author || '',
          totalBooks: entry.work_count || 0,
          category: inferCategoryFromWikidataSearchEntry(entry),
        });
        return {
          isSeriesCard: true,
          isStaticWikidataCard: true,
          wikidata_qid: entry.qid,
          id: `series_wd_${entry.qid}`,
          name,
          author: curated.author,
          category: curated.category || inferCategoryFromWikidataSearchEntry(entry),
          cover_url: null,
          totalBooks: curated.totalBooks,
          completedBooks: 0,
          progressPercent: 0,
          books: [],
          description: fromSearch
            ? `Wikidata · ${entry.work_count ?? 0} œuvre(s) · pop. ${entry.popularity ?? '—'}/100`
            : `Wikidata · tendances · pop. ${entry.popularity ?? '—'}/100`,
          relevanceScore: fromSearch ? 45000 - i * 100 : 40000,
          fromOpenLibrary: false,
        };
      });
    } catch (_) {
      /* optionnel */
    }

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
        const display_title = displayBookTitleFrFirst(book);
        const withDisplay = { ...book, display_title };
        return {
          ...withDisplay,
          isFromOpenLibrary: true,
          isOwned: detectBookOwnership(withDisplay, books),
          id: `ol_${book.ol_key}`,
          categoryBadge,
          category: book.category || categoryBadge.key || 'roman',
        };
      });

      // ── 3. ATTRIBUTION UNIQUE : chaque livre → une série (curé → Wikidata → saga) ──
      // Tout livre attribué est exclu des standalone (corrige LOTR : carte WD + tomes).
      const wdSpotlightByQid = new Map(
        wikidataSpotlight.filter(c => c.wikidata_qid).map(c => [c.wikidata_qid, c])
      );
      const seriesGroups = new Map(); // seriesKey → { attr, books: [] }
      const attributedIds = new Set();

      // Série curée correspondant à la requête (rattachement inter-langues par auteur).
      const querySeries = findCuratedSeriesByQuery(query);

      enriched.forEach(book => {
        // Ordre : curé (titre/variations/volume_titles) → Wikidata → saga,
        // puis repli sur la série de la requête (auteur + hors exclusions).
        let attr = attributeBookToSeries(book, { wikidataMatcher });
        if (!attr && querySeries) attr = attachBookToQuerySeries(book, querySeries);
        if (!attr) return;
        if (!seriesGroups.has(attr.seriesKey)) seriesGroups.set(attr.seriesKey, { attr, books: [] });
        seriesGroups.get(attr.seriesKey).books.push(book);
        if (book.ol_key) attributedIds.add(book.ol_key);
      });

      // ── 4. Construire une carte série par groupe ─────────────────────────
      const seriesCards = [];
      seriesGroups.forEach(({ attr, books: groupBooks }) => {
        const merged = mergeOpenLibraryBooksByVolume(groupBooks);
        const cover = merged.find(b => b.cover_url)?.cover_url || null;
        const author = groupBooks.find(b => b.author)?.author || '';

        if (attr.source === 'wikidata') {
          // Rattacher les tomes à la carte spotlight Wikidata existante (pas de doublon)
          const card = wdSpotlightByQid.get(attr.wikidata_qid);
          if (card) {
            card.books = merged;
            if (!card.cover_url && cover) card.cover_url = cover;
            if (!card.author && author) card.author = author;
            if (!card.totalBooks) card.totalBooks = merged.length;
            return;
          }
        }

        seriesCards.push({
          isSeriesCard: true,
          id: `series_${attr.source}_${attr.seriesKey}`,
          name: attr.seriesName,
          author,
          category: attr.seriesData?.category || groupBooks[0]?.category || 'roman',
          cover_url: cover,
          totalBooks: resolveSeriesTotalBooks(attr.seriesData, merged.length),
          books: merged,
          description: attr.seriesData?.description || `Série de ${attr.seriesName}`,
          relevanceScore: attr.source === 'saga' ? 100000 : 96000,
          fromStaticDB: attr.source === 'curated',
          fromOpenLibrary: attr.source === 'saga',
        });
      });

      // ── 5. Heuristique de repli : auteur + mots du query (livres non attribués) ──
      const remaining = enriched.filter(b => !attributedIds.has(b.ol_key));
      const authorGroups = {};
      remaining.forEach(book => {
        if (!book.author) return;
        const key = book.author.toLowerCase().trim();
        if (!authorGroups[key]) authorGroups[key] = { author: book.author, books: [], category: book.category };
        authorGroups[key].books.push(book);
      });

      const queryWords = query.toLowerCase().split(/\s+/).filter(w => w.length >= 3);
      Object.values(authorGroups).forEach(group => {
        if (group.books.length < 2) return;
        const matchingBooks = queryWords.length > 0
          ? group.books.filter(b => {
              const blob = `${b.display_title || ''} ${b.title || ''}`.toLowerCase();
              return queryWords.some(w => blob.includes(w));
            })
          : group.books;
        if (matchingBooks.length < 2) return;

        const seriesName = queryWords.length > 0 ? query.trim() : group.author;
        matchingBooks.forEach(b => {
          if (b.ol_key) attributedIds.add(b.ol_key);
        });
        const mergedMatching = mergeOpenLibraryBooksByVolume(matchingBooks);

        seriesCards.push({
          isSeriesCard: true,
          id: `series_author_${seriesName.toLowerCase().replace(/\s+/g, '_')}`,
          name: seriesName,
          author: group.author,
          category: group.category,
          cover_url: mergedMatching.find(b => b.cover_url)?.cover_url || null,
          totalBooks: mergedMatching.length,
          books: mergedMatching,
          description: `Série de ${mergedMatching.length} tome(s) de ${group.author}`,
          relevanceScore: 90000,
          fromOpenLibrary: true,
        });
      });

      // ── 6. Séries de la base statique (legacy query-based) — dédoublonnées ──
      const allSeriesNames = new Set([
        ...seriesCards.map(c => (c.name || '').toLowerCase()),
        ...wikidataSpotlight.map(c => (c.name || '').toLowerCase()),
      ]);
      const staticSeriesCards = generateSeriesCardsForSearch(query, data.books) || [];
      const dedupedStatic = staticSeriesCards.filter(
        c => !allSeriesNames.has((c.name || '').toLowerCase())
      );

      // ── 7. Livres individuels (réellement hors série) ────────────────────
      const standaloneBooks = enriched.filter(b => !attributedIds.has(b.ol_key));

      // ── 8. Fusion + dédup (priorité Wikidata sur les doublons) ───────────
      let finalResults = [
        ...seriesCards,
        ...dedupedStatic,
        ...wikidataSpotlight,
        ...standaloneBooks,
      ];
      finalResults = dedupeWikidataStaticSeriesOverOpenLibrary(finalResults);
      finalResults = dedupeSeriesCardsByName(finalResults);

      const totalSeries = finalResults.filter(c => c.isSeriesCard).length;
      setOpenLibraryResults(finalResults);
      toast.success(
        `${standaloneBooks.length} livre(s)` +
        (totalSeries > 0 ? ` + ${totalSeries} série(s)` : '') +
        ` trouvé(s)`
      );
    } else {
      // Open Library indisponible : afficher au moins les cartes Wikidata/tendances.
      if (wikidataSpotlight.length > 0) {
        setOpenLibraryResults(dedupeWikidataStaticSeriesOverOpenLibrary([...wikidataSpotlight]));
      } else {
        toast.error('Erreur lors de la recherche Open Library');
      }
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
    const openLibTitle = normalizeString(book.display_title || book.title);
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
    const addTitle = openLibraryBook.display_title || openLibraryBook.title;
    const bookData = {
      title: addTitle,
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
          bookTitle: addTitle,
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
export const handleSeriesClick = async (series, setSelectedSeries, setShowSeriesModal) => {
  if (series.wikidata_qid && series.isStaticWikidataCard) {
    await openStaticWikidataSeriesModal(series, setSelectedSeries, setShowSeriesModal);
    return;
  }
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
export const handleItemClick = async (item, setSelectedSeries, setShowSeriesModal, setSelectedBook, setShowBookModal) => {
  if (item.isSeriesCard) {
    await handleSeriesClick(item, setSelectedSeries, setShowSeriesModal);
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