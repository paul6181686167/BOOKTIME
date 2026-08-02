/**
 * Configuration Multi-Environnement BOOKTIME
 * Détection automatique Preview Emergent / Vercel Fullstack / Local Development
 */

/**
 * IP privée LAN (ex. 192.168.x.x) — accès depuis un autre PC du réseau
 */
const isPrivateLanHost = (hostname) =>
  /^(192\.168\.|10\.|172\.(1[6-9]|2\d|3[01])\.)/.test(hostname || '');

/**
 * Détection intelligente URL backend selon environnement
 */
const getBackendURL = () => {
  if (typeof window !== 'undefined' && window.location.hostname.includes('emergentagent.com')) {
    return window.location.origin;
  }
  // Accès LAN : même machine hôte, port backend
  if (typeof window !== 'undefined' && isPrivateLanHost(window.location.hostname)) {
    return `http://${window.location.hostname}:8001`;
  }
  // En dev local : toujours le backend local (évite Render endormi par erreur)
  if (
    typeof window !== 'undefined' &&
    (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
  ) {
    return (
      process.env.REACT_APP_API_URL ||
      process.env.REACT_APP_BACKEND_URL ||
      'http://localhost:8001'
    );
  }
  if (process.env.REACT_APP_BACKEND_URL) {
    return process.env.REACT_APP_BACKEND_URL;
  }
  return process.env.REACT_APP_API_URL || 'http://localhost:8001';
};

/**
 * Configuration environnement principal
 */
export const API_BASE_URL = getBackendURL();
export const ENVIRONMENT = process.env.NODE_ENV || 'development';
export const IS_PRODUCTION = ENVIRONMENT === 'production';
export const IS_DEVELOPMENT = ENVIRONMENT === 'development';

/**
 * URLs API complètes
 */
export const API_ENDPOINTS = {
  AUTH: `${API_BASE_URL}/api/auth`,
  BOOKS: `${API_BASE_URL}/api/books`,
  SERIES: `${API_BASE_URL}/api/series`,
  OPENLIBRARY: `${API_BASE_URL}/api/openlibrary`,
  WIKIPEDIA: `${API_BASE_URL}/api/wikipedia`,
  WIKIDATA: `${API_BASE_URL}/api/wikidata`,
  HEALTH: `${API_BASE_URL}/health`,
  STATS: `${API_BASE_URL}/api/stats`,
  DEPLOYMENT: `${API_BASE_URL}/api/deployment-status`
};

export const checkBackendHealth = async () => {
  try {
    const response = await fetch(API_ENDPOINTS.HEALTH);
    return await response.json();
  } catch (error) {
    return { status: 'error', error: error.message };
  }
};

export default {
  API_BASE_URL,
  API_ENDPOINTS,
  ENVIRONMENT,
  IS_PRODUCTION,
  IS_DEVELOPMENT,
  checkBackendHealth
};