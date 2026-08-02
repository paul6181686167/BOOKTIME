import React, { useEffect, useState } from 'react';
import { StarIcon } from '@heroicons/react/24/outline';
import { StarIcon as StarSolidIcon } from '@heroicons/react/24/solid';
import { API_BASE_URL } from '../../config/environment';

function Stars({ value, size = 'md' }) {
  const n = Math.round(Number(value) || 0);
  const cls = size === 'sm' ? 'h-4 w-4' : 'h-5 w-5';
  return (
    <div className="flex items-center gap-0.5" aria-label={`${value || 0} sur 5`}>
      {[1, 2, 3, 4, 5].map((star) =>
        star <= n ? (
          <StarSolidIcon key={star} className={`${cls} text-yellow-400`} />
        ) : (
          <StarIcon key={star} className={`${cls} text-gray-300 dark:text-gray-600`} />
        )
      )}
    </div>
  );
}

/**
 * Section « Avis de la communauté » : moyenne + liste d'avis publics.
 */
export default function CommunityReviews({ book, refreshKey = 0 }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!book) return;
    const title = (book.title || book.name || '').trim();
    const author = (book.author || '').trim();
    const olKey = book.ol_key || '';
    const isbn = book.isbn || '';
    if (!title && !olKey && !isbn) {
      setLoading(false);
      setData({ average_rating: null, ratings_count: 0, reviews: [] });
      return;
    }

    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const token = localStorage.getItem('token');
        const params = new URLSearchParams();
        if (title) params.set('title', title);
        if (author && author !== 'Auteur inconnu') params.set('author', author);
        if (olKey) params.set('ol_key', olKey);
        if (isbn) params.set('isbn', isbn);
        params.set('limit', '20');

        const res = await fetch(
          `${API_BASE_URL}/api/community/books/reviews?${params}`,
          {
            headers: token ? { Authorization: `Bearer ${token}` } : {},
            cache: 'no-store',
          }
        );
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const json = await res.json();
        if (!cancelled) setData(json);
      } catch (e) {
        if (!cancelled) {
          setError('Impossible de charger les avis');
          setData(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => {
      cancelled = true;
    };
  }, [
    book?.id,
    book?.title,
    book?.name,
    book?.author,
    book?.ol_key,
    book?.isbn,
    refreshKey,
  ]);

  if (loading) {
    return (
      <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Avis de la communauté
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400">Chargement…</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
          Avis de la communauté
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400">{error}</p>
      </div>
    );
  }

  const average = data?.average_rating;
  const ratingsCount = data?.ratings_count || 0;
  const reviews = data?.reviews || [];

  return (
    <div className="pt-4 border-t border-gray-200 dark:border-gray-700 space-y-3">
      <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
        Avis de la communauté
      </h3>

      <div className="flex items-center gap-3 flex-wrap">
        {average != null ? (
          <>
            <span className="text-2xl font-semibold text-gray-900 dark:text-white tabular-nums">
              {Number(average).toFixed(1)}
            </span>
            <Stars value={average} />
            <span className="text-sm text-gray-500 dark:text-gray-400">
              {ratingsCount} note{ratingsCount > 1 ? 's' : ''}
              {data?.reviews_count
                ? ` · ${data.reviews_count} avis`
                : ''}
            </span>
          </>
        ) : (
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Pas encore de notes communautaires pour ce livre.
          </p>
        )}
      </div>

      {reviews.length > 0 && (
        <ul className="space-y-3 max-h-64 overflow-y-auto pr-1">
          {reviews.map((r) => (
            <li
              key={`${r.user_id}-${r.date || ''}`}
              className="rounded-lg bg-gray-50 dark:bg-gray-700/40 px-3 py-2"
            >
              <div className="flex items-center justify-between gap-2 mb-1">
                <span className="text-sm font-medium text-gray-800 dark:text-gray-100">
                  {r.display_name}
                  {r.is_mine ? (
                    <span className="ml-1 text-xs text-green-600 dark:text-green-400">
                      (toi)
                    </span>
                  ) : null}
                </span>
                {r.rating ? <Stars value={r.rating} size="sm" /> : null}
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-300 whitespace-pre-wrap">
                {r.review}
              </p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
