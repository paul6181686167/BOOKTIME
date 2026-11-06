import React from 'react';

/** Petite couverture : image si disponible, sinon pavé neutre. */
export function MiniCover({ url, className = 'w-10 h-14' }) {
  return (
    <div
      className={`${className} rounded overflow-hidden bg-gray-200 dark:bg-gray-600 shrink-0`}
      aria-hidden
    >
      {url ? <img src={url} alt="" loading="lazy" className="w-full h-full object-cover" /> : null}
    </div>
  );
}

/** Étoiles dorées (note sur 5). */
export function Stars({ value }) {
  const n = Math.max(0, Math.min(5, Math.round(Number(value) || 0)));
  if (!n) return null;
  return (
    <span className="text-yellow-400 text-xs tracking-tight" aria-label={`${n} sur 5`}>
      {'★'.repeat(n)}
      <span className="text-gray-300 dark:text-gray-600">{'★'.repeat(5 - n)}</span>
    </span>
  );
}

/** Carte cliquable d'un livre recommandé (dans le chat) ou d'une liste de profil. */
export default function BookRefCard({ book, onOpen, tone = 'light', children }) {
  const dark = tone === 'onGreen';
  return (
    <button
      type="button"
      onClick={() => onOpen?.(book)}
      className={`w-full flex items-center gap-3 p-2 rounded-lg text-left transition-colors ${
        dark
          ? 'bg-white/95 hover:bg-white text-gray-900'
          : 'bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-900 dark:text-white'
      }`}
    >
      <MiniCover url={book.cover_url} />
      <span className="min-w-0 flex-1">
        <span className="block text-sm font-semibold truncate">{book.title}</span>
        {book.author ? (
          <span
            className={`block text-xs truncate ${
              dark ? 'text-gray-600' : 'text-gray-500 dark:text-gray-400'
            }`}
          >
            {book.author}
          </span>
        ) : null}
        {children}
      </span>
    </button>
  );
}
