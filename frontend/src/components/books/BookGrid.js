import React from 'react';
import { resolveCoverForGridItem } from '../../utils/helpers';
import { displayBookTitleFrFirst } from '../../utils/openLibraryBookDisplay';

const GRID_CLASSES =
  'grid grid-cols-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-7 gap-2 sm:gap-5 p-2 sm:p-6';

// Nombre de cartes animées à l'apparition. Au-delà, les cartes sont hors écran :
// les animer coûtait du temps de rendu pour un effet invisible.
const ANIMATED_CARDS = 12;

// Rendu progressif : taille du premier lot, puis de chaque extension
const INITIAL_VISIBLE = 30;
const VISIBLE_STEP = 30;

const CARD_SHELL =
  'h-full bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden border border-gray-200 dark:border-gray-700 relative';

const SeriesCardBody = ({ item, coverSrc, categoryEmoji }) => {
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
      <div className="aspect-[3/4] bg-gray-100 dark:bg-gray-700 flex items-center justify-center relative overflow-hidden">
        {coverSrc ? (
          <>
            <img
              src={coverSrc}
              alt={item.name}
              loading="lazy"
              decoding="async"
              className="h-full w-full object-cover"
              onError={(e) => {
                e.target.style.display = 'none';
                const fb = e.target.nextElementSibling;
                if (fb) fb.classList.remove('hidden');
              }}
            />
            <div className="hidden absolute inset-0 flex items-center justify-center text-2xl text-gray-400 sm:text-4xl">{categoryEmoji}</div>
          </>
        ) : (
          <div className="text-gray-400 text-2xl sm:text-4xl">{categoryEmoji}</div>
        )}

        {/* Badge identifiant "Série" — distinction claire avec un livre individuel */}
        <div className="absolute top-1 left-1 sm:top-2 sm:left-2">
          <span className="inline-flex items-center rounded bg-black/70 px-1 py-0.5 text-[9px] font-medium text-white sm:px-2 sm:py-1 sm:text-xs">
            📚 Série
          </span>
        </div>

        {/* Badge statut superposé — uniquement "terminé" (✓), même style que les livres */}
        {seriesStatus === 'completed' && (
          <div className="absolute top-1 right-1">
            <span className="hidden sm:inline-flex px-1.5 py-0.5 rounded text-[10px] font-medium bg-green-500 text-white">
              ✓
            </span>
            {/* Version mobile: point coloré */}
            <span className="sm:hidden w-2.5 h-2.5 rounded-full block border border-white bg-green-500" />
          </div>
        )}
      </div>

      {/* Barre de progression de la série — même endroit (bas de carte) et même couleur que les livres */}
      {item.progressPercent > 0 && (
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-200 dark:bg-gray-700">
          <div
            key={`${item.id}-${item.completedBooks}`}
            className="h-1 bg-blue-500 series-progress-spring"
            style={{ width: `${Math.min(100, item.progressPercent)}%` }}
          />
        </div>
      )}

      <div className="p-1.5 sm:p-3">
        <h3 className="font-medium text-gray-900 dark:text-white text-[11px] sm:text-sm line-clamp-2 leading-tight">
          {item.name}
        </h3>
        <p className="text-[10px] sm:text-xs text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-1">
          {item.author}
          {item.isStaticWikidataCard && (
            <span className="ml-1 text-indigo-500 dark:text-indigo-400">· Wikidata</span>
          )}
        </p>
        <div className="mt-1 text-[10px] sm:text-xs font-medium text-gray-600 dark:text-gray-400">
          {item.completedBooks}/{item.totalBooks} <span className="hidden sm:inline">tomes</span>
        </div>
      </div>
    </div>
  );
};

const BookCardBody = ({ item, coverSrc }) => {
  const title = displayBookTitleFrFirst(item);

  return (
    <div className={CARD_SHELL}>
      {/* Couverture (Open Library en secours si pas d’URL) */}
      <div className="aspect-[3/4] bg-gray-100 dark:bg-gray-700 flex items-center justify-center relative overflow-hidden">
        {coverSrc ? (
          <>
            <img
              src={coverSrc}
              alt={item.display_title || item.title}
              loading="lazy"
              decoding="async"
              className="h-full w-full object-cover"
              onError={(e) => {
                e.target.style.display = 'none';
                const fb = e.target.nextElementSibling;
                if (fb) fb.classList.remove('hidden');
              }}
            />
            <div className="hidden absolute inset-0 flex items-center justify-center text-2xl text-gray-400 sm:text-4xl">📖</div>
          </>
        ) : (
          <div className="text-gray-400 text-2xl sm:text-4xl">📖</div>
        )}
      </div>

      {/* Barre de progression */}
      {item.status === 'reading' && item.total_pages > 0 && item.current_page > 0 && (
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-200 dark:bg-gray-700">
          <div
            className="h-1 bg-blue-500 reading-progress-bar"
            style={{ width: `${Math.min(100, Math.round(((item.current_page || 0) / item.total_pages) * 100))}%` }}
          />
        </div>
      )}

      {/* Badge statut superposé — uniquement "terminé" (✓) */}
      {item.status === 'completed' && (
        <div className="absolute top-1 right-1">
          <span className="hidden sm:inline-flex px-1.5 py-0.5 rounded text-[10px] font-medium bg-green-500 text-white">
            ✓
          </span>
          {/* Version mobile: point coloré */}
          <span className="sm:hidden w-2.5 h-2.5 rounded-full block border border-white bg-green-500" />
        </div>
      )}

      <div className="p-1.5 sm:p-3">
        <h3 className="font-medium text-gray-900 dark:text-white text-[11px] sm:text-sm line-clamp-2 leading-tight">
          {title}
        </h3>
        {/* Titre original si différent du titre affiché */}
        {item.original_title && item.original_title !== title && (
          <p className="text-[9px] sm:text-[10px] text-gray-400 dark:text-gray-500 italic line-clamp-1 mt-0.5 leading-tight">
            {item.original_title}
          </p>
        )}
        <p className="text-[10px] sm:text-xs text-gray-500 dark:text-gray-400 line-clamp-1 mt-0.5">
          {item.author}
        </p>
        {/* Étoiles — desktop seulement */}
        {item.rating > 0 && (
          <div className="hidden sm:flex items-center gap-0.5 mt-1.5">
            {Array.from({ length: 5 }).map((_, i) => (
              <svg key={i} className={`h-2.5 w-2.5 ${i < Math.round(item.rating) ? 'text-yellow-400' : 'text-gray-200 dark:text-gray-600'}`} fill="currentColor" viewBox="0 0 20 20">
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
const GridCard = React.memo(({ item, index, onSelect }) => {
  const coverSrc = resolveCoverForGridItem(item);
  const categoryEmoji = item.category === 'bd' ? '🎨' : item.category === 'manga' ? '🇯🇵' : '📚';
  const animated = index < ANIMATED_CARDS;

  return (
    <div
      className={`col-span-1 group cursor-pointer transform transition-transform duration-200 sm:hover:scale-105 sm:hover:shadow-lg${
        animated ? ' book-card-stagger' : ''
      }`}
      style={animated ? { animationDelay: `${Math.min(index * 40, 400)}ms` } : undefined}
      onClick={() => onSelect(item)}
    >
      {item.isSeriesCard ? (
        <SeriesCardBody item={item} coverSrc={coverSrc} categoryEmoji={categoryEmoji} />
      ) : (
        <BookCardBody item={item} coverSrc={coverSrc} />
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
            <div className="bg-gray-200 dark:bg-gray-700 rounded-lg aspect-[3/4] mb-3"></div>
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
          <GridCard key={item.id} item={item} index={index} onSelect={handleSelect} />
        ))}
      </div>
      {hasMore && <div ref={sentinelRef} aria-hidden="true" className="h-px" />}
    </>
  );
};

export default React.memo(BookGrid);
