import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { ArrowLeftIcon, AdjustmentsHorizontalIcon, PlusIcon, CheckIcon, BookOpenIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

// Import des hooks et composants
import { useAdvancedSearch } from '../hooks/useAdvancedSearch';
import AdvancedSearchBar from './AdvancedSearchBar';
import { useAuth } from '../App';
import { API_BASE_URL } from '../config/environment';

// Service de livres (on récupère depuis App.js)
class BookService {
  constructor() {
    this.backendUrl = API_BASE_URL
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

// Mini-card pour les résultats du catalogue
const CatalogCard = ({ book, alreadyOwned, onAdd }) => {
  const navigate = useNavigate();
  const [adding, setAdding] = useState(false);
  const [added, setAdded] = useState(false);
  const catalogKey = book.ol_key ? (book.ol_key.startsWith('/') ? book.ol_key.slice(1) : book.ol_key) : null;
  const path = catalogKey ? `/catalogue/${catalogKey}` : null;

  const handleAdd = async () => {
    if (adding || added || alreadyOwned) return;
    setAdding(true);
    try {
      await onAdd(book);
      setAdded(true);
    } catch {
      // géré dans handleAddFromCatalog
    } finally {
      setAdding(false);
    }
  };

  const done = added || alreadyOwned;

  return (
    <div className="flex flex-col bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 overflow-hidden hover:shadow-md transition-shadow">
      <div
        className={`h-40 bg-gray-100 dark:bg-gray-700 flex items-center justify-center overflow-hidden ${path ? 'cursor-pointer' : ''}`}
        onClick={() => path && navigate(path)}
      >
        {book.cover_url ? (
          <img src={book.cover_url} alt={book.title} className="h-full w-full object-cover hover:scale-105 transition-transform duration-200" onError={(e) => { e.target.style.display = 'none'; }} />
        ) : (
          <BookOpenIcon className="h-10 w-10 text-gray-300" />
        )}
      </div>
      <div className="flex flex-col flex-1 p-3 gap-1">
        <p
          className={`text-xs font-semibold text-gray-900 dark:text-white line-clamp-2 leading-tight ${path ? 'cursor-pointer hover:text-blue-600 dark:hover:text-blue-400 transition-colors' : ''}`}
          onClick={() => path && navigate(path)}
        >{book.title}</p>
        <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-1">{book.author}</p>
        <div className="mt-auto pt-2">
          {done ? (
            <div className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400 font-medium">
              <CheckIcon className="h-4 w-4" />
              {alreadyOwned ? 'Dans ta bibliothèque' : 'Ajouté !'}
            </div>
          ) : (
            <button
              onClick={handleAdd}
              disabled={adding}
              className="btn-ripple w-full flex items-center justify-center gap-1.5 px-2 py-1.5 text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white rounded-lg transition-colors disabled:opacity-60"
            >
              {adding
                ? <span className="btn-spinner" style={{width:'0.65rem',height:'0.65rem',borderWidth:'1.5px'}} />
                : <PlusIcon className="h-3 w-3" />
              }
              {adding ? 'Ajout…' : 'Ajouter'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

function SearchResultsPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const { user } = useAuth();
  
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('grid'); // 'grid' ou 'list'
  const [catalogResults, setCatalogResults] = useState([]);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const catalogSearchTimer = useRef(null);

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
      // Gérer le format paginé {items: [...]} ou tableau direct
      setBooks(Array.isArray(data) ? data : (data.items || data.books || []));
    } catch (error) {
      console.error('Erreur lors du chargement des livres:', error);
      toast.error('Erreur lors du chargement des livres');
    } finally {
      setLoading(false);
    }
  };

  // Recherche dans le catalogue global (avec debounce)
  useEffect(() => {
    if (!searchTerm || searchTerm.trim().length < 2) {
      setCatalogResults([]);
      return;
    }
    clearTimeout(catalogSearchTimer.current);
    catalogSearchTimer.current = setTimeout(async () => {
      setCatalogLoading(true);
      try {
        const token = localStorage.getItem('token');
        const resp = await fetch(
          `${API_BASE_URL}/api/catalog/search?q=${encodeURIComponent(searchTerm.trim())}&limit=12`,
          { headers: token ? { Authorization: `Bearer ${token}` } : {} }
        );
        if (resp.ok) {
          const d = await resp.json();
          setCatalogResults(d.books || d.results || []);
        }
      } catch {
        // Silencieux
      } finally {
        setCatalogLoading(false);
      }
    }, 400);
    return () => clearTimeout(catalogSearchTimer.current);
  }, [searchTerm]);

  const handleAddFromCatalog = async (catalogBook) => {
    const token = localStorage.getItem('token');
    try {
      const resp = await fetch(`${API_BASE_URL}/api/books`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          title: catalogBook.title,
          author: catalogBook.author,
          category: catalogBook.category || 'roman',
          status: 'to_read',
          cover_url: catalogBook.cover_url || null,
          description: catalogBook.description || null,
          ol_key: catalogBook.ol_key || null,
        }),
      });
      if (!resp.ok) throw new Error();
      toast.success(`"${catalogBook.title}" ajouté à ta bibliothèque`);
      // Refresh local books list
      loadBooks();
    } catch {
      toast.error('Erreur lors de l\'ajout');
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

        {/* Résultats bibliothèque */}
        {filteredBooks.length === 0 && !searchTerm ? (
          <div className="text-center py-12">
            <div className="max-w-md mx-auto">
              <span className="text-6xl mb-4 block">🔍</span>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Aucun résultat trouvé
              </h2>
              <p className="text-gray-500 dark:text-gray-400 mb-4">
                Aucun livre ne correspond à vos filtres
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
        ) : filteredBooks.length > 0 ? (
          <>
            {viewMode === 'grid' ? <GridView /> : <ListView />}
          </>
        ) : null}

        {/* Section Catalogue global */}
        {searchTerm && searchTerm.trim().length >= 2 && (
          <div className="mt-10">
            <div className="flex items-center gap-2 mb-4 pb-2 border-b border-gray-200 dark:border-gray-700">
              <BookOpenIcon className="h-5 w-5 text-indigo-500" />
              <h2 className="text-base font-semibold text-gray-800 dark:text-gray-100">
                Dans le catalogue ({catalogResults.length > 0 ? `${catalogResults.length} résultat${catalogResults.length > 1 ? 's' : ''}` : '…'})
              </h2>
              {catalogLoading && (
                <div className="h-4 w-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin ml-2" />
              )}
            </div>

            {!catalogLoading && catalogResults.length === 0 && (
              <p className="text-sm text-gray-500 dark:text-gray-400 py-4 text-center">
                Aucun livre trouvé dans le catalogue pour cette recherche.
              </p>
            )}

            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {catalogResults.map((book, idx) => {
                const alreadyOwned = books.some(
                  (b) => b.title?.toLowerCase() === book.title?.toLowerCase() ||
                         (book.ol_key && b.ol_key === book.ol_key)
                );
                return (
                  <CatalogCard
                    key={book.ol_key || idx}
                    book={book}
                    alreadyOwned={alreadyOwned}
                    onAdd={handleAddFromCatalog}
                  />
                );
              })}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default SearchResultsPage;


