import React, { useState, useEffect, useContext, createContext } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import toast, { Toaster } from 'react-hot-toast';

// Import des contexts
import { ThemeProvider, useTheme } from './contexts/ThemeContext';

// Import des hooks et composants
import { useAdvancedSearch } from './hooks/useAdvancedSearch';
import AdvancedSearchBar from './components/AdvancedSearchBar';
import OpenLibrarySearch from './components/OpenLibrarySearch';
import BookDetailPage from './components/BookDetailPage';
import AuthorDetailPage from './components/AuthorDetailPage';
import OpenLibraryBookPage from './components/OpenLibraryBookPage';
import OpenLibraryAuthorPage from './components/OpenLibraryAuthorPage';
import SearchResultsPage from './components/SearchResultsPage';

import './App.css';

// Service d'authentification simple
class AuthService {
  constructor() {
    this.backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
  }

  async login(firstName, lastName) {
    try {
      const response = await fetch(`${this.backendUrl}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ first_name: firstName, last_name: lastName })
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        return { success: true, user: data.user };
      } else {
        const error = await response.json();
        return { success: false, error: error.error };
      }
    } catch (error) {
      return { success: false, error: 'Erreur de connexion' };
    }
  }

  async register(firstName, lastName) {
    try {
      const response = await fetch(`${this.backendUrl}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ first_name: firstName, last_name: lastName })
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        return { success: true, user: data.user };
      } else {
        const error = await response.json();
        return { success: false, error: error.error };
      }
    } catch (error) {
      return { success: false, error: 'Erreur de création de compte' };
    }
  }

  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }

  getCurrentUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
  }

  isAuthenticated() {
    return localStorage.getItem('token') !== null;
  }
}

// Service de livres
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

  async getBooks() {
    const response = await fetch(`${this.backendUrl}/api/books`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('Failed to fetch books');
    }

    return response.json();
  }

  async getBookDetails(bookId) {
    const response = await fetch(`${this.backendUrl}/api/books/${bookId}`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('Failed to fetch book details');
    }

    return response.json();
  }

  async getAuthorDetails(authorName) {
    const encodedAuthorName = encodeURIComponent(authorName);
    const response = await fetch(`${this.backendUrl}/api/authors/${encodedAuthorName}`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('Failed to fetch author details');
    }

    return response.json();
  }

  async getAuthorBooks(authorName) {
    const encodedAuthorName = encodeURIComponent(authorName);
    const response = await fetch(`${this.backendUrl}/api/authors/${encodedAuthorName}/books`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('Failed to fetch author books');
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

  async searchUniversal(query, options = {}) {
    const params = new URLSearchParams();
    params.append('q', query);
    
    if (options.limit) params.append('limit', options.limit);
    if (options.category) params.append('category', options.category);

    const response = await fetch(`${this.backendUrl}/api/openlibrary/search-universal?${params}`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('Failed to search OpenLibrary universally');
    }

    return response.json();
  }
}

// Context d'authentification
const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const authService = new AuthService();

  useEffect(() => {
    // Vérifier si l'utilisateur est connecté
    const currentUser = authService.getCurrentUser();
    setUser(currentUser);
    setLoading(false);
  }, []);

  const login = async (firstName, lastName) => {
    const result = await authService.login(firstName, lastName);
    if (result.success) {
      setUser(result.user);
    }
    return result;
  };

  const register = async (firstName, lastName) => {
    const result = await authService.register(firstName, lastName);
    if (result.success) {
      setUser(result.user);
    }
    return result;
  };

  const logout = () => {
    authService.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

const bookService = new BookService();

// Login Component
function LoginPage() {
  const { login, register } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    let result;
    if (isLogin) {
      result = await login(formData.firstName, formData.lastName);
    } else {
      result = await register(formData.firstName, formData.lastName);
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">📚 BOOKTIME</h1>
          <p className="text-gray-600 dark:text-gray-400">Gérez votre bibliothèque personnelle</p>
        </div>

        <div className="flex mb-6 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
          <button
            onClick={() => setIsLogin(true)}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${
              isLogin ? 'bg-white dark:bg-gray-600 text-blue-600 dark:text-blue-400 shadow-sm' : 'text-gray-600 dark:text-gray-400'
            }`}
          >
            Connexion
          </button>
          <button
            onClick={() => setIsLogin(false)}
            className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${
              !isLogin ? 'bg-white dark:bg-gray-600 text-blue-600 dark:text-blue-400 shadow-sm' : 'text-gray-600 dark:text-gray-400'
            }`}
          >
            Inscription
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Prénom
            </label>
            <input
              type="text"
              name="firstName"
              value={formData.firstName}
              onChange={handleInputChange}
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Nom
            </label>
            <input
              type="text"
              name="lastName"
              value={formData.lastName}
              onChange={handleInputChange}
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
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

// Profile Modal Component
function ProfileModal({ isOpen, onClose }) {
  const { user, logout } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isOpen) {
      loadStats();
    }
  }, [isOpen]);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await bookService.getStats();
      setStats(data);
    } catch (error) {
      console.error('Erreur lors du chargement des statistiques:', error);
      toast.error('Erreur lors du chargement des statistiques');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    onClose();
    toast.success('Déconnexion réussie');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-md max-h-90vh overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">Profil</h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                {user?.first_name} {user?.last_name}
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              ✕
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Statistiques */}
          <div className="mb-8">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
              📊 Mes Statistiques
            </h3>
            
            {loading ? (
              <div className="space-y-3">
                {[...Array(4)].map((_, i) => (
                  <div key={i} className="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                {/* Stats générales */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                      {stats.total_books || 0}
                    </div>
                    <div className="text-sm text-blue-600 dark:text-blue-400">Total</div>
                  </div>
                  <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                      {stats.completed_books || 0}
                    </div>
                    <div className="text-sm text-green-600 dark:text-green-400">Terminés</div>
                  </div>
                </div>

                {/* Stats par catégorie */}
                <div className="space-y-3">
                  <h4 className="font-medium text-gray-900 dark:text-white">Par catégorie :</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <span className="flex items-center text-gray-700 dark:text-gray-300">
                        📚 Romans
                      </span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {stats.categories?.roman || 0}
                      </span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <span className="flex items-center text-gray-700 dark:text-gray-300">
                        🎨 Bande dessinée
                      </span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {stats.categories?.bd || 0}
                      </span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <span className="flex items-center text-gray-700 dark:text-gray-300">
                        🇯🇵 Mangas
                      </span>
                      <span className="font-medium text-gray-900 dark:text-white">
                        {stats.categories?.manga || 0}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Stats additionnelles */}
                <div className="space-y-2">
                  <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <span className="flex items-center text-gray-700 dark:text-gray-300">
                      👥 Auteurs différents
                    </span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {stats.authors_count || 0}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <span className="flex items-center text-gray-700 dark:text-gray-300">
                      📖 Sagas
                    </span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {stats.sagas_count || 0}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <span className="flex items-center text-gray-700 dark:text-gray-300">
                      📚 En cours
                    </span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {stats.reading_books || 0}
                    </span>
                  </div>
                  <div className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <span className="flex items-center text-gray-700 dark:text-gray-300">
                      📋 À lire
                    </span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {stats.to_read_books || 0}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Paramètres */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
              ⚙️ Paramètres
            </h3>
            
            <div className="space-y-4">
              {/* Mode sombre */}
              <div className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                <div>
                  <span className="font-medium text-gray-900 dark:text-white">Mode sombre</span>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Basculer entre thème clair et sombre
                  </p>
                </div>
                <button
                  onClick={toggleTheme}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                    isDark ? 'bg-blue-600' : 'bg-gray-200'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      isDark ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={handleLogout}
              className="w-full bg-red-600 hover:bg-red-700 text-white font-medium py-3 px-4 rounded-lg transition-colors"
            >
              Se déconnecter
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Main App Content
function AppContent() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [books, setBooks] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('roman');
  const [activeStatus, setActiveStatus] = useState('all');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showOpenLibraryModal, setShowOpenLibraryModal] = useState(false);
  const [selectedBook, setSelectedBook] = useState(null);
  const [showProfileModal, setShowProfileModal] = useState(false);

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

  // Navigation vers fiche livre
  const handleBookClick = (book) => {
    navigate(`/livre/${book.id}`);
  };

  // Navigation vers fiche auteur
  const handleAuthorClick = (authorName) => {
    navigate(`/auteur/${encodeURIComponent(authorName)}`);
  };

  // Gestionnaire pour ouvrir la recherche Open Library
  const handleOpenLibrarySearch = () => {
    setShowOpenLibraryModal(true);
  };

  // Composant Header moderne avec bouton profil
  const Header = () => (
    <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          <div className="flex items-center space-x-4">
            <button 
              onClick={() => navigate('/')}
              className="text-2xl font-bold text-blue-600 dark:text-blue-400 hover:opacity-80 transition-opacity"
            >
              📚 BOOKTIME
            </button>
            {/* Indicateur de recherche active */}
            {searchStats.hasActiveFilters && (
              <div className="hidden sm:flex items-center space-x-2 px-3 py-1 bg-blue-50 dark:bg-blue-900/20 rounded-full">
                <span className="text-xs text-blue-600 dark:text-blue-400 font-medium">
                  {searchStats.filtered} / {searchStats.total} livres
                </span>
                <button
                  onClick={clearSearch}
                  className="text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-300 text-xs underline"
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
            {/* Bouton Ajouter un livre */}
            <button
              onClick={() => setShowAddModal(true)}
              className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
            >
              <span className="text-lg">+</span>
              <span className="hidden sm:block">Ajouter</span>
            </button>
            
            {/* Bouton Profil */}
            <button
              onClick={() => setShowProfileModal(true)}
              className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors profile-button"
            >
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-medium text-sm">
                {user?.first_name?.charAt(0).toUpperCase()}{user?.last_name?.charAt(0).toUpperCase()}
              </div>
              <span className="hidden sm:block">Profil</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );

  // Composant Navigation des onglets
  const TabNavigation = () => (
    <div className="mb-6">
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-12">
          {[
            { key: 'roman', label: 'Roman' },
            { key: 'bd', label: 'Bande Dessinée' },
            { key: 'manga', label: 'Manga' }
          ].map((category) => (
            <button
              key={category.key}
              onClick={() => setActiveTab(category.key)}
              className={`py-3 px-2 border-b-2 font-medium text-lg ${
                activeTab === category.key
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              {category.label}
            </button>
          ))}
        </nav>
      </div>
    </div>
  );

  // Composant Grille de livres réorganisée
  const BookGrid = () => {
    if (loading) {
      return (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="bg-gray-200 dark:bg-gray-700 h-48 rounded-lg animate-pulse"></div>
          ))}
        </div>
      );
    }

    // Séparer les livres par statut et trier par année de publication
    const readingBooks = finalFilteredBooks
      .filter(book => book.status === 'reading')
      .sort((a, b) => (a.publication_year || 0) - (b.publication_year || 0));
    
    const toReadBooks = finalFilteredBooks
      .filter(book => book.status === 'to_read')
      .sort((a, b) => (a.publication_year || 0) - (b.publication_year || 0));

    const renderBookSection = (books, title) => {
      if (books.length === 0) return null;

      return (
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
            {title === 'En cours de lecture' ? '📖' : '📚'} {title}
            <span className="ml-2 text-sm font-normal text-gray-500 dark:text-gray-400">
              ({books.length} livre{books.length > 1 ? 's' : ''})
            </span>
          </h2>
          <div className="grid grid-cols-3 md:grid-cols-5 lg:grid-cols-8 gap-3">
            {books.map((book) => (
              <div
                key={book.id}
                onClick={() => handleBookClick(book)}
                className="cursor-pointer hover:shadow-lg transition-all hover:scale-105 group"
              >
                <div className="aspect-[2/3] bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center overflow-hidden shadow-md">
                  {book.cover_url ? (
                    <img
                      src={book.cover_url}
                      alt={book.title}
                      className="w-full h-full object-cover rounded-lg group-hover:scale-110 transition-transform duration-300"
                    />
                  ) : (
                    <span className="text-4xl">📖</span>
                  )}
                </div>
                <div className="mt-2 text-center">
                  <p className="text-xs text-gray-600 dark:text-gray-400 truncate">{book.title}</p>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleAuthorClick(book.author);
                    }}
                    className="text-xs text-blue-600 dark:text-blue-400 hover:underline truncate block"
                  >
                    {book.author}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    };

    if (finalFilteredBooks.length === 0) {
      return (
        <div className="text-center py-12">
          <div className="max-w-md mx-auto">
            <span className="text-6xl mb-4 block">🔍</span>
            <p className="text-gray-500 dark:text-gray-400 text-lg mb-2">
              {searchStats.hasActiveFilters ? 'Aucun livre trouvé' : 'Aucun livre dans votre collection'}
            </p>
            <p className="text-gray-400 dark:text-gray-500 text-sm mb-4">
              {searchStats.hasActiveFilters 
                ? 'Essayez de modifier vos critères de recherche' 
                : 'Ajoutez votre premier livre pour commencer !'}
            </p>
            {searchStats.hasActiveFilters && (
              <button
                onClick={clearSearch}
                className="px-4 py-2 text-sm bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors"
              >
                Effacer la recherche
              </button>
            )}
          </div>
        </div>
      );
    }

    return (
      <div>
        {/* Résumé des résultats */}
        {searchStats.hasActiveFilters && (
          <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border dark:border-gray-700">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">
                <strong>{finalFilteredBooks.length}</strong> livre{finalFilteredBooks.length > 1 ? 's' : ''} trouvé{finalFilteredBooks.length > 1 ? 's' : ''}
                {searchStats.hiddenCount > 0 && (
                  <span className="ml-2 text-gray-500 dark:text-gray-500">
                    ({searchStats.hiddenCount} masqué{searchStats.hiddenCount > 1 ? 's' : ''})
                  </span>
                )}
              </span>
              <button
                onClick={clearSearch}
                className="text-xs text-blue-500 hover:text-blue-600 dark:text-blue-400 dark:hover:text-blue-300 underline"
              >
                Effacer les filtres
              </button>
            </div>
          </div>
        )}

        {/* Livres en cours de lecture */}
        {renderBookSection(readingBooks, 'En cours de lecture')}

        {/* Livres à lire */}
        {renderBookSection(toReadBooks, 'À lire')}
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
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
          <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
            Ajouter un Livre
          </h2>
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Titre *
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData({...formData, title: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                required
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Auteur *
              </label>
              <input
                type="text"
                value={formData.author}
                onChange={(e) => setFormData({...formData, author: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                required
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Catégorie
              </label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({...formData, category: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="roman">Roman</option>
                <option value="bd">Bande dessinée</option>
                <option value="manga">Manga</option>
              </select>
            </div>
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setShowAddModal(false)}
                className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
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

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <TabNavigation />
        <BookGrid />
      </main>

      <AddBookModal />
      <ProfileModal isOpen={showProfileModal} onClose={() => setShowProfileModal(false)} />
      
      {/* Modal OpenLibrary */}
      {showOpenLibraryModal && (
        <OpenLibrarySearch
          onImport={handleAddBook}
          onClose={() => setShowOpenLibraryModal(false)}
          defaultCategory={activeTab}
        />
      )}
      
      {/* Modal OpenLibrary */}
      {showOpenLibraryModal && (
        <OpenLibrarySearch
          onImport={handleAddBook}
          onClose={() => setShowOpenLibraryModal(false)}
          defaultCategory={activeTab}
        />
      )}
    </div>
  );
}

// Auth Wrapper Component
function AuthWrapper() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Chargement...</p>
        </div>
      </div>
    );
  }

  return user ? (
    <Routes>
      <Route path="/" element={<AppContent />} />
      <Route path="/livre/:bookId" element={<BookDetailPage />} />
      <Route path="/livre/ol/:workKey" element={<OpenLibraryBookPage />} />
      <Route path="/auteur/:authorName" element={<AuthorDetailPage />} />
      <Route path="/auteur/ol/:authorName" element={<OpenLibraryAuthorPage />} />
    </Routes>
  ) : <LoginPage />;
}

// Main App Component
function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Router>
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
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;