import React from 'react';
import { StarIcon } from '@heroicons/react/24/outline';
import { StarIcon as StarSolidIcon } from '@heroicons/react/24/solid';
import LanguageSelector from '../LanguageSelector';
import { coverImgSrc } from '../../utils/helpers';
import CommunityReviews from '../common/CommunityReviews';
import ExternalRatings from '../common/ExternalRatings';

/** Corps de la fiche : couverture, informations, progression, résumé, notes et avis. */
const BookDetailsGrid = ({
  book,
  titleMain,
  isEditing,
  olDetails,
  editData,
  setEditData,
  publishingReview,
  communityRefreshKey,
  coverProxy,
  setCoverProxy,
  totalPages,
  statusOptions,
  formatReadDate,
  inLibrary,
  displayStatus,
  handleRatingClick,
  handleReviewPublish,
  getProgressPercentage,
  getCurrentStatus,
}) => (
  <>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Grande couverture : desktop uniquement (mobile = vignette en haut) */}
          <div className="hidden md:block md:col-span-1">
            <div className="aspect-[2/3] bg-gray-100 dark:bg-gray-700 rounded-lg overflow-hidden">
              {book.cover_url ? (
                <img
                  src={coverImgSrc(book.cover_url, { forceProxy: coverProxy })}
                  alt={titleMain}
                  className="w-full h-full object-cover"
                  referrerPolicy={coverProxy ? undefined : 'no-referrer'}
                  onError={() => {
                    if (!coverProxy) setCoverProxy(true);
                  }}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800">
                  <div className="text-center p-4">
                    <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">Pas de couverture</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Détails du livre */}
          <div className="md:col-span-2 space-y-6">
            {/* Édition des langues */}
            {isEditing && (
              <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">Modifier les langues</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Langue originale */}
                  <div>
                    <LanguageSelector
                      label="Langue originale"
                      selectedLanguages={[editData.original_language]}
                      onLanguagesChange={(languages) => setEditData(prev => ({ ...prev, original_language: languages[0] || 'français' }))}
                      single={true}
                      placeholder="Sélectionner la langue originale"
                    />
                  </div>

                  {/* Langue de lecture */}
                  <div>
                    <LanguageSelector
                      label="Langue de lecture"
                      selectedLanguages={[editData.reading_language]}
                      onLanguagesChange={(languages) => setEditData(prev => ({ ...prev, reading_language: languages[0] || 'français' }))}
                      single={true}
                      placeholder="Langue dans laquelle vous lisez"
                    />
                  </div>
                </div>

                {/* Traductions disponibles */}
                <div className="mt-4">
                  <LanguageSelector
                    label="Traductions disponibles"
                    selectedLanguages={editData.available_translations}
                    onLanguagesChange={(languages) => setEditData(prev => ({ ...prev, available_translations: languages }))}
                    maxSelections={10}
                    placeholder="Ajouter les langues de traduction disponibles"
                  />
                </div>
              </div>
            )}

            {/* Série / Saga */}
            {isEditing ? (
              <div className="grid grid-cols-3 gap-3">
                <div className="col-span-2">
                  <label htmlFor="book-edit-saga" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Série (optionnel)
                  </label>
                  <input
                    id="book-edit-saga"
                    type="text"
                    value={editData.saga}
                    onChange={(e) => setEditData(prev => ({ ...prev, saga: e.target.value }))}
                    placeholder="ex: Harry Potter, One Piece…"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-booktime-500 text-sm"
                  />
                </div>
                <div>
                  <label htmlFor="book-edit-volume" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Tome n°
                  </label>
                  <input
                    id="book-edit-volume"
                    type="number"
                    value={editData.volume_number}
                    onChange={(e) => setEditData(prev => ({ ...prev, volume_number: e.target.value }))}
                    placeholder="1"
                    min="1"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-booktime-500 text-sm"
                  />
                </div>
              </div>
            ) : book.saga ? (
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Série</h3>
                <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-800 dark:text-indigo-300 rounded-full text-sm font-medium">
                   {book.saga}{book.volume_number ? ` — Tome ${book.volume_number}` : ''}
                </span>
              </div>
            ) : null}

            {/* Statut — uniquement si le livre est dans la bibliothèque */}
            {inLibrary && (isEditing ? (
              <div>
                <label htmlFor="book-edit-status" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Statut
                </label>
                <select
                  id="book-edit-status"
                  value={editData.status}
                  onChange={(e) => setEditData(prev => ({ ...prev, status: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-booktime-500 transition-colors"
                >
                  {statusOptions.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Statut</h3>
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getCurrentStatus().color}`}>
                  {getCurrentStatus().label}
                </span>
              </div>
            ))}

            {/* Progression — masquée en lecture : déjà affichée au-dessus */}
            {totalPages > 0 && !(inLibrary && !isEditing && displayStatus === 'reading') && (
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Progression</h3>
                {isEditing ? (
                  <div className="space-y-2">
                    <input
                      type="number"
                      aria-label="Pages lues"
                      value={editData.current_page}
                      onChange={(e) => setEditData(prev => ({ ...prev, current_page: e.target.value }))}
                      min="0"
                      max={totalPages}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-booktime-500 transition-colors"
                    />
                    <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
                      <span>{editData.current_page} pages lues</span>
                      <span>{totalPages} pages total</span>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
                      <span>{book.current_page || 0} pages lues</span>
                      <span>{totalPages} pages total</span>
                    </div>
                    <div className="progress-bar bg-gray-200 dark:bg-gray-700">
                      <div 
                        className="progress-fill"
                        style={{ width: `${getProgressPercentage()}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Note & avis — terminé ou à relire */}
            {(displayStatus === 'completed' || displayStatus === 'to_reread') && (
              <>
                <div>
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Note</h3>
                  <div className="flex space-x-1">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        type="button"
                        onClick={() => handleRatingClick(star)}
                        aria-label={`Noter ${star} sur 5`}
                        aria-pressed={star <= (editData.rating || book.rating || 0)}
                        className="h-6 w-6 cursor-pointer"
                      >
                        {star <= (editData.rating || book.rating || 0) ? (
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
                    aria-label="Votre avis sur ce livre"
                    value={editData.review}
                    onChange={(e) => setEditData((prev) => ({ ...prev, review: e.target.value }))}
                    rows={4}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-booktime-500 transition-colors"
                    placeholder="Qu'avez-vous pensé de ce livre ?"
                  />
                  <button
                    type="button"
                    onClick={handleReviewPublish}
                    disabled={
                      publishingReview ||
                      !(editData.review || '').trim() ||
                      (editData.review || '').trim() === (book.review || '').trim()
                    }
                    className="mt-2 px-4 py-2 text-sm font-medium rounded-lg bg-green-600 text-white hover:bg-green-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  >
                    {publishingReview ? 'Publication…' : 'Publier'}
                  </button>
                </div>
              </>
            )}

            <ExternalRatings
              title={titleMain || book.title}
              author={book.author || ''}
              isbn={book.isbn || ''}
              category={book.category || ''}
            />

            <CommunityReviews
              book={book}
              refreshKey={communityRefreshKey}
            />

            {/* Sujets / Genres — depuis OL enrichi */}
            {(olDetails?.subjects?.length > 0 || book.subjects?.length > 0) && (
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Genres & Sujets</h3>
                <div className="flex flex-wrap gap-1">
                  {(olDetails?.subjects || book.subjects || [])
                    .map((s) => (typeof s === 'string' ? s : s?.name || ''))
                    .filter(Boolean)
                    // Préférer les sujets FR (accents / mots courants) ; sinon garder un échantillon
                    .sort((a, b) => {
                      const score = (t) =>
                        (/[àâäéèêëïîôùûç]/i.test(t) ? 2 : 0) +
                        (/\b(roman|policier|fantastique|aventure|jeunesse|bande|dessin)/i.test(t)
                          ? 1
                          : 0);
                      return score(b) - score(a);
                    })
                    .slice(0, 8)
                    .map((s, i) => (
                    <span key={i} className="px-2 py-0.5 text-xs bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded-full border border-blue-100 dark:border-blue-800">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Lien Open Library */}
            {book.ol_key &&
              typeof book.ol_key === 'string' &&
              !book.ol_key.startsWith('gbooks_') && (
              <div className="pt-2">
                <a
                  href={`https://openlibrary.org${book.ol_key.startsWith('/') ? book.ol_key : '/' + book.ol_key}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-blue-500 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 underline"
                >
                  Voir sur Open Library →
                </a>
              </div>
            )}

            {/* Informations supplémentaires */}
            <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                {book.original_title && book.original_title !== titleMain && (
                  <div className="col-span-2">
                    <h4 className="font-medium text-gray-700 dark:text-gray-300">Titre original</h4>
                    <p className="text-gray-600 dark:text-gray-400 italic">{book.original_title}</p>
                  </div>
                )}
                <div>
                  <h4 className="font-medium text-gray-700 dark:text-gray-300">Date d'ajout</h4>
                  <p className="text-gray-600 dark:text-gray-400">
                    {book.date_added ? new Date(book.date_added).toLocaleDateString('fr-FR') : '—'}
                  </p>
                </div>
                {book.date_started && (
                  <div>
                    <h4 className="font-medium text-gray-700 dark:text-gray-300">Début de lecture</h4>
                    <p className="text-gray-600 dark:text-gray-400">
                      {new Date(book.date_started).toLocaleDateString('fr-FR')}
                    </p>
                  </div>
                )}
                {book.date_completed && (
                  <div>
                    <h4 className="font-medium text-gray-700 dark:text-gray-300">Terminé le</h4>
                    <p className="text-gray-600 dark:text-gray-400">
                      {new Date(book.date_completed).toLocaleDateString('fr-FR')}
                    </p>
                  </div>
                )}
                {book.isbn && (
                  <div>
                    <h4 className="font-medium text-gray-700 dark:text-gray-300">ISBN</h4>
                    <p className="text-gray-600 dark:text-gray-400">{book.isbn}</p>
                  </div>
                )}
                {Array.isArray(book.reading_history) && book.reading_history.length > 0 && (
                  <div className="col-span-2">
                    <h4 className="font-medium text-gray-700 dark:text-gray-300 mb-1">Lectures précédentes</h4>
                    <ul className="space-y-1 text-gray-600 dark:text-gray-400">
                      {[...book.reading_history].reverse().map((entry, idx) => {
                        const done = formatReadDate(entry?.date_completed);
                        const started = formatReadDate(entry?.date_started);
                        if (!done && !started) return null;
                        return (
                          <li key={idx}>
                            {done ? `Lu le ${done}` : `Commencé le ${started}`}
                            {entry?.rating ? ` · ${entry.rating}/5` : ''}
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
  </>
);

export default BookDetailsGrid;
