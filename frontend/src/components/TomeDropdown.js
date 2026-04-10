import React, { useState } from 'react';
import { ChevronDownIcon, ChevronUpIcon, BookOpenIcon, CalendarIcon, DocumentTextIcon } from '@heroicons/react/24/outline';

const TomeDropdown = ({ tomeNumber, tomeTitle, seriesData, isRead, onToggleRead }) => {
  const [isOpen, setIsOpen] = useState(false);

  // Extraire les informations du tome depuis seriesData si disponibles
  const getTomeInfo = () => {
    // Données de base
    const baseInfo = {
      title: tomeTitle,
      number: tomeNumber,
      pages: null,
      published_year: null,
      description: null,
      isbn: null,
      publisher: null
    };

    // Si on a des données enrichies, on les utilise
    if (seriesData) {
      // Chercher des informations spécifiques au tome
      if (seriesData.volume_details && seriesData.volume_details[tomeNumber]) {
        const volumeDetail = seriesData.volume_details[tomeNumber];
        return {
          ...baseInfo,
          pages: volumeDetail.pages,
          published_year: volumeDetail.published_year,
          description: volumeDetail.description,
          isbn: volumeDetail.isbn,
          publisher: volumeDetail.publisher
        };
      }

      // Estimation basée sur les données de la série
      if (seriesData.first_published) {
        const baseYear = parseInt(seriesData.first_published);
        const estimatedYear = baseYear + (tomeNumber - 1);
        baseInfo.published_year = estimatedYear;
      }

      // Pages estimées selon la catégorie
      if (seriesData.category === 'manga') {
        baseInfo.pages = 180 + Math.floor(Math.random() * 40); // 180-220 pages
      } else if (seriesData.category === 'bd') {
        baseInfo.pages = 44 + Math.floor(Math.random() * 20); // 44-64 pages
      } else {
        baseInfo.pages = 250 + Math.floor(Math.random() * 150); // 250-400 pages
      }

      // Description générique
      baseInfo.description = `${tomeNumber}${tomeNumber === 1 ? 'er' : 'e'} tome de la série ${seriesData.name}`;
    }

    return baseInfo;
  };

  // Calculer le temps de lecture estimé
  const getReadingTime = (pages, category) => {
    if (!pages) return null;

    let wordsPerPage, readingSpeed;
    
    if (category === 'manga') {
      // Manga : Lecture plus rapide, beaucoup d'images
      wordsPerPage = 50;
      readingSpeed = 200; // mots par minute
    } else if (category === 'bd') {
      // BD : Lecture rapide, beaucoup d'images
      wordsPerPage = 30;
      readingSpeed = 180; // mots par minute
    } else {
      // Roman : Lecture normale
      wordsPerPage = 250;
      readingSpeed = 250; // mots par minute
    }

    const totalWords = pages * wordsPerPage;
    const readingTimeMinutes = Math.round(totalWords / readingSpeed);
    
    if (readingTimeMinutes < 60) {
      return `~${readingTimeMinutes} min`;
    } else {
      const hours = Math.floor(readingTimeMinutes / 60);
      const minutes = readingTimeMinutes % 60;
      return minutes > 0 ? `~${hours}h${minutes}min` : `~${hours}h`;
    }
  };

  const tomeInfo = getTomeInfo();
  const readingTime = getReadingTime(tomeInfo.pages, seriesData?.category);

  return (
    <div className="border-l-2 border-gray-200 dark:border-gray-600 ml-4">
      <div className="flex items-center justify-between p-2 hover:bg-gray-50 dark:hover:bg-gray-800 rounded">
        <div className="flex items-center space-x-3 flex-1">
          <span className="text-sm font-medium text-purple-600 dark:text-purple-400 min-w-[60px]">
            Tome {tomeNumber}
          </span>
          <span className={`text-sm transition-colors flex-1 ${
            isRead 
              ? 'text-green-700 dark:text-green-300 line-through' 
              : 'text-gray-700 dark:text-gray-300'
          }`}>
            {tomeTitle}
          </span>
        </div>
        
        <div className="flex items-center space-x-2">
          {/* Toggle Switch lu/non lu */}
          <div className="flex items-center space-x-2">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {isRead ? 'Lu' : 'Non lu'}
            </span>
            <button
              onClick={() => onToggleRead(tomeNumber)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 ${
                isRead
                  ? 'bg-green-600 hover:bg-green-700'
                  : 'bg-gray-200 hover:bg-gray-300 dark:bg-gray-600 dark:hover:bg-gray-500'
              }`}
              title={isRead ? 'Marquer comme non lu' : 'Marquer comme lu'}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-200 ease-in-out ${
                  isRead ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* Bouton dropdown */}
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="p-1 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            title="Afficher les détails du tome"
          >
            {isOpen ? (
              <ChevronUpIcon className="w-4 h-4" />
            ) : (
              <ChevronDownIcon className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>

      {/* Dropdown Content - Mini-fiche du tome */}
      {isOpen && (
        <div className="ml-6 mr-2 mb-2 bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-600">
          <div className="space-y-3">
            {/* Titre complet */}
            <div>
              <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-1">
                {tomeInfo.title}
              </h4>
              <div className="text-xs text-gray-500 dark:text-gray-400">
                Tome {tomeInfo.number} de la série {seriesData?.name}
              </div>
            </div>

            {/* Informations techniques */}
            <div className="grid grid-cols-2 gap-3 text-xs">
              {/* Pages et temps de lecture */}
              {tomeInfo.pages && (
                <div className="flex items-center space-x-1">
                  <BookOpenIcon className="w-3 h-3 text-blue-500" />
                  <span className="text-gray-600 dark:text-gray-400">
                    {tomeInfo.pages} pages
                  </span>
                </div>
              )}

              {readingTime && (
                <div className="flex items-center space-x-1">
                  <DocumentTextIcon className="w-3 h-3 text-green-500" />
                  <span className="text-gray-600 dark:text-gray-400">
                    {readingTime} de lecture
                  </span>
                </div>
              )}

              {/* Année de publication */}
              {tomeInfo.published_year && (
                <div className="flex items-center space-x-1">
                  <CalendarIcon className="w-3 h-3 text-purple-500" />
                  <span className="text-gray-600 dark:text-gray-400">
                    Publié en {tomeInfo.published_year}
                  </span>
                </div>
              )}

              {/* Statut de lecture */}
              <div className="flex items-center space-x-1">
                <div className={`w-3 h-3 rounded-full ${
                  isRead ? 'bg-green-500' : 'bg-gray-300 dark:bg-gray-600'
                }`} />
                <span className="text-gray-600 dark:text-gray-400">
                  {isRead ? 'Terminé' : 'Non lu'}
                </span>
              </div>
            </div>

            {/* Description */}
            {tomeInfo.description && (
              <div>
                <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">
                  {tomeInfo.description}
                </p>
              </div>
            )}

            {/* Métadonnées additionnelles */}
            {(tomeInfo.isbn || tomeInfo.publisher) && (
              <div className="pt-2 border-t border-gray-200 dark:border-gray-600">
                <div className="space-y-1 text-xs text-gray-500 dark:text-gray-400">
                  {tomeInfo.publisher && (
                    <div>
                      <span className="font-medium">Éditeur:</span> {tomeInfo.publisher}
                    </div>
                  )}
                  {tomeInfo.isbn && (
                    <div>
                      <span className="font-medium">ISBN:</span> {tomeInfo.isbn}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Actions rapides */}
            <div className="pt-2 border-t border-gray-200 dark:border-gray-600">
              <div className="flex space-x-2">
                <button
                  onClick={() => onToggleRead(tomeNumber)}
                  className={`px-2 py-1 text-xs rounded transition-colors ${
                    isRead
                      ? 'bg-orange-100 text-orange-700 hover:bg-orange-200 dark:bg-orange-900/20 dark:text-orange-300 dark:hover:bg-orange-900/40'
                      : 'bg-green-100 text-green-700 hover:bg-green-200 dark:bg-green-900/20 dark:text-green-300 dark:hover:bg-green-900/40'
                  }`}
                >
                  {isRead ? 'Marquer non lu' : 'Marquer comme lu'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TomeDropdown;