import React from 'react';
import { SparklesIcon } from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { coverImgSrc } from '../../utils/helpers';
import { getStatusBadge, getStatusLabel, resolveVolumesCount } from '../../utils/seriesDetailHelpers';
import logger from '../../utils/logger';

/** En-tête de la fiche série : vignette, titre, auteur, statut, bouton d'ajout et JSON Wikidata. */
const SeriesHeader = ({
  series,
  seriesCoverUrl,
  coverProxy,
  setCoverProxy,
  onAuthorClick,
  seriesStatus,
  enrichedSeries,
  olBooks,
  books,
  seriesDisplayName,
  goToSimilar,
  showWdRaw,
  setShowWdRaw,
  onAddSeries,
  isSeriesOwned,
  isAdding,
  setIsAdding,
  addDone,
  setAddDone,
  checkIfSeriesOwned,
  onClose,
}) => (
  <>
        {/* Header */}
        <div className="border-b border-gray-200 dark:border-gray-700 px-4 py-3 sm:p-6">
          <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between md:gap-4">
            <div className="flex min-w-0 flex-1 items-start gap-2.5 sm:gap-4">
              {/* Petite vignette à côté du titre */}
              <div className="h-[4.5rem] w-12 shrink-0 rounded-md shadow-md overflow-hidden sm:h-20 sm:w-14">
                {seriesCoverUrl ? (
                  <img
                    src={coverImgSrc(seriesCoverUrl, { forceProxy: coverProxy })}
                    alt={`Couverture de ${series.name}`}
                    className="w-full h-full object-cover"
                    referrerPolicy={coverProxy ? undefined : 'no-referrer'}
                    onError={(e) => {
                      if (!coverProxy) {
                        setCoverProxy(true);
                        return;
                      }
                      e.target.style.display = 'none';
                      if (e.target.nextSibling) e.target.nextSibling.style.display = 'flex';
                    }}
                  />
                ) : null}
                <div
                  className={`w-full h-full bg-gradient-to-br from-purple-500 to-blue-600 rounded-md flex items-center justify-center text-white text-xl font-semibold ${seriesCoverUrl ? 'hidden' : 'flex'}`}
                >
                  {(series?.name || 'S').charAt(0).toUpperCase()}
                </div>
              </div>
              
              <div className="min-w-0 flex-1">
                <h2 className="text-lg sm:text-2xl font-bold text-gray-900 dark:text-white mb-0.5 break-words leading-snug">
                  {series?.name}
                </h2>
                <p className="text-xs sm:text-base text-gray-600 dark:text-gray-400 mb-1.5">
                  {series?.author ? (
                    <>
                      par{' '}
                      <button 
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (onAuthorClick) onAuthorClick(series?.author);
                        }}
                        className="text-left text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors underline"
                      >
                        {series?.author}
                      </button>
                    </>
                  ) : (
                    <span className="text-gray-500 dark:text-gray-400">Référentiel Wikidata statique</span>
                  )}
                </p>
                <div className="flex flex-wrap items-center gap-2 text-xs sm:text-sm">
                  <span className={`px-2 py-1 rounded-full font-medium ${getStatusBadge(seriesStatus)}`}>
                    {getStatusLabel(seriesStatus)}
                  </span>
                  <span className="text-gray-500 dark:text-gray-400 whitespace-nowrap">
                     {resolveVolumesCount(
                      enrichedSeries?.volumes,
                      olBooks.length || books.length || (series?.books?.length) || 0
                    )} tome(s)
                  </span>
                  {seriesDisplayName ? (
                    <button
                      type="button"
                      onClick={goToSimilar}
                      className="inline-flex items-center gap-1 px-2 py-1 rounded-full font-medium bg-purple-100 dark:bg-purple-900/40 text-purple-800 dark:text-purple-200 hover:bg-purple-200 dark:hover:bg-purple-900/60"
                    >
                      <SparklesIcon className="h-3.5 w-3.5" />
                      Similaires
                    </button>
                  ) : null}
                  {series.fromStaticWikidata && series.staticWikidataDetail && (
                    <>
                      <a
                        href={`https://www.wikidata.org/wiki/${series.wikidata_qid || series.staticWikidataDetail.qid}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-indigo-600 dark:text-indigo-400 hover:underline"
                      >
                        Wikidata ↗
                      </a>
                      <button
                        type="button"
                        onClick={() => setShowWdRaw((v) => !v)}
                        className="text-gray-600 dark:text-gray-400 hover:underline"
                      >
                        {showWdRaw ? 'Masquer JSON' : 'JSON brut'}
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
            
            <div className="flex w-full flex-col gap-2 md:w-auto md:shrink-0 md:items-end">
              {/* Bouton Ajouter — identique à celui des livres individuels (pleine largeur sur mobile) */}
              {onAddSeries && !isSeriesOwned && (
                <button
                  type="button"
                  onClick={async () => {
                    if (isAdding || addDone) return;
                    setIsAdding(true);
                    try {
                      await onAddSeries({ ...series, mergedLibraryVolumes: olBooks });
                      setAddDone(true);
                      setTimeout(() => {
                        checkIfSeriesOwned();
                        setIsAdding(false);
                        setAddDone(false);
                      }, 1000);
                    } catch (error) {
                      logger.error('Erreur lors de l\'ajout de la série:', error);
                      toast.error(error.message || 'Erreur lors de l\'ajout de la série');
                      setIsAdding(false);
                    }
                  }}
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

              <button
                type="button"
                onClick={onClose}
                className="hidden md:block p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                aria-label="Fermer"
              >
                <span className="text-xl leading-none">✕</span>
              </button>
            </div>
          </div>
        </div>

        {showWdRaw && series.staticWikidataDetail && (
          <div className="border-b border-gray-200 dark:border-gray-700 px-4 py-3 sm:px-6">
            <pre className="max-h-56 overflow-auto rounded bg-gray-50 p-3 text-left text-[10px] leading-snug text-gray-800 dark:bg-gray-900 dark:text-gray-200 sm:text-xs">
              {JSON.stringify(series.staticWikidataDetail, null, 2)}
            </pre>
          </div>
        )}
  </>
);

export default SeriesHeader;
