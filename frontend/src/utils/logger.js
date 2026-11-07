/**
 * Journal central de l'application.
 *
 * - debug / log / info / warn : visibles en développement, ou en production si
 *   `localStorage.booktime_debug = '1'` (utile pour diagnostiquer sur un téléphone).
 * - error : toujours affiché, conservé dans un historique en mémoire et transmis aux
 *   observateurs enregistrés avec `onError` (futur envoi vers un service de suivi).
 */

const HISTORY_MAX = 50;
const history = [];
const errorListeners = new Set();

function debugEnabled() {
  if (process.env.NODE_ENV !== 'production') return true;
  try {
    return localStorage.getItem('booktime_debug') === '1';
  } catch {
    return false;
  }
}

function push(level, args) {
  history.push({ level, time: Date.now(), message: args.map(formatArg).join(' ') });
  if (history.length > HISTORY_MAX) history.shift();
}

function formatArg(arg) {
  if (arg instanceof Error) return arg.stack || arg.message;
  if (typeof arg === 'string') return arg;
  try {
    return JSON.stringify(arg);
  } catch {
    return String(arg);
  }
}

const debug = (...args) => {
  if (debugEnabled()) console.log(...args);
};

const warn = (...args) => {
  if (debugEnabled()) console.warn(...args);
};

const error = (...args) => {
  push('error', args);
  console.error(...args);
  errorListeners.forEach((fn) => {
    try {
      fn(args);
    } catch {
      /* un observateur défaillant ne doit jamais casser l'application */
    }
  });
};

/** Enregistre un observateur d'erreurs ; renvoie la fonction de désinscription. */
const onError = (fn) => {
  errorListeners.add(fn);
  return () => errorListeners.delete(fn);
};

/** Dernières erreurs (les plus anciennes d'abord), à joindre à un retour utilisateur. */
const getRecentErrors = () => [...history];

const logger = { debug, log: debug, info: debug, warn, error, onError, getRecentErrors };

export default logger;
