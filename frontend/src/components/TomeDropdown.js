import React, { useState, useEffect } from 'react';
import { ChevronDownIcon, ChevronUpIcon, BookOpenIcon, CalendarIcon, DocumentTextIcon } from '@heroicons/react/24/outline';
import { isVolumeUnreleased } from '../utils/volumeRelease';

// tomeStatus : 'non_lu' | 'en_cours' | 'lu'
// onStatusChange(tomeNumber, status, currentPage)
const TomeDropdown = ({ tomeNumber, tomeTitle, seriesData, tomeStatus = 'non_lu', currentPage = null, onToggleRead, onStatusChange }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [pageInput, setPageInput] = useState(currentPage || '');
  const unreleased = isVolumeUnreleased(seriesData, tomeNumber);

  // Synchroniser pageInput si currentPage change depuis le parent
  useEffect(() => {
    setPageInput(currentPage ?? '');
  }, [currentPage]);

  // Rétrocompatibilité : si onStatusChange absent, utiliser onToggleRead (booléen)
  const handleStatusChange = (newStatus) => {
    if (unreleased) return;
    const page = newStatus === 'en_cours' ? (Number(pageInput) || null) : null;
    if (onStatusChange) {
      onStatusChange(tomeNumber, newStatus, page);
    } else if (onToggleRead) {
      onToggleRead(tomeNumber); // legacy
    }
  };

  const handlePageSave = () => {
    if (onStatusChange) {
      onStatusChange(tomeNumber, 'en_cours', Number(pageInput) || null);
    }
  };

  const getTomeInfo = () => {
    const baseInfo = {
      title: tomeTitle,
      number: tomeNumber,
      pages: null,
      published_year: null,
      description: null,
      isbn: null,
      publisher: null,
    };
    if (!seriesData) return baseInfo;

    // 1) Référentiel curé (pages réelles si renseignées)
    if (seriesData.volume_details?.[tomeNumber]) {
      const d = seriesData.volume_details[tomeNumber];
      return {
        ...baseInfo,
        pages: d.pages || null,
        published_year: d.published_year || null,
        description: d.description || null,
        isbn: d.isbn || null,
        publisher: d.publisher || null,
      };
    }

    // 2) Métadonnées issues du merge OL / Google Books / Wikidata
    const fromMerged =
      (Array.isArray(seriesData.mergedLibraryVolumes) &&
        seriesData.mergedLibraryVolumes.find(
          (v) => Number(v.volume_number) === Number(tomeNumber)
        )) ||
      (Array.isArray(seriesData.volumes) &&
        seriesData.volumes.find(
          (v) =>
            Number(v.volume_number) === Number(tomeNumber) ||
            Number(v.number) === Number(tomeNumber)
        ));
    if (fromMerged) {
      const pages =
        fromMerged.page_count ||
        fromMerged.pages ||
        fromMerged.total_pages ||
        fromMerged.number_of_pages ||
        null;
      return {
        ...baseInfo,
        title: fromMerged.display_title || fromMerged.volume_title || fromMerged.title || tomeTitle,
        pages: pages ? Number(pages) : null,
        published_year:
          fromMerged.publication_year ||
          fromMerged.published_year ||
          fromMerged.first_publish_year ||
          null,
        description: fromMerged.description || null,
        isbn: fromMerged.isbn || fromMerged.isbn13 || null,
        publisher: fromMerged.publisher || null,
      };
    }

    // 3) Pas de valeur inventée (ex-320 / 190 / 52) — mieux vaut "inconnu"
    if (seriesData.first_published) {
      const y = parseInt(seriesData.first_published, 10);
      if (!Number.isNaN(y)) {
        baseInfo.published_year = y + (tomeNumber - 1);
      }
    }
    return baseInfo;
  };

  const getReadingTime = (pages, category) => {
    if (!pages) return null;
    const [wpp, speed] = category === 'manga' ? [50, 200] : category === 'bd' ? [30, 180] : [250, 250];
    const mins = Math.round((pages * wpp) / speed);
    return mins < 60 ? `~${mins} min` : `~${Math.floor(mins / 60)}h${mins % 60 ? (mins % 60) + 'min' : ''}`;
  };

  const tomeInfo = getTomeInfo();
  const readingTime = getReadingTime(tomeInfo.pages, seriesData?.category);
  const isRead = tomeStatus === 'lu';
  const isInProgress = tomeStatus === 'en_cours';

  const statusConfig = {
    non_lu:  { label: 'Non lu',   dot: 'bg-gray-300 dark:bg-gray-600',   text: 'text-gray-500 dark:text-gray-400' },
    en_cours: { label: 'En cours', dot: 'bg-blue-500',                   text: 'text-blue-600 dark:text-blue-400' },
    lu:      { label: 'Lu',        dot: 'bg-green-500',                  text: 'text-green-600 dark:text-green-400' },
  };
  const cfg = statusConfig[tomeStatus] || statusConfig.non_lu;

  return (
    <div className="border-l-2 border-gray-200 dark:border-gray-600 ml-1 sm:ml-4">
      {/* Jusqu’à lg : titre + toggle empilés (modales / tablettes étroites) · lg+ : une ligne */}
      <div className="flex flex-col gap-2 p-2 hover:bg-gray-50 dark:hover:bg-gray-800 rounded lg:flex-row lg:items-center lg:justify-between lg:gap-3">
        <div className="flex min-w-0 flex-1 flex-col gap-1 lg:flex-row lg:items-center lg:gap-2">
          <span className="shrink-0 text-xs font-semibold text-purple-600 dark:text-purple-400 lg:w-[4.5rem]">
            Tome {tomeNumber}
          </span>
          <span className={`min-w-0 text-sm leading-snug break-words lg:line-clamp-2 ${isRead ? 'line-through text-gray-400' : 'text-gray-700 dark:text-gray-300'}`}>
            {tomeTitle}
          </span>
          {isInProgress && currentPage && (
            <span className="shrink-0 text-xs text-blue-500 dark:text-blue-400 lg:ml-auto">p.{currentPage}</span>
          )}
        </div>

        <div className="flex w-full shrink-0 items-stretch gap-2 lg:w-auto lg:items-center lg:justify-end">
          {unreleased ? (
            <div
              className="flex min-h-[2.5rem] flex-1 items-center justify-center rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-[11px] font-semibold text-amber-800 dark:border-amber-700/60 dark:bg-amber-900/30 dark:text-amber-200 lg:flex-none lg:text-xs"
              title="Ce volume n'est pas encore paru"
            >
              Non sorti
            </div>
          ) : (
            <div className="grid min-h-[2.5rem] flex-1 grid-cols-3 overflow-hidden rounded-lg border border-gray-200 dark:border-gray-600 text-[10px] font-medium leading-tight lg:flex lg:h-auto lg:min-h-0 lg:flex-none lg:text-xs lg:leading-normal">
              {(['non_lu', 'en_cours', 'lu']).map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => handleStatusChange(s)}
                  className={`flex items-center justify-center px-0.5 py-2 lg:px-2 lg:py-1 transition-colors ${
                    tomeStatus === s
                      ? s === 'lu' ? 'bg-green-600 text-white'
                        : s === 'en_cours' ? 'bg-blue-600 text-white'
                        : 'bg-gray-700 dark:bg-gray-300 text-white dark:text-gray-900'
                      : 'bg-white dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'
                  }`}
                >
                  {statusConfig[s].label}
                </button>
              ))}
            </div>
          )}

          <button type="button" onClick={() => setIsOpen(!isOpen)} className="flex w-10 shrink-0 items-center justify-center rounded-lg border border-gray-200 bg-gray-50 text-gray-500 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-400 lg:w-auto lg:border-0 lg:bg-transparent">
            {isOpen ? <ChevronUpIcon className="w-5 h-5" /> : <ChevronDownIcon className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Dropdown — mini-fiche + saisie pages si "En cours" */}
      {isOpen && (
        <div className="ml-6 mr-2 mb-2 bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-600 space-y-3">
          <div>
            <h4 className="text-sm font-semibold text-gray-900 dark:text-white">{tomeInfo.title}</h4>
            <p className="text-xs text-gray-500 dark:text-gray-400">Tome {tomeNumber} · {seriesData?.name}</p>
          </div>

          {unreleased && (
            <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900 dark:border-amber-700/50 dark:bg-amber-900/20 dark:text-amber-100">
              Ce volume n&apos;est pas encore sorti — il apparaît dans l&apos;onglet À venir. Impossible de le marquer comme lu pour l&apos;instant.
            </div>
          )}

          {/* Pages en cours */}
          {!unreleased && (
          <div className={`flex items-center gap-2 p-2 rounded-lg border transition-colors ${
            isInProgress ? 'border-blue-300 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-700' : 'border-gray-200 dark:border-gray-600'
          }`}>
            <BookOpenIcon className="w-4 h-4 text-blue-500 flex-shrink-0" />
            <span className="text-xs text-gray-600 dark:text-gray-400 flex-shrink-0">Page actuelle :</span>
            <input
              type="number"
              min={1}
              max={tomeInfo.pages || 9999}
              value={pageInput}
              onChange={e => setPageInput(e.target.value)}
              placeholder={tomeInfo.pages ? `/ ${tomeInfo.pages}` : 'optionnel'}
              className="w-20 text-xs px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-1 focus:ring-blue-500 focus:outline-none"
            />
            {tomeInfo.pages && <span className="text-xs text-gray-400">/ {tomeInfo.pages}</span>}
            <button
              onClick={() => { handleStatusChange('en_cours'); }}
              className="ml-auto text-xs px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
            >
              Enregistrer
            </button>
          </div>
          )}

          {/* Infos techniques */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            {tomeInfo.pages && (
              <div className="flex items-center gap-1">
                <DocumentTextIcon className="w-3 h-3 text-blue-500" />
                <span className="text-gray-600 dark:text-gray-400">{tomeInfo.pages} pages</span>
              </div>
            )}
            {readingTime && (
              <div className="flex items-center gap-1">
                <BookOpenIcon className="w-3 h-3 text-green-500" />
                <span className="text-gray-600 dark:text-gray-400">{readingTime}</span>
              </div>
            )}
            {tomeInfo.published_year && (
              <div className="flex items-center gap-1">
                <CalendarIcon className="w-3 h-3 text-purple-500" />
                <span className="text-gray-600 dark:text-gray-400">{tomeInfo.published_year}</span>
              </div>
            )}
            {unreleased ? (
              <div className="flex items-center gap-1">
                <CalendarIcon className="w-3 h-3 text-amber-500" />
                <span className="font-medium text-amber-700 dark:text-amber-300">À paraître</span>
              </div>
            ) : (
              <div className="flex items-center gap-1">
                <div className={`w-2 h-2 rounded-full ${cfg.dot}`} />
                <span className={`font-medium ${cfg.text}`}>{cfg.label}</span>
              </div>
            )}
          </div>

          {tomeInfo.description && (
            <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed">{tomeInfo.description}</p>
          )}

          {(tomeInfo.publisher || tomeInfo.isbn) && (
            <div className="pt-2 border-t border-gray-200 dark:border-gray-600 space-y-0.5 text-xs text-gray-500">
              {tomeInfo.publisher && <p><span className="font-medium">Éditeur :</span> {tomeInfo.publisher}</p>}
              {tomeInfo.isbn && <p><span className="font-medium">ISBN :</span> {tomeInfo.isbn}</p>}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TomeDropdown;
