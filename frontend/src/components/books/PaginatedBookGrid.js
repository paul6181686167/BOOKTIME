// Phase 2.2 - Grille de livres avec pagination pour BOOKTIME
import React, { useState, useEffect, useCallback } from 'react';
import BookGrid from './BookGrid';
import Pagination from '../common/Pagination';
import usePagination from '../../hooks/usePagination';
import { paginationService } from '../../services/paginationService';

const PaginatedBookGrid = ({
  category,
  status,
  author,
  saga,
  viewMode = 'books', // 'books' ou 'series'
  onItemClick,
  excludeSeries = false,
  className = "",
  showFilters = true,
  initialItemsPerPage = 20
}) => {
  const [books, setBooks] = useState([]);
  const [filters, setFilters] = useState({
    category,
    status,
    author,
    saga
  });

  // Hook de pagination
  const pagination = usePagination(1, initialItemsPerPage);

  // Charger les livres avec pagination
  const loadBooks = useCallback(async () => {
    try {
      const params = {
        limit: pagination.itemsPerPage,
        offset: pagination.offset,
        category: filters.category,
        status: filters.status,
        author: filters.author,
        saga: filters.saga,
        sort_by: 'date_added',
        sort_order: 'desc',
        exclude_series: excludeSeries
      };

      let response;
      if (viewMode === 'series') {
        response = await paginationService.getPaginatedSeries(params);
      } else {
        response = await paginationService.getPaginatedBooks(params);
      }

      if (response && response.items) {
        setBooks(response.items);
        pagination.setTotalItems(response.total);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des livres:', error);
      pagination.setError(error.message);
    }
  }, [
    pagination.itemsPerPage,
    pagination.offset,
    filters,
    viewMode,
    excludeSeries
  ]);

  // Charger les livres à chaque changement de pagination ou de filtres
  useEffect(() => {
    loadBooks();
  }, [loadBooks]);

  // Mettre à jour les filtres
  const updateFilters = useCallback((newFilters) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
    pagination.resetPagination();
  }, [pagination]);

  // Gestionnaire de changement de page
  const handlePageChange = useCallback((newPage) => {
    pagination.changePage(newPage);
  }, [pagination]);

  // Gestionnaire de changement d'éléments par page
  const handleItemsPerPageChange = useCallback((newItemsPerPage) => {
    pagination.changeItemsPerPage(newItemsPerPage);
  }, [pagination]);

  // Options de filtre
  const statusOptions = [
    { value: '', label: 'Tous les statuts' },
    { value: 'to_read', label: 'À lire' },
    { value: 'reading', label: 'En cours' },
    { value: 'completed', label: 'Terminé' }
  ];

  const categoryOptions = [
    { value: '', label: 'Toutes les catégories' },
    { value: 'roman', label: 'Roman' },
    { value: 'bd', label: 'BD' },
    { value: 'manga', label: 'Manga' }
  ];

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Filtres */}
      {showFilters && (
        <div className="bg-white dark:bg-gray-800 p-4 rounded-lg shadow-sm">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Filtres
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Filtre par catégorie */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Catégorie
              </label>
              <select
                value={filters.category || ''}
                onChange={(e) => updateFilters({ category: e.target.value || undefined })}
                className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                {categoryOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Filtre par statut */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Statut
              </label>
              <select
                value={filters.status || ''}
                onChange={(e) => updateFilters({ status: e.target.value || undefined })}
                className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-green-500"
              >
                {statusOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Filtre par auteur */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Auteur
              </label>
              <input
                type="text"
                value={filters.author || ''}
                onChange={(e) => updateFilters({ author: e.target.value || undefined })}
                placeholder="Filtrer par auteur..."
                className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-green-500"
              />
            </div>

            {/* Filtre par saga */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Saga
              </label>
              <input
                type="text"
                value={filters.saga || ''}
                onChange={(e) => updateFilters({ saga: e.target.value || undefined })}
                placeholder="Filtrer par saga..."
                className="w-full border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-green-500"
              />
            </div>
          </div>
        </div>
      )}

      {/* Grille de livres */}
      <BookGrid
        books={books}
        loading={pagination.loading}
        onItemClick={onItemClick}
        showEmptyState={true}
        className="min-h-[400px]"
      />

      {/* Pagination */}
      {pagination.totalPages > 1 && (
        <Pagination
          currentPage={pagination.currentPage}
          totalPages={pagination.totalPages}
          totalItems={pagination.totalItems}
          itemsPerPage={pagination.itemsPerPage}
          hasNext={pagination.hasNext}
          hasPrevious={pagination.hasPrevious}
          onPageChange={handlePageChange}
          onItemsPerPageChange={handleItemsPerPageChange}
          loading={pagination.loading}
          className="mt-6"
        />
      )}

      {/* Gestion des erreurs */}
      {pagination.error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-800 dark:text-red-200">
                {pagination.error}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PaginatedBookGrid;