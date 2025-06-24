import React, { useState } from 'react';
import { XMarkIcon, StarIcon, TrashIcon, PencilIcon } from '@heroicons/react/24/outline';
import { StarIcon as StarSolidIcon } from '@heroicons/react/24/solid';
import toast from 'react-hot-toast';

const BookDetailModal = ({ book, onClose, onUpdate, onDelete }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({
    status: book.status,
    current_page: book.current_page || 0,
    rating: book.rating || 0,
    review: book.review || '',
  });
  const [isLoading, setIsLoading] = useState(false);

  const statusOptions = [
    { value: 'to_read', label: 'À lire', color: 'bg-gray-100 text-gray-800' },
    { value: 'reading', label: 'En cours', color: 'bg-blue-100 text-blue-800' },
    { value: 'completed', label: 'Terminé', color: 'bg-green-100 text-green-800' },
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

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content max-w-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between mb-6">
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">{book.title}</h2>
            <p className="text-lg text-gray-600 mb-4">par {book.author}</p>
            
            {/* Catégorie et statut */}
            <div className="flex items-center space-x-3">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-booktime-100 text-booktime-800">
                {book.category === 'roman' && '📚'} 
                {book.category === 'bd' && '🎨'} 
                {book.category === 'manga' && '🇯🇵'} 
                {book.category.charAt(0).toUpperCase() + book.category.slice(1)}
              </span>
              <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getCurrentStatus().color}`}>
                {getCurrentStatus().label}
              </span>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setIsEditing(!isEditing)}
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <PencilIcon className="h-5 w-5" />
            </button>
            <button
              onClick={handleDelete}
              className="p-2 text-red-400 hover:text-red-600 transition-colors"
            >
              <TrashIcon className="h-5 w-5" />
            </button>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Image de couverture */}
          <div className="md:col-span-1">
            <div className="aspect-[2/3] bg-gray-100 rounded-lg overflow-hidden">
              {book.cover_url ? (
                <img 
                  src={book.cover_url} 
                  alt={book.title}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200">
                  <div className="text-center p-4">
                    <div className="text-6xl mb-2">
                      {book.category === 'roman' && '📚'}
                      {book.category === 'bd' && '🎨'}
                      {book.category === 'manga' && '🇯🇵'}
                    </div>
                    <p className="text-sm text-gray-500 font-medium">Pas de couverture</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Détails du livre */}
          <div className="md:col-span-2 space-y-6">
            {/* Statut */}
            {isEditing ? (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Statut
                </label>
                <select
                  value={editData.status}
                  onChange={(e) => setEditData(prev => ({ ...prev, status: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-booktime-500"
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
                <h3 className="text-sm font-medium text-gray-700 mb-1">Statut</h3>
                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getCurrentStatus().color}`}>
                  {getCurrentStatus().label}
                </span>
              </div>
            )}

            {/* Progression */}
            {book.total_pages && (
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Progression</h3>
                {isEditing ? (
                  <div className="space-y-2">
                    <input
                      type="number"
                      value={editData.current_page}
                      onChange={(e) => setEditData(prev => ({ ...prev, current_page: e.target.value }))}
                      min="0"
                      max={book.total_pages}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-booktime-500"
                    />
                    <div className="flex justify-between text-sm text-gray-600">
                      <span>{editData.current_page} pages lues</span>
                      <span>{book.total_pages} pages total</span>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm text-gray-600">
                      <span>{book.current_page} pages lues</span>
                      <span>{book.total_pages} pages total</span>
                    </div>
                    <div className="progress-bar">
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
              <h3 className="text-sm font-medium text-gray-700 mb-2">Note</h3>
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
                      <StarIcon className="h-6 w-6 text-gray-300" />
                    )}
                  </button>
                ))}
              </div>
            </div>

            {/* Avis */}
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">Avis</h3>
              {isEditing ? (
                <textarea
                  value={editData.review}
                  onChange={(e) => setEditData(prev => ({ ...prev, review: e.target.value }))}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-booktime-500"
                  placeholder="Qu'avez-vous pensé de ce livre ?"
                />
              ) : (
                <p className="text-gray-600">
                  {book.review || 'Aucun avis pour le moment.'}
                </p>
              )}
            </div>

            {/* Description */}
            {book.description && (
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Description</h3>
                <p className="text-gray-600 text-sm leading-relaxed">
                  {book.description}
                </p>
              </div>
            )}

            {/* Informations supplémentaires */}
            <div className="border-t pt-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <h4 className="font-medium text-gray-700">Date d'ajout</h4>
                  <p className="text-gray-600">
                    {new Date(book.date_added).toLocaleDateString('fr-FR')}
                  </p>
                </div>
                {book.isbn && (
                  <div>
                    <h4 className="font-medium text-gray-700">ISBN</h4>
                    <p className="text-gray-600">{book.isbn}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Boutons d'action */}
        {isEditing && (
          <div className="flex justify-end space-x-3 pt-6 border-t">
            <button
              onClick={() => setIsEditing(false)}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Annuler
            </button>
            <button
              onClick={handleSave}
              disabled={isLoading}
              className="px-4 py-2 text-sm font-medium text-white bg-booktime-600 border border-transparent rounded-md hover:bg-booktime-700 disabled:opacity-50"
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