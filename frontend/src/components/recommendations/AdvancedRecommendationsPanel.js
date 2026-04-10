/**
 * PHASE 3.4 - Panneau de Recommandations Avancées
 * Interface pour recommandations IA et contextuelles
 */
import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';

const AdvancedRecommendationsPanel = ({ onRecommendationSelect, currentUser }) => {
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeMode, setActiveMode] = useState('contextual');
  const [userProfile, setUserProfile] = useState(null);
  const [context, setContext] = useState({
    time_of_day: 'unknown',
    mood: 'neutral',
    available_time: 60,
    location: 'home',
    reading_goal: 'entertainment'
  });

  useEffect(() => {
    loadUserProfile();
    loadRecommendations();
  }, [activeMode]);

  const loadUserProfile = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/recommendations/advanced/user-profile/advanced`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setUserProfile(data.data);
      }
    } catch (error) {
      console.error('Erreur chargement profil avancé:', error);
    }
  };

  const loadRecommendations = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      let url, body = null;

      if (activeMode === 'contextual') {
        url = `${process.env.REACT_APP_BACKEND_URL}/api/recommendations/advanced/contextual`;
        body = JSON.stringify(context);
      } else if (activeMode === 'social') {
        url = `${process.env.REACT_APP_BACKEND_URL}/api/recommendations/advanced/social`;
      }

      const response = await fetch(url, {
        method: activeMode === 'contextual' ? 'POST' : 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: body
      });

      if (response.ok) {
        const data = await response.json();
        setRecommendations(data.data.recommendations || []);
      } else {
        throw new Error('Erreur lors du chargement');
      }
    } catch (error) {
      console.error('Erreur recommandations avancées:', error);
      setError('Erreur lors du chargement des recommandations');
    } finally {
      setLoading(false);
    }
  };

  const handleContextChange = (field, value) => {
    setContext(prev => ({ ...prev, [field]: value }));
  };

  const handleRecommendationClick = (recommendation) => {
    // Enregistrer le feedback
    submitFeedback(recommendation.recommendation_id, 'clicked');
    
    // Notifier le parent
    if (onRecommendationSelect) {
      onRecommendationSelect(recommendation.book);
    }
  };

  const submitFeedback = async (recommendationId, feedbackType, rating = null) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/recommendations/advanced/feedback`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          recommendation_id: recommendationId,
          feedback_type: feedbackType,
          rating: rating,
          context: context
        })
      });

      if (response.ok) {
        console.log('Feedback envoyé avec succès');
      }
    } catch (error) {
      console.error('Erreur envoi feedback:', error);
    }
  };

  const predictRating = async (bookId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/recommendations/advanced/ml/predict-rating?book_id=${bookId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        toast.success(`Rating prédit: ${data.data.predicted_rating}/5 (${Math.round(data.data.confidence * 100)}% confiance)`);
      }
    } catch (error) {
      console.error('Erreur prédiction rating:', error);
    }
  };

  const getTimeOfDay = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'morning';
    if (hour < 17) return 'afternoon';
    if (hour < 21) return 'evening';
    return 'night';
  };

  const detectContext = () => {
    const detectedContext = {
      ...context,
      time_of_day: getTimeOfDay()
    };
    setContext(detectedContext);
    loadRecommendations();
    toast.success('Contexte détecté automatiquement !');
  };

  const renderContextualControls = () => (
    <div className="bg-blue-50 rounded-lg p-4 mb-4">
      <div className="flex justify-between items-center mb-3">
        <h4 className="font-medium text-blue-900">Contexte de Lecture</h4>
        <button
          onClick={detectContext}
          className="text-sm bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600"
        >
          🤖 Auto-detect
        </button>
      </div>
      
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-sm font-medium text-blue-800 mb-1">Humeur</label>
          <select
            value={context.mood}
            onChange={(e) => handleContextChange('mood', e.target.value)}
            className="w-full text-sm border border-blue-200 rounded px-2 py-1"
          >
            <option value="neutral">😐 Neutre</option>
            <option value="happy">😊 Joyeux</option>
            <option value="stressed">😰 Stressé</option>
            <option value="curious">🤔 Curieux</option>
            <option value="relaxed">😌 Détendu</option>
            <option value="sad">😢 Triste</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-blue-800 mb-1">Lieu</label>
          <select
            value={context.location}
            onChange={(e) => handleContextChange('location', e.target.value)}
            className="w-full text-sm border border-blue-200 rounded px-2 py-1"
          >
            <option value="home">🏠 Maison</option>
            <option value="commute">🚊 Transport</option>
            <option value="work">💼 Travail</option>
            <option value="travel">✈️ Voyage</option>
            <option value="cafe">☕ Café</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-blue-800 mb-1">Temps disponible</label>
          <select
            value={context.available_time}
            onChange={(e) => handleContextChange('available_time', parseInt(e.target.value))}
            className="w-full text-sm border border-blue-200 rounded px-2 py-1"
          >
            <option value={15}>15 min</option>
            <option value={30}>30 min</option>
            <option value={60}>1 heure</option>
            <option value={120}>2 heures</option>
            <option value={240}>4+ heures</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-blue-800 mb-1">Objectif</label>
          <select
            value={context.reading_goal}
            onChange={(e) => handleContextChange('reading_goal', e.target.value)}
            className="w-full text-sm border border-blue-200 rounded px-2 py-1"
          >
            <option value="entertainment">🎯 Divertissement</option>
            <option value="learning">📚 Apprentissage</option>
            <option value="relaxation">🧘 Relaxation</option>
            <option value="exploration">🔍 Exploration</option>
          </select>
        </div>
      </div>
      
      <button
        onClick={loadRecommendations}
        className="w-full mt-3 bg-blue-500 text-white py-2 rounded hover:bg-blue-600 transition-colors"
      >
        🎯 Recommandations Contextuelles
      </button>
    </div>
  );

  const renderUserInsights = () => {
    if (!userProfile) return null;

    return (
      <div className="bg-purple-50 rounded-lg p-4 mb-4">
        <h4 className="font-medium text-purple-900 mb-3">🧠 Insights IA</h4>
        
        <div className="grid grid-cols-3 gap-3 text-center">
          <div className="bg-white rounded p-2">
            <div className="text-lg font-bold text-purple-600">
              {userProfile.reading_velocity?.toFixed(1) || '0'}
            </div>
            <div className="text-xs text-purple-700">Livres/mois</div>
          </div>
          
          <div className="bg-white rounded p-2">
            <div className="text-lg font-bold text-green-600">
              {Math.round((userProfile.behavioral_insights?.exploration_tendency || 0) * 100)}%
            </div>
            <div className="text-xs text-green-700">Exploration</div>
          </div>
          
          <div className="bg-white rounded p-2">
            <div className="text-lg font-bold text-orange-600">
              {Math.round((userProfile.behavioral_insights?.social_influence || 0) * 100)}%
            </div>
            <div className="text-xs text-orange-700">Social</div>
          </div>
        </div>
        
        {userProfile.behavioral_insights?.behavioral_clusters && (
          <div className="mt-3">
            <div className="text-sm text-purple-800 mb-1">Profil lecteur :</div>
            <div className="flex flex-wrap gap-1">
              {userProfile.behavioral_insights.behavioral_clusters.map((cluster, index) => (
                <span key={index} className="text-xs bg-purple-200 text-purple-800 px-2 py-1 rounded">
                  {cluster.replace('_', ' ')}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderRecommendation = (rec, index) => (
    <div key={rec.recommendation_id} className="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow">
      <div className="flex space-x-3">
        <div className="flex-shrink-0">
          <img
            src={rec.book.cover_url || '/placeholder-book.jpg'}
            alt={rec.book.title}
            className="w-16 h-20 object-cover rounded"
          />
        </div>
        
        <div className="flex-1">
          <h4 className="font-medium text-gray-900 mb-1">{rec.book.title}</h4>
          <p className="text-sm text-gray-600 mb-2">{rec.book.author}</p>
          
          {/* Scores */}
          <div className="flex items-center space-x-2 mb-2">
            <div className="flex items-center bg-green-100 px-2 py-1 rounded">
              <span className="text-xs font-medium text-green-800">
                {Math.round(rec.scoring.global_score * 100)}% match
              </span>
            </div>
            
            {rec.scoring.novelty_score > 0.7 && (
              <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                ✨ Nouveau
              </span>
            )}
            
            {rec.scoring.learning_potential > 0.7 && (
              <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                📚 Éducatif
              </span>
            )}
          </div>
          
          {/* Raisons */}
          <div className="text-xs text-gray-600 mb-3">
            {rec.reasoning.context_reasons.length > 0 ? (
              <div className="mb-1">
                <span className="font-medium">🎯 Contexte : </span>
                {rec.reasoning.context_reasons[0]}
              </div>
            ) : null}
            
            {rec.reasoning.base_reasons.length > 0 && (
              <div>
                <span className="font-medium">💡 Pourquoi : </span>
                {rec.reasoning.base_reasons[0]}
              </div>
            )}
          </div>
          
          {/* Actions */}
          <div className="flex space-x-2">
            <button
              onClick={() => handleRecommendationClick(rec)}
              className="text-sm bg-blue-500 text-white px-3 py-1 rounded hover:bg-blue-600"
            >
              📖 Voir détails
            </button>
            
            <button
              onClick={() => predictRating(rec.book.book_id)}
              className="text-sm bg-purple-500 text-white px-3 py-1 rounded hover:bg-purple-600"
            >
              🤖 Prédire note
            </button>
            
            <button
              onClick={() => submitFeedback(rec.recommendation_id, 'not_interested')}
              className="text-sm bg-gray-300 text-gray-700 px-3 py-1 rounded hover:bg-gray-400"
            >
              ❌
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          🤖 Recommandations IA Avancées
        </h2>
        <p className="text-gray-600">
          Recommandations personnalisées par intelligence artificielle
        </p>
      </div>

      {/* Modes */}
      <div className="flex space-x-2 mb-6">
        <button
          onClick={() => setActiveMode('contextual')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeMode === 'contextual'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          🎯 Contextuel
        </button>
        
        <button
          onClick={() => setActiveMode('social')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeMode === 'social'
              ? 'bg-purple-500 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          👥 Social
        </button>
      </div>

      {/* Insights utilisateur */}
      {renderUserInsights()}

      {/* Contrôles contextuels */}
      {activeMode === 'contextual' && renderContextualControls()}

      {/* Recommandations */}
      {loading ? (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-600 border-t-transparent"></div>
          <span className="ml-2 text-gray-600">Génération des recommandations IA...</span>
        </div>
      ) : error ? (
        <div className="text-center py-12">
          <div className="text-red-500 mb-4">⚠️ {error}</div>
          <button
            onClick={loadRecommendations}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            Réessayer
          </button>
        </div>
      ) : recommendations.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-500 mb-4">
            {activeMode === 'social' 
              ? '👥 Suivez d\'autres utilisateurs pour voir leurs recommandations'
              : '🤖 Aucune recommandation contextuelle trouvée'
            }
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {recommendations.map((rec, index) => renderRecommendation(rec, index))}
        </div>
      )}
    </div>
  );
};

export default AdvancedRecommendationsPanel;