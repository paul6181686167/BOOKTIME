/**
 * Page de Recommandations — sections contextuelles, filtre par onglet actif
 */
import React, {
  useState,
  useEffect,
  useCallback,
  useMemo,
  useRef,
} from 'react';
import { createPortal } from 'react-dom';
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
} from '@heroicons/react/24/outline';
import { recommendationService } from '../../services/recommendationService';
import { addSeriesToLibrary } from '../../services/seriesLibraryService';
import { API_BASE_URL } from '../../config/environment';
import { displayBookTitleFrFirst } from '../../utils/openLibraryBookDisplay';
import { resolveCoverForGridItem } from '../../utils/helpers';
import {
  groupRecosAsBooktimeItems,
  recoToBooktimeBook,
  isRecoAlreadyOwned,
} from '../../utils/recommendationBooktime';
import { attributeBookToSeries } from '../../utils/seriesAttribution';
import SmartCover, {
  CARD_SHELL,
  COVER_FRAME,
  CoverScrim,
  PILL,
} from '../books/SmartCover';
import BookDetailModal from '../BookDetailModal';
import SeriesDetailModal from '../SeriesDetailModal';

// ── Cache (sessionStorage) ────────────────────────────────────────────────
// Évite de recalculer les recommandations à chaque visite de la page.
const CACHE_PREFIX = 'booktime_reco_cache_v7_';
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

function toBooktimeSections(grouped, seedLabel = '') {
  const out = {};
  Object.entries(grouped || {}).forEach(([src, items]) => {
    const list = items || [];
    // Déjà regroupé en cartes série Booktime
    if (list.some((i) => i?.isSeriesCard)) {
      out[src] = list;
      return;
    }
    out[src] = groupRecosAsBooktimeItems(list, { seedLabel });
  });
  return out;
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
  seed_similar: {
    icon: SparklesIcon,
    color: 'purple',
    title: (items) => {
      const seed =
        items[0]?._seedLabel ||
        items[0]?.metadata?.seed_title ||
        items[0]?.seed_title;
      return seed ? `Proches de « ${seed} »` : 'Livres et séries similaires';
    },
  },
  seed_similarity: {
    icon: SparklesIcon,
    color: 'purple',
    title: (items) => {
      const seed = items[0]?.metadata?.seed_title || items[0]?._seedLabel;
      return seed ? `Proches de « ${seed} »` : 'Livres similaires';
    },
  },
  seed_similarity_gb: {
    icon: SparklesIcon,
    color: 'indigo',
    title: (items) => {
      const seed = items[0]?.metadata?.seed_title || items[0]?._seedLabel;
      return seed ? `Proches de « ${seed} »` : 'Livres similaires';
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

// ── Carte Booktime = même squelette que la bibliothèque (SmartCover) ─────

const BookCard = ({
  book,
  onOpen,
  onAdd,
  onNotInterested,
  userBooks = [],
  userSeries = [],
  priority = false,
}) => {
  const [adding, setAdding] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [localCover, setLocalCover] = useState(book.cover_url || null);

  const isSeries = !!book.isSeriesCard;
  const title = isSeries
    ? book.name || book.display_title || book.title
    : displayBookTitleFrFirst(book) || book.display_title || book.title;
  const coverItem = localCover ? { ...book, cover_url: localCover } : book;
  const coverSrc = resolveCoverForGridItem(coverItem);

  const alreadyIn = isRecoAlreadyOwned(book, userBooks, userSeries);

  if (dismissed) return null;

  const handleAdd = async (e) => {
    e?.stopPropagation?.();
    if (alreadyIn || adding) return;
    setAdding(true);
    try {
      await onAdd(book);
      toast.success(
        isSeries
          ? `« ${title} » ajoutée à ta bibliothèque`
          : `« ${title} » ajouté à ta bibliothèque`
      );
    } catch {
      toast.error("Erreur lors de l'ajout");
    } finally {
      setAdding(false);
    }
  };

  const handleDismiss = async (e) => {
    e?.stopPropagation?.();
    setDismissed(true);
    try {
      await onNotInterested(book.book_id || book.ol_key);
    } catch {
      // ignore
    }
  };

  const upcoming = !isSeries && isUpcoming(book);

  const openDetails = (e) => {
    // Ne pas ouvrir si le clic vient d'un bouton (+ / X)
    if (e?.target?.closest?.('button')) return;
    onOpen?.(book);
  };

  return (
    <div
      className="col-span-1 group cursor-pointer transform transition-transform duration-200 sm:hover:-translate-y-1"
      onClick={openDetails}
    >
      <div className={CARD_SHELL}>
        <div className={COVER_FRAME}>
          <SmartCover
            item={coverItem}
            alt={title}
            primarySrc={coverSrc || localCover}
            priority={priority}
            onCoverFound={(_, url) => {
              if (url) setLocalCover(url);
            }}
          />
          <CoverScrim />

          {isSeries && (
            <div className="absolute top-1 left-1 sm:top-2 sm:left-2 pointer-events-none">
              <span
                className={`inline-flex items-center rounded-md bg-black/50 px-1.5 py-0.5 text-micro font-medium text-white sm:px-2 sm:py-1 sm:text-xs ${PILL}`}
              >
                Série
                {book.totalBooks || book.books?.length
                  ? ` · ${book.totalBooks || book.books.length}`
                  : ''}
              </span>
            </div>
          )}
          {upcoming && (
            <div className="absolute top-1 left-1 sm:top-2 sm:left-2 pointer-events-none">
              <span
                className={`inline-flex items-center gap-1 rounded-md bg-amber-500/90 px-1.5 py-0.5 text-micro font-medium text-white sm:text-xs ${PILL}`}
              >
                <ClockIcon className="h-3 w-3" />
                À paraître
              </span>
            </div>
          )}

          <button
            type="button"
            onClick={handleDismiss}
            className="absolute top-1 right-1 sm:top-2 sm:right-2 z-10 p-1 rounded-full bg-black/40 hover:bg-red-600/90 text-white transition-colors"
            title="Pas intéressé"
          >
            <XMarkIcon className="h-3.5 w-3.5" />
          </button>

          {!alreadyIn && (
            <button
              type="button"
              onClick={handleAdd}
              disabled={adding}
              className={`absolute bottom-1.5 right-1.5 sm:bottom-2 sm:right-2 z-10 inline-flex items-center justify-center rounded-full bg-booktime-600 hover:bg-booktime-700 text-white shadow-md h-8 w-8 sm:h-9 sm:w-9 transition-colors disabled:opacity-60 ${PILL}`}
              title={isSeries ? 'Ajouter la série' : 'Ajouter'}
            >
              {adding ? (
                <span
                  className="btn-spinner"
                  style={{ width: '0.75rem', height: '0.75rem', borderWidth: '1.5px' }}
                />
              ) : (
                <PlusIcon className="h-4 w-4" />
              )}
            </button>
          )}
          {alreadyIn && (
            <div className="absolute bottom-1.5 right-1.5 sm:bottom-2 sm:right-2 z-10 pointer-events-none">
              <span
                className={`inline-flex items-center justify-center rounded-full bg-booktime-600/90 text-white h-8 w-8 sm:h-9 sm:w-9 ${PILL}`}
                title="Dans ta bibliothèque"
              >
                <CheckIcon className="h-4 w-4" />
              </span>
            </div>
          )}
        </div>

        <div className="pt-1.5 px-0.5 sm:p-3">
          <h3 className="font-medium text-gray-900 dark:text-white text-tiny sm:text-sm line-clamp-2 leading-tight">
            {title}
          </h3>
          {book.original_title &&
            book.original_title !== title &&
            !isSeries && (
              <p className="text-micro sm:text-mini text-gray-400 dark:text-gray-500 italic line-clamp-1 mt-0.5 leading-tight">
                {book.original_title}
              </p>
            )}
          <p className="text-mini sm:text-xs text-gray-500 dark:text-gray-400 line-clamp-1 mt-0.5">
            {book.author}
          </p>
        </div>
      </div>
    </div>
  );
};

// ── Section ───────────────────────────────────────────────────────────────

const RecommendationSection = ({
  source,
  items,
  onOpen,
  onAdd,
  onNotInterested,
  userBooks,
  userSeries,
}) => {
  const cfg = SECTION_CONFIG[source] || SECTION_CONFIG.popular;
  const colors = COLOR_CLASSES[cfg.color];
  const Icon = cfg.icon;

  const visible = items.filter(
    (b) => !isRecoAlreadyOwned(b, userBooks, userSeries)
  );

  if (visible.length === 0) return null;

  const seriesCount = visible.filter((b) => b.isSeriesCard).length;
  const bookCount = visible.length - seriesCount;
  const countLabel =
    seriesCount > 0 && bookCount > 0
      ? `${seriesCount} série${seriesCount > 1 ? 's' : ''} · ${bookCount} livre${bookCount > 1 ? 's' : ''}`
      : seriesCount > 0
        ? `${seriesCount} série${seriesCount > 1 ? 's' : ''}`
        : `${bookCount} suggestion${bookCount > 1 ? 's' : ''}`;

  return (
    <div className="mb-10">
      <div className={`flex items-center gap-2 mb-4 pb-2 border-b ${colors.border}`}>
        <Icon className={`h-5 w-5 ${colors.icon}`} />
        <h2 className="text-base font-semibold text-gray-800 dark:text-gray-100">
          {cfg.title(items)}
        </h2>
        <span className={`ml-auto text-xs font-medium px-2 py-0.5 rounded-full ${colors.badge}`}>
          {countLabel}
        </span>
      </div>

      <div className="grid grid-cols-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-7 gap-2 sm:gap-5">
        {visible.slice(0, 24).map((book, idx) => (
          <BookCard
            key={book.id || book.book_id || book.ol_key || `${source}-${idx}`}
            book={book}
            onOpen={onOpen}
            onAdd={onAdd}
            onNotInterested={onNotInterested}
            userBooks={userBooks}
            userSeries={userSeries}
            priority={idx < 12}
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

  // Enrichir l'auteur du seed (URL / série sans auteur) dès que la biblio est chargée
  useEffect(() => {
    if (!seed || seed.author || !userBooks?.length) return;
    const n = (seed.series || seed.title || '').trim().toLowerCase();
    if (!n) return;
    const match = userBooks.find((b) => {
      if (b.isSeriesCard || !b.author) return false;
      const saga = (b.saga_name || b.series_name || '').trim().toLowerCase();
      const title = (b.title || '').trim().toLowerCase();
      return saga === n || title === n;
    });
    if (match?.author) {
      setSeed((prev) => (prev && !prev.author ? { ...prev, author: match.author } : prev));
    }
  }, [seed, userBooks]);

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
    const authorForSeries = (name) => {
      const n = (name || '').trim().toLowerCase();
      if (!n) return '';
      const fromSeries = (userSeries || []).find(
        (s) => (s.series_name || s.name || s.title || '').trim().toLowerCase() === n && s.author
      );
      if (fromSeries?.author) return fromSeries.author;
      const fromBook = (userBooks || []).find((b) => {
        if (b.isSeriesCard) return false;
        const saga = (b.saga_name || b.series_name || '').trim().toLowerCase();
        const title = (b.title || '').trim().toLowerCase();
        return b.author && (saga === n || title === n);
      });
      return fromBook?.author || '';
    };
    const series = (userSeries || []).map((s) => {
      const name = s.series_name || s.name || s.title || '';
      const author = s.author || authorForSeries(name);
      return {
        id: `s:${s.id || name}`,
        kind: 'series',
        title: name,
        author,
        series: name,
        label: name,
        sub: author ? `Série · ${author}` : 'Série',
      };
    }).filter((o) => o.title);
    // Cartes série de la grille biblio (si présentes dans books)
    const seriesCards = (userBooks || [])
      .filter((b) => b.isSeriesCard)
      .map((b) => {
        const name = b.name || b.title || '';
        const author = b.author || authorForSeries(name);
        return {
          id: `sc:${b.id || name}`,
          kind: 'series',
          title: name,
          author,
          series: name,
          label: name,
          sub: author ? `Série · ${author}` : 'Série',
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

  const similarReqId = useRef(0);
  const loadSimilarForSeed = useCallback(async (seedItem) => {
    if (!seedItem?.title && !seedItem?.series) {
      setSections({});
      return;
    }
    const reqId = ++similarReqId.current;
    setIsLoading(true);
    try {
      const isSeries = seedItem.kind === 'series';
      const seedTitle = isSeries
        ? seedItem.series || seedItem.title || ''
        : seedItem.title || '';
      const res = await recommendationService.getSimilar({
        // Toujours envoyer le titre seed (série ou livre) pour les moteurs OL/GB
        title: seedTitle,
        author: seedItem.author || '',
        series: isSeries ? seedTitle : '',
        limit: 24,
      });
      if (reqId !== similarReqId.current) return;
      const list =
        res?.data?.recommendations ||
        res?.recommendations ||
        (Array.isArray(res?.data) ? res.data : []) ||
        [];
      const seedLabel = seedItem.label || seedItem.title || seedItem.series || '';
      // Une seule grille Booktime : fusion OL + Google Books (plus de bandeaux séparés)
      const unified = list.map((r) => ({
        ...r,
        score: r.score ?? r.confidence_score,
        _seedLabel: seedLabel,
        // Ne pas afficher « · Open Library » sur les vignettes
        reason: undefined,
      }));
      const finalItems = groupRecosAsBooktimeItems(unified, { seedLabel }).sort(
        (a, b) => Number(!!b.cover_url) - Number(!!a.cover_url)
      );
      setSections({
        seed_similar: finalItems.map((b) => ({ ...b, _seedLabel: seedLabel })),
      });
    } catch (err) {
      if (reqId !== similarReqId.current) return;
      console.error('Erreur similaires:', err);
      toast.error('Impossible de charger les similaires');
      setSections({});
    } finally {
      if (reqId === similarReqId.current) setIsLoading(false);
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
        setSections(toBooktimeSections(cached.sections || {}));
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
        const grouped = toBooktimeSections(
          books.length ? { algorithm_genre: books } : {}
        );
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
      const booktime = toBooktimeSections(grouped);
      setSections(booktime);
      if (Object.values(booktime).some((a) => a?.length)) {
        writeCache(tab, booktime, null);
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

  const [selectedBook, setSelectedBook] = useState(null);
  const [showBookModal, setShowBookModal] = useState(false);
  const [selectedSeries, setSelectedSeries] = useState(null);
  const [showSeriesModal, setShowSeriesModal] = useState(false);

  const handleOpenItem = useCallback((item) => {
    if (!item) return;

    const openSeriesModal = (seriesLike) => {
      setSelectedBook(null);
      setShowBookModal(false);
      setSelectedSeries({
        ...seriesLike,
        isSeriesCard: true,
        name: seriesLike.name || seriesLike.title || seriesLike.display_title || '',
        series_name:
          seriesLike.series_name ||
          seriesLike.name ||
          seriesLike.title ||
          seriesLike.display_title ||
          '',
        author: seriesLike.author || '',
        cover_url: seriesLike.cover_url || null,
        books: Array.isArray(seriesLike.books) ? seriesLike.books : [],
        totalBooks:
          seriesLike.totalBooks ||
          seriesLike.total_books ||
          seriesLike.books?.length ||
          0,
        status: seriesLike.status || 'to_read',
      });
      setShowSeriesModal(true);
    };

    if (item.isSeriesCard) {
      openSeriesModal(item);
      return;
    }

    const book = recoToBooktimeBook(item) || item;
    // Livre qui est en réalité une série curée (ex. Dog Man) → fiche série
    const attr = attributeBookToSeries(book);
    const curatedMulti =
      attr?.seriesData &&
      ((Number(attr.seriesData.volumes) || 0) > 1 ||
        Object.keys(attr.seriesData.volume_titles || {}).length > 1);
    if (curatedMulti) {
      openSeriesModal({
        ...book,
        name: attr.seriesName,
        title: attr.seriesName,
        display_title: attr.seriesName,
        author: book.author || attr.seriesData.authors?.[0] || '',
        category: attr.seriesData.category || book.category || 'roman',
        cover_url: book.cover_url || null,
        books: [book],
        totalBooks: attr.seriesData.volumes || 0,
        description: attr.seriesData.description || book.description || '',
      });
      return;
    }

    const fromGb =
      book.isFromGoogleBooks ||
      String(book.ol_key || book.book_id || '').startsWith('gbooks_');
    setSelectedSeries(null);
    setShowSeriesModal(false);
    setSelectedBook({
      ...book,
      status: book.status || 'to_read',
      isFromOpenLibrary: !fromGb,
      isFromGoogleBooks: fromGb,
      display_title: displayBookTitleFrFirst(book) || book.title,
      description: book.description || book.metadata?.description || '',
      subjects: Array.isArray(book.subjects)
        ? book.subjects.map((s) => (typeof s === 'string' ? s : s?.name || String(s))).filter(Boolean)
        : [],
    });
    setShowBookModal(true);
  }, []);

  const handleAdd = async (book) => {
    if (book?.isSeriesCard) {
      const token = localStorage.getItem('token');
      await addSeriesToLibrary(
        {
          series_name: book.name || book.title,
          name: book.name || book.title,
          author: book.author || '',
          category: book.category || 'roman',
          cover_url: book.cover_url,
          books: book.books || [],
          total_books: book.totalBooks || book.books?.length || 0,
        },
        token
      );
      setUserSeries((prev) => [...prev, book]);
      clearRecoCache();
      return;
    }
    const normalized = recoToBooktimeBook(book) || book;
    await recommendationService.addRecommendedBook({
      ...normalized,
      book_id: normalized.ol_key || normalized.book_id,
      title: normalized.display_title || normalized.title,
    });
    setUserBooks((prev) => [...prev, normalized]);
    clearRecoCache();
  };

  const handleAddFromOpenLibrary = async (book) => {
    await handleAdd(book);
    setShowBookModal(false);
    setSelectedBook(null);
  };

  const handleNotInterested = async (bookId) => {
    if (bookId) await recommendationService.markAsNotInterested(bookId);
    clearRecoCache();
  };

  const handleFeedback = async (bookId, type) => {
    if (!bookId) return;
    await recommendationService.submitFeedback(bookId, type);
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
      ? ['seed_similar', 'seed_similarity', 'seed_similarity_gb']
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
    <>
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
          <div className="max-h-48 overflow-y-auto scrollbar-hide divide-y divide-gray-100 dark:divide-gray-700 rounded-lg border border-gray-100 dark:border-gray-700">
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
              <div className="grid grid-cols-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-7 gap-2 sm:gap-5">
                {groupRecosAsBooktimeItems(
                  coldStartBooks.map((b) => ({ ...b, book_id: b.ol_key }))
                )
                  .filter((book) => !isRecoAlreadyOwned(book, userBooks, userSeries))
                  .map((book, idx) => (
                  <BookCard
                    key={book.id || book.ol_key || idx}
                    book={book}
                    onOpen={handleOpenItem}
                    onAdd={handleAdd}
                    onNotInterested={handleNotInterested}
                    userBooks={userBooks}
                    userSeries={userSeries}
                    priority={idx < 12}
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
                onOpen={handleOpenItem}
                onAdd={handleAdd}
                onNotInterested={handleNotInterested}
                userBooks={userBooks}
                userSeries={userSeries}
              />
            ) : null
          )}
          {Object.keys(sections)
            .filter((s) => !ORDER.includes(s))
            .map((src) => (
              <RecommendationSection
                key={src}
                source={src}
                items={sections[src]}
                onOpen={handleOpenItem}
                onAdd={handleAdd}
                onNotInterested={handleNotInterested}
                userBooks={userBooks}
                userSeries={userSeries}
              />
            ))}
        </div>
      )}
    </div>
    </div>

      {typeof document !== 'undefined' &&
        createPortal(
          <>
            {showBookModal && selectedBook && (
              <BookDetailModal
                book={selectedBook}
                isOpen={showBookModal}
                onClose={() => {
                  setShowBookModal(false);
                  setSelectedBook(null);
                }}
                onUpdate={async () => {}}
                onDelete={async () => {
                  setShowBookModal(false);
                  setSelectedBook(null);
                }}
                onAddFromOpenLibrary={handleAddFromOpenLibrary}
              />
            )}
            {showSeriesModal && selectedSeries && (
              <SeriesDetailModal
                series={selectedSeries}
                isOpen={showSeriesModal}
                onClose={() => {
                  setShowSeriesModal(false);
                  setSelectedSeries(null);
                }}
                onUpdate={() => {}}
                onDelete={() => {
                  setShowSeriesModal(false);
                  setSelectedSeries(null);
                }}
                onAddSeries={async (series) => {
                  await handleAdd({ ...series, isSeriesCard: true });
                  setShowSeriesModal(false);
                  setSelectedSeries(null);
                  toast.success('Série ajoutée à ta bibliothèque');
                }}
                userSeriesLibrary={userSeries || []}
              />
            )}
          </>,
          document.body
        )}
    </>
  );
};

export default RecommendationPage;
