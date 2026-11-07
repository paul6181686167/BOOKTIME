import React from 'react';
import { TrashIcon } from '@heroicons/react/24/outline';
import AddToCollectionMenu from '../common/AddToCollectionMenu';

/** Ajout à une collection et retrait de la bibliothèque. */
const SeriesLibraryActions = ({
  isSeriesOwned,
  series,
  books,
  showCollectionMenu,
  setShowCollectionMenu,
  confirmDelete,
  setConfirmDelete,
  handleDeleteSeries,
  deleting,
}) => (
  <>
        {/* Collection + Retirer */}
        {(isSeriesOwned || series.isOwnedSeries || series.isLibrarySeries || series.isSeriesCard || (series.books && series.books.length > 0) || books.length > 0) && (
          <div className="px-4 sm:px-6 py-4 border-t border-gray-200 dark:border-gray-700 space-y-3">
            {(isSeriesOwned || series.isOwnedSeries || series.isLibrarySeries) && (series.id || series._id) && (
              <div>
                {showCollectionMenu ? (
                  <AddToCollectionMenu
                    item={{
                      type: 'series',
                      id: series.id || series._id,
                      title: series.name || series.series_name || 'Série',
                      author: series.author || series.authors?.[0] || '',
                      cover_url: series.cover_url || series.cover_image_url || null,
                    }}
                    onClose={() => setShowCollectionMenu(false)}
                  />
                ) : (
                  <button
                    type="button"
                    onClick={() => setShowCollectionMenu(true)}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-green-700 dark:text-green-400 border border-green-200 dark:border-green-800 rounded-lg hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors"
                  >
                    Ajouter à une collection
                  </button>
                )}
              </div>
            )}
            {confirmDelete ? (
              <div className="flex items-center justify-between bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-4 py-3">
                <span className="text-sm text-red-700 dark:text-red-300 font-medium">
                  Retirer définitivement cette série ?
                </span>
                <div className="flex gap-2">
                  <button
                    onClick={() => setConfirmDelete(false)}
                    className="px-3 py-1.5 text-sm bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
                  >
                    Annuler
                  </button>
                  <button
                    onClick={handleDeleteSeries}
                    disabled={deleting}
                    className="px-3 py-1.5 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors font-medium disabled:opacity-50"
                  >
                    {deleting ? 'Suppression…' : 'Confirmer'}
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setConfirmDelete(true)}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-medium text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
              >
                <TrashIcon className="h-4 w-4" />
                Retirer de ma bibliothèque
              </button>
            )}
          </div>
        )}
  </>
);

export default SeriesLibraryActions;
