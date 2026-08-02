import { bookService } from '../../services/bookService';
import { toast } from 'react-hot-toast';
import { openStaticWikidataSeriesModal } from '../../utils/openStaticWikidataSeries';
import {
  attributeBookToSeries,
  evaluateOwnedSeriesForDisplay,
} from '../../utils/seriesAttribution';
import { isUsableSynopsis } from '../../utils/synopsisQuality';

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
    // - Vraies séries curées (SdA…) gardées même avec 1 tome en bibliothèque
    // - Doublons du même livre (Long Dimanche × N) → fiche livre
    const seriesCards = [];
    const demotedFromSeries = [];
    userSeriesLibrary.forEach((series) => {
      const volArr = Array.isArray(series.volumes) ? series.volumes : [];
      const name = series.series_name || series.name || '';
      const verdict = evaluateOwnedSeriesForDisplay(series);
      const completed = volArr.filter((v) => v.is_read).length;

      if (verdict.demote) {
        demotedFromSeries.push({
          id: series.id,
          seriesLibraryId: series.id,
          isSeriesCard: false,
          isDemotedSeries: true,
          title: name,
          author: (Array.isArray(series.authors) && series.authors[0])
            || series.author
            || '',
          category: series.category || 'roman',
          status: series.series_status || 'to_read',
          cover_url: series.cover_image_url || series.cover_url || null,
          // Ignorer les faux résumés Wikidata / compteurs de tomes
          description: isUsableSynopsis(series.description_fr)
            ? series.description_fr
            : '',
          date_added: series.created_at,
          updated_at: series.updated_at,
          saga: '',
          total_pages: series.total_pages || null,
          current_page: series.current_page ?? null,
          rating: series.rating || 0,
          review: series.review || '',
        });
        return;
      }

      const total = verdict.totalBooks;
      // Enrichir la liste des tomes depuis le référentiel curé si pauvre
      let volumes = volArr;
      const curatedTitles = verdict.curated?.data?.volume_titles;
      if (
        curatedTitles &&
        typeof curatedTitles === 'object' &&
        verdict.distinctOwned <= 1
      ) {
        volumes = Object.entries(curatedTitles).map(([num, title]) => ({
          volume_number: Number(num) || 0,
          volume_title: title,
          is_read: false,
          date_read: null,
        }));
      }

      seriesCards.push({
        id: series.id,
        isSeriesCard: true,
        isOwnedSeries: true,
        name: verdict.curated?.data?.name || name,
        author: series.authors?.[0] || 'Auteur inconnu',
        category: series.category,
        status: series.series_status || 'to_read',
        date_added: series.created_at,
        updated_at: series.updated_at,
        completion_percentage: series.completion_percentage || 0,
        total_books: total,
        totalBooks: total,
        completedBooks: completed,
        readingBooks: 0,
        toReadBooks: Math.max(0, total - completed),
        volumes,
        cover_url: series.cover_image_url || series.cover_url || null,
        title: verdict.curated?.data?.name || name,
        saga: verdict.curated?.data?.name || name,
        description: series.description_fr || `Collection ${name}`,
        progressPercent:
          total > 0
            ? Math.round((completed / total) * 100)
            : series.completion_percentage || 0,
      });
    });


    // 🔍 Attribution unifiée recherche + bibliothèque : ordre curé → saga.
    // (Wikidata réservé à la recherche : pas d'appel réseau par livre côté bibliothèque.)
    const booksWithSeriesMarked = booksList.map(book => {
      const attr = attributeBookToSeries(book);
      if (attr) {
        return {
          ...book,
          belongsToSeries: true,
          detectedSeriesKey: attr.seriesKey,
          detectedSeriesName: attr.seriesName,
          detectionMethod: attr.method || attr.source,
          confidence: attr.confidence != null ? attr.confidence : (attr.source === 'saga' ? 100 : 90)
        };
      }
      // Livre standalone
      return {
        ...book,
        belongsToSeries: false,
        detectedSeriesKey: null,
        detectedSeriesName: null,
        detectionMethod: 'standalone',
        confidence: 0
      };
    });


    booksWithSeriesMarked.forEach(book => {
      if (book.belongsToSeries) {
        // 📚 LIVRE APPARTENANT À UNE SÉRIE - REGROUPEMENT DANS VIGNETTE SÉRIE
        const seriesKey = book.detectedSeriesKey || book.detectedSeriesName.toLowerCase().trim();
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

    // Groupes à 1 seul livre → rester en livre individuel (évite vignettes série fantômes)
    const detectedSeriesCards = [];
    Object.values(seriesGroups).forEach((group) => {
      if ((group.totalBooks || 0) <= 1) {
        if (group.books?.[0]) {
          standaloneBooks.push({
            ...group.books[0],
            belongsToSeries: false,
            detectedSeriesKey: null,
            detectedSeriesName: null,
          });
        }
        return;
      }
      detectedSeriesCards.push(group);
    });
    detectedSeriesCards.sort((a, b) => b.totalBooks - a.totalBooks);

    // Éviter doublons titre entre livres réels et séries rétrogradées
    const standaloneTitles = new Set(
      standaloneBooks.map((b) => (b.title || '').toLowerCase().trim())
    );
    demotedFromSeries.forEach((b) => {
      const key = (b.title || '').toLowerCase().trim();
      if (key && standaloneTitles.has(key)) return;
      standaloneBooks.push(b);
      if (key) standaloneTitles.add(key);
    });
    
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

    // Combiner + dédoublonner : garder la carte avec le plus de tomes
    // (évite qu'une série owned mal remplie écrase une détection correcte)
    const rawSeriesCards = [...seriesCards, ...detectedSeriesCards];
    const bestByName = new Map();
    rawSeriesCards.forEach((card) => {
      const key = (card.name || card.title || '').toLowerCase().trim();
      if (!key) return;
      const prev = bestByName.get(key);
      const score = (c) =>
        (Number(c.totalBooks) || 0) * 10 + (c.isOwnedSeries ? 1 : 0) + (c.books?.length || 0);
      if (!prev || score(card) > score(prev)) {
        bestByName.set(key, card);
      }
    });
    const dedupedSeriesCards = Array.from(bestByName.values());

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
  async handleItemClick(item, actions) {
    const { setSelectedSeries, setShowSeriesModal, setSelectedBook, setShowBookModal } = actions;

    if (item.isSeriesCard && item.wikidata_qid && item.isStaticWikidataCard) {
      await openStaticWikidataSeriesModal(item, setSelectedSeries, setShowSeriesModal);
      return;
    }

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
      throw error; // propager pour que les appelants gèrent l'état (ex. isLoading)
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
