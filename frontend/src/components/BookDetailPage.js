import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { 
  ArrowLeftIcon, 
  StarIcon,
  BookOpenIcon,
  CalendarIcon,
  UserIcon,
  BuildingLibraryIcon,
  IdentificationIcon,
  DocumentTextIcon,
  TagIcon,
  GlobeAltIcon,
  PhotoIcon
} from '@heroicons/react/24/outline';
import { StarIcon as StarIconSolid } from '@heroicons/react/24/solid';

const BookDetailPage = () => {
  const { bookId } = useParams();
  const navigate = useNavigate();
  const [book, setBook] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [editData, setEditData] = useState({});

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    loadBookDetails();
  }, [bookId]);

  const loadBookDetails = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`${backendUrl}/api/books/${bookId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Livre non trouvé');
      }

      const data = await response.json();
      setBook(data);
      setEditData({
        status: data.status,
        rating: data.rating || '',
        review: data.review || '',
        pages_read: data.pages_read || 0,
        reading_start_date: data.reading_start_date || '',
        reading_end_date: data.reading_end_date || ''
      });
    } catch (error) {
      console.error('Erreur lors du chargement du livre:', error);
      toast.error('Erreur lors du chargement du livre');
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  const updateBook = async (updates) => {
    try {
      setUpdating(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`${backendUrl}/api/books/${bookId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updates)
      });

      if (!response.ok) {
        throw new Error('Erreur lors de la mise à jour');
      }

      const updatedBook = await response.json();
      setBook(updatedBook);
      toast.success('Livre mis à jour !');
    } catch (error) {
      console.error('Erreur lors de la mise à jour:', error);
      toast.error('Erreur lors de la mise à jour');
    } finally {
      setUpdating(false);
    }
  };

  const handleStatusChange = async (newStatus) => {
    const updates = { status: newStatus };
    
    // Ajouter automatiquement les dates
    if (newStatus === 'reading' && !book.reading_start_date) {
      updates.reading_start_date = new Date().toISOString().split('T')[0];
    } else if (newStatus === 'completed') {
      updates.reading_end_date = new Date().toISOString().split('T')[0];
    }
    
    await updateBook(updates);
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    await updateBook(editData);
    setEditMode(false);
  };

  const handleAuthorClick = () => {
    navigate(`/auteur/${encodeURIComponent(book.author)}`);
  };

  const handleDeleteBook = async () => {
    if (!window.confirm('Êtes-vous sûr de vouloir supprimer ce livre ?')) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${backendUrl}/api/books/${bookId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error('Erreur lors de la suppression');
      }

      toast.success('Livre supprimé !');
      navigate('/');
    } catch (error) {
      console.error('Erreur lors de la suppression:', error);
      toast.error('Erreur lors de la suppression');
    }
  };

  const renderStars = (rating, onRatingChange = null) => {
    return (
      <div className="flex items-center space-x-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            onClick={() => onRatingChange && onRatingChange(star)}
            className={`${onRatingChange ? 'cursor-pointer hover:scale-110' : 'cursor-default'} transition-all`}
            disabled={!onRatingChange}
          >
            {star <= rating ? (
              <StarIconSolid className="h-5 w-5 text-yellow-400" />
            ) : (
              <StarIcon className="h-5 w-5 text-gray-300 dark:text-gray-600" />
            )}
          </button>
        ))}
        <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">
          {rating ? `${rating}/5` : 'Non noté'}
        </span>
      </div>
    );
  };

  const getStatusInfo = (status) => {
    switch (status) {
      case 'to_read':
        return { label: 'À lire', color: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300', icon: '📚' };
      case 'reading':
        return { label: 'En cours', color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300', icon: '📖' };
      case 'completed':
        return { label: 'Terminé', color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300', icon: '✅' };
      default:
        return { label: 'Inconnu', color: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300', icon: '❓' };
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">Chargement...</p>
        </div>
      </div>
    );
  }

  if (!book) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <span className="text-6xl mb-4 block">📚</span>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Livre non trouvé</h1>
          <button
            onClick={() => navigate('/')}
            className="text-blue-600 dark:text-blue-400 hover:underline"
          >
            Retour à la bibliothèque
          </button>
        </div>
      </div>
    );
  }

  const statusInfo = getStatusInfo(book.status);
  const enrichedData = book.enriched_data || {};

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-4">
            <button
              onClick={() => navigate('/')}
              className="flex items-center space-x-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              <ArrowLeftIcon className="h-5 w-5" />
              <span>Retour à la bibliothèque</span>
            </button>
            
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setEditMode(!editMode)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                {editMode ? 'Annuler' : 'Modifier'}
              </button>
              <button
                onClick={handleDeleteBook}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Supprimer
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Colonne de gauche - Couverture et actions */}
          <div className="lg:col-span-1">
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 sticky top-8">
              {/* Couverture */}
              <div className="aspect-[2/3] bg-gray-100 dark:bg-gray-700 rounded-xl overflow-hidden mb-6 shadow-inner">
                {book.cover_url || enrichedData.cover_url_large ? (
                  <img
                    src={enrichedData.cover_url_large || book.cover_url}
                    alt={book.title}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <PhotoIcon className="h-16 w-16 text-gray-400 dark:text-gray-500" />
                  </div>
                )}
              </div>

              {/* Statut et actions rapides */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Statut :</span>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusInfo.color}`}>
                    {statusInfo.icon} {statusInfo.label}
                  </span>
                </div>

                {/* Boutons de changement de statut */}
                <div className="grid grid-cols-3 gap-2">
                  <button
                    onClick={() => handleStatusChange('to_read')}
                    disabled={updating || book.status === 'to_read'}
                    className={`px-3 py-2 text-xs rounded-lg transition-colors ${
                      book.status === 'to_read'
                        ? 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-400'
                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
                    }`}
                  >
                    📚 À lire
                  </button>
                  <button
                    onClick={() => handleStatusChange('reading')}
                    disabled={updating || book.status === 'reading'}
                    className={`px-3 py-2 text-xs rounded-lg transition-colors ${
                      book.status === 'reading'
                        ? 'bg-blue-200 text-blue-700 dark:bg-blue-800 dark:text-blue-300'
                        : 'bg-blue-100 text-blue-700 hover:bg-blue-200 dark:bg-blue-900 dark:text-blue-300 dark:hover:bg-blue-800'
                    }`}
                  >
                    📖 En cours
                  </button>
                  <button
                    onClick={() => handleStatusChange('completed')}
                    disabled={updating || book.status === 'completed'}
                    className={`px-3 py-2 text-xs rounded-lg transition-colors ${
                      book.status === 'completed'
                        ? 'bg-green-200 text-green-700 dark:bg-green-800 dark:text-green-300'
                        : 'bg-green-100 text-green-700 hover:bg-green-200 dark:bg-green-900 dark:text-green-300 dark:hover:bg-green-800'
                    }`}
                  >
                    ✅ Terminé
                  </button>
                </div>

                {/* Note */}
                <div>
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 block">Note :</span>
                  {editMode ? (
                    <div className="flex items-center space-x-1">
                      {renderStars(editData.rating, (rating) => setEditData({...editData, rating}))}
                    </div>
                  ) : (
                    renderStars(book.rating)
                  )}
                </div>

                {/* Progression de lecture */}
                {book.pages && (
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Progression :</span>
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {editMode ? editData.pages_read : book.pages_read || 0} / {book.pages} pages
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ 
                          width: `${Math.min(100, ((editMode ? editData.pages_read : book.pages_read || 0) / book.pages) * 100)}%` 
                        }}
                      ></div>
                    </div>
                    {editMode && (
                      <input
                        type="number"
                        value={editData.pages_read}
                        onChange={(e) => setEditData({...editData, pages_read: parseInt(e.target.value) || 0})}
                        max={book.pages}
                        min="0"
                        className="mt-2 w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        placeholder="Pages lues"
                      />
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Colonne de droite - Informations détaillées */}
          <div className="lg:col-span-2 space-y-6">
            {/* Informations principales */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">{book.title}</h1>
              <button
                onClick={handleAuthorClick}
                className="text-xl text-blue-600 dark:text-blue-400 hover:underline mb-4 flex items-center space-x-2"
              >
                <UserIcon className="h-5 w-5" />
                <span>{book.author}</span>
              </button>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                {book.category && (
                  <div className="flex items-center space-x-2">
                    <TagIcon className="h-4 w-4 text-gray-400" />
                    <span className="text-gray-600 dark:text-gray-400">Catégorie :</span>
                    <span className="font-medium text-gray-900 dark:text-white capitalize">{book.category}</span>
                  </div>
                )}
                
                {(book.publication_year || enrichedData.first_publish_year) && (
                  <div className="flex items-center space-x-2">
                    <CalendarIcon className="h-4 w-4 text-gray-400" />
                    <span className="text-gray-600 dark:text-gray-400">Année :</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {book.publication_year || enrichedData.first_publish_year}
                    </span>
                  </div>
                )}

                {(book.publisher || enrichedData.publishers?.length > 0) && (
                  <div className="flex items-center space-x-2">
                    <BuildingLibraryIcon className="h-4 w-4 text-gray-400" />
                    <span className="text-gray-600 dark:text-gray-400">Éditeur :</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {book.publisher || enrichedData.publishers?.slice(0, 2).join(', ')}
                    </span>
                  </div>
                )}

                {book.isbn && (
                  <div className="flex items-center space-x-2">
                    <IdentificationIcon className="h-4 w-4 text-gray-400" />
                    <span className="text-gray-600 dark:text-gray-400">ISBN :</span>
                    <span className="font-medium text-gray-900 dark:text-white">{book.isbn}</span>
                  </div>
                )}

                {book.pages && (
                  <div className="flex items-center space-x-2">
                    <BookOpenIcon className="h-4 w-4 text-gray-400" />
                    <span className="text-gray-600 dark:text-gray-400">Pages :</span>
                    <span className="font-medium text-gray-900 dark:text-white">{book.pages}</span>
                  </div>
                )}

                {book.saga && (
                  <div className="flex items-center space-x-2">
                    <DocumentTextIcon className="h-4 w-4 text-gray-400" />
                    <span className="text-gray-600 dark:text-gray-400">Saga :</span>
                    <span className="font-medium text-gray-900 dark:text-white">{book.saga}</span>
                  </div>
                )}
              </div>

              {/* Liens externes */}
              {enrichedData.openlibrary_url && (
                <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <a
                    href={enrichedData.openlibrary_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center space-x-2 text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    <GlobeAltIcon className="h-4 w-4" />
                    <span>Voir sur OpenLibrary</span>
                  </a>
                </div>
              )}
            </div>

            {/* Description */}
            {(book.description || enrichedData.description) && (
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Résumé</h2>
                <p className="text-gray-700 dark:text-gray-300 leading-relaxed">
                  {enrichedData.description || book.description}
                </p>
              </div>
            )}

            {/* Sujets/Genres */}
            {(enrichedData.subjects?.length > 0 || book.genre?.length > 0) && (
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Genres et sujets</h2>
                <div className="flex flex-wrap gap-2">
                  {(enrichedData.subjects || book.genre || []).slice(0, 10).map((subject, index) => (
                    <span
                      key={index}
                      className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 rounded-full text-sm"
                    >
                      {subject}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Critique personnelle */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Ma critique</h2>
              {editMode ? (
                <form onSubmit={handleEditSubmit} className="space-y-4">
                  <textarea
                    value={editData.review}
                    onChange={(e) => setEditData({...editData, review: e.target.value})}
                    className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                    rows="4"
                    placeholder="Écrivez votre critique..."
                  />
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Date de début de lecture
                      </label>
                      <input
                        type="date"
                        value={editData.reading_start_date}
                        onChange={(e) => setEditData({...editData, reading_start_date: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                        Date de fin de lecture
                      </label>
                      <input
                        type="date"
                        value={editData.reading_end_date}
                        onChange={(e) => setEditData({...editData, reading_end_date: e.target.value})}
                        className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                      />
                    </div>
                  </div>

                  <div className="flex justify-end space-x-3">
                    <button
                      type="button"
                      onClick={() => setEditMode(false)}
                      className="px-4 py-2 text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                    >
                      Annuler
                    </button>
                    <button
                      type="submit"
                      disabled={updating}
                      className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                    >
                      {updating ? 'Sauvegarde...' : 'Sauvegarder'}
                    </button>
                  </div>
                </form>
              ) : (
                <div className="space-y-4">
                  {book.review ? (
                    <p className="text-gray-700 dark:text-gray-300 leading-relaxed">{book.review}</p>
                  ) : (
                    <p className="text-gray-500 dark:text-gray-400 italic">Aucune critique écrite pour ce livre.</p>
                  )}
                  
                  {(book.reading_start_date || book.reading_end_date) && (
                    <div className="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
                      {book.reading_start_date && (
                        <span>📅 Commencé le {new Date(book.reading_start_date).toLocaleDateString('fr-FR')}</span>
                      )}
                      {book.reading_end_date && (
                        <span>🏁 Terminé le {new Date(book.reading_end_date).toLocaleDateString('fr-FR')}</span>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Informations d'éditions (si disponibles) */}
            {enrichedData.editions_info?.length > 0 && (
              <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">Éditions disponibles</h2>
                <div className="space-y-3">
                  {enrichedData.editions_info.slice(0, 3).map((edition, index) => (
                    <div key={index} className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <h3 className="font-medium text-gray-900 dark:text-white">{edition.title}</h3>
                      <div className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                        {edition.publish_date && <span>📅 {edition.publish_date}</span>}
                        {edition.publishers?.length > 0 && (
                          <span className="ml-4">🏢 {edition.publishers.slice(0, 2).join(', ')}</span>
                        )}
                        {edition.number_of_pages && (
                          <span className="ml-4">📄 {edition.number_of_pages} pages</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default BookDetailPage;