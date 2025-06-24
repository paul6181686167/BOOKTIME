import React from 'react';
import { StarIcon } from '@heroicons/react/24/solid';
import { StarIcon as StarOutlineIcon } from '@heroicons/react/24/outline';

const BookCard = ({ book, onClick }) => {
  const getStatusBadge = (status) => {
    const badges = {
      to_read: { label: 'À lire', class: 'status-to-read' },
      reading: { label: 'En cours', class: 'status-reading' },
      completed: { label: 'Terminé', class: 'status-completed' },
    };
    return badges[status] || badges.to_read;
  };

  const getCategoryColor = (category) => {
    const colors = {
      roman: 'category-roman',
      bd: 'category-bd',
      manga: 'category-manga',
    };
    return colors[category] || 'category-roman';
  };

  const getProgressPercentage = () => {
    if (!book.total_pages || book.total_pages === 0) return 0;
    return Math.min(100, (book.current_page / book.total_pages) * 100);
  };

  const statusBadge = getStatusBadge(book.status);
  const categoryColor = getCategoryColor(book.category);
  const progressPercentage = getProgressPercentage();

  return (
    <div 
      onClick={onClick}
      className={`book-card bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden cursor-pointer hover:shadow-lg transition-all duration-300 ${categoryColor}`}
    >
      {/* Image de couverture */}
      <div className="aspect-[2/3] bg-gray-100 relative overflow-hidden">
        {book.cover_url ? (
          <img 
            src={book.cover_url} 
            alt={book.title}
            className="w-full h-full object-cover book-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200">
            <div className="text-center p-4">
              <div className="text-4xl mb-2">
                {book.category === 'roman' && '📚'}
                {book.category === 'bd' && '🎨'}
                {book.category === 'manga' && '🇯🇵'}
              </div>
              <p className="text-xs text-gray-500 font-medium">Pas de couverture</p>
            </div>
          </div>
        )}
        
        {/* Badge de statut */}
        <div className="absolute top-2 right-2">
          <span className={`status-badge ${statusBadge.class}`}>
            {statusBadge.label}
          </span>
        </div>
      </div>

      {/* Informations du livre */}
      <div className="p-4">
        <h3 className="font-semibold text-gray-900 text-sm mb-1 line-clamp-2 leading-tight">
          {book.title}
        </h3>
        <p className="text-gray-600 text-xs mb-3 line-clamp-1">
          {book.author}
        </p>

        {/* Note */}
        {book.rating && (
          <div className="flex items-center mb-3">
            <div className="flex space-x-1">
              {[1, 2, 3, 4, 5].map((star) => (
                star <= book.rating ? (
                  <StarIcon key={star} className="h-4 w-4 text-yellow-400" />
                ) : (
                  <StarOutlineIcon key={star} className="h-4 w-4 text-gray-300" />
                )
              ))}
            </div>
          </div>
        )}

        {/* Barre de progression */}
        {book.status === 'reading' && book.total_pages && (
          <div className="mb-3">
            <div className="flex justify-between text-xs text-gray-600 mb-1">
              <span>{book.current_page} pages</span>
              <span>{book.total_pages} pages</span>
            </div>
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
          </div>
        )}

        {/* Date d'ajout */}
        <p className="text-xs text-gray-500">
          Ajouté le {new Date(book.date_added).toLocaleDateString('fr-FR')}
        </p>
      </div>
    </div>
  );
};

export default BookCard;