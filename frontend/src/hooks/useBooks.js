import { useState, useEffect } from 'react';
import BookActions from '../components/books/BookActions';

// Hook personnalisé pour gérer l'état des livres
export const useBooks = () => {
  const [books, setBooks] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedBook, setSelectedBook] = useState(null);
  const [showBookModal, setShowBookModal] = useState(false);

  // Charger les livres au montage
  useEffect(() => {
    loadBooks();
    loadStats();
  }, []);

  // Fonction pour charger les livres
  const loadBooks = async () => {
    await BookActions.loadBooks(setLoading, setBooks);
  };

  // Fonction pour charger les statistiques
  const loadStats = async () => {
    await BookActions.loadStats(setStats);
  };

  // Fonction pour gérer le clic sur un livre
  const handleBookClick = (book) => {
    BookActions.handleBookClick(book, setSelectedBook, setShowBookModal);
  };

  // Fonction pour gérer le clic sur un item (livre ou série)
  const handleItemClick = (item, seriesActions) => {
    if (item.isSeriesCard) {
      seriesActions.setSelectedSeries(item);
      seriesActions.setShowSeriesModal(true);
    } else {
      setSelectedBook(item);
      setShowBookModal(true);
    }
  };

  // Fonction pour mettre à jour un livre
  const handleUpdateBook = async (bookId, bookData) => {
    await BookActions.handleUpdateBook(bookId, bookData, {
      setSelectedBook,
      loadBooks,
      loadStats
    });
  };

  // Fonction pour supprimer un livre
  const handleDeleteBook = async (bookId) => {
    await BookActions.handleDeleteBook(bookId, {
      setSelectedBook,
      setShowBookModal,
      loadBooks,
      loadStats
    });
  };

  // Fonction pour fermer le modal de livre
  const closeBookModal = () => {
    setSelectedBook(null);
    setShowBookModal(false);
  };

  return {
    // États
    books,
    stats,
    loading,
    selectedBook,
    showBookModal,
    
    // Actions
    loadBooks,
    loadStats,
    handleBookClick,
    handleItemClick,
    handleUpdateBook,
    handleDeleteBook,
    closeBookModal,
    
    // Setters (pour compatibilité)
    setBooks,
    setStats,
    setLoading,
    setSelectedBook,
    setShowBookModal
  };
};

export default useBooks;
