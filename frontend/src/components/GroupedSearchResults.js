import React, { useState } from 'react';
import { 
  BookOpenIcon, 
  ChevronRightIcon, 
  ChevronDownIcon,
  UserIcon,
  BookmarkIcon,
  PlusIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
import SeriesDetailModal from './SeriesDetailModal';

const GroupedSearchResults = ({ 
  results = [], 
  searchStats = {}, 
  onBookClick, 
  onSagaExpand,
  onAddFromOpenLibrary 
}) => {
  const [expandedSagas, setExpandedSagas] = useState(new Set());

  const toggleSagaExpansion = (sagaName) => {
    const newExpanded = new Set(expandedSagas);
    if (newExpanded.has(sagaName)) {
      newExpanded.delete(sagaName);
    } else {
      newExpanded.add(sagaName);
    }
    setExpandedSagas(newExpanded);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900/20';
      case 'reading':
        return 'text-blue-600 bg-blue-100 dark:text-blue-400 dark:bg-blue-900/20';
      case 'to_read':
        return 'text-yellow-600 bg-yellow-100 dark:text-yellow-400 dark:bg-yellow-900/20';
      default:
        return 'text-gray-600 bg-gray-100 dark:text-gray-400 dark:bg-gray-700';
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'completed':
        return 'Terminé';
      case 'reading':
        return 'En cours';
      case 'to_read':
        return 'À lire';
      default:
        return status;
    }
  };

  const getCategoryEmoji = (category) => {
    switch (category) {
      case 'bd':
        return '🎨';
      case 'manga':
        return '🇯🇵';
      case 'roman':
        return '📚';
      default:
        return '📖';
    }
  };

  if (!results || results.length === 0) {
    return (
      <div className="text-center py-12">
        <BookOpenIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-500 dark:text-gray-400">
          Aucun résultat trouvé pour "{searchStats.search_term}"
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Statistiques de recherche */}
      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
        <h3 className="text-sm font-medium text-blue-900 dark:text-blue-200 mb-2">
          📊 Résultats pour "{searchStats.search_term}"
        </h3>
        <div className="flex flex-wrap gap-4 text-sm text-blue-700 dark:text-blue-300">
          <span>📚 {searchStats.total_books} livre(s)</span>
          {searchStats.total_sagas > 0 && (
            <span>📖 {searchStats.total_sagas} saga(s)</span>
          )}
          <span>📋 {results.length} résultat(s) groupé(s)</span>
        </div>
      </div>

      {/* Résultats */}
      <div className="space-y-3">
        {results.map((result, index) => (
          <div key={index} className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
            {result.type === 'saga' ? (
              // Affichage saga
              <div>
                <div 
                  className="p-4 hover:bg-gray-50 dark:hover:bg-gray-750 cursor-pointer transition-colors"
                  onClick={() => toggleSagaExpansion(result.name)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3 flex-1">
                      <div className="w-12 h-16 bg-gradient-to-br from-purple-500 to-blue-600 rounded flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                        {getCategoryEmoji(result.category)}
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2 mb-1">
                          <BookmarkIcon className="h-4 w-4 text-purple-500" />
                          <h3 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
                            {result.name}
                          </h3>
                        </div>
                        
                        <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400 mb-2">
                          <UserIcon className="h-3 w-3" />
                          <span>{result.author}</span>
                          <span>•</span>
                          <span className="capitalize">{result.category}</span>
                        </div>
                        
                        <div className="flex flex-wrap gap-2">
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-300">
                            📚 {result.total_books} tome(s)
                          </span>
                          
                          {result.completed_books > 0 && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300">
                              ✅ {result.completed_books} terminé(s)
                            </span>
                          )}
                          
                          {result.reading_books > 0 && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300">
                              📖 {result.reading_books} en cours
                            </span>
                          )}
                          
                          {result.to_read_books > 0 && (
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300">
                              📚 {result.to_read_books} à lire
                            </span>
                          )}
                          
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300">
                            🏆 {result.completion_percentage}% complété
                          </span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-500 dark:text-gray-400">
                        {expandedSagas.has(result.name) ? 'Réduire' : 'Voir les livres'}
                      </span>
                      {expandedSagas.has(result.name) ? (
                        <ChevronDownIcon className="h-5 w-5 text-gray-400" />
                      ) : (
                        <ChevronRightIcon className="h-5 w-5 text-gray-400" />
                      )}
                    </div>
                  </div>
                </div>
                
                {/* Livres de la saga (développés) */}
                {expandedSagas.has(result.name) && result.books && (
                  <div className="border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-750">
                    <div className="p-4">
                      <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                        Livres de la saga ({result.books.length})
                      </h4>
                      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                        {result.books
                          .sort((a, b) => (a.volume_number || 0) - (b.volume_number || 0))
                          .map((book, bookIndex) => (
                            <div 
                              key={bookIndex}
                              className="bg-white dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-600 hover:border-purple-300 dark:hover:border-purple-600 cursor-pointer transition-colors"
                              onClick={() => onBookClick && onBookClick(book)}
                            >
                              <div className="flex items-start space-x-3">
                                <div className="w-8 h-10 bg-gray-100 dark:bg-gray-700 rounded flex-shrink-0 overflow-hidden">
                                  {book.cover_url ? (
                                    <img 
                                      src={book.cover_url} 
                                      alt={book.title}
                                      className="w-full h-full object-cover"
                                    />
                                  ) : (
                                    <div className="w-full h-full flex items-center justify-center">
                                      <BookOpenIcon className="h-3 w-3 text-gray-400" />
                                    </div>
                                  )}
                                </div>
                                
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center space-x-2 mb-1">
                                    {book.volume_number && (
                                      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-300">
                                        T.{book.volume_number}
                                      </span>
                                    )}
                                    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${getStatusColor(book.status)}`}>
                                      {getStatusLabel(book.status)}
                                    </span>
                                  </div>
                                  
                                  <h5 className="text-sm font-medium text-gray-900 dark:text-white truncate mb-1">
                                    {book.title}
                                  </h5>
                                  
                                  {book.rating && (
                                    <div className="flex items-center space-x-1">
                                      {[...Array(5)].map((_, i) => (
                                        <span 
                                          key={i} 
                                          className={`text-xs ${i < book.rating ? 'text-yellow-400' : 'text-gray-300 dark:text-gray-600'}`}
                                        >
                                          ⭐
                                        </span>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              // Affichage livre individuel
              <div 
                className="p-4 hover:bg-gray-50 dark:hover:bg-gray-750 cursor-pointer transition-colors"
                onClick={() => onBookClick && onBookClick(result)}
              >
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-16 bg-gray-100 dark:bg-gray-700 rounded flex-shrink-0 overflow-hidden">
                    {result.cover_url ? (
                      <img 
                        src={result.cover_url} 
                        alt={result.title}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <BookOpenIcon className="h-4 w-4 text-gray-400" />
                      </div>
                    )}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-2 mb-1">
                      <BookOpenIcon className="h-4 w-4 text-blue-500" />
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
                        {result.title}
                      </h3>
                    </div>
                    
                    <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400 mb-2">
                      <UserIcon className="h-3 w-3" />
                      <span>{result.author}</span>
                      <span>•</span>
                      <span className="capitalize">{result.category}</span>
                      {result.publication_year && (
                        <>
                          <span>•</span>
                          <span>{result.publication_year}</span>
                        </>
                      )}
                    </div>
                    
                    <div className="flex flex-wrap gap-2">
                      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(result.status)}`}>
                        {getStatusLabel(result.status)}
                      </span>
                      
                      {result.saga && (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-300">
                          📖 {result.saga}
                          {result.volume_number && ` - T.${result.volume_number}`}
                        </span>
                      )}
                      
                      {result.rating && (
                        <div className="flex items-center space-x-1">
                          {[...Array(5)].map((_, i) => (
                            <span 
                              key={i} 
                              className={`text-xs ${i < result.rating ? 'text-yellow-400' : 'text-gray-300 dark:text-gray-600'}`}
                            >
                              ⭐
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default GroupedSearchResults;