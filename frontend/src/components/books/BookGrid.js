import React from 'react';
import BookActions from './BookActions';

const BookGrid = ({ 
  books, 
  loading, 
  onBookClick, 
  onItemClick,
  onAuthorClick,
  showEmptyState = true 
}) => {
  const applySeriesBookMasking = (booksList) => {
    if (!booksList || !Array.isArray(booksList)) return [];
    
    const unifiedDisplay = BookActions.createUnifiedDisplay(booksList, (book) => {
      if (book.category) {
        switch (book.category.toLowerCase()) {
          case 'roman':
            return { key: 'roman', text: 'Roman', class: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300', emoji: '📚' };
          case 'bd':
            return { key: 'bd', text: 'BD', class: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300', emoji: '🎨' };
          case 'manga':
            return { key: 'manga', text: 'Manga', class: 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-300', emoji: '🇯🇵' };
          default:
            return { key: 'roman', text: 'Roman', class: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300', emoji: '📚' };
        }
      }
      return { key: 'roman', text: 'Roman', class: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300', emoji: '📚' };
    });
    
    return unifiedDisplay.filter(item => {
      if (item.isSeriesCard) return true;
      const belongsToSeries = !!(item.saga && item.saga.trim());
      if (belongsToSeries) return false;
      return true;
    });
  };
  
  const displayedBooks = applySeriesBookMasking(books);

  if (loading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-3 sm:gap-6 p-3 sm:p-6">
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
    <div className="grid grid-cols-2 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-3 sm:gap-6 p-3 sm:p-6">
      {displayedBooks.map((item, index) => (
        <div
          key={item.id}
          className={`
            ${item.isSeriesCard ? 'col-span-2 sm:col-span-2' : 'col-span-1'} 
            group cursor-pointer transform transition-all duration-200 hover:scale-105 hover:shadow-lg
            book-card-stagger
          `}
          style={{ animationDelay: `${Math.min(index * 40, 400)}ms` }}
          onClick={() => onItemClick ? onItemClick(item) : onBookClick(item)}
        >
          {item.isSeriesCard ? (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden border border-gray-200 dark:border-gray-700">
              <div className="aspect-[2/1] bg-gray-100 dark:bg-gray-700 flex items-center justify-center relative overflow-hidden">
                {item.cover_url ? (
                  <>
                    <img 
                      src={item.cover_url} 
                      alt={item.name}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.nextSibling.style.display = 'flex';
                      }}
                    />
                    <div className="w-full h-full bg-gradient-to-r from-blue-500 to-purple-600 items-center justify-center hidden">
                      <div className="text-white text-center">
                        <div className="text-4xl mb-2">📚</div>
                        <div className="text-sm font-medium">Série</div>
                      </div>
                    </div>
                    <div className="absolute top-2 left-2 bg-black bg-opacity-70 text-white text-xs font-medium px-2 py-1 rounded">
                      📚 Série
                    </div>
                  </>
                ) : (
                  <div className="w-full h-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center">
                    <div className="text-white text-center">
                      <div className="text-4xl mb-2">📚</div>
                      <div className="text-sm font-medium">Série</div>
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
              <div className="p-4">
                <h3 className="font-semibold text-gray-900 dark:text-white line-clamp-2 mb-2">
                  {item.name}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      if (onAuthorClick) onAuthorClick(item.author);
                    }}
                    className="text-sm text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors underline"
                  >
                    {item.author}
                  </button>
                </p>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {item.completedBooks}/{item.totalBooks} tomes
                  </span>
                  <div className="w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                    <div 
                      key={`${item.id}-${item.completedBooks}`}
                      className="bg-green-500 h-2 rounded-full series-progress-spring"
                      style={{ width: `${item.progressPercent}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden border border-gray-200 dark:border-gray-700 relative">
              <div className="aspect-[3/4] bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                {item.cover_url ? (
                  <img 
                    src={item.cover_url} 
                    alt={item.title}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="text-gray-400 text-4xl">📖</div>
                )}
              </div>

              {/* Barre de progression lecture pour livres "En cours" */}
              {item.status === 'reading' && item.total_pages > 0 && item.current_page > 0 && (
                <div className="absolute bottom-0 left-0 right-0 h-1 bg-gray-200 dark:bg-gray-700">
                  <div
                    className="h-1 bg-blue-500 reading-progress-bar"
                    style={{ width: `${Math.min(100, Math.round(((item.current_page || 0) / item.total_pages) * 100))}%` }}
                    title={`${item.current_page || 0} / ${item.total_pages} pages (${Math.round(((item.current_page || 0) / item.total_pages) * 100)}%)`}
                  />
                </div>
              )}

              <div className="p-3">
                <h3 className="font-semibold text-gray-900 dark:text-white text-sm line-clamp-2 mb-1">
                  {item.title}
                </h3>
                <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      if (onAuthorClick) onAuthorClick(item.author);
                    }}
                    className="text-sm text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors underline"
                  >
                    {item.author}
                  </button>
                </p>
                <div className="flex items-center justify-between">
                  <span className={`
                    px-2 py-1 rounded-full text-xs font-medium
                    ${item.status === 'completed' ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300' : ''}
                    ${item.status === 'reading' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300 badge-reading-pulse' : ''}
                    ${item.status === 'to_read' ? 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-300' : ''}
                  `}>
                    {item.status === 'completed' ? 'Terminé' : 
                     item.status === 'reading' ? (
                       item.total_pages > 0
                         ? `${Math.round(((item.current_page || 0) / item.total_pages) * 100)}%`
                         : 'En cours'
                     ) : 'À lire'}
                  </span>
                  {item.category && (
                    <span className="text-xs">
                      {item.category === 'roman' ? '📚' : 
                       item.category === 'bd' ? '🎨' : 
                       item.category === 'manga' ? '🇯🇵' : '📚'}
                    </span>
                  )}
                </div>
                {/* Étoiles de notation */}
                {item.rating > 0 && (
                  <div className="flex items-center gap-0.5 mt-2">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <svg
                        key={i}
                        className={`h-3 w-3 ${i < Math.round(item.rating) ? 'text-yellow-400' : 'text-gray-200 dark:text-gray-600'}`}
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                    ))}
                    <span className="text-xs text-gray-400 dark:text-gray-500 ml-1">{item.rating}/5</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default BookGrid;
