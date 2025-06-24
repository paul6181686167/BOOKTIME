import React, { useState, useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import Header from './components/Header';
import TabNavigation from './components/TabNavigation';
import BookGrid from './components/BookGrid';
import AddBookModal from './components/AddBookModal';
import BookDetailModal from './components/BookDetailModal';
import ExtendedStatsPanel from './components/ExtendedStatsPanel';
import AuthorsPanel from './components/AuthorsPanel';
import SagasPanel from './components/SagasPanel';
import { bookService } from './services/bookService';
import './App.css';

function App() {
  const [books, setBooks] = useState([]);
  const [filteredBooks, setFilteredBooks] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('roman');
  const [activeStatus, setActiveStatus] = useState('all');
  const [showAddModal, setShowAddModal] = useState(false);
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
    <div className="min-h-screen bg-gray-50">
      <Header 
        searchTerm={searchTerm}
        onSearchChange={setSearchTerm}
        onAddBook={() => setShowAddModal(true)}
      />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <StatsPanel stats={stats} />
        
        <TabNavigation 
          activeTab={activeTab}
          onTabChange={setActiveTab}
          activeStatus={activeStatus}
          onStatusChange={setActiveStatus}
        />
        
        <BookGrid 
          books={filteredBooks}
          loading={loading}
          onBookClick={setSelectedBook}
        />
      </main>

      {/* Modals */}
      {showAddModal && (
        <AddBookModal
          onClose={() => setShowAddModal(false)}
          onAdd={handleAddBook}
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

export default App;