import { useState, useCallback } from 'react';

// Hook pour le tri des sections
export default function useSectionSort() {
  const [sortConfig, setSortConfig] = useState({ field: 'date_added', order: 'desc' });
  const sortBooks = useCallback((books) => {
    const sorted = [...books].sort((a, b) => {
      let va, vb;
      if (sortConfig.field === 'title') {
        va = (a.name || a.title || '').toLowerCase();
        vb = (b.name || b.title || '').toLowerCase();
      } else if (sortConfig.field === 'author') {
        va = (a.author || '').toLowerCase();
        vb = (b.author || '').toLowerCase();
      } else {
        va = new Date(a.date_added || a.updated_at || 0);
        vb = new Date(b.date_added || b.updated_at || 0);
      }
      if (va < vb) return sortConfig.order === 'asc' ? -1 : 1;
      if (va > vb) return sortConfig.order === 'asc' ? 1 : -1;
      return 0;
    });
    return sorted;
  }, [sortConfig]);
  return { sortConfig, setSortConfig, sortBooks };
}
