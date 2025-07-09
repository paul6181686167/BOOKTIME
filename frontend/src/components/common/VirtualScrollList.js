// Phase 2.3 - Composant Virtual Scrolling pour grandes listes
import React, { useState, useEffect, useRef, useMemo } from 'react';

/**
 * Composant de Virtual Scrolling pour optimiser l'affichage de grandes listes
 * Affiche seulement les éléments visibles dans la fenêtre de visualisation
 */
const VirtualScrollList = ({
  items = [],
  itemHeight = 100,
  containerHeight = 400,
  renderItem,
  overscan = 3,
  className = "",
  onLoadMore,
  hasMore = false,
  loading = false,
  EmptyComponent = null,
  LoadingComponent = null
}) => {
  const [scrollTop, setScrollTop] = useState(0);
  const [containerScrollHeight, setContainerScrollHeight] = useState(0);
  const scrollElementRef = useRef(null);

  // Calculer les index des éléments visibles
  const visibleRange = useMemo(() => {
    const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
    const endIndex = Math.min(
      items.length - 1,
      Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan
    );
    return { startIndex, endIndex };
  }, [scrollTop, containerHeight, itemHeight, overscan, items.length]);

  // Calculer la hauteur totale de la liste
  const totalHeight = items.length * itemHeight;

  // Calculer le décalage pour positionner correctement les éléments visibles
  const offsetY = visibleRange.startIndex * itemHeight;

  // Gérer le scroll
  const handleScroll = (e) => {
    const newScrollTop = e.target.scrollTop;
    setScrollTop(newScrollTop);
    setContainerScrollHeight(e.target.scrollHeight);

    // Charger plus d'éléments si nécessaire
    if (
      onLoadMore &&
      hasMore &&
      !loading &&
      newScrollTop + containerHeight >= e.target.scrollHeight - 100
    ) {
      onLoadMore();
    }
  };

  // Optimisation: throttle du scroll pour éviter trop de re-rendus
  useEffect(() => {
    const scrollElement = scrollElementRef.current;
    if (!scrollElement) return;

    let ticking = false;
    const handleThrottledScroll = (e) => {
      if (!ticking) {
        requestAnimationFrame(() => {
          handleScroll(e);
          ticking = false;
        });
        ticking = true;
      }
    };

    scrollElement.addEventListener('scroll', handleThrottledScroll);
    return () => scrollElement.removeEventListener('scroll', handleThrottledScroll);
  }, [onLoadMore, hasMore, loading, containerHeight]);

  // Méthode pour faire défiler vers un élément spécifique
  const scrollToItem = (index) => {
    if (scrollElementRef.current) {
      const scrollTop = index * itemHeight;
      scrollElementRef.current.scrollTop = scrollTop;
    }
  };

  // Exposer la méthode scrollToItem via useImperativeHandle si nécessaire
  useEffect(() => {
    if (scrollElementRef.current) {
      scrollElementRef.current.scrollToItem = scrollToItem;
    }
  }, []);

  // Éléments à rendre
  const visibleItems = [];
  for (let i = visibleRange.startIndex; i <= visibleRange.endIndex; i++) {
    if (i < items.length) {
      visibleItems.push({
        index: i,
        item: items[i]
      });
    }
  }

  // Affichage si la liste est vide
  if (items.length === 0 && !loading) {
    return (
      <div className={`${className} flex items-center justify-center`} style={{ height: containerHeight }}>
        {EmptyComponent || (
          <div className="text-center text-gray-500 dark:text-gray-400">
            <p>Aucun élément à afficher</p>
          </div>
        )}
      </div>
    );
  }

  return (
    <div
      ref={scrollElementRef}
      className={`${className} overflow-auto`}
      style={{ height: containerHeight }}
      onScroll={handleScroll}
    >
      {/* Conteneur pour maintenir la hauteur totale */}
      <div style={{ height: totalHeight, position: 'relative' }}>
        {/* Conteneur pour les éléments visibles */}
        <div
          style={{
            transform: `translateY(${offsetY}px)`,
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
          }}
        >
          {visibleItems.map(({ index, item }) => (
            <div
              key={index}
              style={{
                height: itemHeight,
                overflow: 'hidden'
              }}
            >
              {renderItem(item, index)}
            </div>
          ))}
        </div>

        {/* Indicateur de chargement */}
        {loading && (
          <div
            style={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              height: 60,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: 'rgba(255, 255, 255, 0.9)',
              borderTop: '1px solid #e5e7eb'
            }}
          >
            {LoadingComponent || (
              <div className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-green-500"></div>
                <span className="text-sm text-gray-600">Chargement...</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default VirtualScrollList;

// Hook pour utiliser la liste virtuelle avec pagination
export const useVirtualizedList = (
  items = [],
  itemHeight = 100,
  containerHeight = 400,
  pageSize = 50
) => {
  const [visibleItems, setVisibleItems] = useState([]);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(false);

  // Simuler le chargement paginé
  const loadMore = async () => {
    if (loading || !hasMore) return;

    setLoading(true);
    // Simuler une requête API
    await new Promise(resolve => setTimeout(resolve, 500));
    
    const nextItems = items.slice(visibleItems.length, visibleItems.length + pageSize);
    setVisibleItems(prev => [...prev, ...nextItems]);
    setHasMore(visibleItems.length + nextItems.length < items.length);
    setLoading(false);
  };

  // Initialiser les premiers éléments
  useEffect(() => {
    if (items.length > 0 && visibleItems.length === 0) {
      const initialItems = items.slice(0, pageSize);
      setVisibleItems(initialItems);
      setHasMore(initialItems.length < items.length);
    }
  }, [items, pageSize, visibleItems.length]);

  return {
    visibleItems,
    hasMore,
    loading,
    loadMore
  };
};