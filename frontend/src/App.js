// Imports
import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';
import { toast, Toaster } from 'react-hot-toast';

// Context imports
import { ThemeProvider, useTheme } from './contexts/ThemeContext';

// Service imports
import { bookService } from './services/bookService';

// Component imports
import UnifiedSearchBar from './components/UnifiedSearchBar';
import BookDetailModal from './components/BookDetailModal';
import GroupedSearchResults from './components/GroupedSearchResults';
import SeriesCard from './components/SeriesCard';
import SeriesDetailModal from './components/SeriesDetailModal';
import SeriesDetailPage from './pages/SeriesDetailPage';
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
        return result;
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
        return result;
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
        // Force immediate navigation after successful auth
        setTimeout(() => {
          window.location.reload();
        }, 1000);
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
  return (
    <Routes>
      <Route path="/" element={<MainApp />} />
      <Route path="/series/:seriesName" element={<SeriesDetailPage />} />
    </Routes>
  );
}

// Composant principal de l'application
function MainApp() {
  const { user } = useAuth();
  const [books, setBooks] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('roman');
  const [showProfileModal, setShowProfileModal] = useState(false);

  const [selectedBook, setSelectedBook] = useState(null);
  const [showBookModal, setShowBookModal] = useState(false);

  // États pour la recherche Open Library
  const [openLibraryResults, setOpenLibraryResults] = useState([]);
  const [detectedSeries, setDetectedSeries] = useState([]);
  const [isSearchMode, setIsSearchMode] = useState(false);
  const [searchLoading, setSearchLoading] = useState(false);
  const [lastSearchTerm, setLastSearchTerm] = useState('');
  // SUPPRESSION VIEWMODE : Plus de toggle livre/série - affichage unifié
  const [addingBooks, setAddingBooks] = useState(new Set()); // Suivi des livres en cours d'ajout

  // État pour les séries simplifiées
  const [selectedSeries, setSelectedSeries] = useState(null);
  const [showSeriesDetail, setShowSeriesDetail] = useState(false);
  const [showSeriesModal, setShowSeriesModal] = useState(false);

  // Hook de recherche avancée
  const {
    filters,
    setFilters,
    filteredBooks,
    searchStats,
    clearSearch
  } = useAdvancedSearch(books);

  // Hook de recherche groupée
  const {
    groupedResults,
    searchStats: groupedSearchStats,
  } = useGroupedSearch();

  // Mettre à jour le service bookService pour supporter le nouveau paramètre
  const updateBookService = () => {
    // Modifier temporairement la fonction getBooks pour inclure viewMode
    bookService.getBooks = async (category = null, status = null, viewMode = 'books') => {
      try {
        const params = {};
        if (category) params.category = category;
        if (status) params.status = status;
        if (viewMode) params.view_mode = viewMode;
        
        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/books?${new URLSearchParams(params)}`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          }
        });
        
        if (!response.ok) {
          throw new Error('Erreur lors de la récupération des données');
        }
        
        return response.json();
      } catch (error) {
        console.error('Erreur lors de la récupération des livres:', error);
        throw new Error('Erreur lors de la récupération des livres');
      }
    };
  };

  useEffect(() => {
    updateBookService();
  }, []);

  // SUPPRESSION TOGGLEVIEWMODE : Plus de fonction de basculement nécessaire

  const loadBooks = async () => {
    try {
      setLoading(true);
      // AFFICHAGE UNIFIÉ : Charger tous les livres (plus de distinction viewMode)
      const data = await bookService.getBooks(null, null, 'books');
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

  // Fonction pour rechercher des séries
  const searchSeries = async (query) => {
    if (!query || query.trim().length < 2) return [];
    
    try {
      const token = localStorage.getItem('token');
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const response = await fetch(`${backendUrl}/api/series/search?q=${encodeURIComponent(query)}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        return data.series.map(series => ({
          ...series,
          isSeriesCard: true,
          isFromSearch: true
        }));
      }
      return [];
    } catch (error) {
      console.error('Erreur recherche séries:', error);
      return [];
    }
  };

  // Fonction modifiée pour la recherche Open Library incluant les séries

  // Fonction pour créer les cartes séries à partir des résultats détectés
  const createSeriesCards = (detectedSeries) => {
    return detectedSeries.map(detected => ({
      id: `series_${detected.series.name.toLowerCase().replace(/\s+/g, '_')}`,
      name: detected.series.name,
      author: detected.series.authors?.join(', ') || 'Auteur inconnu',
      category: detected.series.category,
      description: detected.series.description,
      volumes: detected.series.volumes,
      first_published: detected.series.first_published,
      status: detected.series.status,
      confidence: detected.confidence,
      match_reasons: detected.match_reasons,
      isSeriesCard: true,
      relevanceScore: 50000 + detected.confidence, // Score très élevé pour prioriser les séries
      relevanceInfo: { level: 'excellent', label: 'Série détectée', color: 'bg-purple-600', icon: '📚' }
    }));
  };

  // FONCTION UTILITAIRE : Déterminer le badge de catégorie depuis un livre Open Library
  const getCategoryBadgeFromBook = (book) => {
    // Si la catégorie est déjà définie dans le livre
    if (book.category) {
      switch (book.category.toLowerCase()) {
        case 'roman':
          return { key: 'roman', text: 'Roman', class: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300', emoji: '📚' };
        case 'bd':
          return { key: 'bd', text: 'BD', class: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300', emoji: '🎨' };
        case 'manga':
          return { key: 'manga', text: 'Manga', class: 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-300', emoji: '🇯🇵' };
      }
    }
    
    // Sinon, détecter automatiquement basé sur le titre et la description
    const title = (book.title || '').toLowerCase();
    const description = (book.description || '').toLowerCase();
    const subjects = (book.subjects || []).join(' ').toLowerCase();
    const allText = `${title} ${description} ${subjects}`;
    
    // Détection Manga
    if (allText.includes('manga') || allText.includes('japonais') || allText.includes('japan') || 
        allText.includes('anime') || allText.includes('otaku') || allText.includes('shonen') || 
        allText.includes('shojo') || allText.includes('seinen') || allText.includes('josei')) {
      return { key: 'manga', text: 'Manga', class: 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-300', emoji: '🇯🇵' };
    }
    
    // Détection BD
    if (allText.includes('bande dessinée') || allText.includes('comic') || allText.includes('comics') || 
        allText.includes('graphic novel') || allText.includes('bd') || allText.includes('illustration') ||
        allText.includes('dessins') || allText.includes('album')) {
      return { key: 'bd', text: 'BD', class: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300', emoji: '🎨' };
    }
    
    // Par défaut : Roman
    return { key: 'roman', text: 'Roman', class: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300', emoji: '📚' };
  };

  // FONCTION BIBLIOTHÈQUE : Regrouper les livres par série dans la bibliothèque
  const groupBooksIntoSeries = (booksList) => {
    const seriesGroups = {};
    const standaloneBooks = [];

    booksList.forEach(book => {
      if (book.saga && book.saga.trim()) {
        const seriesKey = book.saga.toLowerCase().trim();
        if (!seriesGroups[seriesKey]) {
          seriesGroups[seriesKey] = {
            id: `library-series-${seriesKey}`,
            isSeriesCard: true,
            isLibrarySeries: true, // Marqueur pour série de bibliothèque
            name: book.saga,
            title: book.saga,
            author: book.author,
            category: book.category,
            books: [],
            totalBooks: 0,
            completedBooks: 0,
            readingBooks: 0,
            toReadBooks: 0,
            cover_url: book.cover_url, // Utiliser la couverture du premier livre
            // Progression
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
  };

  // Fonction pour générer des cartes de séries basées sur la recherche
  const generateSeriesCardsForSearch = (query, books) => {
    // Fonction pour détecter les séries populaires
    const detectPopularSeries = (searchQuery) => {
      const query = searchQuery.toLowerCase();
      
      // Mapping des séries populaires
      const popularSeries = {
        'harry potter': {
          name: 'Harry Potter',
          authors: ['J.K. Rowling'],
          category: 'roman',
          volumes: 7,
          description: 'Série de romans fantastiques écrite par J.K. Rowling, qui décrit les aventures d\'un jeune sorcier nommé Harry Potter à l\'école de sorcellerie Poudlard.',
          first_published: '1997',
          status: 'completed'
        },
        'one piece': {
          name: 'One Piece',
          authors: ['Eiichiro Oda'],
          category: 'manga',
          volumes: 100,
          description: 'Manga qui suit les aventures de Monkey D. Luffy et de son équipage de pirates, à la recherche du trésor ultime, le "One Piece".',
          first_published: '1997',
          status: 'ongoing'
        },
        'astérix': {
          name: 'Astérix',
          authors: ['René Goscinny', 'Albert Uderzo'],
          category: 'bd',
          volumes: 39,
          description: 'Série de bandes dessinées françaises créée par René Goscinny et Albert Uderzo, qui raconte les aventures d\'Astérix et de son ami Obélix dans un village gaulois résistant à l\'occupation romaine.',
          first_published: '1959',
          status: 'ongoing'
        },
        'seigneur des anneaux': {
          name: 'Le Seigneur des Anneaux',
          authors: ['J.R.R. Tolkien'],
          category: 'roman',
          volumes: 3,
          description: 'Épopée de fantasy écrite par J.R.R. Tolkien, qui raconte la quête pour détruire l\'Anneau unique, forgé par le Seigneur des Ténèbres Sauron.',
          first_published: '1954',
          status: 'completed'
        },
        'naruto': {
          name: 'Naruto',
          authors: ['Masashi Kishimoto'],
          category: 'manga',
          volumes: 72,
          description: 'Manga qui raconte l\'histoire de Naruto Uzumaki, un jeune ninja qui rêve de devenir Hokage, le chef de son village.',
          first_published: '1999',
          status: 'completed'
        },
        'tintin': {
          name: 'Les Aventures de Tintin',
          authors: ['Hergé'],
          category: 'bd',
          volumes: 24,
          description: 'Série de bandes dessinées créée par Hergé, qui raconte les aventures du jeune reporter Tintin et de son chien Milou.',
          first_published: '1929',
          status: 'completed'
        }
      };
      
      // Vérifier si la requête correspond à une série populaire
      for (const [key, series] of Object.entries(popularSeries)) {
        if (query.includes(key)) {
          return {
            series: series,
            confidence: 180,
            match_reasons: ['exact_match', 'popular_series']
          };
        }
      }
      
      return null;
    };
    
    // Détecter si la recherche correspond à une série populaire
    const detectedSeries = detectPopularSeries(query);
    if (detectedSeries) {
      return [detectedSeries];
    }
    
    // Si aucune série populaire n'est détectée, essayer de détecter des séries basées sur les livres
    const potentialSeries = {};
    
    books.forEach(book => {
      if (book.saga) {
        const sagaKey = book.saga.toLowerCase();
        if (!potentialSeries[sagaKey]) {
          potentialSeries[sagaKey] = {
            series: {
              name: book.saga,
              authors: [book.author],
              category: book.category,
              volumes: 1,
              description: `Série de livres incluant "${book.title}"`,
              first_published: book.publication_year || 'Inconnue',
              status: 'ongoing'
            },
            confidence: 100,
            match_reasons: ['saga_match']
          };
        } else {
          potentialSeries[sagaKey].confidence += 20;
          if (!potentialSeries[sagaKey].series.authors.includes(book.author)) {
            potentialSeries[sagaKey].series.authors.push(book.author);
          }
          potentialSeries[sagaKey].series.volumes += 1;
        }
      }
    });
    
    // Convertir en tableau et filtrer les séries avec une confiance suffisante
    return Object.values(potentialSeries)
      .filter(series => series.confidence >= 100)
      .sort((a, b) => b.confidence - a.confidence)
      .slice(0, 3); // Limiter à 3 séries maximum
  };

  // Fonction pour rechercher dans Open Library avec RECHERCHE GLOBALE (toutes catégories)
  const searchOpenLibrary = async (query) => {
    console.log('🚀 searchOpenLibrary GLOBALE appelée avec:', query);
    if (!query.trim()) {
      console.log('❌ Recherche annulée: query vide');
      return;
    }
    
    try {
      console.log('✅ Début de la recherche globale Open Library (toutes catégories)');
      setSearchLoading(true);
      setIsSearchMode(true);
      setLastSearchTerm(query);
      
      const token = localStorage.getItem('token');
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      // RECHERCHE GLOBALE : pas de filtre par catégorie, recherche dans TOUTES les catégories
      const response = await fetch(`${backendUrl}/api/openlibrary/search?q=${encodeURIComponent(query)}&limit=40`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        
        // Générer automatiquement les cartes séries basées sur le terme de recherche
        const seriesCards = generateSeriesCardsForSearch(query, data.books);
        
        // AJOUT DES BADGES CATÉGORIE : Marquer les livres avec leur catégorie et badge
        const resultsWithOwnership = data.books.map(book => {
          const isOwned = books.some(localBook => {
            // Normaliser les titres et auteurs pour la comparaison
            const normalizeString = (str) => {
              if (!str) return '';
              return str.toLowerCase()
                .trim()
                .replace(/[^\w\s]/g, '') // Supprimer la ponctuation
                .replace(/\s+/g, ' '); // Normaliser les espaces
            };
            
            const localTitle = normalizeString(localBook.title);
            const localAuthor = normalizeString(localBook.author);
            const openLibTitle = normalizeString(book.title);
            const openLibAuthor = normalizeString(book.author);
            
            // Vérification par ol_key d'abord (plus précise)
            if (localBook.ol_key && book.ol_key && localBook.ol_key === book.ol_key) {
              return true;
            }
            
            // Vérification par ISBN si disponible
            if (localBook.isbn && book.isbn && 
                localBook.isbn.replace(/[-\s]/g, '') === book.isbn.replace(/[-\s]/g, '')) {
              return true;
            }
            
            // Vérification par titre et auteur (comparaison exacte)
            if (localTitle === openLibTitle && localAuthor === openLibAuthor) {
              return true;
            }
            
            // Vérification par titre et auteur (comparaison flexible)
            // Le titre de Open Library doit contenir le titre local OU vice versa
            const titleMatch = (localTitle.includes(openLibTitle) || openLibTitle.includes(localTitle)) && 
                              (localTitle.length > 3 && openLibTitle.length > 3); // Éviter les correspondances trop courtes
            
            // L'auteur doit correspondre exactement ou l'un doit contenir l'autre
            const authorMatch = localAuthor === openLibAuthor || 
                               (localAuthor.includes(openLibAuthor) && openLibAuthor.length > 3) ||
                               (openLibAuthor.includes(localAuthor) && localAuthor.length > 3);
            
            return titleMatch && authorMatch;
          });
          
          // BADGES CATÉGORIE AUTOMATIQUES : Ajouter badge selon la catégorie détectée
          const categoryBadge = getCategoryBadgeFromBook(book);
          
          return {
            ...book,
            isFromOpenLibrary: true,
            isOwned: isOwned,
            id: `ol_${book.ol_key}`,
            // Badge catégorie pour affichage visuel
            categoryBadge: categoryBadge,
            // S'assurer que la catégorie est bien définie pour le placement intelligent
            category: book.category || categoryBadge.key || 'roman' // Défaut roman si non détecté
          };
        });
        
        // Stocker les résultats combinés avec les cartes séries en premier
        setOpenLibraryResults([...seriesCards, ...resultsWithOwnership]);
        toast.success(`${data.books.length} livres trouvés${seriesCards.length > 0 ? ` + ${seriesCards.length} série(s) détectée(s)` : ''}`);
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

  // Gestionnaire stable pour éviter les re-rendus excessifs
  const handleSearchTermChange = useCallback((term) => {
    setLastSearchTerm(term);
  }, []);

  // Fonction pour revenir à la bibliothèque locale
  const backToLibrary = () => {
    setIsSearchMode(false);
    setOpenLibraryResults([]);
    setLastSearchTerm('');
    clearSearch();
  };

  // AJOUT INTELLIGENT : Placement automatique dans le bon onglet selon la catégorie
  const handleAddFromOpenLibrary = async (openLibraryBook) => {
    // Empêcher les clics multiples sur le même livre
    if (addingBooks.has(openLibraryBook.ol_key)) {
      return; // Si le livre est déjà en cours d'ajout, ne rien faire
    }

    try {
      // Marquer le livre comme en cours d'ajout
      setAddingBooks(prev => new Set([...prev, openLibraryBook.ol_key]));
      
      const token = localStorage.getItem('token');
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      // PLACEMENT INTELLIGENT : Déterminer la catégorie automatiquement via le badge
      const categoryBadge = openLibraryBook.categoryBadge || getCategoryBadgeFromBook(openLibraryBook);
      let targetCategory = categoryBadge.key; // Utiliser la catégorie détectée par le badge
      
      // Validation : s'assurer que la catégorie est valide
      if (!targetCategory || !['roman', 'bd', 'manga'].includes(targetCategory)) {
        // Si pas de catégorie ou catégorie invalide, utiliser l'onglet actuel par défaut
        targetCategory = activeTab;
      }
      
      const response = await fetch(`${backendUrl}/api/openlibrary/import`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ol_key: openLibraryBook.ol_key,
          category: targetCategory
        })
      });

      if (response.ok) {
        await loadBooks();
        await loadStats();
        
        // Message de succès avec indication de l'onglet
        const categoryLabels = {
          'roman': 'Roman',
          'bd': 'BD',
          'manga': 'Manga'
        };
        toast.success(`"${openLibraryBook.title}" ajouté à l'onglet ${categoryLabels[targetCategory]} !`);
        
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
          // Marquer le livre comme possédé même si l'ajout a échoué pour cause de doublon
          setOpenLibraryResults(prev => 
            prev.map(book => 
              book.ol_key === openLibraryBook.ol_key 
                ? { ...book, isOwned: true }
                : book
            )
          );
        } else {
          toast.error(error.detail || 'Erreur lors de l\'ajout du livre');
        }
      }
    } catch (error) {
      console.error('Erreur ajout livre:', error);
      toast.error('Erreur lors de l\'ajout du livre');
    } finally {
      // Retirer le livre de la liste des livres en cours d'ajout
      setAddingBooks(prev => {
        const newSet = new Set(prev);
        newSet.delete(openLibraryBook.ol_key);
        return newSet;
      });
    }
  };

  // Gestionnaire de clic sur série pour afficher la fiche dédiée
  const handleSeriesClick = (series) => {
    if (series.isLibrarySeries) {
      // Série de bibliothèque : créer une fiche dédiée locale
      // Pour l'instant, on peut montrer une modal avec les livres de la série
      setSelectedSeries(series);
      setShowSeriesModal(true);
    } else {
      // Série Open Library : naviguer vers la page dédiée
      const navigate = window.location.pathname !== '/' ? 
        (path) => window.location.href = path : 
        (path) => window.history.pushState({}, '', path);
      navigate(`/series/${encodeURIComponent(series.name)}`);
    }
  };

  // Gestionnaire de clic sur livre
  const handleBookClick = (book) => {
    setSelectedBook(book);
    setShowBookModal(true);
  };

  // Gestionnaire de clic conditionnel (livre ou série)
  const handleItemClick = (item) => {
    if (item.isSeriesCard) {
      handleSeriesClick(item);
    } else {
      handleBookClick(item);
    }
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

  // Fonction intelligente de calcul de la pertinence basée sur la popularité et la détection de séries
  const calculateRelevanceScore = (book, searchTerm) => {
    if (!searchTerm || !searchTerm.trim()) return 0;
    
    const term = searchTerm.toLowerCase().trim();
    const termWords = term.split(/\s+/).filter(word => word.length > 1);
    
    // Normalisation des champs de recherche
    const title = (book.title || '').toLowerCase();
    const author = (book.author || '').toLowerCase();
    const saga = (book.saga || '').toLowerCase();
    
    let score = 0;
    
    // === DÉTECTION INTELLIGENTE DES SÉRIES POPULAIRES ===
    
    // Mapping complet des séries populaires avec leurs variations et auteurs
    const seriesMapping = {
      // === ROMANS FANTASY/SF ===
      'harry potter': {
        score: 18000,
        category: 'roman',
        keywords: ['harry', 'potter', 'hogwarts', 'sorcier', 'wizard', 'poudlard', 'voldemort', 'hermione', 'ron', 'dumbledore'],
        authors: ['j.k. rowling', 'jk rowling', 'rowling'],
        variations: ['harry potter', 'école des sorciers', 'chambre des secrets', 'prisonnier d\'azkaban', 'coupe de feu', 'ordre du phénix', 'prince de sang-mêlé', 'reliques de la mort'],
        volumes: 7,
        language: ['fr', 'en']
      },
      'seigneur des anneaux': {
        score: 18000,
        category: 'roman',
        keywords: ['anneau', 'communauté', 'deux tours', 'retour du roi', 'terre du milieu', 'middle earth', 'hobbit', 'frodo', 'gandalf', 'aragorn', 'legolas', 'gimli'],
        authors: ['j.r.r. tolkien', 'jrr tolkien', 'tolkien'],
        variations: ['seigneur des anneaux', 'lord of the rings', 'communauté de l\'anneau', 'fellowship', 'deux tours', 'two towers', 'retour du roi', 'return of the king', 'hobbit'],
        volumes: 3,
        language: ['fr', 'en']
      },
      'game of thrones': {
        score: 16000,
        category: 'roman',
        keywords: ['game of thrones', 'trône de fer', 'westeros', 'jon snow', 'daenerys', 'tyrion', 'stark', 'lannister', 'targaryen'],
        authors: ['george r.r. martin', 'george martin', 'martin'],
        variations: ['game of thrones', 'trône de fer', 'song of ice and fire', 'chanson de glace et de feu'],
        volumes: 5,
        language: ['fr', 'en']
      },
      'witcher': {
        score: 15000,
        category: 'roman',
        keywords: ['witcher', 'sorceleur', 'geralt', 'rivia', 'ciri', 'yennefer', 'triss'],
        authors: ['andrzej sapkowski', 'sapkowski'],
        variations: ['witcher', 'sorceleur', 'geralt de rivia'],
        volumes: 8,
        language: ['fr', 'en', 'pl']
      },
      'dune': {
        score: 16000,
        category: 'roman',
        keywords: ['dune', 'arrakis', 'paul atreides', 'fremen', 'spice', 'épice', 'muad\'dib'],
        authors: ['frank herbert', 'herbert'],
        variations: ['dune', 'cycle de dune'],
        volumes: 6,
        language: ['fr', 'en']
      },

      // === MANGAS ===
      'one piece': {
        score: 18000,
        category: 'manga',
        keywords: ['one piece', 'luffy', 'zoro', 'sanji', 'pirates', 'chapeau de paille', 'grand line', 'nami', 'usopp', 'chopper'],
        authors: ['eiichiro oda', 'oda'],
        variations: ['one piece'],
        volumes: 100,
        language: ['fr', 'en', 'jp']
      },
      'naruto': {
        score: 17000,
        category: 'manga',
        keywords: ['naruto', 'sasuke', 'sakura', 'kakashi', 'ninja', 'konoha', 'sharingan', 'hokage', 'boruto'],
        authors: ['masashi kishimoto', 'kishimoto'],
        variations: ['naruto', 'boruto'],
        volumes: 72,
        language: ['fr', 'en', 'jp']
      },
      'dragon ball': {
        score: 17000,
        category: 'manga',
        keywords: ['dragon ball', 'goku', 'vegeta', 'kamehameha', 'saiyan', 'piccolo', 'gohan', 'frieza', 'cell'],
        authors: ['akira toriyama', 'toriyama'],
        variations: ['dragon ball', 'dragonball', 'dragon ball z', 'dragon ball super'],
        volumes: 42,
        language: ['fr', 'en', 'jp']
      },
      'attack on titan': {
        score: 16000,
        category: 'manga',
        keywords: ['attack on titan', 'attaque des titans', 'eren', 'mikasa', 'armin', 'titans', 'murs', 'shingeki no kyojin'],
        authors: ['hajime isayama', 'isayama'],
        variations: ['attack on titan', 'attaque des titans', 'shingeki no kyojin'],
        volumes: 34,
        language: ['fr', 'en', 'jp']
      },
      'death note': {
        score: 15000,
        category: 'manga',
        keywords: ['death note', 'light', 'l', 'kira', 'ryuk', 'shinigami', 'yagami'],
        authors: ['tsugumi ohba', 'takeshi obata', 'ohba', 'obata'],
        variations: ['death note'],
        volumes: 12,
        language: ['fr', 'en', 'jp']
      },
      'bleach': {
        score: 15000,
        category: 'manga',
        keywords: ['bleach', 'ichigo', 'rukia', 'shinigami', 'hollow', 'soul society', 'zanpakuto'],
        authors: ['tite kubo', 'kubo'],
        variations: ['bleach'],
        volumes: 74,
        language: ['fr', 'en', 'jp']
      },
      'fullmetal alchemist': {
        score: 15000,
        category: 'manga',
        keywords: ['fullmetal alchemist', 'edward elric', 'alphonse', 'alchemy', 'alchimie', 'philosopher stone'],
        authors: ['hiromu arakawa', 'arakawa'],
        variations: ['fullmetal alchemist', 'full metal alchemist'],
        volumes: 27,
        language: ['fr', 'en', 'jp']
      },
      'demon slayer': {
        score: 16000,
        category: 'manga',
        keywords: ['demon slayer', 'kimetsu no yaiba', 'tanjiro', 'nezuko', 'demons', 'hashira'],
        authors: ['koyoharu gotouge', 'gotouge'],
        variations: ['demon slayer', 'kimetsu no yaiba'],
        volumes: 23,
        language: ['fr', 'en', 'jp']
      },
      'my hero academia': {
        score: 15000,
        category: 'manga',
        keywords: ['my hero academia', 'boku no hero', 'midoriya', 'deku', 'quirk', 'all might', 'bakugo'],
        authors: ['kohei horikoshi', 'horikoshi'],
        variations: ['my hero academia', 'boku no hero academia'],
        volumes: 35,
        language: ['fr', 'en', 'jp']
      },

      // === BANDES DESSINÉES ===
      'astérix': {
        score: 18000,
        category: 'bd',
        keywords: ['astérix', 'asterix', 'obélix', 'obelix', 'gaulois', 'potion magique', 'panoramix', 'idéfix'],
        authors: ['rené goscinny', 'albert uderzo', 'goscinny', 'uderzo'],
        variations: ['astérix', 'asterix'],
        volumes: 39,
        language: ['fr', 'en']
      },
      'tintin': {
        score: 18000,
        category: 'bd',
        keywords: ['tintin', 'milou', 'capitaine haddock', 'tournesol', 'dupont', 'dupond', 'mille sabords'],
        authors: ['hergé', 'herge'],
        variations: ['tintin', 'aventures de tintin'],
        volumes: 24,
        language: ['fr', 'en']
      },
      'gaston lagaffe': {
        score: 15000,
        category: 'bd',
        keywords: ['gaston', 'lagaffe', 'spirou', 'fantasio', 'prunelle', 'longtarin'],
        authors: ['andré franquin', 'franquin'],
        variations: ['gaston lagaffe', 'gaston'],
        volumes: 19,
        language: ['fr']
      },
      'lucky luke': {
        score: 15000,
        category: 'bd',
        keywords: ['lucky luke', 'dalton', 'jolly jumper', 'rantanplan', 'cowboy', 'western'],
        authors: ['morris', 'rené goscinny', 'goscinny'],
        variations: ['lucky luke'],
        volumes: 70,
        language: ['fr', 'en']
      },
      'spirou': {
        score: 15000,
        category: 'bd',
        keywords: ['spirou', 'fantasio', 'marsupilami', 'spip', 'zorglub', 'champignac'],
        authors: ['andré franquin', 'franquin', 'rob-vel'],
        variations: ['spirou et fantasio', 'spirou'],
        volumes: 55,
        language: ['fr']
      },
      'thorgal': {
        score: 14000,
        category: 'bd',
        keywords: ['thorgal', 'aaricia', 'jolan', 'louve', 'viking', 'nordique'],
        authors: ['jean van hamme', 'grzegorz rosinski', 'van hamme', 'rosinski'],
        variations: ['thorgal'],
        volumes: 38,
        language: ['fr']
      },
      'xiii': {
        score: 14000,
        category: 'bd',
        keywords: ['xiii', 'treize', 'jason fly', 'conspiracy', 'conspiration'],
        authors: ['jean van hamme', 'william vance', 'van hamme', 'vance'],
        variations: ['xiii', 'treize'],
        volumes: 27,
        language: ['fr', 'en']
      },
      'blake et mortimer': {
        score: 14000,
        category: 'bd',
        keywords: ['blake', 'mortimer', 'francis blake', 'philip mortimer', 'jacobs'],
        authors: ['edgar p. jacobs', 'jacobs'],
        variations: ['blake et mortimer', 'blake mortimer'],
        volumes: 27,
        language: ['fr', 'en']
      },

      // === COMICS AMÉRICAINS ===
      'batman': {
        score: 16000,
        category: 'bd',
        keywords: ['batman', 'bruce wayne', 'gotham', 'joker', 'robin', 'alfred', 'dark knight'],
        authors: ['dc comics', 'bob kane', 'bill finger'],
        variations: ['batman', 'dark knight', 'chevalier noir'],
        volumes: 1000,
        language: ['fr', 'en']
      },
      'superman': {
        score: 16000,
        category: 'bd',
        keywords: ['superman', 'clark kent', 'metropolis', 'lois lane', 'lex luthor', 'kryptonite'],
        authors: ['dc comics', 'jerry siegel', 'joe shuster'],
        variations: ['superman', 'man of steel'],
        volumes: 1000,
        language: ['fr', 'en']
      },
      'spider-man': {
        score: 16000,
        category: 'bd',
        keywords: ['spider-man', 'spiderman', 'peter parker', 'new york', 'web', 'toile'],
        authors: ['marvel comics', 'stan lee', 'steve ditko'],
        variations: ['spider-man', 'spiderman', 'amazing spider-man'],
        volumes: 1000,
        language: ['fr', 'en']
      },
      'x-men': {
        score: 15000,
        category: 'bd',
        keywords: ['x-men', 'wolverine', 'cyclops', 'storm', 'xavier', 'magneto', 'mutants'],
        authors: ['marvel comics', 'stan lee', 'jack kirby'],
        variations: ['x-men', 'uncanny x-men'],
        volumes: 1000,
        language: ['fr', 'en']
      },
      'walking dead': {
        score: 15000,
        category: 'bd',
        keywords: ['walking dead', 'rick grimes', 'zombies', 'walkers', 'apocalypse'],
        authors: ['robert kirkman', 'kirkman'],
        variations: ['walking dead'],
        volumes: 193,
        language: ['fr', 'en']
      },

      // === ROMANS POLICIERS ===
      'sherlock holmes': {
        score: 16000,
        category: 'roman',
        keywords: ['sherlock holmes', 'watson', 'baker street', 'moriarty', 'london', 'detective'],
        authors: ['arthur conan doyle', 'conan doyle', 'doyle'],
        variations: ['sherlock holmes', 'adventures of sherlock holmes'],
        volumes: 60,
        language: ['fr', 'en']
      },
      'hercule poirot': {
        score: 15000,
        category: 'roman',
        keywords: ['hercule poirot', 'agatha christie', 'orient express', 'nil', 'belgian', 'detective'],
        authors: ['agatha christie', 'christie'],
        variations: ['hercule poirot', 'poirot'],
        volumes: 39,
        language: ['fr', 'en']
      },
      'san antonio': {
        score: 14000,
        category: 'roman',
        keywords: ['san antonio', 'bérurier', 'pinaud', 'police', 'commissaire'],
        authors: ['frédéric dard', 'dard'],
        variations: ['san antonio', 'san-antonio'],
        volumes: 175,
        language: ['fr']
      }
    };
    
    // Fonction pour détecter si un livre appartient à une série populaire
    function detectSeries(searchQuery) {
      const query = searchQuery.toLowerCase();
      
      for (const [seriesName, seriesData] of Object.entries(seriesMapping)) {
        // Vérification directe du nom de série dans la requête
        if (query.includes(seriesName)) {
          return { series: seriesName, data: seriesData, confidence: 'high' };
        }
        
        // Vérification des variations
        for (const variation of seriesData.variations) {
          if (query.includes(variation)) {
            return { series: seriesName, data: seriesData, confidence: 'high' };
          }
        }
      }
      
      return null;
    }
    
    // Fonction pour vérifier si un livre correspond à une série
    function isBookInSeries(book, seriesName, seriesData) {
      const bookTitle = (book.title || '').toLowerCase();
      const bookAuthor = (book.author || '').toLowerCase();
      const bookSaga = (book.saga || '').toLowerCase();
      const bookCategory = (book.category || '').toLowerCase();
      
      let confidence = 0;
      
      // Vérification par saga (le plus fiable)
      if (bookSaga.includes(seriesName) || seriesData.variations.some(v => bookSaga.includes(v))) {
        confidence += 100;
      }
      
      // Vérification par auteur (très fiable pour les séries uniques)
      if (seriesData.authors.some(author => bookAuthor.includes(author))) {
        confidence += 90;
      }
      
      // Bonus pour correspondance de catégorie
      if (seriesData.category && bookCategory === seriesData.category) {
        confidence += 20;
      }
      
      // Vérification par mots-clés dans le titre
      let keywordMatches = 0;
      seriesData.keywords.forEach(keyword => {
        if (bookTitle.includes(keyword)) {
          keywordMatches++;
        }
      });
      
      if (keywordMatches > 0) {
        confidence += keywordMatches * 25; // Réduction du score pour éviter les faux positifs
      }
      
      // Vérification par variations dans le titre (très importante)
      seriesData.variations.forEach(variation => {
        if (bookTitle.includes(variation)) {
          confidence += 70;
        }
      });
      
      // Bonus pour titre exact ou quasi-exact
      if (seriesData.variations.some(variation => bookTitle === variation || bookTitle.startsWith(variation))) {
        confidence += 50;
      }
      
      // Vérification des langues supportées
      if (seriesData.language && book.language) {
        if (seriesData.language.includes(book.language)) {
          confidence += 10;
        }
      }
      
      return confidence;
    }
    
    // === CALCUL DE SCORE PRINCIPAL ===
    
    // Détecter si la recherche concerne une série populaire
    const detectedSeries = detectSeries(term);
    
    let matchScore = 0;
    let popularityBonus = 0;
    
    if (detectedSeries) {
      const { series, data } = detectedSeries;
      
      // Vérifier si ce livre appartient à la série recherchée
      const seriesConfidence = isBookInSeries(book, series, data);
      
      if (seriesConfidence >= 100) {
        // Livre confirmé de la série (par saga ou auteur + mots-clés)
        popularityBonus = data.score;
        matchScore = 40000; // Score très élevé pour les vrais livres de la série
      } else if (seriesConfidence >= 80) {
        // Livre probable de la série
        popularityBonus = data.score * 0.8;
        matchScore = 30000;
      } else if (seriesConfidence >= 50) {
        // Livre possible de la série
        popularityBonus = data.score * 0.5;
        matchScore = 20000;
      }
    }
    
    // === CORRESPONDANCES EXACTES CLASSIQUES ===
    
    // Si pas de série détectée ou score faible, utiliser la correspondance classique
    if (matchScore < 20000) {
      // Correspondance exacte complète
      if (title === term) {
        matchScore = Math.max(matchScore, 35000);
      }
      // Correspondance de séquence complète
      else if (title.includes(term)) {
        if (title.startsWith(term)) {
          matchScore = Math.max(matchScore, 25000);
        } else {
          matchScore = Math.max(matchScore, 18000);
        }
      }
      // Multi-mots : tous les mots présents
      else if (termWords.length > 1) {
        let wordsFound = 0;
        termWords.forEach(word => {
          if (title.includes(word)) wordsFound++;
        });
        
        const completeness = wordsFound / termWords.length;
        if (completeness === 1) {
          matchScore = Math.max(matchScore, 15000); // Tous les mots trouvés
        } else if (completeness >= 0.8) {
          matchScore = Math.max(matchScore, 12000); // 80%+ des mots
        } else if (completeness >= 0.6) {
          matchScore = Math.max(matchScore, 8000);  // 60%+ des mots
        } else if (completeness >= 0.4) {
          matchScore = Math.max(matchScore, 5000);  // 40%+ des mots
        }
      }
      // Mot simple
      else {
        if (title.startsWith(term)) {
          matchScore = Math.max(matchScore, 8000);
        } else if (title.includes(` ${term} `) || title.includes(`${term} `) || title.includes(` ${term}`)) {
          matchScore = Math.max(matchScore, 6000); // Mot entier
        } else if (title.includes(term)) {
          matchScore = Math.max(matchScore, 4000); // Contient le mot
        }
      }
    }
    
    // Correspondances dans l'auteur
    if (author.includes(term)) {
      if (author === term) {
        matchScore += 10000;
      } else if (author.startsWith(term)) {
        matchScore += 6000;
      } else {
        matchScore += 3000;
      }
    }
    
    // Correspondances dans la saga
    if (saga && saga.includes(term)) {
      if (saga === term) {
        matchScore += 8000;
      } else if (saga.startsWith(term)) {
        matchScore += 5000;
      } else {
        matchScore += 2000;
      }
    }
    
    // === BONUS GÉNÉRAUX ===
    
    // Séries génériquement populaires (fallback) - Version étendue
    const generalPopularKeywords = [
      // Comics/BD supplémentaires
      'wolverine', 'deadpool', 'iron man', 'captain america', 'hulk', 'thor', 'avengers',
      'wonder woman', 'flash', 'green lantern', 'aquaman', 'justice league',
      'sandman', 'watchmen', 'v for vendetta', 'hellboy', 'spawn',
      
      // Mangas supplémentaires
      'one punch man', 'tokyo ghoul', 'fairy tail', 'black clover', 'jujutsu kaisen',
      'chainsaw man', 'mob psycho', 'hunter x hunter', 'yu yu hakusho',
      'cowboy bebop', 'akira', 'ghost in the shell', 'evangelion',
      
      // Romans supplémentaires
      'percy jackson', 'twilight', 'hunger games', 'divergent', 'maze runner',
      'outlander', 'fifty shades', 'dark tower', 'foundation', 'hyperion',
      'mistborn', 'wheel of time', 'chronicles of narnia', 'his dark materials',
      
      // BD franco-belges supplémentaires
      'largo winch', 'blacksad', 'corto maltese', 'lanfeust', 'trolls de troy',
      'donjon', 'dungeon', 'bone', 'fables', 'saga', 'invincible',
      
      // Classiques
      'james bond', 'indiana jones', 'conan', 'tarzan', 'flash gordon',
      'buck rogers', 'phantom', 'prince valiant', 'dick tracy'
    ];
    
    if (!detectedSeries) {
      const titleAndSaga = `${title} ${saga} ${author}`.toLowerCase();
      for (const keyword of generalPopularKeywords) {
        if (titleAndSaga.includes(keyword) || term.includes(keyword)) {
          popularityBonus += 8000;
          break;
        }
      }
    }
    
    // Bonus pour livres récents
    if (book.first_publish_year) {
      const year = book.first_publish_year;
      if (year >= 2020) popularityBonus += 1000;
      else if (year >= 2015) popularityBonus += 800;
      else if (year >= 2010) popularityBonus += 600;
      else if (year >= 2000) popularityBonus += 400;
      else if (year >= 1990) popularityBonus += 200;
    }
    
    // Bonus pour métadonnées de qualité
    if (book.cover_url) popularityBonus += 500;
    if (book.number_of_pages && book.number_of_pages >= 100 && book.number_of_pages <= 800) {
      popularityBonus += 300;
    }
    
    // === BONUS POUR LIVRES LOCAUX ===
    
    let localBonus = 0;
    if (!book.isFromOpenLibrary) {
      localBonus = 3000; // Bonus pour livres possédés
    } else if (book.isFromOpenLibrary && book.isOwned) {
      localBonus = 1500;
    }
    
    // === CALCUL FINAL ===
    
    score = matchScore + popularityBonus + localBonus;
    
    // Malus pour livres sans métadonnées importantes
    if (!book.author || book.author.trim() === '') score -= 2000;
    if (!book.title || book.title.trim() === '') score -= 3000;
    
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

  // AFFICHAGE INTELLIGENT : Recherche vs Bibliothèque avec regroupement séries
  const displayedBooks = isSearchMode 
    ? [
        // RECHERCHE GLOBALE : Combiner TOUS les livres (toutes catégories)
        ...books.filter(book => {
          if (!lastSearchTerm) return false;
          const term = lastSearchTerm.toLowerCase();
          return (
            (book.title || '').toLowerCase().includes(term) ||
            (book.author || '').toLowerCase().includes(term) ||
            (book.saga || '').toLowerCase().includes(term)
          );
        }).map(book => ({ ...book, isFromOpenLibrary: false, isOwned: true })),
        ...openLibraryResults // Tous les livres Open Library (contient déjà les cartes séries)
      ].map(book => ({
        ...book,
        relevanceScore: calculateRelevanceScore(book, lastSearchTerm),
        relevanceInfo: getRelevanceLevel(calculateRelevanceScore(book, lastSearchTerm))
      }))
      .sort((a, b) => {
        // 1. PRIORITÉ ABSOLUE : Les cartes séries en PREMIER
        if (a.isSeriesCard && !b.isSeriesCard) {
          return -1; // a (série) avant b (livre)
        }
        if (!a.isSeriesCard && b.isSeriesCard) {
          return 1; // b (série) avant a (livre)
        }
        
        // 2. Entre séries : trier par score de pertinence
        if (a.isSeriesCard && b.isSeriesCard) {
          return b.relevanceScore - a.relevanceScore;
        }
        
        // 3. Entre livres : trier par score de pertinence décroissant
        if (a.relevanceScore !== b.relevanceScore) {
          return b.relevanceScore - a.relevanceScore;
        }
        
        // 4. En cas d'égalité de score, prioriser les livres locaux
        if (a.isFromOpenLibrary !== b.isFromOpenLibrary) {
          return a.isFromOpenLibrary ? 1 : -1;
        }
        
        // 5. Pour les livres Open Library, prioriser ceux déjà possédés
        if (a.isFromOpenLibrary && b.isFromOpenLibrary) {
          if (a.isOwned !== b.isOwned) {
            return a.isOwned ? -1 : 1;
          }
        }
        
        // 6. Trier par qualité des métadonnées (livres avec plus d'infos en premier)
        const qualityScoreA = (a.cover_url ? 10 : 0) + (a.description?.length > 100 ? 5 : 0) + (a.first_publish_year ? 3 : 0);
        const qualityScoreB = (b.cover_url ? 10 : 0) + (b.description?.length > 100 ? 5 : 0) + (b.first_publish_year ? 3 : 0);
        
        if (qualityScoreA !== qualityScoreB) {
          return qualityScoreB - qualityScoreA;
        }
        
        // 7. Trier par année de publication (plus récent en premier pour les livres de qualité égale)
        if (a.first_publish_year && b.first_publish_year) {
          return b.first_publish_year - a.first_publish_year;
        }
        
        // 8. Finalement, trier par titre alphabétique
        return (a.title || '').localeCompare(b.title || '', 'fr', { numeric: true });
      })
      // Filtrer les résultats avec un score minimum pour éviter le bruit
      .filter(book => !lastSearchTerm || book.relevanceScore >= 10)
    : (viewMode === 'series' ? 
        // BIBLIOTHÈQUE SÉRIES : Regrouper automatiquement les livres par série
        groupBooksIntoSeries(filteredBooks.filter(book => book.category === activeTab && !book.isSeriesCard)) : 
        // BIBLIOTHÈQUE LIVRES : Affichage classique par livres individuels
        filteredBooks.filter(book => book.category === activeTab && !book.isSeriesCard)
      );

  // Header Component avec barre de recherche unifiée
  const Header = () => (
    <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          <div className="flex items-center space-x-6">
            {/* Logo */}
            <div className="flex items-center space-x-3 text-2xl font-bold text-green-600 dark:text-green-400">
              <div className="w-10 h-10 bg-green-600 rounded-lg flex items-center justify-center text-white text-xl">
                🐝
              </div>
              BookTime
            </div>
            
            {/* Barre de recherche unifiée compacte */}
            <UnifiedSearchBar
              searchTerm={lastSearchTerm}
              onSearchChange={handleSearchTermChange}
              onOpenLibrarySearch={searchOpenLibrary}
              books={books}
              filters={filters}
              onFiltersChange={setFilters}
              isCompact={true}
            />
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

  // Tab Navigation Component avec toggle Vue Livres/Séries
  const TabNavigation = () => (
    <div className="mb-6">
      <div className="border-b border-gray-200 dark:border-gray-700">
        <div className="flex justify-between items-center">
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
                    : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                }`}
              >
                {category.label}
              </button>
            ))}
          </nav>
          
          <div className="flex items-center space-x-4">
            {/* Toggle Vue Livres/Séries */}
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-500 dark:text-gray-400">Vue :</span>
              <button
                onClick={toggleViewMode}
                className={`relative inline-flex h-6 w-12 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 ${
                  viewMode === 'series' ? 'bg-green-600' : 'bg-gray-200 dark:bg-gray-700'
                }`}
              >
                <span className="sr-only">Basculer entre vue livres et séries</span>
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    viewMode === 'series' ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {viewMode === 'series' ? 'Séries' : 'Livres'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Chargement initial des livres et statistiques
  useEffect(() => {
    if (user) {
      loadBooks();
      loadStats();
    }
  }, [user, viewMode]);

  // Rechargement des livres quand l'onglet change
  useEffect(() => {
    if (user) {
      loadBooks();
    }
  }, [activeTab, viewMode]);

  // Rendu principal
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Contenu principal */}
        <div className="space-y-8">
          {/* Navigation par onglets */}
          {!isSearchMode && <TabNavigation />}
          
          {/* Bouton Retour à la bibliothèque (en mode recherche) */}
          {isSearchMode && (
            <div className="mb-6">
              <button
                onClick={backToLibrary}
                className="inline-flex items-center px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                ← Retour à ma bibliothèque
              </button>
            </div>
          )}
          
          {/* Statistiques de recherche (en mode recherche) */}
          {isSearchMode && (
            <div className="mb-6">
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                <h3 className="text-sm font-medium text-blue-900 dark:text-blue-200 mb-2">
                  📊 Résultats pour "{lastSearchTerm}"
                </h3>
                <div className="flex flex-wrap gap-4 text-sm text-blue-700 dark:text-blue-300">
                  <span>
                    {books.filter(book => {
                      const term = lastSearchTerm.toLowerCase();
                      return (
                        (book.title || '').toLowerCase().includes(term) ||
                        (book.author || '').toLowerCase().includes(term) ||
                        (book.saga || '').toLowerCase().includes(term)
                      );
                    }).length} dans ma bibliothèque
                  </span>
                  <span>
                    {openLibraryResults.filter(book => !book.isSeriesCard).length} sur Open Library
                  </span>
                  {openLibraryResults.some(book => book.isSeriesCard) && (
                    <span>
                      {openLibraryResults.filter(book => book.isSeriesCard).length} série(s) détectée(s)
                    </span>
                  )}
                </div>
                <div className="mt-2 text-sm text-blue-700 dark:text-blue-300 font-medium">
                  Résultats classés par pertinence
                </div>
                {displayedBooks.some(book => book.relevanceScore >= 30000) && (
                  <div className="mt-1 text-xs text-green-600 dark:text-green-400">
                    Correspondances exactes trouvées
                  </div>
                )}
              </div>
            </div>
          )}
          
          {/* Grille de livres/séries */}
          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 h-64 animate-pulse">
                  <div className="flex space-x-4">
                    <div className="w-16 h-24 bg-gray-200 dark:bg-gray-700 rounded"></div>
                    <div className="flex-1 space-y-3">
                      <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
                      <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2"></div>
                      <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-5/6"></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {displayedBooks.length > 0 ? (
                displayedBooks.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => handleItemClick(item)}
                    className="cursor-pointer bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow"
                  >
                    {item.isSeriesCard ? (
                      <SeriesCard
                        series={item}
                        isOwned={item.isLibrarySeries}
                        showProgress={item.isLibrarySeries}
                        progressInfo={item.isLibrarySeries ? {
                          completed: item.completedBooks,
                          total: item.totalBooks
                        } : null}
                      />
                    ) : (
                      <div className="p-4">
                        {/* Badges de pertinence et catégorie (en mode recherche) */}
                        {isSearchMode && (
                          <div className="flex justify-between mb-2">
                            {item.relevanceInfo && (
                              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium text-white ${item.relevanceInfo.color}`}>
                                {item.relevanceInfo.icon} {item.relevanceInfo.label}
                              </span>
                            )}
                            {item.categoryBadge && (
                              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${item.categoryBadge.class}`}>
                                {item.categoryBadge.emoji} {item.categoryBadge.text}
                              </span>
                            )}
                          </div>
                        )}
                        
                        <div className="flex items-start space-x-4">
                          <div className="w-16 h-24 bg-gray-100 dark:bg-gray-700 rounded flex-shrink-0 overflow-hidden">
                            {item.cover_url ? (
                              <img 
                                src={item.cover_url} 
                                alt={item.title}
                                className="w-full h-full object-cover"
                              />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center">
                                <span className="text-gray-400 text-2xl">📖</span>
                              </div>
                            )}
                          </div>
                          
                          <div className="flex-1 min-w-0">
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1 line-clamp-2">
                              {item.title}
                            </h3>
                            
                            <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                              {item.author}
                            </p>
                            
                            <div className="flex flex-wrap gap-2">
                              {item.saga && (
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-300">
                                  📖 {item.saga}
                                  {item.volume_number && ` - T.${item.volume_number}`}
                                </span>
                              )}
                              
                              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                item.status === 'completed' 
                                  ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300' 
                                  : item.status === 'reading'
                                    ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300'
                                    : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                              }`}>
                                {item.status === 'completed' ? 'Terminé' : 
                                 item.status === 'reading' ? 'En cours' : 'À lire'}
                              </span>
                              
                              {/* Badge Open Library */}
                              {item.isFromOpenLibrary && (
                                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300">
                                  {item.isOwned ? '✓ Possédé' : '+ Ajouter'}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                ))
              ) : (
                <div className="col-span-full text-center py-12">
                  <div className="mx-auto w-24 h-24 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center mb-4">
                    <span className="text-4xl">📚</span>
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                    {isSearchMode 
                      ? `Aucun résultat pour "${lastSearchTerm}"` 
                      : 'Aucun livre dans cette catégorie'}
                  </h3>
                  <p className="text-gray-500 dark:text-gray-400">
                    {isSearchMode 
                      ? 'Essayez avec un autre terme de recherche' 
                      : 'Ajoutez des livres pour commencer votre collection'}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
      
      {/* Modals */}
      {showBookModal && selectedBook && (
        <BookDetailModal
          book={selectedBook}
          isOpen={showBookModal}
          onClose={() => {
            setSelectedBook(null);
            setShowBookModal(false);
          }}
          onUpdate={handleUpdateBook}
          onDelete={handleDeleteBook}
          onAddFromOpenLibrary={handleAddFromOpenLibrary}
        />
      )}
      
      {showSeriesModal && selectedSeries && (
        <SeriesDetailModal
          series={selectedSeries}
          isOpen={showSeriesModal}
          onClose={() => {
            setSelectedSeries(null);
            setShowSeriesModal(false);
          }}
          onUpdate={loadBooks}
        />
      )}
      
      {showProfileModal && (
        <ProfileModal
          isOpen={showProfileModal}
          onClose={() => setShowProfileModal(false)}
        />
      )}
      
      {/* Toast notifications */}
      <Toaster position="bottom-right" />
    </div>
  );
}

// Main App Component
function App() {
  return (
    <Router>
      <ThemeProvider>
        <AuthProvider>
          <AppWithAuth />
        </AuthProvider>
      </ThemeProvider>
    </Router>
  );
}

// App with Auth Wrapper
function AppWithAuth() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-green-500"></div>
      </div>
    );
  }

  return user ? <AppContent /> : <LoginPage />;
}

export default App;