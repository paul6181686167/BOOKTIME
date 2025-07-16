import React, { useState, useEffect } from 'react';
import { XMarkIcon, UserIcon, BookOpenIcon, CalendarIcon, CollectionIcon, ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline';

const AuthorModal = ({ author, isOpen, onClose }) => {
  const [authorInfo, setAuthorInfo] = useState(null);
  const [authorBooks, setAuthorBooks] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedSeries, setExpandedSeries] = useState({});

  // Fonction pour charger les informations de l'auteur
  const loadAuthorInfo = async () => {
    if (!author) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      const token = localStorage.getItem('token');
      
      // Charger les informations de l'auteur et ses œuvres en parallèle
      const [authorInfoPromise, authorBooksPromise] = await Promise.all([
        loadAuthorProfile(backendUrl),
        loadAuthorBooks(backendUrl, token)
      ]);
      
    } catch (err) {
      console.error('Erreur lors du chargement des informations de l\'auteur:', err);
      setError("Erreur de connexion");
    } finally {
      setLoading(false);
    }
  };

  // Charger le profil de l'auteur (Wikipedia + OpenLibrary)
  const loadAuthorProfile = async (backendUrl) => {
    // Essayer d'abord l'API Wikipedia (nouvelle source optimale)
    const wikipediaResponse = await fetch(`${backendUrl}/api/wikipedia/author/${encodeURIComponent(author)}`);
    
    if (wikipediaResponse.ok) {
      const wikipediaData = await wikipediaResponse.json();
      if (wikipediaData.found) {
        console.log('✅ Informations auteur récupérées depuis Wikipedia:', wikipediaData.author);
        setAuthorInfo({
          ...wikipediaData.author,
          source: 'wikipedia'
        });
        return;
      }
    }
    
    // Fallback vers OpenLibrary si Wikipedia échoue
    const token = localStorage.getItem('token');
    const openlibResponse = await fetch(`${backendUrl}/api/openlibrary/author/${encodeURIComponent(author)}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (openlibResponse.ok) {
      const openlibData = await openlibResponse.json();
      if (openlibData.found) {
        console.log('✅ Informations auteur récupérées depuis OpenLibrary:', openlibData.author);
        setAuthorInfo({
          ...openlibData.author,
          source: 'openlibrary'
        });
        return;
      }
    }
    
    // Aucune source n'a fonctionné pour le profil
    console.log('⚠️ Aucune information de profil trouvée pour l\'auteur');
  };

  // Charger les œuvres de l'auteur depuis la bibliothèque
  const loadAuthorBooks = async (backendUrl, token) => {
    try {
      const response = await fetch(`${backendUrl}/api/authors/${encodeURIComponent(author)}/books`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const booksData = await response.json();
        console.log('✅ Œuvres de l\'auteur récupérées:', booksData);
        setAuthorBooks(booksData);
      } else {
        console.log('⚠️ Aucune œuvre trouvée dans la bibliothèque pour cet auteur');
      }
    } catch (err) {
      console.error('Erreur lors du chargement des œuvres:', err);
    }
  };

  // Fonction pour basculer l'expansion d'une série
  const toggleSeriesExpansion = (seriesName) => {
    setExpandedSeries(prev => ({
      ...prev,
      [seriesName]: !prev[seriesName]
    }));
  };

  // Fonction pour obtenir la couleur du badge de statut
  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';
      case 'reading': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300';
      case 'to_read': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300';
    }
  };

  // Fonction pour obtenir le texte du statut
  const getStatusText = (status) => {
    switch (status) {
      case 'completed': return 'Terminé';
      case 'reading': return 'En cours';
      case 'to_read': return 'À lire';
      default: return 'Inconnu';
    }
  };

  // Charger les informations quand le modal s'ouvre
  useEffect(() => {
    if (isOpen && author) {
      loadAuthorInfo();
    }
  }, [isOpen, author]);

  // Réinitialiser les données quand le modal se ferme
  useEffect(() => {
    if (!isOpen) {
      setAuthorInfo(null);
      setAuthorBooks(null);
      setError(null);
      setExpandedSeries({});
    }
  }, [isOpen]);

  if (!isOpen || !author) return null;

  return (
    <div className="modal-overlay" onClick={onClose} style={{ zIndex: 1100 }}>
      <div className="modal-content-wide" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between mb-6">
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              {authorInfo?.name || author}
            </h2>
          </div>
          
          <button
            onClick={onClose}
            className="p-2 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500"></div>
            <span className="ml-3 text-gray-600 dark:text-gray-400">Chargement des informations...</span>
          </div>
        )}

        {error && (
          <div className="text-center py-8">
            <div className="text-6xl mb-4">👤</div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              {author}
            </h3>
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              {error}
            </p>
            <button
              onClick={loadAuthorInfo}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
            >
              Réessayer
            </button>
          </div>
        )}

        {!loading && (
          <div className="space-y-6">
            {/* Informations auteur */}
            {authorInfo && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Photo de l'auteur */}
                <div className="md:col-span-1">
                  <div className="aspect-square bg-gray-100 dark:bg-gray-700 rounded-lg overflow-hidden">
                    {authorInfo.photo_url ? (
                      <img 
                        src={authorInfo.photo_url} 
                        alt={authorInfo.name}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.target.style.display = 'none';
                          e.target.nextSibling.style.display = 'flex';
                        }}
                      />
                    ) : null}
                    <div 
                      className={`w-full h-full bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white ${authorInfo.photo_url ? 'hidden' : 'flex'}`}
                    >
                      <UserIcon className="h-20 w-20" />
                    </div>
                  </div>
                </div>

                {/* Informations de l'auteur */}
                <div className="md:col-span-2 space-y-6">
                  {/* Biographie */}
                  {authorInfo.bio && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
                        <BookOpenIcon className="h-5 w-5 mr-2 text-green-600" />
                        Biographie
                      </h3>
                      <div className="prose prose-gray dark:prose-invert max-w-none">
                        <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                          {authorInfo.bio}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Informations supplémentaires */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Dates */}
                    {(authorInfo.birth_date || authorInfo.death_date) && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2 flex items-center">
                          <CalendarIcon className="h-4 w-4 mr-1 text-gray-500" />
                          Dates
                        </h4>
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          {authorInfo.birth_date && (
                            <p>Né(e) : {authorInfo.birth_date}</p>
                          )}
                          {authorInfo.death_date && (
                            <p>Décédé(e) : {authorInfo.death_date}</p>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Statistiques */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2 flex items-center">
                        <BookOpenIcon className="h-4 w-4 mr-1 text-gray-500" />
                        Œuvres
                      </h4>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        {authorInfo.work_summary && (
                          <p>{authorInfo.work_summary}</p>
                        )}
                        {authorInfo.work_count > 0 && (
                          <p>{authorInfo.work_count} œuvre(s) répertoriée(s)</p>
                        )}
                        {authorInfo.top_work && (
                          <p className="mt-1 text-xs">
                            <span className="font-medium">Œuvre principale :</span> {authorInfo.top_work}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Noms alternatifs */}
                  {authorInfo.alternate_names && authorInfo.alternate_names.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                        Autres noms
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {authorInfo.alternate_names.slice(0, 5).map((name, index) => (
                          <span
                            key={index}
                            className="inline-flex items-center px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs rounded"
                          >
                            {name}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Source */}
                  <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Informations fournies par{' '}
                      {authorInfo.source === 'wikipedia' ? (
                        <a 
                          href={authorInfo.wikipedia_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-green-600 hover:text-green-700 underline"
                        >
                          Wikipedia
                        </a>
                      ) : (
                        <a 
                          href={`https://openlibrary.org${authorInfo.ol_key}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-green-600 hover:text-green-700 underline"
                        >
                          Open Library
                        </a>
                      )}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Œuvres de l'auteur depuis sources externes */}
            {authorBooks && authorBooks.total_books > 0 && (
              <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                  <CollectionIcon className="h-5 w-5 mr-2 text-green-600" />
                  {authorBooks.fallback ? "Œuvres dans votre bibliothèque" : "Œuvres de l'auteur"}
                  <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
                    ({authorBooks.total_books} livre{authorBooks.total_books > 1 ? 's' : ''})
                  </span>
                  {authorBooks.sources && (
                    <span className="ml-2 text-xs text-gray-400 dark:text-gray-500">
                      {authorBooks.sources.wikipedia ? `Wikipedia: ${authorBooks.sources.wikipedia}` : ''}
                      {authorBooks.sources.openlibrary ? ` OpenLibrary: ${authorBooks.sources.openlibrary}` : ''}
                      {authorBooks.sources.library ? `Bibliothèque: ${authorBooks.sources.library}` : ''}
                    </span>
                  )}
                </h3>

                <div className="space-y-4">
                  {/* Séries */}
                  {authorBooks.series.map((series, index) => (
                    <div key={index} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                      <div 
                        className="flex items-center justify-between cursor-pointer"
                        onClick={() => toggleSeriesExpansion(series.name)}
                      >
                        <div className="flex items-center space-x-3">
                          <div className="flex-shrink-0">
                            <CollectionIcon className="h-5 w-5 text-purple-600" />
                          </div>
                          <div>
                            <h4 className="font-medium text-gray-900 dark:text-white">
                              {series.name}
                            </h4>
                            <p className="text-sm text-gray-500 dark:text-gray-400">
                              {series.description || "Série"}
                              {series.source && (
                                <span className="ml-2 text-xs">
                                  • {series.source === 'wikipedia' ? 'Wikipedia' : 'OpenLibrary'}
                                </span>
                              )}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          {expandedSeries[series.name] ? (
                            <ChevronUpIcon className="h-4 w-4 text-gray-400" />
                          ) : (
                            <ChevronDownIcon className="h-4 w-4 text-gray-400" />
                          )}
                        </div>
                      </div>

                      {expandedSeries[series.name] && (
                        <div className="mt-3 space-y-2">
                          {series.books && series.books.length > 0 ? (
                            series.books.map((book, bookIndex) => (
                              <div key={bookIndex} className="flex items-center justify-between py-2 px-3 bg-white dark:bg-gray-700 rounded">
                                <div className="flex items-center space-x-3">
                                  <span className="text-sm text-gray-500 dark:text-gray-400 min-w-[2rem]">
                                    {book.volume_number || bookIndex + 1}
                                  </span>
                                  <div>
                                    <p className="font-medium text-gray-900 dark:text-white text-sm">
                                      {book.title}
                                    </p>
                                    {book.publication_year && (
                                      <p className="text-xs text-gray-500 dark:text-gray-400">
                                        {book.publication_year}
                                      </p>
                                    )}
                                  </div>
                                </div>
                                {book.status && (
                                  <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getStatusColor(book.status)}`}>
                                    {getStatusText(book.status)}
                                  </span>
                                )}
                              </div>
                            ))
                          ) : (
                            <div className="py-2 px-3 bg-white dark:bg-gray-700 rounded">
                              <p className="text-sm text-gray-500 dark:text-gray-400 italic">
                                Série identifiée - livres détaillés disponibles sur {series.source === 'wikipedia' ? 'Wikipedia' : 'OpenLibrary'}
                              </p>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  ))}

                  {/* Livres individuels */}
                  {authorBooks.individual_books.length > 0 && (
                    <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                      <h4 className="font-medium text-gray-900 dark:text-white mb-3 flex items-center">
                        <BookOpenIcon className="h-5 w-5 mr-2 text-blue-600" />
                        Livres individuels
                      </h4>
                      <div className="space-y-2">
                        {authorBooks.individual_books.map((item, index) => (
                          <div key={index} className="flex items-center justify-between py-2 px-3 bg-white dark:bg-gray-700 rounded">
                            <div>
                              <p className="font-medium text-gray-900 dark:text-white text-sm">
                                {item.book ? item.book.title : item.title}
                              </p>
                              <div className="flex items-center space-x-2 text-xs text-gray-500 dark:text-gray-400">
                                {(item.book ? item.book.publication_year : item.year) && (
                                  <span>{item.book ? item.book.publication_year : item.year}</span>
                                )}
                                {item.source && (
                                  <span>
                                    • {item.source === 'wikipedia' ? 'Wikipedia' : 'OpenLibrary'}
                                  </span>
                                )}
                              </div>
                            </div>
                            {item.book && item.book.status && (
                              <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getStatusColor(item.book.status)}`}>
                                {getStatusText(item.book.status)}
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Message si aucune œuvre trouvée */}
            {authorBooks && authorBooks.total_books === 0 && (
              <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
                <div className="text-center py-8">
                  <BookOpenIcon className="h-12 w-12 mx-auto text-gray-400 dark:text-gray-600 mb-4" />
                  <p className="text-gray-500 dark:text-gray-400">
                    Aucune œuvre trouvée pour cet auteur
                  </p>
                  <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
                    Nous cherchons dans Wikipedia et OpenLibrary
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {!authorInfo && !authorBooks && !loading && !error && (
          <div className="text-center py-8">
            <div className="text-6xl mb-4">👤</div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              {author}
            </h3>
            <p className="text-gray-500 dark:text-gray-400">
              Chargement des informations...
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AuthorModal;