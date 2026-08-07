/**
 * Panneau "À venir" — prochaines sorties personnalisées
 * (prochains tomes de séries, chapitres manga, livres surveillés).
 * Alimenté par l'endpoint agrégé GET /api/upcoming.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { toast } from 'react-hot-toast';
import {
  XMarkIcon,
  ClockIcon,
  BookOpenIcon,
  MagnifyingGlassIcon,
  PlusIcon,
  ArrowRightIcon,
  TrashIcon,
  ArrowPathIcon,
  CheckIcon,
  CalendarDaysIcon,
  QuestionMarkCircleIcon,
  BellIcon,
} from '@heroicons/react/24/outline';
import { upcomingService } from '../services/upcomingService';

// ── helpers ──────────────────────────────────────────────────────────────────

function formatDateLabel(item) {
  const { date, date_confidence: conf } = item;
  if (!date) return 'Date à confirmer';
  const d = new Date(date);
  if (isNaN(d)) return date;
  if (conf === 'year') return `en ${d.getFullYear()}`;
  if (conf === 'month') return d.toLocaleDateString('fr-FR', { month: 'long', year: 'numeric' });
  if (conf === 'estimated') {
    return `~ ${d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })}`;
  }
  return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });
}

// Classes Tailwind écrites en toutes lettres (le JIT ne détecte pas les classes
// construites dynamiquement type `bg-${color}-100`).
const TYPE_META = {
  next_tome: {
    label: 'Prochain tome',
    badge: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400',
  },
  manga_chapter: {
    label: 'Chapitre manga',
    badge: 'bg-pink-100 text-pink-700 dark:bg-pink-900/30 dark:text-pink-400',
  },
  author_release: {
    label: 'Auteur suivi',
    badge: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
  },
  watchlist: {
    label: 'Surveillé',
    badge: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
  },
};

const GROUP_META = [
  { key: 'available', title: 'Disponibles maintenant', header: 'text-green-600 dark:text-green-400', Icon: CheckIcon },
  { key: 'this_week', title: 'Cette semaine', header: 'text-amber-600 dark:text-amber-400', Icon: ClockIcon },
  { key: 'this_month', title: 'Ce mois-ci', header: 'text-orange-600 dark:text-orange-400', Icon: CalendarDaysIcon },
  { key: 'later', title: 'Plus tard', header: 'text-blue-600 dark:text-blue-400', Icon: CalendarDaysIcon },
  { key: 'unknown', title: 'Date à confirmer', header: 'text-gray-500 dark:text-gray-400', Icon: QuestionMarkCircleIcon },
];

// ── Item card ─────────────────────────────────────────────────────────────────

const ItemCard = ({ item, onMigrate, onRemove, onWatch }) => {
  const [busy, setBusy] = useState(false);
  const [watched, setWatched] = useState(false);
  const meta = TYPE_META[item.type] || TYPE_META.watchlist;
  const isWatchlist = item.type === 'watchlist';

  const handleMigrate = async () => {
    setBusy(true);
    try {
      await onMigrate(item.book_id);
      toast.success(`"${item.title}" déplacé dans "À lire" !`);
    } catch {
      toast.error('Erreur lors du déplacement');
      setBusy(false);
    }
  };

  const handleRemove = async () => {
    try {
      await onRemove(item.book_id);
    } catch {
      toast.error('Erreur lors de la suppression');
    }
  };

  const handleWatch = async () => {
    setWatched(true);
    try {
      await onWatch(item);
      toast.success(`"${item.title}" ajouté à ta surveillance !`);
    } catch {
      setWatched(false);
      toast.error("Erreur lors de l'ajout");
    }
  };

  return (
    <div
      className={`flex gap-3 p-3 rounded-xl border transition-all ${
        item.available
          ? 'bg-green-50 dark:bg-green-900/10 border-green-200 dark:border-green-800'
          : 'bg-white dark:bg-gray-800 border-gray-100 dark:border-gray-700'
      }`}
    >
      <div className="w-12 h-16 flex-shrink-0 rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
        {item.cover_url ? (
          <img
            src={item.cover_url}
            alt={item.title}
            className="w-full h-full object-cover"
            onError={(e) => {
              e.target.style.display = 'none';
            }}
          />
        ) : (
          <BookOpenIcon className="h-6 w-6 text-gray-300" />
        )}
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 dark:text-white line-clamp-2 leading-tight">
          {item.title}
        </p>
        {item.author && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-1">{item.author}</p>
        )}
        <div className="flex flex-wrap items-center gap-1.5 mt-1.5">
          <span
            className={`inline-flex items-center text-[10px] px-1.5 py-0.5 rounded-full font-medium ${meta.badge}`}
          >
            {meta.label}
          </span>
          <span
            className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium ${
              item.available
                ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
            }`}
          >
            {item.available ? <CheckIcon className="h-3 w-3" /> : <ClockIcon className="h-3 w-3" />}
            {item.available ? 'Disponible !' : formatDateLabel(item)}
          </span>
        </div>
      </div>

      <div className="flex flex-col gap-1 flex-shrink-0">
        {isWatchlist && item.available && (
          <button
            onClick={handleMigrate}
            disabled={busy}
            title="Déplacer vers À lire"
            className="p-1.5 rounded-lg bg-green-500 hover:bg-green-600 text-white transition-colors disabled:opacity-50"
          >
            {busy ? (
              <div className="h-3.5 w-3.5 border border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <ArrowRightIcon className="h-3.5 w-3.5" />
            )}
          </button>
        )}
        {isWatchlist ? (
          <button
            onClick={handleRemove}
            title="Retirer"
            className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
          >
            <TrashIcon className="h-3.5 w-3.5" />
          </button>
        ) : item.type === 'next_tome' || item.type === 'author_release' ? (
          watched ? (
            <div className="p-1.5 text-green-500">
              <CheckIcon className="h-4 w-4" />
            </div>
          ) : (
            <button
              onClick={handleWatch}
              title="Surveiller ce tome"
              className="p-1.5 rounded-lg bg-indigo-500 hover:bg-indigo-600 text-white transition-colors"
            >
              <PlusIcon className="h-3.5 w-3.5" />
            </button>
          )
        ) : null}
      </div>
    </div>
  );
};

// ── Main Panel ────────────────────────────────────────────────────────────────

const EMPTY_GROUPS = { available: [], this_week: [], this_month: [], later: [], unknown: [] };

const NOTIF_MODES = [
  { value: 'none', label: 'Aucune notification' },
  { value: 'in_app', label: 'Dans l\'app' },
  { value: 'email', label: 'Par e-mail' },
  { value: 'push', label: 'Notifications navigateur' },
];

const UpcomingPanel = ({ isOpen, onClose }) => {
  const [groups, setGroups] = useState(EMPTY_GROUPS);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [notifMode, setNotifMode] = useState('in_app');
  const [notifications, setNotifications] = useState([]);

  const loadData = useCallback(
    async (refresh = false) => {
      if (!isOpen) return;
      setIsLoading(true);
      try {
        const [data, notifData] = await Promise.all([
          upcomingService.getUpcoming(refresh),
          upcomingService.getNotifications(),
        ]);
        setGroups({ ...EMPTY_GROUPS, ...(data.groups || {}) });
        setTotal(data.counts?.total || 0);
        setNotifications((notifData.notifications || []).filter((n) => !n.read));
      } finally {
        setIsLoading(false);
      }
    },
    [isOpen]
  );

  useEffect(() => {
    // Après un changement de règles backend, forcer 1 refresh (évite l'ancien cache 6h).
    const LOGIC_V = '2';
    const key = 'booktime_upcoming_logic_v';
    const stale = localStorage.getItem(key) !== LOGIC_V;
    loadData(stale);
    if (stale) localStorage.setItem(key, LOGIC_V);
  }, [loadData]);

  useEffect(() => {
    if (!isOpen) return;
    upcomingService.getNotificationSettings().then((s) => setNotifMode(s.notif_upcoming || 'in_app'));
  }, [isOpen]);

  const handleChangeNotifMode = async (mode) => {
    setNotifMode(mode);
    try {
      await upcomingService.setNotificationMode(mode);
      toast.success('Préférence de notification enregistrée');
    } catch {
      toast.error("Erreur lors de l'enregistrement");
    }
  };

  const handleMarkAllRead = async () => {
    setNotifications([]);
    try {
      await upcomingService.markAllNotificationsRead();
    } catch {
      /* silencieux */
    }
  };

  useEffect(() => {
    if (!searchQuery || searchQuery.length < 2) {
      setSearchResults([]);
      return;
    }
    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const results = await upcomingService.searchUpcoming(searchQuery);
        setSearchResults(results);
      } finally {
        setIsSearching(false);
      }
    }, 500);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  const handleMigrate = async (bookId) => {
    await upcomingService.migrateToRead(bookId);
    await loadData(true);
  };

  const handleRemove = async (bookId) => {
    await upcomingService.removeUpcomingBook(bookId);
    await loadData(true);
  };

  const handleWatch = async (item) => {
    await upcomingService.addUpcomingBook(item);
    await loadData(true);
  };

  const handleAddFromSearch = async (book) => {
    await upcomingService.addUpcomingBook(book);
    setSearchResults((prev) => prev.filter((b) => b.title !== book.title));
    setSearchQuery('');
    await loadData(true);
    toast.success(`"${book.title}" ajouté à ta surveillance !`);
  };

  if (!isOpen) return null;

  const hasAny = GROUP_META.some((g) => (groups[g.key] || []).length > 0);

  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-40 transition-opacity" onClick={onClose} />

      <div className="fixed top-0 left-0 h-full w-80 sm:w-96 bg-white dark:bg-gray-900 shadow-2xl z-50 flex flex-col transition-transform duration-300">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
          <div className="flex items-center gap-2">
            <ClockIcon className="h-5 w-5 text-amber-500" />
            <h2 className="text-base font-semibold text-gray-900 dark:text-white">
              À venir
              {total > 0 && (
                <span className="ml-2 text-xs bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 px-2 py-0.5 rounded-full font-medium">
                  {total}
                </span>
              )}
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => loadData(true)}
              disabled={isLoading}
              title="Rafraîchir"
              className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              <ArrowPathIcon className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Recherche */}
        <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-800 flex-shrink-0">
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Ajouter un livre à surveiller..."
              className="w-full pl-9 pr-4 py-2 text-sm bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-booktime-500 dark:text-white"
            />
            {isSearching && (
              <div className="absolute right-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 border border-gray-400 border-t-transparent rounded-full animate-spin" />
            )}
          </div>

          {searchResults.length > 0 && (
            <div className="mt-2 space-y-1.5 max-h-52 overflow-y-auto">
              {searchResults.map((book, idx) => (
                <div
                  key={idx}
                  className="flex items-center gap-2 p-2 rounded-lg bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                >
                  <div className="w-8 h-10 flex-shrink-0 rounded overflow-hidden bg-gray-200 dark:bg-gray-600 flex items-center justify-center">
                    {book.cover_url ? (
                      <img
                        src={book.cover_url}
                        alt={book.title}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.target.style.display = 'none';
                        }}
                      />
                    ) : (
                      <BookOpenIcon className="h-4 w-4 text-gray-400" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-gray-900 dark:text-white line-clamp-1">{book.title}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-1">{book.author}</p>
                  </div>
                  <button
                    onClick={() => handleAddFromSearch(book)}
                    className="p-1.5 rounded-lg bg-blue-500 hover:bg-blue-600 text-white transition-colors flex-shrink-0"
                  >
                    <PlusIcon className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Réglage notifications */}
        <div className="px-4 py-2.5 border-b border-gray-100 dark:border-gray-800 flex items-center gap-2 flex-shrink-0">
          <BellIcon className="h-4 w-4 text-gray-400 flex-shrink-0" />
          <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">Me prévenir :</span>
          <select
            value={notifMode}
            onChange={(e) => handleChangeNotifMode(e.target.value)}
            className="flex-1 text-xs bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-2 py-1 focus:outline-none focus:ring-1 focus:ring-booktime-500 dark:text-white"
          >
            {NOTIF_MODES.map((m) => (
              <option key={m.value} value={m.value}>
                {m.label}
              </option>
            ))}
          </select>
        </div>

        {/* Notifications non lues */}
        {notifications.length > 0 && (
          <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-800 flex-shrink-0 bg-blue-50/50 dark:bg-blue-900/10">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-blue-600 dark:text-blue-400 flex items-center gap-1.5">
                <BellIcon className="h-3.5 w-3.5" />
                Notifications ({notifications.length})
              </h3>
              <button
                onClick={handleMarkAllRead}
                className="text-xs text-blue-500 hover:text-blue-600 dark:text-blue-400"
              >
                Tout marquer lu
              </button>
            </div>
            <div className="space-y-1.5 max-h-40 overflow-y-auto">
              {notifications.map((n) => (
                <div key={n.id} className="text-xs px-2.5 py-1.5 rounded-lg bg-white dark:bg-gray-800 border border-blue-100 dark:border-blue-900/40">
                  <p className="font-medium text-gray-900 dark:text-white line-clamp-1">{n.title}</p>
                  {n.body && <p className="text-gray-500 dark:text-gray-400 line-clamp-1">{n.body}</p>}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Contenu scrollable */}
        <div className="flex-1 overflow-y-auto px-4 py-3 space-y-6">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-16 gap-3">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-amber-500 border-t-transparent" />
              <p className="text-sm text-gray-500 dark:text-gray-400">Chargement...</p>
            </div>
          ) : hasAny ? (
            GROUP_META.map(({ key, title, header, Icon }) => {
              const list = groups[key] || [];
              if (list.length === 0) return null;
              return (
                <section key={key}>
                  <h3
                    className={`text-xs font-semibold uppercase tracking-wider ${header} mb-2 flex items-center gap-1.5`}
                  >
                    <Icon className="h-3.5 w-3.5" />
                    {title} ({list.length})
                  </h3>
                  <div className="space-y-2">
                    {list.map((item) => (
                      <ItemCard
                        key={item.id}
                        item={item}
                        onMigrate={handleMigrate}
                        onRemove={handleRemove}
                        onWatch={handleWatch}
                      />
                    ))}
                  </div>
                </section>
              );
            })
          ) : (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <span className="text-5xl mb-4">📅</span>
              <h3 className="text-base font-medium text-gray-700 dark:text-gray-300 mb-2">
                Aucune sortie à venir
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400 max-w-xs">
                Ajoute des séries à ta bibliothèque pour voir leurs prochains tomes, ou surveille un
                livre via la recherche ci-dessus.
              </p>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default UpcomingPanel;
