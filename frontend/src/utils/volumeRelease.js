/**
 * Détecte si un tome d'une série n'est pas encore sorti.
 * S'appuie sur volume_details du référentiel curé (published_year / publish_date / released).
 */

function _todayIso() {
  return new Date().toISOString().slice(0, 10);
}

/**
 * @param {object} seriesData - série enrichie (volume_details, volumes…)
 * @param {number} tomeNumber
 * @returns {boolean}
 */
export function isVolumeUnreleased(seriesData, tomeNumber) {
  const details = seriesData?.volume_details;
  if (!details || typeof details !== 'object') return false;

  const d = details[tomeNumber] ?? details[String(tomeNumber)];
  if (!d || typeof d !== 'object') return false;

  if (d.released === false) return true;
  if (d.released === true) return false;

  if (d.publish_date) {
    const iso = String(d.publish_date).slice(0, 10);
    if (/^\d{4}-\d{2}-\d{2}$/.test(iso)) {
      return iso > _todayIso();
    }
  }

  // Entrée explicite avec année absente = annoncé mais pas sorti (ex. Red God)
  if ('published_year' in d) {
    if (d.published_year == null || d.published_year === '') return true;
    const y = Number(d.published_year);
    if (!Number.isNaN(y) && y > new Date().getFullYear()) return true;
  }

  return false;
}

/**
 * Nombre de tomes déjà sortis (pour le statut « terminé » de la série).
 */
export function countReleasedVolumes(seriesData, totalFallback = 0) {
  const total =
    typeof seriesData?.volumes === 'number'
      ? seriesData.volumes
      : Number(totalFallback) || 0;
  if (total <= 0) return 0;
  let n = 0;
  for (let i = 1; i <= total; i++) {
    if (!isVolumeUnreleased(seriesData, i)) n += 1;
  }
  return n;
}
