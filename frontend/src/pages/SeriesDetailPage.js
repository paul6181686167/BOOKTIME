import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeftIcon, 
  BookOpenIcon, 
  UserIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  PlayIcon,
  PlusIcon
} from '@heroicons/react/24/outline';
import toast from 'react-hot-toast';
import { API_BASE_URL } from '../config/environment';
import { addSeriesToLibrary as saveSeriesToLibrary, generateVolumesList } from '../services/seriesLibraryService';
import { EXTENDED_SERIES_DATABASE } from '../utils/seriesDatabaseExtended';
import { enrichSeriesMetadata } from '../components/series/SeriesActions';

const SeriesDetailPage = () => {
  const { seriesName } = useParams();
  const navigate = useNavigate();
  const [series, setSeries] = useState(null);
  const [volumes, setVolumes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isOwned, setIsOwned] = useState(false);
  const [addingToLibrary, setAddingToLibrary] = useState(false);

  const backendUrl = API_BASE_URL

  useEffect(() => {
    loadSeriesDetails();
  }, [seriesName]);

  const loadSeriesDetails = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      // D'abord, chercher la série dans les séries populaires
      const seriesResponse = await fetch(`${backendUrl}/api/series/popular?limit=1000`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (seriesResponse.ok) {
        const seriesData = await seriesResponse.json();
        const foundSeries = seriesData.series.find(s => 
          s.name.toLowerCase() === decodeURIComponent(seriesName).toLowerCase()
        );

        if (foundSeries) {
          setSeries(foundSeries);
          
          // Générer la liste des volumes
          const volumeList = [];
          for (let i = 1; i <= foundSeries.volumes; i++) {
            volumeList.push({
              volume_number: i,
              title: `${foundSeries.name} - Tome ${i}`,
              status: 'to_read',
              isOwned: false
            });
          }
          
          // Vérifier quels volumes sont déjà possédés
          const booksResponse = await fetch(`${backendUrl}/api/books?category=${foundSeries.category}`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          });

          if (booksResponse.ok) {
            const books = await booksResponse.json();
            
            // FILTRAGE STRICT par série spécifique (PROMPT 3)
            const seriesBooks = books.filter(book => {
              // Vérification de base : le livre doit avoir une saga
              if (!book.saga) return false;
              
              const bookSaga = book.saga.toLowerCase().trim();
              const bookAuthor = (book.author || '').toLowerCase().trim();
              const bookTitle = (book.title || '').toLowerCase().trim();
              
              const seriesName = foundSeries.name.toLowerCase().trim();
              const seriesAuthors = foundSeries.authors.map(a => a.toLowerCase().trim());
              
              // 1. CORRESPONDANCE EXACTE DU NOM DE SÉRIE
              // Le nom de la saga doit correspondre exactement au nom de la série
              const sagaMatches = bookSaga === seriesName || bookSaga.includes(seriesName);
              
              // 2. VÉRIFICATION AUTEUR ORIGINAL
              // L'auteur du livre doit être dans la liste des auteurs originaux de la série
              const authorMatches = seriesAuthors.some(seriesAuthor => {
                // Correspondance exacte ou contient l'auteur
                return bookAuthor === seriesAuthor || 
                       bookAuthor.includes(seriesAuthor) || 
                       seriesAuthor.includes(bookAuthor);
              });
              
              // 3. VÉRIFICATION TITRE DE LA SÉRIE
              // Le titre du livre doit contenir le nom de la série pour être considéré comme faisant partie
              const titleContainsSeries = bookTitle.includes(seriesName);
              
              // 4. EXCLUSION DES SPIN-OFFS ET AUTRES CRÉATEURS
              // Exclusions automatiques par mots-clés
              const excludeKeywords = [
                'spin-off', 'spin off', 'hors-série', 'hors série', 'adaptation', 
                'suite non-officielle', 'suite non officielle', 'continuation posthume',
                'par un autre auteur', 'nouvelle version', 'reboot', 'remake'
              ];
              
              const hasExcludeKeywords = excludeKeywords.some(keyword => 
                bookTitle.includes(keyword) || (book.description || '').toLowerCase().includes(keyword)
              );
              
              // 5. LOGIQUE DE VALIDATION FINALE
              // Le livre doit :
              // - Avoir une correspondance de saga ET (auteur OU titre contient série)
              // - NE PAS avoir de mots-clés d'exclusion
              return sagaMatches && (authorMatches || titleContainsSeries) && !hasExcludeKeywords;
            });

            // Marquer les volumes possédés
            seriesBooks.forEach(book => {
              const volumeIndex = volumeList.findIndex(v => v.volume_number === book.volume_number);
              if (volumeIndex !== -1) {
                volumeList[volumeIndex] = {
                  ...volumeList[volumeIndex],
                  title: book.title,
                  status: book.status,
                  isOwned: true,
                  id: book.id
                };
              }
            });

            setIsOwned(seriesBooks.length >= foundSeries.volumes);
          }
          
          setVolumes(volumeList);
        } else {
          toast.error('Série non trouvée');
          navigate('/');
        }
      }
    } catch (error) {
      console.error('Erreur lors du chargement de la série:', error);
      toast.error('Erreur lors du chargement de la série');
    } finally {
      setLoading(false);
    }
  };

  const toggleVolumeStatus = async (volume) => {
    if (!volume.isOwned) return;

    try {
      const token = localStorage.getItem('token');
      let newStatus;
      
      switch (volume.status) {
        case 'to_read':
          newStatus = 'reading';
          break;
        case 'reading':
          newStatus = 'completed';
          break;
        case 'completed':
          newStatus = 'to_read';
          break;
        default:
          newStatus = 'reading';
      }

      const response = await fetch(`${backendUrl}/api/books/${volume.id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: newStatus })
      });

      if (response.ok) {
        setVolumes(prev => prev.map(v => 
          v.volume_number === volume.volume_number 
            ? { ...v, status: newStatus }
            : v
        ));
        toast.success(`Tome ${volume.volume_number} mis à jour !`);
      }
    } catch (error) {
      console.error('Erreur lors de la mise à jour:', error);
      toast.error('Erreur lors de la mise à jour');
    }
  };

  const addSeriesToLibrary = async () => {
    if (!series) return;
    try {
      setAddingToLibrary(true);
      const token = localStorage.getItem('token');

      const seriesData = {
        name: series.name || 'Série inconnue',
        authors: series.authors || [series.author || 'Auteur inconnu'],
        category: series.category || 'roman',
        volumes: series.volumes || 1,
        first_published: series.first_published || '',
        description: series.description || '',
      };

      const libraryVolumes = generateVolumesList(
        {
          name: seriesData.name,
          author: Array.isArray(seriesData.authors) ? seriesData.authors[0] : seriesData.authors,
          authors: seriesData.authors,
          category: seriesData.category,
          total_volumes: seriesData.volumes,
          volumes: seriesData.volumes,
        },
        EXTENDED_SERIES_DATABASE
      );

      const authors = seriesData.authors;
      const enrichedMetadata = await enrichSeriesMetadata({ ...seriesData, authors });

      const coverFromSeries = (series.cover_url || series.cover_image_url || '').trim();

      const seriesPayload = {
        series_name: String(seriesData.name),
        author: String(seriesData.authors[0] || 'Auteur inconnu'),
        authors: seriesData.authors.map((a) => String(a)),
        category: String(seriesData.category),
        total_volumes: Number(libraryVolumes.length),
        volumes: libraryVolumes,
        description_fr: enrichedMetadata.description_fr,
        cover_image_url: coverFromSeries || enrichedMetadata.cover_image_url,
        first_published: enrichedMetadata.first_published || String(seriesData.first_published),
        last_published: enrichedMetadata.last_published || '',
        publisher: enrichedMetadata.publisher || '',
        series_status: 'to_read',
      };

      const result = await saveSeriesToLibrary(seriesPayload, token);

      if (result.success) {
        toast.success(
          `Série "${seriesData.name}" ajoutée avec ${libraryVolumes.length} tome${libraryVolumes.length > 1 ? 's' : ''}.`,
          { duration: 4000 }
        );
        await loadSeriesDetails();
      } else {
        toast.error(result.message || "Erreur lors de l'ajout de la série");
      }
    } catch (error) {
      console.error('Erreur ajout série (page détail):', error);
      if (error.message && error.message.includes('409')) {
        toast.error('Cette série est déjà dans ta bibliothèque');
      } else if (error.message && error.message.includes('400')) {
        toast.error('Données de série invalides');
      } else {
        toast.error(error.message || "Erreur lors de l'ajout de la série");
      }
    } finally {
      setAddingToLibrary(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'reading':
        return <PlayIcon className="w-5 h-5 text-blue-500" />;
      default:
        return <XCircleIcon className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'completed':
        return 'Lu';
      case 'reading':
        return 'En cours';
      default:
        return 'À lire';
    }
  };

  const getCategoryBadge = (category) => {
    switch (category) {
      case 'roman':
        return { text: 'Roman', class: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300', emoji: '📚' };
      case 'bd':
        return { text: 'BD', class: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300', emoji: '🎨' };
      case 'manga':
        return { text: 'Manga', class: 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-300', emoji: '🇯🇵' };
      default:
        return { text: 'Livre', class: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300', emoji: '📖' };
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-honeycomb p-4">
        <div className="max-w-4xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded mb-4"></div>
            <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded mb-6"></div>
            <div className="space-y-4">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-16 bg-gray-200 dark:bg-gray-700 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!series) {
    return (
      <div className="min-h-screen bg-honeycomb flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Série non trouvée
          </h1>
          <button
            onClick={() => navigate('/')}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
          >
            Retour à l'accueil
          </button>
        </div>
      </div>
    );
  }

  const categoryBadge = getCategoryBadge(series.category);
  const ownedVolumes = volumes.filter(v => v.isOwned).length;
  const completedVolumes = volumes.filter(v => v.status === 'completed').length;

  return (
    <div className="min-h-screen bg-honeycomb">
      {/* Header */}
      <div className="bg-booktime-mistSoft/75 dark:bg-gray-900/70 backdrop-blur-xl shadow-sm border-b border-booktime-mist/55 dark:border-booktime-800/50 sticky top-0 z-30 safe-area-top">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <button
            onClick={() => navigate('/')}
            className="flex items-center text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white mb-4"
          >
            <ArrowLeftIcon className="w-5 h-5 mr-2" />
            Retour à la bibliothèque
          </button>

          <div className="flex items-start space-x-6">
            {/* Icône de série */}
            <div className="w-24 h-30 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center text-white text-4xl flex-shrink-0 shadow-lg">
              {categoryBadge.emoji}
            </div>

            {/* Informations principales */}
            <div className="flex-1">
              <div className="flex items-center space-x-3 mb-2">
                <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                  {series.name}
                </h1>
                <div className={`${categoryBadge.class} text-sm px-3 py-1 rounded-full flex items-center font-medium`}>
                  <span className="mr-1">{categoryBadge.emoji}</span>
                  {categoryBadge.text}
                </div>
              </div>

              <div className="flex items-center text-gray-600 dark:text-gray-400 mb-3">
                <UserIcon className="w-5 h-5 mr-2" />
                <span className="text-lg">{series.authors.join(', ')}</span>
              </div>

              <p className="text-gray-700 dark:text-gray-300 mb-4 text-lg">
                {series.description}
              </p>

              <div className="flex items-center space-x-6 text-sm text-gray-500 dark:text-gray-500">
                <span className="flex items-center">
                  <BookOpenIcon className="w-4 h-4 mr-1" />
                  {(Array.isArray(series.volumes) ? series.volumes.length : series.volumes) || 0} tomes
                </span>
                <span className="flex items-center">
                  <ClockIcon className="w-4 h-4 mr-1" />
                  Depuis {series.first_published}
                </span>
                <span className={`px-2 py-1 rounded ${
                  series.status === 'completed' 
                    ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' 
                    : 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300'
                }`}>
                  {series.status === 'completed' ? 'Terminée' : 'En cours'}
                </span>
              </div>

              {/* Statistiques de possession */}
              {isOwned && (
                <div className="mt-4 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-green-800 dark:text-green-200 font-medium">
                      Dans votre bibliothèque
                    </span>
                    <span className="text-green-600 dark:text-green-400 font-bold">
                      {ownedVolumes}/{series.volumes} tomes possédés
                    </span>
                  </div>
                  <div className="w-full bg-green-200 dark:bg-green-800 rounded-full h-2">
                    <div 
                      className="bg-green-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${(ownedVolumes / series.volumes) * 100}%` }}
                    ></div>
                  </div>
                  <div className="text-sm text-green-700 dark:text-green-300 mt-1">
                    {completedVolumes} tome(s) lu(s) • {Math.round((completedVolumes / ownedVolumes) * 100) || 0}% de progression
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Contenu principal */}
      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* Bouton d'ajout */}
        {!isOwned && (
          <div className="mb-6">
            <button
              onClick={addSeriesToLibrary}
              disabled={addingToLibrary}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-6 py-3 rounded-lg text-lg font-medium flex items-center space-x-2 shadow-lg"
            >
              {addingToLibrary ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  <span>Ajout en cours...</span>
                </>
              ) : (
                <>
                  <PlusIcon className="w-5 h-5" />
                  <span>Ajouter toute la série à ma bibliothèque</span>
                </>
              )}
            </button>
          </div>
        )}

        {/* Liste des tomes */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm">
          <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
              Liste des tomes
            </h2>
          </div>

          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {volumes.map((volume) => (
              <div
                key={volume.volume_number}
                className={`p-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${
                  volume.isOwned ? 'cursor-pointer' : 'cursor-default'
                }`}
                onClick={() => volume.isOwned && toggleVolumeStatus(volume)}
              >
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center text-white font-bold">
                    {volume.volume_number}
                  </div>
                  
                  <div>
                    <h3 className={`font-medium ${
                      volume.isOwned 
                        ? 'text-gray-900 dark:text-white' 
                        : 'text-gray-500 dark:text-gray-400'
                    }`}>
                      {volume.title}
                    </h3>
                    {volume.isOwned && (
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        Cliquez pour changer le statut
                      </p>
                    )}
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  {volume.isOwned ? (
                    <div className="flex items-center space-x-2">
                      {getStatusIcon(volume.status)}
                      <span className={`text-sm font-medium ${
                        volume.status === 'completed' ? 'text-green-600 dark:text-green-400' :
                        volume.status === 'reading' ? 'text-blue-600 dark:text-blue-400' :
                        'text-gray-500 dark:text-gray-400'
                      }`}>
                        {getStatusText(volume.status)}
                      </span>
                    </div>
                  ) : (
                    <span className="text-sm text-gray-400 dark:text-gray-500">
                      Non possédé
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SeriesDetailPage;