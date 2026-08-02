/**
 * Page de Recommandations — sections contextuelles, filtre par onglet actif
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import {
  SparklesIcon,
  FireIcon,
  UserIcon,
  BookOpenIcon,
  ArrowLeftIcon,
  ArrowPathIcon,
  XMarkIcon,
  PlusIcon,
  CheckIcon,
  ClockIcon,
  HandThumbUpIcon,
  HandThumbDownIcon,
} from '@heroicons/react/24/outline';
import {
  HandThumbUpIcon as HandThumbUpIconSolid,
  HandThumbDownIcon as HandThumbDownIconSolid,
} from '@heroicons/react/24/solid';
import { recommendationService } from '../../services/recommendationService';
import { API_BASE_URL } from '../../config/environment';

// ── Cache (sessionStorage) ────────────────────────────────────────────────
// Évite de recalculer les recommandations à chaque visite de la page.
const CACHE_PREFIX = 'booktime_reco_cache_';
const CACHE_TTL_MS = 10 * 60 * 1000; // 10 minutes

function readCache(tab) {
  try {
    const raw = sessionStorage.getItem(CACHE_PREFIX + tab);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || Date.now() - parsed.timestamp > CACHE_TTL_MS) return null;
    return parsed;
  } catch {
    return null;
  }
}

function writeCache(tab, sections, userProfile) {
  try {
    sessionStorage.setItem(
      CACHE_PREFIX + tab,
      JSON.stringify({ timestamp: Date.now(), sections, userProfile })
    );
  } catch {
    // quota dépassé ou storage indisponible → on ignore
  }
}

function clearRecoCache() {
  try {
    Object.keys(sessionStorage)
      .filter((k) => k.startsWith(CACHE_PREFIX))
      .forEach((k) => sessionStorage.removeItem(k));
  } catch {
    // ignore
  }
}

function catalogPath(bookId) {
  if (!bookId) return null;
  if (bookId.startsWith('jikan_') || bookId.startsWith('gbooks_')) {
    return `/catalogue/${bookId}`;
  }
  const stripped = bookId.startsWith('/') ? bookId.slice(1) : bookId;
  return `/catalogue/${stripped}`;
}

// ── helpers ─────────────────────────────────────────────────────────────────

const CATEGORY_MAP = {
  roman: { label: 'Romans', api: 'roman' },
  'graphic_novel': { label: 'Romans Graphiques', api: null }, // manga + bd
  manga: { label: 'Mangas', api: 'manga' },
  bd: { label: 'BD', api: 'bd' },
};

function detectActiveCategory() {
  const stored = localStorage.getItem('booktime_active_tab');
  return stored || 'roman';
}

function categoryForApi(tab) {
  if (tab === 'graphic_novel') return null; // no filter → show all graphic novels mixed
  return CATEGORY_MAP[tab]?.api || null;
}

function isUpcoming(book) {
  if (!book.published_date && !book.publish_date) return false;
  const raw = book.published_date || book.publish_date || '';
  const year = parseInt(raw.substring(0, 4), 10);
  if (!year) return false;
  return year > new Date().getFullYear() ||
    (year === new Date().getFullYear() && raw > new Date().toISOString().substring(0, 10));
}

// ── Section display config ────────────────────────────────────────────────

const SECTION_CONFIG = {
  algorithm_author: {
    icon: UserIcon,
    color: 'blue',
    title: (items) => {
      const author = items[0]?.author || '';
      return author ? `Parce que tu lis ${author}` : 'Parce que tu aimes cet auteur';
    },
  },
  algorithm_series: {
    icon: BookOpenIcon,
    color: 'green',
    title: () => 'Prochain tome de tes séries en cours',
  },
  algorithm_similarity: {
    icon: SparklesIcon,
    color: 'purple',
    title: () => 'Livres similaires à ce que tu as terminé',
  },
  algorithm_category: {
    icon: SparklesIcon,
    color: 'indigo',
    title: () => 'Dans ton genre préféré',
  },
  popular: {
    icon: FireIcon,
    color: 'orange',
    title: () => 'Tendances du moment',
  },
};

const COLOR_CLASSES = {
  blue:   { badge: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300', icon: 'text-blue-500', border: 'border-blue-200 dark:border-blue-800' },
  green:  { badge: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300', icon: 'text-green-500', border: 'border-green-200 dark:border-green-800' },
  purple: { badge: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-300', icon: 'text-purple-500', border: 'border-purple-200 dark:border-purple-800' },
  indigo: { badge: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300', icon: 'text-indigo-500', border: 'border-indigo-200 dark:border-indigo-800' },
  orange: { badge: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300', icon: 'text-orange-500', border: 'border-orange-200 dark:border-orange-800' },
};

// ── Book Card ─────────────────────────────────────────────────────────────

const BookCard = ({ book, onAdd, onNotInterested, onFeedback, userBooks = [] }) => {
  const navigate = useNavigate();
  const [adding, setAdding] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const path = catalogPath(book.book_id || book.ol_key);

  const alreadyIn = userBooks.some(
    (b) =>
      b.title?.toLowerCase() === book.title?.toLowerCase() ||
      (book.book_id && (b.ol_key === book.book_id || b.id === book.book_id))
  );

  if (dismissed) return null;

  const handleAdd = async () => {
    if (alreadyIn || adding) return;
    setAdding(true);
    try {
      await onAdd(book);
      toast.success(`"${book.title}" ajouté à ta bibliothèque`);
    } catch {
      toast.error('Erreur lors de l\'ajout');
    } finally {
      setAdding(false);
    }
  };

  const handleDismiss = async () => {
    setDismissed(true);
    try {
      await onNotInterested(book.book_id);
    } catch {
      // silently ignore
    }
  };

  const handleFeedback = async (type) => {
    if (feedback) return;
    setFeedback(type);
    try {
      await onFeedback?.(book.book_id, type);
    } catch {
      // silently ignore
    }
    if (type === 'like') {
      toast.success('Merci ! On t\'en proposera plus comme ça');
    } else {
      toast.success('Noté, on affinera tes suggestions');
      // Un dislike masque la carte après un court instant
      setTimeout(() => setDismissed(true), 400);
    }
  };

  const upcoming = isUpcoming(book);

  return (
    <div className="relative flex flex-col bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden hover:shadow-md transition-shadow duration-200">
      {/* Badge À paraître */}
      {upcoming && (
        <div className="absolute top-2 left-2 z-10 flex items-center gap-1 bg-amber-500 text-white text-xs font-semibold px-2 py-0.5 rounded-full shadow">
          <ClockIcon className="h-3 w-3" />
          À paraître
        </div>
      )}

      {/* Bouton fermer */}
      <button
        onClick={handleDismiss}
        className="absolute top-2 right-2 z-10 p-1 rounded-full bg-white/80 dark:bg-gray-900/80 hover:bg-red-50 dark:hover:bg-red-900/30 text-gray-400 hover:text-red-500 transition-colors"
        title="Pas intéressé"
      >
        <XMarkIcon className="h-4 w-4" />
      </button>

      {/* Couverture cliquable */}
      <div
        className={`h-44 bg-gray-100 dark:bg-gray-700 flex items-center justify-center overflow-hidden ${path ? 'cursor-pointer' : ''}`}
        onClick={() => path && navigate(path)}
      >
        {book.cover_url ? (
          <img
            src={book.cover_url}
            alt={book.title}
            className="h-full w-full object-cover hover:scale-105 transition-transform duration-200"
            onError={(e) => { e.target.style.display = 'none'; }}
          />
        ) : (
          <BookOpenIcon className="h-12 w-12 text-gray-300" />
        )}
      </div>

      {/* Infos */}
      <div className="flex flex-col flex-1 p-3 gap-1">
        <h3
          className={`text-sm font-semibold text-gray-900 dark:text-white line-clamp-2 leading-tight ${path ? 'cursor-pointer hover:text-blue-600 dark:hover:text-blue-400 transition-colors' : ''}`}
          onClick={() => path && navigate(path)}
        >
          {book.title}
        </h3>
        <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-1">{book.author}</p>

        {book.reason && (
          <p className="text-xs text-gray-400 dark:text-gray-500 italic line-clamp-2 mt-1">{book.reason}</p>
        )}

        {/* Score */}
        {book.score > 0 && (
          <div className="flex items-center gap-1 mt-1">
            {Array.from({ length: 5 }).map((_, i) => (
              <div
                key={i}
                className={`h-1.5 w-4 rounded-full ${i < Math.round(book.score * 5) ? 'bg-yellow-400' : 'bg-gray-200 dark:bg-gray-600'}`}
              />
            ))}
          </div>
        )}

        {/* Feedback like / dislike */}
        {book.book_id && !alreadyIn && (
          <div className="flex items-center gap-2 mt-1">
            <button
              onClick={() => handleFeedback('like')}
              disabled={!!feedback}
              title="J'aime cette suggestion"
              className={`p-1.5 rounded-full transition-colors ${
                feedback === 'like'
                  ? 'bg-green-100 text-green-600 dark:bg-green-900/40 dark:text-green-400'
                  : 'text-gray-400 hover:text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20'
              } disabled:cursor-default`}
            >
              {feedback === 'like' ? (
                <HandThumbUpIconSolid className="h-4 w-4" />
              ) : (
                <HandThumbUpIcon className="h-4 w-4" />
              )}
            </button>
            <button
              onClick={() => handleFeedback('dislike')}
              disabled={!!feedback}
              title="Pas pour moi"
              className={`p-1.5 rounded-full transition-colors ${
                feedback === 'dislike'
                  ? 'bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-400'
                  : 'text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20'
              } disabled:cursor-default`}
            >
              {feedback === 'dislike' ? (
                <HandThumbDownIconSolid className="h-4 w-4" />
              ) : (
                <HandThumbDownIcon className="h-4 w-4" />
              )}
            </button>
          </div>
        )}

        {/* Bouton */}
        <div className="mt-auto pt-2">
          {alreadyIn ? (
            <div className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400 font-medium">
              <CheckIcon className="h-4 w-4" />
              Dans ta bibliothèque
            </div>
          ) : (
            <button
              onClick={handleAdd}
              disabled={adding}
              className="btn-ripple w-full flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white rounded-lg transition-colors disabled:opacity-60"
            >
              {adding ? (
                <span className="btn-spinner" style={{width:'0.7rem',height:'0.7rem',borderWidth:'1.5px'}} />
              ) : (
                <PlusIcon className="h-3.5 w-3.5" />
              )}
              {adding ? 'Ajout…' : (upcoming ? 'Ajouter aux À venir' : 'Ajouter')}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// ── Section ───────────────────────────────────────────────────────────────

const RecommendationSection = ({ source, items, onAdd, onNotInterested, onFeedback, userBooks }) => {
  const cfg = SECTION_CONFIG[source] || SECTION_CONFIG['popular'];
  const colors = COLOR_CLASSES[cfg.color];
  const Icon = cfg.icon;

  const visible = items.filter(
    (b) => !userBooks.some(
      (u) =>
        u.title?.toLowerCase() === b.title?.toLowerCase() ||
        (b.book_id && (u.ol_key === b.book_id || u.id === b.book_id))
    )
  );

  if (visible.length === 0) return null;

  return (
    <div className="mb-10">
      {/* Titre de section */}
      <div className={`flex items-center gap-2 mb-4 pb-2 border-b ${colors.border}`}>
        <Icon className={`h-5 w-5 ${colors.icon}`} />
        <h2 className="text-base font-semibold text-gray-800 dark:text-gray-100">
          {cfg.title(items)}
        </h2>
        <span className={`ml-auto text-xs font-medium px-2 py-0.5 rounded-full ${colors.badge}`}>
          {visible.length} livre{visible.length > 1 ? 's' : ''}
        </span>
      </div>

      {/* Grille */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
        {visible.slice(0, 12).map((book, idx) => (
          <BookCard
            key={book.book_id || `${source}-${idx}`}
            book={book}
            onAdd={onAdd}
            onNotInterested={onNotInterested}
            onFeedback={onFeedback}
            userBooks={userBooks}
          />
        ))}
      </div>
    </div>
  );
};

// ── Skeletons de chargement ───────────────────────────────────────────────

const SkeletonCard = () => (
  <div className="flex flex-col bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden animate-pulse">
    <div className="h-44 bg-gray-200 dark:bg-gray-700" />
    <div className="flex flex-col flex-1 p-3 gap-2">
      <div className="h-3.5 bg-gray-200 dark:bg-gray-700 rounded w-full" />
      <div className="h-3.5 bg-gray-200 dark:bg-gray-700 rounded w-2/3" />
      <div className="h-2.5 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mt-1" />
      <div className="h-7 bg-gray-200 dark:bg-gray-700 rounded-lg mt-3" />
    </div>
  </div>
);

const SkeletonSection = () => (
  <div className="mb-10">
    <div className="flex items-center gap-2 mb-4 pb-2 border-b border-gray-100 dark:border-gray-700">
      <div className="h-5 w-5 rounded bg-gray-200 dark:bg-gray-700 animate-pulse" />
      <div className="h-4 w-56 rounded bg-gray-200 dark:bg-gray-700 animate-pulse" />
    </div>
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
      {Array.from({ length: 6 }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  </div>
);

// ── Main Page ─────────────────────────────────────────────────────────────

const RecommendationPage = () => {
  const navigate = useNavigate();
  const [sections, setSections] = useState({});
  const [userProfile, setUserProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('all');
  const [appTab] = useState(detectActiveCategory);
  const [userBooks, setUserBooks] = useState([]);

  // Charge la liste des livres de l'utilisateur pour détecter "déjà dans bibliothèque"
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) return;
    fetch(`${API_BASE_URL}/api/books`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.json())
      .then((data) => setUserBooks(Array.isArray(data) ? data : data.books || []))
      .catch(() => {});
  }, []);

  const loadRecommendations = useCallback(async (tab, { force = false } = {}) => {
    // Utilise le cache si disponible et non expiré (sauf rafraîchissement forcé)
    if (!force) {
      const cached = readCache(tab);
      if (cached) {
        setSections(cached.sections || {});
        if (cached.userProfile) setUserProfile(cached.userProfile);
        setIsLoading(false);
        return;
      }
    }

    setIsLoading(true);
    try {
      const category = tab === 'all' ? categoryForApi(appTab) : tab === 'graphic_novel' ? null : tab;

      const [personalizedRes, popularRes, profileRes] = await Promise.allSettled([
        recommendationService.getPersonalized({ limit: 30, category, refresh: force }),
        recommendationService.getPopular({ limit: 12, category }),
        recommendationService.getUserProfile(),
      ]);

      // Regroupe par source
      const grouped = {};

      if (personalizedRes.status === 'fulfilled' && personalizedRes.value?.success) {
        const recs = personalizedRes.value.data?.recommendations || [];
        recs.forEach((r) => {
          const src = r.source || 'algorithm_category';
          if (!grouped[src]) grouped[src] = [];
          // Le backend renvoie `reasons` (tableau) ; la carte affiche `reason`
          // et `score`. On normalise ici pour afficher la justification.
          grouped[src].push({
            ...r,
            reason: r.reason || (Array.isArray(r.reasons) ? r.reasons[0] : undefined),
            score: r.score ?? r.confidence_score,
          });
        });
      }

      if (popularRes.status === 'fulfilled' && popularRes.value?.success) {
        const pops = popularRes.value.data?.recommendations || [];
        if (pops.length > 0) {
          grouped['popular'] = pops;
        }
      }

      let profile = null;
      if (profileRes.status === 'fulfilled' && profileRes.value?.success) {
        profile = profileRes.value.data;
        setUserProfile(profile);
      }

      setSections(grouped);
      writeCache(tab, grouped, profile);
    } catch (err) {
      console.error('Erreur chargement recommandations:', err);
      toast.error('Erreur lors du chargement');
    } finally {
      setIsLoading(false);
    }
  }, [appTab]);

  useEffect(() => {
    loadRecommendations(activeTab);
  }, [activeTab, loadRecommendations]);

  const handleRefresh = useCallback(() => {
    clearRecoCache();
    loadRecommendations(activeTab, { force: true });
  }, [activeTab, loadRecommendations]);

  const handleAdd = async (book) => {
    await recommendationService.addRecommendedBook(book);
    setUserBooks((prev) => [...prev, book]);
    // Le livre ajouté ne doit plus être recommandé : on invalide le cache
    clearRecoCache();
  };

  const handleNotInterested = async (bookId) => {
    if (bookId) await recommendationService.markAsNotInterested(bookId);
    // Le contenu affiché change : on invalide le cache pour la prochaine visite
    clearRecoCache();
  };

  const handleFeedback = async (bookId, type) => {
    if (!bookId) return;
    await recommendationService.submitFeedback(bookId, type);
    // Le feedback influence les prochaines recos : on invalide le cache
    clearRecoCache();
  };

  const totalRecs = Object.values(sections).reduce((s, arr) => s + arr.length, 0);
  const appTabLabel = CATEGORY_MAP[appTab]?.label || '';

  // Cold start : charger les livres populaires du catalogue si aucune reco
  const [coldStartBooks, setColdStartBooks] = useState([]);
  useEffect(() => {
    if (!isLoading && totalRecs === 0) {
      const cat = categoryForApi(activeTab === 'all' ? appTab : activeTab);
      const url = `${API_BASE_URL}/api/catalog/popular?limit=18${cat ? `&category=${cat}` : ''}`;
      fetch(url)
        .then((r) => r.ok ? r.json() : { books: [] })
        .then((d) => setColdStartBooks(d.books || []))
        .catch(() => {});
    }
  }, [isLoading, totalRecs, activeTab, appTab]);

  // « Tous » reste distinct des filtres catégorie (évite 2× « Romans » si l'onglet lib est roman)
  const TABS = [
    { id: 'all', label: 'Tous' },
    { id: 'roman', label: 'Romans' },
    { id: 'manga', label: 'Mangas' },
    { id: 'bd', label: 'BD' },
  ];

  const ORDER = ['algorithm_series', 'algorithm_author', 'algorithm_similarity', 'algorithm_category', 'popular'];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Bouton retour */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/')}
          className="inline-flex items-center space-x-2 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors duration-200"
        >
          <ArrowLeftIcon className="h-5 w-5" />
          <span>Retour à la bibliothèque</span>
        </button>
      </div>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div className="flex items-center gap-3">
          <SparklesIcon className="h-8 w-8 text-blue-600" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Recommandations</h1>
            {userProfile?.has_books && (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Basé sur tes {userProfile.total_books} livres
                {appTabLabel ? ` · Onglet actif : ${appTabLabel}` : ''}
              </p>
            )}
          </div>
        </div>

        <button
          onClick={handleRefresh}
          disabled={isLoading}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors disabled:opacity-50"
        >
          <ArrowPathIcon className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          Rafraîchir
        </button>
      </div>

      {/* Statistiques */}
      {userProfile?.has_books && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          {[
            { label: 'Livres', value: userProfile.total_books, icon: BookOpenIcon, color: 'blue' },
            { label: 'Auteurs favoris', value: userProfile.favorite_authors?.length || 0, icon: UserIcon, color: 'green' },
            { label: 'Complétion', value: `${Math.round((userProfile.reading_patterns?.completion_rate || 0) * 100)}%`, icon: SparklesIcon, color: 'purple' },
            { label: 'Note moy.', value: (userProfile.reading_patterns?.average_rating || 0).toFixed(1), icon: FireIcon, color: 'orange' },
          ].map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="bg-white dark:bg-gray-800 rounded-xl p-4 border border-gray-100 dark:border-gray-700 text-center">
              <Icon className={`h-6 w-6 mx-auto mb-1 text-${color}-500`} />
              <div className={`text-xl font-bold text-${color}-600`}>{value}</div>
              <div className="text-xs text-gray-500 dark:text-gray-400">{label}</div>
            </div>
          ))}
        </div>
      )}

      {/* Onglets catégorie */}
      <div className="flex gap-2 mb-8 flex-wrap">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === t.id
                ? 'bg-blue-600 text-white shadow-sm'
                : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Contenu */}
      {isLoading ? (
        <div>
          <SkeletonSection />
          <SkeletonSection />
        </div>
      ) : totalRecs === 0 ? (
        <div>
          <div className="text-center py-8">
            <SparklesIcon className="h-12 w-12 text-gray-200 dark:text-gray-700 mx-auto mb-3" />
            <h2 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-1">
              Pas encore de recommandations personnalisées
            </h2>
            <p className="text-gray-500 dark:text-gray-400 text-sm max-w-sm mx-auto">
              Ajoute des livres à ta bibliothèque pour recevoir des suggestions adaptées à tes goûts.
            </p>
          </div>
          {coldStartBooks.length > 0 && (
            <div className="mt-4">
              <div className="flex items-center gap-2 mb-4 pb-2 border-b border-orange-200 dark:border-orange-800">
                <FireIcon className="h-5 w-5 text-orange-500" />
                <h2 className="text-base font-semibold text-gray-800 dark:text-gray-100">
                  Tendances du moment — par où commencer ?
                </h2>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
                {coldStartBooks.map((book, idx) => (
                  <BookCard
                    key={book.ol_key || idx}
                    book={{ ...book, book_id: book.ol_key }}
                    onAdd={handleAdd}
                    onNotInterested={handleNotInterested}
                    onFeedback={handleFeedback}
                    userBooks={userBooks}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div>
          {ORDER.map((src) =>
            sections[src] ? (
              <RecommendationSection
                key={src}
                source={src}
                items={sections[src]}
                onAdd={handleAdd}
                onNotInterested={handleNotInterested}
                onFeedback={handleFeedback}
                userBooks={userBooks}
              />
            ) : null
          )}
          {/* Sources non répertoriées */}
          {Object.keys(sections)
            .filter((s) => !ORDER.includes(s))
            .map((src) => (
              <RecommendationSection
                key={src}
                source={src}
                items={sections[src]}
                onAdd={handleAdd}
                onNotInterested={handleNotInterested}
                onFeedback={handleFeedback}
                userBooks={userBooks}
              />
            ))}
        </div>
      )}
    </div>
  );
};

export default RecommendationPage;
