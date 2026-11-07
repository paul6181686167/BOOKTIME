// Partage du lien de profil : feuille de partage native (Android / navigateur mobile),
// sinon copie dans le presse-papiers.

async function copyToClipboard(text) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text);
    return true;
  }
  const area = document.createElement('textarea');
  area.value = text;
  area.setAttribute('readonly', '');
  area.style.position = 'fixed';
  area.style.opacity = '0';
  document.body.appendChild(area);
  area.select();
  let ok = false;
  try {
    ok = document.execCommand('copy');
  } finally {
    document.body.removeChild(area);
  }
  return ok;
}

export async function copyLink(url) {
  return copyToClipboard(url);
}

/**
 * Partage le lien. Retourne 'shared' (feuille de partage), 'copied' (copie de secours),
 * 'cancelled' (l'utilisateur a fermé la feuille) ou 'failed'.
 */
export async function shareLink({ title, text, url }) {
  try {
    const { Capacitor } = await import('@capacitor/core');
    if (Capacitor.isNativePlatform()) {
      const { Share } = await import('@capacitor/share');
      await Share.share({ title, text, url, dialogTitle: title });
      return 'shared';
    }
  } catch (err) {
    if (/cancel/i.test(String(err?.message || err))) return 'cancelled';
  }

  if (typeof navigator !== 'undefined' && navigator.share) {
    try {
      await navigator.share({ title, text, url });
      return 'shared';
    } catch (err) {
      if (err?.name === 'AbortError') return 'cancelled';
    }
  }

  try {
    return (await copyToClipboard(`${text} ${url}`.trim())) ? 'copied' : 'failed';
  } catch (_) {
    return 'failed';
  }
}
