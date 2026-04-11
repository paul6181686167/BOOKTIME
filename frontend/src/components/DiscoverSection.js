/**
 * Section "Découvrir" — affichée quand la bibliothèque est vide ou sur demande.
 * Charge des livres populaires depuis /api/catalog/popular.
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import {
  SparklesIcon,
  PlusIcon,
  CheckIcon,
  BookOpenIcon,
  FireIcon,
} from '@heroicons/react/24/outline';
import { API_BASE_URL } from '../config/environment';

function catalogPath(olKey) {
  if (!olKey) return null;
  // /works/OL12345W → /catalogue/works/OL12345W
  const stripped = olKey.startsWith('/') ? olKey.slice(1) : olKey;
  return `/catalogue/${stripped}`;
}

// ── helpers ──────────────────────────────────────────────────────────────────

function authHeaders() {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// ── Book mini-card ────────────────────────────────────────────────────────────

const DiscoverCard = ({ book, onAdd, alreadyOwned }) => {
  const navigate = useNavigate();
  const [adding, setAdding] = useState(false);
  const [added, setAdded] = useState(false);
  const path = catalogPath(book.ol_key);

  const handleAdd = async () => {
    if (adding || added || alreadyOwned) return;
    setAdding(true);
    try {
      await onAdd(book);
      setAdded(true);
    } catch {
      toast.error('Erreur lors de l\'ajout');
    } finally {
      setAdding(false);
    }
  };

  const isAdded = added || alreadyOwned;

  return (
    <div className="flex flex-col w-full bg-white dark:bg-gray-800 rounded-xl border border-gray-100 dark:border-gray-700 overflow-hidden hover:shadow-md transition-shadow duration-200 group">
      {/* Couverture cliquable */}
      <div
        className={`relative h-40 sm:h-44 bg-gray-100 dark:bg-gray-700 overflow-hidden flex items-center justify-center ${path ? 'cursor-pointer' : ''}`}
        onClick={() => path && navigate(path)}
        title={path ? 'Voir la fiche' : ''}
      >
        {book.cover_url ? (
          <img
            src={book.cover_url}
            alt={book.title}
            className="h-full w-full object-cover group-hover:scale-105 transition-transform duration-300"
            onError={(e) => { e.target.style.display = 'none'; }}
          />
        ) : (
          <BookOpenIcon className="h-12 w-12 text-gray-300" />
        )}

        {/* Badge catégorie */}
        {book.category === 'manga' && (
          <span className="absolute top-2 left-2 bg-orange-500 text-white text-xs px-2 py-0.5 rounded-full font-semibold">Manga</span>
        )}
        {book.category === 'bd' && (
          <span className="absolute top-2 left-2 bg-purple-500 text-white text-xs px-2 py-0.5 rounded-full font-semibold">BD</span>
        )}
      </div>

      {/* Infos */}
      <div className="flex flex-col flex-1 p-3 gap-1">
        <h3
          className={`text-sm font-semibold text-gray-900 dark:text-white line-clamp-2 leading-tight ${path ? 'cursor-pointer hover:text-blue-600 dark:hover:text-blue-400 transition-colors' : ''}`}
          onClick={() => path && navigate(path)}
        >
          {book.title}
        </h3>
        <p className="text-xs text-gray-500 dark:text-gray-400 line-clamp-1">{book.author}</p>

        <div className="mt-auto pt-2">
          {isAdded ? (
            <div className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400 font-medium">
              <CheckIcon className="h-4 w-4" />
              {alreadyOwned ? 'Déjà dans ta bibliothèque' : 'Ajouté !'}
            </div>
          ) : (
            <button
              onClick={handleAdd}
              disabled={adding}
              className="btn-ripple w-full flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-blue-600 hover:bg-blue-700 active:bg-blue-800 text-white rounded-lg transition-colors disabled:opacity-60"
            >
              {adding
                ? <span className="btn-spinner" style={{width:'0.7rem',height:'0.7rem',borderWidth:'1.5px'}} />
                : <PlusIcon className="h-3.5 w-3.5" />
              }
              {adding ? 'Ajout…' : 'Ajouter'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// ── Main component ────────────────────────────────────────────────────────────

const DiscoverSection = ({ activeCategory = 'roman', userBooks = [], onBookAdded }) => {
  const [books, setBooks] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [catalogReady, setCatalogReady] = useState(true);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  const PAGE_SIZE = 24;

  const loadBooks = useCallback(async (reset = false) => {
    setIsLoading(true);
    const offset = reset ? 0 : page * PAGE_SIZE;
    const cat = activeCategory === 'graphic_novel' ? 'graphic_novel' : activeCategory;

    try {
      const res = await fetch(
        `${API_BASE_URL}/api/catalog/popular?category=${cat}&limit=${PAGE_SIZE}&offset=${offset}`,
        { headers: authHeaders() }
      );

      if (!res.ok) throw new Error('catalog error');
      const data = await res.json();

      if (data.total === 0 && offset === 0) {
        setCatalogReady(false);
      } else {
        setCatalogReady(true);
        if (reset) {
          setBooks(data.books || []);
          setPage(1);
        } else {
          setBooks((prev) => [...prev, ...(data.books || [])]);
          setPage((p) => p + 1);
        }
        setHasMore((data.books || []).length === PAGE_SIZE);
      }
    } catch {
      setCatalogReady(false);
    } finally {
      setIsLoading(false);
    }
  }, [activeCategory, page]);

  // Reset + reload à chaque changement de catégorie
  useEffect(() => {
    setBooks([]);
    setPage(0);
    setHasMore(true);
    loadBooks(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeCategory]);

  const handleAdd = async (book) => {
    const token = localStorage.getItem('token');
    const res = await fetch(`${API_BASE_URL}/api/books`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({
        title: book.title,
        author: book.author,
        category: book.category,
        cover_url: book.cover_url,
        ol_key: book.ol_key,
        status: 'to_read',
        source: 'catalog',
      }),
    });
    if (!res.ok) throw new Error('add failed');
    toast.success(`"${book.title}" ajouté à ta bibliothèque !`);
    if (onBookAdded) onBookAdded();
  };

  const isOwned = (book) =>
    userBooks.some(
      (b) =>
        b.title?.toLowerCase() === book.title?.toLowerCase() ||
        (book.ol_key && (b.ol_key === book.ol_key || b.id === book.ol_key))
    );

  if (!catalogReady) {
    return (
      <div className="text-center py-16">
        <SparklesIcon className="h-12 w-12 text-gray-200 dark:text-gray-700 mx-auto mb-4" />
        <h3 className="text-base font-semibold text-gray-700 dark:text-gray-300 mb-2">
          Catalogue en cours de chargement
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400 max-w-sm mx-auto mb-4">
          Le catalogue n'est pas encore rempli. Lance le script de seed pour le peupler :
        </p>
        <code className="text-xs bg-gray-100 dark:bg-gray-800 px-3 py-1.5 rounded-lg text-gray-700 dark:text-gray-300">
          cd backend && python scripts/seed_catalog.py
        </code>
      </div>
    );
  }

  return (
    <div>
      {/* Titre */}
      <div className="flex items-center gap-2 mb-5">
        <FireIcon className="h-5 w-5 text-orange-500" />
        <h2 className="text-lg font-semibold text-gray-800 dark:text-gray-100">
          Livres populaires à découvrir
        </h2>
        <span className="text-xs text-gray-400 dark:text-gray-500 ml-1 italic">
          Clique "Ajouter" pour les mettre dans ta bibliothèque
        </span>
      </div>

      {isLoading && books.length === 0 ? (
        <div className="flex gap-3 overflow-x-auto scrollbar-hide sm:grid sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 sm:gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="flex-shrink-0 w-36 sm:w-auto rounded-xl bg-gray-100 dark:bg-gray-800 h-56 sm:h-64 animate-pulse" />
          ))}
        </div>
      ) : (
        <>
          <div className="flex gap-3 overflow-x-auto scrollbar-hide pb-2 sm:grid sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 sm:gap-4 sm:pb-0">
            {books.map((book, i) => (
              <div key={`${book.ol_key}-${i}`} className="flex-shrink-0 w-36 sm:w-auto">
                <DiscoverCard
                  book={book}
                  onAdd={handleAdd}
                  alreadyOwned={isOwned(book)}
                />
              </div>
            ))}
          </div>

          {hasMore && (
            <div className="flex justify-center mt-8">
              <button
                onClick={() => loadBooks(false)}
                disabled={isLoading}
                className="px-6 py-2.5 text-sm font-medium text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800 rounded-xl hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-colors disabled:opacity-50"
              >
                {isLoading ? 'Chargement...' : 'Afficher plus'}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default DiscoverSection;
