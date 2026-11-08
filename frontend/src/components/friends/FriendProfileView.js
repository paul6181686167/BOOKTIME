import React, { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import friendsService, { bookRefToBookLike } from '../../services/friendsService';
import { UserAvatar } from '../common/ProfileIdentityCard';
import BookRefCard, { MiniCover, Stars } from './BookRefCard';

/** Profil d'un ami : bio, livres préférés, avis et lectures en cours. */
export default function FriendProfileView({ friend, onOpenBook, onOpenChat, onRemoved }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [confirmRemove, setConfirmRemove] = useState(false);
  const [removing, setRemoving] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setData(null);
    setError('');
    friendsService
      .getProfile(friend.id)
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || 'Profil indisponible');
      });
    return () => {
      cancelled = true;
    };
  }, [friend.id]);

  const open = (book) => onOpenBook(bookRefToBookLike(book));

  const handleRemove = async () => {
    setRemoving(true);
    try {
      await friendsService.removeFriend(friend.id);
      toast.success(`${friend.display_name} n’est plus dans tes amis`);
      onRemoved();
    } catch (err) {
      toast.error(err.message || 'Action impossible');
      setRemoving(false);
    }
  };

  if (error) {
    return <p className="text-sm text-center text-amber-700 dark:text-amber-300 py-8">{error}</p>;
  }
  if (!data) {
    return (
      <div className="space-y-3">
        <div className="h-24 rounded-xl bg-gray-200 dark:bg-gray-700 animate-pulse" />
        <div className="h-32 rounded-xl bg-gray-200 dark:bg-gray-700 animate-pulse" />
      </div>
    );
  }

  const { user, stats, favorites, reviews, reading } = data;
  const hidden = data.hidden || [];
  const hiddenNote = `${user.display_name} ne montre pas cette section.`;

  return (
    <div className="space-y-5">
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 p-4">
        <div className="flex items-start gap-3">
          <UserAvatar user={user} size={64} />
          <div className="min-w-0 flex-1">
            <p className="font-semibold text-gray-900 dark:text-white truncate">{user.display_name}</p>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              {stats.total_books} livre{stats.total_books > 1 ? 's' : ''} · {stats.completed_books} terminé
              {stats.completed_books > 1 ? 's' : ''}
            </p>
            {user.bio ? (
              <p className="mt-1.5 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-line break-words">
                {user.bio}
              </p>
            ) : null}
          </div>
        </div>
        <button
          type="button"
          onClick={() => onOpenChat(friend)}
          className="mt-3 w-full py-2 rounded-lg bg-green-600 hover:bg-green-700 text-white text-sm font-medium"
        >
          Envoyer un message
        </button>
      </div>

      <section>
        <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">
          Livres préférés
        </h3>
        {hidden.includes('favorites') ? (
          <p className="text-sm text-gray-500 dark:text-gray-400 italic">{hiddenNote}</p>
        ) : favorites.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400">Aucun livre préféré pour le moment.</p>
        ) : (
          <div className="flex gap-3 overflow-x-auto pb-2">
            {favorites.map((b) => (
              <button
                key={b.id}
                type="button"
                onClick={() => open(b)}
                className="w-20 shrink-0 text-left"
                title={b.title}
              >
                <MiniCover url={b.cover_url} className="w-20 h-28" />
                <span className="block mt-1 text-tiny leading-tight text-gray-800 dark:text-gray-200 line-clamp-2">
                  {b.title}
                </span>
              </button>
            ))}
          </div>
        )}
      </section>

      {reading.length > 0 && (
        <section>
          <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">
            Lit en ce moment
          </h3>
          <div className="space-y-1.5">
            {reading.map((b) => (
              <BookRefCard key={b.id} book={b} onOpen={open} />
            ))}
          </div>
        </section>
      )}

      <section>
        <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">
          Avis{hidden.includes('reviews') ? '' : ` (${reviews.length})`}
        </h3>
        {hidden.includes('reviews') ? (
          <p className="text-sm text-gray-500 dark:text-gray-400 italic">{hiddenNote}</p>
        ) : reviews.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400">Aucun avis pour le moment.</p>
        ) : (
          <div className="space-y-2">
            {reviews.map((b) => (
              <BookRefCard key={b.id} book={b} onOpen={open}>
                <Stars value={b.rating} />
                {b.review ? (
                  <span className="block mt-0.5 text-xs text-gray-700 dark:text-gray-300 whitespace-pre-line break-words line-clamp-4">
                    {b.review}
                  </span>
                ) : null}
              </BookRefCard>
            ))}
          </div>
        )}
      </section>

      <div className="pt-2 border-t border-gray-200 dark:border-gray-700">
        {confirmRemove ? (
          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={removing}
              onClick={handleRemove}
              className="flex-1 py-2 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-medium disabled:opacity-50"
            >
              {removing ? 'Retrait…' : `Retirer ${user.display_name}`}
            </button>
            <button
              type="button"
              disabled={removing}
              onClick={() => setConfirmRemove(false)}
              className="px-4 py-2 rounded-lg bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 text-sm"
            >
              Annuler
            </button>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setConfirmRemove(true)}
            className="w-full py-2 text-xs text-gray-500 dark:text-gray-400 hover:text-red-600 transition-colors"
          >
            Retirer des amis
          </button>
        )}
      </div>
    </div>
  );
}
