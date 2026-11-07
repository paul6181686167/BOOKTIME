//  DÉTECTION AUTOMATIQUE À L'AJOUT DE LIVRES
// Intégration dans le processus d'ajout pour détecter automatiquement les séries

import { API_BASE_URL } from '../config/environment';
import logger from '../utils/logger';

export class AutoSeriesDetector {
  constructor() {
    this.apiBase = API_BASE_URL;
    this.enabled = true;
    this.minConfidence = 70;
  }

  //  Détection automatique lors de l'ajout d'un livre
  async detectAndEnhanceBook(bookData) {
    if (!this.enabled) {
      return bookData;
    }

    logger.debug(' Détection automatique série pour:', bookData.title);

    try {
      // 1. Vérifier si le livre a déjà une saga
      if (bookData.saga && bookData.saga.trim()) {
        logger.debug(' Saga déjà définie:', bookData.saga);
        return bookData;
      }

      // 2. Détecter la série
      const detection = await this.detectSeries(bookData);
      
      if (detection.found && detection.confidence >= this.minConfidence) {
        logger.debug(` Série détectée: "${detection.series_name}" (confiance: ${detection.confidence})`);
        
        // 3. Enrichir les données du livre
        const enhancedBook = {
          ...bookData,
          saga: detection.series_name,
          volume_number: detection.series_info?.volume_number || null,
          auto_detected_series: true,
          detection_confidence: detection.confidence,
          detection_reasons: detection.match_reasons
        };

        // 4. Notification utilisateur
        this.notifySeriesDetected(enhancedBook, detection);
        
        return enhancedBook;
      } else {
        logger.debug(` Livre standalone (confiance: ${detection.confidence})`);
        return bookData;
      }

    } catch (error) {
      logger.error(' Erreur détection automatique:', error);
      return bookData; // Retour aux données originales en cas d'erreur
    }
  }

  //  Détection de série
  async detectSeries(bookData) {
    const token = localStorage.getItem('token');
    const params = new URLSearchParams({ title: bookData.title || '' });
    if (bookData.author) params.append('author', bookData.author);

    const response = await fetch(`${this.apiBase}/api/series/detect?${params}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (!response.ok) {
      throw new Error(`Erreur API détection: ${response.status}`);
    }

    const data = await response.json();
    // Normaliser la réponse backend → format attendu par detectAndEnhanceBook
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

  //  Notification utilisateur
  notifySeriesDetected(book, detection) {
    // Toast notification
    if (window.toast) {
      window.toast.success(
        ` Série détectée: "${detection.series_name}" (confiance: ${detection.confidence})`,
        {
          duration: 4000,
          position: 'top-right'
        }
      );
    }

    // Console détaillée
    logger.debug(' DÉTECTION AUTOMATIQUE RÉUSSIE:');
    logger.debug(` Livre: "${book.title}"`);
    logger.debug(` Série: "${detection.series_name}"`);
    logger.debug(` Confiance: ${detection.confidence}`);
    logger.debug(` Raisons: ${detection.match_reasons.join(', ')}`);
    if (book.volume_number) {
      logger.debug(` Volume: ${book.volume_number}`);
    }
  }

  // Configuration
  configure(options = {}) {
    const {
      enabled = true,
      minConfidence = 120,
      notifyUser = true
    } = options;

    this.enabled = enabled;
    this.minConfidence = minConfidence;
    this.notifyUser = notifyUser;

    logger.debug('Configuration détection automatique:', {
      enabled: this.enabled,
      minConfidence: this.minConfidence,
      notifyUser: this.notifyUser
    });
  }
}

//  Hook pour l'intégration dans les composants React
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

//  Export global
window.AutoSeriesDetector = AutoSeriesDetector;

export default AutoSeriesDetector;