import React from 'react';
import { 
  BookOpenIcon, 
  UserIcon,
  ClockIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';

const SeriesCard = ({ 
  series, 
  onClick, 
  isOwned = false, 
  showProgress = false,
  progressInfo = null,
  showAddButton = true, // Nouveau : contrôle l'affichage du bouton d'ajout
  onAddToLibrary = null, // Nouveau : callback pour ajout
  onUpdateVolume = null, // Nouveau : pour séries bibliothèque
  onUpdateStatus = null, // Nouveau : pour séries bibliothèque  
  onDelete = null, // Nouveau : pour séries bibliothèque
  context = "search" // Nouveau : "search" ou "library"
}) => {
  const getCategoryBadge = (category) => {
    switch (category) {
      case 'roman':
        return { text: 'Roman', class: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300', emoji: '📚' };
      case 'bd':
        return { text: 'BD', class: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300', emoji: '🎨' };
      case 'manga':
        return { text: 'Manga', class: 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-300', emoji: '🇯🇵' };
      default:
        return { text: 'Livre', class: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300', emoji: '📖' };
    }
  };

  const categoryBadge = getCategoryBadge(series.category);

  return (
    <div
      onClick={onClick}
      className="cursor-pointer bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 border-2 border-indigo-200 dark:border-indigo-800 rounded-xl p-4 hover:shadow-lg transition-all duration-200 hover:scale-105 group relative"
    >
      {/* Badge de série */}
      <div className="absolute top-3 left-3 z-10">
        <div className="bg-indigo-600 text-white text-xs px-2 py-1 rounded-full flex items-center font-medium">
          <span className="mr-1">📚</span>
          SÉRIE
        </div>
      </div>

      {/* Badge de catégorie */}
      <div className="absolute top-3 right-3 z-10">
        <div className={`${categoryBadge.class} text-xs px-2 py-1 rounded-full flex items-center font-medium`}>
          <span className="mr-1">{categoryBadge.emoji}</span>
          {categoryBadge.text}
        </div>
      </div>

      {/* Badge de propriété */}
      {isOwned && (
        <div className="absolute top-12 right-3 z-10">
          <div className="bg-green-500 text-white text-xs px-2 py-1 rounded-full flex items-center">
            <CheckCircleIcon className="w-3 h-3 mr-1" />
            Possédée
          </div>
        </div>
      )}

      {/* Contenu principal */}
      <div className="pt-8">
        <div className="flex items-start space-x-4">
          {/* Icône de série */}
          <div className="w-16 h-20 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center text-white text-2xl flex-shrink-0 shadow-md">
            {categoryBadge.emoji}
          </div>

          {/* Informations */}
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-1 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
              {series.name}
            </h3>
            
            <div className="flex items-center text-sm text-gray-600 dark:text-gray-400 mb-2">
              <UserIcon className="w-4 h-4 mr-1" />
              <span>{series.author}</span>
            </div>

            {series.description && (
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                {series.description}
              </p>
            )}

            {/* Métadonnées de la série */}
            <div className="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-500">
              <span className="flex items-center">
                <BookOpenIcon className="w-3 h-3 mr-1" />
                {series.volumes || series.total_books || '?'} tomes
              </span>
              
              {series.first_published && (
                <span className="flex items-center">
                  <ClockIcon className="w-3 h-3 mr-1" />
                  Depuis {series.first_published}
                </span>
              )}

              {series.status && (
                <span className={`px-2 py-1 rounded ${
                  series.status === 'completed' 
                    ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' 
                    : 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300'
                }`}>
                  {series.status === 'completed' ? 'Terminée' : 'En cours'}
                </span>
              )}
            </div>

            {/* Indicateur de progression pour les séries possédées */}
            {showProgress && progressInfo && (
              <div className="mt-3 pt-3 border-t border-indigo-200 dark:border-indigo-800">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600 dark:text-gray-400">Progression</span>
                  <span className="font-medium text-indigo-600 dark:text-indigo-400">
                    {progressInfo.completed}/{progressInfo.total} tomes lus
                  </span>
                </div>
                <div className="mt-1 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div 
                    className="bg-gradient-to-r from-indigo-500 to-purple-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${(progressInfo.completed / progressInfo.total) * 100}%` }}
                  ></div>
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-500 mt-1">
                  {Math.round((progressInfo.completed / progressInfo.total) * 100)}% complété
                </div>
              </div>
            )}

            {/* Actions de bibliothèque - uniquement si en mode bibliothèque */}
            {context === "library" && onUpdateVolume && (
              <div className="mt-3 pt-3 border-t border-indigo-200 dark:border-indigo-800">
                <div className="flex items-center justify-between text-sm mb-2">
                  <span className="text-gray-600 dark:text-gray-400">Actions</span>
                  <div className="flex space-x-2">
                    {onUpdateStatus && (
                      <select
                        value={series.series_status || 'to_read'}
                        onChange={(e) => onUpdateStatus(series.id, e.target.value)}
                        className="text-xs border border-gray-300 dark:border-gray-600 rounded px-2 py-1 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        onClick={(e) => e.stopPropagation()}
                      >
                        <option value="to_read">À lire</option>
                        <option value="reading">En cours</option>
                        <option value="completed">Terminé</option>
                      </select>
                    )}
                    {onDelete && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onDelete(series.id);
                        }}
                        className="text-xs text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 px-2 py-1 border border-red-300 dark:border-red-600 rounded hover:bg-red-50 dark:hover:bg-red-900/20"
                      >
                        Supprimer
                      </button>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Bouton d'ajout à la bibliothèque - uniquement si showAddButton=true */}
        {showAddButton && !isOwned && onAddToLibrary && (
          <div className="mt-4 pt-3 border-t border-indigo-200 dark:border-indigo-800">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onAddToLibrary(series);
              }}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors text-sm flex items-center justify-center space-x-2"
            >
              <span>➕</span>
              <span>Ajouter toute la série à ma bibliothèque</span>
            </button>
          </div>
        )}

      </div>
    </div>
  );
};

export default SeriesCard;
