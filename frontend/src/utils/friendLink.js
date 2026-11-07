// Lien de partage de profil : https://<site>/ami/<CODE>
// Le même texte est encodé dans le QR code et envoyé par le bouton Partager.

const DEFAULT_WEB_URL = 'https://booktime-fawn.vercel.app';
const FRIEND_CODE_RE = /^[ABCDEFGHJKMNPQRSTUVWXYZ23456789]{8}$/;

export function publicWebUrl() {
  const fromEnv = process.env.REACT_APP_PUBLIC_WEB_URL;
  return String(fromEnv || DEFAULT_WEB_URL).replace(/\/+$/, '');
}

/** Code en majuscules sans espaces ni tirets, ou '' s'il n'est pas valide. */
export function normalizeFriendCode(raw) {
  const code = String(raw || '').replace(/[\s-]/g, '').toUpperCase();
  return FRIEND_CODE_RE.test(code) ? code : '';
}

export function buildFriendLink(code) {
  return `${publicWebUrl()}/ami/${normalizeFriendCode(code)}`;
}

/** Code lisible : ABCD-2345 */
export function formatFriendCode(code) {
  const clean = normalizeFriendCode(code);
  return clean ? `${clean.slice(0, 4)}-${clean.slice(4)}` : '';
}

/**
 * Retrouve un code d'ami dans un texte scanné ou collé :
 * lien /ami/CODE (n'importe quel domaine), ?ami=CODE, ou code seul.
 */
export function parseFriendCode(text) {
  const value = String(text || '').trim();
  if (!value) return '';
  const fromPath = value.match(/\/ami\/([A-Za-z0-9-]+)/i);
  if (fromPath) return normalizeFriendCode(fromPath[1]);
  const fromQuery = value.match(/[?&]ami=([A-Za-z0-9-]+)/i);
  if (fromQuery) return normalizeFriendCode(fromQuery[1]);
  return normalizeFriendCode(value);
}

export const PENDING_FRIEND_CODE_KEY = 'booktime_pending_friend_code';
