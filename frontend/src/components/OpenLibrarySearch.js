import React, { useState } from 'react';
import { MagnifyingGlassIcon, BookOpenIcon, PhotoIcon } from '@heroicons/react/24/outline';
import { bookService } from '../services/bookService';
import toast from 'react-hot-toast';

const OpenLibrarySearch = ({ onImport, onClose, defaultCategory = 'roman' }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [importing, setImporting] = useState({});

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      toast.error('Veuillez saisir un terme de recherche');
      return;
    }

    setSearching(true);
    try {
      const data = await bookService.searchOpenLibrary(searchQuery, 15);
      setResults(data.books || []);
      
      if (!data.books || data.books.length === 0) {
        toast.error('Aucun livre trouvé pour cette recherche');
      } else {
        toast.success(`${data.books.length} livre${data.books.length > 1 ? 's' : ''} trouvé${data.books.length > 1 ? 's' : ''}`);
      }
    } catch (error) {
      console.error('Erreur de recherche:', error);
      toast.error('Erreur lors de la recherche sur Open Library');
    } finally {
      setSearching(false);
    }
  };

  const handleImport = async (book, category) => {
    setImporting(prev => ({ ...prev, [book.ol_key]: true }));
    try {
      const importedBook = await bookService.importFromOpenLibrary(book.ol_key, category);
      toast.success(`"${book.title}" importé avec succès !`);
      onImport(importedBook);
    } catch (error) {
      console.error('Erreur d\'import:', error);
      toast.error(error.message || 'Erreur lors de l\'import du livre');
    } finally {
      setImporting(prev => ({ ...prev, [book.ol_key]: false }));
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const getCategoryBadgeClass = (category) => {
    const baseClass = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium";
    switch (category) {
      case 'roman':
        return `${baseClass} bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300`;
      case 'bd':
        return `${baseClass} bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300`;
      case 'manga':
        return `${baseClass} bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300`;
      default:
        return `${baseClass} bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300`;
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-3">
            <BookOpenIcon className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Rechercher sur Open Library
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Search Bar */}
        <div className="p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex space-x-4">
            <div className="flex-1">
              <div className="relative">
                <MagnifyingGlassIcon className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Recherchez un livre, un auteur..."
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                />
              </div>
            </div>
            <button
              onClick={handleSearch}
              disabled={searching}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium rounded-lg transition-colors disabled:cursor-not-allowed"
            >
              {searching ? (
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Recherche...</span>
                </div>
              ) : (
                'Rechercher'
              )}
            </button>
          </div>
        </div>

        {/* Results */}
        <div className="flex-1 overflow-y-auto p-6 max-h-[60vh]">
          {results.length === 0 && !searching && (
            <div className="text-center py-12">
              <BookOpenIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">
                Aucune recherche effectuée
              </h3>
              <p className="mt-2 text-gray-600 dark:text-gray-400">
                Utilisez la barre de recherche pour trouver des livres sur Open Library
              </p>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {results.map((book) => (
              <div
                key={book.ol_key}
                className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 border border-gray-200 dark:border-gray-600"
              >
                <div className="flex space-x-4">
                  {/* Cover Image */}
                  <div className="flex-shrink-0">
                    {book.cover_url ? (
                      <img
                        src={book.cover_url}
                        alt={book.title}
                        className="w-16 h-20 object-cover rounded"
                        onError={(e) => {
                          e.target.style.display = 'none';
                          e.target.nextSibling.style.display = 'flex';
                        }}
                      />
                    ) : null}
                    <div 
                      className={`w-16 h-20 bg-gray-200 dark:bg-gray-600 rounded flex items-center justify-center ${book.cover_url ? 'hidden' : 'flex'}`}
                    >
                      <PhotoIcon className="w-6 h-6 text-gray-400" />
                    </div>
                  </div>

                  {/* Book Info */}
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate" title={book.title}>
                      {book.title}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 truncate" title={book.author}>
                      {book.author}
                    </p>
                    
                    <div className="mt-2 flex items-center space-x-2">
                      <span className={getCategoryBadgeClass(book.category)}>
                        {book.category}
                      </span>
                      {book.publication_year && (
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {book.publication_year}
                        </span>
                      )}
                    </div>

                    {book.description && (
                      <p className="mt-2 text-xs text-gray-600 dark:text-gray-400 line-clamp-2">
                        {book.description}
                      </p>
                    )}

                    {/* Import Buttons */}
                    <div className="mt-3 flex flex-wrap gap-2">
                      {[{value: 'roman', label: 'Roman'}, {value: 'bd', label: 'Bande dessinée'}, {value: 'manga', label: 'Manga'}].map((categoryOption) => (
                        <button
                          key={categoryOption.value}
                          onClick={() => handleImport(book, categoryOption.value)}
                          disabled={importing[book.ol_key]}
                          className={`px-3 py-1 text-xs font-medium rounded transition-colors disabled:cursor-not-allowed ${
                            categoryOption.value === defaultCategory
                              ? 'bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white'
                              : 'bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100 text-gray-700 dark:bg-gray-600 dark:hover:bg-gray-500 dark:disabled:bg-gray-700 dark:text-gray-300'
                          }`}
                        >
                          {importing[book.ol_key] ? (
                            <div className="flex items-center space-x-1">
                              <div className="w-3 h-3 border border-current border-t-transparent rounded-full animate-spin"></div>
                              <span>Import...</span>
                            </div>
                          ) : (
                            `Import ${categoryOption.label}`
                          )}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default OpenLibrarySearch;