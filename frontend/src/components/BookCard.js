import React from 'react';
import { StarIcon } from '@heroicons/react/24/solid';
import { StarIcon as StarOutlineIcon } from '@heroicons/react/24/outline';
import LanguageIndicator from './LanguageIndicator';

const BookCard = ({ book, onBookClick }) => {
  const getStatusColor = (status) => {
    switch (status) {
      case 'reading':
        return 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300';
      case 'completed':
        return 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300';
      default:
        return 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300';
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'reading':
        return 'En cours';
      case 'completed':
        return 'Terminé';
      default:
        return 'À lire';
    }
  };

  const getProgressPercentage = () => {
    if (!book.total_pages || book.total_pages === 0) return 0;
    return Math.min(100, (book.current_page / book.total_pages) * 100);
  };

  return (
    <div
      onClick={() => onBookClick(book)}
      className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 hover:shadow-md dark:hover:shadow-gray-900/20 transition-all cursor-pointer overflow-hidden group"
    >
      {/* Image de couverture */}
      <div className="aspect-[2/3] bg-gray-100 dark:bg-gray-700 overflow-hidden relative">
        {book.cover_url ? (
          <img
            src={book.cover_url}
            alt={book.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800">
            <div className="text-center p-4">
              <div className="text-4xl mb-2">
                {book.category === 'roman' && '📚'}
                {book.category === 'bd' && '🎨'}
                {book.category === 'manga' && '🇯🇵'}
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Pas de couverture</p>
            </div>
          </div>
        )}
        
        {/* Indicateur de langue */}
        <div className="absolute top-2 right-2">
          <LanguageIndicator book={book} size="xs" />
        </div>

        {/* Barre de progression pour les livres en cours */}
        {book.status === 'reading' && book.total_pages && (
          <div className="absolute bottom-0 left-0 right-0 h-1 bg-black/20">
            <div
              className="h-full bg-blue-500 transition-all duration-300"
              style={{ width: `${getProgressPercentage()}%` }}
            />
          </div>
        )}
      </div>

      {/* Contenu */}
      <div className="p-4">
        <div className="flex items-start justify-between mb-2">
          <h3 className="font-semibold text-gray-900 dark:text-white text-sm leading-tight line-clamp-2 flex-1">
            {book.title}
          </h3>
        </div>

        <p className="text-xs text-gray-600 dark:text-gray-400 mb-3 line-clamp-1">
          {book.author}
        </p>

        {/* Statut et note */}
        <div className="flex items-center justify-between">
          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(book.status)}`}>
            {getStatusLabel(book.status)}
          </span>

          {/* Note */}
          {book.rating > 0 && (
            <div className="flex items-center space-x-1">
              <div className="flex">
                {[1, 2, 3, 4, 5].map((star) => (
                  <div key={star} className="w-3 h-3">
                    {star <= book.rating ? (
                      <StarIcon className="w-3 h-3 text-yellow-400" />
                    ) : (
                      <StarOutlineIcon className="w-3 h-3 text-gray-300 dark:text-gray-600" />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Informations supplémentaires */}
        <div className="mt-3 pt-3 border-t border-gray-100 dark:border-gray-700">
          <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
            {book.saga && (
              <span className="truncate">📖 {book.saga}</span>
            )}
            {book.total_pages && (
              <span>{book.total_pages} pages</span>
            )}
          </div>
          
          {/* Progression pour les livres en cours */}
          {book.status === 'reading' && book.total_pages && (
            <div className="mt-2">
              <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
                <span>{book.current_page} / {book.total_pages}</span>
                <span>{Math.round(getProgressPercentage())}%</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BookCard;