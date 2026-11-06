import React, { useCallback, useEffect, useRef, useState } from 'react';
import toast from 'react-hot-toast';
import friendsService from '../../services/friendsService';
import { UserAvatar } from '../common/ProfileIdentityCard';

const REFRESH_MS = 15000;

function preview(last) {
  if (!last) return 'Aucun message pour le moment';
  const prefix = last.mine ? 'Toi : ' : '';
  if (last.has_book) return `${prefix}a recommandé « ${last.book_title} »`;
  return `${prefix}${last.text}`;
}

/** Liste d'amis, demandes en attente et recherche de lecteurs. */
export default function FriendsHome({ recommendBook, onOpenChat, onOpenProfile, onCountsChange }) {
  const [friends, setFriends] = useState([]);
  const [requests, setRequests] = useState({ incoming: [], outgoing: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [searching, setSearching] = useState(false);
  const [busyId, setBusyId] = useState(null);
  const searchSeq = useRef(0);

  const load = useCallback(async () => {
    try {
      const [f, r] = await Promise.all([friendsService.listFriends(), friendsService.listRequests()]);
      setFriends(f.friends || []);
      setRequests({ incoming: r.incoming || [], outgoing: r.outgoing || [] });
      setError('');
      onCountsChange?.({
        unread: (f.friends || []).reduce((s, x) => s + (x.unread || 0), 0),
        pending: (r.incoming || []).length,
      });
    } catch (err) {
      setError(err.message || 'Chargement impossible');
    } finally {
      setLoading(false);
    }
  }, [onCountsChange]);

  useEffect(() => {
    load();
    const timer = setInterval(() => {
      if (document.visibilityState === 'visible') load();
    }, REFRESH_MS);
    return () => clearInterval(timer);
  }, [load]);

  // Recherche avec délai : évite une requête à chaque touche
  useEffect(() => {
    const q = query.trim();
    if (q.length < 2 && !q.includes('@')) {
      setResults(null);
      setSearching(false);
      return undefined;
    }
    setSearching(true);
    const seq = ++searchSeq.current;
    const timer = setTimeout(async () => {
      try {
        const data = await friendsService.search(q);
        if (seq === searchSeq.current) setResults(data.users || []);
      } catch (err) {
        if (seq === searchSeq.current) {
          setResults([]);
          toast.error(err.message || 'Recherche impossible');
        }
      } finally {
        if (seq === searchSeq.current) setSearching(false);
      }
    }, 350);
    return () => clearTimeout(timer);
  }, [query]);

  const run = async (id, action, successMessage) => {
    setBusyId(id);
    try {
      await action();
      if (successMessage) toast.success(successMessage);
      await load();
      return true;
    } catch (err) {
      toast.error(err.message || 'Action impossible');
      return false;
    } finally {
      setBusyId(null);
    }
  };

  const addFriend = async (user) => {
    const ok = await run(user.id, () => friendsService.sendRequest(user.id), 'Demande envoyée');
    if (ok) {
      setResults((list) =>
        (list || []).map((u) =>
          u.id === user.id ? { ...u, state: u.state === 'pending_in' ? 'friends' : 'pending_out' } : u
        )
      );
    }
  };

  const searchAction = (user) => {
    if (user.state === 'friends') return <span className="text-xs text-green-600 font-medium">Ami</span>;
    if (user.state === 'pending_out')
      return <span className="text-xs text-gray-500">Demande envoyée</span>;
    return (
      <button
        type="button"
        disabled={busyId === user.id}
        onClick={() => addFriend(user)}
        className="px-3 py-1.5 rounded-lg bg-green-600 hover:bg-green-700 text-white text-xs font-medium disabled:opacity-50"
      >
        {user.state === 'pending_in' ? 'Accepter' : 'Ajouter'}
      </button>
    );
  };

  const searchActive = results !== null || searching;

  return (
    <div className="space-y-5">
      {recommendBook && (
        <div className="rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 p-3 text-sm text-green-800 dark:text-green-200">
          Choisis l’ami à qui recommander « {recommendBook.title} ».
        </div>
      )}

      <div>
        <input
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Trouver un lecteur (nom ou adresse email)"
          aria-label="Trouver un lecteur"
          className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-green-500"
        />
        {searchActive && (
          <div className="mt-2 space-y-1.5">
            {searching && results === null ? (
              <p className="text-xs text-gray-500 px-1">Recherche…</p>
            ) : results.length === 0 ? (
              <p className="text-xs text-gray-500 px-1">
                Aucun lecteur trouvé. Les lecteurs se trouvent par leur nom affiché ou leur adresse
                email complète.
              </p>
            ) : (
              results.map((u) => (
                <div
                  key={u.id}
                  className="flex items-center gap-3 p-2.5 rounded-lg bg-white dark:bg-gray-700/50 border border-gray-100 dark:border-gray-700"
                >
                  <UserAvatar user={u} size={40} />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {u.display_name}
                    </p>
                    {u.bio ? (
                      <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{u.bio}</p>
                    ) : null}
                  </div>
                  {searchAction(u)}
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {requests.incoming.length > 0 && !recommendBook && (
        <section>
          <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">
            Demandes reçues ({requests.incoming.length})
          </h3>
          <div className="space-y-1.5">
            {requests.incoming.map((r) => (
              <div
                key={r.request_id}
                className="flex items-center gap-3 p-2.5 rounded-lg bg-white dark:bg-gray-700/50 border border-green-200 dark:border-green-800"
              >
                <UserAvatar user={r.user} size={40} />
                <p className="min-w-0 flex-1 text-sm font-medium text-gray-900 dark:text-white truncate">
                  {r.user.display_name}
                </p>
                <button
                  type="button"
                  disabled={busyId === r.request_id}
                  onClick={() =>
                    run(r.request_id, () => friendsService.acceptRequest(r.request_id), 'Ami ajouté')
                  }
                  className="px-3 py-1.5 rounded-lg bg-green-600 hover:bg-green-700 text-white text-xs font-medium disabled:opacity-50"
                >
                  Accepter
                </button>
                <button
                  type="button"
                  disabled={busyId === r.request_id}
                  onClick={() => run(r.request_id, () => friendsService.declineRequest(r.request_id))}
                  className="px-3 py-1.5 rounded-lg bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200 text-xs font-medium disabled:opacity-50"
                >
                  Refuser
                </button>
              </div>
            ))}
          </div>
        </section>
      )}

      {requests.outgoing.length > 0 && !recommendBook && (
        <section>
          <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">
            Demandes envoyées
          </h3>
          <div className="space-y-1.5">
            {requests.outgoing.map((r) => (
              <div
                key={r.request_id}
                className="flex items-center gap-3 p-2.5 rounded-lg bg-white dark:bg-gray-700/50 border border-gray-100 dark:border-gray-700"
              >
                <UserAvatar user={r.user} size={36} />
                <p className="min-w-0 flex-1 text-sm text-gray-800 dark:text-gray-200 truncate">
                  {r.user.display_name}
                </p>
                <button
                  type="button"
                  disabled={busyId === r.request_id}
                  onClick={() => run(r.request_id, () => friendsService.declineRequest(r.request_id))}
                  className="text-xs text-gray-500 hover:text-red-600 px-2 py-1"
                >
                  Annuler
                </button>
              </div>
            ))}
          </div>
        </section>
      )}

      <section>
        <h3 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400 mb-2">
          Mes amis{friends.length ? ` (${friends.length})` : ''}
        </h3>
        {loading ? (
          <div className="space-y-2">
            {[0, 1, 2].map((i) => (
              <div key={i} className="h-14 rounded-lg bg-gray-200 dark:bg-gray-700 animate-pulse" />
            ))}
          </div>
        ) : error ? (
          <div className="text-center py-6 space-y-2">
            <p className="text-sm text-amber-700 dark:text-amber-300">{error}</p>
            <button
              type="button"
              onClick={load}
              className="px-3 py-1.5 rounded-lg border border-green-600 text-green-700 dark:text-green-400 text-sm"
            >
              Réessayer
            </button>
          </div>
        ) : friends.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Aucun ami pour le moment</p>
            <p className="text-xs mt-1">Cherche un lecteur ci-dessus pour lui envoyer une demande.</p>
          </div>
        ) : (
          <div className="space-y-1.5">
            {friends.map((f) => (
              <div
                key={f.id}
                className="flex items-center gap-1 rounded-lg bg-white dark:bg-gray-700/50 border border-gray-100 dark:border-gray-700"
              >
                <button
                  type="button"
                  onClick={() => onOpenChat(f)}
                  className="flex-1 min-w-0 flex items-center gap-3 p-2.5 text-left"
                >
                  <UserAvatar user={f} size={44} />
                  <span className="min-w-0 flex-1">
                    <span className="block text-sm font-semibold text-gray-900 dark:text-white truncate">
                      {f.display_name}
                    </span>
                    <span
                      className={`block text-xs truncate ${
                        f.unread
                          ? 'text-gray-900 dark:text-white font-medium'
                          : 'text-gray-500 dark:text-gray-400'
                      }`}
                    >
                      {preview(f.last_message)}
                    </span>
                  </span>
                  {f.unread > 0 && (
                    <span className="min-w-[1.25rem] h-5 px-1.5 rounded-full bg-green-600 text-white text-[11px] font-bold flex items-center justify-center">
                      {f.unread}
                    </span>
                  )}
                </button>
                {!recommendBook && (
                  <button
                    type="button"
                    onClick={() => onOpenProfile(f)}
                    className="shrink-0 mr-2 px-2.5 py-1.5 rounded-lg text-xs font-medium text-green-700 dark:text-green-400 hover:bg-green-50 dark:hover:bg-green-900/20"
                  >
                    Profil
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
