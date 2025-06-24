import React, { useState, useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import toast from 'react-hot-toast';
import { ThemeProvider } from './contexts/ThemeContext';
import { UserLanguageProvider } from './contexts/UserLanguageContext';
import Header from './components/Header';
import TabNavigation from './components/TabNavigation';
import BookGrid from './components/BookGrid';
import AddBookModal from './components/AddBookModal';
import BookDetailModal from './components/BookDetailModal';
import ExtendedStatsPanel from './components/ExtendedStatsPanel';
import AuthorsPanel from './components/AuthorsPanel';
import SagasPanel from './components/SagasPanel';
import AdvancedOpenLibrarySearch from './components/AdvancedOpenLibrarySearch';
import { bookService } from './services/bookService';
import './App.css';

function AppContent() {
  const [books, setBooks] = useState([]);
  const [filteredBooks, setFilteredBooks] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('roman');
  const [activeStatus, setActiveStatus] = useState('all');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showOpenLibraryModal, setShowOpenLibraryModal] = useState(false);
  const [selectedBook, setSelectedBook] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState('books'); // 'books', 'authors', 'sagas'
  const [selectedAuthorBooks, setSelectedAuthorBooks] = useState(null);
  const [selectedSagaBooks, setSelectedSagaBooks] = useState(null);
  const [currentContext, setCurrentContext] = useState(null); // Pour afficher le contexte actuel

  // Charger les livres au démarrage
  useEffect(() => {
    loadBooks();
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
        book.author.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    setFilteredBooks(filtered);
  }, [books, activeTab, activeStatus, searchTerm]);

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

  const loadStats = async () => {
    try {
      const data = await bookService.getStats();
      setStats(data);
    } catch (error) {
      console.error('Erreur lors du chargement des statistiques:', error);
    }
  };

  const handleAuthorSelect = (books, author) => {
    setSelectedAuthorBooks(books);
    setCurrentContext({
      type: 'author',
      name: author.name,
      data: author
    });
    setViewMode('books');
  };

  const handleSagaSelect = (books, saga) => {
    setSelectedSagaBooks(books);
    setCurrentContext({
      type: 'saga',
      name: saga.name,
      data: saga
    });
    setViewMode('books');
  };

  const handleBackToAll = () => {
    setSelectedAuthorBooks(null);
    setSelectedSagaBooks(null);
    setCurrentContext(null);
    setViewMode('books');
  };

  const getCurrentBooks = () => {
    if (selectedAuthorBooks) return selectedAuthorBooks;
    if (selectedSagaBooks) return selectedSagaBooks;
    return filteredBooks;
  };

  const handleAddBook = async (bookData) => {
    try {
      await bookService.createBook(bookData);
      await loadBooks();
      await loadStats();
      setShowAddModal(false);
      // Si on est dans une vue spécifique, rafraîchir
      if (currentContext) {
        if (currentContext.type === 'author') {
          const books = await bookService.getBooksByAuthor(currentContext.name);
          setSelectedAuthorBooks(books);
        } else if (currentContext.type === 'saga') {
          const books = await bookService.getBooksBySaga(currentContext.name);
          setSelectedSagaBooks(books);
        }
      }
    } catch (error) {
      console.error('Erreur lors de l\'ajout du livre:', error);
    }
  };

  const handleOpenLibraryImport = async (importedBook) => {
    try {
      await loadBooks();
      await loadStats();
      setShowOpenLibraryModal(false);
      toast.success(`"${importedBook.title}" ajouté à votre collection !`);
      
      // Si on est dans une vue spécifique, rafraîchir
      if (currentContext) {
        if (currentContext.type === 'author') {
          const books = await bookService.getBooksByAuthor(currentContext.name);
          setSelectedAuthorBooks(books);
        } else if (currentContext.type === 'saga') {
          const books = await bookService.getBooksBySaga(currentContext.name);
          setSelectedSagaBooks(books);
        }
      }
    } catch (error) {
      console.error('Erreur lors du rafraîchissement après import:', error);
    }
  };

  const handleUpdateBook = async (bookId, updates) => {
    try {
      await bookService.updateBook(bookId, updates);
      await loadBooks();
      await loadStats();
      setSelectedBook(null);
      // Si on est dans une vue spécifique, rafraîchir
      if (currentContext) {
        if (currentContext.type === 'author') {
          const books = await bookService.getBooksByAuthor(currentContext.name);
          setSelectedAuthorBooks(books);
        } else if (currentContext.type === 'saga') {
          const books = await bookService.getBooksBySaga(currentContext.name);
          setSelectedSagaBooks(books);
        }
      }
    } catch (error) {
      console.error('Erreur lors de la mise à jour du livre:', error);
    }
  };

  const handleDeleteBook = async (bookId) => {
    try {
      await bookService.deleteBook(bookId);
      await loadBooks();
      await loadStats();
      setSelectedBook(null);
      // Si on est dans une vue spécifique, rafraîchir
      if (currentContext) {
        if (currentContext.type === 'author') {
          const books = await bookService.getBooksByAuthor(currentContext.name);
          setSelectedAuthorBooks(books);
        } else if (currentContext.type === 'saga') {
          const books = await bookService.getBooksBySaga(currentContext.name);
          setSelectedSagaBooks(books);
        }
      }
    } catch (error) {
      console.error('Erreur lors de la suppression du livre:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors">
      <Header 
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        onAddBook={() => setShowAddModal(true)}
        onOpenLibrarySearch={() => setShowOpenLibraryModal(true)}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        currentContext={currentContext}
        onBackToAll={handleBackToAll}
      />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <ExtendedStatsPanel stats={stats} />
        
        {viewMode === 'books' && (
          <>
            {!currentContext && (
              <TabNavigation 
                activeTab={activeTab}
                onTabChange={setActiveTab}
                activeStatus={activeStatus}
                onStatusChange={setActiveStatus}
              />
            )}
            
            {currentContext && (
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 mb-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-medium text-gray-900 dark:text-white">
                      {currentContext.type === 'author' ? 'Livres de' : 'Saga'} : {currentContext.name}
                    </h2>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {getCurrentBooks().length} livre{getCurrentBooks().length > 1 ? 's' : ''}
                      {currentContext.type === 'saga' && currentContext.data && 
                        ` • ${currentContext.data.completed_books} terminé${currentContext.data.completed_books > 1 ? 's' : ''}`
                      }
                    </p>
                  </div>
                  <button
                    onClick={handleBackToAll}
                    className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
                  >
                    Retour à tous les livres
                  </button>
                </div>
              </div>
            )}
            
            <BookGrid 
              books={getCurrentBooks()}
              loading={loading}
              onBookClick={setSelectedBook}
            />
          </>
        )}
        
        {viewMode === 'authors' && (
          <AuthorsPanel onAuthorSelect={handleAuthorSelect} />
        )}
        
        {viewMode === 'sagas' && (
          <SagasPanel onSagaSelect={handleSagaSelect} />
        )}
      </main>

      {/* Modals */}
      {showAddModal && (
        <AddBookModal
          onClose={() => setShowAddModal(false)}
          onAdd={handleAddBook}
          defaultCategory={activeTab}
        />
      )}

      {showOpenLibraryModal && (
        <OpenLibrarySearch
          onImport={handleOpenLibraryImport}
          onClose={() => setShowOpenLibraryModal(false)}
          defaultCategory={activeTab}
        />
      )}

      {selectedBook && (
        <BookDetailModal
          book={selectedBook}
          onClose={() => setSelectedBook(null)}
          onUpdate={handleUpdateBook}
          onDelete={handleDeleteBook}
        />
      )}

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