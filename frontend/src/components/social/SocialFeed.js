/**
 * PHASE 3.3 - Composant Feed Social
 * Affichage du feed d'activités sociales
 */
import React, { useState, useEffect } from 'react';
import socialService from '../../services/socialService';

const SocialFeed = () => {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [hasMore, setHasMore] = useState(false);
  const [offset, setOffset] = useState(0);

  useEffect(() => {
    loadFeed();
  }, []);

  const loadFeed = async (loadMore = false) => {
    try {
      setLoading(true);
      const currentOffset = loadMore ? offset : 0;
      
      const response = await socialService.getFeed(20, currentOffset);
      
      if (loadMore) {
        setActivities(prev => [...prev, ...response.activities]);
      } else {
        setActivities(response.activities);
      }
      
      setHasMore(response.has_more);
      setOffset(currentOffset + 20);
      setError(null);
    } catch (err) {
      setError('Erreur lors du chargement du feed');
      console.error('Erreur feed:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatActivityContent = (activity) => {
    const { activity_type, content, user } = activity;
    
    switch (activity_type) {
      case 'book_completed':
        return (
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <img 
                src={content.cover_url || '/placeholder-book.jpg'} 
                alt={content.title}
                className="w-16 h-20 object-cover rounded"
              />
            </div>
            <div className="flex-1">
              <p className="text-sm text-gray-600 mb-1">
                <span className="font-medium text-gray-900">{user.display_name}</span> a terminé
              </p>
              <h4 className="font-medium text-gray-900">{content.title}</h4>
              <p className="text-sm text-gray-500">par {content.author}</p>
              {content.rating && (
                <div className="flex items-center mt-1">
                  <span className="text-sm text-gray-500">Note: </span>
                  <div className="flex ml-1">
                    {[...Array(5)].map((_, i) => (
                      <span
                        key={i}
                        className={`text-sm ${i < content.rating ? 'text-yellow-400' : 'text-gray-300'}`}
                      >
                        ★
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {content.review && (
                <p className="text-sm text-gray-600 mt-2 italic">"{content.review}"</p>
              )}
            </div>
          </div>
        );
      
      case 'book_added':
        return (
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <img 
                src={content.cover_url || '/placeholder-book.jpg'} 
                alt={content.title}
                className="w-16 h-20 object-cover rounded"
              />
            </div>
            <div className="flex-1">
              <p className="text-sm text-gray-600 mb-1">
                <span className="font-medium text-gray-900">{user.display_name}</span> a ajouté
              </p>
              <h4 className="font-medium text-gray-900">{content.title}</h4>
              <p className="text-sm text-gray-500">par {content.author}</p>
              <span className="inline-block mt-1 px-2 py-1 text-xs font-medium text-blue-600 bg-blue-100 rounded">
                {content.category}
              </span>
            </div>
          </div>
        );
      
      case 'book_rated':
        return (
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <img 
                src={content.cover_url || '/placeholder-book.jpg'} 
                alt={content.title}
                className="w-16 h-20 object-cover rounded"
              />
            </div>
            <div className="flex-1">
              <p className="text-sm text-gray-600 mb-1">
                <span className="font-medium text-gray-900">{user.display_name}</span> a noté
              </p>
              <h4 className="font-medium text-gray-900">{content.title}</h4>
              <p className="text-sm text-gray-500">par {content.author}</p>
              <div className="flex items-center mt-1">
                <div className="flex">
                  {[...Array(5)].map((_, i) => (
                    <span
                      key={i}
                      className={`text-sm ${i < content.rating ? 'text-yellow-400' : 'text-gray-300'}`}
                    >
                      ★
                    </span>
                  ))}
                </div>
                <span className="ml-2 text-sm text-gray-500">({content.rating}/5)</span>
              </div>
            </div>
          </div>
        );
      
      case 'user_followed':
        return (
          <div className="flex items-center space-x-3">
            <div className="flex-shrink-0">
              <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                <span className="text-white font-medium">
                  {user.display_name?.charAt(0) || 'U'}
                </span>
              </div>
            </div>
            <div className="flex-1">
              <p className="text-sm text-gray-600">
                <span className="font-medium text-gray-900">{user.display_name}</span> suit maintenant un nouvel utilisateur
              </p>
            </div>
          </div>
        );
      
      default:
        return (
          <div className="flex items-center space-x-3">
            <div className="flex-shrink-0">
              <div className="w-10 h-10 bg-gray-500 rounded-full flex items-center justify-center">
                <span className="text-white font-medium">
                  {user.display_name?.charAt(0) || 'U'}
                </span>
              </div>
            </div>
            <div className="flex-1">
              <p className="text-sm text-gray-600">
                <span className="font-medium text-gray-900">{user.display_name}</span> a une nouvelle activité
              </p>
            </div>
          </div>
        );
    }
  };

  const formatTimeAgo = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) return 'À l\'instant';
    if (diffInSeconds < 3600) return `Il y a ${Math.floor(diffInSeconds / 60)}min`;
    if (diffInSeconds < 86400) return `Il y a ${Math.floor(diffInSeconds / 3600)}h`;
    if (diffInSeconds < 2592000) return `Il y a ${Math.floor(diffInSeconds / 86400)}j`;
    
    return date.toLocaleDateString();
  };

  if (loading && activities.length === 0) {
    return (
      <div className="space-y-6">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow p-6 animate-pulse">
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0">
                <div className="w-16 h-20 bg-gray-200 rounded"></div>
              </div>
              <div className="flex-1">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2 mb-1"></div>
                <div className="h-3 bg-gray-200 rounded w-1/4"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <span className="text-red-400">⚠️</span>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Erreur</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
            <button 
              onClick={() => loadFeed()}
              className="mt-2 text-sm text-red-600 hover:text-red-500 font-medium"
            >
              Réessayer
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (activities.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center">
        <div className="text-gray-400 mb-4">
          <span className="text-4xl">📚</span>
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">Votre feed est vide</h3>
        <p className="text-gray-500">
          Suivez d'autres utilisateurs pour voir leurs activités de lecture ici.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {activities.map((activity, index) => (
        <div key={`${activity.id}-${index}`} className="bg-white rounded-lg shadow p-6">
          {formatActivityContent(activity)}
          
          <div className="mt-4 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button className="flex items-center space-x-1 text-sm text-gray-500 hover:text-red-500">
                <span className={activity.is_liked ? 'text-red-500' : ''}>❤️</span>
                <span>{activity.likes_count || 0}</span>
              </button>
              <button className="flex items-center space-x-1 text-sm text-gray-500 hover:text-blue-500">
                <span>💬</span>
                <span>{activity.comments_count || 0}</span>
              </button>
            </div>
            <span className="text-sm text-gray-400">
              {formatTimeAgo(activity.created_at)}
            </span>
          </div>
        </div>
      ))}
      
      {hasMore && (
        <div className="flex justify-center">
          <button
            onClick={() => loadFeed(true)}
            disabled={loading}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            {loading ? 'Chargement...' : 'Charger plus'}
          </button>
        </div>
      )}
    </div>
  );
};

export default SocialFeed;