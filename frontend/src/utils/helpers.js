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
  
  // Détection automatique basée sur le contenu
  const title = (book.title || '').toLowerCase();
  const description = (book.description || '').toLowerCase();
  const subjects = (book.subjects || []).join(' ').toLowerCase();
  const allText = `${title} ${description} ${subjects}`;
  
  if (allText.includes('manga') || allText.includes('japonais') || allText.includes('japan')) {
    return CATEGORY_BADGES.manga;
  }
  
  if (allText.includes('bande dessinée') || allText.includes('comic') || allText.includes('bd')) {
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