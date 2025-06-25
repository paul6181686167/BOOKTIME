import React, { useState, useEffect, createContext, useContext } from 'react';
import { Toaster } from 'react-hot-toast';
import toast from 'react-hot-toast';
import AdvancedSearchBar from './components/AdvancedSearchBar';
import { useAdvancedSearch } from './hooks/useAdvancedSearch';
import './App.css';

// Auth Context
const AuthContext = createContext();

// Auth Provider
function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    // Check if user is logged in on app start
    const token = localStorage.getItem('token');
    if (token) {
      checkAuthStatus(token);
    } else {
      setLoading(false);
    }
  }, []);

  const checkAuthStatus = async (token) => {
    try {
      const response = await fetch(`${backendUrl}/api/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        localStorage.removeItem('token');
      }
    } catch (error) {
      console.error('Error checking auth status:', error);
      localStorage.removeItem('token');
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await fetch(`${backendUrl}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        setUser(data.user);
        return { success: true };
      } else {
        const error = await response.json();
        return { success: false, error: error.detail };
      }
    } catch (error) {
      return { success: false, error: 'Erreur de connexion' };
    }
  };

  const register = async (email, password, firstName, lastName) => {
    try {
      const response = await fetch(`${backendUrl}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email,
          password,
          first_name: firstName,
          last_name: lastName
        })
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        setUser(data.user);
        return { success: true };
      } else {
        const error = await response.json();
        return { success: false, error: error.detail };
      }
    } catch (error) {
      return { success: false, error: 'Erreur lors de l\'inscription' };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  const value = {
    user,
    loading,
    login,
    register,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// Hook to use auth context
function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// Book Service
class BookService {
  constructor() {
    this.backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
  }

  getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };
  }

  async getBooks(category = null, status = null) {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (status) params.append('status', status);

    const response = await fetch(`${this.backendUrl}/api/books?${params}`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('Failed to fetch books');
    }

    return response.json();
  }

  async createBook(bookData) {
    const response = await fetch(`${this.backendUrl}/api/books`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(bookData)
    });

    if (!response.ok) {
      throw new Error('Failed to create book');
    }

    return response.json();
  }

  async updateBook(bookId, updates) {
    const response = await fetch(`${this.backendUrl}/api/books/${bookId}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(updates)
    });

    if (!response.ok) {
      throw new Error('Failed to update book');
    }

    return response.json();
  }

  async deleteBook(bookId) {
    const response = await fetch(`${this.backendUrl}/api/books/${bookId}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('Failed to delete book');
    }

    return response.json();
  }

  async getStats() {
    const response = await fetch(`${this.backendUrl}/api/stats`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('Failed to fetch stats');
    }

    return response.json();
  }

  async searchOpenLibrary(query) {
    const response = await fetch(`${this.backendUrl}/api/openlibrary/search?q=${encodeURIComponent(query)}`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('Failed to search OpenLibrary');
    }

    return response.json();
  }
}

const bookService = new BookService();

// Login Component
function LoginPage() {
  const { login, register } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    firstName: '',
    lastName: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    let result;
    if (isLogin) {
      result = await login(formData.email, formData.password);
    } else {
      result = await register(formData.email, formData.password, formData.firstName, formData.lastName);
    }

    if (result.success) {
      toast.success(isLogin ? 'Connexion réussie !' : 'Compte créé avec succès !');
    } else {
      toast.error(result.error);
    }
    
    setLoading(false);
  };

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">📚 BOOKTIME</h1>
          <p className="text-gray-600">Gérez votre bibliothèque personnelle</p>
        </div>

        <div className="flex mb-6 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setIsLogin(true)}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${
              isLogin ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600'
            }`}
          >
            Connexion
          </button>
          <button
            onClick={() => setIsLogin(false)}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${
              !isLogin ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600'
            }`}
          >
            Inscription
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Prénom
                </label>
                <input
                  type="text"
                  name="firstName"
                  value={formData.firstName}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required={!isLogin}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nom
                </label>
                <input
                  type="text"
                  name="lastName"
                  value={formData.lastName}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required={!isLogin}
                />
              </div>
            </>
          )}
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Mot de passe
            </label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Chargement...' : (isLogin ? 'Se connecter' : 'Créer un compte')}
          </button>
        </form>
      </div>
    </div>
  );
}

// Main App Content
function AppContent() {
  const { user } = useAuth();
  const [books, setBooks] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('roman');
  const [activeStatus, setActiveStatus] = useState('all');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showOpenLibraryModal, setShowOpenLibraryModal] = useState(false);
  const [selectedBook, setSelectedBook] = useState(null);

  // Utiliser le hook de recherche avancée
  const {
    searchTerm,
    setSearchTerm,
    filters,
    setFilters,
    filteredBooks: searchFilteredBooks,
    searchStats,
    clearSearch
  } = useAdvancedSearch(books);

  // Appliquer les filtres d'onglets et de statut par-dessus la recherche avancée
  const [finalFilteredBooks, setFinalFilteredBooks] = useState([]);

  useEffect(() => {
    let filtered = searchFilteredBooks;

    // Filtrer par onglet actif
    if (activeTab !== 'all') {
      filtered = filtered.filter(book => book.category === activeTab);
    }

    // Filtrer par statut actif
    if (activeStatus !== 'all') {
      filtered = filtered.filter(book => book.status === activeStatus);
    }

    setFinalFilteredBooks(filtered);
  }, [searchFilteredBooks, activeTab, activeStatus]);

  // Charger les livres au démarrage
  useEffect(() => {
    if (user) {
      loadBooks();
      loadStats();
    }
  }, [user]);

  const loadBooks = async () => {
    try {
      setLoading(true);
      const data = await bookService.getBooks();
      setBooks(data);
    } catch (error) {
      console.error('Erreur lors du chargement des livres:', error);
      toast.error('Erreur lors du chargement des livres');
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const data = await bookService.getStats();
      setStats(data);
    } catch (error) {
      console.error('Erreur lors du chargement des statistiques:', error);
    }
  };

  const handleAddBook = async (bookData) => {
    try {
      await bookService.createBook(bookData);
      await loadBooks();
      await loadStats();
      setShowAddModal(false);
      toast.success(`"${bookData.title}" ajouté à votre collection !`);
    } catch (error) {
      console.error('Erreur lors de l\'ajout du livre:', error);
      toast.error('Erreur lors de l\'ajout du livre');
    }
  };

  const handleUpdateBook = async (bookId, updates) => {
    try {
      await bookService.updateBook(bookId, updates);
      await loadBooks();
      await loadStats();
      setSelectedBook(null);
      toast.success('Livre mis à jour !');
    } catch (error) {
      console.error('Erreur lors de la mise à jour du livre:', error);
      toast.error('Erreur lors de la mise à jour');
    }
  };

  const handleDeleteBook = async (bookId) => {
    try {
      await bookService.deleteBook(bookId);
      await loadBooks();
      await loadStats();
      setSelectedBook(null);
      toast.success('Livre supprimé !');
    } catch (error) {
      console.error('Erreur lors de la suppression du livre:', error);
      toast.error('Erreur lors de la suppression');
    }
  };

  // Gestionnaire pour ouvrir la recherche Open Library
  const handleOpenLibrarySearch = () => {
    setShowOpenLibraryModal(true);
  };

  // Composant Header moderne
  const Header = () => (
    <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          <div className="flex items-center space-x-4">
            <h1 className="text-2xl font-bold text-booktime-600 dark:text-booktime-400">
              📚 BOOKTIME
            </h1>
            {/* Indicateur de recherche active */}
            {searchStats.hasActiveFilters && (
              <div className="hidden sm:flex items-center space-x-2 px-3 py-1 bg-booktime-50 dark:bg-booktime-900/20 rounded-full">
                <span className="text-xs text-booktime-600 dark:text-booktime-400 font-medium">
                  {searchStats.filtered} / {searchStats.total} livres
                </span>
                <button
                  onClick={clearSearch}
                  className="text-booktime-500 hover:text-booktime-600 dark:text-booktime-400 dark:hover:text-booktime-300 text-xs underline"
                >
                  Effacer
                </button>
              </div>
            )}
          </div>
          
          {/* Barre de recherche centrale */}
          <div className="flex-1 max-w-lg mx-4">
            <AdvancedSearchBar
              searchTerm={searchTerm}
              onSearchChange={setSearchTerm}
              books={books}
              filters={filters}
              onFiltersChange={setFilters}
              onOpenLibrarySearch={handleOpenLibrarySearch}
            />
          </div>

          {/* Actions utilisateur */}
          <div className="flex items-center space-x-3">
            <span className="hidden sm:block text-sm text-gray-600 dark:text-gray-400">
              Bonjour, {user?.first_name}
            </span>
            <button
              onClick={() => setShowAddModal(true)}
              className="flex items-center space-x-1 px-4 py-2 text-sm font-medium text-white bg-booktime-600 border border-transparent rounded-md hover:bg-booktime-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-booktime-500 transition-colors"
            >
              <span className="text-sm">➕</span>
              <span className="hidden sm:inline">Ajouter</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );

  // Composant Navigation des onglets
  const TabNavigation = () => (
    <div className="mb-6">
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {['roman', 'bd', 'manga'].map((category) => (
            <button
              key={category}
              onClick={() => setActiveTab(category)}
              className={`py-2 px-1 border-b-2 font-medium text-sm capitalize ${
                activeTab === category
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {category}
            </button>
          ))}
        </nav>
      </div>
      <div className="mt-4">
        <div className="flex space-x-4">
          {['all', 'to_read', 'reading', 'completed'].map((status) => (
            <button
              key={status}
              onClick={() => setActiveStatus(status)}
              className={`px-3 py-1 rounded-full text-sm ${
                activeStatus === status
                  ? 'bg-blue-100 text-blue-800'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              {status === 'all' ? 'Tous' : 
               status === 'to_read' ? 'À lire' :
               status === 'reading' ? 'En cours' : 'Terminés'}
            </button>
          ))}
        </div>
      </div>
    </div>
  );

  // Composant Stats
  const StatsPanel = () => (
    <div className="mb-6 grid grid-cols-2 md:grid-cols-4 gap-4">
      <div className="bg-white p-4 rounded-lg border">
        <h3 className="text-lg font-semibold text-gray-900">
          {stats.total_books || 0}
        </h3>
        <p className="text-gray-600">Total</p>
      </div>
      <div className="bg-white p-4 rounded-lg border">
        <h3 className="text-lg font-semibold text-green-600">
          {stats.completed_books || 0}
        </h3>
        <p className="text-gray-600">Terminés</p>
      </div>
      <div className="bg-white p-4 rounded-lg border">
        <h3 className="text-lg font-semibold text-yellow-600">
          {stats.reading_books || 0}
        </h3>
        <p className="text-gray-600">En cours</p>
      </div>
      <div className="bg-white p-4 rounded-lg border">
        <h3 className="text-lg font-semibold text-blue-600">
          {stats.to_read_books || 0}
        </h3>
        <p className="text-gray-600">À lire</p>
      </div>
    </div>
  );

  // Composant Grille de livres
  const BookGrid = () => {
    if (loading) {
      return (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-gray-200 h-48 rounded-lg animate-pulse"></div>
          ))}
        </div>
      );
    }

    if (filteredBooks.length === 0) {
      return (
        <div className="text-center py-12">
          <p className="text-gray-500">
            Aucun livre trouvé. Ajoutez votre premier livre !
          </p>
        </div>
      );
    }

    return (
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {filteredBooks.map((book) => (
          <div
            key={book.id}
            onClick={() => setSelectedBook(book)}
            className="bg-white rounded-lg border border-gray-200 p-3 cursor-pointer hover:shadow-lg transition-shadow"
          >
            <div className="aspect-[2/3] bg-gray-100 rounded mb-2 flex items-center justify-center">
              {book.cover_url ? (
                <img
                  src={book.cover_url}
                  alt={book.title}
                  className="w-full h-full object-cover rounded"
                />
              ) : (
                <span className="text-4xl">📖</span>
              )}
            </div>
            <h3 className="font-medium text-sm text-gray-900 truncate">
              {book.title}
            </h3>
            <p className="text-xs text-gray-600 truncate">
              {book.author}
            </p>
            <div className="mt-2">
              <span className={`inline-block px-2 py-1 rounded-full text-xs ${
                book.status === 'completed' ? 'bg-green-100 text-green-800' :
                book.status === 'reading' ? 'bg-yellow-100 text-yellow-800' :
                'bg-blue-100 text-blue-800'
              }`}>
                {book.status === 'completed' ? '✅' :
                 book.status === 'reading' ? '📖' : '📚'}
              </span>
            </div>
          </div>
        ))}
      </div>
    );
  };

  // Modal d'ajout simplifié
  const AddBookModal = () => {
    const [formData, setFormData] = useState({
      title: '',
      author: '',
      category: activeTab,
      description: ''
    });

    const handleSubmit = (e) => {
      e.preventDefault();
      if (formData.title && formData.author) {
        handleAddBook(formData);
      }
    };

    if (!showAddModal) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-md">
          <h2 className="text-xl font-bold mb-4 text-gray-900">
            Ajouter un Livre
          </h2>
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Titre *
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({...formData, title: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Auteur *
              </label>
              <input
                type="text"
                value={formData.author}
                onChange={(e) => setFormData({...formData, author: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Catégorie
              </label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({...formData, category: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="roman">Roman</option>
                <option value="bd">BD</option>
                <option value="manga">Manga</option>
              </select>
            </div>
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Annuler
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Ajouter
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  // Modal de détails simplifié
  const BookDetailModal = () => {
    if (!selectedBook) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 w-full max-w-md">
          <h2 className="text-xl font-bold mb-4 text-gray-900">
            {selectedBook.title}
          </h2>
          <p className="text-gray-600 mb-2">
            <strong>Auteur:</strong> {selectedBook.author}
          </p>
          <p className="text-gray-600 mb-2">
            <strong>Catégorie:</strong> {selectedBook.category}
          </p>
          <p className="text-gray-600 mb-4">
            <strong>Statut:</strong> {
              selectedBook.status === 'completed' ? 'Terminé' :
              selectedBook.status === 'reading' ? 'En cours' : 'À lire'
            }
          </p>
          
          <div className="flex justify-between">
            <button
              onClick={() => {
                const newStatus = 
                  selectedBook.status === 'to_read' ? 'reading' :
                  selectedBook.status === 'reading' ? 'completed' : 'to_read';
                handleUpdateBook(selectedBook.id, { status: newStatus });
              }}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
            >
              Changer Statut
            </button>
            <button
              onClick={() => {
                if (window.confirm('Supprimer ce livre ?')) {
                  handleDeleteBook(selectedBook.id);
                }
              }}
              className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
            >
              Supprimer
            </button>
            <button
              onClick={() => setSelectedBook(null)}
              className="px-4 py-2 text-gray-600 hover:text-gray-800"
            >
              Fermer
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <StatsPanel />
        <TabNavigation />
        <BookGrid />
      </main>

      <AddBookModal />
      <BookDetailModal />
    </div>
  );
}

// Auth Wrapper Component
function AuthWrapper() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Chargement...</p>
        </div>
      </div>
    );
  }

  return user ? <AppContent /> : <LoginPage />;
}

// Main App Component
function App() {
  return (
    <AuthProvider>
      <div className="App">
        <AuthWrapper />
        <Toaster 
          position="top-right"
          toastOptions={{
            duration: 3000,
            style: {
              background: '#363636',
              color: '#fff',
            },
          }}
        />
      </div>
    </AuthProvider>
  );
}

export default App;