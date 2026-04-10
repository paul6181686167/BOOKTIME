import React, { useState } from 'react';
import { 
  CheckCircleIcon, 
  CircleStackIcon,
  PencilIcon,
  TrashIcon
} from '@heroicons/react/24/outline';

const SeriesLibraryCard = ({ series, onUpdateVolume, onUpdateStatus, onDelete }) => {
  const [expandedVolumes, setExpandedVolumes] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);

  const handleVolumeToggle = async (volumeNumber, isRead) => {
    setIsUpdating(true);
    try {
      await onUpdateVolume(series.id, volumeNumber, isRead);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleStatusChange = async (newStatus) => {
    await onUpdateStatus(series.id, newStatus);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100';
      case 'reading': return 'text-blue-600 bg-blue-100';
      case 'to_read': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'completed': return 'Terminé';
      case 'reading': return 'En cours';
      case 'to_read': return 'À lire';
      default: return 'À lire';
    }
  };

  const getCategoryEmoji = (category) => {
    switch (category) {
      case 'roman': return '📚';
      case 'bd': return '🗨️';
      case 'manga': return '🎎';
      default: return '📖';
    }
  };

  const readVolumes = series.volumes.filter(v => v.is_read).length;
  const totalVolumes = series.volumes.length;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
      {/* Header avec image et info principale */}
      <div className="flex items-start space-x-4 mb-4">
        {/* Image de la série */}
        <div className="flex-shrink-0">
          {series.cover_image_url ? (
            <img 
              src={series.cover_image_url}
              alt={series.series_name}
              className="w-16 h-20 object-cover rounded-lg shadow-sm"
            />
          ) : (
            <div className="w-16 h-20 bg-gradient-to-br from-emerald-100 to-emerald-200 dark:from-emerald-800 dark:to-emerald-900 rounded-lg flex items-center justify-center">
              <CircleStackIcon className="w-8 h-8 text-emerald-600 dark:text-emerald-300" />
            </div>
          )}
        </div>

        {/* Informations principales */}
        <div className="flex-1 min-w-0">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white truncate mb-1">
            {getCategoryEmoji(series.category)} {series.series_name}
          </h3>
          
          <p className="text-sm text-gray-600 dark:text-gray-300 mb-1">
            ✨ Série • {totalVolumes} tome{totalVolumes > 1 ? 's' : ''} • {series.authors.join(', ')}
          </p>

          {/* Progression */}
          <div className="flex items-center space-x-2 mb-2">
            <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div 
                className="bg-emerald-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${series.completion_percentage}%` }}
              />
            </div>
            <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
              📊 {readVolumes}/{totalVolumes} ({series.completion_percentage}%)
            </span>
          </div>

          {/* Statut avec dropdown */}
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600 dark:text-gray-400">📖 Statut:</span>
            <select
              value={series.series_status}
              onChange={(e) => handleStatusChange(e.target.value)}
              className={`text-sm px-3 py-1 rounded-full font-medium border-0 cursor-pointer ${getStatusColor(series.series_status)}`}
            >
              <option value="to_read">À lire</option>
              <option value="reading">En cours</option>
              <option value="completed">Terminé</option>
            </select>
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col space-y-2">
          <button
            onClick={() => setExpandedVolumes(!expandedVolumes)}
            className="p-2 text-gray-500 hover:text-emerald-600 dark:text-gray-400 dark:hover:text-emerald-400 transition-colors"
            title="Voir/masquer les tomes"
          >
            <PencilIcon className="w-5 h-5" />
          </button>
          <button
            onClick={() => onDelete(series.id)}
            className="p-2 text-gray-500 hover:text-red-600 dark:text-gray-400 dark:hover:text-red-400 transition-colors"
            title="Supprimer de la bibliothèque"
          >
            <TrashIcon className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Description */}
      {series.description_fr && (
        <div className="mb-4">
          <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
            {series.description_fr}
          </p>
        </div>
      )}

      {/* Liste des tomes (expandable) */}
      {expandedVolumes && (
        <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
          <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-3">
            TOMES ({readVolumes}/{totalVolumes}):
          </h4>
          
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {series.volumes.map((volume) => (
              <div 
                key={volume.volume_number}
                className="flex items-center space-x-3 p-2 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <button
                  onClick={() => handleVolumeToggle(volume.volume_number, !volume.is_read)}
                  disabled={isUpdating}
                  className={`flex-shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center transition-all ${
                    volume.is_read 
                      ? 'bg-emerald-500 border-emerald-500 text-white' 
                      : 'border-gray-300 dark:border-gray-600 hover:border-emerald-500'
                  } ${isUpdating ? 'opacity-50' : ''}`}
                >
                  {volume.is_read && <CheckCircleIcon className="w-3 h-3" />}
                </button>
                
                <span className="flex-1 text-sm text-gray-700 dark:text-gray-300">
                  <span className="font-medium">{volume.volume_number}.</span> {volume.volume_title}
                </span>
                
                {volume.is_read && volume.date_read && (
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    Lu le {new Date(volume.date_read).toLocaleDateString('fr-FR')}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Métadonnées en bas */}
      <div className="flex justify-between items-center mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400">
        <span>
          Ajouté le {new Date(series.date_added).toLocaleDateString('fr-FR')}
        </span>
        {series.first_published && (
          <span>
            {series.first_published}{series.last_published && series.last_published !== series.first_published ? ` - ${series.last_published}` : ''}
          </span>
        )}
      </div>
    </div>
  );
};

export default SeriesLibraryCard;
