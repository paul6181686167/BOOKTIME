/**
 * PHASE 3.1 - Page de Recommandations
 * Page principale pour afficher et gérer les recommandations
 */
import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { 
  SparklesIcon, 
  FireIcon, 
  UserIcon,
  BookOpenIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';

import RecommendationGrid from './RecommendationGrid';
import { recommendationService } from '../../services/recommendationService';

const RecommendationPage = () => {
  const [recommendations, setRecommendations] = useState([]);
  const [userProfile, setUserProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('personalized');

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Charger les recommandations et le profil utilisateur en parallèle
      const [recommendationsResponse, profileResponse] = await Promise.all([
        recommendationService.getPersonalized({ limit: 20 }),
        recommendationService.getUserProfile()
      ]);

      if (recommendationsResponse.success) {
        setRecommendations(recommendationsResponse.data.recommendations);
        setUserProfile(recommendationsResponse.data.user_profile);
      } else {
        setError('Erreur lors du chargement des recommandations');
      }

      if (profileResponse.success) {
        setUserProfile(profileResponse.data);
      }

    } catch (error) {
      console.error('Erreur chargement initial:', error);
      setError('Erreur lors du chargement des données');
      toast.error('Erreur lors du chargement des recommandations');
    } finally {
      setIsLoading(false);
    }
  };

  const loadPopularRecommendations = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await recommendationService.getPopular({ limit: 20 });
      
      if (response.success) {
        setRecommendations(response.data.recommendations);
      } else {
        setError('Erreur lors du chargement des recommandations populaires');
      }
    } catch (error) {
      console.error('Erreur chargement populaires:', error);
      setError('Erreur lors du chargement des recommandations populaires');
      toast.error('Erreur lors du chargement des recommandations populaires');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    
    if (tab === 'personalized') {
      loadInitialData();
    } else if (tab === 'popular') {
      loadPopularRecommendations();
    }
  };

  const getWelcomeMessage = () => {
    if (!userProfile) return "Découvrez de nouveaux livres";
    
    if (!userProfile.has_books) {
      return "Bienvenue ! Voici quelques livres populaires pour commencer";
    }
    
    const favoriteAuthors = userProfile.favorite_authors || [];
    const favoriteCategories = userProfile.favorite_categories || [];
    
    if (favoriteAuthors.length > 0 && favoriteCategories.length > 0) {
      return `Basé sur vos goûts pour ${favoriteAuthors[0]} et les ${favoriteCategories[0]}s`;
    } else if (favoriteAuthors.length > 0) {
      return `Basé sur vos goûts pour ${favoriteAuthors[0]}`;
    } else if (favoriteCategories.length > 0) {
      return `Basé sur vos goûts pour les ${favoriteCategories[0]}s`;
    }
    
    return "Recommandations personnalisées basées sur votre bibliothèque";
  };

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center py-12">
          <BookOpenIcon className="h-12 w-12 text-red-300 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">
            Erreur de chargement
          </h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={loadInitialData}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="flex justify-center items-center space-x-2 mb-4">
          <SparklesIcon className="h-8 w-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-900">
            Recommandations
          </h1>
        </div>
        <p className="text-lg text-gray-600">
          {getWelcomeMessage()}
        </p>
      </div>

      {/* Statistiques rapides */}
      {userProfile && userProfile.has_books && (
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-center">
            <div className="flex flex-col items-center">
              <BookOpenIcon className="h-8 w-8 text-blue-600 mb-2" />
              <div className="text-2xl font-bold text-blue-600">
                {userProfile.total_books}
              </div>
              <div className="text-sm text-gray-600">Livres dans votre bibliothèque</div>
            </div>
            
            <div className="flex flex-col items-center">
              <UserIcon className="h-8 w-8 text-green-600 mb-2" />
              <div className="text-2xl font-bold text-green-600">
                {userProfile.favorite_authors?.length || 0}
              </div>
              <div className="text-sm text-gray-600">Auteurs favoris</div>
            </div>
            
            <div className="flex flex-col items-center">
              <ChartBarIcon className="h-8 w-8 text-purple-600 mb-2" />
              <div className="text-2xl font-bold text-purple-600">
                {Math.round((userProfile.reading_patterns?.completion_rate || 0) * 100)}%
              </div>
              <div className="text-sm text-gray-600">Taux de completion</div>
            </div>
            
            <div className="flex flex-col items-center">
              <SparklesIcon className="h-8 w-8 text-yellow-600 mb-2" />
              <div className="text-2xl font-bold text-yellow-600">
                {(userProfile.reading_patterns?.average_rating || 0).toFixed(1)}
              </div>
              <div className="text-sm text-gray-600">Note moyenne</div>
            </div>
          </div>
        </div>
      )}

      {/* Onglets */}
      <div className="flex space-x-1 mb-8">
        <button
          onClick={() => handleTabChange('personalized')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-md font-medium transition-colors ${
            activeTab === 'personalized'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          <SparklesIcon className="h-4 w-4" />
          <span>Personnalisées</span>
        </button>
        
        <button
          onClick={() => handleTabChange('popular')}
          className={`flex items-center space-x-2 px-4 py-2 rounded-md font-medium transition-colors ${
            activeTab === 'popular'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          <FireIcon className="h-4 w-4" />
          <span>Populaires</span>
        </button>
      </div>

      {/* Contenu */}
      {isLoading ? (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-600 border-t-transparent"></div>
          <span className="ml-2 text-gray-600">Chargement des recommandations...</span>
        </div>
      ) : (
        <RecommendationGrid 
          initialRecommendations={recommendations}
          userProfile={userProfile}
        />
      )}
    </div>
  );
};

export default RecommendationPage;