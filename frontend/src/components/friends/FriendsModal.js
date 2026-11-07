import React, { useEffect, useState } from 'react';
import { UserAvatar } from '../common/ProfileIdentityCard';
import FriendsHome from './FriendsHome';
import FriendChat from './FriendChat';
import FriendProfileView from './FriendProfileView';

/**
 * Fenêtre des amis : liste et recherche, profil d'un ami, messagerie.
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
  const [view, setView] = useState({ name: 'home' });
  const [pendingBook, setPendingBook] = useState(recommendBook || null);

  useEffect(() => {
    if (isOpen) {
      setView({ name: 'home' });
      setPendingBook(recommendBook || null);
    }
    // Réinitialise à chaque ouverture ou nouveau livre à recommander
  }, [isOpen, recommendBook]);

  if (!isOpen) return null;

  const goHome = () => setView({ name: 'home' });

  const openChat = (friend) => {
    setView({ name: 'chat', friend, book: pendingBook });
    setPendingBook(null);
  };

  const title =
    view.name === 'home'
      ? 'Amis'
      : view.name === 'chat'
        ? view.friend.display_name
        : `Profil de ${view.friend.display_name}`;

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-end md:items-center justify-center z-50 md:p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="bg-[#f3faf6] dark:bg-gray-800 md:rounded-2xl shadow-2xl w-full md:max-w-lg h-[92dvh] md:h-[80vh] flex flex-col modal-animate safe-area-bottom overflow-hidden"
        style={{ borderRadius: '20px 20px 0 0' }}
      >
        <div className="md:hidden flex justify-center pt-2.5 pb-1 flex-shrink-0">
          <div className="w-9 h-1 bg-booktime-mist dark:bg-booktime-700 rounded-full" />
        </div>

        <div className="flex-shrink-0 flex items-center gap-2 px-3 py-3 border-b border-booktime-mist/55 dark:border-booktime-800/50 bg-booktime-mistSoft/75 dark:bg-gray-900/70 backdrop-blur-xl">
          {view.name !== 'home' && (
            <button
              type="button"
              onClick={goHome}
              aria-label="Retour à la liste d’amis"
              className="px-2 py-1 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
            >
              ←
            </button>
          )}
          {view.name !== 'home' && <UserAvatar user={view.friend} size={32} />}
          <h2 className="flex-1 min-w-0 text-lg font-bold text-gray-900 dark:text-white truncate">
            {title}
          </h2>
          {view.name === 'chat' && (
            <button
              type="button"
              onClick={() => setView({ name: 'profile', friend: view.friend })}
              className="px-2.5 py-1.5 rounded-lg text-xs font-medium text-green-700 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20"
            >
              Profil
            </button>
          )}
          <button
            type="button"
            onClick={onClose}
            aria-label="Fermer"
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 rounded-lg"
          >
            ✕
          </button>
        </div>

        {view.name === 'chat' ? (
          <div className="flex-1 min-h-0 flex flex-col">
            <FriendChat
              friend={view.friend}
              libraryBooks={libraryBooks}
              initialBook={view.book}
              onOpenBook={onOpenBook}
            />
          </div>
        ) : (
          <div className="flex-1 min-h-0 overflow-y-auto p-4">
            {view.name === 'home' ? (
              <FriendsHome
                recommendBook={pendingBook}
                inviteCode={inviteCode}
                onOpenChat={openChat}
                onOpenProfile={(friend) => setView({ name: 'profile', friend })}
              />
            ) : (
              <FriendProfileView
                friend={view.friend}
                onOpenBook={onOpenBook}
                onOpenChat={openChat}
                onRemoved={goHome}
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
