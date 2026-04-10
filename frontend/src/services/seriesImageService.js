import { API_BASE_URL } from '../config/environment';
/**
 * Service d'enrichissement d'images pour les séries
 * Communique avec l'API backend pour enrichir les séries avec des images de couverture
 */

class SeriesImageService {
    constructor() {
        this.backendUrl = API_BASE_URL
    }

    /**
     * Obtenir le token d'authentification
     */
    getAuthHeaders() {
        const token = localStorage.getItem('token');
        return {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        };
    }

    /**
     * Enrichir un échantillon de séries populaires
     */
    async enrichSampleSeries(count = 10) {
        try {
            const response = await fetch(`${this.backendUrl}/api/series/enrich/sample?count=${count}`, {
                method: 'GET',
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error(`Erreur ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('✅ Échantillon enrichi:', data);
            return data;

        } catch (error) {
            console.error('❌ Erreur enrichissement échantillon:', error);
            throw error;
        }
    }

    /**
     * Enrichir une série unique
     */
    async enrichSingleSeries(seriesData) {
        try {
            const response = await fetch(`${this.backendUrl}/api/series/enrich/single`, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify(seriesData)
            });

            if (!response.ok) {
                throw new Error(`Erreur ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('✅ Série enrichie:', data);
            return data;

        } catch (error) {
            console.error('❌ Erreur enrichissement série:', error);
            throw error;
        }
    }

    /**
     * Enrichir une liste de séries
     */
    async enrichSeriesList(seriesList) {
        try {
            const response = await fetch(`${this.backendUrl}/api/series/enrich/images`, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify({ series_list: seriesList })
            });

            if (!response.ok) {
                throw new Error(`Erreur ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('✅ Liste enrichie:', data);
            return data;

        } catch (error) {
            console.error('❌ Erreur enrichissement liste:', error);
            throw error;
        }
    }

    /**
     * Enrichir la base de données complète
     */
    async enrichDatabase(sampleSize = null) {
        try {
            const requestData = {};
            if (sampleSize) {
                requestData.sample_size = sampleSize;
            }

            const response = await fetch(`${this.backendUrl}/api/series/enrich/database`, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify(requestData)
            });

            if (!response.ok) {
                throw new Error(`Erreur ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('✅ Enrichissement base démarré:', data);
            return data;

        } catch (error) {
            console.error('❌ Erreur enrichissement base:', error);
            throw error;
        }
    }

    /**
     * Obtenir le statut de l'enrichissement
     */
    async getEnrichmentStatus() {
        try {
            const response = await fetch(`${this.backendUrl}/api/series/images/status`, {
                method: 'GET',
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error(`Erreur ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log('📊 Statut enrichissement:', data);
            return data;

        } catch (error) {
            console.error('❌ Erreur statut enrichissement:', error);
            throw error;
        }
    }

    /**
     * Récupérer la couverture d'une série directement depuis Open Library
     * Étape 1 : chercher la série → cover_i
     * Étape 2 : si pas de résultat → chercher "tome 1" de la série
     * Retourne une URL d'image ou null
     */
    async fetchCoverFromOpenLibrary(seriesName) {
        if (!seriesName) return null;

        const tryFetch = async (query) => {
            try {
                const url = `https://openlibrary.org/search.json?q=${encodeURIComponent(query)}&limit=5&fields=cover_i,title`;
                const response = await fetch(url);
                if (!response.ok) return null;
                const data = await response.json();
                const hit = (data.docs || []).find(d => d.cover_i);
                if (hit?.cover_i) {
                    return `https://covers.openlibrary.org/b/id/${hit.cover_i}-L.jpg`;
                }
                return null;
            } catch {
                return null;
            }
        };

        // Essai 1 : nom de la série seul
        let url = await tryFetch(seriesName);
        if (url) return url;

        // Essai 2 : "série tome 1"
        url = await tryFetch(`${seriesName} tome 1`);
        if (url) return url;

        // Essai 3 : "série volume 1" (pour les séries anglaises)
        url = await tryFetch(`${seriesName} volume 1`);
        return url;
    }

    /**
     * Utiliser vision_expert_agent pour obtenir des images de qualité
     */
    async getVisionExpertImages(seriesName, category, count = 1) {
        try {
            // Note: Cette méthode sera implémentée quand vision_expert_agent sera disponible
            console.log(`🎨 Vision expert requis pour "${seriesName}" (${category})`);
            
            // Pour l'instant, on simule l'appel
            const placeholder = {
                series_name: seriesName,
                category: category,
                images: [], // Sera rempli par vision_expert_agent
                message: "Vision expert agent integration pending"
            };

            return placeholder;

        } catch (error) {
            console.error('❌ Erreur vision expert:', error);
            throw error;
        }
    }

    /**
     * Enrichir automatiquement les séries populaires au chargement de l'app
     * OPTIMISÉ - Robuste et sans dépendance au statut
     */
    async autoEnrichPopularSeries() {
        try {
            console.log('🚀 Auto-enrichissement des séries populaires...');
            
            // Essayer directement l'enrichissement d'un échantillon
            // Ne plus dépendre du statut qui nécessite une authentification
            const result = await this.enrichSampleSeries(10);
            
            if (result && result.enriched_count > 0) {
                console.log(`✅ Auto-enrichissement réussi: ${result.enriched_count}/${result.total_count} séries enrichies`);
                console.log('🖼️ Images disponibles pour:', result.series
                    .filter(s => s.cover_url)
                    .map(s => s.name)
                    .join(', ')
                );
                return result;
            } else {
                console.log('📷 Auto-enrichissement: aucune nouvelle image trouvée');
                return result;
            }

        } catch (error) {
            console.warn('⚠️ Auto-enrichissement échoué (mode graceful):', error.message);
            // Mode dégradé: ne pas faire échouer l'app
            // Les séries utiliseront les dégradés par défaut
            return null;
        }
    }

    /**
     * Mettre à jour une série avec une nouvelle image
     */
    updateSeriesImage(series, imageUrl) {
        if (!series || !imageUrl) return series;

        return {
            ...series,
            cover_url: imageUrl,
            image_enriched: true,
            image_updated_at: new Date().toISOString()
        };
    }

    /**
     * Vérifier si une série a une image valide
     */
    hasValidImage(series) {
        return series && series.cover_url && series.cover_url.trim() !== '';
    }

    /**
     * Obtenir une URL d'image de fallback selon la catégorie
     */
    getFallbackImage(category) {
        const fallbacks = {
            'roman': '/images/fallback/book-roman.jpg',
            'bd': '/images/fallback/book-bd.jpg',
            'manga': '/images/fallback/book-manga.jpg',
            'default': '/images/fallback/book-default.jpg'
        };

        return fallbacks[category] || fallbacks['default'];
    }

    /**
     * Précharger les images pour améliorer les performances
     */
    preloadImages(seriesList) {
        if (!Array.isArray(seriesList)) return;

        seriesList.forEach(series => {
            if (this.hasValidImage(series)) {
                const img = new Image();
                img.src = series.cover_url;
                // Les images seront mises en cache par le navigateur
            }
        });
    }
}

// Export de l'instance
export const seriesImageService = new SeriesImageService();

// Export de la classe pour tests
export default SeriesImageService;