/**
 * Page de Recommandations — sections contextuelles, filtre par onglet actif
 */
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
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
import { displayBookTitleFrFirst } from '../../utils/openLibraryBookDisplay';

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

const PRIMARY_TABS = [
  { id: 'pour_toi', label: 'Pour toi' },
  { id: 'aime', label: 'Parce que vous avez aimé' },
  { id: 'lisez', label: 'Parce que vous lisez' },
  { id: 'similaires', label: 'Similaires à…' },
];

const GENRE_TABS = [
  { id: 'genre_jeunesse', label: 'Jeunesse', query: 'jeunesse young adult' },
  { id: 'genre_polar', label: 'Polar', query: 'polar mystery detective' },
  { id: 'genre_fantasy', label: 'Fantasy', query: 'fantasy fantastique' },
  { id: 'genre_sf', label: 'Science-fiction', query: 'science fiction SF' },
  { id: 'genre_thriller', label: 'Thriller', query: 'thriller suspense' },
  { id: 'genre_romance', label: 'Romance', query: 'romance amour' },
  { id: 'genre_classiques', label: 'Classiques', query: 'classiques littérature classique' },
  { id: 'genre_historique', label: 'Histororique', query: 'roman historique historical fiction' },
];

const TAB_SECTION_FILTER = {
  pour_toi: null, // toutes les sources
  aime: ['algorithm_similarity', 'algorithm_similarity_gb', 'algorithm_category'],
  lisez: ['algorithm_author', 'algorithm_series'],
};

function filterSectionsBySources(grouped, sources) {
  if (!sources) return grouped || {};
  const out = {};
  sources.forEach((src) => {
    if (grouped?.[src]?.length) out[src] = grouped[src];
  });
  return out;
}

async function fetchGenreBooks(genreTab, token) {
  const q = genreTab.query || genreTab.label;
  const res = await fetch(
    `${API_BASE_URL}/api/openlibrary/search?q=${encodeURIComponent(q)}&limit=24`,
    { headers: token ? { Authorization: `Bearer ${token}` } : {} }
  );
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  const books = Array.isArray(data) ? data : data.books || data.results || [];
  return books.map((b) => ({
    ...b,
    book_id: b.ol_key || b.id,
    reason: `Sélection ${genreTab.label}`,
    source: 'algorithm_genre',
    _genreLabel: genreTab.label,
    category: b.category || 'roman',
  }));
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
    title: () => 'Similaires à tes coups de cœur · Open Library',
  },
  algorithm_similarity_gb: {
    icon: SparklesIcon,
    color: 'indigo',
    title: () => 'Similaires à tes coups de cœur · Google Books',
  },
  seed_similarity: {
    icon: SparklesIcon,
    color: 'purple',
    title: (items) => {
      const seed = items[0]?.metadata?.seed_title || items[0]?._seedLabel;
      return seed ? `Open Library · proches de « ${seed} »` : 'Open Library · similaires';
    },
  },
  seed_similarity_gb: {
    icon: SparklesIcon,
    color: 'indigo',
    title: (items) => {
      const seed = items[0]?.metadata?.seed_title || items[0]?._seedLabel;
      return seed ? `Google Books · proches de « ${seed} »` : 'Google Books · similaires';
    },
  },
  algorithm_category: {
    icon: SparklesIcon,
    color: 'indigo',
    title: () => 'Dans ton genre préféré',
  },
  algorithm_genre: {
    icon: SparklesIcon,
    color: 'indigo',
    title: (items) =>
      items[0]?._genreLabel
        ? `Romans · ${items[0]._genreLabel}`
        : 'Par genre',
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
          {book.display_title || book.title_fr || book.title}
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
  const [searchParams, setSearchParams] = useSearchParams();
  const [sections, setSections] = useState({});
  const [userProfile, setUserProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const initialTab = searchParams.get('tab') === 'similaires' ? 'similaires' : 'pour_toi';
  const [activeTab, setActiveTab] = useState(initialTab);
  const [userBooks, setUserBooks] = useState([]);
  const [userSeries, setUserSeries] = useState([]);
  const [seed, setSeed] = useState(() => {
    const title = searchParams.get('title') || '';
    const author = searchParams.get('author') || '';
    const series = searchParams.get('series') || '';
    if (title || series) {
      return {
        kind: series ? 'series' : 'book',
        title: series || title,
        author,
        series: series || '',
        label: series || title,
      };
    }
    return null;
  });
  const [seedFilter, setSeedFilter] = useState('');

  // Charge la liste des livres / séries pour détecter "déjà dans bibliothèque" + picker
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) return;
    const headers = { Authorization: `Bearer ${token}` };
    fetch(`${API_BASE_URL}/api/books/all?limit=1000`, { headers })
      .then((r) => r.json())
      .then((data) => setUserBooks(Array.isArray(data) ? data : data.books || data.items || []))
      .catch(() => {});
    fetch(`${API_BASE_URL}/api/series/library`, { headers })
      .then((r) => (r.ok ? r.json() : []))
      .then((data) => {
        const list = Array.isArray(data) ? data : data.series || data.items || [];
        setUserSeries(list);
      })
      .catch(() => {});
  }, []);

  const seedOptions = useMemo(() => {
    const books = (userBooks || [])
      .filter((b) => !b.isSeriesCard)
      .map((b) => {
        const title = displayBookTitleFrFirst(b) || b.title || '';
        return {
          id: `b:${b.id}`,
          kind: 'book',
          title,
          author: b.author || '',
          series: '',
          label: title,
          sub: b.author || '',
        };
      })
      .filter((o) => o.title);
    const series = (userSeries || []).map((s) => {
      const name = s.series_name || s.name || s.title || '';
      return {
        id: `s:${s.id || name}`,
        kind: 'series',
        title: name,
        author: s.author || '',
        series: name,
        label: name,
        sub: s.author ? `Série · ${s.author}` : 'Série',
      };
    }).filter((o) => o.title);
    // Cartes série de la grille biblio (si présentes dans books)
    const seriesCards = (userBooks || [])
      .filter((b) => b.isSeriesCard)
      .map((b) => {
        const name = b.name || b.title || '';
        return {
          id: `sc:${b.id || name}`,
          kind: 'series',
          title: name,
          author: b.author || '',
          series: name,
          label: name,
          sub: b.author ? `Série · ${b.author}` : 'Série',
        };
      })
      .filter((o) => o.title);
    const seen = new Set();
    return [...series, ...seriesCards, ...books].filter((o) => {
      const k = `${o.kind}:${o.label.toLowerCase()}`;
      if (seen.has(k)) return false;
      seen.add(k);
      return true;
    });
  }, [userBooks, userSeries]);

  const filteredSeedOptions = useMemo(() => {
    const q = seedFilter.trim().toLowerCase();
    if (!q) return seedOptions.slice(0, 40);
    return seedOptions
      .filter(
        (o) =>
          o.label.toLowerCase().includes(q) ||
          (o.sub || '').toLowerCase().includes(q)
      )
      .slice(0, 40);
  }, [seedOptions, seedFilter]);

  const loadPersonalizedBundle = useCallback(async ({ force = false } = {}) => {
    if (!force) {
      const cached = readCache('pour_toi');
      // Ne réutiliser un cache que s'il contient vraiment des suggestions
      const hasItems = cached?.sections && Object.values(cached.sections).some((a) => a?.length);
      if (hasItems) {
        if (cached.userProfile) setUserProfile(cached.userProfile);
        return cached.sections;
      }
    }

    const [personalizedRes, popularRes, profileRes] = await Promise.allSettled([
      recommendationService.getPersonalized({ limit: 36, refresh: force }),
      recommendationService.getPopular({ limit: 12 }),
      recommendationService.getUserProfile(),
    ]);

    const grouped = {};

    if (personalizedRes.status === 'fulfilled' && personalizedRes.value?.success) {
      const recs = personalizedRes.value.data?.recommendations || [];
      recs.forEach((r) => {
        const src = r.source || 'algorithm_category';
        if (!grouped[src]) grouped[src] = [];
        grouped[src].push({
          ...r,
          reason: r.reason || (Array.isArray(r.reasons) ? r.reasons[0] : undefined),
          score: r.score ?? r.confidence_score,
        });
      });
      // Profil parfois renvoyé avec les recos
      const inlineProfile = personalizedRes.value.data?.user_profile;
      if (inlineProfile?.has_books) {
        setUserProfile(inlineProfile);
      }
    } else if (personalizedRes.status === 'rejected') {
      console.error('Recos personnalisées en échec:', personalizedRes.reason);
    }

    if (popularRes.status === 'fulfilled' && popularRes.value?.success) {
      const pops = popularRes.value.data?.recommendations || [];
      if (pops.length > 0) grouped.popular = pops;
    }

    let profile = null;
    if (profileRes.status === 'fulfilled' && profileRes.value?.success) {
      profile = profileRes.value.data;
      setUserProfile(profile);
    }

    const hasItems = Object.values(grouped).some((a) => a?.length);
    if (hasItems) {
      writeCache('pour_toi', grouped, profile);
    }
    return grouped;
  }, []);

  const loadSimilarForSeed = useCallback(async (seedItem) => {
    if (!seedItem?.title && !seedItem?.series) {
      setSections({});
      return;
    }
    setIsLoading(true);
    try {
      const res = await recommendationService.getSimilar({
        title: seedItem.kind === 'series' ? '' : seedItem.title,
        author: seedItem.author || '',
        series: seedItem.kind === 'series' ? seedItem.series || seedItem.title : '',
        limit: 24,
      });
      const grouped = {};
      (res?.data?.recommendations || []).forEach((r) => {
        const src = r.source || 'seed_similarity';
        if (!grouped[src]) grouped[src] = [];
        grouped[src].push({
          ...r,
          reason: r.reason || (Array.isArray(r.reasons) ? r.reasons[0] : undefined),
          score: r.score ?? r.confidence_score,
          _seedLabel: seedItem.label || seedItem.title,
        });
      });
      setSections(grouped);
    } catch (err) {
      console.error('Erreur similaires:', err);
      toast.error('Impossible de charger les similaires');
      setSections({});
    } finally {
      setIsLoading(false);
    }
  }, []);

  const loadRecommendations = useCallback(async (tab, { force = false } = {}) => {
    if (tab === 'similaires') {
      if (seed) {
        await loadSimilarForSeed(seed);
      } else {
        setSections({});
        setIsLoading(false);
      }
      return;
    }

    if (!force) {
      const cached = readCache(tab);
      const hasItems = cached?.sections && Object.values(cached.sections).some((a) => a?.length);
      if (hasItems) {
        setSections(cached.sections || {});
        if (cached.userProfile) setUserProfile(cached.userProfile);
        setIsLoading(false);
        return;
      }
    }

    setIsLoading(true);
    try {
      const genreTab = GENRE_TABS.find((t) => t.id === tab);

      if (genreTab) {
        const token = localStorage.getItem('token');
        const books = await fetchGenreBooks(genreTab, token);
        const grouped = books.length ? { algorithm_genre: books } : {};
        setSections(grouped);
        if (books.length) writeCache(tab, grouped, null);
        return;
      }

      const bundle = await loadPersonalizedBundle({ force });
      const sources = TAB_SECTION_FILTER[tab];
      const grouped = filterSectionsBySources(bundle, sources);
      // « Pour toi » garde aussi les tendances ; les autres onglets perso non
      if (tab === 'pour_toi' && bundle.popular?.length && !grouped.popular) {
        grouped.popular = bundle.popular;
      }
      setSections(grouped);
      if (Object.values(grouped).some((a) => a?.length)) {
        writeCache(tab, grouped, null);
      }
    } catch (err) {
      console.error('Erreur chargement recommandations:', err);
      toast.error('Erreur lors du chargement');
    } finally {
      setIsLoading(false);
    }
  }, [loadPersonalizedBundle, loadSimilarForSeed, seed]);

  useEffect(() => {
    loadRecommendations(activeTab);
  }, [activeTab, loadRecommendations]);

  const selectSeed = useCallback(
    (option) => {
      const next = {
        kind: option.kind,
        title: option.title,
        author: option.author || '',
        series: option.series || '',
        label: option.label,
      };
      setSeed(next);
      setActiveTab('similaires');
      const params = new URLSearchParams({ tab: 'similaires' });
      if (next.kind === 'series') params.set('series', next.series || next.title);
      else {
        params.set('title', next.title);
        if (next.author) params.set('author', next.author);
      }
      setSearchParams(params, { replace: true });
      setSeedFilter('');
    },
    [setSearchParams]
  );

  const clearSeed = useCallback(() => {
    setSeed(null);
    setSections({});
    setSearchParams({ tab: 'similaires' }, { replace: true });
  }, [setSearchParams]);

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

  const totalRecs = Object.values(sections).reduce((s, arr) => s + (arr?.length || 0), 0);

  // Cold start : catalogue populaire si aucune reco perso
  const [coldStartBooks, setColdStartBooks] = useState([]);
  useEffect(() => {
    if (
      !isLoading &&
      totalRecs === 0 &&
      !String(activeTab).startsWith('genre_') &&
      activeTab !== 'similaires'
    ) {
      fetch(`${API_BASE_URL}/api/catalog/popular?limit=18`)
        .then((r) => (r.ok ? r.json() : { books: [] }))
        .then((d) => setColdStartBooks(d.books || []))
        .catch(() => {});
    }
  }, [isLoading, totalRecs, activeTab]);

  const ORDER =
    activeTab === 'similaires'
      ? ['seed_similarity', 'seed_similarity_gb']
      : activeTab === 'aime'
        ? ['algorithm_similarity', 'algorithm_similarity_gb', 'algorithm_category', 'popular']
        : activeTab === 'lisez'
          ? ['algorithm_author', 'algorithm_series', 'popular']
          : [
              'algorithm_series',
              'algorithm_author',
              'algorithm_similarity',
              'algorithm_similarity_gb',
              'algorithm_category',
              'algorithm_genre',
              'popular',
            ];

  return (
    <div className="min-h-screen bg-honeycomb">
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pb-[calc(5rem+env(safe-area-inset-bottom))] md:pb-8">
      {/* Bouton retour */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/')}
          className="inline-flex items-center space-x-2 px-4 py-2 bg-booktime-600 hover:bg-booktime-700 text-white rounded-lg transition-colors duration-200"
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

      {/* Onglets principaux */}
      <div className="flex gap-2 mb-3 flex-wrap">
        {PRIMARY_TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => {
              setActiveTab(t.id);
              if (t.id === 'similaires') {
                const params = new URLSearchParams({ tab: 'similaires' });
                if (seed?.kind === 'series') params.set('series', seed.series || seed.title);
                else if (seed?.title) {
                  params.set('title', seed.title);
                  if (seed.author) params.set('author', seed.author);
                }
                setSearchParams(params, { replace: true });
              } else {
                setSearchParams({}, { replace: true });
              }
            }}
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

      {/* Genres littéraires */}
      {activeTab !== 'similaires' && (
      <div className="flex gap-2 mb-8 flex-wrap">
        {GENRE_TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
              activeTab === t.id
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>
      )}

      {/* Sélecteur « similaires à un livre / série » */}
      {activeTab === 'similaires' && (
        <div className="mb-8 rounded-xl border border-purple-200 dark:border-purple-800 bg-white/80 dark:bg-gray-800/80 p-4">
          <p className="text-sm font-medium text-gray-800 dark:text-gray-100 mb-2">
            Choisis un livre ou une série de ta bibliothèque
          </p>
          {seed ? (
            <div className="flex flex-wrap items-center gap-2 mb-3">
              <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-sm bg-purple-100 dark:bg-purple-900/40 text-purple-800 dark:text-purple-200">
                {seed.kind === 'series' ? 'Série' : 'Livre'} · {seed.label}
                <button
                  type="button"
                  onClick={clearSeed}
                  className="ml-1 rounded-full p-0.5 hover:bg-purple-200/80 dark:hover:bg-purple-800"
                  aria-label="Changer de référence"
                >
                  <XMarkIcon className="h-4 w-4" />
                </button>
              </span>
            </div>
          ) : null}
          <input
            type="search"
            value={seedFilter}
            onChange={(e) => setSeedFilter(e.target.value)}
            placeholder="Rechercher dans ta bibliothèque…"
            className="w-full mb-3 px-3 py-2 text-sm rounded-lg border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
          />
          <div className="max-h-48 overflow-y-auto divide-y divide-gray-100 dark:divide-gray-700 rounded-lg border border-gray-100 dark:border-gray-700">
            {filteredSeedOptions.length === 0 ? (
              <p className="p-3 text-sm text-gray-500">
                Aucun titre trouvé. Ajoute des livres à ta bibliothèque pour commencer.
              </p>
            ) : (
              filteredSeedOptions.map((opt) => (
                <button
                  key={opt.id}
                  type="button"
                  onClick={() => selectSeed(opt)}
                  className={`w-full text-left px-3 py-2.5 text-sm hover:bg-purple-50 dark:hover:bg-purple-900/20 transition-colors ${
                    seed?.label === opt.label && seed?.kind === opt.kind
                      ? 'bg-purple-50 dark:bg-purple-900/30'
                      : ''
                  }`}
                >
                  <span className="font-medium text-gray-900 dark:text-white">{opt.label}</span>
                  {opt.sub ? (
                    <span className="block text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                      {opt.sub}
                    </span>
                  ) : null}
                </button>
              ))
            )}
          </div>
        </div>
      )}

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
              {activeTab === 'similaires'
                ? seed
                  ? 'Aucune proposition similaire trouvée'
                  : 'Choisis un livre ou une série ci-dessus'
                : 'Pas encore de recommandations personnalisées'}
            </h2>
            <p className="text-gray-500 dark:text-gray-400 text-sm max-w-sm mx-auto">
              {activeTab === 'similaires'
                ? seed
                  ? 'Essaie un autre titre, ou rafraîchis dans un instant.'
                  : 'On te proposera des lectures proches de ton choix.'
                : 'Ajoute des livres à ta bibliothèque pour recevoir des suggestions adaptées à tes goûts.'}
            </p>
          </div>
          {activeTab !== 'similaires' && coldStartBooks.length > 0 && (
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
    </div>
  );
};

export default RecommendationPage;
