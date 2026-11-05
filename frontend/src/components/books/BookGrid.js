import React, { useEffect, useState } from 'react';
import { resolveCoverForGridItem } from '../../utils/helpers';
import { displayBookTitleFrFirst } from '../../utils/openLibraryBookDisplay';
import SmartCover, {
  CARD_SHELL,
  COVER_FRAME,
  CoverScrim,
  PILL,
} from './SmartCover';

const GRID_CLASSES =
  'grid grid-cols-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-7 gap-x-2.5 gap-y-4 sm:gap-5 p-1 sm:p-6';

// Nombre de cartes animées à l'apparition. Au-delà, les cartes sont hors écran :
// les animer coûtait du temps de rendu pour un effet invisible.
const ANIMATED_CARDS = 12;

// Rendu progressif : taille du premier lot, puis de chaque extension
const INITIAL_VISIBLE = 30;
const VISIBLE_STEP = 30;

/** Fraction + barre style streaming sous la couverture */
const CinemaProgress = ({ current, total, percent }) => {
  const hasNumbers = Number.isFinite(current) && Number.isFinite(total) && total > 0;
  const pct = Math.min(
    100,
    Math.max(
      0,
      Number.isFinite(percent)
        ? percent
        : hasNumbers
          ? Math.round((current / total) * 100)
          : 0
    )
  );
  if (!hasNumbers && pct <= 0) return null;
  return (
    <div className="mt-1.5 space-y-1">
      {hasNumbers && (
        <p className="text-[10px] sm:text-xs font-medium tabular-nums tracking-wide text-gray-500 dark:text-white/55">
          {current}/{total}
        </p>
      )}
      <div className="cinema-progress-track">
        <div className="cinema-progress-fill" style={{ width: `${pct}%` }} />
      </div>
    </div>
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

  const done = item.completedBooks ?? 0;
  const total = item.totalBooks ?? 0;
  const pct =
    item.progressPercent > 0
      ? item.progressPercent
      : seriesStatus === 'completed' && total > 0
        ? 100
        : 0;

  return (
    <div className={CARD_SHELL}>
      <div className={COVER_FRAME}>
        <SmartCover
          item={item}
          alt={item.name}
          primarySrc={coverSrc}
          onCoverFound={onCoverFound}
          priority={priority}
        />
        <CoverScrim />

        <div className="absolute top-1.5 left-1.5">
          <span className={`inline-flex items-center rounded-md bg-black/65 px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wider text-white/90 ${PILL}`}>
            Série
          </span>
        </div>

        {seriesStatus === 'completed' && (
          <div className="absolute top-1.5 right-1.5">
            <span className={`inline-flex h-5 w-5 items-center justify-center rounded-full bg-[#f0d060]/90 text-[10px] font-bold text-black ${PILL}`}>
              ✓
            </span>
          </div>
        )}
      </div>

      <div className="pt-2 px-0.5">
        <h3 className="font-medium text-gray-900 dark:text-white text-[11px] sm:text-sm line-clamp-2 leading-snug tracking-tight">
          {item.name}
        </h3>
        <CinemaProgress current={done} total={total} percent={pct} />
      </div>
    </div>
  );
};

const BookCardBody = ({ item, coverSrc, onCoverFound, priority }) => {
  const title = displayBookTitleFrFirst(item);
  const current = item.current_page || 0;
  const total = item.total_pages || 0;
  const isReading = item.status === 'reading' && total > 0 && current > 0;
  const isDone = item.status === 'completed';
  const pct = isDone
    ? 100
    : isReading
      ? Math.round((current / total) * 100)
      : 0;

  return (
    <div className={CARD_SHELL}>
      <div className={COVER_FRAME}>
        <SmartCover
          item={item}
          alt={title}
          primarySrc={coverSrc}
          onCoverFound={onCoverFound}
          priority={priority}
        />
        <CoverScrim />

        {isDone && (
          <div className="absolute top-1.5 right-1.5">
            <span className={`inline-flex h-5 w-5 items-center justify-center rounded-full bg-[#f0d060]/90 text-[10px] font-bold text-black ${PILL}`}>
              ✓
            </span>
          </div>
        )}
        {item.status === 'to_reread' && (
          <div className="absolute top-1.5 right-1.5">
            <span className={`inline-flex h-5 w-5 items-center justify-center rounded-full bg-white/15 text-[10px] text-white ${PILL}`}>
              ↻
            </span>
          </div>
        )}
      </div>

      <div className="pt-2 px-0.5">
        <h3 className="font-medium text-gray-900 dark:text-white text-[11px] sm:text-sm line-clamp-2 leading-snug tracking-tight">
          {title}
        </h3>
        {(isReading || isDone) && total > 0 ? (
          <CinemaProgress
            current={isDone ? total : current}
            total={total}
            percent={pct}
          />
        ) : null}
      </div>
    </div>
  );
};

// Carte mémoïsée : sans cela, changer d'onglet ou de tri redessinait toutes les
// cartes de la bibliothèque, ce qui se sentait nettement sur mobile.
const GridCard = React.memo(({ item, index, onSelect, onCoverFound }) => {
  const coverSrc = resolveCoverForGridItem(item);
  const animated = index < ANIMATED_CARDS;
  // Premier écran + un peu sous la ligne de flottaison
  const priority = index < 15;

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
  const loadLockRef = React.useRef(false);

  // Clé stable : reset seulement si les IDs changent (pas à chaque cover_url)
  const listIdentity = React.useMemo(
    () => displayedBooks.map((b) => b?.id).join('|'),
    [displayedBooks]
  );

  React.useEffect(() => {
    setVisibleCount(INITIAL_VISIBLE);
    loadLockRef.current = false;
  }, [listIdentity]);

  const hasMore = displayedBooks.length > visibleCount;

  React.useEffect(() => {
    if (!hasMore) return undefined;
    const node = sentinelRef.current;
    if (!node || typeof IntersectionObserver === 'undefined') {
      setVisibleCount(displayedBooks.length);
      return undefined;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        if (!entries.some((entry) => entry.isIntersecting)) return;
        if (loadLockRef.current) return;
        loadLockRef.current = true;
        setVisibleCount((count) => count + VISIBLE_STEP);
        // Laisse le DOM se stabiliser avant un nouveau palier (évite le tressautement)
        window.setTimeout(() => {
          loadLockRef.current = false;
        }, 180);
      },
      { rootMargin: '240px 0px' }
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
            <div className="bg-white/[0.06] rounded-xl aspect-[2/3] mb-3 shadow-[inset_0_0_0_1px_rgba(255,255,255,0.28)]"></div>
            <div className="h-3 bg-white/[0.06] rounded mb-2"></div>
            <div className="h-2 bg-white/[0.04] rounded w-3/4"></div>
          </div>
        ))}
      </div>
    );
  }

  if (showEmptyState && displayedBooks.length === 0) {
    return (
      <div className="text-center py-12">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          {emptyTitle}
        </h3>
        <p className="text-gray-600 dark:text-white/40">
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
