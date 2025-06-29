import React, { useState } from 'react';
import { MagnifyingGlassIcon, BookOpenIcon, StarIcon, CheckIcon, PlusIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

const SeriesDiscovery = ({ isOpen, onClose, initialSeries = '', initialAuthor = '' }) => {
  const [seriesName, setSeriesName] = useState(initialSeries);
  const [author, setAuthor] = useState(initialAuthor);
  const [loading, setLoading] = useState(false);
  const [discoveryResult, setDiscoveryResult] = useState(null);
  const [importingBooks, setImportingBooks] = useState(new Set());

  const handleDiscover = async () => {
    if (!seriesName.trim()) {
      toast.error('Veuillez entrer le nom d\'une série');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const params = new URLSearchParams({
        series_name: seriesName,
        ...(author && { author })
      });

      const response = await fetch(`${backendUrl}/api/series/discover?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setDiscoveryResult(data);
        toast.success(`${data.statistics.total_discovered} livres découverts pour "${seriesName}"`);
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Erreur lors de la découverte');
      }
    } catch (error) {
      console.error('Erreur découverte:', error);
      toast.error('Erreur lors de la découverte de série');
    } finally {
      setLoading(false);
    }
  };

  const handleImportBook = async (book) => {
    if (importingBooks.has(book.ol_key)) return;

    try {
      setImportingBooks(prev => new Set([...prev, book.ol_key]));
      
      const token = localStorage.getItem('token');
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const response = await fetch(`${backendUrl}/api/openlibrary/import`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ol_key: book.ol_key,
          category: book.category || 'roman'
        })
      });

      if (response.ok) {
        toast.success(`"${book.title}" ajouté à votre collection !`);
        
        // Mettre à jour le statut de possession dans les résultats
        setDiscoveryResult(prev => {
          const updated = { ...prev };
          Object.keys(updated.books).forEach(category => {
            updated.books[category] = updated.books[category].map(b => 
              b.ol_key === book.ol_key ? { ...b, is_owned: true } : b
            );
          });
          return updated;
        });
      } else {
        const error = await response.json();
        if (response.status === 409) {
          toast.error('Ce livre est déjà dans votre collection');
        } else {
          toast.error(error.detail || 'Erreur lors de l\'ajout du livre');
        }
      }
    } catch (error) {
      console.error('Erreur import livre:', error);
      toast.error('Erreur lors de l\'ajout du livre');
    } finally {
      setImportingBooks(prev => {
        const newSet = new Set(prev);
        newSet.delete(book.ol_key);
        return newSet;
      });
    }
  };

  const handleImportMissingBooks = async () => {
    if (!discoveryResult?.recommendations?.next_to_buy?.length) {
      toast.error('Aucun livre à importer');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const ol_keys = discoveryResult.recommendations.next_to_buy
        .filter(book => !book.is_owned)
        .slice(0, 5) // Limiter à 5 livres
        .map(book => book.ol_key);

      const response = await fetch(`${backendUrl}/api/series/import-missing`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ol_keys,
          series_name: seriesName
        })
      });

      if (response.ok) {
        const data = await response.json();
        toast.success(data.message);
        // Recharger la découverte pour voir les changements
        await handleDiscover();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Erreur lors de l\'import en lot');
      }
    } catch (error) {
      console.error('Erreur import en lot:', error);
      toast.error('Erreur lors de l\'import en lot');
    }
  };

  const BookCard = ({ book, compact = false }) => (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-md p-3 ${compact ? 'text-sm' : ''}`}>
      <div className="flex items-start space-x-3">
        {book.cover_url ? (
          <img
            src={book.cover_url}
            alt={book.title}
            className={`${compact ? 'w-12 h-16' : 'w-16 h-20'} object-cover rounded flex-shrink-0`}
          />
        ) : (
          <div className={`${compact ? 'w-12 h-16' : 'w-16 h-20'} bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center flex-shrink-0`}>
            <BookOpenIcon className="w-6 h-6 text-gray-400" />
          </div>
        )}
        
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-gray-900 dark:text-white truncate" title={book.title}>
            {book.title}
          </h4>
          <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
            {book.author}
          </p>
          {book.volume_number && (
            <p className="text-xs text-blue-600 dark:text-blue-400">
              Tome {book.volume_number}
            </p>
          )}
          {book.first_publish_year && (
            <p className="text-xs text-gray-500">
              {book.first_publish_year}
            </p>
          )}
          
          <div className="flex items-center justify-between mt-2">
            <div className="flex items-center space-x-2">
              {book.is_owned ? (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                  <CheckIcon className="w-3 h-3 mr-1" />
                  Possédé
                </span>
              ) : (
                <button
                  onClick={() => handleImportBook(book)}
                  disabled={importingBooks.has(book.ol_key)}
                  className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-blue-100 hover:bg-blue-200 text-blue-800 dark:bg-blue-900 dark:text-blue-200 disabled:opacity-50"
                >
                  {importingBooks.has(book.ol_key) ? (
                    '⏳'
                  ) : (
                    <>
                      <PlusIcon className="w-3 h-3 mr-1" />
                      Ajouter
                    </>
                  )}
                </button>
              )}
              
              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs ${
                book.book_type === 'main_series' ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200' :
                book.book_type === 'spin_off' ? 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200' :
                book.book_type === 'companion' ? 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200' :
                'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
              }`}>
                {book.book_type === 'main_series' ? 'Série principale' :
                 book.book_type === 'spin_off' ? 'Spin-off' :
                 book.book_type === 'companion' ? 'Guide' : 'Connexe'}
              </span>
            </div>
            
            {book.relevance_score > 0 && (
              <div className="flex items-center text-xs text-yellow-600 dark:text-yellow-400">
                <StarIcon className="w-3 h-3 mr-1" />
                {book.relevance_score}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg max-w-6xl w-full mx-4 max-h-[90vh] overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            🔍 Découverte Complète de Série
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {/* Formulaire de recherche */}
          <div className="mb-6 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Nom de la série *
                </label>
                <input
                  type="text"
                  value={seriesName}
                  onChange={(e) => setSeriesName(e.target.value)}
                  placeholder="Ex: Harry Potter, One Piece, Astérix..."
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Auteur (optionnel)
                </label>
                <input
                  type="text"
                  value={author}
                  onChange={(e) => setAuthor(e.target.value)}
                  placeholder="Ex: J.K. Rowling, Eiichiro Oda..."
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
              </div>
            </div>
            
            <button
              onClick={handleDiscover}
              disabled={loading || !seriesName.trim()}
              className="w-full md:w-auto px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Découverte en cours...
                </>
              ) : (
                <>
                  <MagnifyingGlassIcon className="w-4 h-4 mr-2" />
                  Découvrir la série complète
                </>
              )}
            </button>
          </div>

          {/* Résultats de découverte */}
          {discoveryResult && (
            <div className="space-y-6">
              {/* Statistiques */}
              <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-3">
                  📊 Statistiques de "{discoveryResult.series_name}"
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                      {discoveryResult.statistics.total_discovered}
                    </div>
                    <div className="text-gray-600 dark:text-gray-400">Livres découverts</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                      {discoveryResult.statistics.owned_count}
                    </div>
                    <div className="text-gray-600 dark:text-gray-400">Possédés</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                      {discoveryResult.statistics.completion_percentage}%
                    </div>
                    <div className="text-gray-600 dark:text-gray-400">Complétion</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                      {discoveryResult.statistics.missing_volumes.length}
                    </div>
                    <div className="text-gray-600 dark:text-gray-400">Tomes manquants</div>
                  </div>
                </div>
                
                {discoveryResult.recommendations.next_to_buy.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-blue-200 dark:border-blue-800">
                    <button
                      onClick={handleImportMissingBooks}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
                    >
                      📥 Importer les 5 prochains livres recommandés
                    </button>
                  </div>
                )}
              </div>

              {/* Série principale */}
              {discoveryResult.books.main_series.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                    📚 Série Principale ({discoveryResult.books.main_series.length} livres)
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {discoveryResult.books.main_series.map((book, index) => (
                      <BookCard key={index} book={book} />
                    ))}
                  </div>
                </div>
              )}

              {/* Spin-offs */}
              {discoveryResult.books.spin_offs.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                    🌟 Spin-offs ({discoveryResult.books.spin_offs.length} livres)
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {discoveryResult.books.spin_offs.map((book, index) => (
                      <BookCard key={index} book={book} compact />
                    ))}
                  </div>
                </div>
              )}

              {/* Guides et compagnons */}
              {discoveryResult.books.companions.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                    📖 Guides & Compagnons ({discoveryResult.books.companions.length} livres)
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {discoveryResult.books.companions.map((book, index) => (
                      <BookCard key={index} book={book} compact />
                    ))}
                  </div>
                </div>
              )}

              {/* Œuvres connexes */}
              {discoveryResult.books.related.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                    🔗 Œuvres Connexes ({discoveryResult.books.related.length} livres)
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {discoveryResult.books.related.map((book, index) => (
                      <BookCard key={index} book={book} compact />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SeriesDiscovery;