/**
 * PHASE 3.1 - Composant Carte de Recommandation
 * Affiche une recommandation avec actions utilisateur
 */
import React, { useState } from 'react';
import { toast } from 'react-hot-toast';
import { 
  HeartIcon, 
  HandThumbUpIcon, 
  HandThumbDownIcon, 
  PlusIcon,
  XMarkIcon,
  BookOpenIcon,
  StarIcon
} from '@heroicons/react/24/outline';
import { 
  HeartIcon as HeartIconSolid,
  HandThumbUpIcon as HandThumbUpIconSolid,
  HandThumbDownIcon as HandThumbDownIconSolid
} from '@heroicons/react/24/solid';

import { recommendationService } from '../../services/recommendationService';

const RecommendationCard = ({ recommendation, onAddToLibrary, onFeedback }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [userFeedback, setUserFeedback] = useState(null);
  const [isAddingToLibrary, setIsAddingToLibrary] = useState(false);

  const handleAddToLibrary = async () => {
    setIsAddingToLibrary(true);
    try {
      await recommendationService.addRecommendedBook(recommendation);
      toast.success(`"${recommendation.title}" ajouté à votre bibliothèque !`);
      setUserFeedback('added_to_library');
      if (onAddToLibrary) {
        onAddToLibrary(recommendation);
      }
    } catch (error) {
      toast.error('Erreur lors de l\'ajout à la bibliothèque');
      console.error('Erreur ajout:', error);
    } finally {
      setIsAddingToLibrary(false);
    }
  };

  const handleFeedback = async (feedbackType) => {
    setIsLoading(true);
    try {
      await recommendationService.submitFeedback(recommendation.book_id, feedbackType);
      setUserFeedback(feedbackType);
      
      const messages = {
        'like': 'Merci pour votre avis positif !',
        'dislike': 'Merci pour votre retour, nous améliorerons nos suggestions',
        'not_interested': 'Recommandation masquée'
      };
      
      toast.success(messages[feedbackType]);
      
      if (onFeedback) {
        onFeedback(recommendation.book_id, feedbackType);
      }
    } catch (error) {
      toast.error('Erreur lors de l\'envoi du feedback');
      console.error('Erreur feedback:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getConfidenceColor = (score) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConfidenceLabel = (score) => {
    if (score >= 0.8) return 'Très recommandé';
    if (score >= 0.6) return 'Recommandé';
    return 'Peut-être';
  };

  const getCategoryColor = (category) => {
    const colors = {
      'roman': 'bg-blue-100 text-blue-800',
      'bd': 'bg-green-100 text-green-800',
      'manga': 'bg-purple-100 text-purple-800'
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  // Masquer si pas intéressé
  if (userFeedback === 'not_interested') {
    return null;
  }

  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200 p-4 border border-gray-200">
      {/* Header avec catégorie et score de confiance */}
      <div className="flex justify-between items-start mb-3">
        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(recommendation.category)}`}>
          {recommendation.category.toUpperCase()}
        </span>
        
        <div className="flex items-center space-x-1">
          <StarIcon className={`h-4 w-4 ${getConfidenceColor(recommendation.confidence_score)}`} />
          <span className={`text-xs font-medium ${getConfidenceColor(recommendation.confidence_score)}`}>
            {getConfidenceLabel(recommendation.confidence_score)}
          </span>
        </div>
      </div>

      {/* Contenu principal */}
      <div className="flex space-x-3">
        {/* Couverture */}
        <div className="flex-shrink-0">
          {recommendation.cover_url ? (
            <img
              src={recommendation.cover_url}
              alt={recommendation.title}
              className="w-16 h-24 object-cover rounded-md shadow-sm"
              onError={(e) => {
                e.target.style.display = 'none';
                e.target.nextSibling.style.display = 'flex';
              }}
            />
          ) : null}
          <div 
            className="w-16 h-24 bg-gray-200 rounded-md flex items-center justify-center"
            style={{ display: recommendation.cover_url ? 'none' : 'flex' }}
          >
            <BookOpenIcon className="h-8 w-8 text-gray-400" />
          </div>
        </div>

        {/* Informations */}
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-gray-900 truncate">
            {recommendation.title}
          </h3>
          <p className="text-xs text-gray-600 truncate mt-1">
            {recommendation.author}
          </p>
          
          {/* Raisons */}
          <div className="mt-2">
            {recommendation.reasons.map((reason, index) => (
              <span
                key={index}
                className="inline-block text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded-full mr-1 mb-1"
              >
                {reason}
              </span>
            ))}
          </div>

          {/* Score de confiance */}
          <div className="mt-2 flex items-center space-x-2">
            <div className="flex-1 bg-gray-200 rounded-full h-1">
              <div 
                className={`h-1 rounded-full ${
                  recommendation.confidence_score >= 0.8 ? 'bg-green-500' :
                  recommendation.confidence_score >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${recommendation.confidence_score * 100}%` }}
              />
            </div>
            <span className="text-xs text-gray-500">
              {Math.round(recommendation.confidence_score * 100)}%
            </span>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex justify-between items-center mt-4 pt-3 border-t border-gray-100">
        {/* Feedback */}
        <div className="flex space-x-2">
          <button
            onClick={() => handleFeedback('like')}
            disabled={isLoading || userFeedback}
            className={`p-2 rounded-full transition-colors ${
              userFeedback === 'like' 
                ? 'bg-green-100 text-green-600' 
                : 'text-gray-400 hover:text-green-600 hover:bg-green-50'
            }`}
          >
            {userFeedback === 'like' ? (
              <HandThumbUpIconSolid className="h-4 w-4" />
            ) : (
              <HandThumbUpIcon className="h-4 w-4" />
            )}
          </button>
          
          <button
            onClick={() => handleFeedback('dislike')}
            disabled={isLoading || userFeedback}
            className={`p-2 rounded-full transition-colors ${
              userFeedback === 'dislike' 
                ? 'bg-red-100 text-red-600' 
                : 'text-gray-400 hover:text-red-600 hover:bg-red-50'
            }`}
          >
            {userFeedback === 'dislike' ? (
              <HandThumbDownIconSolid className="h-4 w-4" />
            ) : (
              <HandThumbDownIcon className="h-4 w-4" />
            )}
          </button>
          
          <button
            onClick={() => handleFeedback('not_interested')}
            disabled={isLoading || userFeedback}
            className="p-2 rounded-full text-gray-400 hover:text-gray-600 hover:bg-gray-50 transition-colors"
          >
            <XMarkIcon className="h-4 w-4" />
          </button>
        </div>

        {/* Ajouter à la bibliothèque */}
        <button
          onClick={handleAddToLibrary}
          disabled={isAddingToLibrary || userFeedback === 'added_to_library'}
          className={`flex items-center space-x-1 px-3 py-1 rounded-full text-sm font-medium transition-colors ${
            userFeedback === 'added_to_library'
              ? 'bg-green-100 text-green-700 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {isAddingToLibrary ? (
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent" />
          ) : userFeedback === 'added_to_library' ? (
            <>
              <BookOpenIcon className="h-4 w-4" />
              <span>Ajouté</span>
            </>
          ) : (
            <>
              <PlusIcon className="h-4 w-4" />
              <span>Ajouter</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};

export default RecommendationCard;