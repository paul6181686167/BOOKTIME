// Phase 2.3 - Composant BookCard optimisé avec React.memo et useMemo
import React, { memo, useMemo } from 'react';
import { getCategoryBadge } from '../../utils/helpers';

/**
 * Composant BookCard optimisé avec memoization
 * Évite les re-rendus inutiles quand les props ne changent pas
 */
const MemoizedBookCard = memo(({
  book,
  onItemClick,
  showBadges = true,
  className = ""
}) => {
  // Memoization des calculs coûteux
  const categoryBadge = useMemo(() => {
    return getCategoryBadge(book);
  }, [book.category]);

  const progressPercentage = useMemo(() => {
    if (!book.total_pages || !book.current_page) return 0;
    return Math.round((book.current_page / book.total_pages) * 100);
  }, [book.total_pages, book.current_page]);

  const statusColor = useMemo(() => {
    switch (book.status) {
      case 'completed':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'reading':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'to_read':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  }, [book.status]);

  const statusText = useMemo(() => {
    switch (book.status) {
      case 'completed':
        return 'Terminé';
      case 'reading':
        return 'En cours';
      case 'to_read':
        return 'À lire';
      default:
        return 'Inconnu';
    }
  }, [book.status]);

  // Fonction de clic optimisée
  const handleClick = useMemo(() => {
    return () => onItemClick(book);
  }, [book, onItemClick]);

  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:shadow-md transition-shadow duration-200 cursor-pointer group ${className}`}
      onClick={handleClick}
    >
      {/* Image de couverture */}
      <div className="aspect-[3/4] rounded-t-lg overflow-hidden bg-gray-100 dark:bg-gray-700">
        {book.cover_url ? (
          <img
            src={book.cover_url}
            alt={book.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            <svg className="w-12 h-12" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clipRule="evenodd" />
            </svg>
          </div>
        )}
      </div>

      {/* Informations du livre */}
      <div className="p-4">
        {/* Titre */}
        <h3 className="font-medium text-gray-900 dark:text-white text-sm mb-1 line-clamp-2">
          {book.title}
        </h3>

        {/* Auteur */}
        <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
          {book.author}
        </p>

        {/* Badges */}
        {showBadges && (
          <div className="flex flex-wrap gap-1 mb-3">
            {/* Badge catégorie */}
            <span className={`px-2 py-1 text-xs font-medium rounded-full ${categoryBadge.className}`}>
              {categoryBadge.emoji} {categoryBadge.label}
            </span>

            {/* Badge statut */}
            <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusColor}`}>
              {statusText}
            </span>
          </div>
        )}

        {/* Progression pour les livres en cours */}
        {book.status === 'reading' && book.total_pages && book.current_page && (
          <div className="mt-2">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs text-gray-600 dark:text-gray-400">
                Progression
              </span>
              <span className="text-xs text-gray-600 dark:text-gray-400">
                {progressPercentage}%
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className="bg-green-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-500 mt-1">
              {book.current_page} / {book.total_pages} pages
            </p>
          </div>
        )}

        {/* Note si le livre est terminé */}
        {book.status === 'completed' && book.rating && (
          <div className="mt-2 flex items-center gap-1">
            <span className="text-xs text-gray-600 dark:text-gray-400">Note:</span>
            <div className="flex">
              {[...Array(5)].map((_, i) => (
                <svg
                  key={i}
                  className={`w-3 h-3 ${
                    i < book.rating ? 'text-yellow-400' : 'text-gray-300 dark:text-gray-600'
                  }`}
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
});

// Fonction de comparaison personnalisée pour React.memo
MemoizedBookCard.displayName = 'MemoizedBookCard';

export default MemoizedBookCard;

// Hook pour optimiser la liste de livres
export const useOptimizedBookList = (books = []) => {
  return useMemo(() => {
    // Trier les livres par date d'ajout (plus récent en premier)
    return [...books].sort((a, b) => {
      const dateA = new Date(a.date_added || a.updated_at);
      const dateB = new Date(b.date_added || b.updated_at);
      return dateB - dateA;
    });
  }, [books]);
};