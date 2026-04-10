import React, { useState, useEffect } from 'react';
import { StarIcon, PlusIcon, XMarkIcon } from '@heroicons/react/24/solid';
import { toast } from 'react-hot-toast';
import { API_BASE_URL } from '../../config/environment';

/**
 * Panel de recommandations IA BOOKTIME
 * Système intelligent de suggestions basé sur l'historique de lecture
 * Sessions 86.1-86.7 : Architecture modulaire + IA recommendations
 */

const RecommendationsPanel = ({ 
  onClose, 
  onAddBook,
  userBooks = [],
  className = ""
}) => {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [addingBooks, setAddingBooks] = useState(new Set());
  
  const backendUrl = API_BASE_URL;

  useEffect(() => {
    fetchRecommendations();
  }, []);

  const fetchRecommendations = async () => {
    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('token');
      if (!token) {
        setError('Authentification requise');
        return;
      }

      const response = await fetch(`${backendUrl}/api/recommendations/user`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      
      if (data.success && data.recommendations) {
        setRecommendations(data.recommendations);
      } else {
        setError(data.message || 'Aucune recommandation disponible');
      }

    } catch (error) {
      console.error('Erreur recommandations:', error);
      setError('Erreur lors du chargement des recommandations');
    } finally {
      setLoading(false);
    }
  };

  const handleAddRecommendation = async (recommendation) => {
    if (addingBooks.has(recommendation.ol_key)) return;

    try {
      setAddingBooks(prev => new Set([...prev, recommendation.ol_key]));

      const token = localStorage.getItem('token');
      const response = await fetch(`${backendUrl}/api/openlibrary/import`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ol_key: recommendation.ol_key,
          category: recommendation.category || 'roman'
        })
      });

      const result = await response.json();
      
      if (response.ok) {
        toast.success(`"${recommendation.title}" ajouté à votre bibliothèque !`);
        if (onAddBook) {
          onAddBook(result.book);
        }
        
        // Retirer de la liste des recommandations
        setRecommendations(prev => 
          prev.filter(rec => rec.ol_key !== recommendation.ol_key)
        );
      } else {
        toast.error(result.detail || 'Erreur lors de l\'ajout');
      }

    } catch (error) {
      console.error('Erreur ajout recommandation:', error);
      toast.error('Erreur lors de l\'ajout du livre');
    } finally {
      setAddingBooks(prev => {
        const newSet = new Set(prev);
        newSet.delete(recommendation.ol_key);
        return newSet;
      });
    }
  };

  const getCategoryBadge = (category) => {
    const badges = {
      'roman': { bg: 'bg-blue-100 text-blue-800', label: 'Roman' },
      'bd': { bg: 'bg-purple-100 text-purple-800', label: 'BD' },
      'manga': { bg: 'bg-pink-100 text-pink-800', label: 'Manga' }
    };
    return badges[category] || badges['roman'];
  };

  const formatAuthors = (authors) => {
    if (Array.isArray(authors)) {
      return authors.slice(0, 2).join(', ');
    }
    return authors || 'Auteur inconnu';
  };

  if (loading) {
    return (
      <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 ${className}`}>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            🤖 Recommandations IA
          </h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>
        
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500 mx-auto"></div>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Analyse de vos goûts littéraires...
          </p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 ${className}`}>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            🤖 Recommandations IA
          </h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>
        
        <div className="text-center py-8">
          <p className="text-red-600 dark:text-red-400 mb-4">{error}</p>
          <button
            onClick={fetchRecommendations}
            className="text-emerald-600 hover:text-emerald-700 dark:text-emerald-400"
          >
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 ${className}`}>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          🤖 Recommandations IA
        </h3>
        <button
          onClick={onClose}
          className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        >
          <XMarkIcon className="h-5 w-5" />
        </button>
      </div>

      {recommendations.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-gray-500 dark:text-gray-400">
            Pas de nouvelles recommandations pour le moment
          </p>
          <p className="text-sm text-gray-400 dark:text-gray-500 mt-2">
            Ajoutez plus de livres pour améliorer les suggestions
          </p>
        </div>
      ) : (
        <div className="space-y-4 max-h-96 overflow-y-auto">
          {recommendations.map((rec) => {
            const badge = getCategoryBadge(rec.category);
            const isAdding = addingBooks.has(rec.ol_key);
            
            return (
              <div
                key={rec.ol_key}
                className="flex items-start space-x-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
              >
                {/* Couverture */}
                <div className="flex-shrink-0">
                  {rec.cover_url ? (
                    <img
                      src={rec.cover_url}
                      alt={rec.title}
                      className="w-12 h-16 object-cover rounded"
                      onError={(e) => {
                        e.target.style.display = 'none';
                      }}
                    />
                  ) : (
                    <div className="w-12 h-16 bg-gray-300 dark:bg-gray-600 rounded flex items-center justify-center">
                      <span className="text-xs text-gray-500">📚</span>
                    </div>
                  )}
                </div>

                {/* Informations */}
                <div className="flex-grow min-w-0">
                  <h4 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {rec.title}
                  </h4>
                  <p className="text-xs text-gray-600 dark:text-gray-400 truncate">
                    {formatAuthors(rec.authors)}
                  </p>
                  
                  {/* Badge + Score */}
                  <div className="flex items-center mt-1 space-x-2">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${badge.bg}`}>
                      {badge.label}
                    </span>
                    
                    {rec.confidence_score && (
                      <div className="flex items-center">
                        <StarIcon className="h-3 w-3 text-yellow-400" />
                        <span className="text-xs text-gray-500 ml-1">
                          {Math.round(rec.confidence_score * 100)}%
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Raison */}
                  {rec.reason && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 italic">
                      {rec.reason}
                    </p>
                  )}
                </div>

                {/* Bouton ajouter */}
                <button
                  onClick={() => handleAddRecommendation(rec)}
                  disabled={isAdding}
                  className={`flex-shrink-0 p-2 rounded-full transition-colors ${
                    isAdding
                      ? 'bg-gray-200 dark:bg-gray-600 cursor-not-allowed'
                      : 'bg-emerald-100 hover:bg-emerald-200 dark:bg-emerald-900 dark:hover:bg-emerald-800'
                  }`}
                  title="Ajouter à ma bibliothèque"
                >
                  {isAdding ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-emerald-600"></div>
                  ) : (
                    <PlusIcon className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                  )}
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* Bouton rafraîchir */}
      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-600">
        <button
          onClick={fetchRecommendations}
          className="w-full text-sm text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 dark:hover:text-emerald-300"
        >
          🔄 Actualiser les recommandations
        </button>
      </div>
    </div>
  );
};

export default RecommendationsPanel;