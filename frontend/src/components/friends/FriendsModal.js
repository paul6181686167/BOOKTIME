import React from 'react';
import ModalOverlay, { MODAL_Z } from '../common/ModalOverlay';
import FriendsPanel from './FriendsPanel';

/**
 * Fenêtre des amis : ouverte par un lien d'ami (/ami/CODE) ou depuis une fiche livre pour
 * recommander ce livre. Le reste du temps, les amis sont dans l'onglet Profil.
 * `recommendBook` : livre à recommander (ouvert depuis une fiche) — l'utilisateur choisit l'ami.
 */
export default function FriendsModal({
  isOpen,
  onClose,
  libraryBooks,
  onOpenBook,
  recommendBook,
  inviteCode,
}) {
  if (!isOpen) return null;

  return (
    <ModalOverlay onClose={onClose} zIndex={MODAL_Z.panel} ariaLabel="Amis" closeOnBackdrop className="fixed inset-0 bg-black bg-opacity-50 flex items-end md:items-center justify-center md:p-4"
    >
      <div
        className="bg-[#f3faf6] dark:bg-gray-800 md:rounded-2xl shadow-2xl w-full md:max-w-lg h-[92dvh] md:h-[80vh] flex flex-col modal-animate safe-area-bottom overflow-hidden"
        style={{ borderRadius: '20px 20px 0 0' }}
      >
        <div className="md:hidden flex justify-center pt-2.5 pb-1 flex-shrink-0">
          <div className="w-9 h-1 bg-booktime-mist dark:bg-booktime-700 rounded-full" />
        </div>

        <div className="flex-shrink-0 flex items-center gap-2 px-3 py-3 border-b border-booktime-mist/55 dark:border-booktime-800/50 bg-booktime-mistSoft/75 dark:bg-gray-900/70 backdrop-blur-xl">
          <h2 className="flex-1 min-w-0 text-lg font-bold text-gray-900 dark:text-white truncate">
            Amis
          </h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Fermer"
            className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 rounded-lg"
          >
            ✕
          </button>
        </div>

        <FriendsPanel
          // Nouvelle demande (autre livre à recommander, autre lien) : on repart de la liste
          key={`${inviteCode || ''}|${recommendBook?.id || recommendBook?.title || ''}`}
          libraryBooks={libraryBooks}
          onOpenBook={onOpenBook}
          recommendBook={recommendBook}
          inviteCode={inviteCode}
        />
      </div>
    </ModalOverlay>
  );
}
