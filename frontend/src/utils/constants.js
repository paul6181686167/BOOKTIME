// Constantes globales pour l'application BOOKTIME

// Catégories de livres
export const BOOK_CATEGORIES = {
  ROMAN: 'roman',
  BD: 'bd',
  MANGA: 'manga'
};

// Statuts de livres
export const BOOK_STATUSES = {
  TO_READ: 'to_read',
  READING: 'reading',
  COMPLETED: 'completed'
};

// Configuration des badges de catégorie
export const CATEGORY_BADGES = {
  [BOOK_CATEGORIES.ROMAN]: {
    key: 'roman',
    text: 'Roman',
    class: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300',
    emoji: '📚'
  },
  [BOOK_CATEGORIES.BD]: {
    key: 'bd',
    text: 'BD',
    class: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300',
    emoji: '🎨'
  },
  [BOOK_CATEGORIES.MANGA]: {
    key: 'manga',
    text: 'Manga',
    class: 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-300',
    emoji: '🇯🇵'
  }
};

// Configuration des statuts
export const STATUS_CONFIG = {
  [BOOK_STATUSES.TO_READ]: {
    label: 'À lire',
    color: 'gray',
    emoji: '📖'
  },
  [BOOK_STATUSES.READING]: {
    label: 'En cours',
    color: 'yellow',
    emoji: '📚'
  },
  [BOOK_STATUSES.COMPLETED]: {
    label: 'Terminé',
    color: 'green',
    emoji: '✅'
  }
};

// Configuration des onglets de navigation
export const TAB_CONFIG = [
  {
    key: BOOK_CATEGORIES.ROMAN,
    label: '📚 Romans',
    emoji: '📚'
  },
  {
    key: BOOK_CATEGORIES.BD,
    label: 'Bandes dessinées',
    emoji: ''
  },
  {
    key: BOOK_CATEGORIES.MANGA,
    label: 'Mangas',
    emoji: ''
  }
];

// Configuration de recherche
export const SEARCH_CONFIG = {
  MIN_SEARCH_LENGTH: 2,
  SEARCH_DEBOUNCE_DELAY: 300,
  MAX_RESULTS_PER_PAGE: 20,
  DEFAULT_LIMIT: 10
};

// Configuration des toasts
export const TOAST_CONFIG = {
  duration: 3000,
  position: 'bottom-right'
};

// Messages d'erreur fréquents
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Erreur de connexion. Veuillez réessayer.',
  BOOK_NOT_FOUND: 'Livre non trouvé.',
  INVALID_DATA: 'Données invalides.',
  SERVER_ERROR: 'Erreur serveur. Veuillez réessayer plus tard.',
  UNAUTHORIZED: 'Accès non autorisé. Veuillez vous reconnecter.'
};

// Messages de succès
export const SUCCESS_MESSAGES = {
  BOOK_ADDED: 'Livre ajouté avec succès !',
  BOOK_UPDATED: 'Livre mis à jour avec succès !',
  BOOK_DELETED: 'Livre supprimé avec succès !',
  SERIES_ADDED: 'Série ajoutée avec succès !',
  PROFILE_UPDATED: 'Profil mis à jour avec succès !'
};

// Configuration de l'API
export const API_CONFIG = {
  BASE_URL: process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001',
  TIMEOUT: 10000,
  RETRY_ATTEMPTS: 3
};

// Configuration des thèmes
export const THEME_CONFIG = {
  LIGHT: 'light',
  DARK: 'dark',
  SYSTEM: 'system'
};

// Configuration des langues
export const LANGUAGE_CONFIG = {
  DEFAULT: 'fr',
  SUPPORTED: ['fr', 'en', 'es', 'de', 'it']
};

// Configuration des formats de date
export const DATE_FORMATS = {
  DISPLAY: 'DD/MM/YYYY',
  API: 'YYYY-MM-DD',
  DATETIME: 'DD/MM/YYYY HH:mm'
};

// Configuration des animations
export const ANIMATION_CONFIG = {
  DURATION: 200,
  EASE: 'ease-in-out'
};

// Configuration des grilles
export const GRID_CONFIG = {
  COLS: {
    DEFAULT: 1,
    SM: 2,
    MD: 3,
    LG: 4,
    XL: 5
  },
  GAP: 4
};

// Configuration des modales
export const MODAL_CONFIG = {
  ANIMATION_DURATION: 200,
  BACKDROP_OPACITY: 0.5,
  Z_INDEX: 1000
};

// Configuration des scores de pertinence
export const RELEVANCE_CONFIG = {
  THRESHOLDS: {
    HIGH: 100000,
    MEDIUM: 1000,
    LOW: 100
  },
  LABELS: {
    HIGH: 'Très pertinent',
    MEDIUM: 'Pertinent',
    LOW: 'Peu pertinent'
  }
};