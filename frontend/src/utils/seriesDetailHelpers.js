/** Fonctions pures de la fiche série (identifiants, volumes, libellés de statut). */
import { displayBookTitleFrFirst } from './openLibraryBookDisplay';

export const isPersistedLibraryId = (id) =>
  id &&
  typeof id === 'string' &&
  !id.startsWith('ol_') &&
  !id.startsWith('series_') &&
  !id.startsWith('jikan_') &&
  !id.startsWith('gbooks_');


export function parseVolumeFromWork(vol) {
  if (vol == null || vol === '') return null;
  const m = String(vol).match(/\d+/);
  if (!m) return null;
  const n = parseInt(m[0], 10);
  return Number.isNaN(n) ? null : n;
}

/** volumes peut être un nombre (référentiel) ou un tableau (série bibliothèque). */
export function resolveVolumesCount(volumes, fallback = 0) {
  if (typeof volumes === 'number' && Number.isFinite(volumes)) return volumes;
  if (Array.isArray(volumes)) return volumes.length;
  return fallback;
}

export function volumeTitlesFromLibraryVolumes(volumes) {
  if (!Array.isArray(volumes)) return null;
  const map = {};
  volumes.forEach((v, i) => {
    const num = v?.volume_number ?? i + 1;
    map[num] = v?.volume_title || v?.title || `Tome ${num}`;
  });
  return Object.keys(map).length ? map : null;
}

export function normalizeSeriesVolumesField(seriesData) {
  if (!seriesData || !Array.isArray(seriesData.volumes)) return seriesData;
  return {
    ...seriesData,
    volumes: seriesData.volumes.length,
    volume_titles:
      seriesData.volume_titles || volumeTitlesFromLibraryVolumes(seriesData.volumes) || {},
  };
}

export function mapStaticWikidataWorksToOlBooks(works) {
  return (works || []).map((w, i) => {
    const titleFr = w.title_fr || '';
    const titleEn = w.title_en || '';
    const primary = titleFr || titleEn || 'Œuvre';
    const vn = parseVolumeFromWork(w.volume);
    return {
      title: primary,
      display_title: displayBookTitleFrFirst({
        title: primary,
        original_title: titleFr && titleEn && titleFr !== titleEn ? titleEn : undefined,
      }),
      volume_number: vn != null ? vn : i + 1,
      first_publish_year: w.publication_date ? parseInt(String(w.publication_date).slice(0, 4), 10) : null,
      cover_url: null,
      ol_key: null,
      work_qid: w.work_qid,
      isFromStaticWikidata: true,
    };
  });
}

export const getStatusBadge = (status) => {
  switch (status) {
    case 'completed':
      return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300';
    case 'reading':
      return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
  }
};

export const getStatusLabel = (status) => {
  switch (status) {
    case 'completed': return 'Lu';
    case 'reading': return 'En cours';
    default: return 'Non lu';
  }
};
