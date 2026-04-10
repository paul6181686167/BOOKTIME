/**
 * PHASE 3.3 - Composant Profil Utilisateur
 * Affichage du profil public d'un utilisateur
 */
import React, { useState, useEffect } from 'react';
import socialService from '../../services/socialService';

const UserProfile = ({ userId, onClose }) => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isFollowing, setIsFollowing] = useState(false);
  const [followLoading, setFollowLoading] = useState(false);

  useEffect(() => {
    if (userId) {
      loadProfile();
    }
  }, [userId]);

  const loadProfile = async () => {
    try {
      setLoading(true);
      const response = await socialService.getProfile(userId);
      setProfile(response);
      setIsFollowing(response.is_following);
      setError(null);
    } catch (err) {
      setError('Erreur lors du chargement du profil');
      console.error('Erreur profil:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFollowToggle = async () => {
    if (!profile || !profile.can_follow) return;
    
    try {
      setFollowLoading(true);
      
      if (isFollowing) {
        await socialService.unfollowUser(userId);
        setIsFollowing(false);
        setProfile(prev => ({
          ...prev,
          followers_count: prev.followers_count - 1
        }));
      } else {
        await socialService.followUser(userId);
        setIsFollowing(true);
        setProfile(prev => ({
          ...prev,
          followers_count: prev.followers_count + 1
        }));
      }
    } catch (err) {
      console.error('Erreur follow/unfollow:', err);
      alert('Erreur lors de l\'opération');
    } finally {
      setFollowLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto animate-pulse">
          <div className="flex items-center space-x-4 mb-6">
            <div className="w-20 h-20 bg-gray-200 rounded-full"></div>
            <div className="flex-1">
              <div className="h-6 bg-gray-200 rounded w-1/3 mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            </div>
          </div>
          <div className="space-y-4">
            <div className="h-4 bg-gray-200 rounded w-full"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-md w-full">
          <div className="text-center">
            <div className="text-red-500 text-4xl mb-4">⚠️</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Erreur</h3>
            <p className="text-gray-500 mb-4">{error}</p>
            <div className="flex space-x-3">
              <button 
                onClick={loadProfile}
                className="flex-1 bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600"
              >
                Réessayer
              </button>
              <button 
                onClick={onClose}
                className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded hover:bg-gray-400"
              >
                Fermer
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!profile) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-8 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header du profil */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center space-x-4">
            <div className="w-20 h-20 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
              {profile.avatar_url ? (
                <img 
                  src={profile.avatar_url} 
                  alt={profile.display_name || 'Avatar'}
                  className="w-full h-full rounded-full object-cover"
                />
              ) : (
                <span className="text-white text-2xl font-bold">
                  {profile.display_name?.charAt(0) || 'U'}
                </span>
              )}
            </div>
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                {profile.display_name || 'Utilisateur'}
              </h2>
              {profile.location && (
                <p className="text-gray-500 flex items-center">
                  <span className="mr-1">📍</span>
                  {profile.location}
                </p>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl font-bold"
          >
            ×
          </button>
        </div>

        {/* Statistiques */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{profile.books_count}</div>
            <div className="text-sm text-gray-500">Livres</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{profile.followers_count}</div>
            <div className="text-sm text-gray-500">Followers</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">{profile.following_count}</div>
            <div className="text-sm text-gray-500">Following</div>
          </div>
        </div>

        {/* Bouton Follow/Unfollow */}
        {profile.can_follow && (
          <div className="mb-6">
            <button
              onClick={handleFollowToggle}
              disabled={followLoading}
              className={`w-full py-2 px-4 rounded-lg font-medium transition-colors ${
                isFollowing
                  ? 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  : 'bg-blue-500 text-white hover:bg-blue-600'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {followLoading 
                ? 'Chargement...' 
                : isFollowing 
                  ? 'Ne plus suivre' 
                  : 'Suivre'
              }
            </button>
          </div>
        )}

        {/* Biographie */}
        {profile.bio && (
          <div className="mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-2">À propos</h3>
            <p className="text-gray-600">{profile.bio}</p>
          </div>
        )}

        {/* Site web */}
        {profile.website && (
          <div className="mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-2">Site web</h3>
            <a 
              href={profile.website} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-blue-500 hover:text-blue-600"
            >
              {profile.website}
            </a>
          </div>
        )}

        {/* Statistiques de lecture */}
        {profile.reading_stats && (
          <div className="mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-3">Statistiques de lecture</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="text-sm text-gray-500">Livres terminés</div>
                <div className="text-lg font-semibold text-gray-900">
                  {profile.reading_stats.completed_books}
                </div>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="text-sm text-gray-500">En cours</div>
                <div className="text-lg font-semibold text-gray-900">
                  {profile.reading_stats.reading_books}
                </div>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="text-sm text-gray-500">Note moyenne</div>
                <div className="text-lg font-semibold text-gray-900">
                  {profile.reading_stats.avg_rating || 0}/5
                </div>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="text-sm text-gray-500">Pages lues</div>
                <div className="text-lg font-semibold text-gray-900">
                  {profile.reading_stats.total_pages || 0}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Lectures en cours */}
        {profile.current_reading && profile.current_reading.length > 0 && (
          <div className="mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-3">Lectures en cours</h3>
            <div className="space-y-3">
              {profile.current_reading.map((book, index) => (
                <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                  <img 
                    src={book.cover_url || '/placeholder-book.jpg'} 
                    alt={book.title}
                    className="w-12 h-16 object-cover rounded"
                  />
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">{book.title}</h4>
                    <p className="text-sm text-gray-500">{book.author}</p>
                    <div className="mt-1 w-full bg-gray-200 rounded-full h-1.5">
                      <div 
                        className="bg-blue-500 h-1.5 rounded-full" 
                        style={{ width: `${book.progress}%` }}
                      ></div>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">{Math.round(book.progress)}% terminé</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Livres récents */}
        {profile.recent_books && profile.recent_books.length > 0 && (
          <div className="mb-6">
            <h3 className="text-lg font-medium text-gray-900 mb-3">Livres récents</h3>
            <div className="grid grid-cols-3 gap-3">
              {profile.recent_books.slice(0, 6).map((book, index) => (
                <div key={index} className="text-center">
                  <img 
                    src={book.cover_url || '/placeholder-book.jpg'} 
                    alt={book.title}
                    className="w-full h-24 object-cover rounded mb-2"
                  />
                  <h4 className="text-xs font-medium text-gray-900 truncate">{book.title}</h4>
                  <p className="text-xs text-gray-500 truncate">{book.author}</p>
                  {book.rating && (
                    <div className="flex justify-center mt-1">
                      {[...Array(5)].map((_, i) => (
                        <span
                          key={i}
                          className={`text-xs ${i < book.rating ? 'text-yellow-400' : 'text-gray-300'}`}
                        >
                          ★
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Pied de page */}
        <div className="text-center text-sm text-gray-500">
          Membre depuis {new Date(profile.created_at).toLocaleDateString()}
        </div>
      </div>
    </div>
  );
};

export default UserProfile;