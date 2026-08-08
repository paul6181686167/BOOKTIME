// Fonctions utilitaires pour l'application BOOKTIME

import { CATEGORY_BADGES, STATUS_CONFIG, ERROR_MESSAGES } from './constants';

/**
 * Obtient le badge de catégorie pour un livre
 * @param {Object} book - Livre avec propriété category
 * @returns {Object} Badge de catégorie
 */
export const getCategoryBadge = (book) => {
  if (!book) return CATEGORY_BADGES.roman;
  
  const category = book.category?.toLowerCase();
  if (category && CATEGORY_BADGES[category]) {
    return CATEGORY_BADGES[category];
  }
  
  // Heuristiques prudentes : pas de japan/bd en sous-chaîne (faux positifs)
  const title = (book.title || '').toLowerCase();
  const subjects = (book.subjects || []).join(' ').toLowerCase();
  const description = ((book.description || '').slice(0, 200)).toLowerCase();
  const allText = `${title} ${subjects} ${description}`;

  if (/\b(manga|manhwa|manhua|webtoon|shonen|shounen|seinen|josei|shojo)\b/i.test(allText)) {
    return CATEGORY_BADGES.manga;
  }

  if (
    /\b(comic books?|comic strips?|graphic novels?|roman graphique|bande dessin[ée]e|fumetti)\b/i.test(
      allText
    )
  ) {
    return CATEGORY_BADGES.bd;
  }

  return CATEGORY_BADGES.roman;
};

/**
 * Obtient la configuration d'un statut
 * @param {string} status - Statut du livre
 * @returns {Object} Configuration du statut
 */
export const getStatusConfig = (status) => {
  return STATUS_CONFIG[status] || STATUS_CONFIG.to_read;
};

/**
 * Formate une date pour l'affichage
 * @param {string|Date} date - Date à formater
 * @param {string} format - Format de sortie ('short', 'long', 'relative')
 * @returns {string} Date formatée
 */
export const formatDate = (date, format = 'short') => {
  if (!date) return '';
  
  const dateObj = new Date(date);
  if (isNaN(dateObj.getTime())) return '';
  
  const now = new Date();
  const diffTime = now - dateObj;
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
  
  switch (format) {
    case 'relative':
      if (diffDays === 0) return 'Aujourd\'hui';
      if (diffDays === 1) return 'Hier';
      if (diffDays < 7) return `Il y a ${diffDays} jours`;
      if (diffDays < 30) return `Il y a ${Math.floor(diffDays / 7)} semaines`;
      if (diffDays < 365) return `Il y a ${Math.floor(diffDays / 30)} mois`;
      return `Il y a ${Math.floor(diffDays / 365)} ans`;
    
    case 'long':
      return dateObj.toLocaleDateString('fr-FR', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    
    case 'short':
    default:
      return dateObj.toLocaleDateString('fr-FR');
  }
};

/**
 * Tronque un texte à une longueur donnée
 * @param {string} text - Texte à tronquer
 * @param {number} maxLength - Longueur maximale
 * @param {string} suffix - Suffixe à ajouter ('...' par défaut)
 * @returns {string} Texte tronqué
 */
export const truncateText = (text, maxLength = 100, suffix = '...') => {
  if (!text || text.length <= maxLength) return text || '';
  return text.substring(0, maxLength).trim() + suffix;
};

/**
 * Capitalise la première lettre d'un texte
 * @param {string} text - Texte à capitaliser
 * @returns {string} Texte capitalisé
 */
export const capitalize = (text) => {
  if (!text) return '';
  return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
};

/**
 * Nettoie et normalise un nom d'auteur
 * @param {string} author - Nom de l'auteur
 * @returns {string} Nom nettoyé
 */
export const cleanAuthorName = (author) => {
  if (!author) return '';
  
  return author
    .trim()
    .replace(/\s+/g, ' ')
    .replace(/,+/g, ',')
    .replace(/^,|,$/, '')
    .trim();
};

/**
 * Génère un ID unique simple
 * @returns {string} ID unique
 */
export const generateId = () => {
  return Math.random().toString(36).substring(2, 15) + 
         Math.random().toString(36).substring(2, 15);
};

/**
 * Débounce une fonction
 * @param {Function} func - Fonction à débouncer
 * @param {number} delay - Délai en millisecondes
 * @returns {Function} Fonction débouncée
 */
export const debounce = (func, delay) => {
  let timeoutId;
  return function (...args) {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func.apply(this, args), delay);
  };
};

/**
 * Vérifie si une chaîne est vide ou ne contient que des espaces
 * @param {string} str - Chaîne à vérifier
 * @returns {boolean} True si vide
 */
export const isEmpty = (str) => {
  return !str || str.trim().length === 0;
};

/**
 * Normalise une chaîne pour la recherche (supprime accents, ponctuation)
 * @param {string} str - Chaîne à normaliser
 * @returns {string} Chaîne normalisée
 */
export const normalizeForSearch = (str) => {
  if (!str) return '';
  
  return str
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^\w\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
};

/**
 * Calcule le pourcentage de progression d'un livre
 * @param {number} currentPage - Page actuelle
 * @param {number} totalPages - Total de pages
 * @returns {number} Pourcentage (0-100)
 */
export const calculateProgress = (currentPage, totalPages) => {
  if (!totalPages || totalPages <= 0) return 0;
  if (!currentPage || currentPage <= 0) return 0;
  
  const progress = Math.round((currentPage / totalPages) * 100);
  return Math.min(progress, 100);
};

/**
 * Formate un nombre avec séparateurs de milliers
 * @param {number} number - Nombre à formater
 * @returns {string} Nombre formaté
 */
export const formatNumber = (number) => {
  if (typeof number !== 'number' || isNaN(number)) return '0';
  return number.toLocaleString('fr-FR');
};

/**
 * Gère les erreurs de façon cohérente
 * @param {Error} error - Erreur à traiter
 * @param {string} context - Contexte de l'erreur
 * @returns {string} Message d'erreur formaté
 */
export const handleError = (error, context = '') => {
  console.error(`Error in ${context}:`, error);
  
  if (error.message) {
    if (error.message.includes('Network') || error.message.includes('fetch')) {
      return ERROR_MESSAGES.NETWORK_ERROR;
    }
    if (error.message.includes('401') || error.message.includes('Unauthorized')) {
      return ERROR_MESSAGES.UNAUTHORIZED;
    }
    if (error.message.includes('404')) {
      return ERROR_MESSAGES.BOOK_NOT_FOUND;
    }
    if (error.message.includes('400')) {
      return ERROR_MESSAGES.INVALID_DATA;
    }
  }
  
  return ERROR_MESSAGES.SERVER_ERROR;
};

/**
 * Vérifie si un objet est vide
 * @param {Object} obj - Objet à vérifier
 * @returns {boolean} True si vide
 */
export const isEmptyObject = (obj) => {
  return !obj || Object.keys(obj).length === 0;
};

/**
 * Copie un objet en profondeur
 * @param {Object} obj - Objet à copier
 * @returns {Object} Copie de l'objet
 */
export const deepCopy = (obj) => {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj);
  if (obj instanceof Array) return obj.map(item => deepCopy(item));
  if (typeof obj === 'object') {
    const copy = {};
    Object.keys(obj).forEach(key => {
      copy[key] = deepCopy(obj[key]);
    });
    return copy;
  }
  return obj;
};

/**
 * Extrait les initiales d'un nom
 * @param {string} firstName - Prénom
 * @param {string} lastName - Nom
 * @returns {string} Initiales (ex: "JD")
 */
export const getInitials = (firstName, lastName) => {
  const first = firstName?.charAt(0)?.toUpperCase() || '';
  const last = lastName?.charAt(0)?.toUpperCase() || '';
  return `${first}${last}`;
};

/**
 * Convertit un slug en titre lisible
 * @param {string} slug - Slug à convertir
 * @returns {string} Titre lisible
 */
export const slugToTitle = (slug) => {
  if (!slug) return '';
  
  return slug
    .split('-')
    .map(word => capitalize(word))
    .join(' ');
};

/**
 * Convertit un titre en slug
 * @param {string} title - Titre à convertir
 * @returns {string} Slug
 */
export const titleToSlug = (title) => {
  if (!title) return '';
  
  return normalizeForSearch(title)
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
};

/**
 * Vérifie si une URL est valide
 * @param {string} url - URL à vérifier
 * @returns {boolean} True si valide
 */
export const isValidUrl = (url) => {
  if (!url) return false;
  
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

/**
 * Combine des classes CSS conditionnellement
 * @param {...string} classes - Classes à combiner
 * @returns {string} Classes combinées
 */
export const classNames = (...classes) => {
  return classes.filter(Boolean).join(' ');
};

/**
 * URL de couverture Open Library à partir d'un livre / document (ol_key, isbn, cover_i).
 * @param {object} entity
 * @returns {string|null}
 */
/** True si l'URL est une vraie couverture (pas placeholder SVG / archive.org). */
export const isUsableCoverUrl = (url) => {
  const u = String(url || '').trim();
  if (!u || u.includes('undefined')) return false;
  if (u.startsWith('data:')) return false;
  if (/\/b\/(?:id|olid)\/OL\d+W/i.test(u)) return false;
  if (/archive\.org/i.test(u)) return false;
  return true;
};

/** Réécrit archive.org / -L.jpg vers le CDN OL -M (plus rapide). */
export const normalizeCoverUrl = (url) => {
  let u = String(url || '').trim();
  if (!u) return '';
  u = u.replace('http://', 'https://');
  // Google Books : les query params (id, printsec, img…) sont obligatoires
  if (/books\.google\./i.test(u) || /googleusercontent\.com/i.test(u)) {
    u = u.replace(/([?&])zoom=\d/i, '$1zoom=0');
    if (!/[?&]edge=/.test(u)) u += (u.includes('?') ? '&' : '?') + 'edge=curl';
    return u;
  }
  if (/archive\.org/i.test(u)) {
    const arch = u.match(/(?:\/|=)(\d+)-[LM]\.jpe?g/i);
    if (arch) return `https://covers.openlibrary.org/b/id/${arch[1]}-M.jpg`;
    return '';
  }
  u = u.replace(
    /(covers\.openlibrary\.org\/b\/(?:id|olid|isbn)\/[^/?]+)-[LS]\.jpe?g/i,
    '$1-M.jpg'
  );
  return u.split('?')[0];
};

/** Params wsrv : vignette légère (grille ≈ 110–180px CSS, 2× ≈ 220–360). */
const COVER_PROXY_PARAMS = 'w=200&q=72&output=webp&n=-1&maxage=31d';

const viaWsrv = (hostPathOrUrl) => {
  const hostPath = String(hostPathOrUrl || '')
    .replace(/^https?:\/\//i, '')
    .replace(/^\/\//, '');
  if (!hostPath) return '';
  return `https://wsrv.nl/?url=${encodeURIComponent(hostPath)}&${COVER_PROXY_PARAMS}`;
};

/**
 * src <img> : proxy wsrv.nl pour OL / Wikimedia / GB (latence FR + cache CDN).
 * WebP + 200px : ~3–5× plus léger que l’ancien JPG 280px.
 */
export const coverImgSrc = (url) => {
  const raw = String(url || '').trim();
  if (!raw) return '';

  if (/books\.google\./i.test(raw) || /googleusercontent\.com/i.test(raw)) {
    let n = raw.replace('http://', 'https://');
    n = n.replace(/([?&])zoom=\d/i, '$1zoom=0');
    if (!/[?&]edge=/.test(n)) n += (n.includes('?') ? '&' : '?') + 'edge=curl';
    return viaWsrv(n);
  }

  let n = normalizeCoverUrl(raw);
  if (!n) return '';

  if (/covers\.openlibrary\.org/i.test(n)) {
    const bare = n.split('?')[0];
    const hostPath = bare.replace(/^https?:\/\//i, '');
    const proxied = `${hostPath}${hostPath.includes('?') ? '&' : '?'}default=false`;
    return viaWsrv(proxied);
  }

  if (/upload\.wikimedia\.org/i.test(n)) {
    return viaWsrv(n);
  }

  return n;
};

/** true si l'image Google Books a besoin d'un referrer « normal ». */
export const coverNeedsReferrer = (url) =>
  /books\.google\./i.test(url || '') || /googleusercontent\.com/i.test(url || '');

/** Google Books sert souvent le faux « image not available ». */
export const isGoogleBooksCoverUrl = (url) =>
  /books\.google\./i.test(url || '') || /googleusercontent\.com/i.test(url || '');

/**
 * Photo (célèbre / auteur) plutôt qu’une couverture livre (ratio ~2:3).
 * Pas besoin de CORS : naturalWidth/Height suffisent.
 */
export const isLikelyPhotoNotCover = (img) => {
  if (!img) return true;
  const w = img.naturalWidth;
  const h = img.naturalHeight;
  if (!(w > 0 && h > 0)) return true;
  const ratio = w / h;
  // Couverture typique ≈ 0.62–0.75 ; portrait photo / paysage / carré wiki → hors plage
  if (ratio > 0.86 || ratio < 0.42) return true;
  return false;
};

/**
 * Détecte les fausses couvertures Google « image not available »
 * (coins gris clairs ; le texte au centre fausse une moyenne globale).
 */
export const isBlankOrPlaceholderCover = (img) => {
  if (!img) return true;
  const w = img.naturalWidth;
  const h = img.naturalHeight;
  if (!(w > 0 && h > 0)) return true;
  if (w < 40 || h < 40) return true;
  try {
    const tw = 32;
    const th = 32;
    const canvas = document.createElement('canvas');
    canvas.width = tw;
    canvas.height = th;
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    if (!ctx) return false;
    ctx.drawImage(img, 0, 0, tw, th);
    const { data } = ctx.getImageData(0, 0, tw, th);
    const isLightGray = (i) => {
      const r = data[i];
      const g = data[i + 1];
      const b = data[i + 2];
      const avg = (r + g + b) / 3;
      return Math.abs(r - g) < 18 && Math.abs(g - b) < 18 && avg > 160 && avg < 250;
    };
    // Coins uniquement (évite le texte « image not available » au centre)
    const corners = [
      0,
      (tw - 1) * 4,
      (th - 1) * tw * 4,
      ((th - 1) * tw + (tw - 1)) * 4,
      (2 * tw + 2) * 4,
      (2 * tw + (tw - 3)) * 4,
    ];
    const cornerHits = corners.filter((i) => isLightGray(i)).length;
    if (cornerHits >= 5) return true;

    let lightGray = 0;
    const total = tw * th;
    for (let i = 0; i < data.length; i += 4) {
      if (isLightGray(i)) lightGray += 1;
    }
    return lightGray / total > 0.65;
  } catch (_) {
    return false;
  }
};

export const resolveOpenLibraryCoverUrl = (entity) => {
  if (!entity || typeof entity !== 'object') return null;

  // Couvertures invalides fréquentes : /b/id/OL…W (clé work ≠ id numérique)
  const isInvalidOlCover = (url) =>
    /\/b\/(?:id|olid)\/OL\d+W/i.test(url) || /\/b\/id\/\d{10,13}-/i.test(url);

  const rawCover = entity.cover_url || entity.cover_image_url;
  if (rawCover && String(rawCover).trim() && !String(rawCover).includes('undefined')) {
    const url = normalizeCoverUrl(rawCover);
    if (url && !isInvalidOlCover(url) && isUsableCoverUrl(url)) return url;
  }
  if (entity.cover_i != null && Number.isFinite(Number(entity.cover_i))) {
    return `https://covers.openlibrary.org/b/id/${Number(entity.cover_i)}-M.jpg`;
  }
  let raw = entity.ol_key || entity.open_library_key || entity.work_key || entity.openlibrary_key || '';
  if (!raw && typeof entity.id === 'string' && entity.id.startsWith('ol_')) {
    raw = entity.id.replace(/^ol_/, '/works/');
  }
  raw = String(raw);
  // Les covers /b/olid/ marchent pour les éditions (OL…M), pas les works (OL…W)
  const edition = raw.match(/(OL\d+M)\b/i);
  if (edition) {
    return `https://covers.openlibrary.org/b/olid/${edition[1]}-M.jpg`;
  }
  let isbn = entity.isbn || entity.isbn13 || entity.isbn10;
  if (Array.isArray(isbn)) isbn = isbn[0];
  isbn = String(isbn || '').replace(/[^0-9X]/gi, '');
  if (isbn.length >= 10) {
    return `https://covers.openlibrary.org/b/isbn/${isbn}-M.jpg`;
  }
  return null;
};

/** Chaîne de secours si la 1ʳᵉ URL échoue au chargement. */
export const coverFallbackCandidates = (entity) => {
  if (!entity) return [];
  const out = [];
  const push = (u) => {
    const n = normalizeCoverUrl(u);
    if (n && isUsableCoverUrl(n) && !out.includes(n)) out.push(n);
  };
  push(entity.cover_url);
  push(entity.cover_image_url);
  const primary = resolveOpenLibraryCoverUrl(entity);
  if (primary) push(primary);
  let isbn = entity.isbn || entity.isbn13 || entity.isbn10;
  if (Array.isArray(isbn)) isbn = isbn[0];
  isbn = String(isbn || '').replace(/[^0-9X]/gi, '');
  if (isbn.length >= 10) push(`https://covers.openlibrary.org/b/isbn/${isbn}-M.jpg`);
  if (entity.cover_i != null) {
    push(`https://covers.openlibrary.org/b/id/${Number(entity.cover_i)}-M.jpg`);
  }
  // Google Books en dernier : souvent le placeholder « image not available »
  const trusted = out.filter((u) => !isGoogleBooksCoverUrl(u));
  const google = out.filter((u) => isGoogleBooksCoverUrl(u));
  return [...trusted, ...google];
};

/** Couverture pour une carte grille (livre ou série avec books[]). */
export const resolveCoverForGridItem = (item) => {
  if (!item) return null;
  if (item.isSeriesCard) {
    const direct = resolveOpenLibraryCoverUrl({
      ...item,
      cover_url: item.cover_url || item.cover_image_url,
    });
    if (direct) return direct;
    for (const b of item.books || item.volumes || []) {
      if (typeof b !== 'object') continue;
      const c = resolveOpenLibraryCoverUrl(b);
      if (c) return c;
    }
    return null;
  }
  return resolveOpenLibraryCoverUrl(item);
};