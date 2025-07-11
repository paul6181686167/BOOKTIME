import React, { useState, useEffect } from 'react';
import {
  BookOpenIcon,
  CheckCircleIcon,
  ClockIcon,
  PlusIcon,
  MagnifyingGlassIcon,
  ExclamationTriangleIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
import { bookService } from '../services/bookService';
import { EXTENDED_SERIES_DATABASE } from '../utils/seriesDatabaseExtended';
import toast from 'react-hot-toast';

const SeriesDetailModal = ({ 
  series, 
  isOpen, 
  onClose, 
  onUpdate,
  onAddSeries
}) => {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedTomes, setSelectedTomes] = useState(new Set());
  const [autoCompleting, setAutoCompleting] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [missingAnalysis, setMissingAnalysis] = useState(null);
  const [isSeriesOwned, setIsSeriesOwned] = useState(false);
  const [seriesStatus, setSeriesStatus] = useState('to_read');
  const [readTomes, setReadTomes] = useState(new Set()); // ← AJOUT: État des tomes lus/non lus

  // Fonction pour enrichir les données de série avec les métadonnées de référence
  const enrichSeriesData = (series) => {
    if (!series?.name) return series;
    
    // Rechercher dans la base de données de référence
    const seriesName = series.name.toLowerCase();
    let referenceData = null;
    
    // Parcourir toutes les catégories de la base de données de référence
    for (const category of Object.values(EXTENDED_SERIES_DATABASE)) {
      for (const seriesData of Object.values(category)) {
        if (seriesData.name.toLowerCase() === seriesName || 
            seriesData.variations?.some(variation => variation.toLowerCase() === seriesName)) {
          referenceData = seriesData;
          break;
        }
      }
      if (referenceData) break;
    }
    
    // Enrichir avec les données de référence si trouvées
    if (referenceData) {
      return {
        ...series,
        volumes: referenceData.volumes,
        volume_titles: referenceData.volume_titles, // ← AJOUT: Inclure les vrais noms des tomes
        description: referenceData.description,
        first_published: referenceData.first_published,
        status: referenceData.status,
        referenceFound: true
      };
    }
    
    return series;
  };

  // Fonction pour basculer l'état lu/non lu d'un tome
  const handleTomeReadToggle = (tomeNumber) => {
    setReadTomes(prev => {
      const newReadTomes = new Set(prev);
      if (newReadTomes.has(tomeNumber)) {
        newReadTomes.delete(tomeNumber);
      } else {
        newReadTomes.add(tomeNumber);
      }
      return newReadTomes;
    });
  };

  // Enrichir les données de série au chargement
  const enrichedSeries = enrichSeriesData(series);

  // Options de statut pour les boutons rapides
  const statusOptions = [
    { value: 'to_read', label: 'À lire', color: 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300', emoji: '' },
    { value: 'reading', label: 'En cours', color: 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-300', emoji: '' },
    { value: 'completed', label: 'Terminé', color: 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300', emoji: '' },
  ];

  // Fonction pour changer rapidement le statut de la série
  const handleQuickStatusChange = async (newStatus) => {
    console.log('🎯 DÉBUT handleQuickStatusChange:', { newStatus, isSeriesOwned, series });
    
    if (!isSeriesOwned) {
      console.log('❌ Série non possédée, affichage erreur');
      toast.error('Vous devez d\'abord ajouter cette série à votre bibliothèque');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      console.log('🔑 Token trouvé:', !!token);
      console.log('🔄 Changement statut série:', series.name, 'vers', newStatus);
      
      // Rechercher le livre série dans la bibliothèque
      const response = await fetch(`${backendUrl}/api/books/all?saga=${encodeURIComponent(series.name)}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log('📡 Réponse recherche série:', { status: response.status, ok: response.ok });
      
      if (response.ok) {
        const data = await response.json();
        console.log('📚 Données reçues:', data);
        
        // CORRECTION RCA: Même logique case-insensitive pour chercher le livre série
        const seriesBook = data.items?.find(book => 
          book.saga?.toLowerCase().includes(series.name.toLowerCase()) && 
          (book.is_series === true || book.title?.toLowerCase().includes('collection'))
        );
        
        if (seriesBook) {
          console.log('📖 Livre série trouvé:', seriesBook);
          // Mettre à jour le statut du livre série
          const updateResponse = await fetch(`${backendUrl}/api/books/${seriesBook.id}`, {
            method: 'PUT',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: newStatus })
          });
          
          console.log('🔄 Réponse mise à jour:', { status: updateResponse.status, ok: updateResponse.ok });
          
          if (updateResponse.ok) {
            const updatedBook = await updateResponse.json();
            console.log('✅ Livre mis à jour:', updatedBook);
            setSeriesStatus(newStatus);
            toast.success(`Statut de la série "${series.name}" changé vers "${statusOptions.find(s => s.value === newStatus)?.label}"`);
            
            // Actualiser la bibliothèque
            if (onUpdate) {
              console.log('🔄 Actualisation bibliothèque');
              onUpdate();
            }
          } else {
            const errorData = await updateResponse.json();
            console.error('❌ Erreur mise à jour:', errorData);
            toast.error('Erreur lors de la mise à jour du statut');
          }
        } else {
          console.error('❌ Livre série non trouvé dans les résultats');
          console.log('📋 Livres disponibles:', data.items?.map(b => ({ title: b.title, saga: b.saga, is_series: b.is_series })));
          toast.error('Livre série non trouvé dans la bibliothèque');
        }
      } else {
        const errorData = await response.json();
        console.error('❌ Erreur recherche série:', errorData);
        toast.error('Erreur lors de la recherche de la série');
      }
    } catch (error) {
      console.error('❌ Erreur générale changement statut:', error);
      toast.error('Erreur lors du changement de statut');
    }
  };

  // Fonction pour vérifier si la série est déjà dans la bibliothèque
  const checkIfSeriesOwned = async () => {
    if (!series?.name) {
      console.log('⚠️ Pas de nom de série fourni');
      return;
    }
    
    try {
      const token = localStorage.getItem('token');
      const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
      
      console.log('🔍 Vérification série possédée:', series.name);
      console.log('🔑 Token disponible:', !!token);
      console.log('🌐 Backend URL:', backendUrl);
      
      // Rechercher les livres de cette saga
      const response = await fetch(`${backendUrl}/api/books/all?saga=${encodeURIComponent(series.name)}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log('📡 Réponse vérification:', { 
        status: response.status, 
        ok: response.ok,
        statusText: response.statusText 
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('📚 Livres trouvés pour saga:', data);
        
        // CORRECTION RCA: Utiliser case-insensitive substring match pour compatibilité avec regex backend
        const hasSeriesBook = data.items && data.items.some(book => 
          book.saga?.toLowerCase().includes(series.name.toLowerCase()) && 
          (book.is_series === true || book.title?.toLowerCase().includes('collection'))
        );
        
        console.log('📖 Série déjà possédée:', hasSeriesBook);
        setIsSeriesOwned(hasSeriesBook);
        
        // Récupérer le statut de la série si elle existe
        if (hasSeriesBook) {
          // CORRECTION RCA: Même logique case-insensitive pour récupérer le statut
          const seriesBook = data.items.find(book => 
            book.saga?.toLowerCase().includes(series.name.toLowerCase()) && 
            (book.is_series === true || book.title?.toLowerCase().includes('collection'))
          );
          if (seriesBook) {
            setSeriesStatus(seriesBook.status || 'to_read');
            console.log('📊 Statut série récupéré:', seriesBook.status);
          }
        }
        
        console.log('✅ Série déjà possédée:', hasSeriesBook);
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Erreur inconnue' }));
        console.error('❌ Erreur API vérification série:', {
          status: response.status,
          statusText: response.statusText,
          error: errorData
        });
        // Ne pas bloquer l'interface si l'API échoue
        setIsSeriesOwned(false);
      }
    } catch (error) {
      console.error('❌ Erreur lors de la vérification de la série:', error);
      // Ne pas bloquer l'interface si la vérification échoue
      setIsSeriesOwned(false);
    }
  };

  useEffect(() => {
    if (isOpen && series) {
      loadSeriesBooks();
      checkIfSeriesOwned();
      setReadTomes(new Set()); // ← AJOUT: Réinitialiser l'état des tomes lus à chaque ouverture
    }
  }, [isOpen, series]);

  const loadSeriesBooks = async () => {
    if (!series?.name) return;
    
    try {
      setLoading(true);
      const booksData = await bookService.getBooksBySaga(series.name);
      setBooks(booksData.sort((a, b) => (a.volume_number || 0) - (b.volume_number || 0)));
    } catch (error) {
      console.error('Erreur lors du chargement des livres de la série:', error);
      toast.error('Erreur lors du chargement des livres');
    } finally {
      setLoading(false);
    }
  };

  const handleTomeToggle = async (book, isRead) => {
    try {
      await bookService.toggleTomeStatus(series.name, book.volume_number, isRead);
      await loadSeriesBooks();
      if (onUpdate) onUpdate();
      toast.success(`Tome ${book.volume_number} marqué comme ${isRead ? 'lu' : 'non lu'}`);
    } catch (error) {
      console.error('Erreur lors de la mise à jour du tome:', error);
      toast.error('Erreur lors de la mise à jour');
    }
  };

  const handleAutoComplete = async () => {
    try {
      setAutoCompleting(true);
      const maxVolume = Math.max(...books.map(b => b.volume_number || 0));
      const targetVolume = Math.max(maxVolume + 10, 20);

      const result = await bookService.autoCompleteSaga(series.name, targetVolume);
      await loadSeriesBooks();
      if (onUpdate) onUpdate();
      toast.success(`${result.created_books?.length || 0} nouveaux tomes ajoutés !`);
    } catch (error) {
      console.error('Erreur lors de l\'auto-complétion:', error);
      toast.error('Erreur lors de l\'auto-complétion');
    } finally {
      setAutoCompleting(false);
    }
  };

  const handleAnalyzeMissing = async () => {
    try {
      setAnalyzing(true);
      const analysis = await bookService.analyzeMissingVolumes(series.name);
      setMissingAnalysis(analysis);
      
      if (analysis.missing_volumes.length > 0) {
        toast.success(`${analysis.missing_volumes.length} tome(s) manquant(s) détecté(s)`);
      } else {
        toast.success('Aucun tome manquant détecté');
      }
    } catch (error) {
      console.error('Erreur lors de l\'analyse:', error);
      toast.error('Erreur lors de l\'analyse');
    } finally {
      setAnalyzing(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300';
      case 'reading':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
    }
  };

  const getStatusLabel = (status) => {
    switch (status) {
      case 'completed': return 'Lu';
      case 'reading': return 'En cours';
      default: return 'Non lu';
    }
  };

  const getCategoryEmoji = (category) => {
    switch (category) {
      case 'bd': return '🎨';
      case 'manga': return '🇯🇵';
      case 'roman': return '📚';
      default: return '📖';
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="modal-content-wide shadow-2xl overflow-hidden">>
        
        {/* Header */}
        <div className="border-b border-gray-200 dark:border-gray-700 p-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center space-x-4">
              <div className="w-16 h-20 bg-gradient-to-br from-purple-500 to-blue-600 rounded-lg flex items-center justify-center text-white text-2xl">
                {getCategoryEmoji(series?.category)}
              </div>
              
              <div>
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-1">
                  {series?.name}
                </h2>
                <p className="text-gray-600 dark:text-gray-400 mb-2">
                  par {series?.author}
                </p>
                <div className="flex items-center space-x-4 text-sm">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadge(series?.status)}`}>
                    {getStatusLabel(series?.status)}
                  </span>
                  <span className="text-gray-500 dark:text-gray-400">
                    📚 {books.length} tome(s)
                  </span>
                  <span className="text-gray-500 dark:text-gray-400">
                    🏆 {series?.completion_percentage || 0}% complété
                  </span>
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              {/* Bouton Ajouter fonctionnel (même style que BookDetailModal) */}
              {!isSeriesOwned && onAddSeries && (
                <button
                  onClick={async () => {
                    try {
                      console.log('🟢 Clic sur ajouter série:', series);
                      await onAddSeries(series);
                      // CORRECTION: Attendre un peu puis re-vérifier si la série est possédée
                      setTimeout(() => {
                        checkIfSeriesOwned();
                      }, 1000);
                    } catch (error) {
                      console.error('❌ Erreur lors de l\'ajout de la série:', error);
                    }
                  }}
                  className="px-4 py-2 text-sm font-medium text-white bg-green-600 hover:bg-green-700 rounded-md transition-colors flex items-center space-x-2"
                >
                  <span>+</span>
                  <span>Ajouter à ma bibliothèque</span>
                </button>
              )}
              
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 text-xl"
              >
                ✕
              </button>
            </div>
          </div>
        </div>

        {/* Boutons rapides de changement de statut - MÊME EMPLACEMENT QUE DANS BookDetailModal */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center mb-2">
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Changer le statut rapidement :</h3>
            {/* Indicateur de debug */}
            <span className="ml-2 text-xs text-gray-500">
              (Série possédée: {isSeriesOwned ? '✅' : '❌'})
            </span>
          </div>
          <div className="flex rounded-lg overflow-hidden border border-gray-200 dark:border-gray-600 w-fit">
            {statusOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => {
                  console.log('🖱️ CLIC BOUTON STATUT:', {
                    option: option.value,
                    isSeriesOwned,
                    seriesName: series?.name
                  });
                  handleQuickStatusChange(option.value);
                }}
                className={`px-4 py-2 text-sm font-medium transition-all flex items-center space-x-2 ${
                  seriesStatus === option.value
                    ? 'bg-gray-900 dark:bg-white text-white dark:text-gray-900 shadow-md'
                    : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'
                }`}
                title={`Marquer comme ${option.label}`}
                disabled={!isSeriesOwned}
              >
                <span className="text-base">{option.emoji}</span>
                <span>{option.label}</span>
              </button>
            ))}
          </div>
          {!isSeriesOwned && (
            <p className="text-xs text-gray-500 mt-2">
              Ajoutez d'abord cette série à votre bibliothèque pour changer son statut
            </p>
          )}
        </div>

        {/* Actions Bar */}
        <div className="border-b border-gray-200 dark:border-gray-700 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {selectedTomes.size > 0 && (
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {selectedTomes.size} sélectionné(s)
                  </span>
                  <button
                    onClick={() => setSelectedTomes(new Set())}
                    className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
                  >
                    Désélectionner
                  </button>
                </div>
              )}
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={handleAnalyzeMissing}
                disabled={analyzing}
                className="p-2 text-orange-600 hover:bg-orange-50 dark:hover:bg-orange-900/20 rounded-full transition-colors"
                title="Analyser les tomes manquants"
              >
                {analyzing ? (
                  <div className="w-5 h-5 border-2 border-orange-600 border-t-transparent rounded-full animate-spin" />
                ) : (
                  <MagnifyingGlassIcon className="w-5 h-5" />
                )}
              </button>
              
              <button
                onClick={handleAutoComplete}
                disabled={autoCompleting}
                className="p-2 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-full transition-colors"
                title="Auto-compléter la série"
              >
                {autoCompleting ? (
                  <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                ) : (
                  <SparklesIcon className="w-5 h-5" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Missing Volumes Analysis */}
        {missingAnalysis && missingAnalysis.missing_volumes.length > 0 && (
          <div className="bg-orange-50 dark:bg-orange-900/20 border-b border-orange-200 dark:border-orange-800 px-6 py-3">
            <div className="flex items-center space-x-2 text-orange-800 dark:text-orange-300">
              <ExclamationTriangleIcon className="w-4 h-4" />
              <span className="text-sm font-medium">
                {missingAnalysis.missing_volumes.length} tome(s) manquant(s) : 
                {missingAnalysis.missing_volumes.slice(0, 10).join(', ')}
                {missingAnalysis.missing_volumes.length > 10 && '...'}
              </span>
            </div>
          </div>
        )}

        {/* Liste des tomes avec toggles lu/non lu */}
        <div className="border-b border-gray-200 dark:border-gray-700 px-6 py-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">Liste des tomes</h3>
          
          {enrichedSeries?.volumes && enrichedSeries.volumes > 0 ? (
            <div className="space-y-2">
              {Array.from({ length: enrichedSeries.volumes }, (_, index) => {
                const tomeNumber = index + 1;
                // Utiliser le titre spécifique s'il existe, sinon titre générique
                const tomeTitle = enrichedSeries.volume_titles?.[tomeNumber] || `${enrichedSeries.name} - Tome ${tomeNumber}`;
                const isRead = readTomes.has(tomeNumber);
                
                return (
                  <div key={tomeNumber} className="flex items-center justify-between p-2 hover:bg-gray-50 dark:hover:bg-gray-800 rounded">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-medium text-purple-600 dark:text-purple-400 min-w-[60px]">
                        Tome {tomeNumber}
                      </span>
                      <span className={`text-sm transition-colors ${
                        isRead 
                          ? 'text-green-700 dark:text-green-300 line-through' 
                          : 'text-gray-700 dark:text-gray-300'
                      }`}>
                        {tomeTitle}
                      </span>
                    </div>
                    
                    {/* Toggle Switch lu/non lu */}
                    <div className="flex items-center space-x-2">
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {isRead ? 'Lu' : 'Non lu'}
                      </span>
                      <button
                        onClick={() => handleTomeReadToggle(tomeNumber)}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 ${
                          isRead
                            ? 'bg-green-600 hover:bg-green-700'
                            : 'bg-gray-200 hover:bg-gray-300 dark:bg-gray-600 dark:hover:bg-gray-500'
                        }`}
                        title={isRead ? 'Marquer comme non lu' : 'Marquer comme lu'}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform duration-200 ease-in-out ${
                            isRead ? 'translate-x-6' : 'translate-x-1'
                          }`}
                        />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400 italic">
              Informations sur les tomes non disponibles pour cette série
            </p>
          )}
        </div>

        {/* Books List (Section détaillée existante) */}
        <div className="flex-1 overflow-y-auto p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Gestion détaillée</h3>
          {loading ? (
            <div className="space-y-3">
              {Array.from({ length: 10 }).map((_, i) => (
                <div key={i} className="h-16 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {books.map((book) => (
                <div
                  key={book.id}
                  className={`flex items-center justify-between p-4 rounded-lg border transition-all ${
                    selectedTomes.has(book.volume_number)
                      ? 'border-blue-300 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }`}
                >
                  <div className="flex items-center space-x-4">
                    <input
                      type="checkbox"
                      checked={selectedTomes.has(book.volume_number)}
                      onChange={(e) => {
                        const newSelected = new Set(selectedTomes);
                        if (e.target.checked) {
                          newSelected.add(book.volume_number);
                        } else {
                          newSelected.delete(book.volume_number);
                        }
                        setSelectedTomes(newSelected);
                      }}
                      className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                    
                    <div className="w-8 h-10 bg-gray-100 dark:bg-gray-700 rounded flex-shrink-0 overflow-hidden">
                      {book.cover_url ? (
                        <img 
                          src={book.cover_url} 
                          alt={book.title}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center">
                          <BookOpenIcon className="w-4 h-4 text-gray-400" />
                        </div>
                      )}
                    </div>
                    
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-300">
                          Tome {book.volume_number || '?'}
                        </span>
                        <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${getStatusBadge(book.status)}`}>
                          {getStatusLabel(book.status)}
                        </span>
                        {book.auto_added && (
                          <span className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-300">
                            Auto-ajouté
                          </span>
                        )}
                      </div>
                      
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white mb-1">
                        {book.title}
                      </h4>
                      
                      {book.description && (
                        <p className="text-xs text-gray-600 dark:text-gray-400 truncate">
                          {book.description.substring(0, 100)}...
                        </p>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleTomeToggle(book, book.status !== 'completed')}
                      className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                        book.status === 'completed'
                          ? 'bg-green-100 text-green-800 hover:bg-green-200 dark:bg-green-900/20 dark:text-green-300'
                          : 'bg-gray-100 text-gray-800 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
                      }`}
                    >
                      {book.status === 'completed' ? '✓ Lu' : 'Marquer comme lu'}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SeriesDetailModal;