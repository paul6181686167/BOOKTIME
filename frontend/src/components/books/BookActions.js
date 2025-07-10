import { bookService } from '../../services/bookService';
import { toast } from 'react-hot-toast';

// Composant BookActions pour gérer toutes les actions liées aux livres
const BookActions = {
  // Fonction pour charger tous les livres
  async loadBooks(setLoading, setBooks) {
    try {
      setLoading(true);
      const booksData = await bookService.getBooks();
      // Vérification que booksData est un array
      if (Array.isArray(booksData)) {
        setBooks(booksData);
      } else if (booksData && Array.isArray(booksData.books)) {
        // Si l'API retourne un objet avec une propriété 'books'
        setBooks(booksData.books);
      } else {
        // Si les données ne sont pas dans le format attendu
        console.warn('Format de données inattendu pour les livres:', booksData);
        setBooks([]);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des livres:', error);
      toast.error('Erreur lors du chargement des livres');
      // IMPORTANT : Définir books comme array vide en cas d'erreur
      setBooks([]);
    } finally {
      setLoading(false);
    }
  },

  // Fonction pour charger les statistiques
  async loadStats(setStats) {
    try {
      const stats = await bookService.getStats();
      setStats(stats);
    } catch (error) {
      console.error('Erreur lors du chargement des statistiques:', error);
      toast.error('Erreur lors du chargement des statistiques');
    }
  },

  // Fonction pour rechercher des séries
  async searchSeries(query) {
    try {
      const response = await bookService.searchSeries(query);
      return response.series || [];
    } catch (error) {
      console.error('Erreur lors de la recherche de séries:', error);
      return [];
    }
  },

  // Fonction pour créer l'affichage unifié des livres et séries
  createUnifiedDisplay(booksList, getCategoryBadgeFromBook) {
    const seriesGroups = {};
    const standaloneBooks = [];

    booksList.forEach(book => {
      if (book.saga && book.saga.trim()) {
        const seriesKey = book.saga.toLowerCase().trim();
        if (!seriesGroups[seriesKey]) {
          seriesGroups[seriesKey] = {
            id: `library-series-${seriesKey}`,
            isSeriesCard: true,
            isLibrarySeries: true,
            name: book.saga,
            title: book.saga,
            author: book.author,
            category: book.category,
            books: [],
            totalBooks: 0,
            completedBooks: 0,
            readingBooks: 0,
            toReadBooks: 0,
            cover_url: book.cover_url,
            progressPercent: 0
          };
        }
        
        seriesGroups[seriesKey].books.push(book);
        seriesGroups[seriesKey].totalBooks += 1;
        
        // Compter les statuts
        switch (book.status) {
          case 'completed':
            seriesGroups[seriesKey].completedBooks += 1;
            break;
          case 'reading':
            seriesGroups[seriesKey].readingBooks += 1;
            break;
          case 'to_read':
            seriesGroups[seriesKey].toReadBooks += 1;
            break;
        }
        
        // Calculer le pourcentage de progression
        seriesGroups[seriesKey].progressPercent = Math.round(
          (seriesGroups[seriesKey].completedBooks / seriesGroups[seriesKey].totalBooks) * 100
        );
      } else {
        // Livre standalone (sans série)
        standaloneBooks.push(book);
      }
    });

    // Convertir les groupes en tableau et trier par nombre de livres
    const seriesCards = Object.values(seriesGroups).sort((a, b) => b.totalBooks - a.totalBooks);
    
    return [...seriesCards, ...standaloneBooks];
  },

  // Fonction pour gérer le clic sur un livre
  handleBookClick(book, setSelectedBook, setShowBookModal) {
    setSelectedBook(book);
    setShowBookModal(true);
  },

  // Fonction pour gérer le clic sur un item (livre ou série)
  handleItemClick(item, actions) {
    const { setSelectedSeries, setShowSeriesModal, setSelectedBook, setShowBookModal } = actions;
    
    if (item.isSeriesCard) {
      setSelectedSeries(item);
      setShowSeriesModal(true);
    } else {
      setSelectedBook(item);
      setShowBookModal(true);
    }
  },

  // Fonction pour mettre à jour un livre
  async handleUpdateBook(bookId, bookData, actions) {
    const { setSelectedBook, loadBooks, loadStats } = actions;
    
    try {
      const updatedBook = await bookService.updateBook(bookId, bookData);
      setSelectedBook(updatedBook);
      
      // Recharger les données
      await loadBooks();
      await loadStats();
      
      toast.success('Livre mis à jour avec succès !');
    } catch (error) {
      console.error('Erreur lors de la mise à jour du livre:', error);
      toast.error('Erreur lors de la mise à jour du livre');
    }
  },

  // Fonction pour supprimer un livre
  async handleDeleteBook(bookId, actions) {
    const { setSelectedBook, setShowBookModal, loadBooks, loadStats } = actions;
    
    try {
      await bookService.deleteBook(bookId);
      setSelectedBook(null);
      setShowBookModal(false);
      
      // Recharger les données
      await loadBooks();
      await loadStats();
      
      toast.success('Livre supprimé avec succès !');
    } catch (error) {
      console.error('Erreur lors de la suppression du livre:', error);
      toast.error('Erreur lors de la suppression du livre');
    }
  }
};

export default BookActions;
