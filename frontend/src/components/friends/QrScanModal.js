import React, { useCallback, useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import { parseFriendCode } from '../../utils/friendLink';

/** Scanner de QR code Booktime (caméra) avec saisie manuelle du code en secours. */
export default function QrScanModal({ onClose, onCode }) {
  const scannerRef = useRef(null);
  const doneRef = useRef(false);
  const [error, setError] = useState('');
  const [manual, setManual] = useState('');
  const readerId = 'booktime-qr-reader';

  const stop = useCallback(async () => {
    const scanner = scannerRef.current;
    scannerRef.current = null;
    if (!scanner) return;
    try {
      if (scanner.isScanning) await scanner.stop();
      await scanner.clear();
    } catch (_) {
      /* ignore */
    }
  }, []);

  const finish = useCallback(
    async (code) => {
      if (doneRef.current) return;
      doneRef.current = true;
      await stop();
      onCode(code);
    },
    [onCode, stop]
  );

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const { Html5Qrcode, Html5QrcodeSupportedFormats } = await import('html5-qrcode');
        if (cancelled) return;
        const scanner = new Html5Qrcode(readerId, {
          verbose: false,
          formatsToSupport: [Html5QrcodeSupportedFormats.QR_CODE],
        });
        scannerRef.current = scanner;
        await scanner.start(
          { facingMode: 'environment' },
          { fps: 10, qrbox: { width: 220, height: 220 } },
          (text) => {
            const code = parseFriendCode(text);
            if (code) finish(code);
          },
          () => {}
        );
        if (cancelled) await stop();
      } catch (_) {
        if (!cancelled) {
          setError("La caméra n'est pas accessible. Autorise-la, ou saisis le code ci-dessous.");
        }
      }
    })();
    return () => {
      cancelled = true;
      stop();
    };
  }, [finish, stop]);

  const submitManual = (e) => {
    e.preventDefault();
    const code = parseFriendCode(manual);
    if (!code) {
      setError('Ce code ou ce lien n’est pas valide.');
      return;
    }
    finish(code);
  };

  return createPortal(
    <div
      className="fixed inset-0 z-[1300] bg-black/70 flex items-center justify-center p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="w-full max-w-sm rounded-2xl bg-white dark:bg-gray-800 p-4 space-y-3"
        role="dialog"
        aria-label="Scanner un QR code"
      >
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold text-gray-900 dark:text-white">Scanner un QR code</h3>
          <button
            type="button"
            onClick={onClose}
            aria-label="Fermer"
            className="p-2 text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>
        <div className="overflow-hidden rounded-xl bg-black">
          <div id={readerId} className="w-full min-h-[240px]" />
        </div>
        {error && <p className="text-xs text-amber-700 dark:text-amber-300">{error}</p>}
        <form onSubmit={submitManual} className="flex gap-2">
          <input
            type="text"
            value={manual}
            onChange={(e) => setManual(e.target.value)}
            placeholder="Code ami ou lien (ABCD-2345)"
            aria-label="Code ami ou lien"
            autoCapitalize="characters"
            className="flex-1 min-w-0 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-green-500"
          />
          <button
            type="submit"
            className="px-3 py-2 rounded-lg bg-green-600 text-white text-sm font-medium"
          >
            Valider
          </button>
        </form>
      </div>
    </div>,
    document.body
  );
}
