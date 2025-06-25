import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { 
  ArrowLeftIcon, 
  BookOpenIcon,
  CalendarIcon,
  UserIcon,
  BuildingLibraryIcon,
  IdentificationIcon,
  GlobeAltIcon,
  PhotoIcon,
  PlusIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';

const OpenLibraryBookPage = () => {
  const { workKey } = useParams();
  const navigate = useNavigate();
  const [book, setBook] = useState(null);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    loadBookDetails();
  }, [workKey]);

  const loadBookDetails = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`${backendUrl}/api/openlibrary/book/${workKey}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Livre non trouvé');
      }

      const data = await response.json();
      setBook(data);
    } catch (error) {
      console.error('Erreur lors du chargement du livre:', error);
      toast.error('Erreur lors du chargement du livre');
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  const addToLibrary = async () => {
    if (!book || book.in_user_library) return;
    
    try {
      setAdding(true);
      const token = localStorage.getItem('token');
      
      const bookData = {
        title: book.title,
        author: book.author || (book.authors && book.authors.length > 0 ? book.authors[0].name : 'Auteur inconnu'),
        category: book.category || 'roman',
        description: book.description || '',
        isbn: book.isbn || '',
        publication_year: book.publication_year,
        publisher: book.publisher || '',
        pages: book.pages,
        cover_url: book.cover_url || '',
        genre: book.subjects || []
      };

      const response = await fetch(`${backendUrl}/api/books`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(bookData)
      });

      if (!response.ok) {
        throw new Error('Erreur lors de l\'ajout');
      }

      const newBook = await response.json();
      toast.success(`"${book.title}" ajouté à votre bibliothèque !`);
      
      navigate(`/livre/${newBook.id}`);
    } catch (error) {
      console.error('Erreur lors de l\'ajout:', error);
      toast.error('Erreur lors de l\'ajout du livre');
    } finally {
      setAdding(false);
    }
  };

  const handleAuthorClick = (authorName) => {
    navigate(`/auteur/ol/${encodeURIComponent(authorName)}`);
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'bd': return '🎨';
      case 'manga': return '🇯🇵';
      default: return '📚';
    }
  };

  const getCategoryLabel = (category) => {
    switch (category) {
      case 'bd': return 'Bande Dessinée';
      case 'manga': return 'Manga';
      case 'roman': return 'Roman';
      default: return 'Livre';
    }
  };

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

  if (!book) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <span className="text-6xl mb-4 block">📚</span>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Livre non trouvé</h1>
          <button
            onClick={() => navigate('/')}
            className="text-blue-600 dark:text-blue-400 hover:underline"
          >
            Retour à la bibliothèque
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-4">
            <button
              onClick={() => navigate('/')}
              className="flex items-center space-x-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              <ArrowLeftIcon className="h-5 w-5" />
              <span>Retour à la bibliothèque</span>
            </button>
            
            <div className="flex items-center space-x-3">
              {book.in_user_library ? (
                <button
                  onClick={() => navigate(`/livre/${book.user_book_id}`)}
                  className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                >
                  <CheckCircleIcon className="h-4 w-4" />
                  <span>Dans ma bibliothèque</span>
                </button>
              ) : (
                <button
                  onClick={addToLibrary}
                  disabled={adding}
                  className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  <PlusIcon className="h-4 w-4" />
                  <span>{adding ? 'Ajout...' : 'Ajouter à ma bibliothèque'}</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1">
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 sticky top-8">
              <div className="mb-4">
                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300">
                  🌐 OpenLibrary
                </span>
              </div>

              <div className="aspect-[2/3] bg-gray-100 dark:bg-gray-700 rounded-xl overflow-hidden mb-6 shadow-inner">
                {book.cover_url ? (
                  <img
                    src={book.cover_url}
                    alt={book.title}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <PhotoIcon className="h-16 w-16 text-gray-400 dark:text-gray-500" />
                  </div>
                )}
              </div>

              <div className="flex items-center justify-center mb-4">
                <span className={`px-4 py-2 rounded-full text-sm font-medium ${
                  book.category === 'bd' ? 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300' :
                  book.category === 'manga' ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300' :
                  'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300'
                }`}>
                  {getCategoryIcon(book.category)} {getCategoryLabel(book.category)}
                </span>
              </div>
            </div>
          </div>

          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">{book.title}</h1>
              
              {book.authors && book.authors.length > 0 ? (
                <div className="mb-4">
                  {book.authors.map((author, index) => (
                    <button
                      key={index}
                      onClick={() => handleAuthorClick(author.name)}
                      className="text-xl text-blue-600 dark:text-blue-400 hover:underline mr-4 flex items-center space-x-2"
                    >
                      <UserIcon className="h-5 w-5" />
                      <span>{author.name}</span>
                    </button>
                  ))}
                </div>
              ) : book.author && (
                <button
                  onClick={() => handleAuthorClick(book.author)}
                  className="text-xl text-blue-600 dark:text-blue-400 hover:underline mb-4 flex items-center space-x-2"
                >
                  <UserIcon className="h-5 w-5" />
                  <span>{book.author}</span>
                </button>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                {book.publication_year && (
                  <div className="flex items-center space-x-2">
                    <CalendarIcon className="h-4 w-4 text-gray-400" />
                    <span className="text-gray-600 dark:text-gray-400">Année :</span>
                    <span className="font-medium text-gray-900 dark:text-white">{book.publication_year}</span>
                  </div>
                )}

                {book.publisher && (
                  <div className="flex items-center space-x-2">
                    <BuildingLibraryIcon className="h-4 w-4 text-gray-400" />
                    <span className="text-gray-600 dark:text-gray-400">Éditeur :</span>
                    <span className="font-medium text-gray-900 dark:text-white">{book.publisher}</span>
                  </div>
                )}

                {book.isbn && (
                  <div className="flex items-center space-x-2">
                    <IdentificationIcon className="h-4 w-4 text-gray-400" />
                    <span className="text-gray-600 dark:text-gray-400">ISBN :</span>
                    <span className="font-medium text-gray-900 dark:text-white">{book.isbn}</span>
                  </div>
                )}

                {book.pages && (
                  <div className="flex items-center space-x-2">
                    <BookOpenIcon className="h-4 w-4 text-gray-400" />
                    <span className="text-gray-600 dark:text-gray-400">Pages :</span>
                    <span className="font-medium text-gray-900 dark:text-white">{book.pages}</span>
                  </div>
                )}
              </div>

              {book.openlibrary_url && (
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <a
                    href={book.openlibrary_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center space-x-2 text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    <GlobeAltIcon className="h-4 w-4" />
                    <span>Voir sur OpenLibrary</span>
                  </a>
                </div>
              )}
            </div>

            {book.description && (
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Résumé</h2>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed">{book.description}</p>
              </div>
            )}

            {book.subjects && book.subjects.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Genres et sujets</h2>
                <div className="flex flex-wrap gap-2">
                  {book.subjects.slice(0, 15).map((subject, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded-full text-sm"
                    >
                      {subject}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default OpenLibraryBookPage;