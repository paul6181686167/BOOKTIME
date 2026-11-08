import { API_BASE_URL } from '../config/environment';
import { getToken } from './apiClient';

const REQUEST_TIMEOUT_MS = 60000;

async function request(method, path, body) {
  const token = getToken();
  // Le serveur gratuit peut mettre une minute à se réveiller : on abandonne ensuite proprement
  // (au lieu d'un chargement sans fin) pour que l'écran puisse proposer « Réessayer ».
  const controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
  const timer = controller ? setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS) : null;
  let res;
  try {
    res = await fetch(`${API_BASE_URL}/api/friends${path}`, {
      method,
      headers: {
        ...(body ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
      signal: controller?.signal,
    });
  } catch (err) {
    if (err?.name === 'AbortError') {
      throw new Error('Le serveur met trop de temps à répondre. Réessaie dans un instant.');
    }
    throw new Error('Connexion impossible. Vérifie ton réseau et réessaie.');
  } finally {
    if (timer) clearTimeout(timer);
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail =
      typeof data.detail === 'string' ? data.detail : data.detail?.[0]?.msg || 'Action impossible';
    throw new Error(detail);
  }
  return data;
}

const friendsService = {
  search: (q) => request('GET', `/search?q=${encodeURIComponent(q)}`),
  myCode: () => request('GET', '/me/code'),
  byCode: (code) => request('GET', `/by-code/${encodeURIComponent(code)}`),
  sendRequest: (userId) => request('POST', '/requests', { user_id: userId }),
  listRequests: () => request('GET', '/requests'),
  acceptRequest: (requestId) => request('POST', `/requests/${requestId}/accept`),
  declineRequest: (requestId) => request('DELETE', `/requests/${requestId}`),
  listFriends: () => request('GET', ''),
  unreadSummary: () => request('GET', '/unread'),
  removeFriend: (userId) => request('DELETE', `/${userId}`),
  getProfile: (userId) => request('GET', `/${userId}/profile`),
  getMessages: (userId, after) =>
    request('GET', `/${userId}/messages${after ? `?after=${encodeURIComponent(after)}` : ''}`),
  sendMessage: (userId, { text, book }) => request('POST', `/${userId}/messages`, { text, book }),
};

export default friendsService;

/** Livre d'une bibliothèque ou d'un profil -> référence légère envoyée dans un message. */
export function toBookRef(book) {
  if (!book) return null;
  return {
    title: book.display_title || book.title || '',
    author: book.author || '',
    cover_url: book.cover_url || book.cover_image_url || '',
    category: book.category || 'roman',
    ol_key: book.ol_key || '',
    isbn: book.isbn || '',
  };
}

/** Référence reçue -> objet livre affichable dans la fiche (livre à découvrir, pas encore possédé). */
export function bookRefToBookLike(ref) {
  const key = ref.ol_key || ref.isbn || `${ref.title}|${ref.author}`;
  return {
    id: `friend_${key}`,
    title: ref.title,
    author: ref.author || 'Auteur inconnu',
    category: ref.category || 'roman',
    cover_url: ref.cover_url || '',
    ol_key: ref.ol_key || undefined,
    isbn: ref.isbn || '',
    description: ref.description || '',
    total_pages: ref.total_pages || null,
    isFromOpenLibrary: true,
  };
}
