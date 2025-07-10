/**
 * PHASE 3.4 - Modal de Recommandations Avancées
 * Interface pour les recommandations IA et ML
 */
import React, { useState, useEffect } from 'react';
import advancedRecommendationService from '../../services/advancedRecommendationService';

const AdvancedRecommendationsModal = ({ isOpen, onClose, onAddBook }) => {
  const [activeTab, setActiveTab] = useState('contextual');
  const [loading, setLoading] = useState(false);
  const [contextualRecs, setContextualRecs] = useState([]);
  const [socialRecs, setSocialRecs] = useState([]);
  const [userProfile, setUserProfile] = useState(null);
  const [mlStats, setMLStats] = useState(null);
  const [context, setContext] = useState({});

  useEffect(() => {
    if (isOpen) {
      loadAdvancedRecommendations();
    }
  }, [isOpen]);

  const loadAdvancedRecommendations = async () => {
    setLoading(true);
    try {
      // Récupérer le contexte intelligent
      const smartContext = advancedRecommendationService.getSmartContext();
      setContext(smartContext);

      // Charger les différents types de recommandations
      await Promise.all([
        loadContextualRecommendations(smartContext),
        loadSocialRecommendations(),
        loadUserProfile(),
        loadMLStats()
      ]);
    } catch (error) {
      console.error('Erreur lors du chargement des recommandations avancées:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadContextualRecommendations = async (ctx = context) => {
    try {
      const response = await advancedRecommendationService.getContextualRecommendations(ctx, 10);
      setContextualRecs(response.data || []);
    } catch (error) {
      console.error('Erreur recommandations contextuelles:', error);
      setContextualRecs([]);
    }
  };

  const loadSocialRecommendations = async () => {
    try {
      const response = await advancedRecommendationService.getSocialRecommendations(10);
      setSocialRecs(response.data || []);
    } catch (error) {
      console.error('Erreur recommandations sociales:', error);
      setSocialRecs([]);
    }
  };

  const loadUserProfile = async () => {
    try {
      const response = await advancedRecommendationService.getAdvancedUserProfile();
      setUserProfile(response.data);
    } catch (error) {
      console.error('Erreur profil utilisateur:', error);
      setUserProfile(null);
    }
  };

  const loadMLStats = async () => {
    try {
      const response = await advancedRecommendationService.getMLStats();
      setMLStats(response.data);
    } catch (error) {
      console.error('Erreur stats ML:', error);
      setMLStats(null);
    }
  };

  const handleAddRecommendation = async (recommendation) => {
    try {
      const bookData = {
        title: recommendation.base_recommendation.title,
        author: recommendation.base_recommendation.author,
        category: recommendation.base_recommendation.category,
        cover_url: recommendation.base_recommendation.cover_url,
        status: 'to_read',
        source: 'advanced_recommendation'
      };

      await onAddBook(bookData);

      // Envoyer feedback automatique
      await advancedRecommendationService.submitAdvancedFeedback(
        recommendation.base_recommendation.book_id,
        'added_to_library',
        { context_score: recommendation.context_score }
      );

      // Recharger les recommandations
      await loadAdvancedRecommendations();
    } catch (error) {
      console.error('Erreur lors de l\'ajout:', error);
    }
  };

  const handleFeedback = async (recommendation, feedbackType) => {
    try {
      await advancedRecommendationService.submitAdvancedFeedback(
        recommendation.base_recommendation.book_id,
        feedbackType,
        { context_score: recommendation.context_score }
      );

      // Recharger après feedback
      if (activeTab === 'contextual') {
        await loadContextualRecommendations();
      } else if (activeTab === 'social') {
        await loadSocialRecommendations();
      }
    } catch (error) {
      console.error('Erreur lors du feedback:', error);
    }
  };

  const handleContextChange = async (newContext) => {
    setContext({ ...context, ...newContext });
    await loadContextualRecommendations({ ...context, ...newContext });
  };

  const trainModel = async (modelType) => {
    setLoading(true);
    try {
      await advancedRecommendationService.trainModel(modelType);
      await loadMLStats();
      alert(`Modèle ${modelType} entraîné avec succès !`);
    } catch (error) {
      console.error('Erreur entraînement modèle:', error);
      alert('Erreur lors de l\'entraînement du modèle');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-lg w-full max-w-6xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              🤖 Recommandations IA
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Recommandations intelligentes avec Machine Learning
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Contexte intelligent */}
        {context && (
          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border-b border-gray-200 dark:border-gray-700">
            <div className="flex flex-wrap gap-4 text-sm">
              <span className="flex items-center gap-2">
                🕒 <strong>Moment:</strong> {context.time_of_day}
              </span>
              <span className="flex items-center gap-2">
                😊 <strong>Humeur:</strong> {context.mood}
              </span>
              <span className="flex items-center gap-2">
                ⏱️ <strong>Temps:</strong> {context.available_time}min
              </span>
              <span className="flex items-center gap-2">
                🎯 <strong>Objectif:</strong> {context.purpose}
              </span>
            </div>
          </div>
        )}

        {/* Navigation onglets */}
        <div className="flex border-b border-gray-200 dark:border-gray-700">
          {[
            { id: 'contextual', label: '🎯 Contextuelles', count: contextualRecs.length },
            { id: 'social', label: '👥 Sociales', count: socialRecs.length },
            { id: 'profile', label: '📊 Profil IA', count: null },
            { id: 'ml', label: '🔬 Modèles ML', count: null }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-6 py-3 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-b-2 border-green-500 text-green-600 dark:text-green-400'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
              }`}
            >
              {tab.label}
              {tab.count !== null && (
                <span className="ml-2 px-2 py-1 bg-gray-200 dark:bg-gray-700 rounded-full text-xs">
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Contenu */}
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500"></div>
              <span className="ml-4 text-gray-600 dark:text-gray-400">
                Calcul des recommandations IA...
              </span>
            </div>
          ) : (
            <>
              {/* Onglet Recommandations Contextuelles */}
              {activeTab === 'contextual' && (
                <div>
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold mb-4">Recommandations Contextuelles</h3>
                    {contextualRecs.length === 0 ? (
                      <p className="text-gray-600 dark:text-gray-400">
                        Aucune recommandation contextuelle disponible
                      </p>
                    ) : (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {contextualRecs.map((rec, index) => (
                          <div key={index} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                            <div className="flex gap-4">
                              {rec.base_recommendation.cover_url && (
                                <img
                                  src={rec.base_recommendation.cover_url}
                                  alt={rec.base_recommendation.title}
                                  className="w-16 h-24 object-cover rounded"
                                />
                              )}
                              <div className="flex-1">
                                <h4 className="font-semibold text-gray-900 dark:text-white">
                                  {rec.base_recommendation.title}
                                </h4>
                                <p className="text-gray-600 dark:text-gray-400">
                                  {rec.base_recommendation.author}
                                </p>
                                <div className="mt-2">
                                  <span className="text-xs bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 px-2 py-1 rounded">
                                    Score: {(rec.context_score * 100).toFixed(0)}%
                                  </span>
                                </div>
                                <div className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                                  {rec.context_reasons.slice(0, 2).map((reason, i) => (
                                    <div key={i}>• {reason}</div>
                                  ))}
                                </div>
                              </div>
                            </div>
                            <div className="mt-4 flex gap-2">
                              <button
                                onClick={() => handleAddRecommendation(rec)}
                                className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 text-sm"
                              >
                                Ajouter
                              </button>
                              <button
                                onClick={() => handleFeedback(rec, 'like')}
                                className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
                              >
                                👍
                              </button>
                              <button
                                onClick={() => handleFeedback(rec, 'not_interested')}
                                className="px-3 py-1 bg-gray-500 text-white rounded hover:bg-gray-600 text-sm"
                              >
                                ❌
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Onglet Recommandations Sociales */}
              {activeTab === 'social' && (
                <div>
                  <h3 className="text-lg font-semibold mb-4">Recommandations Sociales IA</h3>
                  {socialRecs.length === 0 ? (
                    <p className="text-gray-600 dark:text-gray-400">
                      Aucune recommandation sociale disponible
                    </p>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {socialRecs.map((rec, index) => (
                        <div key={index} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                          <div className="flex gap-4">
                            {rec.base_recommendation.cover_url && (
                              <img
                                src={rec.base_recommendation.cover_url}
                                alt={rec.base_recommendation.title}
                                className="w-16 h-24 object-cover rounded"
                              />
                            )}
                            <div className="flex-1">
                              <h4 className="font-semibold text-gray-900 dark:text-white">
                                {rec.base_recommendation.title}
                              </h4>
                              <p className="text-gray-600 dark:text-gray-400">
                                {rec.base_recommendation.author}
                              </p>
                              {rec.social_proof && (
                                <div className="mt-2">
                                  <span className="text-xs bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200 px-2 py-1 rounded">
                                    {rec.social_proof.recommendation_count} recommandations
                                  </span>
                                  <span className="text-xs bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200 px-2 py-1 rounded ml-2">
                                    ⭐ {rec.social_proof.average_rating?.toFixed(1)}
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                          <div className="mt-4 flex gap-2">
                            <button
                              onClick={() => handleAddRecommendation(rec)}
                              className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 text-sm"
                            >
                              Ajouter
                            </button>
                            <button
                              onClick={() => handleFeedback(rec, 'like')}
                              className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
                            >
                              👍
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Onglet Profil IA */}
              {activeTab === 'profile' && (
                <div>
                  <h3 className="text-lg font-semibold mb-4">Profil Utilisateur IA</h3>
                  {userProfile ? (
                    <div className="space-y-6">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
                          <h4 className="font-semibold text-blue-900 dark:text-blue-200">Vitesse de lecture</h4>
                          <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                            {userProfile.reading_velocity} livres/mois
                          </p>
                        </div>
                        <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
                          <h4 className="font-semibold text-green-900 dark:text-green-200">Exploration</h4>
                          <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                            {(userProfile.behavioral_insights.exploration_tendency * 100).toFixed(0)}%
                          </p>
                        </div>
                        <div className="bg-purple-50 dark:bg-purple-900/20 p-4 rounded-lg">
                          <h4 className="font-semibold text-purple-900 dark:text-purple-200">Influence sociale</h4>
                          <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                            {(userProfile.behavioral_insights.social_influence * 100).toFixed(0)}%
                          </p>
                        </div>
                      </div>

                      <div>
                        <h4 className="font-semibold mb-2">Clusters comportementaux</h4>
                        <div className="flex flex-wrap gap-2">
                          {userProfile.behavioral_insights.behavioral_clusters.map((cluster, index) => (
                            <span key={index} className="px-3 py-1 bg-gray-200 dark:bg-gray-700 rounded-full text-sm">
                              {cluster}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div>
                        <h4 className="font-semibold mb-2">Préférences de genres</h4>
                        <div className="space-y-2">
                          {Object.entries(userProfile.genre_preferences || {}).map(([genre, score]) => (
                            <div key={genre} className="flex items-center gap-4">
                              <span className="w-20 text-sm">{genre}</span>
                              <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                                <div
                                  className="bg-green-500 h-2 rounded-full"
                                  style={{ width: `${score * 100}%` }}
                                ></div>
                              </div>
                              <span className="text-sm">{(score * 100).toFixed(0)}%</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <p className="text-gray-600 dark:text-gray-400">
                      Profil IA non disponible
                    </p>
                  )}
                </div>
              )}

              {/* Onglet Modèles ML */}
              {activeTab === 'ml' && (
                <div>
                  <h3 className="text-lg font-semibold mb-4">Modèles Machine Learning</h3>
                  {mlStats ? (
                    <div className="space-y-6">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {Object.entries(mlStats.models_status || {}).map(([model, status]) => (
                          <div key={model} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                            <h4 className="font-semibold">{model.replace('_', ' ')}</h4>
                            <div className="mt-2 space-y-2">
                              <span className={`inline-block px-2 py-1 rounded text-xs ${
                                status.loaded ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                              }`}>
                                {status.loaded ? 'Chargé' : 'Non chargé'}
                              </span>
                              {status.needs_retrain && (
                                <div>
                                  <button
                                    onClick={() => trainModel(model)}
                                    disabled={loading}
                                    className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
                                  >
                                    Entraîner
                                  </button>
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <p className="text-gray-600 dark:text-gray-400">
                      Statistiques ML non disponibles
                    </p>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdvancedRecommendationsModal;