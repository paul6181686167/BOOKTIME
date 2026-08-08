import React, { useEffect, useMemo, useState } from 'react';
import {
  coverFallbackCandidates,
  coverImgSrc,
  isBlankOrPlaceholderCover,
  isGoogleBooksCoverUrl,
  isUsableCoverUrl,
  normalizeCoverUrl,
  resolveCoverForGridItem,
} from '../../utils/helpers';
import { displayBookTitleFrFirst } from '../../utils/openLibraryBookDisplay';
import { resolveCoverForVisibleItem } from '../../services/libraryMetaEnrichment';

const GRID_CLASSES =
  'grid grid-cols-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-7 gap-2 sm:gap-5 p-2 sm:p-6';

// Nombre de cartes animées à l'apparition. Au-delà, les cartes sont hors écran :
// les animer coûtait du temps de rendu pour un effet invisible.
const ANIMATED_CARDS = 12;

// Rendu progressif : taille du premier lot, puis de chaque extension
const INITIAL_VISIBLE = 30;
const VISIBLE_STEP = 30;

// Couverture porte la carte : pas de bordure / ring. Sur mobile, pas d’ombre
// ni de fond « carte » (évite le cadre blanc) ; ombre discrète desktop seulement.
const CARD_SHELL =
  'h-full bg-transparent sm:bg-white sm:dark:bg-gray-800 rounded-xl overflow-hidden relative transition-shadow duration-200 sm:shadow-card sm:group-hover:shadow-card-hover';

const COVER_FRAME =
  'aspect-[2/3] rounded-xl sm:rounded-none bg-booktime-mist/35 dark:bg-gray-700 relative overflow-hidden';
const COVER_IMAGE =
  'h-full w-full object-cover transition-transform duration-300 sm:group-hover:scale-[1.04]';

// Pastille translucide — sans ring sur mobile (contour superflu)
const PILL = 'backdrop-blur-sm sm:ring-1 sm:ring-white/15';

// Teintes sourdes des vignettes de secours, tenables en clair comme en sombre
const PLACEHOLDER_TINTS = [
  'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-200',
  'bg-sky-100 text-sky-800 dark:bg-sky-900/40 dark:text-sky-200',
  'bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-200',
  'bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-200',
  'bg-violet-100 text-violet-800 dark:bg-violet-900/40 dark:text-violet-200',
  'bg-teal-100 text-teal-800 dark:bg-teal-900/40 dark:text-teal-200',
];

const INITIALS_SKIPPED = new Set(['le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'the', 'a', 'an', 'of', 'and', 'et']);

const initialsFor = (text) => {
  const words = (text || '')
    .replace(/[^\p{L}\p{N}\s]/gu, ' ')
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (!words.length) return '?';
  const kept = words.filter((word) => !INITIALS_SKIPPED.has(word.toLowerCase()));
  return (kept.length ? kept : words)
    .slice(0, 2)
    .map((word) => word[0].toUpperCase())
    .join('');
};

// Teinte stable d'un rendu à l'autre : dérivée du texte, pas tirée au hasard
const tintFor = (text) => {
  let hash = 0;
  for (let i = 0; i < (text || '').length; i += 1) {
    hash = (hash * 31 + text.charCodeAt(i)) % 9973;
  }
  return PLACEHOLDER_TINTS[hash % PLACEHOLDER_TINTS.length];
};

// Remplace les emojis de secours (📖, 📚, 🎨) par une initiale composée en serif
const CoverPlaceholder = ({ text, hidden = false }) => (
  <div
    className={`${hidden ? 'hidden ' : ''}absolute inset-0 flex items-center justify-center ${tintFor(text)}`}
  >
    <span className="font-display text-xl font-semibold tracking-tight sm:text-3xl">
      {initialsFor(text)}
    </span>
  </div>
);

// Voile bas de couverture : assoit les badges et la barre de progression
const CoverScrim = () => (
  <div className="pointer-events-none absolute inset-x-0 bottom-0 h-1/4 bg-gradient-to-t from-black/25 to-transparent" />
);

/** Image de couverture : ignore Google Books (souvent « image not available »). */
const SmartCover = ({ item, alt, primarySrc, onCoverFound, priority = false }) => {
  const candidates = useMemo(() => {
    const list = coverFallbackCandidates(item);
    if (primarySrc && !list.includes(primarySrc)) {
      if (isGoogleBooksCoverUrl(primarySrc)) list.push(primarySrc);
      else list.unshift(primarySrc);
    }
    // Ne jamais afficher une URL Google Books : placeholder trompeur
    return list.filter((u) => !isGoogleBooksCoverUrl(u));
  }, [item, primarySrc]);
  const [idx, setIdx] = useState(0);
  const [fetched, setFetched] = useState(null);
  const [searchTried, setSearchTried] = useState(false);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    setIdx(0);
    setFetched(null);
    setSearchTried(false);
    setSearching(false);
  }, [item?.id, primarySrc, candidates[0]]);

  const exhausted = !fetched && (candidates.length === 0 || idx >= candidates.length);

  useEffect(() => {
    if (!exhausted || fetched || searchTried) return;
    let cancelled = false;
    setSearchTried(true);
    setSearching(true);
    const safety = setTimeout(() => {
      if (!cancelled) setSearching(false);
    }, 28000);
    resolveCoverForVisibleItem(item)
      .then((url) => {
        if (cancelled || !url) return;
        // Google Books accepté seulement après validation visuelle (onLoad)
        const cover = isGoogleBooksCoverUrl(url)
          ? url
          : normalizeCoverUrl(url) || url;
        if (isUsableCoverUrl(cover) || isGoogleBooksCoverUrl(cover)) {
          setFetched(cover);
        }
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setSearching(false);
        clearTimeout(safety);
      });
    return () => {
      cancelled = true;
      clearTimeout(safety);
    };
  }, [item, exhausted, fetched, searchTried]);

  const src = fetched || (idx < candidates.length ? candidates[idx] : null);

  if (!src) {
    if (searching || (!searchTried && exhausted)) {
      return (
        <div className="absolute inset-0 bg-gray-200 dark:bg-gray-700 animate-pulse" />
      );
    }
    return <CoverPlaceholder text={alt} />;
  }

  const imgSrc = coverImgSrc(src);
  const needsPlaceholderCheck = isGoogleBooksCoverUrl(src);

  const failCurrent = () => {
    if (fetched) {
      setFetched(null);
      setSearchTried(false);
      return;
    }
    setIdx((i) => i + 1);
  };

  return (
    <img
      src={imgSrc}
      alt={alt}
      loading={priority ? 'eager' : 'lazy'}
      fetchPriority={priority ? 'high' : 'auto'}
      decoding={priority ? 'sync' : 'async'}
      // CORS seulement si on lit les pixels (placeholder GB) — sinon +lent
      crossOrigin={needsPlaceholderCheck ? 'anonymous' : undefined}
      referrerPolicy="no-referrer"
      className={COVER_IMAGE}
      onLoad={(e) => {
        if (needsPlaceholderCheck && isBlankOrPlaceholderCover(e.currentTarget)) {
          failCurrent();
          return;
        }
        if (fetched && typeof onCoverFound === 'function') {
          onCoverFound(item, fetched);
        }
      }}
      onError={failCurrent}
    />
  );
};

const SeriesCardBody = ({ item, coverSrc, onCoverFound, priority }) => {
  // Statut série : priorité au statut manuel, sinon progression des tomes
  const seriesStatus =
    item.status ||
    item.series_status ||
    (item.progressPercent >= 100
      ? 'completed'
      : item.progressPercent > 0
        ? 'reading'
        : 'to_read');

  return (
    <div className={CARD_SHELL}>
      {/* Couverture (même squelette que les livres individuels) */}
      <div className={COVER_FRAME}>
        <SmartCover
          item={item}
          alt={item.name}
          primarySrc={coverSrc}
          onCoverFound={onCoverFound}
          priority={priority}
        />
        <CoverScrim />

        {/* Badge identifiant "Série" — distinction claire avec un livre individuel */}
        <div className="absolute top-1 left-1 sm:top-2 sm:left-2">
          <span className={`inline-flex items-center rounded-md bg-black/50 px-1.5 py-0.5 text-micro font-medium text-white sm:px-2 sm:py-1 sm:text-xs ${PILL}`}>
            Série
          </span>
        </div>

        {/* Badge statut superposé — uniquement "terminé" (✓), même style que les livres */}
        {seriesStatus === 'completed' && (
          <div className="absolute top-1 right-1 sm:top-2 sm:right-2">
            <span className={`hidden sm:inline-flex px-1.5 py-0.5 rounded-md text-mini font-semibold bg-booktime-600/90 text-white ${PILL}`}>
              ✓
            </span>
            {/* Version mobile: point coloré, sans anneau */}
            <span className="sm:hidden w-2.5 h-2.5 rounded-full block bg-booktime-500" />
          </div>
        )}
      </div>

      {/* Barre de progression de la série — même endroit (bas de carte) et même couleur que les livres */}
      {item.progressPercent > 0 && (
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-black/10 dark:bg-white/10 sm:bg-gray-200 sm:dark:bg-gray-700">
          <div
            key={`${item.id}-${item.completedBooks}`}
            className="h-1 bg-blue-500 series-progress-spring"
            style={{ width: `${Math.min(100, item.progressPercent)}%` }}
          />
        </div>
      )}

      <div className="pt-1.5 px-0.5 sm:p-3">
        <h3 className="font-medium text-gray-900 dark:text-white text-tiny sm:text-sm line-clamp-2 leading-tight">
          {item.name}
        </h3>
        <p className="text-mini sm:text-xs text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-1">
          {item.author}
          {item.isStaticWikidataCard && (
            <span className="ml-1 text-indigo-500 dark:text-indigo-400">· Wikidata</span>
          )}
        </p>
        <div className="mt-1 text-mini sm:text-xs font-medium text-gray-600 dark:text-gray-400">
          {item.completedBooks}/{item.totalBooks} <span className="hidden sm:inline">tomes</span>
        </div>
      </div>
    </div>
  );
};

const BookCardBody = ({ item, coverSrc, onCoverFound, priority }) => {
  const title = displayBookTitleFrFirst(item);

  return (
    <div className={CARD_SHELL}>
      {/* Couverture (Open Library en secours si pas d’URL) */}
      <div className={COVER_FRAME}>
        <SmartCover
          item={item}
          alt={title}
          primarySrc={coverSrc}
          onCoverFound={onCoverFound}
          priority={priority}
        />
        <CoverScrim />
      </div>

      {/* Barre de progression */}
      {item.status === 'reading' && item.total_pages > 0 && item.current_page > 0 && (
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-black/10 dark:bg-white/10 sm:bg-gray-200 sm:dark:bg-gray-700">
          <div
            className="h-1 bg-blue-500 reading-progress-bar"
            style={{ width: `${Math.min(100, Math.round(((item.current_page || 0) / item.total_pages) * 100))}%` }}
          />
        </div>
      )}

      {/* Badge statut superposé — uniquement "terminé" (✓) */}
      {item.status === 'completed' && (
        <div className="absolute top-1 right-1 sm:top-2 sm:right-2">
          <span className={`hidden sm:inline-flex px-1.5 py-0.5 rounded-md text-mini font-semibold bg-booktime-600/90 text-white ${PILL}`}>
            ✓
          </span>
          {/* Version mobile: point coloré, sans anneau */}
          <span className="sm:hidden w-2.5 h-2.5 rounded-full block bg-booktime-500" />
        </div>
      )}

      <div className="pt-1.5 px-0.5 sm:p-3">
        <h3 className="font-medium text-gray-900 dark:text-white text-tiny sm:text-sm line-clamp-2 leading-tight">
          {title}
        </h3>
        {/* Titre original si différent du titre affiché */}
        {item.original_title && item.original_title !== title && (
          <p className="text-micro sm:text-mini text-gray-400 dark:text-gray-500 italic line-clamp-1 mt-0.5 leading-tight">
            {item.original_title}
          </p>
        )}
        <p className="text-mini sm:text-xs text-gray-500 dark:text-gray-400 line-clamp-1 mt-0.5">
          {item.author}
        </p>
        {/* Étoiles — desktop seulement */}
        {item.rating > 0 && (
          <div className="hidden sm:flex items-center gap-0.5 mt-1.5">
            {Array.from({ length: 5 }).map((_, i) => (
              <svg key={i} className={`h-2.5 w-2.5 ${i < Math.round(item.rating) ? 'text-amber-400' : 'text-gray-200 dark:text-gray-600'}`} fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Carte mémoïsée : sans cela, changer d'onglet ou de tri redessinait toutes les
// cartes de la bibliothèque, ce qui se sentait nettement sur mobile.
const GridCard = React.memo(({ item, index, onSelect, onCoverFound }) => {
  const coverSrc = resolveCoverForGridItem(item);
  const animated = index < ANIMATED_CARDS;
  // Premier écran mobile (3×3) : chargement prioritaire, pas de lazy
  const priority = index < 9;

  return (
    <div
      className={`col-span-1 group cursor-pointer transform transition-transform duration-200 sm:hover:-translate-y-1${
        animated ? ' book-card-stagger' : ''
      }`}
      style={animated ? { animationDelay: `${Math.min(index * 40, 400)}ms` } : undefined}
      onClick={() => onSelect(item)}
    >
      {item.isSeriesCard ? (
        <SeriesCardBody item={item} coverSrc={coverSrc} onCoverFound={onCoverFound} priority={priority} />
      ) : (
        <BookCardBody item={item} coverSrc={coverSrc} onCoverFound={onCoverFound} priority={priority} />
      )}
    </div>
  );
});
GridCard.displayName = 'GridCard';

const BookGrid = ({
  books,
  loading,
  onBookClick,
  onItemClick,
  onAuthorClick,
  onCoverFound,
  showEmptyState = true,
  emptyTitle = 'Aucun livre dans votre bibliothèque',
  emptySubtitle = 'Commencez par rechercher des livres à ajouter à votre collection.',
}) => {
  // Filtre soft : n'exclure un livre « saga » que si une carte série du même nom
  // est déjà présente (évite de vider la grille quand OL tague saga sans carte).
  const displayedBooks = React.useMemo(() => {
    if (!books || !Array.isArray(books)) return [];
    const seriesNames = new Set(
      books
        .filter((item) => item.isSeriesCard)
        .map((item) => (item.name || item.title || '').toLowerCase().trim())
        .filter(Boolean)
    );
    return books.filter((item) => {
      if (item.isSeriesCard) return true;
      const saga = (item.saga || '').trim().toLowerCase();
      if (!saga) return true;
      // Garder le livre s'il n'y a pas déjà une carte série pour cette saga
      return !seriesNames.has(saga);
    });
  }, [books]);

  const handleSelect = React.useCallback(
    (item) => (onItemClick ? onItemClick(item) : onBookClick(item)),
    [onItemClick, onBookClick]
  );

  // Rendu progressif : on ne monte qu'un premier lot de cartes, étendu à
  // l'approche du bas de liste. Une bibliothèque de plusieurs centaines de titres
  // produisait sinon des milliers de nœuds DOM dès l'affichage.
  const [visibleCount, setVisibleCount] = React.useState(INITIAL_VISIBLE);
  const sentinelRef = React.useRef(null);

  // Nouvelle liste (onglet, tri, recherche) : on repart du premier lot
  React.useEffect(() => {
    setVisibleCount(INITIAL_VISIBLE);
  }, [displayedBooks]);

  const hasMore = displayedBooks.length > visibleCount;

  React.useEffect(() => {
    if (!hasMore) return undefined;
    const node = sentinelRef.current;
    if (!node || typeof IntersectionObserver === 'undefined') {
      // Sans IntersectionObserver, on renonce au découpage plutôt qu'à l'affichage
      setVisibleCount(displayedBooks.length);
      return undefined;
    }
    // L'observateur est recréé à chaque palier : une sentinelle restée visible
    // ne déclencherait pas de nouvelle notification.
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setVisibleCount((count) => count + VISIBLE_STEP);
        }
      },
      // Marge d'anticipation : le lot suivant arrive avant d'atteindre le bas
      { rootMargin: '600px 0px' }
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [hasMore, visibleCount, displayedBooks.length]);

  const visibleBooks = React.useMemo(
    () => (displayedBooks.length > visibleCount ? displayedBooks.slice(0, visibleCount) : displayedBooks),
    [displayedBooks, visibleCount]
  );

  if (loading) {
    return (
      <div className={GRID_CLASSES}>
        {Array.from({ length: 12 }).map((_, index) => (
          <div key={index} className="animate-pulse">
            <div className="bg-gray-200 dark:bg-gray-700 rounded-xl aspect-[2/3] mb-3"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
          </div>
        ))}
      </div>
    );
  }

  if (showEmptyState && displayedBooks.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">📚</div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          {emptyTitle}
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          {emptySubtitle}
        </p>
      </div>
    );
  }

  return (
    <>
      <div className={GRID_CLASSES}>
        {visibleBooks.map((item, index) => (
          <GridCard
            key={item.id}
            item={item}
            index={index}
            onSelect={handleSelect}
            onCoverFound={onCoverFound}
          />
        ))}
      </div>
      {hasMore && <div ref={sentinelRef} aria-hidden="true" className="h-px" />}
    </>
  );
};

export default React.memo(BookGrid);
