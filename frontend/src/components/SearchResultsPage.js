import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { ArrowLeftIcon, AdjustmentsHorizontalIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

// Import des hooks et composants
import { useAdvancedSearch } from '../hooks/useAdvancedSearch';
import AdvancedSearchBar from './AdvancedSearchBar';
import { useAuth } from '../App';

// Service de livres (on récupère depuis App.js)
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
}

const bookService = new BookService();

function SearchResultsPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const { user } = useAuth();
  
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('grid'); // 'grid' ou 'list'

  // Récupérer les paramètres de recherche depuis l'URL
  const initialSearchTerm = searchParams.get('q') || '';
  const initialFilters = {
    category: searchParams.get('category') || '',
    status: searchParams.get('status') || '',
    author: searchParams.get('author') || '',
    saga: searchParams.get('saga') || '',
    yearFrom: searchParams.get('yearFrom') || '',
    yearTo: searchParams.get('yearTo') || '',
    minRating: searchParams.get('minRating') || '',
    hasReview: searchParams.get('hasReview') === 'true'
  };

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

  // Initialiser la recherche avec les paramètres URL
  useEffect(() => {
    if (initialSearchTerm) {
      setSearchTerm(initialSearchTerm);
    }
    // Appliquer les filtres initiaux s'ils existent
    const hasFilters = Object.values(initialFilters).some(value => value !== '' && value !== false);
    if (hasFilters) {
      setFilters(initialFilters);
    }
  }, []);

  // Mettre à jour l'URL quand la recherche change
  useEffect(() => {
    const params = new URLSearchParams();
    
    if (searchTerm) {
      params.set('q', searchTerm);
    }
    
    // Ajouter les filtres actifs
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== '' && value !== false) {
        params.set(key, value.toString());
      }
    });

    // Mettre à jour l'URL sans recharger la page
    const newUrl = params.toString() ? `?${params.toString()}` : '';
    if (newUrl !== location.search) {
      setSearchParams(params);
    }
  }, [searchTerm, filters, setSearchParams, location.search]);

  // Charger les livres
  useEffect(() => {
    if (user) {
      loadBooks();
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

  // Navigation vers fiche livre
  const handleBookClick = (book) => {
    navigate(`/livre/${book.id}`);
  };

  // Navigation vers fiche auteur
  const handleAuthorClick = (authorName) => {    
    navigate(`/auteur/${encodeURIComponent(authorName)}`);
  };

  // Retour vers la page principale
  const handleBackToHome = () => {
    navigate('/');
  };

  // Gestionnaire pour effacer la recherche et retourner à l'accueil
  const handleClearAndGoHome = () => {
    clearSearch();
    navigate('/');
  };

  // Composant pour afficher les résultats en grille
  const GridView = () => (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8 gap-4">
      {filteredBooks.map((book) => (
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
            <p className="text-xs text-gray-600 dark:text-gray-400 truncate font-medium">
              {book.title}
            </p>
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleAuthorClick(book.author);
              }}
              className="text-xs text-blue-600 dark:text-blue-400 hover:underline truncate block"
            >
              {book.author}
            </button>
            {book.publication_year && (
              <p className="text-xs text-gray-400 dark:text-gray-500">
                {book.publication_year}
              </p>
            )}
          </div>
        </div>
      ))}
    </div>
  );

  // Composant pour afficher les résultats en liste
  const ListView = () => (
    <div className="space-y-4">
      {filteredBooks.map((book) => (
        <div
          key={book.id}
          onClick={() => handleBookClick(book)}
          className="cursor-pointer bg-white dark:bg-gray-800 rounded-lg p-4 shadow-sm hover:shadow-md transition-all border border-gray-200 dark:border-gray-700"
        >
          <div className="flex items-start space-x-4">
            <div className="w-16 h-24 bg-gray-100 dark:bg-gray-700 rounded flex items-center justify-center overflow-hidden flex-shrink-0">
              {book.cover_url ? (
                <img
                  src={book.cover_url}
                  alt={book.title}
                  className="w-full h-full object-cover rounded"
                />
              ) : (
                <span className="text-xl">📖</span>
              )}
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
                {book.title}
              </h3>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleAuthorClick(book.author);
                }}
                className="text-blue-600 dark:text-blue-400 hover:underline text-sm"
              >
                {book.author}
              </button>
              <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500 dark:text-gray-400">
                <span className="flex items-center">
                  {book.category === 'roman' && '📚'}
                  {book.category === 'bd' && '🎨'}
                  {book.category === 'manga' && '🇯🇵'}
                  <span className="ml-1 capitalize">{book.category}</span>
                </span>
                <span className="flex items-center">
                  {book.status === 'reading' && '📖 En cours'}
                  {book.status === 'completed' && '✅ Terminé'}
                  {book.status === 'to_read' && '📚 À lire'}
                </span>
                {book.publication_year && (
                  <span>{book.publication_year}</span>
                )}
                {book.rating && (
                  <span className="flex items-center">
                    ⭐ {book.rating}/5
                  </span>
                )}
              </div>
              {book.description && (
                <p className="text-sm text-gray-600 dark:text-gray-300 mt-2 line-clamp-2">
                  {book.description}
                </p>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        {/* Header */}
        <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-40">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between py-4">
              <button
                onClick={handleBackToHome}
                className="flex items-center space-x-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
              >
                <ArrowLeftIcon className="h-5 w-5" />
                <span>Retour</span>
              </button>
              <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                Recherche...
              </h1>
              <div></div>
            </div>
          </div>
        </header>

        {/* Loading */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header avec barre de recherche */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-4">
            {/* Bouton retour */}
            <button
              onClick={handleBackToHome}
              className="flex items-center space-x-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              <ArrowLeftIcon className="h-5 w-5" />
              <span className="hidden sm:block">Retour</span>
            </button>

            {/* Barre de recherche centrale */}
            <div className="flex-1 max-w-2xl mx-4">
              <AdvancedSearchBar
                searchTerm={searchTerm}
                onSearchChange={setSearchTerm}
                books={books}
                filters={filters}
                onFiltersChange={setFilters}
                onOpenLibrarySearch={() => {}} // Désactivé sur la page de recherche
              />
            </div>

            {/* Actions */}
            <div className="flex items-center space-x-2">
              {/* Sélecteur de vue */}
              <div className="flex items-center bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-2 rounded-md transition-colors ${
                    viewMode === 'grid'
                      ? 'bg-white dark:bg-gray-600 text-blue-600 dark:text-blue-400 shadow-sm'
                      : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                  }`}
                  title="Vue grille"
                >
                  <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M3 4a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H4a1 1 0 01-1-1V4zm6 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V4zm-6 8a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H4a1 1 0 01-1-1v-4zm6 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" clipRule="evenodd" />
                  </svg>
                </button>
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2 rounded-md transition-colors ${
                    viewMode === 'list'
                      ? 'bg-white dark:bg-gray-600 text-blue-600 dark:text-blue-400 shadow-sm'
                      : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                  }`}
                  title="Vue liste"
                >
                  <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M3 4a1 1 0 000 2h14a1 1 0 100-2H3zm0 4a1 1 0 000 2h14a1 1 0 100-2H3zm0 4a1 1 0 000 2h14a1 1 0 100-2H3z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Contenu principal */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Titre et statistiques */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Résultats de recherche
              </h1>
              {searchTerm && (
                <p className="text-gray-600 dark:text-gray-400 mt-1">
                  pour "{searchTerm}"
                </p>
              )}
            </div>
            
            {/* Statistiques */}
            <div className="text-right">
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {filteredBooks.length} résultat{filteredBooks.length > 1 ? 's' : ''}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                sur {books.length} livre{books.length > 1 ? 's' : ''}
              </p>
            </div>
          </div>

          {/* Filtres actifs */}
          {searchStats.hasActiveFilters && (
            <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <AdjustmentsHorizontalIcon className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                  <span className="text-sm text-blue-700 dark:text-blue-300">
                    Filtres actifs
                  </span>
                </div>
                <button
                  onClick={handleClearAndGoHome}
                  className="text-sm text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 underline"
                >
                  Effacer et retourner à l'accueil
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Résultats */}
        {filteredBooks.length === 0 ? (
          <div className="text-center py-12">
            <div className="max-w-md mx-auto">
              <span className="text-6xl mb-4 block">🔍</span>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Aucun résultat trouvé
              </h2>
              <p className="text-gray-500 dark:text-gray-400 mb-4">
                {searchTerm 
                  ? `Aucun livre ne correspond à votre recherche "${searchTerm}"`
                  : 'Aucun livre ne correspond à vos filtres'
                }
              </p>
              <div className="space-y-2">
                <button
                  onClick={handleClearAndGoHome}
                  className="block w-full px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Retourner à l'accueil
                </button>
                <button
                  onClick={clearSearch}
                  className="block w-full px-4 py-2 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-md hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                >
                  Effacer les filtres
                </button>
              </div>
            </div>
          </div>
        ) : (
          <>
            {/* Affichage des résultats */}
            {viewMode === 'grid' ? <GridView /> : <ListView />}
          </>
        )}
      </main>
    </div>
  );
}

export default SearchResultsPage;

const SearchResultsPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'list'
  const bookService = new BookService();

  // Parse query parameters from URL
  const queryParams = new URLSearchParams(location.search);
  const initialSearchTerm = queryParams.get('q') || '';
  
  // Initialize filters from URL parameters
  const initialFilters = {
    category: queryParams.get('category') || '',
    status: queryParams.get('status') || '',
    author: queryParams.get('author') || '',
    saga: queryParams.get('saga') || '',
    yearStart: queryParams.get('yearStart') || '',
    yearEnd: queryParams.get('yearEnd') || '',
    rating: queryParams.get('rating') ? parseInt(queryParams.get('rating')) : 0,
  };

  // Use the advanced search hook
  const {
    searchTerm,
    setSearchTerm,
    filters,
    setFilters,
    filteredBooks,
    searchStats,
    clearSearch
  } = useAdvancedSearch(books, initialSearchTerm, initialFilters);

  // Load books on component mount
  useEffect(() => {
    const loadBooks = async () => {
      try {
        setLoading(true);
        const data = await bookService.getBooks();
        setBooks(data);
      } catch (error) {
        console.error('Error loading books:', error);
      } finally {
        setLoading(false);
      }
    };

    loadBooks();
  }, []);

  // Update URL when search term or filters change
  useEffect(() => {
    const params = new URLSearchParams();
    
    if (searchTerm) params.set('q', searchTerm);
    
    // Add filters to URL
    if (filters.category) params.set('category', filters.category);
    if (filters.status) params.set('status', filters.status);
    if (filters.author) params.set('author', filters.author);
    if (filters.saga) params.set('saga', filters.saga);
    if (filters.yearStart) params.set('yearStart', filters.yearStart);
    if (filters.yearEnd) params.set('yearEnd', filters.yearEnd);
    if (filters.rating > 0) params.set('rating', filters.rating.toString());
    
    // Update URL without reloading the page
    navigate(`/recherche?${params.toString()}`, { replace: true });
  }, [searchTerm, filters, navigate]);

  // Handle book click
  const handleBookClick = (book) => {
    navigate(`/livre/${book.id}`);
  };

  // Handle back button click
  const handleBackClick = () => {
    navigate('/');
  };

  // Render book in grid view
  const renderBookGrid = (book) => (
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
      <div className="mt-2">
        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{book.title}</p>
        <p className="text-xs text-gray-600 dark:text-gray-400 truncate">{book.author}</p>
      </div>
    </div>
  );

  // Render book in list view
  const renderBookList = (book) => (
    <div 
      key={book.id}
      onClick={() => handleBookClick(book)}
      className="flex items-center p-3 border-b border-gray-200 dark:border-gray-700 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
    >
      <div className="h-16 w-12 flex-shrink-0 bg-gray-100 dark:bg-gray-700 rounded overflow-hidden mr-4">
        {book.cover_url ? (
          <img
            src={book.cover_url}
            alt={book.title}
            className="h-full w-full object-cover"
          />
        ) : (
          <div className="h-full w-full flex items-center justify-center">
            <span className="text-2xl">📖</span>
          </div>
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">{book.title}</p>
        <p className="text-xs text-gray-600 dark:text-gray-400">{book.author}</p>
        <div className="flex items-center mt-1">
          <span className="text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded-full text-gray-600 dark:text-gray-400">
            {book.category === 'roman' ? 'Roman' : book.category === 'bd' ? 'BD' : 'Manga'}
          </span>
          {book.saga && (
            <span className="ml-2 text-xs px-2 py-1 bg-blue-50 dark:bg-blue-900/20 rounded-full text-blue-600 dark:text-blue-400">
              {book.saga}
            </span>
          )}
        </div>
      </div>
      <div className="ml-4 flex-shrink-0">
        <span className={`inline-block w-3 h-3 rounded-full ${
          book.status === 'completed' ? 'bg-green-500' : 
          book.status === 'reading' ? 'bg-blue-500' : 'bg-yellow-500'
        }`}></span>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <button 
                onClick={handleBackClick}
                className="mr-4 p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                aria-label="Retour"
              >
                <ArrowLeftIcon className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              </button>
              <h1 className="text-xl font-bold text-gray-900 dark:text-white">Résultats de recherche</h1>
            </div>
            
            <div className="flex items-center space-x-2">
              <button 
                onClick={() => setViewMode('grid')}
                className={`p-2 rounded-md ${viewMode === 'grid' 
                  ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' 
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'}`}
                aria-label="Vue grille"
              >
                <ViewGridIcon className="h-5 w-5" />
              </button>
              <button 
                onClick={() => setViewMode('list')}
                className={`p-2 rounded-md ${viewMode === 'list' 
                  ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400' 
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'}`}
                aria-label="Vue liste"
              >
                <ViewListIcon className="h-5 w-5" />
              </button>
            </div>
          </div>
          
          {/* Search bar */}
          <div className="py-3">
            <AdvancedSearchBar
              searchTerm={searchTerm}
              onSearchChange={setSearchTerm}
              books={books}
              filters={filters}
              onFiltersChange={setFilters}
            />
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Results summary */}
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white">
              {loading ? 'Chargement...' : 
                `${filteredBooks.length} résultat${filteredBooks.length !== 1 ? 's' : ''} pour "${searchTerm}"`}
            </h2>
            {searchStats.hasActiveFilters && (
              <button
                onClick={clearSearch}
                className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
              >
                Effacer les filtres
              </button>
            )}
          </div>
          
          {/* Active filters display */}
          {searchStats.hasActiveFilters && (
            <div className="mt-2 flex flex-wrap gap-2">
              {filters.category && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200">
                  Catégorie: {filters.category === 'roman' ? 'Roman' : filters.category === 'bd' ? 'BD' : 'Manga'}
                </span>
              )}
              {filters.status && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200">
                  Statut: {filters.status === 'completed' ? 'Terminé' : filters.status === 'reading' ? 'En cours' : 'À lire'}
                </span>
              )}
              {filters.author && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200">
                  Auteur: {filters.author}
                </span>
              )}
              {filters.saga && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200">
                  Saga: {filters.saga}
                </span>
              )}
              {(filters.yearStart || filters.yearEnd) && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200">
                  Année: {filters.yearStart || '...'} - {filters.yearEnd || '...'}
                </span>
              )}
              {filters.rating > 0 && (
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200">
                  Note: {filters.rating}+ ⭐
                </span>
              )}
            </div>
          )}
        </div>

        {/* Books display */}
        {loading ? (
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="bg-gray-200 dark:bg-gray-700 h-48 rounded-lg animate-pulse"></div>
            ))}
          </div>
        ) : filteredBooks.length === 0 ? (
          <div className="text-center py-12">
            <div className="max-w-md mx-auto">
              <span className="text-6xl mb-4 block">🔍</span>
              <p className="text-gray-500 dark:text-gray-400 text-lg mb-2">
                Aucun livre trouvé
              </p>
              <p className="text-gray-400 dark:text-gray-500 text-sm mb-4">
                Essayez de modifier vos critères de recherche
              </p>
              <button
                onClick={clearSearch}
                className="px-4 py-2 text-sm bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-md transition-colors"
              >
                Effacer la recherche
              </button>
            </div>
          </div>
        ) : viewMode === 'grid' ? (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {filteredBooks.map(book => renderBookGrid(book))}
          </div>
        ) : (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
            {filteredBooks.map(book => renderBookList(book))}
          </div>
        )}
      </main>
    </div>
  );
};

export default SearchResultsPage;
