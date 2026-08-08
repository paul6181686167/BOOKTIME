import React, { useState, useEffect } from 'react';
import { XMarkIcon, UserIcon, BookOpenIcon, CalendarIcon, QueueListIcon, ChevronDownIcon, ChevronUpIcon, StarIcon, TrophyIcon } from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';
import { API_BASE_URL } from '../config/environment';
import { EXTENDED_SERIES_DATABASE } from '../utils/seriesDatabaseExtended';
import { buildMergedLibraryVolumeRowsFromOlBooks } from '../utils/openLibraryBookDisplay';

// Cherche une série dans la base statique par nom (insensible à la casse)
const findSeriesInDB = (name) => {
  if (!name) return null;
  const nameLower = name.toLowerCase().trim();
  for (const category of Object.values(EXTENDED_SERIES_DATABASE)) {
    for (const s of Object.values(category)) {
      if (
        s.name.toLowerCase() === nameLower ||
        s.variations?.some(v => v.toLowerCase() === nameLower)
      ) return s;
    }
  }
  return null;
};

const AuthorModal = ({ author, isOpen, onClose, userBooks = [], onAddBook, onOpenSeries, onAddSeries }) => {
  const [authorInfo, setAuthorInfo] = useState(null);
  const [authorBooks, setAuthorBooks] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedSeries, setExpandedSeries] = useState({});
  const [isFollowing, setIsFollowing] = useState(false);

  // Charger l'état "Suivre" depuis le backend (auteurs suivis persistés)
  useEffect(() => {
    if (!author) return;
    const token = localStorage.getItem('token');
    fetch(`${API_BASE_URL}/api/authors/following`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((res) => (res.ok ? res.json() : { authors: [] }))
      .then((data) => {
        const followed = data.authors || [];
        setIsFollowing(followed.some((a) => a?.toLowerCase() === author.toLowerCase()));
      })
      .catch(() => setIsFollowing(false));
  }, [author]);

  const handleToggleFollow = async () => {
    const token = localStorage.getItem('token');
    const headers = {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
    const next = !isFollowing;
    setIsFollowing(next); // optimiste
    try {
      if (next) {
        await fetch(`${API_BASE_URL}/api/authors/follow`, {
          method: 'POST',
          headers,
          body: JSON.stringify({ author }),
        });
      } else {
        await fetch(`${API_BASE_URL}/api/authors/follow/${encodeURIComponent(author)}`, {
          method: 'DELETE',
          headers,
        });
      }
    } catch (err) {
      setIsFollowing(!next); // rollback en cas d'échec
      console.warn('Erreur suivi auteur:', err);
    }
  };

  const isBookInLibrary = (title) => {
    if (!title || !userBooks.length) return false;
    return userBooks.some(b => b.title?.toLowerCase().trim() === title.toLowerCase().trim());
  };

  // Fonction pour charger les informations de l'auteur
  const loadAuthorInfo = async () => {
    if (!author) return;
    
    setLoading(true);
    setError(null);
    
    const backendUrl = API_BASE_URL;
    const token = localStorage.getItem('token');

    // Timeout de 8 secondes max — on n'attend pas indéfiniment Wikidata
    const withTimeout = (promise, ms = 8000) =>
      Promise.race([promise, new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), ms))]);

    try {
      // Lancer profil et livres en parallèle avec timeout
      await Promise.allSettled([
        withTimeout(loadAuthorProfile(backendUrl)),
        withTimeout(loadAuthorBooks(backendUrl, token))
      ]);
    } catch (err) {
      console.warn('Chargement auteur partiel:', err);
    } finally {
      setLoading(false);
    }
  };

  // Charger le profil de l'auteur (Wikidata → Wikipedia → OpenLibrary)
  const loadAuthorProfile = async (backendUrl) => {
    // 1. PRIORITÉ : Wikidata (données structurées séries)
    try {
      const wikidataResponse = await fetch(`${backendUrl}/api/wikidata/author/${encodeURIComponent(author)}/info`);
      
      if (wikidataResponse.ok) {
        const wikidataData = await wikidataResponse.json();
        if (wikidataData.found) {
          console.log('✅ Informations auteur récupérées depuis Wikidata:', wikidataData.author);
          setAuthorInfo({
            ...wikidataData.author,
            photo_url: wikidataData.author.image_url || wikidataData.author.photo_url || null,
            source: 'wikidata'
          });
          return;
        }
      }
    } catch (error) {
      console.warn('⚠️ Erreur Wikidata, passage au fallback Wikipedia:', error);
    }
    
    // 2. FALLBACK : Wikipedia (biographies + parsing)
    try {
      const wikipediaResponse = await fetch(`${backendUrl}/api/wikipedia/author/${encodeURIComponent(author)}`);
      
      if (wikipediaResponse.ok) {
        const wikipediaData = await wikipediaResponse.json();
        if (wikipediaData.found) {
          console.log('✅ Informations auteur récupérées depuis Wikipedia:', wikipediaData.author);
          setAuthorInfo({
            ...wikipediaData.author,
            source: 'wikipedia'
          });
          return;
        }
      }
    } catch (error) {
      console.warn('⚠️ Erreur Wikipedia, passage au fallback OpenLibrary:', error);
    }
    
    // 3. FALLBACK : OpenLibrary (données basiques)
    try {
      const token = localStorage.getItem('token');
      const openlibResponse = await fetch(`${backendUrl}/api/openlibrary/author/${encodeURIComponent(author)}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (openlibResponse.ok) {
        const openlibData = await openlibResponse.json();
        if (openlibData.found) {
          console.log('✅ Informations auteur récupérées depuis OpenLibrary:', openlibData.author);
          setAuthorInfo({
            ...openlibData.author,
            source: 'openlibrary'
          });
          return;
        }
      }
    } catch (error) {
      console.warn('⚠️ Erreur OpenLibrary:', error);
    }
    
    // Aucune source n'a fonctionné pour le profil
    console.log('⚠️ Aucune information de profil trouvée pour l\'auteur');
  };

  // Charger les œuvres de l'auteur (Wikidata → Wikipedia → Bibliothèque)
  const loadAuthorBooks = async (backendUrl, token) => {
    try {
      // 1. PRIORITÉ : Wikidata (séries structurées)
      const wikidataSeriesResponse = await fetch(`${backendUrl}/api/wikidata/author/${encodeURIComponent(author)}/series`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (wikidataSeriesResponse.ok) {
        const wikidataSeriesData = await wikidataSeriesResponse.json();
        if (wikidataSeriesData.found && (wikidataSeriesData.series.length > 0 || wikidataSeriesData.individual_books.length > 0)) {
          console.log('✅ Séries et livres récupérés depuis Wikidata:', wikidataSeriesData);
          setAuthorBooks({
            series: wikidataSeriesData.series,
            individual_books: wikidataSeriesData.individual_books || [],
            total_books: wikidataSeriesData.results_count,
            total_series: wikidataSeriesData.total_series || wikidataSeriesData.series.length,
            total_individual_books: wikidataSeriesData.total_individual_books || 0,
            sources: { 
              wikidata: (wikidataSeriesData.total_series || 0) + (wikidataSeriesData.total_individual_books || 0)
            }
          });
          return;
        }
      }
      
      // 2. FALLBACK : Wikipedia (parsing intelligent)
      const wikipediaWorksResponse = await fetch(`${backendUrl}/api/wikipedia/author/${encodeURIComponent(author)}/works`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (wikipediaWorksResponse.ok) {
        const wikipediaWorksData = await wikipediaWorksResponse.json();
        if (wikipediaWorksData.found) {
          console.log('✅ Œuvres récupérées depuis Wikipedia (optimisé):', wikipediaWorksData);
          setAuthorBooks({
            series: wikipediaWorksData.series,
            individual_books: wikipediaWorksData.individual_books,
            total_books: wikipediaWorksData.total_books,
            total_series: wikipediaWorksData.total_series,
            total_individual_books: wikipediaWorksData.total_individual_books,
            sources: wikipediaWorksData.sources
          });
          return;
        }
      }
      
      // 3. FALLBACK : Bibliothèque personnelle
      const response = await fetch(`${backendUrl}/api/authors/${encodeURIComponent(author)}/books`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (response.ok) {
        const booksData = await response.json();
        console.log('✅ Œuvres de l\'auteur récupérées depuis la bibliothèque:', booksData);
        
        // Utiliser le format retourné par l'endpoint /api/authors/{author}/books
        setAuthorBooks({
          series: booksData.series || [],
          individual_books: booksData.individual_books || [],
          total_books: booksData.total_books || 0,
          total_series: booksData.total_series || 0,
          total_individual_books: booksData.total_individual_books || 0,
          sources: booksData.sources || { library: booksData.total_books || 0 },
          fallback: true
        });
      } else {
        console.log('⚠️ Aucune œuvre trouvée pour cet auteur');
        // Définir des valeurs par défaut
        setAuthorBooks({
          series: [],
          individual_books: [],
          total_books: 0,
          total_series: 0,
          total_individual_books: 0,
          sources: {},
          fallback: true
        });
      }
    } catch (err) {
      console.error('Erreur lors du chargement des œuvres:', err);
      // Définir des valeurs par défaut en cas d'erreur
      setAuthorBooks({
        series: [],
        individual_books: [],
        total_books: 0,
        total_series: 0,
        total_individual_books: 0,
        sources: {},
        fallback: true
      });
    }
  };

  // Fonction pour basculer l'expansion d'une série
  const toggleSeriesExpansion = (seriesName) => {
    setExpandedSeries(prev => ({
      ...prev,
      [seriesName]: !prev[seriesName]
    }));
  };

  // Fonction pour obtenir la couleur du badge de statut
  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';
      case 'reading': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300';
      case 'to_read': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-300';
    }
  };

  // Fonction pour obtenir le texte du statut
  const getStatusText = (status) => {
    switch (status) {
      case 'completed': return 'Terminé';
      case 'reading': return 'En cours';
      case 'to_read': return 'À lire';
      default: return 'Inconnu';
    }
  };

  // Charger les informations quand le modal s'ouvre
  useEffect(() => {
    if (isOpen && author) {
      loadAuthorInfo();
    }
  }, [isOpen, author]);

  // Réinitialiser les données quand le modal se ferme
  useEffect(() => {
    if (!isOpen) {
      setAuthorInfo(null);
      setAuthorBooks(null);
      setError(null);
      setExpandedSeries({});
    }
  }, [isOpen]);

  if (!isOpen || !author) return null;

  return (
    <div className="modal-overlay" onClick={onClose} style={{ zIndex: 1100 }}>
      <div className="modal-content-wide w-full md:w-auto" onClick={(e) => e.stopPropagation()}>
        {/* Barre mobile avec bouton fermeture */}
        <div className="sticky top-0 z-20 flex items-center justify-between px-4 py-3 md:hidden border-b border-booktime-mist/55 dark:border-booktime-800/50 bg-booktime-mistSoft/75 dark:bg-gray-900/70 backdrop-blur-xl">
          <span className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Auteur</span>
          <button onClick={onClose} className="w-10 h-10 flex items-center justify-center rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>
        <div className="flex items-start justify-between mb-6">
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              {authorInfo?.name || author}
            </h2>
            {authorInfo?.genres?.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1">
                {authorInfo.genres.slice(0, 3).map((genre, i) => (
                  <span key={i} className="px-2 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 text-xs rounded-full">
                    {genre}
                  </span>
                ))}
              </div>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={handleToggleFollow}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                isFollowing
                  ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 hover:bg-yellow-200'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
              title={isFollowing ? 'Ne plus suivre' : 'Suivre cet auteur'}
            >
              {isFollowing
                ? <StarIconSolid className="h-4 w-4" />
                : <StarIcon className="h-4 w-4" />
              }
              {isFollowing ? 'Suivi' : 'Suivre'}
            </button>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
        </div>

        {loading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-500"></div>
            <span className="ml-3 text-gray-600 dark:text-gray-400">Chargement des informations...</span>
          </div>
        )}

        {error && (
          <div className="text-center py-8">
            <div className="text-6xl mb-4">👤</div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              {author}
            </h3>
            <p className="text-gray-500 dark:text-gray-400 mb-4">
              {error}
            </p>
            <button
              onClick={loadAuthorInfo}
              className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
            >
              Réessayer
            </button>
          </div>
        )}

        {!loading && (
          <div className="space-y-6">
            {/* Informations auteur */}
            {authorInfo && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Photo de l'auteur */}
                <div className="md:col-span-1">
                  <div className="aspect-square bg-gray-100 dark:bg-gray-700 rounded-lg overflow-hidden">
                    {authorInfo.photo_url ? (
                      <img 
                        src={authorInfo.photo_url} 
                        alt={authorInfo.name}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.target.style.display = 'none';
                          e.target.nextSibling.style.display = 'flex';
                        }}
                      />
                    ) : null}
                    <div 
                      className={`w-full h-full bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center text-white ${authorInfo.photo_url ? 'hidden' : 'flex'}`}
                    >
                      <UserIcon className="h-20 w-20" />
                    </div>
                  </div>
                </div>

                {/* Informations de l'auteur */}
                <div className="md:col-span-2 space-y-6">
                  {/* Biographie */}
                  {authorInfo.bio && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
                        <BookOpenIcon className="h-5 w-5 mr-2 text-green-600" />
                        Biographie
                      </h3>
                      <div className="prose prose-gray dark:prose-invert max-w-none">
                        <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                          {authorInfo.bio}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Informations supplémentaires */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Dates */}
                    {(authorInfo.birth_date || authorInfo.death_date) && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2 flex items-center">
                          <CalendarIcon className="h-4 w-4 mr-1 text-gray-500" />
                          Dates
                        </h4>
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          {authorInfo.birth_date && (
                            <p>Né(e) : {authorInfo.birth_date}</p>
                          )}
                          {authorInfo.death_date && (
                            <p>Décédé(e) : {authorInfo.death_date}</p>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Statistiques */}
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2 flex items-center">
                        <BookOpenIcon className="h-4 w-4 mr-1 text-gray-500" />
                        Œuvres
                      </h4>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        {authorInfo.work_summary && (
                          <p>{authorInfo.work_summary}</p>
                        )}
                        {authorInfo.work_count > 0 && (
                          <p>{authorInfo.work_count} œuvre(s) répertoriée(s)</p>
                        )}
                        {authorInfo.top_work && (
                          <p className="mt-1 text-xs">
                            <span className="font-medium">Œuvre principale :</span> {authorInfo.top_work}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Noms alternatifs */}
                  {authorInfo.alternate_names && authorInfo.alternate_names.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2">
                        Autres noms
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {authorInfo.alternate_names.slice(0, 5).map((name, index) => (
                          <span
                            key={index}
                            className="inline-flex items-center px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-xs rounded"
                          >
                            {name}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Prix littéraires */}
                  {authorInfo.awards?.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-2 flex items-center">
                        <TrophyIcon className="h-4 w-4 mr-1 text-yellow-500" />
                        Prix littéraires
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {authorInfo.awards.slice(0, 8).map((award, index) => (
                          <span
                            key={index}
                            className="inline-flex items-center px-2 py-1 bg-yellow-50 dark:bg-yellow-900/20 text-yellow-800 dark:text-yellow-300 text-xs rounded border border-yellow-200 dark:border-yellow-800"
                          >
                            🏆 {award}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Source */}
                  <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      Informations fournies par{' '}
                      {authorInfo.source === 'wikidata' ? (
                        <a 
                          href={`https://www.wikidata.org/wiki/${authorInfo.id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-700 underline"
                        >
                          Wikidata
                        </a>
                      ) : authorInfo.source === 'wikipedia' ? (
                        <a 
                          href={authorInfo.wikipedia_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-green-600 hover:text-green-700 underline"
                        >
                          Wikipedia
                        </a>
                      ) : (
                        <a 
                          href={`https://openlibrary.org${authorInfo.ol_key}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-green-600 hover:text-green-700 underline"
                        >
                          Open Library
                        </a>
                      )}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Œuvres de l'auteur depuis sources externes */}
            {authorBooks && authorBooks.total_books > 0 && (
              <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
                  <QueueListIcon className="h-5 w-5 mr-2 text-green-600" />
                  {authorBooks.fallback ? "Œuvres dans votre bibliothèque" : "Œuvres de l'auteur"}
                  <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">
                    ({authorBooks.total_books} livre{authorBooks.total_books > 1 ? 's' : ''})
                  </span>
                  {authorBooks.sources && (
                    <span className="ml-2 text-xs text-gray-400 dark:text-gray-500">
                      {authorBooks.sources.wikidata ? `Wikidata: ${authorBooks.sources.wikidata}` : ''}
                      {authorBooks.sources.wikipedia ? `Wikipedia: ${authorBooks.sources.wikipedia}` : ''}
                      {authorBooks.sources.openlibrary ? ` OpenLibrary: ${authorBooks.sources.openlibrary}` : ''}
                      {authorBooks.sources.library ? `Bibliothèque: ${authorBooks.sources.library}` : ''}
                    </span>
                  )}
                </h3>

                <div className="space-y-3">
                  {/* Séries — dédupliquées + enrichies depuis la base statique */}
                  {(() => {
                    const normalize = (name) =>
                      (name || '').toLowerCase()
                        .replace(/\b(trilogy|tetralogy|series|saga|cycle|duology|quartet)\b/g, '')
                        .replace(/\s+/g, ' ').trim();
                    const seen = new Map();
                    authorBooks.series.forEach((s) => {
                      const key = normalize(s.name);
                      const existing = seen.get(key);
                      if (!existing || (s.books?.length || 0) > (existing.books?.length || 0)) {
                        seen.set(key, s);
                      }
                    });
                    return Array.from(seen.values());
                  })().map((series, index) => {
                    const db = findSeriesInDB(series.name);
                    const rawVolumes = db?.volumes ?? series.books?.length ?? null;
                    const volumes = Array.isArray(rawVolumes) ? rawVolumes.length : rawVolumes;
                    const status = db?.status;
                    const firstYear = db?.first_published || series.books?.[0]?.publication_year;
                    const lastYear = db?.volume_details
                      ? Object.values(db.volume_details).map(d => d.published_year).filter(Boolean).sort().reverse()[0]
                      : null;
                    const description = db?.description || series.description || null;
                    const coverUrl = series.cover_url || series.books?.find(b => b.cover_url)?.cover_url || null;

                    // Titres des tomes : depuis la base statique ou les livres Wikidata
                    const volumeTitles = db?.volume_titles || (() => {
                      const map = {};
                      (series.books || []).forEach((b, i) => { map[b.volume_number || i + 1] = b.title; });
                      return Object.keys(map).length ? map : null;
                    })();

                    return (
                      <div key={index} className="bg-gray-50 dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
                        {/* En-tête de la carte série */}
                        <div className="flex items-start gap-3 p-4">
                          {/* Couverture ou icône */}
                          <div className="flex-shrink-0 w-12 h-16 rounded overflow-hidden bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
                            {coverUrl
                              ? <img src={coverUrl} alt={series.name} className="w-full h-full object-cover" />
                              : <QueueListIcon className="h-6 w-6 text-purple-500" />
                            }
                          </div>

                          {/* Infos principales */}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-start justify-between gap-2">
                              <h4 className="font-semibold text-gray-900 dark:text-white text-sm leading-tight">
                                {series.name}
                              </h4>
                              <div className="flex items-center gap-1 flex-shrink-0">
                                {onOpenSeries && (
                                  <button
                                    onClick={() => onOpenSeries({ name: series.name, author, books: series.books || [] })}
                                    className="text-xs px-2 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded transition-colors"
                                  >
                                    Voir →
                                  </button>
                                )}
                                {onAddSeries && (
                                  <button
                                    onClick={() => {
                                      const books = series.books || [];
                                      const mergedLibraryVolumes = buildMergedLibraryVolumeRowsFromOlBooks(books);
                                      onAddSeries({
                                        name: series.name,
                                        author,
                                        books,
                                        category: series.category || 'roman',
                                        total_volumes: series.volumes ?? books.length,
                                        ...(mergedLibraryVolumes
                                          ? { mergedLibraryVolumes }
                                          : {}),
                                      });
                                    }}
                                    className="text-xs px-2 py-1 bg-green-600 hover:bg-green-700 text-white rounded transition-colors"
                                  >
                                    + Ajouter
                                  </button>
                                )}
                                <button onClick={() => toggleSeriesExpansion(series.name)}>
                                  {expandedSeries[series.name]
                                    ? <ChevronUpIcon className="h-4 w-4 text-gray-400" />
                                    : <ChevronDownIcon className="h-4 w-4 text-gray-400" />}
                                </button>
                              </div>
                            </div>

                            {/* Badges : tomes + statut + années */}
                            <div className="flex flex-wrap items-center gap-1.5 mt-1.5">
                              {volumes && (
                                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 text-xs rounded-full font-medium">
                                  📚 {volumes} tome{volumes > 1 ? 's' : ''}
                                </span>
                              )}
                              {status && (
                                <span className={`inline-flex items-center px-2 py-0.5 text-xs rounded-full font-medium ${
                                  status === 'completed'
                                    ? 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300'
                                    : 'bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-300'
                                }`}>
                                  {status === 'completed' ? '✓ Terminée' : '⏳ En cours'}
                                </span>
                              )}
                              {firstYear && (
                                <span className="text-xs text-gray-500 dark:text-gray-400">
                                  {firstYear}{lastYear && lastYear !== firstYear ? ` – ${lastYear}` : ''}
                                </span>
                              )}
                            </div>

                            {/* Description courte */}
                            {description && (
                              <p className="text-xs text-gray-600 dark:text-gray-400 mt-1.5 line-clamp-2 leading-relaxed">
                                {description}
                              </p>
                            )}
                          </div>
                        </div>

                        {/* Liste des tomes (expansion) */}
                        {expandedSeries[series.name] && (
                          <div className="border-t border-gray-200 dark:border-gray-700 px-4 py-3 space-y-1 bg-white dark:bg-gray-900/30">
                            {volumeTitles ? (
                              Object.entries(volumeTitles)
                                .sort(([a], [b]) => Number(a) - Number(b))
                                .map(([num, title]) => {
                                  const detail = db?.volume_details?.[num];
                                  const inLib = isBookInLibrary(title);
                                  return (
                                    <div key={num} className="flex items-center justify-between py-1.5 px-2 rounded hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                                      <div className="flex items-center gap-2 min-w-0">
                                        <span className="text-xs font-semibold text-purple-600 dark:text-purple-400 w-12 flex-shrink-0">
                                          Tome {num}
                                        </span>
                                        <div className="min-w-0">
                                          <p className="text-sm text-gray-900 dark:text-white truncate">{title}</p>
                                          {detail?.published_year && (
                                            <p className="text-xs text-gray-400">{detail.published_year}</p>
                                          )}
                                        </div>
                                      </div>
                                      {inLib ? (
                                        <span className="text-xs text-green-600 dark:text-green-400 flex-shrink-0 ml-2">✓</span>
                                      ) : onAddBook ? (
                                        <button
                                          onClick={() => onAddBook({ title, author })}
                                          className="text-xs px-2 py-0.5 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors flex-shrink-0 ml-2"
                                        >
                                          + Ajouter
                                        </button>
                                      ) : null}
                                    </div>
                                  );
                                })
                            ) : (
                              <p className="text-xs text-gray-400 italic py-1">
                                Détails des tomes disponibles en ouvrant la série
                              </p>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}

                  {/* Livres individuels */}
                  {authorBooks.individual_books.length > 0 && (
                    <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4">
                      <h4 className="font-medium text-gray-900 dark:text-white mb-3 flex items-center">
                        <BookOpenIcon className="h-5 w-5 mr-2 text-blue-600" />
                        Livres individuels
                      </h4>
                      <div className="space-y-2">
                        {authorBooks.individual_books.map((item, index) => {
                          const title = item.book ? item.book.title : item.title;
                          const inLibrary = isBookInLibrary(title);
                          const bookStatus = item.book?.status;
                          return (
                            <div key={index} className="flex items-center justify-between py-2 px-3 bg-white dark:bg-gray-700 rounded">
                              <div>
                                <p className="font-medium text-gray-900 dark:text-white text-sm">
                                  {title}
                                </p>
                                <div className="flex items-center space-x-2 text-xs text-gray-500 dark:text-gray-400">
                                  {(item.book ? item.book.publication_year : item.year) && (
                                    <span>{item.book ? item.book.publication_year : item.year}</span>
                                  )}
                                </div>
                              </div>
                              <div className="flex items-center gap-2">
                                {bookStatus && (
                                  <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getStatusColor(bookStatus)}`}>
                                    {getStatusText(bookStatus)}
                                  </span>
                                )}
                                {inLibrary ? (
                                  <span className="text-xs text-green-600 dark:text-green-400 font-medium">
                                    ✓ Dans ma bibliothèque
                                  </span>
                                ) : onAddBook && title ? (
                                  <button
                                    onClick={() => onAddBook({ title, author })}
                                    className="text-xs px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors"
                                  >
                                    + Ajouter
                                  </button>
                                ) : null}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Message si aucune œuvre trouvée */}
            {authorBooks && authorBooks.total_books === 0 && (
              <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
                <div className="text-center py-8">
                  <BookOpenIcon className="h-12 w-12 mx-auto text-gray-400 dark:text-gray-600 mb-4" />
                  <p className="text-gray-500 dark:text-gray-400">
                    Aucune œuvre trouvée pour cet auteur
                  </p>
                  <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
                    Nous cherchons dans Wikipedia et OpenLibrary
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {!authorInfo && !authorBooks && !loading && !error && (
          <div className="text-center py-8">
            <div className="text-6xl mb-4">👤</div>
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
              {author}
            </h3>
            <p className="text-gray-500 dark:text-gray-400">
              Chargement des informations...
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default AuthorModal;