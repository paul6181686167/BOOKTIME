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
 * Réseaux et messageries proposés pour envoyer le lien de profil.
 * Chaque cible est un simple lien (ouvre l'application, ou son site si elle n'est pas installée).
 * Instagram, Signal… n'ont pas de lien de partage web : ils passent par « Autres applications ».
 */
export function socialShareTargets({ text, url, title = 'Mon profil Booktime' }) {
  const message = `${text} ${url}`.trim();
  const enc = encodeURIComponent;
  return [
    { id: 'whatsapp', label: 'WhatsApp', color: '#25D366', href: `https://wa.me/?text=${enc(message)}` },
    {
      id: 'telegram',
      label: 'Telegram',
      color: '#229ED9',
      href: `https://t.me/share/url?url=${enc(url)}&text=${enc(text)}`,
    },
    {
      id: 'facebook',
      label: 'Facebook',
      color: '#1877F2',
      href: `https://www.facebook.com/sharer/sharer.php?u=${enc(url)}`,
    },
    {
      id: 'x',
      label: 'X',
      color: '#111827',
      href: `https://twitter.com/intent/tweet?text=${enc(text)}&url=${enc(url)}`,
    },
    { id: 'sms', label: 'SMS', color: '#16A34A', href: `sms:?&body=${enc(message)}` },
    {
      id: 'email',
      label: 'E-mail',
      color: '#6B7280',
      href: `mailto:?subject=${enc(title)}&body=${enc(message)}`,
    },
  ];
}

/** Vrai si l'appareil sait ouvrir sa propre feuille de partage (toutes les applications installées). */
export function canUseSystemShare() {
  if (typeof window === 'undefined') return false;
  return Boolean(window.Capacitor?.isNativePlatform?.()) || typeof navigator?.share === 'function';
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
