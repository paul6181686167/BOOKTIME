import React from 'react';
import toast from 'react-hot-toast';
import ModalOverlay, { MODAL_Z } from '../common/ModalOverlay';
import { formatFriendCode } from '../../utils/friendLink';
import { copyLink } from '../../utils/shareProfile';
import useMyFriendCode from './useMyFriendCode';

/** « Afficher le QR code » : ton QR code en grand, à faire scanner par un ami. */
export default function MyQrModal({ onClose, onScan }) {
  const { loading, error, code, link, qrSrc, qrFailed, username, reload } = useMyFriendCode({
    withQr: true,
  });

  const onCopy = async () => {
    try {
      if (await copyLink(link)) toast.success('Lien copié');
      else toast.error('Copie impossible');
    } catch (_) {
      toast.error('Copie impossible');
    }
  };

  return (
    <ModalOverlay
      onClose={onClose}
      zIndex={MODAL_Z.nested}
      ariaLabel="Mon QR code"
      className="fixed inset-0 bg-black/70 flex items-center justify-center p-4"
    >
      <div
        className="w-full max-w-sm rounded-2xl bg-white dark:bg-gray-800 p-4 space-y-3 text-center"
        data-testid="my-qr-modal"
      >
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold text-gray-900 dark:text-white">Mon QR code</h3>
          <button
            type="button"
            onClick={onClose}
            aria-label="Fermer"
            className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>

        {loading ? (
          <div role="status" className="space-y-2">
            <div className="mx-auto h-60 w-60 rounded-xl bg-gray-200 dark:bg-gray-700 animate-pulse" />
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Création de ton QR code… le serveur peut mettre un instant à démarrer.
            </p>
          </div>
        ) : error ? (
          <div className="rounded-xl border border-amber-300 p-4 space-y-2">
            <p className="text-sm text-amber-700 dark:text-amber-300">{error}</p>
            <button
              type="button"
              onClick={reload}
              className="px-3 py-1.5 rounded-lg border border-green-600 text-green-700 dark:text-green-400 text-sm"
            >
              Réessayer
            </button>
          </div>
        ) : (
          <>
            <p className="text-sm text-gray-600 dark:text-gray-300">
              Fais scanner ce QR code avec l'appareil photo d'un ami : il te retrouve en un geste.
            </p>
            {qrSrc ? (
              <img
                src={qrSrc}
                alt="QR code de ton profil Booktime"
                className="mx-auto w-60 h-60 rounded-lg border border-gray-200 bg-white"
              />
            ) : (
              qrFailed && (
                <p className="text-sm text-amber-700 dark:text-amber-300">
                  Le QR code n'a pas pu être créé. Donne ton code ami ou copie ton lien.
                </p>
              )
            )}
            <div>
              {username ? (
                <p className="text-base font-semibold text-gray-900 dark:text-white">@{username}</p>
              ) : null}
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Code ami <span className="font-mono tracking-wider">{formatFriendCode(code)}</span>
              </p>
              {!username && (
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Choisis un pseudo dans Paramètres pour être trouvé par son nom.
                </p>
              )}
            </div>
            <div className="flex gap-2 justify-center">
              <button
                type="button"
                onClick={onCopy}
                className="px-4 py-2 rounded-lg bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-100 text-sm font-medium"
              >
                Copier le lien
              </button>
              {onScan && (
                <button
                  type="button"
                  onClick={onScan}
                  className="px-4 py-2 rounded-lg border border-green-600 text-green-700 dark:text-green-400 text-sm font-medium"
                >
                  Scanner celui d'un ami
                </button>
              )}
            </div>
          </>
        )}
      </div>
    </ModalOverlay>
  );
}
