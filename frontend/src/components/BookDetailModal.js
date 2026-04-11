import React, { useState, useEffect, useRef, useCallback } from 'react';
import { XMarkIcon, StarIcon, TrashIcon, PencilIcon, LanguageIcon, SparklesIcon, BookmarkIcon, ChatBubbleLeftIcon } from '@heroicons/react/24/outline';
import { StarIcon as StarSolidIcon, BookmarkIcon as BookmarkSolidIcon } from '@heroicons/react/24/solid';
import toast from 'react-hot-toast';
import LanguageSelector from './LanguageSelector';
import { getLanguageByCode } from '../constants/languages';
import { API_BASE_URL } from '../config/environment';
import confetti from 'canvas-confetti';

// Déclenche les confettis de célébration
const launchConfetti = () => {
  const count = 180;
  const defaults = { origin: { y: 0.65 }, zIndex: 9999 };
  const fire = (particleRatio, opts) => {
    confetti({ ...defaults, ...opts, particleCount: Math.floor(count * particleRatio) });
  };
  fire(0.25, { spread: 26, startVelocity: 55 });
  fire(0.2,  { spread: 60 });
  fire(0.35, { spread: 100, decay: 0.91, scalar: 0.8 });
  fire(0.1,  { spread: 120, startVelocity: 25, decay: 0.92, scalar: 1.2 });
  fire(0.1,  { spread: 120, startVelocity: 45 });
};

// Service Open Library pour l'enrichissement
const openLibraryService = {
  async enrichBook(bookId) {
    try {
      const response = await fetch(`${API_BASE_URL}/api/books/${bookId}/enrich`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Erreur HTTP: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Erreur lors de l\'enrichissement:', error);
      throw error;
    }
  }
};

const BookDetailModal = ({ book, onClose, onUpdate, onDelete, onAddFromOpenLibrary, onAuthorClick }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [activeTab, setActiveTab] = useState('details'); // 'details' | 'notes'
  const [bouncing, setBouncing] = useState(null); // id du bouton en train de bouncer
  const [olDetails, setOlDetails] = useState(null); // détails enrichis depuis OL
  const [olLoading, setOlLoading] = useState(false);
  const [editData, setEditData] = useState({
    status: book.status,
    current_page: book.current_page || 0,
    rating: book.rating || 0,
    review: book.review || '',
    notes: book.notes || '',
    original_language: book.original_language || 'français',
    available_translations: book.available_translations || [],
    reading_language: book.reading_language || 'français',
    saga: book.saga || '',
    volume_number: book.volume_number || '',
  });
  const [pageInput, setPageInput] = useState(book.current_page || 0);
  const [isLoading, setIsLoading] = useState(false);
  const [enriching, setEnriching] = useState(false);
  const [isAdding, setIsAdding] = useState(false);
  const [addDone, setAddDone] = useState(false);
  const pageInputRef = useRef(null);

  useEffect(() => {
    setEditData({
      status: book.status,
      current_page: book.current_page || 0,
      rating: book.rating || 0,
      review: book.review || '',
      notes: book.notes || '',
      original_language: book.original_language || 'français',
      available_translations: book.available_translations || [],
      reading_language: book.reading_language || 'français',
      saga: book.saga || '',
      volume_number: book.volume_number || '',
    });
    setPageInput(book.current_page || 0);
  }, [book]);

  // Charger la description complète depuis OL si le livre est isFromOpenLibrary et sans description
  useEffect(() => {
    const olKey = book.ol_key;
    if (!olKey || book.description) return; // déjà une description, rien à faire
    if (!book.isFromOpenLibrary && !olKey.startsWith('/works/')) return;

    setOlLoading(true);
    const stripped = olKey.startsWith('/') ? olKey.slice(1) : olKey;
    const token = localStorage.getItem('token');
    fetch(`${API_BASE_URL}/api/openlibrary/book/${stripped}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
      .then((r) => r.ok ? r.json() : null)
      .then((data) => { if (data) setOlDetails(data); })
      .catch(() => {})
      .finally(() => setOlLoading(false));
  }, [book.ol_key, book.description, book.isFromOpenLibrary]);

  // Micro-bounce sur un bouton
  const triggerBounce = useCallback((id) => {
    setBouncing(id);
    setTimeout(() => setBouncing(null), 380);
  }, []);

  const statusOptions = [
    { value: 'to_read',   label: 'À lire',   color: 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300',    emoji: '📌' },
    { value: 'reading',   label: 'En cours', color: 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-300',    emoji: '📖' },
    { value: 'completed', label: 'Terminé',  color: 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300', emoji: '✅' },
  ];

  // Changer rapidement le statut
  const handleQuickStatusChange = async (newStatus) => {
    triggerBounce(`status-${newStatus}`);
    try {
      const updates = { ...editData, status: newStatus };
      await onUpdate(book.id, updates);
      if (newStatus === 'completed') {
        setTimeout(launchConfetti, 200);
        toast.success('🎉 Bravo, livre terminé !', { duration: 3000, icon: '🏆' });
      }
    } catch (error) {
      toast.error('Erreur lors de la mise à jour du statut');
    }
  };

  // Sauvegarder la page courante rapidement (sans mode édition complet)
  const handlePageSave = async () => {
    const page = parseInt(pageInput) || 0;
    if (page === (book.current_page || 0)) return;
    triggerBounce('page-save');
    try {
      await onUpdate(book.id, { current_page: page });
    } catch (error) {
      toast.error('Erreur lors de la mise à jour de la page');
    }
  };


  const handleSave = async () => {
    setIsLoading(true);
    triggerBounce('save');
    try {
      const updates = {
        ...editData,
        current_page: parseInt(editData.current_page) || 0,
      };
      if (updates.status === 'completed' && book.status !== 'completed') {
        setTimeout(launchConfetti, 300);
      }
      await onUpdate(book.id, updates);
      setIsEditing(false);
      toast.success('Livre mis à jour !');
    } catch (error) {
      toast.error('Erreur lors de la mise à jour');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer ce livre ?')) {
      setIsLoading(true);
      try {
        await onDelete(book.id);
        toast.success('Livre supprimé avec succès !');
      } catch (error) {
        toast.error('Erreur lors de la suppression');
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleEnrich = async () => {
    setEnriching(true);
    try {
      const result = await openLibraryService.enrichBook(book.id);
      if (result.message) {
        toast.success(result.message);
        if (result.book) {
          // Recharger les données du livre dans le parent
          window.location.reload(); // Solution simple pour rafraîchir
        }
      }
    } catch (error) {
      console.error('Erreur lors de l\'enrichissement:', error);
      toast.error(error.message || 'Erreur lors de l\'enrichissement du livre');
    } finally {
      setEnriching(false);
    }
  };

  // Fonction pour ajouter un livre depuis Open Library
  const handleAddFromOpenLibrary = async () => {
    if (!onAddFromOpenLibrary || !book.isFromOpenLibrary || isAdding) return;
    setIsAdding(true);
    try {
      await onAddFromOpenLibrary(book);
      setAddDone(true);
      setTimeout(() => onClose(), 800);
    } catch (error) {
      console.error('Erreur ajout livre:', error);
      setIsAdding(false);
    }
  };

  const handleRatingClick = (rating) => {
    setEditData(prev => ({ ...prev, rating }));
  };

  const getProgressPercentage = () => {
    if (!book.total_pages || book.total_pages === 0) return 0;
    const currentPage = isEditing ? editData.current_page : book.current_page;
    return Math.min(100, (currentPage / book.total_pages) * 100);
  };

  const getCurrentStatus = () => {
    const status = isEditing ? editData.status : book.status;
    return statusOptions.find(s => s.value === status) || statusOptions[0];
  };

  const getLanguageInfo = (languageCode) => {
    return getLanguageByCode(languageCode);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content-wide modal-animate w-full md:w-auto" onClick={(e) => e.stopPropagation()}>
        {/* Barre mobile sticky : fermeture toujours visible */}
        <div className="sticky top-0 z-20 flex items-center justify-between px-4 py-3 md:hidden border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
          <span className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Détail</span>
          <button type="button" onClick={onClose} className="w-10 h-10 flex items-center justify-center rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>
        <div className="px-4 md:px-0 pt-2 md:pt-0">
        <div className="flex flex-col gap-4 mb-4 md:flex-row md:items-start md:justify-between md:gap-6">
          <div className="min-w-0 flex-1">
            <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white mb-2 break-words">{book.title}</h2>
            <p className="text-base sm:text-lg text-gray-600 dark:text-gray-400 mb-4">
              par{' '}
              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  if (onAuthorClick) onAuthorClick(book.author);
                }}
                className="text-lg text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors underline"
              >
                {book.author}
              </button>
            </p>
            
            {/* Catégorie et statut */}
            <div className="flex items-center space-x-3 mb-4">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-booktime-100 dark:bg-booktime-900/30 text-booktime-800 dark:text-booktime-300">
                {book.category === 'roman' && '📚'} 
                {book.category === 'bd' && '🎨'} 
                {book.category === 'manga' && '🇯🇵'} 
                {book.category.charAt(0).toUpperCase() + book.category.slice(1)}
              </span>
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getCurrentStatus().color}`}>
                {getCurrentStatus().label}
              </span>
            </div>

            {/* Boutons rapides de changement de statut */}
            {(!book.isFromOpenLibrary || book.isOwned) && !isEditing && (
              <div className="mb-4">
                <div className="flex items-center mb-2">
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Statut :</h3>
                </div>
                <div className="flex rounded-lg overflow-hidden border border-gray-200 dark:border-gray-600 w-fit">
                  {statusOptions.map((option) => (
                    <button
                      key={option.value}
                      onClick={() => handleQuickStatusChange(option.value)}
                      className={`btn-ripple px-4 py-2 text-sm font-medium transition-all flex items-center space-x-2 ${
                        bouncing === `status-${option.value}` ? 'btn-bounce' : ''
                      } ${
                        book.status === option.value
                          ? 'bg-gray-900 dark:bg-white text-white dark:text-gray-900 shadow-md'
                          : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'
                      }`}
                      title={`Marquer comme ${option.label}`}
                    >
                      <span className="text-base">{option.emoji}</span>
                      <span>{option.label}</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Saisie rapide de la page (visible dès qu'En cours, page optionnelle) */}
            {(!book.isFromOpenLibrary || book.isOwned) && !isEditing && book.status === 'reading' && (
              <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-100 dark:border-blue-800">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-sm font-medium text-blue-700 dark:text-blue-300">Progression de lecture</h3>
                  {book.total_pages > 0 && pageInput > 0 && (
                    <span className="text-sm font-bold text-blue-700 dark:text-blue-300">
                      {Math.round(((pageInput || 0) / book.total_pages) * 100)}%
                    </span>
                  )}
                </div>
                {book.total_pages > 0 && pageInput > 0 && (
                  <div className="w-full bg-blue-200 dark:bg-blue-800 rounded-full h-2 mb-3">
                    <div
                      className="bg-blue-500 h-2 rounded-full reading-progress-bar transition-all duration-300"
                      style={{ width: `${Math.min(100, Math.round(((pageInput || 0) / book.total_pages) * 100))}%` }}
                    />
                  </div>
                )}
                <div className="flex items-center gap-2">
                  <span className="text-sm text-blue-600 dark:text-blue-400">Page</span>
                  <input
                    ref={pageInputRef}
                    type="number"
                    value={pageInput || ''}
                    placeholder="optionnel"
                    onChange={(e) => setPageInput(Math.max(0, Math.min(book.total_pages || 99999, parseInt(e.target.value) || 0)))}
                    onBlur={handlePageSave}
                    onKeyDown={(e) => e.key === 'Enter' && handlePageSave()}
                    min="0"
                    max={book.total_pages || undefined}
                    className="w-24 px-2 py-1 text-sm border border-blue-300 dark:border-blue-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-400 text-center"
                  />
                  {book.total_pages > 0 && (
                    <span className="text-sm text-blue-600 dark:text-blue-400">/ {book.total_pages}</span>
                  )}
                  <button
                    onClick={handlePageSave}
                    className={`btn-ripple ml-auto px-3 py-1 text-sm font-medium bg-blue-500 hover:bg-blue-600 active:bg-blue-700 text-white rounded-md transition-colors ${bouncing === 'page-save' ? 'btn-bounce' : ''}`}
                  >
                    ✓ Sauvegarder
                  </button>
                </div>
              </div>
            )}


            {/* Informations linguistiques */}
            <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 mb-4">
              <div className="flex items-center gap-2 mb-3">
                <LanguageIcon className="h-5 w-5 text-gray-600 dark:text-gray-400" />
                <h3 className="text-sm font-medium text-gray-900 dark:text-white">Informations linguistiques</h3>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-gray-600 dark:text-gray-400">Langue originale:</span>
                  <div className="flex items-center gap-1 mt-1">
                    <span>{getLanguageInfo(book.original_language).flag}</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {getLanguageInfo(book.original_language).name}
                    </span>
                  </div>
                </div>
                
                <div>
                  <span className="text-gray-600 dark:text-gray-400">Langue de lecture:</span>
                  <div className="flex items-center gap-1 mt-1">
                    <span>{getLanguageInfo(book.reading_language).flag}</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {getLanguageInfo(book.reading_language).name}
                    </span>
                  </div>
                </div>
                
                <div>
                  <span className="text-gray-600 dark:text-gray-400">Traductions:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {book.available_translations && book.available_translations.length > 0 ? (
                      book.available_translations.map(lang => (
                        <span key={lang} className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 text-xs rounded">
                          <span>{getLanguageInfo(lang).flag}</span>
                          <span>{getLanguageInfo(lang).name}</span>
                        </span>
                      ))
                    ) : (
                      <span className="text-gray-500 dark:text-gray-400 text-xs">Aucune traduction renseignée</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div className="flex w-full flex-col gap-2 shrink-0 md:w-auto md:items-end">
            {/* Bouton Ajouter pour les livres Open Library — pleine largeur sur mobile */}
            {book.isFromOpenLibrary && !book.isOwned && onAddFromOpenLibrary && (
              <button
                onClick={handleAddFromOpenLibrary}
                disabled={isAdding || addDone}
                className={`btn-ripple w-full md:w-auto md:min-w-[180px] px-4 py-3 md:py-2 text-sm font-semibold text-white rounded-xl md:rounded-lg transition-all flex items-center justify-center gap-2 ${
                  addDone
                    ? 'bg-green-500 cursor-default'
                    : isAdding
                    ? 'bg-green-500 cursor-not-allowed opacity-80'
                    : 'bg-green-600 hover:bg-green-700 hover:shadow-md active:bg-green-800'
                }`}
              >
                {addDone ? (
                  <>
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                    <span>Ajouté !</span>
                  </>
                ) : isAdding ? (
                  <>
                    <span className="btn-spinner" />
                    <span>Ajout en cours…</span>
                  </>
                ) : (
                  <>
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                    </svg>
                    <span>Ajouter à ma bibliothèque</span>
                  </>
                )}
              </button>
            )}
            
            <div className="flex flex-row flex-wrap items-center justify-end gap-1 md:gap-2">
            {/* Boutons pour les livres locaux ou possédés */}
            {(!book.isFromOpenLibrary || book.isOwned) && (
              <>
                <button
                  onClick={handleEnrich}
                  disabled={enriching}
                  className="p-2 text-blue-400 dark:text-blue-500 hover:text-blue-600 dark:hover:text-blue-400 transition-colors disabled:opacity-50"
                  title="Enrichir avec Open Library"
                >
                  {enriching ? (
                    <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                  ) : (
                    <SparklesIcon className="h-5 w-5" />
                  )}
                </button>
                <button
                  onClick={() => setIsEditing(!isEditing)}
                  className="p-2 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                >
                  <PencilIcon className="h-5 w-5" />
                </button>
                <button
                  onClick={handleDelete}
                  className="p-2 text-red-400 dark:text-red-500 hover:text-red-600 dark:hover:text-red-400 transition-colors"
                >
                  <TrashIcon className="h-5 w-5" />
                </button>
              </>
            )}
            
            <button
              type="button"
              onClick={onClose}
              className="hidden md:block p-2 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
              aria-label="Fermer"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
            </div>
          </div>
        </div>

        {/* Onglets Détails / Notes */}
        {true && (
          <div className="flex space-x-1 mb-5 border-b border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setActiveTab('details')}
              className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors flex items-center gap-2 ${
                activeTab === 'details'
                  ? 'bg-white dark:bg-gray-800 text-booktime-600 border-b-2 border-booktime-500'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
              }`}
            >
              <BookmarkIcon className="h-4 w-4" />
              Détails
            </button>
            <button
              onClick={() => setActiveTab('notes')}
              className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors flex items-center gap-2 ${
                activeTab === 'notes'
                  ? 'bg-white dark:bg-gray-800 text-booktime-600 border-b-2 border-booktime-500'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
              }`}
            >
              <ChatBubbleLeftIcon className="h-4 w-4" />
              Notes & Citations
              {book.notes && <span className="w-2 h-2 rounded-full bg-green-500 inline-block" />}
            </button>
          </div>
        )}

        {/* Onglet Notes */}
        {activeTab === 'notes' && (
          <div className="animate-fadeIn">
            <div className="mb-4 p-4 bg-yellow-50 dark:bg-yellow-900/10 border border-yellow-200 dark:border-yellow-800 rounded-lg">
              <p className="text-xs text-yellow-700 dark:text-yellow-400">
                💡 Notez ici vos passages préférés, citations marquantes, pensées ou réflexions sur ce livre.
              </p>
            </div>
            <textarea
              value={isEditing ? editData.notes : (book.notes || '')}
              onChange={(e) => isEditing && setEditData(prev => ({ ...prev, notes: e.target.value }))}
              readOnly={!isEditing}
              rows={12}
              placeholder={isEditing ? "Écrivez vos notes, citations et réflexions sur ce livre..." : "Aucune note pour ce livre. Cliquez sur ✏️ pour en ajouter."}
              className={`w-full px-4 py-3 border rounded-lg text-sm leading-relaxed resize-none transition-colors ${
                isEditing
                  ? 'border-blue-300 dark:border-blue-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-booktime-500'
                  : 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 text-gray-700 dark:text-gray-300 cursor-default'
              }`}
            />
            {!isEditing && !book.notes && (
              <button
                onClick={() => { setIsEditing(true); setTimeout(() => {}, 50); }}
                className="mt-3 w-full py-2 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg text-gray-500 dark:text-gray-400 hover:border-booktime-400 hover:text-booktime-600 transition-colors text-sm"
              >
                + Ajouter une note
              </button>
            )}
          </div>
        )}

        {/* Onglet Détails */}
        {activeTab === 'details' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Image de couverture */}
          <div className="md:col-span-1">
            <div className="aspect-[2/3] bg-gray-100 dark:bg-gray-700 rounded-lg overflow-hidden">
              {book.cover_url ? (
                <img 
                  src={book.cover_url} 
                  alt={book.title}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800">
                  <div className="text-center p-4">
                    <div className="text-6xl mb-2">
                      {book.category === 'roman' && '📚'}
                      {book.category === 'bd' && '🎨'}
                      {book.category === 'manga' && '🇯🇵'}
                    </div>
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
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">🌍 Modifier les langues</h3>
                
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
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Série (optionnel)
                  </label>
                  <input
                    type="text"
                    value={editData.saga}
                    onChange={(e) => setEditData(prev => ({ ...prev, saga: e.target.value }))}
                    placeholder="ex: Harry Potter, One Piece…"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-booktime-500 text-sm"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Tome n°
                  </label>
                  <input
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
                  📚 {book.saga}{book.volume_number ? ` — Tome ${book.volume_number}` : ''}
                </span>
              </div>
            ) : null}

            {/* Statut */}
            {isEditing ? (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Statut
                </label>
                <select
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
            )}

            {/* Progression */}
            {book.total_pages && (
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Progression</h3>
                {isEditing ? (
                  <div className="space-y-2">
                    <input
                      type="number"
                      value={editData.current_page}
                      onChange={(e) => setEditData(prev => ({ ...prev, current_page: e.target.value }))}
                      min="0"
                      max={book.total_pages}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-booktime-500 transition-colors"
                    />
                    <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
                      <span>{editData.current_page} pages lues</span>
                      <span>{book.total_pages} pages total</span>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
                      <span>{book.current_page} pages lues</span>
                      <span>{book.total_pages} pages total</span>
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

            {/* Note */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Note</h3>
              <div className="flex space-x-1">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    onClick={() => isEditing && handleRatingClick(star)}
                    className={`h-6 w-6 ${isEditing ? 'cursor-pointer' : 'cursor-default'}`}
                    disabled={!isEditing}
                  >
                    {star <= (isEditing ? editData.rating : book.rating) ? (
                      <StarSolidIcon className="h-6 w-6 text-yellow-400" />
                    ) : (
                      <StarIcon className="h-6 w-6 text-gray-300 dark:text-gray-600" />
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Avis */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Avis</h3>
              {isEditing ? (
                <textarea
                  value={editData.review}
                  onChange={(e) => setEditData(prev => ({ ...prev, review: e.target.value }))}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-booktime-500 transition-colors"
                  placeholder="Qu'avez-vous pensé de ce livre ?"
                />
              ) : (
                <p className="text-gray-600 dark:text-gray-400">
                  {book.review || 'Aucun avis pour le moment.'}
                </p>
              )}
            </div>

            {/* Description — depuis le livre ou depuis OL enrichi */}
            {(book.description || olDetails?.description) ? (
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Description</h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">
                  {book.description || olDetails?.description}
                </p>
              </div>
            ) : olLoading ? (
              <div className="flex items-center gap-2 text-sm text-gray-400 py-2">
                <div className="h-4 w-4 border-2 border-gray-300 border-t-blue-500 rounded-full animate-spin" />
                Chargement du résumé…
              </div>
            ) : null}

            {/* Sujets / Genres — depuis OL enrichi */}
            {(olDetails?.subjects?.length > 0 || book.subjects?.length > 0) && (
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Genres & Sujets</h3>
                <div className="flex flex-wrap gap-1">
                  {(olDetails?.subjects || book.subjects || []).slice(0, 12).map((s, i) => (
                    <span key={i} className="px-2 py-0.5 text-xs bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 rounded-full border border-blue-100 dark:border-blue-800">
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Lien Open Library */}
            {book.ol_key && (
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
                <div>
                  <h4 className="font-medium text-gray-700 dark:text-gray-300">Date d'ajout</h4>
                  <p className="text-gray-600 dark:text-gray-400">
                    {new Date(book.date_added).toLocaleDateString('fr-FR')}
                  </p>
                </div>
                {book.isbn && (
                  <div>
                    <h4 className="font-medium text-gray-700 dark:text-gray-300">ISBN</h4>
                    <p className="text-gray-600 dark:text-gray-400">{book.isbn}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
        )} {/* Fin onglet Détails */}

        {/* Boutons d'action */}
        {isEditing && (
          <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setIsEditing(false)}
              className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
            >
              Annuler
            </button>
            <button
              onClick={handleSave}
              disabled={isLoading}
              className={`btn-ripple px-4 py-2 text-sm font-semibold text-white bg-booktime-600 border border-transparent rounded-lg hover:bg-booktime-700 disabled:opacity-50 flex items-center gap-2 min-w-[120px] justify-center ${bouncing === 'save' ? 'btn-bounce' : ''}`}
            >
              {isLoading ? (
                <>
                  <span className="btn-spinner" />
                  <span>Sauvegarde…</span>
                </>
              ) : (
                <>
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                  <span>Sauvegarder</span>
                </>
              )}
            </button>
          </div>
        )}
        </div>
      </div>
    </div>
  );
};

export default BookDetailModal;
