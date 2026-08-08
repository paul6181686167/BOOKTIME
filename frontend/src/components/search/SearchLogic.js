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
import SeriesDetector from '../../utils/seriesDetector';
import { API_BASE_URL } from '../../config/environment';
import { displayBookTitleFrFirst, mergeOpenLibraryBooksByVolume } from '../../utils/openLibraryBookDisplay';
import { openStaticWikidataSeriesModal } from '../../utils/openStaticWikidataSeries';
import { buildOwnershipIndex, isBookOwned } from '../../utils/bookOwnership';
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
  findCuratedSeriesForBook,
  resolveSeriesTotalBooks,
} from '../../utils/seriesAttribution';

// Une réponse lente ne doit jamais écraser les résultats d'une recherche plus
// récente : chaque appel prend un numéro de séquence et seul le dernier a le droit
// d'écrire dans l'état. La requête précédente est en outre interrompue, pour ne pas
// consommer réseau et batterie pour un résultat qui ne sera pas affiché.
let searchSequence = 0;
let inFlightSearch = null;

// OL ne bloque plus l'UI : ce timeout ne sert qu'à abandonner l'enrichissement
// en arrière-plan. Wikidata (local) a son propre plafond bien plus court.
const OL_CLIENT_TIMEOUT_MS = 10000;
const WIKIDATA_CLIENT_TIMEOUT_MS = 2000;

/** fetch avec timeout local, sans annuler le signal parent (Wikidata continue). */
function fetchWithTimeout(url, options = {}, timeoutMs = OL_CLIENT_TIMEOUT_MS) {
  const local = new AbortController();
  const timer = setTimeout(() => local.abort(), timeoutMs);
  const parent = options.signal;
  const onParentAbort = () => local.abort();
  if (parent) {
    if (parent.aborted) local.abort();
    else parent.addEventListener('abort', onParentAbort, { once: true });
  }
  return fetch(url, { ...options, signal: local.signal }).finally(() => {
    clearTimeout(timer);
    if (parent) parent.removeEventListener('abort', onParentAbort);
  });
}

async function fetchWikidataSpotlight(query, token, backendUrl, signal) {
  let wikidataSpotlight = [];
  let wikidataMatcher = () => null;
  try {
    const wdRes = await fetch(
      `${backendUrl}/api/static-wikidata/series/search?q=${encodeURIComponent(query.trim())}&limit=10`,
      { headers: token ? { Authorization: `Bearer ${token}` } : {}, signal }
    );
    let wdData = wdRes.ok ? await wdRes.json() : null;
    let rows = wdData?.results || [];
    let fromSearch = rows.length > 0;
    if (!rows.length) {
      const topR = await fetch(
        `${backendUrl}/api/static-wikidata/series/top/by-popularity?limit=4`,
        { headers: token ? { Authorization: `Bearer ${token}` } : {}, signal }
      );
      if (topR.ok) {
        wdData = await topR.json();
        rows = wdData?.results || [];
        fromSearch = false;
      }
    }
    wikidataMatcher = buildWikidataSeriesMatcher(fromSearch ? rows : []);
    wikidataSpotlight = (rows || [])
      .map((entry, i) => {
        const name = entry.name_fr || entry.name || entry.name_en || entry.label || entry.qid;
        const curated = enrichWikidataCardFromCurated(name, {
          author: entry.author_label || entry.author || '',
          totalBooks: entry.work_count || 0,
          category: inferCategoryFromWikidataSearchEntry(entry),
        });
        // work_count peut être 0 dans l'index : on affiche quand même les hits
        // de recherche (sinon « 0 résultat » dès qu'Open Library est down).
        const totalBooks = curated.totalBooks || entry.work_count || (fromSearch ? 1 : 0);
        if (!fromSearch && totalBooks < 1) return null;
        return {
          isSeriesCard: true,
          isStaticWikidataCard: true,
          wikidata_qid: entry.qid,
          id: `series_wd_${entry.qid}`,
          name,
          author: curated.author,
          category: curated.category || inferCategoryFromWikidataSearchEntry(entry),
          cover_url: null,
          totalBooks,
          completedBooks: 0,
          progressPercent: 0,
          books: [],
          description: fromSearch
            ? `Wikidata · ${entry.work_count ?? 0} œuvre(s) · pop. ${entry.popularity ?? '—'}/100`
            : `Wikidata · tendances · pop. ${entry.popularity ?? '—'}/100`,
          relevanceScore: fromSearch ? 45000 - i * 100 : 40000,
          fromOpenLibrary: false,
        };
      })
      .filter(Boolean);
  } catch (_) {
    /* optionnel */
  }
  return { wikidataSpotlight, wikidataMatcher };
}

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

  // Cette recherche devient la référence ; la précédente est abandonnée.
  const sequence = ++searchSequence;
  const isStale = () => sequence !== searchSequence;
  if (inFlightSearch) inFlightSearch.abort();
  const controller = new AbortController();
  inFlightSearch = controller;

  setSearchLoading(true);
  setIsSearchMode(true);
  setLastSearchTerm(query);

  // Cartes curées locales : disponibles même si le backend/OL est down
  const applyCuratedFallback = (extra = []) => {
    const curated = generateSeriesCardsForSearch(query, []) || [];
    let results = dedupeSeriesCardsByName(
      dedupeWikidataStaticSeriesOverOpenLibrary([...curated, ...extra])
    );
    if (isStale()) return results;
    setOpenLibraryResults(results);
    return results;
  };

  let didToast = false;
  const toastOnce = (message, kind = 'success') => {
    if (didToast || isStale()) return;
    didToast = true;
    if (kind === 'error') toast.error(message);
    else toast.success(message);
  };

  // 1) Curé synchrone → l'UI a déjà des cartes (One Piece, etc.)
  const immediate = applyCuratedFallback([]);
  // Dès qu'il y a du local, on coupe le spinner : OL ne doit plus faire attendre.
  if (immediate.length > 0) {
    setSearchLoading(false);
    toastOnce(`${immediate.length} résultat(s) trouvé(s)`);
  }

  const token = localStorage.getItem('token');
  const backendUrl = API_BASE_URL;
  const authHeaders = {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    'Content-Type': 'application/json',
  };

  // 2) Wikidata (backend local, rapide) + OL (lent) en parallèle
  const wdRace = Promise.race([
    fetchWikidataSpotlight(query, token, backendUrl, controller.signal),
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error('wd-timeout')), WIKIDATA_CLIENT_TIMEOUT_MS)
    ),
  ]).catch(() => ({ wikidataSpotlight: [], wikidataMatcher: () => null }));

  const olPromise = fetchWithTimeout(
    `${backendUrl}/api/openlibrary/search?q=${encodeURIComponent(query)}&limit=40`,
    { headers: authHeaders, signal: controller.signal },
    OL_CLIENT_TIMEOUT_MS
  );

  let wikidataSpotlight = [];
  let wikidataMatcher = () => null;

  try {
    const wd = await wdRace;
    if (!isStale()) {
      wikidataSpotlight = wd.wikidataSpotlight || [];
      wikidataMatcher = wd.wikidataMatcher || (() => null);
      const merged = applyCuratedFallback(wikidataSpotlight);
      setSearchLoading(false);
      if (merged.length > 0) toastOnce(`${merged.length} résultat(s) trouvé(s)`);
    }
  } catch (_) {
    if (!isStale()) setSearchLoading(false);
  }

  // 3) Open Library en arrière-plan : enrichit la grille sans bloquer
  if (isStale()) {
    if (inFlightSearch === controller) inFlightSearch = null;
    return;
  }

  try {
    const response = await olPromise;
    if (isStale()) return;

    if (!response?.ok) {
      const results = applyCuratedFallback(wikidataSpotlight);
      if (results.length === 0) toastOnce('Aucun résultat trouvé', 'error');
      return;
    }

    const data = await response.json();
    if (isStale()) return;

    if (data.source_unavailable || !(data.books || []).length) {
      const results = applyCuratedFallback(wikidataSpotlight);
      if (results.length === 0) {
        toastOnce(
          data.source_unavailable
            ? 'Open Library indisponible — aucun résultat local'
            : 'Aucun résultat trouvé',
          'error'
        );
      }
      return;
    }

    // ── 1. Dédoublonnage par ol_key ──────────────────────────────────────
    const seen = new Set();
    const uniqueBooks = (data.books || []).filter((b) => {
      if (!b.ol_key || seen.has(b.ol_key)) return false;
      seen.add(b.ol_key);
      return true;
    });

    // ── 2. Enrichir chaque livre (ownership + badge) ─────────────────────
    const ownershipIndex = buildOwnershipIndex(books);
    const enriched = uniqueBooks.map((book) => {
      const categoryBadge = getCategoryBadgeFromBook(book);
      const display_title = displayBookTitleFrFirst(book);
      const withDisplay = { ...book, display_title };
      return {
        ...withDisplay,
        isFromOpenLibrary: true,
        isOwned: isBookOwned(withDisplay, ownershipIndex),
        id: `ol_${book.ol_key}`,
        categoryBadge,
        category: book.category || categoryBadge.key || 'roman',
      };
    });

    // ── 3. ATTRIBUTION UNIQUE : chaque livre → une série ──
    const wdSpotlightByQid = new Map(
      wikidataSpotlight.filter((c) => c.wikidata_qid).map((c) => [c.wikidata_qid, c])
    );
    const seriesGroups = new Map();
    const attributedIds = new Set();
    const querySeries = findCuratedSeriesByQuery(query);

    enriched.forEach((book) => {
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
      const cover = merged.find((b) => b.cover_url)?.cover_url || null;
      const author = groupBooks.find((b) => b.author)?.author || '';

      if (attr.source === 'wikidata') {
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

    // ── 5. Heuristique de repli : auteur + mots du query ──
    const remaining = enriched.filter((b) => !attributedIds.has(b.ol_key));
    const authorGroups = {};
    remaining.forEach((book) => {
      if (!book.author) return;
      const key = book.author.toLowerCase().trim();
      if (!authorGroups[key]) authorGroups[key] = { author: book.author, books: [], category: book.category };
      authorGroups[key].books.push(book);
    });

    const queryWords = query.toLowerCase().split(/\s+/).filter((w) => w.length >= 3);
    Object.values(authorGroups).forEach((group) => {
      if (group.books.length < 2) return;
      const matchingBooks =
        queryWords.length > 0
          ? group.books.filter((b) => {
              const blob = `${b.display_title || ''} ${b.title || ''}`.toLowerCase();
              return queryWords.some((w) => blob.includes(w));
            })
          : group.books;
      if (matchingBooks.length < 2) return;

      const seriesName = queryWords.length > 0 ? query.trim() : group.author;
      matchingBooks.forEach((b) => {
        if (b.ol_key) attributedIds.add(b.ol_key);
      });
      const mergedMatching = mergeOpenLibraryBooksByVolume(matchingBooks);

      seriesCards.push({
        isSeriesCard: true,
        id: `series_author_${seriesName.toLowerCase().replace(/\s+/g, '_')}`,
        name: seriesName,
        author: group.author,
        category: group.category,
        cover_url: mergedMatching.find((b) => b.cover_url)?.cover_url || null,
        totalBooks: mergedMatching.length,
        books: mergedMatching,
        description: `Série de ${mergedMatching.length} tome(s) de ${group.author}`,
        relevanceScore: 90000,
        fromOpenLibrary: true,
      });
    });

    // ── 6. Séries de la base statique ──
    const allSeriesNames = new Set([
      ...seriesCards.map((c) => (c.name || '').toLowerCase()),
      ...wikidataSpotlight.map((c) => (c.name || '').toLowerCase()),
    ]);
    const staticSeriesCards = generateSeriesCardsForSearch(query, data.books) || [];
    const dedupedStatic = staticSeriesCards.filter(
      (c) => !allSeriesNames.has((c.name || '').toLowerCase())
    );

    // ── 7–8. Livres individuels + fusion ──
    const standaloneBooks = enriched.filter((b) => !attributedIds.has(b.ol_key));
    let finalResults = [
      ...seriesCards,
      ...dedupedStatic,
      ...wikidataSpotlight,
      ...standaloneBooks,
    ];
    finalResults = dedupeWikidataStaticSeriesOverOpenLibrary(finalResults);
    finalResults = dedupeSeriesCardsByName(finalResults);

    if (isStale()) return;
    setOpenLibraryResults(finalResults);
    const totalSeries = finalResults.filter((c) => c.isSeriesCard).length;
    // Toast seulement si on n'avait encore rien annoncé (titre inconnu du curé)
    toastOnce(
      `${standaloneBooks.length} livre(s)` +
        (totalSeries > 0 ? ` + ${totalSeries} série(s)` : '') +
        ` trouvé(s)`
    );
  } catch (error) {
    if (isStale() || error?.name === 'AbortError') return;
    console.error('Erreur recherche Open Library (arrière-plan):', error);
    const results = applyCuratedFallback(wikidataSpotlight);
    if (results.length === 0) toastOnce('Aucun résultat trouvé', 'error');
  } finally {
    if (!isStale()) setSearchLoading(false);
    if (inFlightSearch === controller) inFlightSearch = null;
  }
};

// La détection de propriété vit désormais dans utils/bookOwnership.js (règle unique)

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
    return;
  }

  const addTitle =
    openLibraryBook.display_title ||
    openLibraryBook.title_fr ||
    openLibraryBook.title;
  const categoryBadge =
    openLibraryBook.categoryBadge || getCategoryBadgeFromBook(openLibraryBook);
  let targetCategory = categoryBadge?.key;
  if (!targetCategory || !['roman', 'bd', 'manga'].includes(targetCategory)) {
    targetCategory = ['roman', 'bd', 'manga'].includes(activeTab)
      ? activeTab
      : 'roman';
  }

  // Détection de série locale (synchrone) — plus d'aller-retour /api/series/detect
  let saga = openLibraryBook.saga || null;
  let volume_number = openLibraryBook.volume_number || null;
  let auto_detected_series = false;
  let detection_confidence = null;
  if (!saga) {
    const curated = findCuratedSeriesForBook({
      title: addTitle,
      display_title: addTitle,
      original_title: openLibraryBook.original_title,
      author: openLibraryBook.author,
    });
    if (curated?.seriesName) {
      saga = curated.seriesName;
      auto_detected_series = true;
      detection_confidence = curated.confidence || null;
    }
  }

  try {
    setAddingBooks((prev) => new Set([...prev, openLibraryBook.ol_key]));

    // Feedback immédiat : la grille et le toast ne dépendent plus du reload bibliothèque
    setOpenLibraryResults((prev) =>
      prev.map((book) =>
        book.ol_key === openLibraryBook.ol_key ? { ...book, isOwned: true } : book
      )
    );

    const token = localStorage.getItem('token');
    const backendUrl = API_BASE_URL;

    const response = await fetch(`${backendUrl}/api/openlibrary/import`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ol_key: openLibraryBook.ol_key,
        category: targetCategory,
        title: addTitle,
        title_fr: openLibraryBook.title_fr || null,
        author: openLibraryBook.author || '',
        cover_url: openLibraryBook.cover_url || '',
        original_title:
          openLibraryBook.original_title || openLibraryBook.title || null,
        isbn: openLibraryBook.isbn || '',
        description: openLibraryBook.description || '',
        first_publish_year: openLibraryBook.first_publish_year || null,
        saga,
        volume_number,
        auto_detected_series,
        detection_confidence,
      }),
    });

    if (response.ok) {
      toast.success(`« ${addTitle} » ajouté`, { duration: 2000 });

      window.dispatchEvent(
        new CustomEvent('backToLibrary', {
          detail: {
            reason: 'book_added_success',
            bookTitle: addTitle,
            targetCategory,
          },
        })
      );

      // Reload bibliothèque en arrière-plan (ne bloque plus le clic)
      Promise.resolve()
        .then(() =>
          loadStats ? Promise.all([loadBooks(), loadStats()]) : loadBooks()
        )
        .catch((err) => console.warn('Refresh bibliothèque après ajout:', err));
    } else {
      const error = await response.json().catch(() => ({}));
      if (response.status === 409) {
        toast.error('Ce livre est déjà dans votre collection');
      } else {
        // Annuler l'optimistic "possédé" si l'import a réellement échoué
        setOpenLibraryResults((prev) =>
          prev.map((book) =>
            book.ol_key === openLibraryBook.ol_key
              ? { ...book, isOwned: false }
              : book
          )
        );
        toast.error(error.detail || "Erreur lors de l'ajout du livre");
      }
    }
  } catch (error) {
    console.error('Erreur ajout livre:', error);
    setOpenLibraryResults((prev) =>
      prev.map((book) =>
        book.ol_key === openLibraryBook.ol_key
          ? { ...book, isOwned: false }
          : book
      )
    );
    toast.error("Erreur lors de l'ajout du livre");
  } finally {
    setAddingBooks((prev) => {
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