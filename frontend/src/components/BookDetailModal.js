import React, { useState } from 'react';
import { XMarkIcon, StarIcon, TrashIcon, PencilIcon, LanguageIcon, SparklesIcon } from '@heroicons/react/24/outline';
import { StarIcon as StarSolidIcon } from '@heroicons/react/24/solid';
import toast from 'react-hot-toast';
import LanguageSelector from './LanguageSelector';
import { getLanguageByCode } from '../constants/languages';

// Service Open Library pour l'enrichissement
const openLibraryService = {
  async enrichBook(bookId) {
    try {
      const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
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

// Service Open Library pour l'enrichissement
const openLibraryService = {
  async enrichBook(bookId) {
    try {
      const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
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

const BookDetailModal = ({ book, onClose, onUpdate, onDelete }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({
    status: book.status,
    current_page: book.current_page || 0,
    rating: book.rating || 0,
    review: book.review || '',
    original_language: book.original_language || 'français',
    available_translations: book.available_translations || [],
    reading_language: book.reading_language || 'français',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [enriching, setEnriching] = useState(false);

  const statusOptions = [
    { value: 'to_read', label: 'À lire', color: 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300' },
    { value: 'reading', label: 'En cours', color: 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-300' },
    { value: 'completed', label: 'Terminé', color: 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-300' },
  ];

  const handleSave = async () => {
    setIsLoading(true);
    try {
      const updates = {
        ...editData,
        current_page: parseInt(editData.current_page) || 0,
      };
      
      await onUpdate(book.id, updates);
      setIsEditing(false);
      toast.success('Livre mis à jour avec succès !');
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
      <div className="modal-content max-w-4xl max-h-[90vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between mb-6">
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">{book.title}</h2>
            <p className="text-lg text-gray-600 dark:text-gray-400 mb-4">par {book.author}</p>
            
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
          
          <div className="flex items-center space-x-2">
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
            <button
              onClick={onClose}
              className="p-2 text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
        </div>

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

            {/* Description */}
            {book.description && (
              <div>
                <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Description</h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">
                  {book.description}
                </p>
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
              className="px-4 py-2 text-sm font-medium text-white bg-booktime-600 border border-transparent rounded-md hover:bg-booktime-700 disabled:opacity-50 transition-colors"
            >
              {isLoading ? 'Sauvegarde...' : 'Sauvegarder'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default BookDetailModal;