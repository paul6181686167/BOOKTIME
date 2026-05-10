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
  // Fonction pour créer l'affichage unifié des livres et séries
  // SESSION 84 - PHASE B : Intégration userSeriesLibrary dans affichage  
  createUnifiedDisplay(booksList, getCategoryBadgeFromBook, userSeriesLibrary = [], readingPreferences = {}) {
    // Vérification renforcée : s'assurer que booksList est toujours un array
    if (!booksList || !Array.isArray(booksList)) {
      console.warn('createUnifiedDisplay: booksList n\'est pas un array:', booksList);
      return [];
    }


    const seriesGroups = {};
    const standaloneBooks = [];

    // 🆕 PHASE B : Convertir séries bibliothèque en format d'affichage
    const seriesCards = userSeriesLibrary.map(series => ({
      id: series.id,
      isSeriesCard: true,
      isOwnedSeries: true, // Marquer comme série possédée
      name: series.series_name,
      author: series.authors?.[0] || 'Auteur inconnu',
      category: series.category,
      status: series.series_status || 'to_read',
      date_added: series.created_at,
      updated_at: series.updated_at,
      completion_percentage: series.completion_percentage || 0,
      total_books: series.total_volumes || 0,
      totalBooks: series.total_volumes || 0,
      completedBooks: series.volumes?.filter(v => v.is_read).length || 0,
      readingBooks: 0, // Calculé selon logique série
      toReadBooks: (series.total_volumes || 0) - (series.volumes?.filter(v => v.is_read).length || 0),
      volumes: series.volumes || [],
      cover_url: series.cover_image_url || series.cover_url || null,
      // Données pour tri et affichage
      title: series.series_name,
      saga: series.series_name,
      // Métadonnées enrichies
      description: series.description_fr || `Collection ${series.series_name}`,
      progressPercent: series.completion_percentage || 0
    }));


    // 🔍 SESSION 82.2 - CORRECTION RCA : Utiliser SeriesDetector pour détection complète
    // Import dynamique du SeriesDetector
    let SeriesDetector;
    try {
      SeriesDetector = require('../../utils/seriesDetector').SeriesDetector;
    } catch (e) {
      console.warn('SeriesDetector non disponible, fallback vers détection saga uniquement');
      SeriesDetector = null;
    }
    
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
      
      // Méthode 2 : Détection intelligente (seuil plus strict si pas de saga = éviter faux positifs)
      if (SeriesDetector) {
        const detection = SeriesDetector.detectBookSeries(book);
        const minConfidence = 90; // Livre sans saga : seuil élevé pour éviter de masquer des standalone
        if (detection.belongsToSeries && detection.confidence >= minConfidence) {
          return {
            ...book,
            belongsToSeries: true,
            detectedSeriesName: detection.seriesName,
            detectionMethod: detection.method,
            confidence: detection.confidence
          };
        }
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


    booksWithSeriesMarked.forEach(book => {
      if (book.belongsToSeries) {
        // 📚 LIVRE APPARTENANT À UNE SÉRIE - REGROUPEMENT DANS VIGNETTE SÉRIE
        const seriesKey = book.detectedSeriesName.toLowerCase().trim();
        if (!seriesGroups[seriesKey]) {
          seriesGroups[seriesKey] = {
            id: `library-series-${seriesKey}`,
            isSeriesCard: true,
            isLibrarySeries: true,
            name: book.detectedSeriesName,
            title: book.detectedSeriesName,
            author: book.author,
            authors: [book.author], // 🔍 NOUVEAU: Stockage de tous les auteurs de la série
            category: book.category,
            books: [],
            totalBooks: 0,
            completedBooks: 0,
            readingBooks: 0,
            toReadBooks: 0,
            cover_url: book.cover_url,
            progressPercent: 0,
            // SESSION 82.2 - NOUVEAUX CHAMPS : Informations de détection
            detectionMethod: book.detectionMethod,
            averageConfidence: book.confidence
          };
        }
        
        seriesGroups[seriesKey].books.push(book);
        seriesGroups[seriesKey].totalBooks += 1;

        // Prendre la première couverture disponible parmi tous les livres du groupe
        if (!seriesGroups[seriesKey].cover_url && book.cover_url) {
          seriesGroups[seriesKey].cover_url = book.cover_url;
        }
        
        // 🔍 NOUVEAU: Ajouter l'auteur à la liste si pas déjà présent
        if (book.author && !seriesGroups[seriesKey].authors.includes(book.author)) {
          seriesGroups[seriesKey].authors.push(book.author);
        }
        
        // SESSION 82.2 - Mise à jour confiance moyenne
        const currentBooks = seriesGroups[seriesKey].books;
        const totalConfidence = currentBooks.reduce((sum, b) => sum + (b.confidence || 0), 0);
        seriesGroups[seriesKey].averageConfidence = Math.round(totalConfidence / currentBooks.length);
        
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
        
        
      } else {
        standaloneBooks.push(book);
      }
    });

    // Convertir les groupes de livres détectés en tableau et trier par nombre de livres
    const detectedSeriesCards = Object.values(seriesGroups).sort((a, b) => b.totalBooks - a.totalBooks);
    
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

    // 🆕 Enrichir la progression avec reading-preferences (tomes lus dans le modal)
    const getRefVolumes = (seriesName) => {
      try {
        const { EXTENDED_SERIES_DATABASE } = require('../../utils/seriesDatabaseExtended');
        const sn = (seriesName || '').toLowerCase();
        for (const category of Object.values(EXTENDED_SERIES_DATABASE)) {
          for (const s of Object.values(category)) {
            if (s.name?.toLowerCase() === sn || s.variations?.some(v => v?.toLowerCase() === sn)) {
              return s.volumes;
            }
          }
        }
      } catch (e) {}
      return null;
    };
    const applyReadingPreferences = (cards) => cards.map(card => {
      const readTomes = readingPreferences[card.name] ?? readingPreferences[card.name?.trim()];
      const refVolumes = getRefVolumes(card.name);
      if (refVolumes && Array.isArray(readTomes)) {
        const completed = readTomes.length;
        return { ...card, totalBooks: refVolumes, completedBooks: completed, progressPercent: Math.round((completed / refVolumes) * 100), total_books: refVolumes };
      }
      if (refVolumes) {
        return { ...card, totalBooks: refVolumes, total_books: refVolumes };
      }
      return card;
    });

    // Combiner séries bibliothèque + séries détectées, puis dédoublonner par nom normalisé
    // Priorité : série de bibliothèque (isOwnedSeries) > série détectée
    const rawSeriesCards = [...seriesCards, ...detectedSeriesCards];
    const seenSeriesNames = new Set();
    const dedupedSeriesCards = rawSeriesCards.filter(card => {
      const key = (card.name || card.title || '').toLowerCase().trim();
      if (!key) return true;
      if (seenSeriesNames.has(key)) return false;
      seenSeriesNames.add(key);
      return true;
    });

    const allSeriesCards = applyReadingPreferences(dedupedSeriesCards).sort((a, b) => {
      if (a.isOwnedSeries && !b.isOwnedSeries) return -1;
      if (!a.isOwnedSeries && b.isOwnedSeries) return 1;
      const dateA = new Date(a.updated_at || a.date_added || 0);
      const dateB = new Date(b.updated_at || b.date_added || 0);
      return dateB - dateA;
    });

    return [...allSeriesCards, ...sortedStandaloneBooks];
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
      
      if (bookData.category) {
        const categoryLabels = { roman: 'Romans', bd: 'Romans Graphiques', manga: 'Mangas' };
        toast.success(`Livre déplacé vers : ${categoryLabels[bookData.category] || bookData.category}`);
      } else {
        toast.success('Livre mis à jour avec succès !');
      }
    } catch (error) {
      console.error('Erreur lors de la mise à jour du livre:', error);
      toast.error('Erreur lors de la mise à jour du livre');
    }
  },

  // Fonction pour ajouter un livre à la bibliothèque
  async addBook(bookData) {
    try {
      const result = await bookService.createBook(bookData);
      toast.success(`"${bookData.title || 'Livre'}" ajouté à la bibliothèque !`);
      return result;
    } catch (error) {
      console.error('Erreur lors de l\'ajout du livre:', error);
      toast.error('Impossible d\'ajouter le livre. Réessaie dans un instant.');
      throw error;
    }
  },

  // Fonction pour supprimer un livre
  async handleDeleteBook(bookId, actions) {
    const { setSelectedBook, setShowBookModal, loadBooks, loadStats } = actions;
    
    await bookService.deleteBook(bookId);
    setSelectedBook(null);
    setShowBookModal(false);
    
    await loadBooks();
    await loadStats();
    
    toast.success('Livre retiré de ta bibliothèque !');
  }
};

export default BookActions;
