// Phase 2.3 - Hook de debouncing pour optimiser les recherches
import { useState, useEffect } from 'react';

/**
 * Hook de debouncing pour optimiser les recherches et filtres
 * @param {*} value - Valeur à debouncer
 * @param {number} delay - Délai en millisecondes (défaut: 300ms)
 * @returns {*} - Valeur debouncée
 */
export const useDebounce = (value, delay = 300) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    // Créer un timer qui met à jour la valeur debouncée après le délai
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    // Nettoyer le timer si la valeur change avant la fin du délai
    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
};

/**
 * Hook de debouncing avancé avec contrôle du loading
 * @param {*} value - Valeur à debouncer
 * @param {number} delay - Délai en millisecondes
 * @param {boolean} immediate - Exécuter immédiatement la première fois
 * @returns {Object} - { debouncedValue, isDebouncing }
 */
export const useAdvancedDebounce = (value, delay = 300, immediate = false) => {
  const [debouncedValue, setDebouncedValue] = useState(immediate ? value : undefined);
  const [isDebouncing, setIsDebouncing] = useState(false);

  useEffect(() => {
    // Si c'est la première fois et immediate est true, définir la valeur directement
    if (immediate && debouncedValue === undefined) {
      setDebouncedValue(value);
      return;
    }

    // Indiquer que le debouncing est en cours
    setIsDebouncing(true);

    const timer = setTimeout(() => {
      setDebouncedValue(value);
      setIsDebouncing(false);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay, immediate, debouncedValue]);

  return { debouncedValue, isDebouncing };
};

/**
 * Hook de debouncing pour les fonctions de callback
 * @param {Function} callback - Fonction à debouncer
 * @param {number} delay - Délai en millisecondes
 * @param {Array} deps - Dépendances pour useCallback
 * @returns {Function} - Fonction debouncée
 */
export const useDebouncedCallback = (callback, delay = 300, deps = []) => {
  const [timer, setTimer] = useState(null);

  return useCallback((...args) => {
    // Nettoyer le timer précédent
    if (timer) {
      clearTimeout(timer);
    }

    // Créer un nouveau timer
    const newTimer = setTimeout(() => {
      callback(...args);
    }, delay);

    setTimer(newTimer);
  }, [callback, delay, ...deps]);
};

export default useDebounce;