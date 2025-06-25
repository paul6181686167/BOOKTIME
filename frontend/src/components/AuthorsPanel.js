import React, { useState, useEffect } from 'react';
import { UserIcon, BookOpenIcon, RectangleStackIcon } from '@heroicons/react/24/outline';
import { bookService } from '../services/bookService';

const AuthorsPanel = ({ onAuthorSelect }) => {
  const [authors, setAuthors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAuthor, setSelectedAuthor] = useState(null);

  useEffect(() => {
    loadAuthors();
  }, []);

  const loadAuthors = async () => {
    try {
      setLoading(true);
      const data = await bookService.getAuthors();
      setAuthors(data);
    } catch (error) {
      console.error('Erreur lors du chargement des auteurs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAuthorClick = async (author) => {
    setSelectedAuthor(author);
    if (onAuthorSelect) {
      try {
        const books = await bookService.getBooksByAuthor(author.name);
        onAuthorSelect(books, author);
      } catch (error) {
        console.error('Erreur lors du chargement des livres de l\'auteur:', error);
      }
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Auteurs</h3>
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, index) => (
            <div key={index} className="h-16 bg-gray-200 rounded loading-skeleton"></div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Auteurs</h3>
        <span className="text-sm text-gray-500">{authors.length} auteurs</span>
      </div>

      <div className="space-y-2 max-h-96 overflow-y-auto">
        {authors.map((author) => (
          <div
            key={author.name}
            onClick={() => handleAuthorClick(author)}
            className={`p-3 rounded-lg border cursor-pointer transition-all hover:shadow-md ${
              selectedAuthor?.name === author.name
                ? 'border-booktime-500 bg-booktime-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-1">
                  <UserIcon className="h-4 w-4 text-gray-500" />
                  <h4 className="font-medium text-gray-900 text-sm">{author.name}</h4>
                </div>
                
                <div className="flex items-center space-x-4 text-xs text-gray-600">
                  <div className="flex items-center space-x-1">
                    <BookOpenIcon className="h-3 w-3" />
                    <span>{author.books_count} livre{author.books_count > 1 ? 's' : ''}</span>
                  </div>
                  
                  {author.sagas.length > 0 && (
                    <div className="flex items-center space-x-1">
                      <RectangleStackIcon className="h-3 w-3" />
                      <span>{author.sagas.length} saga{author.sagas.length > 1 ? 's' : ''}</span>
                    </div>
                  )}
                </div>
                
                {/* Catégories */}
                <div className="flex flex-wrap gap-1 mt-2">
                  {author.categories.map((category) => (
                    <span 
                      key={category}
                      className={`px-2 py-0.5 rounded text-xs font-medium ${
                        category === 'roman' ? 'bg-blue-100 text-blue-600' :
                        category === 'bd' ? 'bg-green-100 text-green-600' :
                        'bg-yellow-100 text-yellow-600'
                      }`}
                    >
                      {category === 'roman' && '📚'} 
                      {category === 'bd' && '🎨'} 
                      {category === 'manga' && '🇯🇵'} 
                      {category === 'bd' ? 'bande dessinée' : category}
                    </span>
                  ))}
                </div>

                {/* Sagas */}
                {author.sagas.length > 0 && (
                  <div className="mt-2">
                    <div className="text-xs text-gray-500 mb-1">Sagas :</div>
                    <div className="flex flex-wrap gap-1">
                      {author.sagas.slice(0, 3).map((saga) => (
                        <span 
                          key={saga}
                          className="px-2 py-0.5 bg-purple-100 text-purple-600 rounded text-xs"
                        >
                          {saga}
                        </span>
                      ))}
                      {author.sagas.length > 3 && (
                        <span className="text-xs text-gray-400">
                          +{author.sagas.length - 3}
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default AuthorsPanel;