import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeftIcon } from '@heroicons/react/24/outline';
import { Squares2X2Icon as ViewGridIcon, ListBulletIcon as ViewListIcon } from '@heroicons/react/24/outline';
import BookService from '../services/bookService';
import { useAdvancedSearch } from '../hooks/useAdvancedSearch';
import AdvancedSearchBar from './AdvancedSearchBar';

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
