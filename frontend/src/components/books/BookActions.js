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
      } else if (booksData && Array.isArray(booksData.items)) {
        // Si l'API retourne un objet avec une propriété 'items' (format paginé)
        setBooks(booksData.items);
      } else {
        // Si les données ne sont pas dans le format attendu
        console.warn('⚠️ Format de données inattendu pour les livres:', booksData);
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
  // SESSION 82.2 - CORRECTION RCA SYSTÈME VIGNETTES : Intégration SeriesDetector
  createUnifiedDisplay(booksList, getCategoryBadgeFromBook) {
    // Vérification renforcée : s'assurer que booksList est toujours un array
    if (!booksList || !Array.isArray(booksList)) {
      console.warn('createUnifiedDisplay: booksList n\'est pas un array:', booksList);
      return [];
    }

    console.log('🔍 [SESSION 82.2] createUnifiedDisplay - Livres reçus:', booksList.length);

    const seriesGroups = {};
    const standaloneBooks = [];

    // 🔍 SESSION 82.2 - CORRECTION RCA : Utiliser SeriesDetector pour détection complète
    const SeriesDetector = require('../../utils/seriesDetector').default;
    
    const booksWithSeriesMarked = booksList.map(book => {
      // Méthode 1 : Champ saga existant (priorité haute)
      if (book.saga && book.saga.trim()) {
        return {
          ...book,
          belongsToSeries: true,
          detectedSeriesName: book.saga.trim(),
          detectionMethod: 'existing_saga_field',
          confidence: 100
        };
      }
      
      // Méthode 2 : Détection intelligente automatique
      const detection = SeriesDetector.detectBookSeries(book);
      
      if (detection.belongsToSeries && detection.confidence >= 70) {
        return {
          ...book,
          belongsToSeries: true,
          detectedSeriesName: detection.seriesName,
          detectionMethod: detection.method,
          confidence: detection.confidence
        };
      }
      
      // Méthode 3 : Livre standalone
      return {
        ...book,
        belongsToSeries: false,
        detectedSeriesName: null,
        detectionMethod: 'standalone',
        confidence: 0
      };
    });

    console.log('🔍 [SESSION 81.1] Analyse des livres:');
    console.log(`📚 Total: ${booksWithSeriesMarked.length} livres`);
    console.log(`📚 Avec série: ${booksWithSeriesMarked.filter(b => b.belongsToSeries).length} livres`);
    console.log(`📖 Standalone: ${booksWithSeriesMarked.filter(b => !b.belongsToSeries).length} livres`);

    booksWithSeriesMarked.forEach(book => {
      if (book.belongsToSeries) {
        // 📚 LIVRE APPARTENANT À UNE SÉRIE - REGROUPEMENT DANS VIGNETTE SÉRIE
        const seriesKey = book.saga.toLowerCase().trim();
        if (!seriesGroups[seriesKey]) {
          seriesGroups[seriesKey] = {
            id: `library-series-${seriesKey}`,
            isSeriesCard: true,
            isLibrarySeries: true,
            name: book.saga,
            title: book.saga,
            author: book.author,
            authors: [book.author], // 🔍 NOUVEAU: Stockage de tous les auteurs de la série
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
        
        // 🔍 NOUVEAU: Ajouter l'auteur à la liste si pas déjà présent
        if (book.author && !seriesGroups[seriesKey].authors.includes(book.author)) {
          seriesGroups[seriesKey].authors.push(book.author);
        }
        
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
        
        // MODIFICATION ORGANISATIONNELLE : Déterminer le statut de la série
        // Logique : Si au moins un livre est "en cours" → EN COURS
        //          Sinon, si tous les livres sont "terminés" → TERMINÉ  
        //          Sinon → À LIRE
        if (seriesGroups[seriesKey].readingBooks > 0) {
          seriesGroups[seriesKey].status = 'reading';
        } else if (seriesGroups[seriesKey].completedBooks === seriesGroups[seriesKey].totalBooks) {
          seriesGroups[seriesKey].status = 'completed';
        } else {
          seriesGroups[seriesKey].status = 'to_read';
        }
        
        // ✅ SESSION 81.1 - MASQUAGE CONFIRMÉ : Livre d'une série, PAS d'ajout aux standaloneBooks
        console.log(`📚 [SESSION 81.1] Livre "${book.title}" appartient à la série "${book.saga}" - MASQUÉ (regroupé dans vignette série)`);
        
      } else {
        // 📖 LIVRE STANDALONE (sans série) - VIGNETTE INDIVIDUELLE AUTORISÉE
        standaloneBooks.push(book);
        console.log(`📖 [SESSION 81.1] Livre "${book.title}" standalone - VIGNETTE INDIVIDUELLE`);
      }
    });

    // Convertir les groupes en tableau et trier par nombre de livres
    const seriesCards = Object.values(seriesGroups).sort((a, b) => b.totalBooks - a.totalBooks);
    
    // MODIFICATION ORGANISATIONNELLE : Tri des livres standalone par statut
    // Ordre prioritaire : EN COURS → À LIRE → TERMINÉ
    const getStatusPriority = (status) => {
      switch (status) {
        case 'reading':    return 1; // EN COURS - Priorité maximale
        case 'to_read':    return 2; // À LIRE - Priorité moyenne
        case 'completed':  return 3; // TERMINÉ - Priorité minimale
        default:           return 4; // Statut inconnu - En dernier
      }
    };
    
    // Tri des livres standalone par statut puis par date d'ajout
    const sortedStandaloneBooks = standaloneBooks.sort((a, b) => {
      const statusPriorityA = getStatusPriority(a.status);
      const statusPriorityB = getStatusPriority(b.status);
      
      // Si les statuts sont différents, trier par priorité de statut
      if (statusPriorityA !== statusPriorityB) {
        return statusPriorityA - statusPriorityB;
      }
      
      // Si même statut, trier par date d'ajout (plus récent d'abord)
      const dateA = new Date(a.date_added || a.updated_at || 0);
      const dateB = new Date(b.date_added || b.updated_at || 0);
      return dateB - dateA;
    });
    
    // 📊 SESSION 81.1 - RÉSUMÉ AFFICHAGE DÉTAILLÉ
    console.log(`🎯 [SESSION 81.1] Résumé affichage final:`);
    console.log(`🎯 - ${seriesCards.length} vignettes de série (${Object.keys(seriesGroups).length} séries uniques)`);
    console.log(`🎯 - ${sortedStandaloneBooks.length} livres standalone (vignettes individuelles)`);
    console.log(`🎯 - ${booksList.length - sortedStandaloneBooks.length} livres masqués (dans vignettes série)`);
    
    seriesCards.forEach(series => {
      console.log(`📚 [SESSION 81.1] Série "${series.name}" - ${series.totalBooks} tomes regroupés`);
    });
    
    return [...seriesCards, ...sortedStandaloneBooks];
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
