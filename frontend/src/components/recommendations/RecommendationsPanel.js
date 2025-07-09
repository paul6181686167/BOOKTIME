import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';

/**
 * PHASE 3.1 - SYSTÈME DE RECOMMANDATIONS
 * Composant panneau des recommandations personnalisées
 * Affiche les suggestions basées sur l'analyse du profil utilisateur
 */

const RecommendationsPanel = ({ isOpen, onClose, onAddBook }) => {
  const [recommendations, setRecommendations] = useState([]);
  const [userProfile, setUserProfile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState('all');

  // Catégories disponibles
  const categories = [
    { key: 'all', label: 'Toutes' },
    { key: 'roman', label: 'Romans' },
    { key: 'bd', label: 'BD' },
    { key: 'manga', label: 'Mangas' }
  ];

  // Chargement des recommandations
  const loadRecommendations = async (category = null) => {
    setLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('token');
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      let url = `${backendUrl}/api/recommendations/?limit=20`;
      if (category && category !== 'all') {
        url += `&category=${category}`;
      }
      
      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (!response.ok) {
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setRecommendations(data.recommendations || []);
      setUserProfile(data.user_profile || null);
      
    } catch (err) {
      console.error('Erreur lors du chargement des recommandations:', err);
      setError(err.message);
      toast.error('Erreur lors du chargement des recommandations');
    } finally {
      setLoading(false);
    }
  };

  // Chargement initial
  useEffect(() => {
    if (isOpen) {
      loadRecommendations(selectedCategory);
    }
  }, [isOpen, selectedCategory]);

  // Gestion du changement de catégorie
  const handleCategoryChange = (category) => {
    setSelectedCategory(category);
  };

  // Ajout d'un livre recommandé
  const handleAddRecommendedBook = async (recommendation) => {
    try {
      const bookData = {
        title: recommendation.title,
        author: recommendation.author,
        category: recommendation.category,
        cover_url: recommendation.cover_url,
        description: recommendation.description || '',
        publication_year: recommendation.publication_year,
        publisher: recommendation.publisher || '',
        ol_key: recommendation.ol_key
      };
      
      await onAddBook(bookData);
      toast.success(`"${recommendation.title}" ajouté à votre bibliothèque !`);
      
      // Recharger les recommandations pour enlever le livre ajouté
      loadRecommendations(selectedCategory);
      
    } catch (error) {
      console.error('Erreur lors de l\'ajout du livre:', error);
      toast.error('Erreur lors de l\'ajout du livre');
    }
  };

  // Fonction pour obtenir la couleur du badge de confiance
  const getConfidenceBadgeColor = (score) => {
    if (score >= 0.8) return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';
    if (score >= 0.6) return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300';
    return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
  };

  // Fonction pour obtenir le label de confiance
  const getConfidenceLabel = (score) => {
    if (score >= 0.8) return 'Très pertinent';
    if (score >= 0.6) return 'Pertinent';
    return 'Peut-être';
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-11/12 max-w-6xl shadow-lg rounded-md bg-white dark:bg-gray-800">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center">
              <span className="mr-2">🎯</span>
              Recommandations personnalisées
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Découvrez de nouveaux livres basés sur vos préférences
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Filtres par catégorie */}
        <div className="flex space-x-2 mb-6">
          {categories.map((category) => (
            <button
              key={category.key}
              onClick={() => handleCategoryChange(category.key)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedCategory === category.key
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-200 hover:bg-gray-300 text-gray-700 dark:bg-gray-700 dark:hover:bg-gray-600 dark:text-gray-300'
              }`}
            >
              {category.label}
            </button>
          ))}
        </div>

        {/* Profil utilisateur (si disponible) */}
        {userProfile && userProfile.total_books > 0 && (
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 mb-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Votre profil de lecture
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Livres total</p>
                <p className="text-xl font-bold text-green-600">{userProfile.total_books}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Auteur préféré</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">
                  {userProfile.favorite_authors?.[0]?.name || 'Aucun'}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Catégorie préférée</p>
                <p className="text-lg font-semibold text-gray-900 dark:text-white">
                  {userProfile.favorite_categories?.[0]?.name || 'Aucune'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* États de chargement et erreur */}
        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-500"></div>
            <span className="ml-3 text-gray-600 dark:text-gray-400">Génération des recommandations...</span>
          </div>
        )}

        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 mb-6">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
                  Erreur lors du chargement
                </h3>
                <p className="text-sm text-red-700 dark:text-red-300 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Grille des recommandations */}
        {!loading && !error && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {recommendations.map((recommendation, index) => (
              <div
                key={`${recommendation.ol_key}-${index}`}
                className="bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-lg transition-shadow"
              >
                {/* Image de couverture */}
                <div className="aspect-w-3 aspect-h-4 bg-gray-200 dark:bg-gray-700">
                  {recommendation.cover_url ? (
                    <img
                      src={recommendation.cover_url}
                      alt={recommendation.title}
                      className="w-full h-48 object-cover"
                      onError={(e) => {
                        e.target.style.display = 'none';
                      }}
                    />
                  ) : (
                    <div className="w-full h-48 flex items-center justify-center bg-gray-300 dark:bg-gray-600">
                      <span className="text-4xl">📚</span>
                    </div>
                  )}
                </div>

                {/* Contenu */}
                <div className="p-4">
                  {/* Titre et auteur */}
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1 line-clamp-2">
                    {recommendation.title}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                    {recommendation.author}
                  </p>

                  {/* Badges */}
                  <div className="flex flex-wrap gap-2 mb-3">
                    {/* Badge catégorie */}
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      recommendation.category === 'roman' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300' :
                      recommendation.category === 'bd' ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300' :
                      'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-300'
                    }`}>
                      {recommendation.category.toUpperCase()}
                    </span>

                    {/* Badge confiance */}
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getConfidenceBadgeColor(recommendation.confidence_score)}`}>
                      {getConfidenceLabel(recommendation.confidence_score)}
                    </span>
                  </div>

                  {/* Raison de la recommandation */}
                  <p className="text-sm text-gray-700 dark:text-gray-300 mb-4 line-clamp-2">
                    {recommendation.reason}
                  </p>

                  {/* Informations supplémentaires */}
                  {(recommendation.publication_year || recommendation.publisher) && (
                    <div className="text-xs text-gray-500 dark:text-gray-400 mb-4">
                      {recommendation.publication_year && (
                        <span>Publié en {recommendation.publication_year}</span>
                      )}
                      {recommendation.publication_year && recommendation.publisher && (
                        <span> • </span>
                      )}
                      {recommendation.publisher && (
                        <span>{recommendation.publisher}</span>
                      )}
                    </div>
                  )}

                  {/* Bouton d'ajout */}
                  <button
                    onClick={() => handleAddRecommendedBook(recommendation)}
                    className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors flex items-center justify-center"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Ajouter à ma bibliothèque
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Message si pas de recommandations */}
        {!loading && !error && recommendations.length === 0 && (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🤔</div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              Aucune recommandation trouvée
            </h3>
            <p className="text-gray-600 dark:text-gray-400">
              Ajoutez plus de livres à votre bibliothèque pour obtenir des recommandations personnalisées !
            </p>
          </div>
        )}

        {/* Footer */}
        <div className="mt-8 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Recommandations générées par intelligence artificielle
            </p>
            <button
              onClick={() => loadRecommendations(selectedCategory)}
              className="text-green-600 hover:text-green-700 dark:text-green-400 dark:hover:text-green-300 font-medium text-sm"
            >
              🔄 Actualiser
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RecommendationsPanel;