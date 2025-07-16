import React, { useState, useEffect } from 'react';
import { XMarkIcon, UserIcon, BookOpenIcon, CalendarIcon } from '@heroicons/react/24/outline';

const AuthorModal = ({ author, isOpen, onClose }) => {
  const [authorInfo, setAuthorInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fonction pour charger les informations de l'auteur
  const loadAuthorInfo = async () => {
    if (!author) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
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
      
      // Aucune source n'a fonctionné
      setError("Informations de l'auteur non disponibles");
      
    } catch (err) {
      console.error('Erreur lors du chargement des informations de l\'auteur:', err);
      setError("Erreur de connexion");
    } finally {
      setLoading(false);
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
      setError(null);
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

        {authorInfo && !loading && (
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
                      // Fallback vers icône si l'image ne charge pas
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
                    <p>{authorInfo.work_count || 0} œuvre(s) répertoriée(s)</p>
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
                  <a 
                    href={`https://openlibrary.org${authorInfo.ol_key}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-green-600 hover:text-green-700 underline"
                  >
                    Open Library
                  </a>
                </p>
              </div>
            </div>
          </div>
        )}

        {!authorInfo && !loading && !error && (
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