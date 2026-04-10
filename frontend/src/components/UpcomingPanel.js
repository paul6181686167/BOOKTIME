/**
 * Panneau "À venir" — livres à paraître, prochains tomes, auteurs suivis
 */
import React, { useState, useEffect, useCallback } from 'react';
import { toast } from 'react-hot-toast';
import {
  XMarkIcon,
  ClockIcon,
  BookOpenIcon,
  MagnifyingGlassIcon,
  UserIcon,
  PlusIcon,
  ArrowRightIcon,
  TrashIcon,
  ArrowPathIcon,
  CheckIcon,
} from '@heroicons/react/24/outline';
import { upcomingService } from '../services/upcomingService';

// ── helpers ──────────────────────────────────────────────────────────────────

function formatDate(dateStr) {
  if (!dateStr) return 'Date inconnue';
  const d = new Date(dateStr);
  if (isNaN(d)) return dateStr;
  return d.toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' });
}

function isReleased(dateStr) {
  if (!dateStr) return false;
  return dateStr.substring(0, 10) <= new Date().toISOString().substring(0, 10);
}

// ── Mini-card ─────────────────────────────────────────────────────────────────

const UpcomingCard = ({ book, onMigrate, onRemove, released = false }) => {
  const [loading, setLoading] = useState(false);

  const handleMigrate = async () => {
    setLoading(true);
    try {
      await onMigrate(book.id);
      toast.success(`"${book.title}" déplacé dans "À lire" !`);
    } catch {
      toast.error('Erreur lors du déplacement');
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = async () => {
    try {
      await onRemove(book.id);
    } catch {
      toast.error('Erreur lors de la suppression');
    }
  };

  return (
    <div className={`flex gap-3 p-3 rounded-xl border transition-all ${
      released
        ? 'bg-green-50 dark:bg-green-900/10 border-green-200 dark:border-green-800'
        : 'bg-white dark:bg-gray-800 border-gray-100 dark:border-gray-700'
    }`}>
      {/* Cover */}
      <div className="w-12 h-16 flex-shrink-0 rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
        {book.cover_url ? (
          <img src={book.cover_url} alt={book.title} className="w-full h-full object-cover" onError={(e) => { e.target.style.display = 'none'; }} />
        ) : (
          <BookOpenIcon className="h-6 w-6 text-gray-300" />
        )}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 dark:text-white line-clamp-2 leading-tight">{book.title}</p>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{book.author}</p>
        <div className={`inline-flex items-center gap-1 mt-1.5 text-xs px-2 py-0.5 rounded-full font-medium ${
          released
            ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
            : 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
        }`}>
          {released ? <CheckIcon className="h-3 w-3" /> : <ClockIcon className="h-3 w-3" />}
          {released ? 'Disponible !' : formatDate(book.publish_date || book.published_date)}
        </div>
      </div>

      {/* Actions */}
      <div className="flex flex-col gap-1 flex-shrink-0">
        {released && (
          <button
            onClick={handleMigrate}
            disabled={loading}
            title="Déplacer vers À lire"
            className="p-1.5 rounded-lg bg-green-500 hover:bg-green-600 text-white transition-colors disabled:opacity-50"
          >
            {loading
              ? <div className="h-3.5 w-3.5 border border-white border-t-transparent rounded-full animate-spin" />
              : <ArrowRightIcon className="h-3.5 w-3.5" />
            }
          </button>
        )}
        <button
          onClick={handleRemove}
          title="Retirer"
          className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
        >
          <TrashIcon className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
};

// ── Next tome suggestion card ────────────────────────────────────────────────

const NextTomeCard = ({ suggestion, onAdd }) => {
  const [added, setAdded] = useState(false);

  const handleAdd = async () => {
    setAdded(true);
    try {
      await onAdd(suggestion);
      toast.success(`"${suggestion.title}" ajouté aux À venir !`);
    } catch {
      setAdded(false);
      toast.error('Erreur lors de l\'ajout');
    }
  };

  return (
    <div className="flex gap-3 p-3 rounded-xl border bg-indigo-50 dark:bg-indigo-900/10 border-indigo-100 dark:border-indigo-800">
      <div className="w-12 h-16 flex-shrink-0 rounded-lg overflow-hidden bg-indigo-100 dark:bg-indigo-800 flex items-center justify-center">
        {suggestion.cover_url ? (
          <img src={suggestion.cover_url} alt={suggestion.title} className="w-full h-full object-cover" onError={(e) => { e.target.style.display = 'none'; }} />
        ) : (
          <BookOpenIcon className="h-6 w-6 text-indigo-300" />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 dark:text-white line-clamp-2 leading-tight">{suggestion.title}</p>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{suggestion.author}</p>
        <p className="text-xs text-indigo-500 dark:text-indigo-400 mt-1 italic">{suggestion.reason}</p>
      </div>
      <div className="flex-shrink-0">
        {added ? (
          <div className="p-1.5 text-green-500"><CheckIcon className="h-4 w-4" /></div>
        ) : (
          <button
            onClick={handleAdd}
            title="Surveiller ce tome"
            className="p-1.5 rounded-lg bg-indigo-500 hover:bg-indigo-600 text-white transition-colors"
          >
            <PlusIcon className="h-3.5 w-3.5" />
          </button>
        )}
      </div>
    </div>
  );
};

// ── Main Panel ────────────────────────────────────────────────────────────────

const UpcomingPanel = ({ isOpen, onClose, userBooks = [] }) => {
  const [upcomingBooks, setUpcomingBooks] = useState([]);
  const [nextTomes, setNextTomes] = useState([]);
  const [followedAuthors, setFollowedAuthors] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  const [migratedIds, setMigratedIds] = useState(new Set());

  const loadData = useCallback(async () => {
    if (!isOpen) return;
    setIsLoading(true);
    try {
      const [books, migrated] = await Promise.allSettled([
        upcomingService.getUpcomingBooks(),
        upcomingService.autoMigrateReleasedBooks(),
      ]);

      const booksData = books.status === 'fulfilled' ? books.value : [];
      setUpcomingBooks(booksData);

      if (migrated.status === 'fulfilled' && migrated.value > 0) {
        toast.success(`${migrated.value} livre${migrated.value > 1 ? 's' : ''} déplacé${migrated.value > 1 ? 's' : ''} dans "À lire" automatiquement !`);
        // Rechargement après migration
        const refreshed = await upcomingService.getUpcomingBooks();
        setUpcomingBooks(refreshed);
      }
    } finally {
      setIsLoading(false);
    }
  }, [isOpen]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    const tomes = upcomingService.computeNextTomes(userBooks);
    setNextTomes(tomes);
    setFollowedAuthors(upcomingService.getFollowedAuthors());
  }, [userBooks]);

  // Recherche debounced
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
    setMigratedIds((prev) => new Set([...prev, bookId]));
    setUpcomingBooks((prev) => prev.filter((b) => b.id !== bookId));
  };

  const handleRemove = async (bookId) => {
    await upcomingService.removeUpcomingBook(bookId);
    setUpcomingBooks((prev) => prev.filter((b) => b.id !== bookId));
  };

  const handleAddNextTome = async (suggestion) => {
    await upcomingService.addUpcomingBook(suggestion);
    // Retirer la suggestion après ajout
    setNextTomes((prev) => prev.filter((t) => t.title !== suggestion.title));
  };

  const handleAddFromSearch = async (book) => {
    await upcomingService.addUpcomingBook(book);
    setSearchResults((prev) => prev.filter((b) => b.title !== book.title));
    setSearchQuery('');
    const refreshed = await upcomingService.getUpcomingBooks();
    setUpcomingBooks(refreshed);
    toast.success(`"${book.title}" ajouté aux À venir !`);
  };

  const releasedBooks = upcomingBooks.filter((b) => isReleased(b.publish_date || b.published_date));
  const pendingBooks = upcomingBooks.filter((b) => !isReleased(b.publish_date || b.published_date));
  const total = upcomingBooks.length;

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/50 z-40 transition-opacity"
        onClick={onClose}
      />

      {/* Panel */}
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
            <button onClick={loadData} disabled={isLoading} className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
              <ArrowPathIcon className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
            <button onClick={onClose} className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
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
              className="w-full pl-9 pr-4 py-2 text-sm bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"
            />
            {isSearching && (
              <div className="absolute right-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 border border-gray-400 border-t-transparent rounded-full animate-spin" />
            )}
          </div>

          {/* Résultats de recherche */}
          {searchResults.length > 0 && (
            <div className="mt-2 space-y-1.5 max-h-52 overflow-y-auto">
              {searchResults.map((book, idx) => (
                <div key={idx} className="flex items-center gap-2 p-2 rounded-lg bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
                  <div className="w-8 h-10 flex-shrink-0 rounded overflow-hidden bg-gray-200 dark:bg-gray-600 flex items-center justify-center">
                    {book.cover_url
                      ? <img src={book.cover_url} alt={book.title} className="w-full h-full object-cover" onError={(e) => { e.target.style.display = 'none'; }} />
                      : <BookOpenIcon className="h-4 w-4 text-gray-400" />
                    }
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

        {/* Contenu scrollable */}
        <div className="flex-1 overflow-y-auto px-4 py-3 space-y-6">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-16 gap-3">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-amber-500 border-t-transparent" />
              <p className="text-sm text-gray-500 dark:text-gray-400">Chargement...</p>
            </div>
          ) : (
            <>
              {/* Disponibles maintenant */}
              {releasedBooks.length > 0 && (
                <section>
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-green-600 dark:text-green-400 mb-2 flex items-center gap-1.5">
                    <CheckIcon className="h-3.5 w-3.5" />
                    Disponibles maintenant ({releasedBooks.length})
                  </h3>
                  <div className="space-y-2">
                    {releasedBooks.map((book) => (
                      <UpcomingCard key={book.id} book={book} onMigrate={handleMigrate} onRemove={handleRemove} released />
                    ))}
                  </div>
                </section>
              )}

              {/* En attente */}
              {pendingBooks.length > 0 && (
                <section>
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-amber-600 dark:text-amber-400 mb-2 flex items-center gap-1.5">
                    <ClockIcon className="h-3.5 w-3.5" />
                    En attente ({pendingBooks.length})
                  </h3>
                  <div className="space-y-2">
                    {pendingBooks.map((book) => (
                      <UpcomingCard key={book.id} book={book} onMigrate={handleMigrate} onRemove={handleRemove} />
                    ))}
                  </div>
                </section>
              )}

              {/* Prochains tomes suggérés */}
              {nextTomes.length > 0 && (
                <section>
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-indigo-600 dark:text-indigo-400 mb-2 flex items-center gap-1.5">
                    <BookOpenIcon className="h-3.5 w-3.5" />
                    Prochains tomes de tes séries
                  </h3>
                  <div className="space-y-2">
                    {nextTomes.map((t, i) => (
                      <NextTomeCard key={i} suggestion={t} onAdd={handleAddNextTome} />
                    ))}
                  </div>
                </section>
              )}

              {/* Auteurs suivis */}
              {followedAuthors.length > 0 && (
                <section>
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-purple-600 dark:text-purple-400 mb-2 flex items-center gap-1.5">
                    <UserIcon className="h-3.5 w-3.5" />
                    Auteurs suivis ({followedAuthors.length})
                  </h3>
                  <div className="space-y-1.5">
                    {followedAuthors.map((author, i) => (
                      <div key={i} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-purple-50 dark:bg-purple-900/10 border border-purple-100 dark:border-purple-800">
                        <UserIcon className="h-4 w-4 text-purple-400 flex-shrink-0" />
                        <span className="text-sm text-gray-800 dark:text-gray-200 flex-1">{author}</span>
                        <span className="text-xs text-purple-400 dark:text-purple-500 italic">Notifications actives</span>
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {/* État vide */}
              {total === 0 && nextTomes.length === 0 && followedAuthors.length === 0 && (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <span className="text-5xl mb-4">📅</span>
                  <h3 className="text-base font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Aucune sortie à venir
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400 max-w-xs">
                    Utilise la recherche ci-dessus pour surveiller un livre, ou suis des auteurs depuis leurs fiches.
                  </p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </>
  );
};

export default UpcomingPanel;
