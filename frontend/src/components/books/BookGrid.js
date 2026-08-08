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
  'grid grid-cols-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-7 gap-2 sm:gap-5 p-2 sm:p-6';

// Nombre de cartes animées à l'apparition. Au-delà, les cartes sont hors écran :
// les animer coûtait du temps de rendu pour un effet invisible.
const ANIMATED_CARDS = 12;

// Rendu progressif : taille du premier lot, puis de chaque extension
const INITIAL_VISIBLE = 30;
const VISIBLE_STEP = 30;

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
