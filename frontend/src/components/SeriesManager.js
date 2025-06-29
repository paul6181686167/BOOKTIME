import React, { useState, useEffect } from 'react';
import { XMarkIcon, MagnifyingGlassIcon, BookOpenIcon, PlusIcon, CheckIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';

const SeriesManager = ({ isOpen, onClose, onSeriesComplete }) => {
  const [activeTab, setActiveTab] = useState('discover');
  const [popularSeries, setPopularSeries] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [detectedSeries, setDetectedSeries] = useState([]);
  const [detectLoading, setDetectLoading] = useState(false);

  // Charger les séries populaires
  const loadPopularSeries = async (category = '') => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const params = new URLSearchParams();
      if (category) params.append('category', category);
      params.append('limit', '50');
      
      const response = await fetch(`${backendUrl}/api/series/popular?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setPopularSeries(data.series);
      } else {
        throw new Error('Erreur lors du chargement des séries');
      }
    } catch (error) {
      console.error('Erreur:', error);
      toast.error('Erreur lors du chargement des séries populaires');
    } finally {
      setLoading(false);
    }
  };

  // Détecter une série à partir d'un titre/auteur
  const detectSeries = async () => {
    if (!searchTerm.trim()) {
      toast.error('Veuillez saisir un titre de livre');
      return;
    }

    setDetectLoading(true);
    try {
      const token = localStorage.getItem('token');
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const params = new URLSearchParams();
      params.append('title', searchTerm);
      
      const response = await fetch(`${backendUrl}/api/series/detect?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        setDetectedSeries(data.detected_series);
        if (data.detected_series.length === 0) {
          toast.info('Aucune série détectée pour ce titre');
        }
      } else {
        throw new Error('Erreur lors de la détection');
      }
    } catch (error) {
      console.error('Erreur:', error);
      toast.error('Erreur lors de la détection de série');
    } finally {
      setDetectLoading(false);
    }
  };

  // Auto-compléter une série
  const completeSeries = async (series, targetVolumes) => {
    try {
      const token = localStorage.getItem('token');
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      const response = await fetch(`${backendUrl}/api/series/complete`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          series_name: series.name,
          target_volumes: targetVolumes
        })
      });

      if (response.ok) {
        const data = await response.json();
        toast.success(`${data.created_volumes} tome(s) ajouté(s) à ${series.name}`);
        if (onSeriesComplete) {
          onSeriesComplete(data);
        }
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Erreur lors de l\'auto-complétion');
      }
    } catch (error) {
      console.error('Erreur:', error);
      toast.error('Erreur lors de l\'auto-complétion de la série');
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadPopularSeries(selectedCategory);
    }
  }, [isOpen, selectedCategory]);

  const SeriesCard = ({ series, showCompleteButton = true }) => (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-bold text-lg text-gray-900 dark:text-white">{series.name}</h3>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
          series.category === 'roman' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' :
          series.category === 'manga' ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200' :
          'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
        }`}>
          {series.category === 'roman' ? 'Roman' : series.category === 'manga' ? 'Manga' : 'BD'}
        </span>
      </div>
      
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
        {series.authors?.join(', ')}
      </p>
      
      <p className="text-sm text-gray-500 dark:text-gray-500 mb-3">
        {series.description}
      </p>
      
      <div className="flex justify-between items-center text-xs text-gray-500 dark:text-gray-500 mb-3">
        <span>{series.volumes} volumes</span>
        <span>Depuis {series.first_published}</span>
        <span className={`px-2 py-1 rounded ${
          series.status === 'completed' ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' :
          'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300'
        }`}>
          {series.status === 'completed' ? 'Terminée' : 'En cours'}
        </span>
      </div>
      
      {showCompleteButton && (
        <div className="flex space-x-2">
          <button
            onClick={() => completeSeries(series, Math.min(series.volumes, 10))}
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-sm py-2 px-3 rounded-md transition-colors flex items-center justify-center"
          >
            <PlusIcon className="h-4 w-4 mr-1" />
            Ajouter 10 premiers
          </button>
          <button
            onClick={() => completeSeries(series, series.volumes)}
            className="flex-1 bg-green-600 hover:bg-green-700 text-white text-sm py-2 px-3 rounded-md transition-colors flex items-center justify-center"
          >
            <CheckIcon className="h-4 w-4 mr-1" />
            Série complète
          </button>
        </div>
      )}
    </div>
  );

  const DetectedSeriesCard = ({ detectedSeries }) => (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg border border-blue-200 dark:border-blue-800 p-4">
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-bold text-lg text-blue-900 dark:text-blue-100">{detectedSeries.series.name}</h3>
        <div className="flex items-center space-x-2">
          <span className="bg-blue-600 text-white text-xs px-2 py-1 rounded-full">
            {detectedSeries.confidence}% confiance
          </span>
        </div>
      </div>
      
      <p className="text-sm text-blue-700 dark:text-blue-300 mb-2">
        {detectedSeries.series.authors?.join(', ')}
      </p>
      
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
        Correspondance: {detectedSeries.match_reasons.join(', ')}
      </p>
      
      <SeriesCard series={detectedSeries.series} />
    </div>
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-900 rounded-lg w-full max-w-6xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Gestionnaire de Séries
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Découvrez et gérez vos séries de livres préférées
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setActiveTab('discover')}
            className={`px-6 py-3 text-sm font-medium border-b-2 ${
              activeTab === 'discover'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            Découvrir des Séries
          </button>
          <button
            onClick={() => setActiveTab('detect')}
            className={`px-6 py-3 text-sm font-medium border-b-2 ${
              activeTab === 'detect'
                ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            Détecter une Série
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {activeTab === 'discover' && (
            <div>
              {/* Filtres */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Filtrer par catégorie:
                </label>
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="w-full md:w-64 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                >
                  <option value="">Toutes les catégories</option>
                  <option value="roman">Romans</option>
                  <option value="manga">Mangas</option>
                  <option value="bd">Bandes Dessinées</option>
                </select>
              </div>

              {/* Grille des séries */}
              {loading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {[...Array(6)].map((_, i) => (
                    <div key={i} className="bg-gray-200 dark:bg-gray-700 h-48 rounded-lg animate-pulse"></div>
                  ))}
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {popularSeries.map((series, index) => (
                    <SeriesCard key={index} series={series} />
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === 'detect' && (
            <div>
              {/* Zone de recherche */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Titre du livre à analyser:
                </label>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    placeholder="Ex: Harry Potter et la Pierre Philosophale"
                    className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                    onKeyPress={(e) => e.key === 'Enter' && detectSeries()}
                  />
                  <button
                    onClick={detectSeries}
                    disabled={detectLoading}
                    className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-4 py-2 rounded-md transition-colors flex items-center"
                  >
                    {detectLoading ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    ) : (
                      <MagnifyingGlassIcon className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>

              {/* Résultats de détection */}
              {detectedSeries.length > 0 && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    Séries détectées:
                  </h3>
                  {detectedSeries.map((detected, index) => (
                    <DetectedSeriesCard key={index} detectedSeries={detected} />
                  ))}
                </div>
              )}

              {searchTerm && detectedSeries.length === 0 && !detectLoading && (
                <div className="text-center py-8">
                  <BookOpenIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500 dark:text-gray-400">
                    Aucune série détectée. Essayez avec un titre plus précis ou un auteur.
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SeriesManager;