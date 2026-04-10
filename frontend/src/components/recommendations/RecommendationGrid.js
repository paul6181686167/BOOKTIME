/**
 * PHASE 3.1 - Grille de Recommandations
 * Affiche une grille de recommandations avec gestion des états
 */
import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { 
  ArrowPathIcon, 
  FunnelIcon, 
  EyeIcon,
  ChartBarIcon,
  UserIcon
} from '@heroicons/react/24/outline';

import RecommendationCard from './RecommendationCard';
import { recommendationService } from '../../services/recommendationService';

const RecommendationGrid = ({ initialRecommendations = [], userProfile = null }) => {
  const [recommendations, setRecommendations] = useState(initialRecommendations);
  const [isLoading, setIsLoading] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState('all');
  const [showUserProfile, setShowUserProfile] = useState(false);
  const [stats, setStats] = useState(null);

  useEffect(() => {
    if (initialRecommendations.length > 0) {
      setRecommendations(initialRecommendations);
    }
  }, [initialRecommendations]);

  const handleRefresh = async () => {
    setIsLoading(true);
    try {
      const response = await recommendationService.getPersonalized({ 
        limit: 20, 
        refresh: true 
      });
      
      if (response.success) {
        setRecommendations(response.data.recommendations);
        toast.success('Recommandations mises à jour !');
      }
    } catch (error) {
      toast.error('Erreur lors du rafraîchissement');
      console.error('Erreur refresh:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCategoryFilter = async (category) => {
    setCategoryFilter(category);
    
    if (category === 'all') {
      handleRefresh();
      return;
    }

    setIsLoading(true);
    try {
      const response = await recommendationService.getPersonalized({ 
        limit: 20, 
        category: category 
      });
      
      if (response.success) {
        setRecommendations(response.data.recommendations);
      }
    } catch (error) {
      toast.error('Erreur lors du filtrage');
      console.error('Erreur filtre:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddToLibrary = (recommendation) => {
    // Retirer la recommandation de la liste
    setRecommendations(prev => 
      prev.filter(rec => rec.book_id !== recommendation.book_id)
    );
  };

  const handleFeedback = (bookId, feedbackType) => {
    if (feedbackType === 'not_interested') {
      // Retirer la recommandation de la liste
      setRecommendations(prev => 
        prev.filter(rec => rec.book_id !== bookId)
      );
    }
  };

  const loadStats = async () => {
    try {
      const response = await recommendationService.getStats();
      if (response.success) {
        setStats(response.data);
      }
    } catch (error) {
      console.error('Erreur chargement stats:', error);
    }
  };

  const filteredRecommendations = recommendations.filter(rec => {
    if (categoryFilter === 'all') return true;
    return rec.category === categoryFilter;
  });

  const getCategoryCount = (category) => {
    return recommendations.filter(rec => rec.category === category).length;
  };

  return (
    <div className="space-y-6">
      {/* Header avec actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">
            Recommandations pour vous
          </h2>
          <p className="text-sm text-gray-600 mt-1">
            Découvrez de nouveaux livres basés sur vos goûts
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowUserProfile(!showUserProfile)}
            className="flex items-center space-x-1 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            <UserIcon className="h-4 w-4" />
            <span>Profil</span>
          </button>
          
          <button
            onClick={loadStats}
            className="flex items-center space-x-1 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            <ChartBarIcon className="h-4 w-4" />
            <span>Stats</span>
          </button>
          
          <button
            onClick={handleRefresh}
            disabled={isLoading}
            className="flex items-center space-x-1 px-3 py-2 text-sm font-medium text-white bg-blue-600 border border-blue-600 rounded-md hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            <ArrowPathIcon className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            <span>Actualiser</span>
          </button>
        </div>
      </div>

      {/* Profil utilisateur */}
      {showUserProfile && userProfile && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="text-lg font-medium text-blue-900 mb-3">Votre Profil de Lecture</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <h4 className="font-medium text-blue-800 mb-2">Auteurs Favoris</h4>
              <div className="space-y-1">
                {userProfile.favorite_authors?.slice(0, 3).map((author, index) => (
                  <span key={index} className="inline-block text-sm bg-blue-100 text-blue-700 px-2 py-1 rounded-full mr-1">
                    {author}
                  </span>
                ))}
              </div>
            </div>
            
            <div>
              <h4 className="font-medium text-blue-800 mb-2">Catégories Préférées</h4>
              <div className="space-y-1">
                {userProfile.favorite_categories?.map((category, index) => (
                  <span key={index} className="inline-block text-sm bg-blue-100 text-blue-700 px-2 py-1 rounded-full mr-1">
                    {category}
                  </span>
                ))}
              </div>
            </div>
            
            <div>
              <h4 className="font-medium text-blue-800 mb-2">Statistiques</h4>
              <div className="text-sm text-blue-700 space-y-1">
                <div>Total livres: {userProfile.total_books}</div>
                <div>Taux de completion: {Math.round((userProfile.reading_patterns?.completion_rate || 0) * 100)}%</div>
                <div>Note moyenne: {(userProfile.reading_patterns?.average_rating || 0).toFixed(1)}/5</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Statistiques */}
      {stats && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
          <h3 className="text-lg font-medium text-gray-900 mb-3">Vos Statistiques de Recommandations</h3>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-green-600">{stats.feedback_stats?.like || 0}</div>
              <div className="text-sm text-gray-600">Aimées</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-blue-600">{stats.feedback_stats?.added_to_library || 0}</div>
              <div className="text-sm text-gray-600">Ajoutées</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-red-600">{stats.feedback_stats?.dislike || 0}</div>
              <div className="text-sm text-gray-600">Refusées</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-purple-600">{Math.round(stats.engagement_rate || 0)}%</div>
              <div className="text-sm text-gray-600">Engagement</div>
            </div>
          </div>
        </div>
      )}

      {/* Filtres par catégorie */}
      <div className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg">
        <FunnelIcon className="h-5 w-5 text-gray-500" />
        <span className="text-sm font-medium text-gray-700">Filtrer par catégorie:</span>
        
        <div className="flex space-x-2">
          {[
            { key: 'all', label: `Tout (${recommendations.length})` },
            { key: 'roman', label: `Romans (${getCategoryCount('roman')})` },
            { key: 'bd', label: `BD (${getCategoryCount('bd')})` },
            { key: 'manga', label: `Mangas (${getCategoryCount('manga')})` }
          ].map(({ key, label }) => (
            <button
              key={key}
              onClick={() => handleCategoryFilter(key)}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                categoryFilter === key
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Grille de recommandations */}
      {isLoading ? (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-600 border-t-transparent"></div>
          <span className="ml-2 text-gray-600">Chargement des recommandations...</span>
        </div>
      ) : filteredRecommendations.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredRecommendations.map((recommendation) => (
            <RecommendationCard
              key={recommendation.book_id}
              recommendation={recommendation}
              onAddToLibrary={handleAddToLibrary}
              onFeedback={handleFeedback}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <EyeIcon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Aucune recommandation trouvée
          </h3>
          <p className="text-gray-600 mb-4">
            {categoryFilter === 'all' 
              ? 'Nous n\'avons pas trouvé de recommandations pour vous en ce moment.'
              : `Aucune recommandation trouvée pour la catégorie "${categoryFilter}".`
            }
          </p>
          <button
            onClick={handleRefresh}
            className="inline-flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            <ArrowPathIcon className="h-4 w-4" />
            <span>Actualiser les recommandations</span>
          </button>
        </div>
      )}
    </div>
  );
};

export default RecommendationGrid;