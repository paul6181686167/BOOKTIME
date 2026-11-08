import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import toast from 'react-hot-toast';
import friendsService, { bookRefToBookLike, toBookRef } from '../../services/friendsService';
import { refreshFriendsUnread } from '../../hooks/useFriendsUnread';
import BookRefCard, { MiniCover } from './BookRefCard';

const POLL_MS = 4000;

function formatTime(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  const now = new Date();
  const time = d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  if (d.toDateString() === now.toDateString()) return time;
  return `${d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' })} ${time}`;
}

/** Choix d'un livre de sa bibliothèque à recommander. */
function BookPicker({ libraryBooks, onPick, onClose }) {
  const [q, setQ] = useState('');
  const choices = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return (libraryBooks || [])
      .filter((b) => b && !b.isSeriesCard && b.title)
      .filter(
        (b) =>
          !needle ||
          b.title.toLowerCase().includes(needle) ||
          String(b.author || '').toLowerCase().includes(needle)
      )
      .slice(0, 50);
  }, [libraryBooks, q]);

  return (
    <div className="absolute inset-0 z-10 flex flex-col bg-[#f3faf6] dark:bg-gray-800">
      <div className="flex items-center gap-2 p-3 border-b border-gray-200 dark:border-gray-700">
        <input
          autoFocus
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Chercher dans ta bibliothèque"
          aria-label="Chercher un livre à recommander"
          className="flex-1 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-green-500"
        />
        <button
          type="button"
          onClick={onClose}
          className="px-3 py-2 text-sm text-gray-600 dark:text-gray-300"
        >
          Annuler
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-3 space-y-1.5">
        {choices.length === 0 ? (
          <p className="text-sm text-center text-gray-500 dark:text-gray-400 py-8">Aucun livre trouvé.</p>
        ) : (
          choices.map((b) => (
            <BookRefCard key={b.id} book={toBookRef(b)} onOpen={onPick} />
          ))
        )}
      </div>
    </div>
  );
}

function Bubble({ message, onOpenBook }) {
  const mine = message.mine;
  return (
    <div className={`flex ${mine ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[82%] rounded-2xl px-3 py-2 space-y-2 ${
          mine
            ? 'bg-green-600 text-white rounded-br-sm'
            : 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white border border-gray-100 dark:border-gray-600 rounded-bl-sm'
        }`}
      >
        {message.book && (
          <BookRefCard
            book={message.book}
            tone={mine ? 'onGreen' : 'light'}
            onOpen={(b) => onOpenBook(bookRefToBookLike(b))}
          />
        )}
        {message.text ? (
          <p className="text-sm whitespace-pre-line break-words">{message.text}</p>
        ) : null}
        <p className={`text-tiny ${mine ? 'text-green-100' : 'text-gray-500 dark:text-gray-400'}`}>
          {formatTime(message.created_at)}
        </p>
      </div>
    </div>
  );
}

/** Conversation avec un ami : messages et recommandations de livres. */
export default function FriendChat({ friend, libraryBooks, initialBook, onOpenBook }) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [text, setText] = useState('');
  const [draftBook, setDraftBook] = useState(initialBook || null);
  const [picking, setPicking] = useState(false);
  const [sending, setSending] = useState(false);
  const listRef = useRef(null);
  const lastAtRef = useRef(null);
  const stickToBottom = useRef(true);

  const append = useCallback((incoming) => {
    if (!incoming.length) return;
    setMessages((prev) => {
      const known = new Set(prev.map((m) => m.id));
      const fresh = incoming.filter((m) => !known.has(m.id));
      return fresh.length ? [...prev, ...fresh] : prev;
    });
    lastAtRef.current = incoming[incoming.length - 1].created_at;
  }, []);

  useEffect(() => {
    let cancelled = false;
    lastAtRef.current = null;
    setMessages([]);
    setLoading(true);
    friendsService
      .getMessages(friend.id)
      .then((res) => {
        if (cancelled) return;
        append(res.messages || []);
        setError('');
        refreshFriendsUnread();
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || 'Messages indisponibles');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    // Pas de connexion temps réel : on vérifie régulièrement s'il y a du nouveau
    const timer = setInterval(async () => {
      if (document.visibilityState !== 'visible') return;
      try {
        const res = await friendsService.getMessages(friend.id, lastAtRef.current);
        if (!cancelled) append(res.messages || []);
      } catch (_) {
        /* une coupure réseau passagère ne doit pas casser la conversation */
      }
    }, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [friend.id, append]);

  useEffect(() => {
    const el = listRef.current;
    if (el && stickToBottom.current) el.scrollTop = el.scrollHeight;
  }, [messages, loading]);

  const handleScroll = () => {
    const el = listRef.current;
    if (!el) return;
    stickToBottom.current = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
  };

  const handleSend = async () => {
    const body = text.trim();
    if ((!body && !draftBook) || sending) return;
    setSending(true);
    try {
      const res = await friendsService.sendMessage(friend.id, { text: body, book: draftBook });
      stickToBottom.current = true;
      append([res.message]);
      setText('');
      setDraftBook(null);
    } catch (err) {
      toast.error(err.message || 'Envoi impossible');
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="relative flex flex-col flex-1 min-h-0">
      <div
        ref={listRef}
        onScroll={handleScroll}
        className="flex-1 min-h-0 overflow-y-auto p-4 space-y-3"
      >
        {loading ? (
          <p className="text-sm text-center text-gray-500 dark:text-gray-400 py-8">Chargement…</p>
        ) : error ? (
          <p className="text-sm text-center text-amber-700 dark:text-amber-300 py-8">{error}</p>
        ) : messages.length === 0 ? (
          <div className="text-center py-10 text-gray-500 dark:text-gray-400">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
              Commence la conversation avec {friend.display_name}
            </p>
            <p className="text-xs mt-1">Utilise « Livre » pour lui recommander une lecture.</p>
          </div>
        ) : (
          messages.map((m) => <Bubble key={m.id} message={m} onOpenBook={onOpenBook} />)
        )}
      </div>

      <div className="shrink-0 border-t border-gray-200 dark:border-gray-700 p-3 space-y-2 bg-[#f3faf6] dark:bg-gray-800">
        {draftBook && (
          <div className="flex items-center gap-2 p-2 rounded-lg bg-white dark:bg-gray-700 border border-green-200 dark:border-green-800">
            <MiniCover url={draftBook.cover_url} className="w-8 h-11" />
            <div className="min-w-0 flex-1">
              <p className="text-xs text-green-700 dark:text-green-300 font-medium">Livre recommandé</p>
              <p className="text-sm text-gray-900 dark:text-white truncate">{draftBook.title}</p>
            </div>
            <button
              type="button"
              onClick={() => setDraftBook(null)}
              aria-label="Retirer le livre"
              className="px-2 py-1 text-gray-500 dark:text-gray-400 hover:text-red-600"
            >
              ✕
            </button>
          </div>
        )}
        <div className="flex items-end gap-2">
          <button
            type="button"
            onClick={() => setPicking(true)}
            className="shrink-0 px-3 py-2 rounded-lg border border-green-600 text-green-700 dark:text-green-400 text-sm font-medium hover:bg-green-50 dark:hover:bg-green-900/20"
          >
            Livre
          </button>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            rows={1}
            maxLength={1000}
            placeholder={draftBook ? 'Ajoute un mot (facultatif)' : 'Écris un message'}
            aria-label="Message"
            className="flex-1 max-h-28 resize-none px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-green-500"
          />
          <button
            type="button"
            onClick={handleSend}
            disabled={sending || (!text.trim() && !draftBook)}
            className="shrink-0 px-4 py-2 rounded-lg bg-green-600 hover:bg-green-700 text-white text-sm font-medium disabled:opacity-40"
          >
            Envoyer
          </button>
        </div>
      </div>

      {picking && (
        <BookPicker
          libraryBooks={libraryBooks}
          onClose={() => setPicking(false)}
          onPick={(ref) => {
            setDraftBook(ref);
            setPicking(false);
          }}
        />
      )}
    </div>
  );
}
