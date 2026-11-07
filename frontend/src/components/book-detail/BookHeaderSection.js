import React from 'react';
import { XMarkIcon, ArrowPathIcon, SparklesIcon, HeartIcon, PaperAirplaneIcon } from '@heroicons/react/24/outline';
import { HeartIcon as HeartSolidIcon } from '@heroicons/react/24/solid';
import { coverImgSrc } from '../../utils/helpers';

/** En-tête de la fiche livre : titre, auteur, statut, favori, partage. */
const BookHeaderSection = ({
  book,
  onClose,
  onAuthorClick,
  navigate,
  titleMain,
  isEditing,
  bouncing,
  olLoading,
  pageInput,
  setPageInput,
  isAdding,
  addDone,
  coverProxy,
  setCoverProxy,
  isFavorite,
  pageInputRef,
  totalPages,
  displaySynopsis,
  statusOptions,
  formatReadDate,
  handleQuickStatusChange,
  handleMarkToReread,
  handleStartReread,
  handlePageSave,
  canAddFromCatalog,
  inLibrary,
  handleAddFromOpenLibrary,
  displayStatus,
  handleToggleFavorite,
  handleRecommendToFriend,
  getCurrentStatus,
}) => (
  <>
        <div className="flex flex-col gap-3 mb-3 md:flex-row md:items-start md:justify-between md:gap-6">
          <div className="min-w-0 flex-1">
            {/* En-tête : petite vignette + titre (surtout mobile) */}
            <div className="flex items-start gap-3 mb-3">
              <div className="h-[4.5rem] w-12 shrink-0 overflow-hidden rounded-md shadow-md bg-gray-100 dark:bg-gray-700 md:h-24 md:w-16">
                {book.cover_url ? (
                  <img
                    src={coverImgSrc(book.cover_url, { forceProxy: coverProxy })}
                    alt=""
                    className="h-full w-full object-cover"
                    referrerPolicy={coverProxy ? undefined : 'no-referrer'}
                    onError={() => {
                      if (!coverProxy) setCoverProxy(true);
                    }}
                  />
                ) : (
                  <div className="flex h-full w-full items-center justify-center text-xl bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800">
                  </div>
                )}
              </div>
              <div className="min-w-0 flex-1">
                <h2 className="text-lg sm:text-2xl font-bold text-gray-900 dark:text-white mb-1 break-words leading-snug">{titleMain}</h2>
                <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400 mb-2">
                  par{' '}
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      if (onAuthorClick) onAuthorClick(book.author);
                    }}
                    className="text-sm sm:text-base text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors underline"
                  >
                    {book.author}
                  </button>
                </p>
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-booktime-100 dark:bg-booktime-900/30 text-booktime-800 dark:text-booktime-300">
                    {(book.category || 'roman').charAt(0).toUpperCase() + (book.category || 'roman').slice(1)}
                  </span>
                  {inLibrary && (
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getCurrentStatus().color}`}>
                      {getCurrentStatus().label}
                    </span>
                  )}
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
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 dark:bg-purple-900/40 text-purple-800 dark:text-purple-200 hover:bg-purple-200 dark:hover:bg-purple-900/60 transition-colors"
                    >
                      <SparklesIcon className="h-3.5 w-3.5" />
                      Similaires
                    </button>
                  ) : null}
                  {inLibrary && book?.id && !book.isDemotedSeries ? (
                    <button
                      type="button"
                      onClick={handleToggleFavorite}
                      aria-pressed={isFavorite}
                      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium transition-colors ${
                        isFavorite
                          ? 'bg-rose-100 dark:bg-rose-900/40 text-rose-700 dark:text-rose-200'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-600'
                      }`}
                    >
                      {isFavorite ? (
                        <HeartSolidIcon className="h-3.5 w-3.5" />
                      ) : (
                        <HeartIcon className="h-3.5 w-3.5" />
                      )}
                      {isFavorite ? 'Préféré' : 'Ajouter aux préférés'}
                    </button>
                  ) : null}
                  {titleMain ? (
                    <button
                      type="button"
                      onClick={handleRecommendToFriend}
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900/40 text-green-800 dark:text-green-200 hover:bg-green-200 dark:hover:bg-green-900/60 transition-colors"
                    >
                      <PaperAirplaneIcon className="h-3.5 w-3.5" />
                      Recommander à un ami
                    </button>
                  ) : null}
                </div>
              </div>
            </div>

            {/* Résumé FR uniquement — jamais de message « Aucun résumé » */}
            {displaySynopsis ? (
              <div className="mb-3">
                <h3 className="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Résumé
                </h3>
                <p className="text-gray-600 dark:text-gray-400 text-xs sm:text-sm leading-relaxed whitespace-pre-line">
                  {displaySynopsis}
                </p>
              </div>
            ) : olLoading ? (
              <div className="mb-3 flex items-center gap-2 text-xs text-gray-400 py-1">
                <div className="h-3.5 w-3.5 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin" />
                Chargement du résumé…
              </div>
            ) : null}

            {/* Boutons rapides de changement de statut — une seule ligne compacte */}
            {inLibrary && !isEditing && (
              <div className="mb-3">
                <div className="flex items-center mb-1.5">
                  <h3 className="text-xs font-medium text-gray-700 dark:text-gray-300">Statut</h3>
                </div>
                <div className="flex flex-nowrap items-center gap-2 overflow-x-auto">
                  <div className="flex min-w-0 flex-1 sm:flex-initial rounded-lg overflow-hidden border border-gray-200 dark:border-gray-600">
                    {statusOptions.map((option) => (
                      <button
                        key={option.value}
                        type="button"
                        onClick={() => handleQuickStatusChange(option.value)}
                        className={`btn-ripple flex flex-1 items-center justify-center whitespace-nowrap px-2 py-1.5 text-[11px] sm:text-xs font-medium transition-all sm:px-3 sm:py-2 ${
                          bouncing === `status-${option.value}` ? 'btn-bounce' : ''
                        } ${
                          displayStatus === option.value
                            ? 'bg-gray-900 dark:bg-white text-white dark:text-gray-900 shadow-md'
                            : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'
                        }`}
                        title={`Marquer comme ${option.label}`}
                      >
                        {option.label}
                      </button>
                    ))}
                  </div>
                  {displayStatus === 'completed' && (
                    <button
                      type="button"
                      onClick={handleMarkToReread}
                      className={`inline-flex shrink-0 items-center gap-1 whitespace-nowrap px-2 py-1.5 text-[11px] sm:text-xs font-medium rounded-lg border border-purple-200 dark:border-purple-800 bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 hover:bg-purple-100 dark:hover:bg-purple-900/50 transition-colors ${
                        bouncing === 'to-reread' ? 'btn-bounce' : ''
                      }`}
                      title="Mettre dans la section À relire"
                    >
                      <ArrowPathIcon className="h-3.5 w-3.5" />
                      À relire
                    </button>
                  )}
                  {displayStatus === 'to_reread' && (
                    <button
                      type="button"
                      onClick={handleStartReread}
                      className={`inline-flex shrink-0 items-center gap-1 whitespace-nowrap px-2 py-1.5 text-[11px] sm:text-xs font-medium rounded-lg border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors ${
                        bouncing === 'reread' ? 'btn-bounce' : ''
                      }`}
                      title="Commencer la relecture depuis le début"
                    >
                      <ArrowPathIcon className="h-3.5 w-3.5" />
                      Commencer
                    </button>
                  )}
                </div>

                {(displayStatus === 'completed' || displayStatus === 'to_reread') &&
                  formatReadDate(book.date_completed) && (
                  <p className="mt-2 text-sm text-green-700 dark:text-green-400">
                    Lu le {formatReadDate(book.date_completed)}
                    {formatReadDate(book.date_started) &&
                      formatReadDate(book.date_started) !== formatReadDate(book.date_completed) && (
                        <span className="text-gray-500 dark:text-gray-400">
                          {' '}· commencé le {formatReadDate(book.date_started)}
                        </span>
                      )}
                  </p>
                )}
                {displayStatus === 'reading' && formatReadDate(book.date_started) && (
                  <p className="mt-2 text-sm text-blue-700 dark:text-blue-400">
                    Lecture commencée le {formatReadDate(book.date_started)}
                  </p>
                )}
              </div>
            )}

            {/* Saisie rapide de la page (livres individuels + séries rétrogradées, comme les tomes) */}
            {inLibrary && !isEditing && displayStatus === 'reading' && (
              <div className="mb-4 p-3 bg-gray-50 dark:bg-gray-800/40 rounded-lg border border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-xs font-medium text-gray-500 dark:text-gray-400">Progression de lecture</h3>
                  {totalPages > 0 && pageInput > 0 && (
                    <span className="text-xs font-medium text-gray-600 dark:text-gray-300">
                      {Math.round(((pageInput || 0) / totalPages) * 100)}%
                    </span>
                  )}
                </div>
                {totalPages > 0 && pageInput > 0 && (
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 mb-3">
                    <div
                      className="bg-blue-500 h-1.5 rounded-full reading-progress-bar transition-all duration-300"
                      style={{ width: `${Math.min(100, Math.round(((pageInput || 0) / totalPages) * 100))}%` }}
                    />
                  </div>
                )}
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-500 dark:text-gray-400">Page</span>
                  <input
                    ref={pageInputRef}
                    type="number"
                    value={pageInput || ''}
                    placeholder="optionnel"
                    onChange={(e) => setPageInput(Math.max(0, Math.min(totalPages || 99999, parseInt(e.target.value) || 0)))}
                    onBlur={handlePageSave}
                    onKeyDown={(e) => e.key === 'Enter' && handlePageSave()}
                    min="0"
                    max={totalPages || undefined}
                    className="w-24 px-2 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-booktime-500 text-center"
                  />
                  {totalPages > 0 ? (
                    <span className="text-sm text-gray-500 dark:text-gray-400">/ {totalPages}</span>
                  ) : olLoading ? (
                    <span className="text-xs text-gray-400 dark:text-gray-500">recherche du total…</span>
                  ) : null}
                  {(parseInt(pageInput) || 0) !== (book.current_page || 0) && (
                    <button
                      onClick={handlePageSave}
                      className={`btn-ripple ml-auto px-3 py-1 text-sm font-medium bg-blue-500 hover:bg-blue-600 active:bg-blue-700 text-white rounded-md transition-colors ${bouncing === 'page-save' ? 'btn-bounce' : ''}`}
                    >
                      ✓ Sauvegarder
                    </button>
                  )}
                </div>
              </div>
            )}


          </div>
          
          <div className="flex w-full flex-col gap-2 shrink-0 md:w-auto md:items-end">
            {/* Bouton Ajouter pour les livres Open Library — pleine largeur sur mobile */}
            {canAddFromCatalog && (
              <button
                onClick={handleAddFromOpenLibrary}
                disabled={isAdding || addDone}
                className={`btn-ripple w-full md:w-auto md:min-w-[180px] px-4 py-3 md:py-2 text-sm font-semibold text-white rounded-xl md:rounded-lg transition-all flex items-center justify-center gap-2 ${
                  addDone
                    ? 'bg-green-500 cursor-default'
                    : isAdding
                    ? 'bg-green-500 cursor-not-allowed opacity-80'
                    : 'bg-green-600 hover:bg-green-700 hover:shadow-md active:bg-green-800'
                }`}
              >
                {addDone ? (
                  <>
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                    <span>Ajouté !</span>
                  </>
                ) : isAdding ? (
                  <>
                    <span className="btn-spinner" />
                    <span>Ajout en cours…</span>
                  </>
                ) : (
                  <>
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                    </svg>
                    <span>Ajouter à ma bibliothèque</span>
                  </>
                )}
              </button>
            )}
            
            <div className="hidden md:flex flex-row flex-wrap items-center justify-end gap-1 md:gap-2">
            <button
              type="button"
              onClick={onClose}
              className="p-2 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
              aria-label="Fermer"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
            </div>
          </div>
        </div>
  </>
);

export default BookHeaderSection;
