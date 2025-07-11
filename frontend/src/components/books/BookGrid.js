import React from 'react';
import BookActions from './BookActions';

// Composant pour afficher la grille des livres
const BookGrid = ({ 
  books, 
  loading, 
  onBookClick, 
  onItemClick,
  showEmptyState = true 
}) => {
  // SESSION 81.1 - DOUBLE PROTECTION : Masquage des livres individuels de série dans BookGrid
  const applySeriesBookMasking = (booksList) => {
    if (!booksList || !Array.isArray(booksList)) {
      return [];
    }
    
    console.log('🔍 [SESSION 81.1] BookGrid - Masquage des livres de série:', booksList.length, 'livres reçus');
    
    // Créer l'affichage unifié avec masquage
    const unifiedDisplay = BookActions.createUnifiedDisplay(booksList, (book) => {
      // Fonction pour déterminer le badge de catégorie
      if (book.category) {
        switch (book.category.toLowerCase()) {
          case 'roman':
            return { key: 'roman', text: 'Roman', class: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300', emoji: '📚' };
          case 'bd':
            return { key: 'bd', text: 'BD', class: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300', emoji: '🎨' };
          case 'manga':
            return { key: 'manga', text: 'Manga', class: 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-300', emoji: '🇯🇵' };
          default:
            return { key: 'roman', text: 'Roman', class: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300', emoji: '📚' };
        }
      }
      return { key: 'roman', text: 'Roman', class: 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300', emoji: '📚' };
    });
    
    // 🔍 SESSION 81.1 - PROTECTION FINALE dans BookGrid : Vérifier qu'aucun livre de série n'échappe
    const finalBooks = unifiedDisplay.filter(item => {
      if (item.isSeriesCard) {
        // Les vignettes de série sont autorisées
        return true;
      } else {
        // Pour les livres individuels, vérifier qu'ils n'appartiennent pas à une série
        const belongsToSeries = !!(item.saga && item.saga.trim());
        if (belongsToSeries) {
          console.warn(`⚠️ [SESSION 81.1] BookGrid PROTECTION FINALE: Livre "${item.title}" de la série "${item.saga}" détecté - MASQUÉ`);
          return false; // Masquer ce livre
        }
        return true; // Livre standalone autorisé
      }
    });
    
    console.log(`🎯 [SESSION 81.1] BookGrid - Résultat final: ${finalBooks.length} éléments (${finalBooks.filter(f => f.isSeriesCard).length} séries + ${finalBooks.filter(f => !f.isSeriesCard).length} livres standalone)`);
    
    return finalBooks;
  };
  
  // Appliquer le masquage des livres de série
  const displayedBooks = applySeriesBookMasking(books);

  // État de chargement
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-6 p-6">
        {Array.from({ length: 12 }).map((_, index) => (
          <div key={index} className="animate-pulse">
            <div className="bg-gray-200 dark:bg-gray-700 rounded-lg aspect-[3/4] mb-3"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
            <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-3/4"></div>
          </div>
        ))}
      </div>
    );
  }

  // État vide
  if (showEmptyState && displayedBooks.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">📚</div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Aucun livre dans votre bibliothèque
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          Commencez par rechercher des livres à ajouter à votre collection.
        </p>
      </div>
    );
  }

  // Affichage de la grille
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-6 p-6">
      {displayedBooks.map((item) => (
        <div
          key={item.id}
          className={`
            ${item.isSeriesCard ? 'col-span-1 sm:col-span-2' : 'col-span-1'} 
            group cursor-pointer transform transition-all duration-200 hover:scale-105 hover:shadow-lg
          `}
          onClick={() => onItemClick ? onItemClick(item) : onBookClick(item)}
        >
          {item.isSeriesCard ? (
            // Carte série
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden border border-gray-200 dark:border-gray-700">
              <div className="aspect-[2/1] bg-gray-100 dark:bg-gray-700 flex items-center justify-center relative overflow-hidden">
                {item.cover_url ? (
                  <>
                    <img 
                      src={item.cover_url} 
                      alt={item.name}
                      className="w-full h-full object-cover"
                    />
                    {/* Overlay pour le texte "Série" */}
                    <div className="absolute inset-0 bg-black bg-opacity-40 flex items-center justify-center">
                      <div className="text-white text-center">
                        <div className="text-4xl mb-2">📚</div>
                        <div className="text-sm font-medium bg-black bg-opacity-50 px-2 py-1 rounded">Série</div>
                      </div>
                    </div>
                  </>
                ) : (
                  // Fallback avec dégradé si pas d'image
                  <div className="w-full h-full bg-gradient-to-r from-blue-500 to-purple-600 flex items-center justify-center">
                    <div className="text-white text-center">
                      <div className="text-4xl mb-2">📚</div>
                      <div className="text-sm font-medium">Série</div>
                    </div>
                  </div>
                )}
              </div>
              <div className="p-4">
                <h3 className="font-semibold text-gray-900 dark:text-white line-clamp-2 mb-2">
                  {item.name}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                  {item.author}
                </p>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {item.completedBooks}/{item.totalBooks} tomes
                  </span>
                  <div className="w-16 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div 
                      className="bg-green-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${item.progressPercent}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>
          ) : (
            // Carte livre
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden border border-gray-200 dark:border-gray-700">
              <div className="aspect-[3/4] bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                {item.cover_url ? (
                  <img 
                    src={item.cover_url} 
                    alt={item.title}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="text-gray-400 text-4xl">📖</div>
                )}
              </div>
              <div className="p-3">
                <h3 className="font-semibold text-gray-900 dark:text-white text-sm line-clamp-2 mb-1">
                  {item.title}
                </h3>
                <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
                  {item.author}
                </p>
                <div className="flex items-center justify-between">
                  <span className={`
                    px-2 py-1 rounded-full text-xs font-medium
                    ${item.status === 'completed' ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-300' : ''}
                    ${item.status === 'reading' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300' : ''}
                    ${item.status === 'to_read' ? 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-300' : ''}
                  `}>
                    {item.status === 'completed' ? 'Terminé' : 
                     item.status === 'reading' ? 'En cours' : 'À lire'}
                  </span>
                  {item.category && (
                    <span className="text-xs">
                      {item.category === 'roman' ? '📚' : 
                       item.category === 'bd' ? '🎨' : 
                       item.category === 'manga' ? '🇯🇵' : '📚'}
                    </span>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default BookGrid;
