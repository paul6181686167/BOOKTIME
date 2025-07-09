// Phase 2.2 - Composant de pagination pour BOOKTIME
import React from 'react';
import { 
  ChevronLeftIcon, 
  ChevronRightIcon, 
  ChevronDoubleLeftIcon, 
  ChevronDoubleRightIcon 
} from '@heroicons/react/24/outline';

const Pagination = ({ 
  currentPage, 
  totalPages, 
  totalItems, 
  itemsPerPage, 
  hasNext, 
  hasPrevious, 
  onPageChange, 
  onItemsPerPageChange, 
  loading = false,
  showItemsPerPage = true,
  showTotalInfo = true,
  className = ""
}) => {
  // Options pour le nombre d'éléments par page
  const itemsPerPageOptions = [10, 20, 50, 100];
  
  // Calculer les numéros de pages à afficher
  const getPageNumbers = () => {
    const pages = [];
    const maxVisiblePages = 5;
    
    if (totalPages <= maxVisiblePages) {
      // Toutes les pages sont visibles
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Logique pour les pages avec ellipses
      const startPage = Math.max(1, currentPage - 2);
      const endPage = Math.min(totalPages, currentPage + 2);
      
      // Toujours afficher la première page
      if (startPage > 1) {
        pages.push(1);
        if (startPage > 2) {
          pages.push('...');
        }
      }
      
      // Pages autour de la page courante
      for (let i = startPage; i <= endPage; i++) {
        pages.push(i);
      }
      
      // Toujours afficher la dernière page
      if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
          pages.push('...');
        }
        pages.push(totalPages);
      }
    }
    
    return pages;
  };

  const pageNumbers = getPageNumbers();

  return (
    <div className={`flex flex-col sm:flex-row justify-between items-center gap-4 ${className}`}>
      {/* Informations sur les éléments */}
      {showTotalInfo && (
        <div className="text-sm text-gray-600 dark:text-gray-400">
          Affichage {((currentPage - 1) * itemsPerPage) + 1} à {Math.min(currentPage * itemsPerPage, totalItems)} sur {totalItems} éléments
        </div>
      )}
      
      {/* Contrôles de pagination */}
      <div className="flex items-center gap-2">
        {/* Première page */}
        <button
          onClick={() => onPageChange(1)}
          disabled={!hasPrevious || loading}
          className="p-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
          title="Première page"
        >
          <ChevronDoubleLeftIcon className="w-4 h-4" />
        </button>
        
        {/* Page précédente */}
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={!hasPrevious || loading}
          className="p-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
          title="Page précédente"
        >
          <ChevronLeftIcon className="w-4 h-4" />
        </button>
        
        {/* Numéros de pages */}
        <div className="flex gap-1">
          {pageNumbers.map((page, index) => (
            <button
              key={index}
              onClick={() => typeof page === 'number' ? onPageChange(page) : null}
              disabled={loading || page === '...'}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-200 ${
                page === currentPage
                  ? 'bg-green-600 text-white'
                  : page === '...'
                  ? 'text-gray-400 cursor-default'
                  : 'border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
              }`}
            >
              {page}
            </button>
          ))}
        </div>
        
        {/* Page suivante */}
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={!hasNext || loading}
          className="p-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
          title="Page suivante"
        >
          <ChevronRightIcon className="w-4 h-4" />
        </button>
        
        {/* Dernière page */}
        <button
          onClick={() => onPageChange(totalPages)}
          disabled={!hasNext || loading}
          className="p-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
          title="Dernière page"
        >
          <ChevronDoubleRightIcon className="w-4 h-4" />
        </button>
      </div>
      
      {/* Sélecteur d'éléments par page */}
      {showItemsPerPage && (
        <div className="flex items-center gap-2 text-sm">
          <label htmlFor="itemsPerPage" className="text-gray-600 dark:text-gray-400">
            Éléments par page:
          </label>
          <select
            id="itemsPerPage"
            value={itemsPerPage}
            onChange={(e) => onItemsPerPageChange(Number(e.target.value))}
            disabled={loading}
            className="border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-1 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50"
          >
            {itemsPerPageOptions.map(option => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
};

export default Pagination;