// Service de mock pour GitHub Pages (sans backend)
import { bookService as realBookService } from './bookService';

// Stockage local avec localStorage
const STORAGE_KEY = 'booktime_data';

// Données initiales
const initialData = {
  books: [
    {
      id: "1",
      _id: "1",
      title: "Le Seigneur des Anneaux - La Communauté de l'Anneau",
      author: "J.R.R. Tolkien",
      category: "roman",
      description: "Premier tome de la saga épique",
      status: "completed",
      current_page: 0,
      total_pages: 423,
      rating: 5,
      review: "Un chef-d'œuvre de la fantasy !",
      date_added: new Date().toISOString(),
      date_completed: new Date().toISOString(),
      saga: "Le Seigneur des Anneaux",
      volume_number: 1,
      genre: ["Fantasy", "Aventure"],
      publisher: "Christian Bourgois",
      original_language: "anglais",
      reading_language: "français",
      available_translations: ["français", "anglais"]
    },
    {
      id: "2",
      _id: "2",
      title: "One Piece - Tome 1",
      author: "Eiichiro Oda",
      category: "manga",
      description: "Le début de l'aventure de Luffy",
      status: "reading",
      current_page: 50,
      total_pages: 200,
      date_added: new Date().toISOString(),
      date_started: new Date().toISOString(),
      saga: "One Piece",
      volume_number: 1,
      genre: ["Shōnen", "Aventure", "Comédie"],
      publisher: "Glénat",
      original_language: "japonais",
      reading_language: "français",
      available_translations: ["français", "anglais", "japonais"]
    },
    {
      id: "3",
      _id: "3",
      title: "Tintin - Les Cigares du Pharaon",
      author: "Hergé",
      category: "bd",
      description: "Les aventures de Tintin en Égypte",
      status: "to_read",
      current_page: 0,
      total_pages: 62,
      date_added: new Date().toISOString(),
      saga: "Les Aventures de Tintin",
      volume_number: 4,
      genre: ["Aventure", "Mystère"],
      publisher: "Casterman",
      original_language: "français",
      reading_language: "français",
      available_translations: ["français", "anglais", "néerlandais"]
    }
  ]
};

// Utilitaires de stockage
const loadData = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : initialData;
  } catch (error) {
    console.error('Erreur lors du chargement des données:', error);
    return initialData;
  }
};

const saveData = (data) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch (error) {
    console.error('Erreur lors de la sauvegarde:', error);
  }
};

// Générer un ID unique
const generateId = () => {
  return Date.now().toString() + Math.random().toString(36).substr(2, 9);
};

// Service mock
export const mockBookService = {
  // Récupérer tous les livres
  async getBooks(category = null, status = null) {
    const data = loadData();
    let books = data.books || [];
    
    if (category) {
      books = books.filter(book => book.category === category);
    }
    
    if (status) {
      books = books.filter(book => book.status === status);
    }
    
    return books;
  },

  // Créer un livre
  async createBook(bookData) {
    const data = loadData();
    const newBook = {
      ...bookData,
      id: generateId(),
      _id: generateId(),
      status: "to_read",
      current_page: 0,
      date_added: new Date().toISOString(),
      category: bookData.category.toLowerCase()
    };
    
    data.books.push(newBook);
    saveData(data);
    
    return newBook;
  },

  // Récupérer un livre par ID
  async getBook(bookId) {
    const data = loadData();
    const book = data.books.find(book => book.id === bookId || book._id === bookId);
    
    if (!book) {
      throw new Error('Livre non trouvé');
    }
    
    return book;
  },

  // Mettre à jour un livre
  async updateBook(bookId, updates) {
    const data = loadData();
    const bookIndex = data.books.findIndex(book => book.id === bookId || book._id === bookId);
    
    if (bookIndex === -1) {
      throw new Error('Livre non trouvé');
    }
    
    // Automatiquement définir les dates selon le statut
    if (updates.status) {
      if (updates.status === "reading" && !updates.date_started) {
        updates.date_started = new Date().toISOString();
      } else if (updates.status === "completed" && !updates.date_completed) {
        updates.date_completed = new Date().toISOString();
      }
    }
    
    data.books[bookIndex] = { ...data.books[bookIndex], ...updates };
    saveData(data);
    
    return data.books[bookIndex];
  },

  // Supprimer un livre
  async deleteBook(bookId) {
    const data = loadData();
    const bookIndex = data.books.findIndex(book => book.id === bookId || book._id === bookId);
    
    if (bookIndex === -1) {
      throw new Error('Livre non trouvé');
    }
    
    data.books.splice(bookIndex, 1);
    saveData(data);
    
    return { message: 'Livre supprimé avec succès' };
  },

  // Récupérer les statistiques
  async getStats() {
    const data = loadData();
    const books = data.books || [];
    
    const total_books = books.length;
    const completed_books = books.filter(book => book.status === "completed").length;
    const reading_books = books.filter(book => book.status === "reading").length;
    const to_read_books = books.filter(book => book.status === "to_read").length;
    
    const roman_count = books.filter(book => book.category === "roman").length;
    const bd_count = books.filter(book => book.category === "bd").length;
    const manga_count = books.filter(book => book.category === "manga").length;
    
    const sagas = [...new Set(books.filter(book => book.saga).map(book => book.saga))];
    const authors = [...new Set(books.map(book => book.author))];
    const auto_added_count = books.filter(book => book.auto_added).length;
    
    return {
      total_books,
      completed_books,
      reading_books,
      to_read_books,
      categories: {
        roman: roman_count,
        bd: bd_count,
        manga: manga_count
      },
      sagas_count: sagas.length,
      authors_count: authors.length,
      auto_added_count
    };
  },

  // Récupérer les livres par auteur
  async getBooksByAuthor(authorName) {
    const data = loadData();
    return data.books.filter(book => 
      book.author.toLowerCase().includes(authorName.toLowerCase())
    );
  },

  // Récupérer les livres par saga
  async getBooksBySaga(sagaName) {
    const data = loadData();
    return data.books.filter(book => book.saga === sagaName)
      .sort((a, b) => (a.volume_number || 0) - (b.volume_number || 0));
  },

  // Mock pour les autres méthodes
  async getAuthors() {
    const data = loadData();
    const authorsMap = {};
    
    data.books.forEach(book => {
      if (!authorsMap[book.author]) {
        authorsMap[book.author] = {
          name: book.author,
          books_count: 0,
          categories: new Set(),
          sagas: new Set()
        };
      }
      
      authorsMap[book.author].books_count++;
      authorsMap[book.author].categories.add(book.category);
      if (book.saga) {
        authorsMap[book.author].sagas.add(book.saga);
      }
    });
    
    return Object.values(authorsMap).map(author => ({
      ...author,
      categories: Array.from(author.categories),
      sagas: Array.from(author.sagas)
    }));
  },

  async getSagas() {
    const data = loadData();
    const sagasMap = {};
    
    data.books.forEach(book => {
      if (book.saga) {
        if (!sagasMap[book.saga]) {
          sagasMap[book.saga] = {
            name: book.saga,
            books_count: 0,
            completed_books: 0,
            author: book.author,
            category: book.category,
            next_volume: 1
          };
        }
        
        sagasMap[book.saga].books_count++;
        if (book.status === "completed") {
          sagasMap[book.saga].completed_books++;
        }
        if (book.volume_number) {
          sagasMap[book.saga].next_volume = Math.max(
            sagasMap[book.saga].next_volume, 
            book.volume_number + 1
          );
        }
      }
    });
    
    return Object.values(sagasMap);
  }
};

// Service adaptatif : utilise le vrai service si backend disponible, sinon mock
export const adaptiveBookService = {
  ...realBookService,
  
  async getBooks(...args) {
    try {
      return await realBookService.getBooks(...args);
    } catch (error) {
      console.log('🔄 Backend indisponible, utilisation du mode offline');
      return await mockBookService.getBooks(...args);
    }
  },

  async createBook(...args) {
    try {
      return await realBookService.createBook(...args);
    } catch (error) {
      console.log('🔄 Backend indisponible, utilisation du mode offline');
      return await mockBookService.createBook(...args);
    }
  },

  async getBook(...args) {
    try {
      return await realBookService.getBook(...args);
    } catch (error) {
      console.log('🔄 Backend indisponible, utilisation du mode offline');
      return await mockBookService.getBook(...args);
    }
  },

  async updateBook(...args) {
    try {
      return await realBookService.updateBook(...args);
    } catch (error) {
      console.log('🔄 Backend indisponible, utilisation du mode offline');
      return await mockBookService.updateBook(...args);
    }
  },

  async deleteBook(...args) {
    try {
      return await realBookService.deleteBook(...args);
    } catch (error) {
      console.log('🔄 Backend indisponible, utilisation du mode offline');
      return await mockBookService.deleteBook(...args);
    }
  },

  async getStats(...args) {
    try {
      return await realBookService.getStats(...args);
    } catch (error) {
      console.log('🔄 Backend indisponible, utilisation du mode offline');
      return await mockBookService.getStats(...args);
    }
  },

  async getBooksByAuthor(...args) {
    try {
      return await realBookService.getBooksByAuthor(...args);
    } catch (error) {
      console.log('🔄 Backend indisponible, utilisation du mode offline');
      return await mockBookService.getBooksByAuthor(...args);
    }
  },

  async getBooksBySaga(...args) {
    try {
      return await realBookService.getBooksBySaga(...args);
    } catch (error) {
      console.log('🔄 Backend indisponible, utilisation du mode offline');
      return await mockBookService.getBooksBySaga(...args);
    }
  },

  async getAuthors(...args) {
    try {
      return await realBookService.getAuthors(...args);
    } catch (error) {
      console.log('🔄 Backend indisponible, utilisation du mode offline');
      return await mockBookService.getAuthors(...args);
    }
  },

  async getSagas(...args) {
    try {
      return await realBookService.getSagas(...args);
    } catch (error) {
      console.log('🔄 Backend indisponible, utilisation du mode offline');
      return await mockBookService.getSagas(...args);
    }
  }
};