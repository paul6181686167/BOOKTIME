// Validateurs pour l'application BOOKTIME

import { BOOK_CATEGORIES, BOOK_STATUSES } from './constants';

/**
 * Valide un livre
 * @param {Object} book - Livre à valider
 * @returns {Object} Résultat de validation avec isValid et errors
 */
export const validateBook = (book) => {
  const errors = [];
  
  // Titre requis
  if (!book.title || book.title.trim().length === 0) {
    errors.push('Le titre est requis');
  } else if (book.title.trim().length < 2) {
    errors.push('Le titre doit contenir au moins 2 caractères');
  } else if (book.title.length > 200) {
    errors.push('Le titre ne peut pas dépasser 200 caractères');
  }
  
  // Auteur requis
  if (!book.author || book.author.trim().length === 0) {
    errors.push('L\'auteur est requis');
  } else if (book.author.trim().length < 2) {
    errors.push('L\'auteur doit contenir au moins 2 caractères');
  } else if (book.author.length > 100) {
    errors.push('L\'auteur ne peut pas dépasser 100 caractères');
  }
  
  // Catégorie valide
  if (!book.category || !Object.values(BOOK_CATEGORIES).includes(book.category)) {
    errors.push('La catégorie doit être roman, bd ou manga');
  }
  
  // Statut valide
  if (book.status && !Object.values(BOOK_STATUSES).includes(book.status)) {
    errors.push('Le statut doit être to_read, reading ou completed');
  }
  
  // Pages valides
  if (book.pages && (typeof book.pages !== 'number' || book.pages < 1 || book.pages > 10000)) {
    errors.push('Le nombre de pages doit être entre 1 et 10000');
  }
  
  // Page actuelle valide
  if (book.current_page && (typeof book.current_page !== 'number' || book.current_page < 0)) {
    errors.push('La page actuelle doit être un nombre positif');
  }
  
  // Page actuelle ne peut pas dépasser le total
  if (book.current_page && book.pages && book.current_page > book.pages) {
    errors.push('La page actuelle ne peut pas dépasser le nombre total de pages');
  }
  
  // Note valide
  if (book.rating && (typeof book.rating !== 'number' || book.rating < 1 || book.rating > 5)) {
    errors.push('La note doit être entre 1 et 5');
  }
  
  // Année de publication valide
  if (book.publication_year && (typeof book.publication_year !== 'number' || book.publication_year < 1000 || book.publication_year > new Date().getFullYear() + 5)) {
    errors.push('L\'année de publication doit être valide');
  }
  
  // Numéro de volume valide
  if (book.volume_number && (typeof book.volume_number !== 'number' || book.volume_number < 1 || book.volume_number > 1000)) {
    errors.push('Le numéro de volume doit être entre 1 et 1000');
  }
  
  // Avis
  if (book.review && book.review.length > 2000) {
    errors.push('L\'avis ne peut pas dépasser 2000 caractères');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
};

/**
 * Valide une série
 * @param {Object} series - Série à valider
 * @returns {Object} Résultat de validation avec isValid et errors
 */
export const validateSeries = (series) => {
  const errors = [];
  
  // Nom requis
  if (!series.name || series.name.trim().length === 0) {
    errors.push('Le nom de la série est requis');
  } else if (series.name.trim().length < 2) {
    errors.push('Le nom de la série doit contenir au moins 2 caractères');
  } else if (series.name.length > 200) {
    errors.push('Le nom de la série ne peut pas dépasser 200 caractères');
  }
  
  // Auteur requis
  if (!series.author || series.author.trim().length === 0) {
    errors.push('L\'auteur est requis');
  }
  
  // Catégorie valide
  if (!series.category || !Object.values(BOOK_CATEGORIES).includes(series.category)) {
    errors.push('La catégorie doit être roman, bd ou manga');
  }
  
  // Nombre de volumes valide
  if (series.volumes && (typeof series.volumes !== 'number' || series.volumes < 1 || series.volumes > 1000)) {
    errors.push('Le nombre de volumes doit être entre 1 et 1000');
  }
  
  // Description
  if (series.description && series.description.length > 5000) {
    errors.push('La description ne peut pas dépasser 5000 caractères');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
};

/**
 * Valide un utilisateur
 * @param {Object} user - Utilisateur à valider
 * @returns {Object} Résultat de validation avec isValid et errors
 */
export const validateUser = (user) => {
  const errors = [];
  
  // Prénom requis
  if (!user.first_name || user.first_name.trim().length === 0) {
    errors.push('Le prénom est requis');
  } else if (user.first_name.trim().length < 2) {
    errors.push('Le prénom doit contenir au moins 2 caractères');
  } else if (user.first_name.length > 50) {
    errors.push('Le prénom ne peut pas dépasser 50 caractères');
  }
  
  // Nom requis
  if (!user.last_name || user.last_name.trim().length === 0) {
    errors.push('Le nom est requis');
  } else if (user.last_name.trim().length < 2) {
    errors.push('Le nom doit contenir au moins 2 caractères');
  } else if (user.last_name.length > 50) {
    errors.push('Le nom ne peut pas dépasser 50 caractères');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
};

/**
 * Valide une requête de recherche
 * @param {string} query - Requête de recherche
 * @returns {Object} Résultat de validation avec isValid et errors
 */
export const validateSearchQuery = (query) => {
  const errors = [];
  
  if (!query || query.trim().length === 0) {
    errors.push('La requête de recherche ne peut pas être vide');
  } else if (query.trim().length < 2) {
    errors.push('La requête de recherche doit contenir au moins 2 caractères');
  } else if (query.length > 100) {
    errors.push('La requête de recherche ne peut pas dépasser 100 caractères');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
};

/**
 * Valide un email
 * @param {string} email - Email à valider
 * @returns {boolean} True si valide
 */
export const validateEmail = (email) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Valide un URL
 * @param {string} url - URL à valider
 * @returns {boolean} True si valide
 */
export const validateUrl = (url) => {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
};

/**
 * Valide un numéro de téléphone français
 * @param {string} phone - Numéro de téléphone
 * @returns {boolean} True si valide
 */
export const validatePhoneNumber = (phone) => {
  const phoneRegex = /^(?:(?:\+33|0)[1-9](?:[\s.-]?\d{2}){4})$/;
  return phoneRegex.test(phone);
};

/**
 * Valide un mot de passe
 * @param {string} password - Mot de passe
 * @returns {Object} Résultat de validation avec isValid, errors et strength
 */
export const validatePassword = (password) => {
  const errors = [];
  let strength = 0;
  
  if (!password) {
    errors.push('Le mot de passe est requis');
    return { isValid: false, errors, strength: 0 };
  }
  
  if (password.length < 8) {
    errors.push('Le mot de passe doit contenir au moins 8 caractères');
  } else {
    strength += 1;
  }
  
  if (!/[a-z]/.test(password)) {
    errors.push('Le mot de passe doit contenir au moins une minuscule');
  } else {
    strength += 1;
  }
  
  if (!/[A-Z]/.test(password)) {
    errors.push('Le mot de passe doit contenir au moins une majuscule');
  } else {
    strength += 1;
  }
  
  if (!/\d/.test(password)) {
    errors.push('Le mot de passe doit contenir au moins un chiffre');
  } else {
    strength += 1;
  }
  
  if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
    errors.push('Le mot de passe doit contenir au moins un caractère spécial');
  } else {
    strength += 1;
  }
  
  return {
    isValid: errors.length === 0,
    errors,
    strength
  };
};

/**
 * Valide un formulaire générique
 * @param {Object} data - Données du formulaire
 * @param {Object} rules - Règles de validation
 * @returns {Object} Résultat de validation avec isValid et errors
 */
export const validateForm = (data, rules) => {
  const errors = {};
  
  Object.keys(rules).forEach(field => {
    const rule = rules[field];
    const value = data[field];
    
    // Champ requis
    if (rule.required && (!value || value.toString().trim().length === 0)) {
      errors[field] = `${rule.label || field} est requis`;
      return;
    }
    
    // Longueur minimale
    if (rule.minLength && value && value.toString().length < rule.minLength) {
      errors[field] = `${rule.label || field} doit contenir au moins ${rule.minLength} caractères`;
      return;
    }
    
    // Longueur maximale
    if (rule.maxLength && value && value.toString().length > rule.maxLength) {
      errors[field] = `${rule.label || field} ne peut pas dépasser ${rule.maxLength} caractères`;
      return;
    }
    
    // Validation personnalisée
    if (rule.validate && value) {
      const result = rule.validate(value);
      if (result !== true) {
        errors[field] = result;
      }
    }
  });
  
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};

/**
 * Nettoie et valide les données d'un livre avant envoi
 * @param {Object} book - Livre à nettoyer
 * @returns {Object} Livre nettoyé
 */
export const sanitizeBook = (book) => {
  const sanitized = { ...book };
  
  // Nettoyer les champs texte
  if (sanitized.title) sanitized.title = sanitized.title.trim();
  if (sanitized.author) sanitized.author = sanitized.author.trim();
  if (sanitized.saga) sanitized.saga = sanitized.saga.trim();
  if (sanitized.genre) sanitized.genre = sanitized.genre.trim();
  if (sanitized.publisher) sanitized.publisher = sanitized.publisher.trim();
  if (sanitized.review) sanitized.review = sanitized.review.trim();
  
  // Nettoyer les nombres
  if (sanitized.pages) sanitized.pages = parseInt(sanitized.pages, 10) || undefined;
  if (sanitized.current_page) sanitized.current_page = parseInt(sanitized.current_page, 10) || undefined;
  if (sanitized.rating) sanitized.rating = parseInt(sanitized.rating, 10) || undefined;
  if (sanitized.publication_year) sanitized.publication_year = parseInt(sanitized.publication_year, 10) || undefined;
  if (sanitized.volume_number) sanitized.volume_number = parseInt(sanitized.volume_number, 10) || undefined;
  
  // Supprimer les champs vides
  Object.keys(sanitized).forEach(key => {
    if (sanitized[key] === '' || sanitized[key] === null) {
      delete sanitized[key];
    }
  });
  
  return sanitized;
};