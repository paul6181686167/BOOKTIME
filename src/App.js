import React, { useState, useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import toast from 'react-hot-toast';
import { ThemeProvider } from './contexts/ThemeContext';
import { UserLanguageProvider } from './contexts/UserLanguageContext';
import { adaptiveBookService as bookService } from './services/mockBookService';
import './App.css';

function AppContent() {
  const [books, setBooks] = useState([]);
  const [series, setSeries] = useState([]);
  const [filteredBooks, setFilteredBooks] = useState([]);
  const [filteredSeries, setFilteredSeries] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('roman');
  const [activeStatus, setActiveStatus] = useState('all');
  const [viewMode, setViewMode] = useState('books'); // 'books' ou 'series'
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedBook, setSelectedBook] = useState(null);
  const [selectedSeries, setSelectedSeries] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  // Charger les données au démarrage
  useEffect(() => {
    loadBooks();
    loadSeries();
    loadStats();
  }, []);

  // Filtrer les livres selon l'onglet actif, le statut et la recherche
  useEffect(() => {
    let filtered = books.filter(book => book.category === activeTab);
    
    if (activeStatus !== 'all') {
      filtered = filtered.filter(book => book.status === activeStatus);
    }
    
    if (searchTerm) {
      filtered = filtered.filter(book => 
        book.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        book.author.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (book.saga && book.saga.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }
    
    setFilteredBooks(filtered);
  }, [books, activeTab, activeStatus, searchTerm]);

  // Filtrer les séries
  useEffect(() => {
    let filtered = series.filter(serie => serie.category === activeTab);
    
    if (searchTerm) {
      filtered = filtered.filter(serie => 
        serie.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        serie.author.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    setFilteredSeries(filtered);
  }, [series, activeTab, searchTerm]);

  const loadBooks = async () => {
    try {
      setLoading(true);
      const data = await bookService.getBooks();
      setBooks(data);
    } catch (error) {
      console.error('Erreur lors du chargement des livres:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadSeries = async () => {
    try {
      const data = await bookService.getSeries();
      setSeries(data.series || []);
    } catch (error) {
      console.error('Erreur lors du chargement des séries:', error);
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
      await loadSeries();
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
      await loadSeries();
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
      await loadSeries();
      await loadStats();
      setSelectedBook(null);
      toast.success('Livre supprimé !');
    } catch (error) {
      console.error('Erreur lors de la suppression du livre:', error);
      toast.error('Erreur lors de la suppression');
    }
  };

  const handleSeriesClick = async (seriesName) => {
    try {
      const seriesDetails = await bookService.getSeriesDetails(seriesName);
      setSelectedSeries(seriesDetails);
    } catch (error) {
      console.error('Erreur lors du chargement des détails de la série:', error);
      toast.error('Erreur lors du chargement des détails de la série');
    }
  };

  // Composant Header simplifié
  const Header = () => (
    <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-6">
          <div className="flex items-center">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              📚 BOOKTIME
            </h1>
          </div>
          <div className="flex items-center space-x-4">
            <input
              type="text"
              placeholder={viewMode === 'series' ? "Rechercher une série..." : "Rechercher un livre..."}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
            />
            <div className="flex bg-gray-100 dark:bg-gray-700 rounded-md p-1">
              <button
                onClick={() => setViewMode('books')}
                className={`px-3 py-1 rounded text-sm ${
                  viewMode === 'books' 
                    ? 'bg-white dark:bg-gray-600 shadow-sm' 
                    : 'text-gray-600 dark:text-gray-400'
                }`}
              >
                📚 Livres
              </button>
              <button
                onClick={() => setViewMode('series')}
                className={`px-3 py-1 rounded text-sm ${
                  viewMode === 'series' 
                    ? 'bg-white dark:bg-gray-600 shadow-sm' 
                    : 'text-gray-600 dark:text-gray-400'
                }`}
              >
                📖 Séries
              </button>
            </div>
            <button
              onClick={() => setShowAddModal(true)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              ➕ Ajouter
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
        <nav className="-mb-px flex space-x-8">
          {['roman', 'bd', 'manga'].map((category) => (
            <button
              key={category}
              onClick={() => setActiveTab(category)}
              className={`py-2 px-1 border-b-2 font-medium text-sm capitalize ${
                activeTab === category
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
              }`}
            >
              {category}
            </button>
          ))}
        </nav>
      </div>
      {viewMode === 'books' && (
        <div className="mt-4">
          <div className="flex space-x-4">
            {['all', 'to_read', 'reading', 'completed'].map((status) => (
              <button
                key={status}
                onClick={() => setActiveStatus(status)}
                className={`px-3 py-1 rounded-full text-sm ${
                  activeStatus === status
                    ? 'bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-100'
                    : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                }`}
              >
                {status === 'all' ? 'Tous' : 
                 status === 'to_read' ? 'À lire' :
                 status === 'reading' ? 'En cours' : 'Terminés'}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  // Composant Stats
  const StatsPanel = () => (
    <div className="mb-6 grid grid-cols-2 md:grid-cols-4 gap-4">
      <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          {stats.total_books || 0}
        </h3>
        <p className="text-gray-600 dark:text-gray-400">Total Livres</p>
      </div>
      <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border">
        <h3 className="text-lg font-semibold text-green-600">
          {stats.completed_books || 0}
        </h3>
        <p className="text-gray-600 dark:text-gray-400">Terminés</p>
      </div>
      <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border">
        <h3 className="text-lg font-semibold text-yellow-600">
          {stats.reading_books || 0}
        </h3>
        <p className="text-gray-600 dark:text-gray-400">En cours</p>
      </div>
      <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border">
        <h3 className="text-lg font-semibold text-purple-600">
          {stats.sagas_count || 0}
        </h3>
        <p className="text-gray-600 dark:text-gray-400">Séries</p>
      </div>
    </div>
  );

  // Composant Grille de livres
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

    if (filteredBooks.length === 0) {
      return (
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400">
            Aucun livre trouvé. Ajoutez votre premier livre !
          </p>
        </div>
      );
    }

    return (
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {filteredBooks.map((book) => (
          <div
            key={book.id || book._id}
            onClick={() => setSelectedBook(book)}
            className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-3 cursor-pointer hover:shadow-lg transition-shadow"
          >
            <div className="aspect-[2/3] bg-gray-100 dark:bg-gray-700 rounded mb-2 flex items-center justify-center">
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
            <h3 className="font-medium text-sm text-gray-900 dark:text-white truncate">
              {book.title}
            </h3>
            <p className="text-xs text-gray-600 dark:text-gray-400 truncate">
              {book.author}
            </p>
            {book.saga && (
              <p className="text-xs text-purple-600 dark:text-purple-400 truncate">
                📚 {book.saga}
              </p>
            )}
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

  // Composant Grille de séries
  const SeriesGrid = () => {
    if (loading) {
      return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="bg-gray-200 dark:bg-gray-700 h-32 rounded-lg animate-pulse"></div>
          ))}
        </div>
      );
    }

    if (filteredSeries.length === 0) {
      return (
        <div className="text-center py-12">
          <p className="text-gray-500 dark:text-gray-400">
            Aucune série trouvée. Ajoutez des livres avec des sagas !
          </p>
        </div>
      );
    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredSeries.map((serie) => (
          <div
            key={serie.name}
            onClick={() => handleSeriesClick(serie.name)}
            className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 cursor-pointer hover:shadow-lg transition-shadow"
          >
            <div className="flex items-start space-x-4">
              <div className="w-16 h-20 bg-gray-100 dark:bg-gray-700 rounded flex items-center justify-center flex-shrink-0">
                {serie.cover_url ? (
                  <img
                    src={serie.cover_url}
                    alt={serie.name}
                    className="w-full h-full object-cover rounded"
                  />
                ) : (
                  <span className="text-2xl">📚</span>
                )}
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-gray-900 dark:text-white truncate">
                  {serie.name}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                  {serie.author}
                </p>
                <div className="mt-2 flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
                  <span>{serie.total_books} livres</span>
                  <span>{serie.completed_books} terminés</span>
                </div>
                <div className="mt-2">
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-green-500 h-2 rounded-full"
                      style={{
                        width: `${serie.total_books > 0 ? (serie.completed_books / serie.total_books) * 100 : 0}%`
                      }}
                    ></div>
                  </div>
                </div>
              </div>
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
      description: '',
      saga: '',
      volume_number: ''
    });

    const handleSubmit = (e) => {
      e.preventDefault();
      if (formData.title && formData.author) {
        const bookData = {
          ...formData,
          volume_number: formData.volume_number ? parseInt(formData.volume_number) : undefined
        };
        handleAddBook(bookData);
      }
    };

    if (!showAddModal) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
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
                <option value="bd">BD</option>
                <option value="manga">Manga</option>
              </select>
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Série/Saga
              </label>
              <input
                type="text"
                value={formData.saga}
                onChange={(e) => setFormData({...formData, saga: e.target.value})}
                placeholder="Ex: Le Seigneur des Anneaux"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Numéro de tome
              </label>
              <input
                type="number"
                value={formData.volume_number}
                onChange={(e) => setFormData({...formData, volume_number: e.target.value})}
                placeholder="1, 2, 3..."
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              />
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

  // Modal de détails simplifié
  const BookDetailModal = () => {
    if (!selectedBook) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
          <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
            {selectedBook.title}
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-2">
            <strong>Auteur:</strong> {selectedBook.author}
          </p>
          <p className="text-gray-600 dark:text-gray-400 mb-2">
            <strong>Catégorie:</strong> {selectedBook.category}
          </p>
          {selectedBook.saga && (
            <p className="text-gray-600 dark:text-gray-400 mb-2">
              <strong>Série:</strong> {selectedBook.saga}
              {selectedBook.volume_number && ` - Tome ${selectedBook.volume_number}`}
            </p>
          )}
          <p className="text-gray-600 dark:text-gray-400 mb-4">
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
                handleUpdateBook(selectedBook.id || selectedBook._id, { status: newStatus });
              }}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
            >
              Changer Statut
            </button>
            <button
              onClick={() => {
                if (window.confirm('Supprimer ce livre ?')) {
                  handleDeleteBook(selectedBook.id || selectedBook._id);
                }
              }}
              className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
            >
              Supprimer
            </button>
            <button
              onClick={() => setSelectedBook(null)}
              className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
            >
              Fermer
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Modal de détails de série
  const SeriesDetailModal = () => {
    if (!selectedSeries) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                📚 {selectedSeries.name}
              </h2>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                par {selectedSeries.author}
              </p>
            </div>
            <button
              onClick={() => setSelectedSeries(null)}
              className="text-gray-400 hover:text-gray-600 text-2xl"
            >
              ×
            </button>
          </div>

          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{selectedSeries.stats.total_books}</div>
              <div className="text-sm text-gray-500">Total</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{selectedSeries.stats.completed_books}</div>
              <div className="text-sm text-gray-500">Terminés</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">{selectedSeries.stats.reading_books}</div>
              <div className="text-sm text-gray-500">En cours</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-600">{selectedSeries.stats.to_read_books}</div>
              <div className="text-sm text-gray-500">À lire</div>
            </div>
          </div>

          <div className="mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
              Livres de la série
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {selectedSeries.books.map((book) => (
                <div
                  key={book.id || book._id}
                  onClick={() => {
                    setSelectedSeries(null);
                    setSelectedBook(book);
                  }}
                  className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 cursor-pointer hover:shadow-md transition-shadow"
                >
                  <div className="aspect-[2/3] bg-gray-100 dark:bg-gray-600 rounded mb-2 flex items-center justify-center">
                    {book.cover_url ? (
                      <img
                        src={book.cover_url}
                        alt={book.title}
                        className="w-full h-full object-cover rounded"
                      />
                    ) : (
                      <span className="text-2xl">📖</span>
                    )}
                  </div>
                  <h4 className="font-medium text-xs text-gray-900 dark:text-white truncate">
                    {book.volume_number && `T${book.volume_number}. `}{book.title}
                  </h4>
                  <div className="mt-1">
                    <span className={`inline-block px-1 py-0.5 rounded text-xs ${
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
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
      <Header />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <StatsPanel />
        <TabNavigation />
        {viewMode === 'books' ? <BookGrid /> : <SeriesGrid />}
      </main>

      <AddBookModal />
      <BookDetailModal />
      <SeriesDetailModal />

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
  );
}

function App() {
  return (
    <ThemeProvider>
      <UserLanguageProvider>
        <AppContent />
      </UserLanguageProvider>
    </ThemeProvider>
  );
}

export default App;