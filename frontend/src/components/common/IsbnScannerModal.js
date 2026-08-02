import React, { useCallback, useEffect, useRef, useState } from 'react';
import toast from 'react-hot-toast';
import { Html5Qrcode, Html5QrcodeSupportedFormats } from 'html5-qrcode';
import { API_BASE_URL } from '../../config/environment';

function normalizeIsbn(raw) {
  return String(raw || '')
    .replace(/[^0-9Xx]/g, '')
    .toUpperCase();
}

function isValidIsbn(isbn) {
  return isbn.length === 10 || isbn.length === 13;
}

/**
 * Scan caméra ISBN (EAN-13 / code-barres livre) + saisie manuelle.
 */
export default function IsbnScannerModal({ isOpen, onClose, onBookFound, onAddBook }) {
  const [scanning, setScanning] = useState(false);
  const [manualIsbn, setManualIsbn] = useState('');
  const [lookingUp, setLookingUp] = useState(false);
  const [foundBook, setFoundBook] = useState(null);
  const [adding, setAdding] = useState(false);
  const [cameraError, setCameraError] = useState('');
  const scannerRef = useRef(null);
  const handledRef = useRef(false);
  const readerId = 'booktime-isbn-reader';

  const stopScanner = useCallback(async () => {
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
      if (!isValidIsbn(isbn)) {
        toast.error('ISBN invalide (10 ou 13 chiffres)');
        return;
      }
      setLookingUp(true);
      setFoundBook(null);
      try {
        const token = localStorage.getItem('token');
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
      const scanner = new Html5Qrcode(readerId);
      scannerRef.current = scanner;
      await scanner.start(
        { facingMode: 'environment' },
        {
          fps: 8,
          qrbox: (viewW, viewH) => {
            const w = Math.min(280, Math.floor(viewW * 0.85));
            const h = Math.min(140, Math.floor(viewH * 0.35));
            return { width: w, height: h };
          },
          aspectRatio: 1.333,
          formatsToSupport: [
            Html5QrcodeSupportedFormats.EAN_13,
            Html5QrcodeSupportedFormats.EAN_8,
            Html5QrcodeSupportedFormats.UPC_A,
            Html5QrcodeSupportedFormats.CODE_128,
          ],
        },
        async (decoded) => {
          if (handledRef.current) return;
          const isbn = normalizeIsbn(decoded);
          if (!isValidIsbn(isbn)) return;
          handledRef.current = true;
          toast.success(`ISBN détecté : ${isbn}`);
          await lookupIsbn(isbn);
        },
        () => {}
      );
      setScanning(true);
    } catch (err) {
      console.warn('Camera scan error', err);
      setCameraError(
        "Caméra inaccessible. Autorise l'accès ou saisis l'ISBN manuellement."
      );
      setScanning(false);
    }
  }, [lookupIsbn, stopScanner]);

  useEffect(() => {
    if (!isOpen) {
      stopScanner();
      setFoundBook(null);
      setManualIsbn('');
      setCameraError('');
      handledRef.current = false;
      return undefined;
    }
    // Démarrer la caméra dès l'ouverture (mobile)
    const t = setTimeout(() => {
      startScanner();
    }, 250);
    return () => {
      clearTimeout(t);
      stopScanner();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  if (!isOpen) return null;

  const handleAdd = async () => {
    if (!foundBook || !onAddBook) return;
    setAdding(true);
    try {
      await onAddBook(foundBook);
      toast.success('Livre ajouté à ta bibliothèque');
      onClose();
    } catch (err) {
      toast.error(err?.message || "Impossible d'ajouter le livre");
    } finally {
      setAdding(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-[60] bg-black/70 flex items-end md:items-center justify-center md:p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="bg-white dark:bg-gray-800 w-full md:max-w-md md:rounded-2xl max-h-[92dvh] flex flex-col shadow-2xl"
        style={{ borderRadius: '20px 20px 0 0' }}
      >
        <div className="md:hidden flex justify-center pt-2.5 pb-1">
          <div className="w-9 h-1 bg-gray-300 dark:bg-gray-600 rounded-full" />
        </div>

        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white">
              Scanner un ISBN
            </h2>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Cadre le code-barres du livre
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 rounded-lg"
          >
            ✕
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {!foundBook && (
            <>
              <div
                id={readerId}
                className="w-full overflow-hidden rounded-xl bg-black min-h-[220px]"
              />
              {cameraError && (
                <p className="text-sm text-amber-700 dark:text-amber-300 bg-amber-50 dark:bg-amber-900/20 rounded-lg p-3">
                  {cameraError}
                </p>
              )}
              {!scanning && !cameraError && (
                <button
                  type="button"
                  onClick={startScanner}
                  className="w-full py-2.5 rounded-lg bg-green-600 text-white font-medium hover:bg-green-700"
                >
                  Activer la caméra
                </button>
              )}

              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Ou saisis l’ISBN
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    inputMode="numeric"
                    value={manualIsbn}
                    onChange={(e) => setManualIsbn(e.target.value)}
                    placeholder="978…"
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
              </div>
            </>
          )}

          {lookingUp && (
            <p className="text-sm text-gray-500 dark:text-gray-400 text-center">
              Recherche du livre…
            </p>
          )}

          {foundBook && (
            <div className="space-y-3">
              <div className="flex gap-3">
                <div className="w-20 h-28 rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-700 shrink-0">
                  {foundBook.cover_url ? (
                    <img
                      src={foundBook.cover_url}
                      alt=""
                      className="w-full h-full object-cover"
                    />
                  ) : null}
                </div>
                <div className="min-w-0">
                  <h3 className="font-semibold text-gray-900 dark:text-white">
                    {foundBook.title}
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-300">
                    {foundBook.author}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">ISBN {foundBook.isbn}</p>
                  {foundBook.total_pages ? (
                    <p className="text-xs text-gray-500">{foundBook.total_pages} pages</p>
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
    </div>
  );
}
