import { useState, useEffect } from 'react';
import { bookService } from '../services/bookService';

const useStats = () => {
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await bookService.getStats();
      setStats(response || {});
    } catch (err) {
      console.error('Error loading stats:', err);
      setError('Erreur lors du chargement des statistiques');
      setStats({});
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  return {
    stats,
    loading,
    error,
    loadStats,
    refreshStats: loadStats
  };
};

export default useStats;