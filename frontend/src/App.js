// Imports
import React, { createContext, useState, useContext, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import { toast, Toaster } from 'react-hot-toast';

// Context imports
import { ThemeProvider, useTheme } from './contexts/ThemeContext';

// Service imports
import { bookService } from './services/bookService';

// Component imports
import AdvancedSearchBar from './components/AdvancedSearchBar';
import BookDetailModal from './components/BookDetailModal';
import GroupedSearchResults from './components/GroupedSearchResults';
import { useAdvancedSearch } from './hooks/useAdvancedSearch';
import { useGroupedSearch } from './hooks/useGroupedSearch';

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
        return { success: false, error: error.detail || 'Erreur de connexion' };
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
        return { success: false, error: error.detail || 'Erreur d\'inscription' };
      }
    } catch (error) {
      return { success: false, error: 'Erreur de connexion' };
    }
  }

  getCurrentUser() {
    try {
      const userString = localStorage.getItem('user');
      const token = localStorage.getItem('token');
      
      if (userString && token) {
        return JSON.parse(userString);
      }
      return null;
    } catch (error) {
      return null;
    }
  }

  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }
}

// Auth Context
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
    if (currentUser) {
      setUser(currentUser);
    }
    setLoading(false);
  }, []);

  const login = async (firstName, lastName) => {
    try {
      const result = await authService.login(firstName, lastName);
      if (result.success) {
        setUser(result.user);
        // Force re-render and state update
        setTimeout(() => {
          window.location.reload(); // Temporary fix to ensure state sync
        }, 100);
      }
      return result;
    } catch (error) {
      console.error('Login error:', error);
      return { success: false, error: 'Erreur de connexion' };
    }
  };

  const register = async (firstName, lastName) => {
    try {
      const result = await authService.register(firstName, lastName);
      if (result.success) {
        setUser(result.user);
        // Force re-render and state update
        setTimeout(() => {
          window.location.reload(); // Temporary fix to ensure state sync
        }, 100);
      }
      return result;
    } catch (error) {
      console.error('Register error:', error);
      return { success: false, error: 'Erreur d\'inscription' };
    }
  };

  const logout = () => {
    authService.logout();
    setUser(null);
    window.location.reload(); // Ensure clean logout
  };

  return (
    <AuthContext.Provider value={{ user, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Login Page Component
function LoginPage() {
  const { login, register } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.firstName || !formData.lastName) return;

    setLoading(true);
    try {
      let result;
      if (isLogin) {
        result = await login(formData.firstName, formData.lastName);
      } else {
        result = await register(formData.firstName, formData.lastName);
      }

      if (result.success) {
        toast.success(isLogin ? 'Connexion réussie !' : 'Inscription réussie !');
      } else {
        toast.error(result.error || 'Une erreur est survenue');
      }
    } catch (error) {
      toast.error('Erreur de connexion');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <div className="flex justify-center mb-6">
            <div className="w-16 h-16 bg-green-600 rounded-2xl flex items-center justify-center text-white text-2xl font-bold shadow-lg">
              🐝
            </div>
          </div>
          <h2 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">
            BookTime
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Votre bibliothèque personnelle
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 shadow-2xl rounded-2xl p-8 space-y-6 border dark:border-gray-700">
          <div className="flex mb-6 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
            <button
              onClick={() => setIsLogin(true)}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${
                isLogin ? 'bg-white dark:bg-gray-600 text-green-600 dark:text-green-400 shadow-sm' : 'text-gray-600 dark:text-gray-400'
              }`}
            >
              Connexion
            </button>
            <button
              onClick={() => setIsLogin(false)}
              className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-all ${
                !isLogin ? 'bg-white dark:bg-gray-600 text-green-600 dark:text-green-400 shadow-sm' : 'text-gray-600 dark:text-gray-400'
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
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
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
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-green-600 text-white py-3 px-4 rounded-lg hover:bg-green-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Chargement...' : (isLogin ? 'Se connecter' : 'Créer un compte')}
            </button>
          </form>
        </div>
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
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-md max-h-[80vh] flex flex-col">
        <div className="flex-shrink-0 p-4 border-b border-gray-200 dark:border-gray-700">
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

        <div className="flex-1 overflow-y-auto p-4">
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
              📊 Mes Statistiques
            </h3>
            
            {loading ? (
              <div className="space-y-2">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="h-3 bg-gray-200 dark:bg-gray-700 rounded animate-pulse"></div>
                ))}
              </div>
            ) : (
              <div className="space-y-3">
                <div className="grid grid-cols-3 gap-2">
                  <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 text-center">
                    <div className="text-lg font-bold text-blue-600 dark:text-blue-400">
                      {stats.total_books || 0}
                    </div>
                    <div className="text-xs text-blue-600 dark:text-blue-400">Total</div>
                  </div>
                  <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 text-center">
                    <div className="text-lg font-bold text-green-600 dark:text-green-400">
                      {stats.completed_books || 0}
                    </div>
                    <div className="text-xs text-green-600 dark:text-green-400">Terminés</div>
                  </div>
                  <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-3 text-center">
                    <div className="text-lg font-bold text-orange-600 dark:text-orange-400">
                      {stats.reading_books || 0}
                    </div>
                    <div className="text-xs text-orange-600 dark:text-orange-400">En cours</div>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
              ⚙️ Paramètres
            </h3>
            
            <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
              <div>
                <span className="font-medium text-gray-900 dark:text-white text-sm">Mode sombre</span>
                <p className="text-xs text-gray-600 dark:text-gray-400">
                  Basculer entre thème clair et sombre
                </p>
              </div>
              <button
                onClick={toggleTheme}
                className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                  isDark ? 'bg-blue-600' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${
                    isDark ? 'translate-x-5' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        <div className="flex-shrink-0 p-4 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={handleLogout}
            className="w-full bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg transition-colors text-sm"
          >
            Se déconnecter
          </button>
        </div>
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
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedBook, setSelectedBook] = useState(null);
  const [showBookModal, setShowBookModal] = useState(false);

  // États pour la recherche Open Library
  const [openLibraryResults, setOpenLibraryResults] = useState([]);
  const [isSearchMode, setIsSearchMode] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [lastSearchTerm, setLastSearchTerm] = useState('');
  const [useGroupedSearchMode, setUseGroupedSearchMode] = useState(false);

  // Hook de recherche avancée
  const {
    searchTerm,
    setSearchTerm,
    filters,
    setFilters,
    filteredBooks,
    searchStats,
    clearSearch
  } = useAdvancedSearch(books);

  // Hook de recherche groupée
  const {
    searchTerm: groupedSearchTerm,
    setSearchTerm: setGroupedSearchTerm,
    groupedResults,
    isLoading: groupedSearchLoading,
    searchStats: groupedSearchStats,
    clearSearch: clearGroupedSearch,
    hasResults: hasGroupedResults
  } = useGroupedSearch();

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

  // Fonction pour rechercher dans Open Library
  const searchOpenLibrary = async (query) => {
    if (!query.trim()) return;
    
    try {
      setSearchLoading(true);
      setIsSearchMode(true);
      setLastSearchTerm(query);
      
      const token = localStorage.getItem('token');
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const response = await fetch(`${backendUrl}/api/openlibrary/search?q=${encodeURIComponent(query)}&limit=20`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        
        // Marquer les livres déjà possédés
        const resultsWithOwnership = data.books.map(book => {
          const isOwned = books.some(localBook => 
            localBook.title.toLowerCase() === book.title.toLowerCase() &&
            localBook.author.toLowerCase() === book.author.toLowerCase()
          );
          
          return {
            ...book,
            isFromOpenLibrary: true,
            isOwned: isOwned,
            id: `ol_${book.ol_key}`
          };
        });
        
        setOpenLibraryResults(resultsWithOwnership);
        toast.success(`${data.books.length} livres trouvés sur Open Library`);
      } else {
        toast.error('Erreur lors de la recherche Open Library');
      }
    } catch (error) {
      console.error('Erreur recherche Open Library:', error);
      toast.error('Erreur lors de la recherche Open Library');
    } finally {
      setSearchLoading(false);
    }
  };

  // Fonction pour revenir à la bibliothèque locale
  const backToLibrary = () => {
    setIsSearchMode(false);
    setOpenLibraryResults([]);
    setLastSearchTerm('');
    setUseGroupedSearchMode(false);
    clearSearch();
    clearGroupedSearch();
  };



  // Fonction pour ajouter un livre depuis Open Library
  const handleAddFromOpenLibrary = async (openLibraryBook) => {
    try {
      const token = localStorage.getItem('token');
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const response = await fetch(`${backendUrl}/api/openlibrary/import`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ol_key: openLibraryBook.ol_key,
          category: openLibraryBook.category || activeTab
        })
      });

      if (response.ok) {
        await loadBooks();
        await loadStats();
        toast.success(`"${openLibraryBook.title}" ajouté à votre collection !`);
        
        // Mettre à jour le statut de possession dans les résultats
        setOpenLibraryResults(prev => 
          prev.map(book => 
            book.ol_key === openLibraryBook.ol_key 
              ? { ...book, isOwned: true }
              : book
          )
        );
      } else {
        const error = await response.json();
        if (response.status === 409) {
          toast.error('Ce livre est déjà dans votre collection');
        } else {
          toast.error(error.detail || 'Erreur lors de l\'ajout du livre');
        }
      }
    } catch (error) {
      console.error('Erreur ajout livre:', error);
      toast.error('Erreur lors de l\'ajout du livre');
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

  const handleBookClick = (book) => {
    setSelectedBook(book);
    setShowBookModal(true);
  };

  const handleUpdateBook = async (bookData) => {
    try {
      await bookService.updateBook(selectedBook.id, bookData);
      await loadBooks();
      await loadStats();
      setSelectedBook(null);
      setShowBookModal(false);
      toast.success('Livre mis à jour !');
    } catch (error) {
      console.error('Erreur lors de la mise à jour du livre:', error);
      toast.error('Erreur lors de la mise à jour du livre');
    }
  };

  const handleDeleteBook = async (bookId) => {
    try {
      await bookService.deleteBook(bookId);
      await loadBooks();
      await loadStats();
      setSelectedBook(null);
      setShowBookModal(false);
      toast.success('Livre supprimé !');
    } catch (error) {
      console.error('Erreur lors de la suppression du livre:', error);
      toast.error('Erreur lors de la suppression du livre');
    }
  };

  // Fonction avancée de calcul de la pertinence d'un livre par rapport au terme de recherche
  const calculateRelevanceScore = (book, searchTerm) => {
    if (!searchTerm || !searchTerm.trim()) return 0;
    
    const term = searchTerm.toLowerCase().trim();
    const termWords = term.split(/\s+/).filter(word => word.length > 2); // Mots de plus de 2 caractères
    
    // Normalisation des champs de recherche
    const title = (book.title || '').toLowerCase();
    const author = (book.author || '').toLowerCase();
    const description = (book.description || '').toLowerCase();
    const genre = (book.genre || '').toLowerCase();
    const saga = (book.saga || '').toLowerCase();
    const publisher = (book.publisher || '').toLowerCase();
    const isbn = (book.isbn || '').toLowerCase();
    
    let score = 0;
    
    // === CORRESPONDANCES EXACTES (Score très élevé) ===
    
    // Correspondance exacte du titre complet
    if (title === term) score += 1000;
    
    // Correspondance exacte de l'auteur complet
    if (author === term) score += 900;
    
    // Correspondance exacte de la saga
    if (saga && saga === term) score += 800;
    
    // === CORRESPONDANCES PARTIELLES DU TITRE (Score élevé) ===
    
    // Titre commence par le terme
    if (title.startsWith(term)) score += 700;
    
    // Titre contient le terme comme mot entier
    if (title.includes(` ${term} `) || title.includes(`${term} `) || title.includes(` ${term}`)) score += 600;
    
    // Titre contient le terme avec délimiteurs
    if (title.includes(`-${term}-`) || title.includes(`(${term})`) || title.includes(`[${term}]`)) score += 550;
    
    // Titre contient le terme n'importe où
    if (title.includes(term)) score += 400;
    
    // === CORRESPONDANCES PARTIELLES DE L'AUTEUR (Score élevé) ===
    
    // Auteur commence par le terme
    if (author.startsWith(term)) score += 650;
    
    // Auteur contient le terme comme mot entier
    if (author.includes(` ${term} `) || author.includes(`${term} `) || author.includes(` ${term}`)) score += 500;
    
    // Auteur contient le terme n'importe où
    if (author.includes(term)) score += 300;
    
    // === CORRESPONDANCES PAR MOTS MULTIPLES ===
    
    if (termWords.length > 1) {
      let multiWordScore = 0;
      let matchedWords = 0;
      
      termWords.forEach(word => {
        // Correspondances dans le titre
        if (title.includes(word)) {
          multiWordScore += 50;
          matchedWords++;
        }
        
        // Correspondances dans l'auteur
        if (author.includes(word)) {
          multiWordScore += 40;
          matchedWords++;
        }
        
        // Correspondances dans la saga
        if (saga && saga.includes(word)) {
          multiWordScore += 30;
          matchedWords++;
        }
      });
      
      // Bonus si plusieurs mots correspondent
      if (matchedWords > 1) {
        multiWordScore *= (1 + (matchedWords - 1) * 0.5); // Bonus exponentiel
      }
      
      score += multiWordScore;
    }
    
    // === CORRESPONDANCES DANS D'AUTRES CHAMPS ===
    
    // Correspondances dans la saga
    if (saga && saga.includes(term)) {
      if (saga.startsWith(term)) score += 350;
      else score += 200;
    }
    
    // Correspondances dans la description
    if (description.includes(term)) score += 100;
    
    // Correspondances dans le genre
    if (genre.includes(term)) score += 80;
    
    // Correspondances dans l'éditeur
    if (publisher.includes(term)) score += 60;
    
    // Correspondances dans l'ISBN
    if (isbn.includes(term.replace(/[-\s]/g, ''))) score += 150;
    
    // === BONUS ET MALUS ===
    
    // Bonus important pour les livres de la bibliothèque locale
    if (!book.isFromOpenLibrary) {
      score += 100; // Priorité aux livres possédés
    }
    
    // Bonus pour les livres déjà possédés d'Open Library
    if (book.isFromOpenLibrary && book.isOwned) {
      score += 80;
    }
    
    // Bonus pour la qualité des métadonnées
    if (book.isFromOpenLibrary) {
      // Livres récents
      if (book.first_publish_year && book.first_publish_year > 2000) score += 10;
      
      // Livres avec couverture
      if (book.cover_url) score += 15;
      
      // Livres avec nombre de pages raisonnable
      if (book.number_of_pages && book.number_of_pages > 50 && book.number_of_pages < 2000) score += 10;
      
      // Livres avec description
      if (book.description && book.description.length > 50) score += 10;
    }
    
    // Malus pour les livres avec métadonnées manquantes
    if (!book.author || book.author.trim() === '') score -= 50;
    if (!book.title || book.title.trim() === '') score -= 100;
    
    // Malus pour les livres très anciens avec peu de pertinence
    if (book.first_publish_year && book.first_publish_year < 1900 && score < 100) score -= 30;
    
    // Malus pour les livres sans couverture (moins attrayants visuellement)
    if (book.isFromOpenLibrary && !book.cover_url) score -= 10;
    
    // === BONUS SPÉCIAUX SELON LE CONTEXTE ===
    
    // Bonus pour les correspondances de langue cohérente
    if (term.match(/[àáâäéèêëïîôöùûüç]/)) { // Caractères français détectés
      if (description.includes('français') || description.includes('france')) score += 20;
    }
    
    // Bonus pour les séries populaires
    const popularSeries = ['harry potter', 'one piece', 'naruto', 'astérix', 'tintin', 'dragon ball'];
    if (popularSeries.some(series => title.includes(series) || saga.includes(series))) {
      score += 25;
    }
    
    // Score final avec minimum à 0
    return Math.max(0, Math.round(score));
  };

  // Fonction pour obtenir le niveau de pertinence d'un livre
  const getRelevanceLevel = (score) => {
    if (score >= 800) return { level: 'excellent', label: 'Très pertinent', color: 'bg-green-500', icon: '🎯' };
    if (score >= 400) return { level: 'good', label: 'Pertinent', color: 'bg-blue-500', icon: '✨' };
    if (score >= 100) return { level: 'moderate', label: 'Moyennement pertinent', color: 'bg-yellow-500', icon: '👁️' };
    if (score >= 50) return { level: 'low', label: 'Peu pertinent', color: 'bg-orange-500', icon: '🔍' };
    return { level: 'minimal', label: 'Faiblement pertinent', color: 'bg-gray-500', icon: '📄' };
  };

  // Combiner et trier les livres locaux et Open Library selon le mode et la pertinence
  const displayedBooks = isSearchMode 
    ? [
        // Combiner tous les livres
        ...filteredBooks.filter(book => book.category === activeTab),
        ...openLibraryResults.filter(book => 
          !book.category || book.category === activeTab || activeTab === ''
        )
      ].map(book => ({
        ...book,
        relevanceScore: calculateRelevanceScore(book, lastSearchTerm),
        relevanceInfo: getRelevanceLevel(calculateRelevanceScore(book, lastSearchTerm))
      }))
      .sort((a, b) => {
        // 1. Trier par score de pertinence décroissant (priorité principale)
        if (a.relevanceScore !== b.relevanceScore) {
          return b.relevanceScore - a.relevanceScore;
        }
        
        // 2. En cas d'égalité de score, prioriser les livres locaux
        if (a.isFromOpenLibrary !== b.isFromOpenLibrary) {
          return a.isFromOpenLibrary ? 1 : -1;
        }
        
        // 3. Pour les livres Open Library, prioriser ceux déjà possédés
        if (a.isFromOpenLibrary && b.isFromOpenLibrary) {
          if (a.isOwned !== b.isOwned) {
            return a.isOwned ? -1 : 1;
          }
        }
        
        // 4. Trier par qualité des métadonnées (livres avec plus d'infos en premier)
        const qualityScoreA = (a.cover_url ? 10 : 0) + (a.description?.length > 100 ? 5 : 0) + (a.first_publish_year ? 3 : 0);
        const qualityScoreB = (b.cover_url ? 10 : 0) + (b.description?.length > 100 ? 5 : 0) + (b.first_publish_year ? 3 : 0);
        
        if (qualityScoreA !== qualityScoreB) {
          return qualityScoreB - qualityScoreA;
        }
        
        // 5. Trier par année de publication (plus récent en premier pour les livres de qualité égale)
        if (a.first_publish_year && b.first_publish_year) {
          return b.first_publish_year - a.first_publish_year;
        }
        
        // 6. Finalement, trier par titre alphabétique
        return (a.title || '').localeCompare(b.title || '', 'fr', { numeric: true });
      })
      // Filtrer les résultats avec un score minimum pour éviter le bruit
      .filter(book => !lastSearchTerm || book.relevanceScore >= 10)
    : filteredBooks.filter(book => book.category === activeTab);

  // Header Component
  const Header = () => (
    <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          <div className="flex items-center space-x-3 text-2xl font-bold text-green-600 dark:text-green-400">
            <div className="w-10 h-10 bg-green-600 rounded-lg flex items-center justify-center text-white text-xl">
              🐝
            </div>
            BookTime
          </div>
          
          <div className="flex items-center space-x-3">
            <button
              onClick={() => setShowProfileModal(true)}
              className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors"
            >
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-medium text-sm">
                {user?.first_name?.charAt(0).toUpperCase()}{user?.last_name?.charAt(0).toUpperCase()}
              </div>
              <span>Profil</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );

  // Tab Navigation Component
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
                  ? 'border-green-500 text-green-600 dark:text-green-400'
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

  // Add Book Modal
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

  // Book Grid Component
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

    if (displayedBooks.length === 0) {
      return (
        <div className="text-center py-12">
          <div className="max-w-md mx-auto">
            <span className="text-6xl mb-4 block">📚</span>
            {searchStats.hasActiveFilters ? (
              <>
                <p className="text-gray-500 dark:text-gray-400 text-lg mb-2">
                  Aucun livre trouvé
                </p>
                <p className="text-gray-400 dark:text-gray-500 text-sm mb-4">
                  Essayez d'ajuster vos critères de recherche
                </p>
                <button
                  onClick={clearSearch}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                >
                  Effacer les filtres
                </button>
              </>
            ) : (
              <>
                <p className="text-gray-500 dark:text-gray-400 text-lg mb-2">
                  Aucun livre dans cette catégorie
                </p>
                <p className="text-gray-400 dark:text-gray-500 text-sm mb-4">
                  Ajoutez votre premier livre pour commencer !
                </p>
              </>
            )}
          </div>
        </div>
      );
    }

    return (
      <div className="grid grid-cols-3 md:grid-cols-5 lg:grid-cols-8 gap-3">
        {displayedBooks.map((book) => (
          <div
            key={book.id}
            className="cursor-pointer hover:shadow-lg transition-all hover:scale-105 group relative"
            onClick={() => handleBookClick(book)}
          >
            {/* Badge de pertinence (uniquement en mode recherche) */}
            {isSearchMode && book.relevanceInfo && book.relevanceScore > 50 && (
              <div className="absolute top-1 left-1 z-10">
                <div 
                  className={`${book.relevanceInfo.color} text-white text-xs px-1.5 py-0.5 rounded-full flex items-center opacity-90`}
                  title={`${book.relevanceInfo.label} (Score: ${book.relevanceScore})`}
                >
                  <span className="mr-0.5">{book.relevanceInfo.icon}</span>
                  <span className="font-medium">{book.relevanceScore}</span>
                </div>
              </div>
            )}
            
            {/* Badge pour les livres Open Library */}
            {book.isFromOpenLibrary && (
              <div className="absolute top-1 right-1 z-10">
                {book.isOwned ? (
                  <div className="bg-green-500 text-white text-xs px-1.5 py-0.5 rounded-full flex items-center">
                    ✓
                  </div>
                ) : (
                  <div className="bg-blue-500 text-white text-xs px-1.5 py-0.5 rounded-full flex items-center">
                    +
                  </div>
                )}
              </div>
            )}
            
            <div className={`aspect-[2/3] bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center overflow-hidden shadow-md ${
              book.isFromOpenLibrary && !book.isOwned ? 'ring-2 ring-blue-200 dark:ring-blue-800' : ''
            } ${
              isSearchMode && book.relevanceInfo?.level === 'excellent' ? 'ring-2 ring-green-300 dark:ring-green-600' : ''
            } ${
              isSearchMode && book.relevanceInfo?.level === 'good' ? 'ring-1 ring-blue-300 dark:ring-blue-600' : ''
            }`}>
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
              <p className="text-xs text-gray-600 dark:text-gray-400 truncate" title={book.title}>{book.title}</p>
              <p className="text-xs text-blue-600 dark:text-blue-400 truncate" title={book.author}>{book.author}</p>
              {book.isFromOpenLibrary && !book.isOwned && (
                <p className="text-xs text-green-600 dark:text-green-400 font-medium">Open Library</p>
              )}
              {/* Indicateur de pertinence textuel en mode recherche */}
              {isSearchMode && book.relevanceInfo && book.relevanceScore > 100 && (
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  {book.relevanceInfo.label}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Barre de recherche */}
        <div className="mb-6">
          <AdvancedSearchBar
            searchTerm={useGroupedSearchMode ? groupedSearchTerm : searchTerm}
            onSearchChange={handleSearchChange}
            onOpenLibrarySearch={searchOpenLibrary}
            books={books}
            filters={filters}
            onFiltersChange={setFilters}
            className="max-w-2xl mx-auto"
          />
          
          {/* Bouton retour à la bibliothèque */}
          {(isSearchMode || useGroupedSearchMode) && (
            <div className="mt-3 text-center">
              <button
                onClick={backToLibrary}
                className="inline-flex items-center px-4 py-2 text-sm font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 dark:bg-blue-900/20 dark:text-blue-400 dark:hover:bg-blue-900/40 rounded-lg transition-colors"
              >
                ← Retour à ma bibliothèque
              </button>
            </div>
          )}
          
          {/* Statistiques de recherche */}
          {(searchStats.hasActiveFilters || isSearchMode) && (
            <div className="mt-3 text-center space-y-1">
              {isSearchMode ? (
                <>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Recherche "{lastSearchTerm}" - {displayedBooks.filter(b => !b.isFromOpenLibrary).length} dans ma bibliothèque, {displayedBooks.filter(b => b.isFromOpenLibrary).length} sur Open Library
                  </p>
                  {displayedBooks.length > 0 && (
                    <p className="text-xs text-gray-500 dark:text-gray-500 flex items-center justify-center">
                      <span className="mr-1">🎯</span>
                      Résultats classés par pertinence 
                      {displayedBooks.some(book => book.relevanceScore >= 800) && (
                        <span className="ml-1 text-green-600 dark:text-green-400 font-medium">
                          - Correspondances exactes trouvées
                        </span>
                      )}
                    </p>
                  )}
                </>
              ) : (
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {searchStats.filtered} résultat{searchStats.filtered > 1 ? 's' : ''} trouvé{searchStats.filtered > 1 ? 's' : ''} 
                  {searchStats.hiddenCount > 0 && (
                    <span> ({searchStats.hiddenCount} masqué{searchStats.hiddenCount > 1 ? 's' : ''})</span>
                  )}
                </p>
              )}
            </div>
          )}
          
          {/* Indicateur de chargement */}
          {searchLoading && (
            <div className="mt-3 text-center">
              <div className="inline-flex items-center text-sm text-gray-600 dark:text-gray-400">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
                Recherche en cours sur Open Library...
              </div>
            </div>
          )}
        </div>

        {/* Affichage des résultats groupés ou interface normale */}
        {useGroupedSearchMode && hasGroupedResults ? (
          <GroupedSearchResults
            results={groupedResults}
            searchStats={groupedSearchStats}
            onBookClick={(book) => {
              setSelectedBook(book);
              setShowBookModal(true);
            }}
          />
        ) : (
          <>
            <TabNavigation />
            <BookGrid />
          </>
        )}
      </main>

      <AddBookModal />
      <ProfileModal isOpen={showProfileModal} onClose={() => setShowProfileModal(false)} />
      
      {selectedBook && (
        <BookDetailModal
          book={selectedBook}
          onClose={() => {
            setSelectedBook(null);
            setShowBookModal(false);
          }}
          onUpdate={handleUpdateBook}
          onDelete={handleDeleteBook}
          onAddFromOpenLibrary={handleAddFromOpenLibrary}
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

  return user ? <AppContent /> : <LoginPage />;
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