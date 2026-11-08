import React, { useState } from 'react';
import { UserAvatar } from '../common/ProfileIdentityCard';
import FriendsHome from './FriendsHome';
import FriendChat from './FriendChat';
import FriendProfileView from './FriendProfileView';

/**
 * Contenu des amis : liste et recherche, profil d'un ami, messagerie.
 * Utilisé dans la fenêtre « Amis » (ouverture par lien ou depuis une fiche livre) et dans
 * l'onglet Profil.
 *
 * `embedded` : intégré dans une page qui défile déjà (onglet Profil) ; sinon, remplit la fenêtre.
 * `recommendBook` : livre à recommander (ouvert depuis une fiche) — l'utilisateur choisit l'ami.
 */
export default function FriendsPanel({
  libraryBooks,
  onOpenBook,
  recommendBook,
  inviteCode,
  embedded = false,
}) {
  const [view, setView] = useState({ name: 'home' });
  const [pendingBook, setPendingBook] = useState(recommendBook || null);

  const goHome = () => setView({ name: 'home' });

  const openChat = (friend) => {
    setView({ name: 'chat', friend, book: pendingBook });
    setPendingBook(null);
  };

  const title =
    view.name === 'chat'
      ? view.friend.display_name
      : view.name === 'profile'
        ? `Profil de ${view.friend.display_name}`
        : '';

  const rootClass = embedded ? 'space-y-3' : 'flex-1 min-h-0 flex flex-col';

  return (
    <div className={rootClass} data-testid="friends-panel">
      {view.name !== 'home' && (
        <div
          className={`flex-shrink-0 flex items-center gap-2 ${
            embedded
              ? 'rounded-xl bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 px-2 py-2'
              : 'px-3 py-2 border-b border-booktime-mist/55 dark:border-booktime-800/50'
          }`}
        >
          <button
            type="button"
            onClick={goHome}
            aria-label="Retour à la liste d’amis"
            className="px-2 py-1 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
          >
            ←
          </button>
          <UserAvatar user={view.friend} size={32} />
          <h3 className="flex-1 min-w-0 text-base font-bold text-gray-900 dark:text-white truncate">
            {title}
          </h3>
          {view.name === 'chat' && (
            <button
              type="button"
              onClick={() => setView({ name: 'profile', friend: view.friend })}
              className="px-2.5 py-1.5 rounded-lg text-xs font-medium text-green-700 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20"
            >
              Profil
            </button>
          )}
        </div>
      )}

      {view.name === 'chat' ? (
        <div
          className={
            embedded
              ? 'h-[65dvh] min-h-[360px] flex flex-col rounded-xl overflow-hidden border border-gray-100 dark:border-gray-700'
              : 'flex-1 min-h-0 flex flex-col'
          }
        >
          <FriendChat
            friend={view.friend}
            libraryBooks={libraryBooks}
            initialBook={view.book}
            onOpenBook={onOpenBook}
          />
        </div>
      ) : (
        <div className={embedded ? '' : 'flex-1 min-h-0 overflow-y-auto p-4'}>
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
  );
}
