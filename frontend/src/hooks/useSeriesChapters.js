/**
 * Hook personnalisé pour la gestion des chapitres de séries
 * ======================================================
 * 
 * Fonctionnalités :
 * - Récupération des chapitres d'une série
 * - Actualisation forcée des données
 * - Cache et gestion d'état optimisée
 * - Gestion d'erreurs robuste
 */

import { useState, useEffect, useCallback } from 'react';
import { API_BASE_URL } from '../config/environment';

export const useSeriesChapters = (seriesName) => {
  const [chaptersData, setChaptersData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  // Cache simple en localStorage
  const getCacheKey = useCallback((name) => `chapters_${name.toLowerCase().replace(/\s+/g, '_')}`, []);
  
  const getFromCache = useCallback((name) => {
    try {
      const cached = localStorage.getItem(getCacheKey(name));
      if (cached) {
        const parsed = JSON.parse(cached);
        const now = Date.now();
        const cacheAge = now - parsed.timestamp;
        
        // Cache valide pendant 1 heure
        if (cacheAge < 3600000) { // 1 heure en millisecondes
          return parsed.data;
        }
      }
    } catch (e) {
      console.warn('Erreur lecture cache chapters:', e);
    }
    return null;
  }, [getCacheKey]);

  const saveToCache = useCallback((name, data) => {
    try {
      const cacheData = {
        data,
        timestamp: Date.now()
      };
      localStorage.setItem(getCacheKey(name), JSON.stringify(cacheData));
    } catch (e) {
      console.warn('Erreur sauvegarde cache chapters:', e);
    }
  }, [getCacheKey]);

  const fetchChapters = useCallback(async (forceFresh = false) => {
    if (!seriesName) {
      setChaptersData(null);
      return;
    }

    // Vérifier cache si pas de refresh forcé
    if (!forceFresh) {
      const cachedData = getFromCache(seriesName);
      if (cachedData) {
        setChaptersData(cachedData);
        setError(null);
        setLastUpdated(new Date());
        return;
      }
    }

    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const user = localStorage.getItem('user');
      
      console.log('🔍 DEBUG useSeriesChapters:', {
        seriesName,
        hasToken: !!token,
        hasUser: !!user,
        tokenLength: token ? token.length : 0,
        apiUrl: `${API_BASE_URL}/api/chapters/series/${encodeURIComponent(seriesName)}`
      });
      
      if (!token) {
        throw new Error('Token d\'authentification requis - Veuillez vous reconnecter');
      }

      const url = `${API_BASE_URL}/api/chapters/series/${encodeURIComponent(seriesName)}`;
      const queryParams = forceFresh ? '?force_refresh=true' : '';

      console.log('🌐 Requête API Chapters:', `${url}${queryParams}`);

      const response = await fetch(`${url}${queryParams}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      console.log('📡 Réponse API:', {
        status: response.status,
        statusText: response.statusText,
        ok: response.ok,
        headers: response.headers
      });

      if (!response.ok) {
        if (response.status === 401) {
          console.error('❌ Token expiré ou invalide - Nettoyage localStorage');
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          throw new Error('Session expirée, veuillez vous reconnecter');
        } else if (response.status === 404) {
          const errorText = await response.text();
          console.error('❌ 404 Error Details:', errorText);
          throw new Error('Aucune donnée chapitre disponible pour cette série');
        } else {
          const errorData = await response.text();
          console.error('❌ Erreur serveur:', errorData);
          throw new Error(`Erreur serveur (${response.status}): ${errorData}`);
        }
      }

      const data = await response.json();
      console.log('✅ Données reçues:', {
        success: data.success,
        hasData: !!data.data,
        totalChapters: data.data?.total_chapters_released,
        totalVolumes: data.data?.total_volumes_released,
        chaptersCount: data.data?.current_chapters?.length,
        volumesCount: data.data?.volumes?.length
      });
      
      // Validation des données reçues
      if (data && typeof data === 'object') {
        setChaptersData(data);
        setError(null);
        setLastUpdated(new Date());
        
        // Sauvegarder en cache
        saveToCache(seriesName, data);
      } else {
        throw new Error('Format de données invalide reçu du serveur');
      }

    } catch (err) {
      console.error('❌ Erreur récupération chapitres:', err);
      setError(err.message);
      setChaptersData(null);
    } finally {
      setLoading(false);
    }
  }, [seriesName, getFromCache, saveToCache]);

  const refreshChapters = useCallback(async () => {
    if (!seriesName) return;

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Token d\'authentification requis');
      }

      // Déclencher actualisation côté serveur
      await fetch(`${API_BASE_URL}/api/chapters/series/${encodeURIComponent(seriesName)}/refresh`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      // Puis récupérer les données fraîches
      await fetchChapters(true);

    } catch (err) {
      console.error('Erreur actualisation chapitres:', err);
      setError(err.message);
    }
  }, [seriesName, fetchChapters]);

  // Charger données au montage ou changement de série
  useEffect(() => {
    fetchChapters();
  }, [fetchChapters]);

  // Nettoyage du cache si série change
  useEffect(() => {
    return () => {
      // Optionnel: nettoyage si nécessaire
    };
  }, [seriesName]);

  return {
    chaptersData,
    loading,
    error,
    lastUpdated,
    fetchChapters,
    refreshChapters,
    
    // Helpers pour les composants
    hasChapters: chaptersData && chaptersData.current_chapters && chaptersData.current_chapters.length > 0,
    hasVolumes: chaptersData && chaptersData.volumes && chaptersData.volumes.length > 0,
    hasPredictions: chaptersData && chaptersData.predictions && Object.keys(chaptersData.predictions).length > 0,
    
    // Métriques rapides
    totalChapters: chaptersData?.total_chapters_released || 0,
    latestChapter: chaptersData?.current_chapters?.[chaptersData.current_chapters.length - 1] || null,
    nextPrediction: chaptersData?.predictions?.next_chapter || null,
  };
};

export default useSeriesChapters;