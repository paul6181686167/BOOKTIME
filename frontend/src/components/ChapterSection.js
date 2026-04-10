/**
 * Composant ChapterSection - Section chapitres pour modals série
 * =============================================================
 * 
 * Fonctionnalités :
 * - Affichage chapitres récents et à venir
 * - Regroupement par volumes
 * - Prédictions de sorties
 * - Actualisation temps réel
 * - Interface utilisateur intuitive
 */

import React, { useState } from 'react';
import { useSeriesChapters } from '../hooks/useSeriesChapters';

// Icônes (Heroicons ou équivalent)
const RefreshIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
          d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
  </svg>
);

const ChapterIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
          d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
  </svg>
);

const VolumeIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
          d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
  </svg>
);

const CalendarIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
          d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
  </svg>
);

const ChapterSection = ({ seriesName, onClose }) => {
  const [showAllChapters, setShowAllChapters] = useState(false);
  const [showAllVolumes, setShowAllVolumes] = useState(false);
  
  const {
    chaptersData,
    loading,
    error,
    lastUpdated,
    refreshChapters,
    hasChapters,
    hasVolumes,
    hasPredictions,
    totalChapters,
    latestChapter,
    nextPrediction,
  } = useSeriesChapters(seriesName);

  // Formatage des dates
  const formatDate = (dateString) => {
    if (!dateString) return 'Date inconnue';
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('fr-FR', {
        day: 'numeric',
        month: 'short',
        year: date.getFullYear() !== new Date().getFullYear() ? 'numeric' : undefined
      });
    } catch (e) {
      return 'Date invalide';
    }
  };

  // Formatage confiance
  const formatConfidence = (confidence) => {
    if (!confidence || confidence === 0) return '';
    const percent = Math.round(confidence * 100);
    if (percent >= 80) return '🟢';
    if (percent >= 60) return '🟡';
    return '🔴';
  };

  // Rendu des chapitres
  const renderChapters = () => {
    if (!hasChapters) return null;

    const chapters = chaptersData.current_chapters || [];
    const displayChapters = showAllChapters ? chapters : chapters.slice(-8); // 8 derniers

    // Séparer les chapitres assignés aux tomes et les chapitres orphelins
    const orphanChapters = chapters.filter(ch => ch.volume_number === null || ch.volume_number === undefined);

    return (
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-md font-semibold text-gray-900 dark:text-white flex items-center">
            <ChapterIcon />
            <span className="ml-2">Chapitres Récents</span>
            {totalChapters > 0 && (
              <span className="ml-2 text-sm text-gray-500">({totalChapters} total)</span>
            )}
          </h4>
          
          {chapters.length > 8 && (
            <button
              onClick={() => setShowAllChapters(!showAllChapters)}
              className="text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400"
            >
              {showAllChapters ? 'Voir moins' : `Voir tous (${chapters.length})`}
            </button>
          )}
        </div>

        {/* Section chapitres sans tome assigné (orphelins) */}
        {orphanChapters.length > 0 && (
          <div className="mb-4">
            <h5 className="text-sm font-medium text-orange-800 dark:text-orange-300 mb-2 flex items-center">
              <span className="w-2 h-2 bg-orange-500 rounded-full mr-2"></span>
              Chapitres sans tome assigné ({orphanChapters.length})
            </h5>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
              {orphanChapters.slice(-10).map((chapter, index) => (
                <div
                  key={`orphan-${chapter.chapter_number}-${index}`}
                  className="p-2 rounded-lg border text-xs bg-orange-50 border-orange-200 text-orange-800 dark:bg-orange-900/20 dark:border-orange-700 dark:text-orange-300"
                >
                  <div className="font-semibold">Ch. {chapter.chapter_number}</div>
                  {chapter.title && (
                    <div className="text-xs opacity-75 truncate">{chapter.title}</div>
                  )}
                  <div className="text-xs opacity-60 mt-1">
                    {formatDate(chapter.release_date)}
                  </div>
                  <div className="text-xs text-orange-600 dark:text-orange-400 mt-1">
                    Non collecté
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Section chapitres principaux */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
          {displayChapters.map((chapter, index) => (
            <div
              key={`${chapter.chapter_number}-${index}`}
              className={`
                p-2 rounded-lg border text-xs
                ${chapter.status === 'released' 
                  ? 'bg-green-50 border-green-200 text-green-800 dark:bg-green-900/20 dark:border-green-700 dark:text-green-300'
                  : chapter.status === 'upcoming'
                  ? 'bg-blue-50 border-blue-200 text-blue-800 dark:bg-blue-900/20 dark:border-blue-700 dark:text-blue-300'
                  : 'bg-yellow-50 border-yellow-200 text-yellow-800 dark:bg-yellow-900/20 dark:border-yellow-700 dark:text-yellow-300'
                }
              `}
            >
              <div className="font-semibold">Ch. {chapter.chapter_number}</div>
              {chapter.title && (
                <div className="text-xs opacity-75 truncate">{chapter.title}</div>
              )}
              <div className="text-xs opacity-60 mt-1">
                {formatDate(chapter.release_date)}
              </div>
              {chapter.volume_number && (
                <div className="text-xs text-gray-500 mt-1">
                  Vol. {chapter.volume_number}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Rendu des volumes
  const renderVolumes = () => {
    if (!hasVolumes) return null;

    const volumes = chaptersData.volumes || [];
    const displayVolumes = showAllVolumes ? volumes : volumes.slice(-4); // 4 derniers

    return (
      <div className="mb-6">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-md font-semibold text-gray-900 dark:text-white flex items-center">
            <VolumeIcon />
            <span className="ml-2">Volumes/Tomes</span>
          </h4>
          
          {volumes.length > 4 && (
            <button
              onClick={() => setShowAllVolumes(!showAllVolumes)}
              className="text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400"
            >
              {showAllVolumes ? 'Voir moins' : `Voir tous (${volumes.length})`}
            </button>
          )}
        </div>

        <div className="space-y-2">
          {displayVolumes.map((volume, index) => (
            <div
              key={`${volume.volume_number}-${index}`}
              className="p-3 rounded-lg border bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <span className="font-semibold text-gray-900 dark:text-white">
                    Volume {volume.volume_number}
                  </span>
                  {volume.chapters_range && (
                    <span className="ml-2 text-xs text-gray-500">
                      Ch. {volume.chapters_range}
                    </span>
                  )}
                </div>
                
                <div className="text-xs text-gray-500">
                  {formatDate(volume.release_date)}
                </div>
              </div>
              
              {volume.chapters_included && volume.chapters_included.length > 0 && (
                <div className="mt-1 text-xs text-gray-600 dark:text-gray-300">
                  {volume.chapters_included.length} chapitres inclus
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Rendu des prédictions
  const renderPredictions = () => {
    if (!hasPredictions) return null;

    const predictions = chaptersData.predictions || {};

    return (
      <div className="mb-4">
        <h4 className="text-md font-semibold text-gray-900 dark:text-white flex items-center mb-3">
          <CalendarIcon />
          <span className="ml-2">Prédictions Sorties</span>
        </h4>

        <div className="space-y-2">
          {predictions.next_chapter && (
            <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700">
              <div className="flex items-center justify-between">
                <div className="text-sm font-medium text-blue-900 dark:text-blue-100">
                  Prochain Chapitre {predictions.next_chapter.estimated_number}
                </div>
                <div className="text-xs text-blue-600 dark:text-blue-300">
                  {formatConfidence(predictions.next_chapter.confidence)}
                </div>
              </div>
              <div className="text-xs text-blue-700 dark:text-blue-200 mt-1">
                Prévu le {formatDate(predictions.next_chapter.estimated_date)}
              </div>
            </div>
          )}

          {predictions.next_volume && (
            <div className="p-3 rounded-lg bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-700">
              <div className="flex items-center justify-between">
                <div className="text-sm font-medium text-purple-900 dark:text-purple-100">
                  Prochain Volume {predictions.next_volume.estimated_number}
                </div>
                <div className="text-xs text-purple-600 dark:text-purple-300">
                  {formatConfidence(predictions.next_volume.confidence)}
                </div>
              </div>
              <div className="text-xs text-purple-700 dark:text-purple-200 mt-1">
                Prévu le {formatDate(predictions.next_volume.estimated_date)}
              </div>
              {predictions.next_volume.estimated_chapters_range && (
                <div className="text-xs text-purple-600 dark:text-purple-300 mt-1">
                  Chapitres {predictions.next_volume.estimated_chapters_range}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    );
  };

  // Rendu principal
  if (!seriesName) return null;

  return (
    <div className="mt-6 border-t pt-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          📚 Chapitres et Prédictions
        </h3>
        
        <div className="flex items-center space-x-2">
          {lastUpdated && (
            <span className="text-xs text-gray-500">
              Mis à jour {lastUpdated.toLocaleTimeString()}
            </span>
          )}
          
          <button
            onClick={refreshChapters}
            disabled={loading}
            className={`
              p-2 rounded-lg border transition-colors
              ${loading 
                ? 'bg-gray-100 border-gray-300 text-gray-400 cursor-not-allowed'
                : 'bg-white hover:bg-gray-50 border-gray-300 text-gray-700 hover:text-gray-900'
              }
              dark:bg-gray-700 dark:hover:bg-gray-600 dark:border-gray-600 dark:text-gray-300
            `}
            title="Actualiser les données"
          >
            <RefreshIcon />
          </button>
          
          {onClose && (
            <button
              onClick={onClose}
              className="text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              Fermer
            </button>
          )}
        </div>
      </div>

      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="flex items-center text-sm text-gray-500">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600 mr-2"></div>
            Récupération des données chapitres...
          </div>
        </div>
      )}

      {error && (
        <div className="p-4 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 mb-4">
          <div className="text-sm text-red-800 dark:text-red-200">
            <strong>Erreur :</strong> {error}
          </div>
          <button
            onClick={() => refreshChapters()}
            className="mt-2 text-xs text-red-600 hover:text-red-800 dark:text-red-400 underline"
          >
            Réessayer
          </button>
        </div>
      )}

      {chaptersData && !loading && (
        <div>
          {/* Prédictions en premier pour visibilité */}
          {renderPredictions()}
          
          {/* Chapitres récents */}
          {renderChapters()}
          
          {/* Volumes */}
          {renderVolumes()}
          
          {!hasChapters && !hasVolumes && !hasPredictions && (
            <div className="text-center py-8 text-gray-500 dark:text-gray-400">
              <ChapterIcon />
              <div className="mt-2 text-sm">
                Aucune donnée de chapitre disponible pour cette série.
              </div>
              <div className="text-xs mt-1">
                Les données peuvent prendre du temps à être collectées.
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ChapterSection;