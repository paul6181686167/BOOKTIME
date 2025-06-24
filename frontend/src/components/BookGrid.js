import React from 'react';
import BookCard from './BookCard';

const BookGrid = ({ books, loading, onBookClick }) => {
  if (loading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-booktime-500"></div>
      </div>
    );
  }

  if (!books || books.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">📚</div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
          Aucun livre trouvé
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          Commencez par ajouter votre premier livre à votre collection
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
      {books.map((book) => (
        <BookCard
          key={book.id}
          book={book}
          onBookClick={onBookClick}
        />
      ))}
    </div>
  );
};

export default BookGrid;