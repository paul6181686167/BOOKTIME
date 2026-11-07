import React from 'react';
import { StarIcon } from '@heroicons/react/24/outline';
import { StarIcon as StarSolidIcon } from '@heroicons/react/24/solid';
import CommunityReviews from '../common/CommunityReviews';
import ExternalRatings from '../common/ExternalRatings';

/** Note, avis personnel et avis de la communauté. */
const SeriesRatingReview = ({
  isSeriesOwned,
  seriesRating,
  handleSeriesRatingClick,
  seriesReview,
  setSeriesReview,
  handleSeriesReviewPublish,
  publishingSeriesReview,
  savedSeriesReview,
  seriesDisplayName,
  series,
  communityRefreshKey,
}) => (
  <>
        {/* Note & avis — tout en bas de la fiche */}
        <div className="border-t border-gray-200 dark:border-gray-700 px-4 py-3 sm:px-6 space-y-3">
          {isSeriesOwned ? (
            <>
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Note</h3>
                <div className="flex space-x-1">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      type="button"
                      onClick={() => handleSeriesRatingClick(star)}
                      className="h-6 w-6 cursor-pointer"
                      aria-label={`Noter ${star} sur 5`}
                    >
                      {star <= (seriesRating || 0) ? (
                        <StarSolidIcon className="h-6 w-6 text-yellow-400" />
                      ) : (
                        <StarIcon className="h-6 w-6 text-gray-300 dark:text-gray-600" />
                      )}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Avis</h3>
                <textarea
                  value={seriesReview}
                  onChange={(e) => setSeriesReview(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-booktime-500 transition-colors"
                  placeholder="Qu’avez-vous pensé de cette série ?"
                />
                <button
                  type="button"
                  onClick={handleSeriesReviewPublish}
                  disabled={
                    publishingSeriesReview ||
                    !(seriesReview || '').trim() ||
                    (seriesReview || '').trim() === (savedSeriesReview || '').trim()
                  }
                  className="mt-2 px-4 py-2 text-sm font-medium rounded-lg bg-green-600 text-white hover:bg-green-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  {publishingSeriesReview ? 'Publication…' : 'Publier'}
                </button>
              </div>
            </>
          ) : (
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Ajoutez la série pour noter et publier un avis.
            </p>
          )}

          <ExternalRatings
            title={seriesDisplayName}
            author={series?.author || series?.authors?.[0] || ''}
            kind="series"
            category={series?.category || ''}
          />

          <CommunityReviews
            book={{
              title: seriesDisplayName,
              name: seriesDisplayName,
              author: series?.author || series?.authors?.[0] || '',
            }}
            refreshKey={communityRefreshKey}
            emptyLabel="Pas encore de notes communautaires pour cette série."
          />
        </div>
  </>
);

export default SeriesRatingReview;
