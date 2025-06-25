import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { 
  ArrowLeftIcon, 
  UserIcon,
  BookOpenIcon,
  CalendarIcon,
  PhotoIcon,
  GlobeAltIcon,
  ChartBarIcon,
  CheckCircleIcon,
  ClockIcon,
  BookmarkIcon,
  PlusIcon
} from '@heroicons/react/24/outline';

const OpenLibraryAuthorPage = () => {
  const { authorName } = useParams();
  const navigate = useNavigate();
  const [author, setAuthor] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('biography');

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    loadAuthorData();
  }, [authorName]);

  const loadAuthorData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`${backendUrl}/api/openlibrary/author/${encodeURIComponent(authorName)}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Auteur non trouvé');
      }

      const authorData = await response.json();
      setAuthor(authorData);
    } catch (error) {
      console.error('Erreur lors du chargement de l\'auteur:', error);
      toast.error('Erreur lors du chargement de l\'auteur');
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  const handleBookClick = (book) => {
    if (book.user_book_id) {
      navigate(`/livre/${book.user_book_id}`);
    } else if (book.openlibrary_key) {
      const workKey = book.openlibrary_key.replace('/works/', '');
      navigate(`/livre/ol/${workKey}`);
    } else {
      toast.info('Détails du livre non disponibles');
    }
  };

  const addBookToLibrary = async (book) => {
    try {
      const token = localStorage.getItem('token');
      const bookData = {
        title: book.title,
        author: authorName,
        isbn: book.isbn || '',
        publication_year: book.first_publish_year,
        cover_url: book.cover_url || '',
        publisher: book.publisher || '',
        genre: book.subjects || [],
        category: book.category || 'roman'
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
      
      loadAuthorData();
      navigate(`/livre/${newBook.id}`);
    } catch (error) {
      console.error('Erreur lors de l\'ajout du livre:', error);
      toast.error('Erreur lors de l\'ajout du livre');
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-4 w-4 text-green-500" />;
      case 'reading':
        return <ClockIcon className="h-4 w-4 text-blue-500" />;
      case 'to_read':
        return <BookmarkIcon className="h-4 w-4 text-gray-500" />;
      default:
        return null;
    }
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'bd': return '🎨';
      case 'manga': return '🇯🇵';
      default: return '📚';
    }
  };

  const groupBooksByDecade = (books) => {
    const grouped = {};
    books.forEach(book => {
      const year = book.first_publish_year;
      if (year) {
        const decade = Math.floor(year / 10) * 10;
        const key = `${decade}s`;
        if (!grouped[key]) {
          grouped[key] = [];
        }
        grouped[key].push(book);
      } else {
        if (!grouped['Année inconnue']) {
          grouped['Année inconnue'] = [];
        }
        grouped['Année inconnue'].push(book);
      }
    });
    return grouped;
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

  if (!author) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <span className="text-6xl mb-4 block">👤</span>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Auteur non trouvé</h1>
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

  const groupedBooks = groupBooksByDecade(author.bibliography || []);
  const userStats = author.user_stats || {};

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

              <div className="aspect-square bg-gray-100 dark:bg-gray-700 rounded-xl overflow-hidden mb-6 shadow-inner">
                {author.photo_url ? (
                  <img
                    src={author.photo_url}
                    alt={author.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <UserIcon className="h-16 w-16 text-gray-400 dark:text-gray-500" />
                  </div>
                )}
              </div>

              <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4 text-center">{author.name}</h1>

              {(author.birth_date || author.death_date) && (
                <div className="text-center mb-4 text-sm text-gray-600 dark:text-gray-400">
                  {author.birth_date && `Né(e) en ${author.birth_date}`}
                  {author.birth_date && author.death_date && ' - '}
                  {author.death_date && `Décédé(e) en ${author.death_date}`}
                </div>
              )}

              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
                  <ChartBarIcon className="h-5 w-5 mr-2" />
                  Mes statistiques
                </h3>
                
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                      {userStats.books_read || 0}
                    </div>
                    <div className="text-xs text-blue-600 dark:text-blue-400">Lus</div>
                  </div>
                  <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                      {userStats.books_reading || 0}
                    </div>
                    <div className="text-xs text-green-600 dark:text-green-400">En cours</div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-gray-600 dark:text-gray-400">
                      {userStats.books_to_read || 0}
                    </div>
                    <div className="text-xs text-gray-600 dark:text-gray-400">À lire</div>
                  </div>
                  <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-3 text-center">
                    <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                      {userStats.total_bibliography || 0}
                    </div>
                    <div className="text-xs text-purple-600 dark:text-purple-400">Total</div>
                  </div>
                </div>

                {userStats.total_bibliography > 0 && (
                  <div className="mt-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Progression :</span>
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {userStats.completion_percentage || 0}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${userStats.completion_percentage || 0}%` }}
                      ></div>
                    </div>
                  </div>
                )}

                {author.wikipedia_url && (
                  <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                    <a
                      href={author.wikipedia_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center space-x-2 text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      <GlobeAltIcon className="h-4 w-4" />
                      <span>Page Wikipedia</span>
                    </a>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg">
              <div className="border-b border-gray-200 dark:border-gray-700">
                <nav className="-mb-px flex">
                  <button
                    onClick={() => setActiveTab('biography')}
                    className={`py-4 px-6 border-b-2 font-medium text-sm ${
                      activeTab === 'biography'
                        ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                        : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                    }`}
                  >
                    📖 Biographie
                  </button>
                  <button
                    onClick={() => setActiveTab('bibliography')}
                    className={`py-4 px-6 border-b-2 font-medium text-sm ${
                      activeTab === 'bibliography'
                        ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                        : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                    }`}
                  >
                    📚 Bibliographie ({author.bibliography?.length || 0})
                  </button>
                  <button
                    onClick={() => setActiveTab('timeline')}
                    className={`py-4 px-6 border-b-2 font-medium text-sm ${
                      activeTab === 'timeline'
                        ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                        : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                    }`}
                  >
                    ⏰ Chronologie
                  </button>
                </nav>
              </div>

              <div className="p-6">
                {activeTab === 'biography' && (
                  <div className="space-y-4">
                    {author.biography ? (
                      <div className="text-gray-700 dark:text-gray-300 leading-relaxed">
                        <p>{author.biography}</p>
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <span className="text-4xl mb-4 block">📝</span>
                        <p className="text-gray-500 dark:text-gray-400">
                          Aucune biographie disponible pour cet auteur.
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'bibliography' && (
                  <div className="space-y-6">
                    {author.bibliography && author.bibliography.length > 0 ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {author.bibliography.map((book, index) => (
                          <div
                            key={index}
                            className={`p-4 rounded-lg border-2 transition-all cursor-pointer ${
                              book.in_user_library
                                ? 'border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-900/20'
                                : 'border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-600'
                            }`}
                            onClick={() => handleBookClick(book)}
                          >
                            <div className="flex space-x-3">
                              <div className="w-12 h-16 bg-gray-100 dark:bg-gray-700 rounded flex-shrink-0 overflow-hidden">
                                {book.cover_url ? (
                                  <img
                                    src={book.cover_url}
                                    alt={book.title}
                                    className="w-full h-full object-cover"
                                  />
                                ) : (
                                  <div className="w-full h-full flex items-center justify-center">
                                    <BookOpenIcon className="h-4 w-4 text-gray-400" />
                                  </div>
                                )}
                              </div>
                              
                              <div className="flex-1 min-w-0">
                                <h3 className="font-medium text-gray-900 dark:text-white truncate">
                                  {book.title}
                                </h3>
                                <div className="flex items-center space-x-2 mt-1">
                                  {book.first_publish_year && (
                                    <span className="text-sm text-gray-600 dark:text-gray-400">
                                      {book.first_publish_year}
                                    </span>
                                  )}
                                  {book.category && (
                                    <span className="text-xs">
                                      {getCategoryIcon(book.category)}
                                    </span>
                                  )}
                                  {book.in_user_library && getStatusIcon(book.user_status)}
                                </div>
                                
                                {book.subjects && book.subjects.length > 0 && (
                                  <div className="mt-2">
                                    <span className="inline-block px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded">
                                      {book.subjects[0]}
                                    </span>
                                  </div>
                                )}
                              </div>

                              <div className="flex items-center">
                                {book.in_user_library ? (
                                  <div className="text-blue-600 dark:text-blue-400">
                                    <CheckCircleIcon className="h-5 w-5" />
                                  </div>
                                ) : (
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      addBookToLibrary(book);
                                    }}
                                    className="flex items-center space-x-1 px-3 py-1 text-xs bg-blue-100 hover:bg-blue-200 dark:bg-blue-900/30 dark:hover:bg-blue-900/50 text-blue-700 dark:text-blue-300 rounded transition-colors"
                                  >
                                    <PlusIcon className="h-3 w-3" />
                                    <span>Ajouter</span>
                                  </button>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <span className="text-4xl mb-4 block">📚</span>
                        <p className="text-gray-500 dark:text-gray-400">
                          Aucun livre trouvé pour cet auteur.
                        </p>
                      </div>
                    )}
                  </div>
                )}

                {activeTab === 'timeline' && (
                  <div className="space-y-6">
                    {Object.keys(groupedBooks).length > 0 ? (
                      Object.entries(groupedBooks)
                        .sort(([a], [b]) => {
                          if (a === 'Année inconnue') return 1;
                          if (b === 'Année inconnue') return -1;
                          return b.localeCompare(a);
                        })
                        .map(([decade, books]) => (
                          <div key={decade} className="border-l-4 border-blue-200 dark:border-blue-800 pl-4">
                            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
                              <CalendarIcon className="h-5 w-5 mr-2" />
                              {decade}
                            </h3>
                            <div className="space-y-2">
                              {books
                                .sort((a, b) => (a.first_publish_year || 0) - (b.first_publish_year || 0))
                                .map((book, index) => (
                                  <div
                                    key={index}
                                    className={`p-3 rounded-lg cursor-pointer transition-all ${
                                      book.in_user_library
                                        ? 'bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800'
                                        : 'bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700'
                                    }`}
                                    onClick={() => handleBookClick(book)}
                                  >
                                    <div className="flex items-center justify-between">
                                      <div className="flex items-center space-x-3">
                                        {book.in_user_library && getStatusIcon(book.user_status)}
                                        <span className="font-medium text-gray-900 dark:text-white">
                                          {book.title}
                                        </span>
                                        {book.category && (
                                          <span className="text-sm">
                                            {getCategoryIcon(book.category)}
                                          </span>
                                        )}
                                      </div>
                                      <div className="flex items-center space-x-2">
                                        {book.first_publish_year && (
                                          <span className="text-sm text-gray-600 dark:text-gray-400">
                                            {book.first_publish_year}
                                          </span>
                                        )}
                                        {!book.in_user_library && (
                                          <button
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              addBookToLibrary(book);
                                            }}
                                            className="px-2 py-1 text-xs bg-blue-100 hover:bg-blue-200 dark:bg-blue-900/30 dark:hover:bg-blue-900/50 text-blue-700 dark:text-blue-300 rounded transition-colors"
                                          >
                                            +
                                          </button>
                                        )}
                                      </div>
                                    </div>
                                  </div>
                                ))}
                            </div>
                          </div>
                        ))
                    ) : (
                      <div className="text-center py-8">
                        <span className="text-4xl mb-4 block">⏰</span>
                        <p className="text-gray-500 dark:text-gray-400">
                          Aucune chronologie disponible.
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default OpenLibraryAuthorPage;