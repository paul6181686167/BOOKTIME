// Phase 2.2 - Hook de pagination pour BOOKTIME
import { useState, useCallback, useEffect } from 'react';

export const usePagination = (initialPage = 1, initialItemsPerPage = 20) => {
  const [currentPage, setCurrentPage] = useState(initialPage);
  const [itemsPerPage, setItemsPerPage] = useState(initialItemsPerPage);
  const [totalItems, setTotalItems] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Calculer les métadonnées de pagination
  const totalPages = Math.ceil(totalItems / itemsPerPage);
  const hasNext = currentPage < totalPages;
  const hasPrevious = currentPage > 1;
  const offset = (currentPage - 1) * itemsPerPage;

  // Changer de page
  const changePage = useCallback((newPage) => {
    if (newPage >= 1 && newPage <= totalPages && newPage !== currentPage) {
      setCurrentPage(newPage);
    }
  }, [currentPage, totalPages]);

  // Changer le nombre d'éléments par page
  const changeItemsPerPage = useCallback((newItemsPerPage) => {
    setItemsPerPage(newItemsPerPage);
    setCurrentPage(1); // Retour à la première page
  }, []);

  // Réinitialiser la pagination
  const resetPagination = useCallback(() => {
    setCurrentPage(1);
    setTotalItems(0);
    setError(null);
  }, []);

  // Fonction pour faire une requête paginée
  const fetchPaginatedData = useCallback(async (fetchFunction, ...args) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetchFunction({
        limit: itemsPerPage,
        offset: offset,
        ...args
      });
      
      // Vérifier le format de réponse
      if (response && typeof response === 'object') {
        if (response.items !== undefined && response.total !== undefined) {
          // Format PaginatedResponse
          setTotalItems(response.total);
          return response.items;
        } else if (Array.isArray(response)) {
          // Format simple array
          setTotalItems(response.length);
          return response;
        }
      }
      
      throw new Error('Format de réponse invalide');
    } catch (err) {
      console.error('Erreur lors de la récupération des données paginées:', err);
      setError(err.message || 'Erreur lors du chargement des données');
      return [];
    } finally {
      setLoading(false);
    }
  }, [itemsPerPage, offset]);

  // Effet pour réinitialiser la page si elle dépasse le total
  useEffect(() => {
    if (totalPages > 0 && currentPage > totalPages) {
      setCurrentPage(Math.max(1, totalPages));
    }
  }, [totalPages, currentPage]);

  return {
    // État de pagination
    currentPage,
    itemsPerPage,
    totalItems,
    totalPages,
    hasNext,
    hasPrevious,
    offset,
    loading,
    error,
    
    // Actions
    changePage,
    changeItemsPerPage,
    resetPagination,
    fetchPaginatedData,
    
    // Setters pour usage externe
    setTotalItems,
    setLoading,
    setError
  };
};

export default usePagination;