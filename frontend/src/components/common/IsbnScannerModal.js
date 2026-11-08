import React, { useCallback, useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import toast from 'react-hot-toast';
import { API_BASE_URL } from '../../config/environment';
import logger from '../../utils/logger';
import { getToken } from '../../services/apiClient';
import ModalOverlay, { MODAL_Z } from './ModalOverlay';

function normalizeIsbn(raw) {
  return String(raw || '')
    .replace(/[^0-9Xx]/g, '')
    .toUpperCase();
}

/** Longueur + clé de contrôle : écarte les codes-barres mal lus par la caméra. */
function isValidIsbn(isbn) {
  if (isbn.length === 13 && /^\d{13}$/.test(isbn)) {
    let total = 0;
    for (let i = 0; i < 12; i += 1) total += Number(isbn[i]) * (i % 2 === 0 ? 1 : 3);
    return (10 - (total % 10)) % 10 === Number(isbn[12]);
  }
  if (isbn.length === 10 && /^\d{9}[\dX]$/.test(isbn)) {
    let total = 0;
    for (let i = 0; i < 9; i += 1) total += Number(isbn[i]) * (10 - i);
    total += isbn[9] === 'X' ? 10 : Number(isbn[9]);
    return total % 11 === 0;
  }
  return false;
}

function readCaps(scanner) {
  try {
    return scanner?.getRunningTrackCapabilities?.() || {};
  } catch (_) {
    return {};
  }
}

function hasFocusMode(caps, mode) {
  const modes = caps.focusMode;
  if (!modes) return false;
  return Array.isArray(modes) ? modes.includes(mode) : modes === mode;
}

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

/** Autofocus continu + léger zoom. Chaque réglage est isolé : un refus n'annule pas les autres. */
async function applyBarcodeFocus(scanner) {
  if (!scanner) return;
  const caps = readCaps(scanner);

  if (hasFocusMode(caps, 'continuous')) {
    try {
      await scanner.applyVideoConstraints({ advanced: [{ focusMode: 'continuous' }] });
    } catch (_) {
      /* ignore */
    }
  }

  if (caps.zoom) {
    try {
      const max = Number(typeof caps.zoom === 'object' ? caps.zoom.max : caps.zoom) || 1;
      const min = Number(typeof caps.zoom === 'object' ? caps.zoom.min : 1) || 1;
      // Léger zoom : permet de tenir le livre plus loin que la distance minimale de mise au point
      const target = Math.min(max, Math.max(min, 1.6));
      await scanner.applyVideoConstraints({ advanced: [{ zoom: target }] });
    } catch (_) {
      /* ignore */
    }
  }
}

/**
 * Mise au point au toucher, comme l'appareil photo d'un téléphone : point d'intérêt
 * (x, y entre 0 et 1) quand le navigateur le gère, sinon simple relance de l'autofocus.
 */
async function triggerFocus(scanner, point) {
  if (!scanner) return;
  const caps = readCaps(scanner);
  const attempts = [];
  if (point) {
    const poi = { x: point.x, y: point.y };
    if (hasFocusMode(caps, 'single-shot')) {
      attempts.push({ pointsOfInterest: [poi], focusMode: 'single-shot' });
    }
    attempts.push({ pointsOfInterest: [poi] });
  }
  if (hasFocusMode(caps, 'single-shot')) attempts.push({ focusMode: 'single-shot' });
  else if (hasFocusMode(caps, 'manual')) attempts.push({ focusMode: 'manual' });

  for (const advanced of attempts) {
    try {
      await scanner.applyVideoConstraints({ advanced: [advanced] });
      await wait(700);
      break;
    } catch (_) {
      /* essaie la variante suivante */
    }
  }
  await applyBarcodeFocus(scanner);
}

const VALID_CATEGORIES = ['roman', 'bd', 'manga'];

/** Corps envoyé à l'import : uniquement des champs propres, même chemin que la recherche. */
export function buildImportPayload(book) {
  const toInt = (value) => {
    const n = parseInt(value, 10);
    return Number.isFinite(n) && n > 0 ? n : null;
  };
  return {
    ol_key: book.ol_key || '',
    title: String(book.title || '').trim(),
    author: book.author && book.author !== 'Auteur inconnu' ? String(book.author).trim() : '',
    category: VALID_CATEGORIES.includes(book.category) ? book.category : 'roman',
    cover_url: book.cover_url || '',
    isbn: book.isbn || '',
    description: book.description || '',
    publisher: typeof book.publisher === 'string' ? book.publisher : '',
    total_pages: toInt(book.total_pages || book.number_of_pages),
    first_publish_year: toInt(book.first_publish_year),
  };
}

/** Vignette : repli lisible si la couverture est absente, cassée ou réduite à un pixel. */
function CoverThumb({ url, title }) {
  // On mémorise l'URL en échec (plutôt qu'un booléen réinitialisé dans un effet) : une image
  // déjà en cache peut se charger avant l'exécution des effets, et le reset effaçait alors le verdict.
  const [failedUrl, setFailedUrl] = useState(null);
  const failed = failedUrl === url;

  if (!url || failed) {
    return (
      <div
        className="w-full h-full flex items-center justify-center p-1.5 text-center text-tiny leading-tight font-medium text-gray-500 dark:text-gray-300 bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-600"
        data-testid="cover-placeholder"
      >
        {title}
      </div>
    );
  }
  return (
    <img
      src={url}
      alt=""
      className="w-full h-full object-cover"
      onLoad={(e) => {
        if (e.currentTarget.naturalWidth <= 1) setFailedUrl(url);
      }}
      onError={() => setFailedUrl(url)}
    />
  );
}

/**
 * Scan caméra ISBN (EAN-13 / code-barres livre) + saisie manuelle.
 * `onAdded(book)` est appelé après l'ajout réussi pour rafraîchir la bibliothèque.
 */
export default function IsbnScannerModal({ isOpen, onClose, onBookFound, onAdded }) {
  const [scanning, setScanning] = useState(false);
  const [manualIsbn, setManualIsbn] = useState('');
  const [lookingUp, setLookingUp] = useState(false);
  const [foundBook, setFoundBook] = useState(null);
  const [adding, setAdding] = useState(false);
  const [cameraError, setCameraError] = useState('');
  const [focusRing, setFocusRing] = useState(null);
  const scannerRef = useRef(null);
  const handledRef = useRef(false);
  const focusTimerRef = useRef(null);
  const ringTimerRef = useRef(null);
  const lastTriedRef = useRef({ isbn: '', at: 0 });
  const readerId = 'booktime-isbn-reader';

  const stopScanner = useCallback(async () => {
    if (focusTimerRef.current) {
      clearTimeout(focusTimerRef.current);
      focusTimerRef.current = null;
    }
    if (ringTimerRef.current) {
      clearTimeout(ringTimerRef.current);
      ringTimerRef.current = null;
    }
    const scanner = scannerRef.current;
    scannerRef.current = null;
    setScanning(false);
    if (!scanner) return;
    try {
      if (scanner.isScanning) {
        await scanner.stop();
      }
      await scanner.clear();
    } catch (_) {
      /* ignore */
    }
  }, []);

  const lookupIsbn = useCallback(
    async (isbnRaw) => {
      const isbn = normalizeIsbn(isbnRaw);
      if (isbn.length !== 10 && isbn.length !== 13) {
        toast.error('ISBN invalide (10 ou 13 chiffres)');
        return;
      }
      if (!isValidIsbn(isbn)) {
        toast.error('ISBN invalide : vérifie les chiffres');
        handledRef.current = false;
        return;
      }
      setLookingUp(true);
      setFoundBook(null);
      try {
        const token = getToken();
        const res = await fetch(
          `${API_BASE_URL}/api/openlibrary/search-isbn?isbn=${encodeURIComponent(isbn)}`,
          {
            headers: token ? { Authorization: `Bearer ${token}` } : {},
          }
        );
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw new Error(
            typeof data.detail === 'string'
              ? data.detail
              : 'Livre introuvable pour cet ISBN'
          );
        }
        const book = data.book;
        if (!book?.title) throw new Error('Livre introuvable pour cet ISBN');
        const enriched = {
          ...book,
          isFromOpenLibrary: true,
          id: book.ol_key ? `ol_${book.ol_key}` : `isbn_${isbn}`,
          category: book.category || 'roman',
          total_pages: book.total_pages || book.number_of_pages || null,
        };
        setFoundBook(enriched);
        onBookFound?.(enriched);
        await stopScanner();
      } catch (err) {
        toast.error(err.message || 'Recherche ISBN échouée');
        handledRef.current = false;
      } finally {
        setLookingUp(false);
      }
    },
    [onBookFound, stopScanner]
  );

  const startScanner = useCallback(async () => {
    setCameraError('');
    handledRef.current = false;
    await stopScanner();
    try {
      // Chargé à la demande : le décodeur de codes-barres pèse ~1,2 Mo et ne concerne
      // que les utilisateurs qui activent la caméra.
      const { Html5Qrcode, Html5QrcodeSupportedFormats } = await import('html5-qrcode');
      const scanner = new Html5Qrcode(readerId, {
        verbose: false,
        formatsToSupport: [
          Html5QrcodeSupportedFormats.EAN_13,
          Html5QrcodeSupportedFormats.EAN_8,
          Html5QrcodeSupportedFormats.UPC_A,
          Html5QrcodeSupportedFormats.UPC_E,
          Html5QrcodeSupportedFormats.CODE_128,
        ],
      });
      scannerRef.current = scanner;

      // facingMode « environment » laisse Android choisir l'objectif principal (avec autofocus).
      // Choisir une caméra par deviceId risquait de tomber sur l'ultra grand-angle ou le macro.
      const scanConfig = {
        fps: 15,
        // Bande large et basse = cadre naturel d’un ISBN
        qrbox: (viewW, viewH) => {
          const w = Math.floor(Math.min(viewW * 0.92, 360));
          const h = Math.floor(Math.min(viewH * 0.22, 120));
          return { width: Math.max(220, w), height: Math.max(70, h) };
        },
        aspectRatio: 1.777,
        disableFlip: true,
        experimentalFeatures: {
          useBarCodeDetectorIfSupported: true,
        },
      };
      const onDecoded = async (decoded) => {
        if (handledRef.current) return;
        const isbn = normalizeIsbn(decoded);
        // Clé de contrôle fausse = code mal lu : on continue de scanner sans rien dire
        if (!isValidIsbn(isbn)) return;
        const last = lastTriedRef.current;
        if (last.isbn === isbn && Date.now() - last.at < 5000) return;
        lastTriedRef.current = { isbn, at: Date.now() };
        handledRef.current = true;
        toast.success(`ISBN détecté : ${isbn}`);
        await lookupIsbn(isbn);
      };

      try {
        // Haute résolution : le code-barres reste net même un peu flou
        await scanner.start(
          { facingMode: { ideal: 'environment' } },
          {
            ...scanConfig,
            videoConstraints: {
              facingMode: { ideal: 'environment' },
              width: { ideal: 1920 },
              height: { ideal: 1080 },
            },
          },
          onDecoded,
          () => {}
        );
      } catch (_) {
        // Repli : contraintes minimales
        await scanner.start({ facingMode: 'environment' }, scanConfig, onDecoded, () => {});
      }

      setScanning(true);

      // Autofocus + zoom une fois le flux démarré
      focusTimerRef.current = setTimeout(() => {
        applyBarcodeFocus(scanner);
      }, 900);
    } catch (err) {
      logger.warn('Camera scan error', err);
      setCameraError(
        "Caméra inaccessible. Autorise l'accès (HTTPS) ou saisis l'ISBN manuellement."
      );
      setScanning(false);
    }
  }, [lookupIsbn, stopScanner]);

  // Toucher le cadre = mise au point à cet endroit, comme l'appareil photo du téléphone
  const handleTapFocus = async (e) => {
    const scanner = scannerRef.current;
    if (!scanner || !scanning) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const px = e.clientX - rect.left;
    const py = e.clientY - rect.top;
    setFocusRing({ x: px, y: py, key: Date.now() });
    if (ringTimerRef.current) clearTimeout(ringTimerRef.current);
    ringTimerRef.current = setTimeout(() => setFocusRing(null), 1100);
    await triggerFocus(scanner, {
      x: Math.min(1, Math.max(0, px / rect.width)),
      y: Math.min(1, Math.max(0, py / rect.height)),
    });
  };

  useEffect(() => {
    if (!isOpen) {
      stopScanner();
      setFoundBook(null);
      setManualIsbn('');
      setCameraError('');
      setFocusRing(null);
      handledRef.current = false;
      lastTriedRef.current = { isbn: '', at: 0 };
      return undefined;
    }
    const t = setTimeout(() => {
      startScanner();
    }, 300);
    return () => {
      clearTimeout(t);
      stopScanner();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  if (!isOpen) return null;

  const handleAdd = async () => {
    if (!foundBook || adding) return;
    setAdding(true);
    try {
      const token = getToken();
      const res = await fetch(`${API_BASE_URL}/api/openlibrary/import`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(buildImportPayload(foundBook)),
      });
      const data = await res.json().catch(() => ({}));
      if (res.status === 409) {
        toast('Ce livre est déjà dans ta bibliothèque');
        onClose();
        return;
      }
      if (!res.ok) {
        throw new Error(
          typeof data.detail === 'string' ? data.detail : "Impossible d'ajouter le livre"
        );
      }
      toast.success(`« ${foundBook.title} » ajouté à ta bibliothèque`);
      try {
        await onAdded?.(data.book || foundBook);
      } catch (_) {
        /* le livre est ajouté : un échec de rafraîchissement ne doit pas l'annuler */
      }
      onClose();
    } catch (err) {
      toast.error(err?.message || "Impossible d'ajouter le livre");
    } finally {
      setAdding(false);
    }
  };

  // Rendu dans <body> : la fenêtre ne doit dépendre d'aucun parent (carrousel de pages
  // transformé, barre de navigation du bas) qui la rognerait ou la recouvrirait.
  const modal = (
    <ModalOverlay
      onClose={onClose}
      zIndex={MODAL_Z.nested}
      ariaLabel="Scanner un ISBN"
      className="fixed inset-0 bg-black/80 flex items-end md:items-center justify-center md:p-4"
    >
      <div
        className="bg-[#f3faf6] dark:bg-gray-800 w-full md:max-w-md md:rounded-2xl max-h-[94dvh] flex flex-col shadow-2xl safe-area-bottom"
        style={{ borderRadius: '20px 20px 0 0' }}
      >
        <div className="md:hidden flex justify-center pt-2.5 pb-1">
          <div className="w-9 h-1 bg-booktime-mist dark:bg-booktime-700 rounded-full" />
        </div>

        <div className="flex items-center justify-between px-4 py-3 border-b border-booktime-mist/55 dark:border-booktime-800/50 bg-booktime-mistSoft/75 dark:bg-gray-900/70 backdrop-blur-xl">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white">
            Scanner un ISBN
          </h2>
          <button aria-label="Fermer"
            type="button"
            onClick={onClose}
            className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 rounded-lg"
          >
            ✕
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {!foundBook && (
            <>
              <div className="relative overflow-hidden rounded-xl bg-black">
                <div
                  id={readerId}
                  onClick={handleTapFocus}
                  className="w-full h-[34dvh] min-h-[200px] max-h-[300px] isbn-scanner-view"
                />
                <style>{`
                  #${readerId} { overflow: hidden; }
                  #${readerId} video {
                    object-fit: cover !important;
                    width: 100% !important;
                    height: 100% !important;
                  }
                  #${readerId} > div { height: 100% !important; }
                  #${readerId} img { display: none !important; }
                  @keyframes isbn-focus-ring {
                    0% { transform: translate(-50%, -50%) scale(1.5); opacity: 0; }
                    25% { opacity: 1; }
                    100% { transform: translate(-50%, -50%) scale(1); opacity: 0.9; }
                  }
                `}</style>

                {focusRing && (
                  <div
                    key={focusRing.key}
                    className="absolute pointer-events-none rounded-lg border-2 border-yellow-300"
                    style={{
                      left: focusRing.x,
                      top: focusRing.y,
                      width: 72,
                      height: 72,
                      animation: 'isbn-focus-ring 0.35s ease-out forwards',
                      boxShadow: '0 0 0 1px rgba(0,0,0,0.35)',
                    }}
                  />
                )}

                {lookingUp && (
                  <div className="absolute inset-0 flex items-center justify-center bg-black/55 pointer-events-none">
                    <div className="w-8 h-8 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                  </div>
                )}
              </div>

              {cameraError && (
                <div className="space-y-2">
                  <p className="text-sm text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-900/20 rounded-lg p-3">
                    {cameraError}
                  </p>
                  <button
                    type="button"
                    onClick={startScanner}
                    className="w-full py-2.5 rounded-lg bg-green-600 text-white font-medium hover:bg-green-700"
                  >
                    Activer la caméra
                  </button>
                </div>
              )}

              <div className="flex gap-2">
                <input
                  type="text"
                  inputMode="numeric"
                  value={manualIsbn}
                  onChange={(e) => setManualIsbn(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !lookingUp && normalizeIsbn(manualIsbn)) {
                      lookupIsbn(manualIsbn);
                    }
                  }}
                  placeholder="Saisir l’ISBN"
                  aria-label="Saisir l’ISBN"
                  className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                />
                <button
                  type="button"
                  disabled={lookingUp || !normalizeIsbn(manualIsbn)}
                  onClick={() => lookupIsbn(manualIsbn)}
                  className="px-4 py-2 rounded-lg bg-green-600 text-white font-medium disabled:opacity-40"
                >
                  {lookingUp ? '…' : 'OK'}
                </button>
              </div>
            </>
          )}

          {foundBook && (
            <div className="space-y-3">
              <div className="flex gap-3">
                <div className="w-20 h-28 rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-700 shrink-0">
                  <CoverThumb url={foundBook.cover_url} title={foundBook.title} />
                </div>
                <div className="min-w-0">
                  <h3 className="font-semibold text-gray-900 dark:text-white">
                    {foundBook.title}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-300">
                    {foundBook.author}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">ISBN {foundBook.isbn}</p>
                  {foundBook.total_pages ? (
                    <p className="text-xs text-gray-500 dark:text-gray-400">{foundBook.total_pages} pages</p>
                  ) : null}
                </div>
              </div>
              <button
                type="button"
                onClick={handleAdd}
                disabled={adding}
                className="w-full py-3 rounded-lg bg-green-600 text-white font-medium hover:bg-green-700 disabled:opacity-50"
              >
                {adding ? 'Ajout…' : 'Ajouter à ma bibliothèque'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setFoundBook(null);
                  handledRef.current = false;
                  startScanner();
                }}
                className="w-full py-2 text-sm text-gray-600 dark:text-gray-300 hover:underline"
              >
                Scanner un autre livre
              </button>
            </div>
          )}
        </div>
      </div>
    </ModalOverlay>
  );

  return createPortal(modal, document.body);
}
