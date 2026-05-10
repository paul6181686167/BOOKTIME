// 🔄 DÉTECTION AUTOMATIQUE À L'AJOUT DE LIVRES
import { API_BASE_URL } from '../config/environment';
import { SeriesDetector } from '../utils/seriesDetector';

export class AutoSeriesDetector {
  constructor() {
    this.apiBase = API_BASE_URL;
    this.enabled = true;
    this.minConfidence = 70;
  }

  // 🎯 Détection automatique lors de l'ajout d'un livre
  async detectAndEnhanceBook(bookData) {
    if (!this.enabled) return bookData;

    try {
      // 1. Saga déjà connue (ex: champ OL series) → priorité absolue
      if (bookData.saga && bookData.saga.trim()) {
        return bookData;
      }

      // 2. Détection locale via EXTENDED_SERIES_DATABASE (100+ séries, sans appel réseau)
      const localResult = SeriesDetector.detectBookSeries(bookData);
      if (localResult.belongsToSeries && localResult.confidence >= this.minConfidence) {
        return {
          ...bookData,
          saga: localResult.seriesName,
          volume_number: localResult.volumeNumber || null,
          auto_detected_series: true,
          detection_confidence: localResult.confidence,
          detection_method: localResult.method,
        };
      }

      // 3. Fallback : appel backend /detect (séries inconnues localement)
      const detection = await this.detectSeries(bookData);
      if (detection.found && detection.confidence >= this.minConfidence) {
        return {
          ...bookData,
          saga: detection.series_name,
          volume_number: detection.series_info?.volume_number || null,
          auto_detected_series: true,
          detection_confidence: detection.confidence,
          detection_method: 'backend_api',
        };
      }

      return bookData;
    } catch (error) {
      console.error('Erreur détection automatique série:', error);
      return bookData;
    }
  }

  // 🔍 Appel backend /detect (fallback)
  async detectSeries(bookData) {
    const token = localStorage.getItem('token');
    const params = new URLSearchParams({ title: bookData.title || '' });
    if (bookData.author) params.append('author', bookData.author);

    const response = await fetch(`${this.apiBase}/api/series/detect?${params}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!response.ok) throw new Error(`Erreur API détection: ${response.status}`);

    const data = await response.json();
    const best = data.detected_series?.[0];
    if (best) {
      return {
        found: true,
        series_name: best.series_name,
        confidence: best.confidence,
        series_info: { volume_number: best.volume_number || null },
        match_reasons: [`confiance: ${best.confidence}`]
      };
    }
    return { found: false, confidence: 0, series_name: null, match_reasons: [] };
  }

  // 📢 Notification utilisateur
  notifySeriesDetected(book, detection) {
    // Toast notification
    if (window.toast) {
      window.toast.success(
        `📚 Série détectée: "${detection.series_name}" (confiance: ${detection.confidence})`,
        {
          duration: 4000,
          position: 'top-right'
        }
      );
    }

    // Console détaillée
    console.log('🎯 DÉTECTION AUTOMATIQUE RÉUSSIE:');
    console.log(`📚 Livre: "${book.title}"`);
    console.log(`🎯 Série: "${detection.series_name}"`);
    console.log(`📊 Confiance: ${detection.confidence}`);
    console.log(`🔍 Raisons: ${detection.match_reasons.join(', ')}`);
    if (book.volume_number) {
      console.log(`📖 Volume: ${book.volume_number}`);
    }
  }

  // ⚙️ Configuration
  configure(options = {}) {
    const {
      enabled = true,
      minConfidence = 120,
      notifyUser = true
    } = options;

    this.enabled = enabled;
    this.minConfidence = minConfidence;
    this.notifyUser = notifyUser;

    console.log('⚙️ Configuration détection automatique:', {
      enabled: this.enabled,
      minConfidence: this.minConfidence,
      notifyUser: this.notifyUser
    });
  }
}

// 🔄 Hook pour l'intégration dans les composants React
export const useAutoSeriesDetection = () => {
  const detector = new AutoSeriesDetector();

  const enhanceBookWithSeries = async (bookData) => {
    return await detector.detectAndEnhanceBook(bookData);
  };

  const configure = (options) => {
    detector.configure(options);
  };

  return {
    enhanceBookWithSeries,
    configure,
    detector
  };
};

// 🌍 Export global
window.AutoSeriesDetector = AutoSeriesDetector;

export default AutoSeriesDetector;