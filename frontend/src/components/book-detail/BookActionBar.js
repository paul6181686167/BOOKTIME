import React from 'react';
import { TrashIcon, SparklesIcon } from '@heroicons/react/24/outline';
import AddToCollectionMenu from '../common/AddToCollectionMenu';

/** Boutons d'action : enregistrer / annuler en édition, ajouter, modifier, supprimer. */
const BookActionBar = ({
  book,
  onClose,
  onDelete,
  navigate,
  titleMain,
  isEditing,
  setIsEditing,
  bouncing,
  isLoading,
  confirmDelete,
  setConfirmDelete,
  showCollectionMenu,
  setShowCollectionMenu,
  handleSave,
  handleDelete,
}) => (
  <>
        {/* Boutons d'action */}
        {isEditing ? (
          <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setIsEditing(false)}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
            >
              Annuler
            </button>
            <button
              onClick={handleSave}
              disabled={isLoading}
              className={`btn-ripple px-4 py-2 text-sm font-semibold text-white bg-booktime-600 border border-transparent rounded-lg hover:bg-booktime-700 disabled:opacity-50 flex items-center gap-2 min-w-[120px] justify-center ${bouncing === 'save' ? 'btn-bounce' : ''}`}
            >
              {isLoading ? (
                <>
                  <span className="btn-spinner" />
                  <span>Sauvegarde…</span>
                </>
              ) : (
                <>
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                  <span>Sauvegarder</span>
                </>
              )}
            </button>
          </div>
        ) : (
          /* Similaires + Collection + Retirer */
          <div className="pt-4 border-t border-gray-200 dark:border-gray-700 space-y-3">
            {titleMain ? (
              <button
                type="button"
                onClick={() => {
                  const params = new URLSearchParams({
                    tab: 'similaires',
                    title: titleMain,
                  });
                  if (book.author) params.set('author', book.author);
                  onClose?.();
                  navigate(`/recommendations?${params}`);
                }}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 text-sm font-semibold text-white bg-purple-600 hover:bg-purple-700 active:bg-purple-800 rounded-xl transition-colors shadow-sm"
              >
                <SparklesIcon className="h-5 w-5" />
                Voir des livres similaires
              </button>
            ) : null}
          {!book.isFromOpenLibrary && (
            <>
              {book.id && (
                <div>
                  {showCollectionMenu ? (
                    <AddToCollectionMenu
                      item={{
                        type: book.isDemotedSeries ? 'series' : 'book',
                        id: book.id,
                        title: titleMain || book.title,
                        author: book.author || '',
                        cover_url: book.cover_url || null,
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
              {onDelete && (confirmDelete ? (
                <div className="flex items-center justify-between bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg px-4 py-3">
                  <span className="text-sm text-red-700 dark:text-red-300 font-medium">
                    Retirer définitivement ce livre ?
                  </span>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setConfirmDelete(false)}
                      className="px-3 py-1.5 text-sm bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
                    >
                      Annuler
                    </button>
                    <button
                      onClick={handleDelete}
                      disabled={isLoading}
                      className="px-3 py-1.5 text-sm bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors font-medium disabled:opacity-50"
                    >
                      {isLoading ? 'Suppression…' : 'Confirmer'}
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
              ))}
            </>
          )}
          </div>
        )}
  </>
);

export default BookActionBar;
