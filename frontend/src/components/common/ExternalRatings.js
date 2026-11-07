import React, { useEffect, useState } from 'react';
import { StarIcon } from '@heroicons/react/24/solid';
import { fetchExternalRatings } from '../../services/externalRatingsService';
import logger from '../../utils/logger';

const formatScore = (score) =>
  Number(score).toLocaleString('fr-FR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });

const formatCount = (count) => count.toLocaleString('fr-FR');

/** Notes d'autres sites pour une fiche livre ou série (Open Library, Google Books, AniList, MyAnimeList). */
const ExternalRatings = ({ title, author = '', isbn = '', kind = 'book', category = '' }) => {
  const [state, setState] = useState({ status: 'loading', ratings: [], links: [] });

  useEffect(() => {
    let cancelled = false;
    setState({ status: 'loading', ratings: [], links: [] });
    fetchExternalRatings({ title, author, isbn, kind, category })
      .then((data) => {
        if (!cancelled) setState({ status: 'done', ...data });
      })
      .catch((error) => {
        logger.debug('Notes externes indisponibles', error);
        if (!cancelled) setState({ status: 'error', ratings: [], links: [] });
      });
    return () => {
      cancelled = true;
    };
  }, [title, author, isbn, kind, category]);

  if (state.status === 'error') return null; // hors ligne ou serveur indisponible : on n'affiche rien

  return (
    <section aria-label="Notes des autres sites" data-testid="external-ratings">
      <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Notes des autres sites</h3>

      {state.status === 'loading' ? (
        <p className="text-xs text-gray-500 dark:text-gray-400">Recherche des notes…</p>
      ) : (
        <>
          {state.ratings.length > 0 ? (
            <ul className="flex flex-wrap gap-2">
              {state.ratings.map((r) => {
                const body = (
                  <>
                    <StarIcon className="h-4 w-4 text-yellow-400" aria-hidden="true" />
                    <span className="font-semibold text-gray-900 dark:text-white">{formatScore(r.score)}/5</span>
                    <span className="text-gray-600 dark:text-gray-300">
                      {r.label}
                      {r.scope === 'series' && kind === 'book' ? ' (série)' : ''}
                    </span>
                    {r.count ? (
                      <span className="text-gray-500 dark:text-gray-400">· {formatCount(r.count)} avis</span>
                    ) : null}
                  </>
                );
                const cls =
                  'inline-flex items-center gap-1.5 rounded-full border border-gray-200 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-1 text-xs';
                return (
                  <li key={r.source}>
                    {r.url ? (
                      <a href={r.url} target="_blank" rel="noopener noreferrer" className={`${cls} hover:border-booktime-500`}>
                        {body}
                      </a>
                    ) : (
                      <span className={cls}>{body}</span>
                    )}
                  </li>
                );
              })}
            </ul>
          ) : (
            <p className="text-xs text-gray-500 dark:text-gray-400">Aucune note trouvée sur les autres sites.</p>
          )}

          {state.links.length > 0 && (
            <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
              Voir sur{' '}
              {state.links.map((l, i) => (
                <React.Fragment key={l.label}>
                  {i > 0 && ' · '}
                  <a
                    href={l.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="underline hover:text-booktime-700 dark:hover:text-booktime-400"
                  >
                    {l.label} ↗
                  </a>
                </React.Fragment>
              ))}
            </p>
          )}
        </>
      )}
    </section>
  );
};

export default ExternalRatings;
