/**
 * Configuration Multi-Environnement BOOKTIME
 * Détection automatique Preview Emergent / Vercel Fullstack / Local Development
 */

/**
 * Détection intelligente URL backend selon environnement
 */
const getBackendURL = () => {
  // Preview Emergent - utilise même domaine (backend et frontend sur même URL)
  if (window.location.hostname.includes('emergentagent.com')) {
    console.log('🌍 Environment: Emergent Preview');
    return window.location.origin;
  }

  // Production : Railway backend URL fournie via variable d'environnement Vercel
  // Définie dans le dashboard Vercel : REACT_APP_BACKEND_URL = https://xxxx.up.railway.app
  if (process.env.REACT_APP_BACKEND_URL) {
    console.log('🌍 Environment: Production (Railway backend)');
    return process.env.REACT_APP_BACKEND_URL;
  }

  // Development local - URL directe backend pour éviter 405 (proxy) et 500
  console.log('🌍 Environment: Local Development (backend direct)');
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

/**
 * Configuration debugging
 */
if (!IS_PRODUCTION) {
  console.log('🔗 Backend URL:', API_BASE_URL);
  console.log('🌍 Environment:', ENVIRONMENT);
  console.log('📡 API Endpoints:', API_ENDPOINTS);
}

/**
 * Test connectivité backend au chargement
 */
export const checkBackendHealth = async () => {
  try {
    const response = await fetch(API_ENDPOINTS.HEALTH);
    const data = await response.json();
    console.log('✅ Backend Health:', data);
    return data;
  } catch (error) {
    console.error('❌ Backend Health Check Failed:', error);
    return { status: 'error', error: error.message };
  }
};

// Test automatique en development
if (IS_DEVELOPMENT) {
  setTimeout(checkBackendHealth, 2000);
}

export default {
  API_BASE_URL,
  API_ENDPOINTS,
  ENVIRONMENT,
  IS_PRODUCTION,
  IS_DEVELOPMENT,
  checkBackendHealth
};