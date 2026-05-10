import React from 'react';
import { resolveCoverForGridItem } from '../../utils/helpers';

const BookGrid = ({ 
  books, 
  loading, 
  onBookClick, 
  onItemClick,
  onAuthorClick,
  showEmptyState = true 
}) => {
  // Les livres reçus sont déjà traités par App.js (createUnifiedDisplay + filtrage)
  // On n'applique qu'un filtre minimal pour éviter les livres standalone avec saga
  const displayedBooks = React.useMemo(() => {
    if (!books || !Array.isArray(books)) return [];
    return books.filter(item => {
      if (item.isSeriesCard) return true;
      const belongsToSeries = !!(item.saga && item.saga.trim());
      return !belongsToSeries;
    });
  }, [books]);

  if (loading) {
    return (
      <div className="grid grid-cols-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-7 gap-2 sm:gap-5 p-2 sm:p-6">
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
          Aucun livre dans votre bibliothèque
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          Commencez par rechercher des livres à ajouter à votre collection.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-3 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 2xl:grid-cols-7 gap-2 sm:gap-5 p-2 sm:p-6">
      {displayedBooks.map((item, index) => {
        const coverSrc = resolveCoverForGridItem(item);
        return (
        <div
          key={item.id}
          className={`
            col-span-1
            group cursor-pointer transform transition-all duration-200 hover:scale-105 hover:shadow-lg
            book-card-stagger
          `}
          style={{ animationDelay: `${Math.min(index * 40, 400)}ms` }}
          onClick={() => onItemClick ? onItemClick(item) : onBookClick(item)}
        >
          {item.isSeriesCard ? (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden border border-gray-200 dark:border-gray-700 relative">
              <div className="aspect-[3/4] bg-gray-100 dark:bg-gray-700 flex items-center justify-center relative overflow-hidden">
                {coverSrc ? (
                  <>
                    <img 
                      src={coverSrc} 
                      alt={item.name}
                      className="h-full w-full object-cover"
                      onError={(e) => {
                        e.target.style.display = 'none';
                        const fb = e.target.nextElementSibling;
                        if (fb) fb.classList.remove('hidden');
                      }}
                    />
                    <div className="hidden h-full w-full items-center justify-center bg-gradient-to-r from-blue-500 to-purple-600">
                      <div className="text-center text-white">
                        <div className="text-2xl sm:text-4xl">📚</div>
                        <div className="text-[10px] font-medium sm:text-sm">Série</div>
                      </div>
                    </div>
                    <div className="absolute left-1 top-1 rounded bg-black/70 px-1 py-0.5 text-[9px] font-medium text-white sm:left-2 sm:top-2 sm:px-2 sm:py-1 sm:text-xs">
                      📚 Série
                    </div>
                  </>
                ) : (
                  <div className="flex h-full w-full items-center justify-center bg-gradient-to-r from-blue-500 to-purple-600">
                    <div className="text-center text-white">
                      <div className="text-2xl sm:text-4xl">📚</div>
                      <div className="text-[10px] font-medium sm:text-sm">Série</div>
                    </div>
                  </div>
                )}
                {item.category === 'manga' && (
                  <div className="absolute top-2 right-2 bg-red-500 text-white text-xs font-bold px-2 py-1 rounded-full">
                    Manga
                  </div>
                )}
                {item.category === 'bd' && (
                  <div className="absolute top-2 right-2 bg-yellow-500 text-white text-xs font-bold px-2 py-1 rounded-full">
                    BD
                  </div>
                )}
              </div>
              <div className="p-1.5 sm:p-3">
                <h3 className="font-medium text-gray-900 dark:text-white text-[11px] sm:text-sm line-clamp-2 leading-tight">
                  {item.name}
                </h3>
                <p className="text-[10px] sm:text-xs text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-1">
                  {item.author}
                </p>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-[10px] sm:text-xs font-medium text-gray-600 dark:text-gray-400">
                    {item.completedBooks}/{item.totalBooks} <span className="hidden sm:inline">tomes</span>
                  </span>
                  <div className="w-10 sm:w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-1 sm:h-2 overflow-hidden">
                    <div 
                      key={`${item.id}-${item.completedBooks}`}
                      className="bg-green-500 h-full rounded-full series-progress-spring"
                      style={{ width: `${item.progressPercent}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm overflow-hidden border border-gray-200 dark:border-gray-700 relative">
              {/* Couverture (Open Library en secours si pas d’URL) */}
              <div className="aspect-[3/4] bg-gray-100 dark:bg-gray-700 flex items-center justify-center relative">
                {coverSrc ? (
                  <>
                    <img 
                      src={coverSrc} 
                      alt={item.title}
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

              {/* Badge statut superposé sur mobile */}
              <div className="absolute top-1 right-1">
                <span className={`
                  hidden sm:inline-flex px-1.5 py-0.5 rounded text-[10px] font-medium
                  ${item.status === 'completed' ? 'bg-green-500 text-white' : ''}
                  ${item.status === 'reading' ? 'bg-blue-500 text-white' : ''}
                  ${item.status === 'to_read' ? 'bg-gray-400 text-white' : ''}
                `}>
                  {item.status === 'completed' ? '✓' : item.status === 'reading' ? '…' : ''}
                </span>
                {/* Version mobile: point coloré */}
                <span className={`
                  sm:hidden w-2.5 h-2.5 rounded-full block border border-white
                  ${item.status === 'completed' ? 'bg-green-500' : ''}
                  ${item.status === 'reading' ? 'bg-blue-500' : ''}
                  ${item.status === 'to_read' ? 'bg-gray-300' : ''}
                `} />
              </div>

              <div className="p-1.5 sm:p-3">
                <h3 className="font-medium text-gray-900 dark:text-white text-[11px] sm:text-sm line-clamp-2 leading-tight">
                  {item.title}
                </h3>
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
          )}
        </div>
        );
      })}
    </div>
  );
};

export default BookGrid;
