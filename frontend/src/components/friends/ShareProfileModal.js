import React from 'react';
import toast from 'react-hot-toast';
import ModalOverlay, { MODAL_Z } from '../common/ModalOverlay';
import { canUseSystemShare, copyLink, shareLink, socialShareTargets } from '../../utils/shareProfile';
import useMyFriendCode from './useMyFriendCode';

/** « Partager mon profil » : envoie ton lien d'ami sur le réseau ou la messagerie de ton choix. */
export default function ShareProfileModal({ onClose }) {
  const { loading, error, link, username, displayName, reload } = useMyFriendCode();

  const name = displayName || (username ? `@${username}` : '');
  const text = name
    ? `Je suis ${name} sur Booktime. Ajoute-moi en un clic pour échanger nos lectures :`
    : 'Retrouve-moi sur Booktime. Ajoute-moi en un clic pour échanger nos lectures :';

  const onCopy = async () => {
    try {
      if (await copyLink(link)) toast.success('Lien copié');
      else toast.error('Copie impossible');
    } catch (_) {
      toast.error('Copie impossible');
    }
  };

  const onSystemShare = async () => {
    const result = await shareLink({ title: 'Mon profil Booktime', text, url: link });
    if (result === 'copied') toast.success('Lien copié, colle-le dans ta conversation');
    else if (result === 'failed') toast.error('Partage impossible');
  };

  const targets = link ? socialShareTargets({ text, url: link }) : [];

  return (
    <ModalOverlay
      onClose={onClose}
      zIndex={MODAL_Z.nested}
      ariaLabel="Partager mon profil"
      className="fixed inset-0 bg-black/60 flex items-end sm:items-center justify-center p-0 sm:p-4"
    >
      <div
        className="w-full sm:max-w-sm rounded-t-2xl sm:rounded-2xl bg-white dark:bg-gray-800 p-4 space-y-4"
        data-testid="share-profile-modal"
      >
        <div className="flex items-center justify-between">
          <h3 className="text-base font-bold text-gray-900 dark:text-white">Partager mon profil</h3>
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
          <div className="space-y-2" role="status">
            <div className="h-24 rounded-xl bg-gray-200 dark:bg-gray-700 animate-pulse" />
            <p className="text-xs text-center text-gray-500 dark:text-gray-400">
              Préparation de ton lien… le serveur peut mettre un instant à démarrer.
            </p>
          </div>
        ) : error ? (
          <div className="rounded-xl border border-amber-300 p-4 text-center space-y-2">
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
              Envoie ton lien : la personne arrive sur Booktime, se connecte et te retrouve en un
              geste.
            </p>

            <ul className="grid grid-cols-3 gap-2" aria-label="Envoyer le lien avec">
              {targets.map((t) => (
                <li key={t.id}>
                  <a
                    href={t.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex flex-col items-center gap-1.5 rounded-xl border border-gray-200 dark:border-gray-700 py-3 text-xs font-medium text-gray-800 dark:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-700/50"
                  >
                    <span
                      aria-hidden="true"
                      className="h-9 w-9 rounded-full flex items-center justify-center text-white text-sm font-bold"
                      style={{ backgroundColor: t.color }}
                    >
                      {t.label.slice(0, 1)}
                    </span>
                    {t.label}
                  </a>
                </li>
              ))}
            </ul>

            {canUseSystemShare() && (
              <button
                type="button"
                onClick={onSystemShare}
                className="w-full px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 text-white text-sm font-medium"
              >
                Autres applications…
              </button>
            )}

            <div className="flex items-center gap-2">
              <input
                type="text"
                readOnly
                value={link}
                aria-label="Ton lien d'ami"
                onFocus={(e) => e.target.select()}
                className="flex-1 min-w-0 px-3 py-2 text-xs border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-700 dark:text-gray-200"
              />
              <button
                type="button"
                onClick={onCopy}
                className="px-3 py-2 rounded-lg bg-gray-200 dark:bg-gray-600 text-gray-800 dark:text-gray-100 text-sm font-medium"
              >
                Copier
              </button>
            </div>
          </>
        )}
      </div>
    </ModalOverlay>
  );
}
