import React from 'react';
import TomeDropdown from '../TomeDropdown';
import {
  displayBookTitleFrFirst,
  mergeOpenLibraryBooksByVolume,
  sortOpenLibraryBooksByVolume,
} from '../../utils/openLibraryBookDisplay';
import { resolveVolumesCount } from '../../utils/seriesDetailHelpers';

/** Liste des tomes (un TomeDropdown par tome) — référentiel statique, sinon Wikidata / Open Library. */
const SeriesTomeList = ({
  onClose,
  enrichedSeries,
  olBooks,
  series,
  readTomes,
  tomeStatuses,
  handleTomeStatusChange,
  handleTomeFeedbackChange,
  handleTomeReadToggle,
}) => (
  <>
        {/* Liste des tomes avec mini-fiches dropdown */}
        <div className="border-b border-gray-200 dark:border-gray-700 px-4 py-4 sm:px-6">
          <div className="sticky top-0 z-10 -mx-4 mb-3 flex items-center justify-between border-b border-gray-100 bg-white px-4 py-2 dark:border-gray-800 dark:bg-gray-800 sm:static sm:mx-0 sm:mb-3 sm:border-0 sm:bg-transparent sm:p-0 dark:sm:bg-transparent">
            <h3 className="text-base font-semibold text-gray-900 dark:text-white sm:text-lg">Liste des tomes</h3>
            <button
              type="button"
              onClick={onClose}
              className="rounded-full bg-gray-100 px-3 py-1.5 text-xs font-medium text-gray-600 dark:bg-gray-700 dark:text-gray-300 sm:hidden"
            >
              Fermer
            </button>
          </div>
          
          {(resolveVolumesCount(enrichedSeries?.volumes) > 0) || olBooks.length > 0 ? (
            <div className="space-y-1">
              {(() => {
                const volumeCount = resolveVolumesCount(enrichedSeries?.volumes);
                // Construire la liste finale : préférence enrichedSeries (base statique) > olBooks (Wikidata/OL)
                if (volumeCount > 0 && !enrichedSeries.fromFallbackBooks) {
                  // Source : EXTENDED_SERIES_DATABASE → style TomeDropdown exact comme Harry Potter
                  return Array.from({ length: volumeCount }, (_, index) => {
                    const tomeNumber = index + 1;
                    const tomeTitle = enrichedSeries.volume_titles?.[tomeNumber] || `${enrichedSeries.name} - Tome ${tomeNumber}`;
                    return (
                      <TomeDropdown
                        key={tomeNumber}
                        tomeNumber={tomeNumber}
                        tomeTitle={tomeTitle}
                        seriesData={enrichedSeries}
                        tomeStatus={tomeStatuses[String(tomeNumber)]?.status || 'non_lu'}
                        currentPage={tomeStatuses[String(tomeNumber)]?.currentPage || null}
                        rating={tomeStatuses[String(tomeNumber)]?.rating || 0}
                        review={tomeStatuses[String(tomeNumber)]?.review || ''}
                        onStatusChange={handleTomeStatusChange}
                        onFeedbackChange={handleTomeFeedbackChange}
                        onToggleRead={handleTomeReadToggle}
                      />
                    );
                  });
                }

                // Source : Wikidata ou OL → construire un enrichedSeries synthétique
                const booksToShowRaw = olBooks.length > 0 ? olBooks : (series.books || []);
                const booksToShow = mergeOpenLibraryBooksByVolume([...booksToShowRaw]).sort(sortOpenLibraryBooksByVolume);
                const syntheticVolumeTitles = {};
                booksToShow.forEach((b, i) => {
                  const num = b.volume_number || (i + 1);
                  syntheticVolumeTitles[num] = displayBookTitleFrFirst(b) || `${series.name} - Tome ${num}`;
                });
                const syntheticSeries = {
                  ...enrichedSeries,
                  volumes: booksToShow.length,
                  volume_titles: syntheticVolumeTitles,
                };
                return booksToShow.map((book, index) => {
                  const tomeNumber = book.volume_number || (index + 1);
                  const tomeTitle = syntheticVolumeTitles[tomeNumber] || displayBookTitleFrFirst(book);
                  return (
                    <TomeDropdown
                      key={book.ol_key || book.id || `tome-${tomeNumber}-${index}`}
                      tomeNumber={tomeNumber}
                      tomeTitle={tomeTitle}
                      seriesData={syntheticSeries}
                      tomeStatus={tomeStatuses[String(tomeNumber)]?.status || 'non_lu'}
                      currentPage={tomeStatuses[String(tomeNumber)]?.currentPage || null}
                      rating={tomeStatuses[String(tomeNumber)]?.rating || 0}
                      review={tomeStatuses[String(tomeNumber)]?.review || ''}
                      onStatusChange={handleTomeStatusChange}
                      onFeedbackChange={handleTomeFeedbackChange}
                      onToggleRead={handleTomeReadToggle}
                    />
                  );
                });
              })()}
            </div>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400 italic">
              Informations sur les tomes non disponibles pour cette série
            </p>
          )}
        </div>
  </>
);

export default SeriesTomeList;
