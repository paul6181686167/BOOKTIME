/**
 * SERIES DETECTOR - Détection intelligente de séries pour masquage automatique
 * 
 * Utilise les mêmes capacités de détection que l'application possède déjà
 * pour déterminer si un livre fait partie d'une série, même sans champ saga
 */

import { EXTENDED_SERIES_DATABASE } from './seriesDatabaseExtended.js';
import { FuzzyMatcher } from './fuzzyMatcher.js';

export class SeriesDetector {
  
  /**
   * Détecte si un livre fait partie d'une série basé sur son titre et auteur
   * @param {Object} book - Le livre à analyser
   * @returns {Object} - Résultat de détection {belongsToSeries: boolean, seriesName: string, confidence: number}
   */
  static detectBookSeries(book) {
    // 1. Vérifier d'abord le champ saga existant
    if (book.saga && book.saga.trim()) {
      return {
        belongsToSeries: true,
        seriesName: book.saga.trim(),
        confidence: 100,
        method: 'existing_saga_field'
      };
    }
    
    // 2. Détection automatique basée sur titre et auteur
    const titleAnalysis = this.analyzeBookTitle(book.title, book.author);
    
    if (titleAnalysis.belongsToSeries) {
      return titleAnalysis;
    }
    
    // 3. Recherche dans la base de séries étendue
    const seriesMatch = this.searchInSeriesDatabase(book.title, book.author);
    
    if (seriesMatch.belongsToSeries) {
      return seriesMatch;
    }
    
    // 4. Aucune série détectée
    return {
      belongsToSeries: false,
      seriesName: null,
      confidence: 0,
      method: 'no_series_detected'
    };
  }
  
  /**
   * Analyse le titre du livre pour détecter des patterns de série
   */
  static analyzeBookTitle(title, author) {
    if (!title) return { belongsToSeries: false };
    
    const titleLower = title.toLowerCase().trim();
    const patterns = [
      // Patterns Harry Potter
      {
        regex: /harry\s*potter/i,
        seriesName: 'Harry Potter',
        authors: ['j.k. rowling', 'j. k. rowling', 'joanne rowling']
      },
      // Patterns One Piece
      {
        regex: /one\s*piece/i,
        seriesName: 'One Piece',
        authors: ['eiichiro oda']
      },
      // Patterns Astérix
      {
        regex: /ast[eé]rix/i,
        seriesName: 'Astérix',
        authors: ['rené goscinny', 'albert uderzo', 'goscinny', 'uderzo']
      },
      // Patterns Le Seigneur des Anneaux
      {
        regex: /(seigneur.*anneaux|lord.*rings)/i,
        seriesName: 'Le Seigneur des Anneaux',
        authors: ['j.r.r. tolkien', 'tolkien']
      },
      // Patterns Dragon Ball
      {
        regex: /dragon\s*ball/i,
        seriesName: 'Dragon Ball',
        authors: ['akira toriyama']
      },
      // Patterns Naruto
      {
        regex: /naruto/i,
        seriesName: 'Naruto',
        authors: ['masashi kishimoto']
      },
      // Patterns génériques avec numérotation
      {
        regex: /tome\s*\d+|volume\s*\d+|vol\.\s*\d+|#\d+/i,
        detectFromTitle: true
      }
    ];
    
    for (const pattern of patterns) {
      if (pattern.regex.test(titleLower)) {
        // Vérifier l'auteur si spécifié
        if (pattern.authors && author) {
          const authorLower = author.toLowerCase().trim();
          const authorMatch = pattern.authors.some(seriesAuthor => 
            authorLower.includes(seriesAuthor) || seriesAuthor.includes(authorLower)
          );
          
          if (authorMatch) {
            return {
              belongsToSeries: true,
              seriesName: pattern.seriesName,
              confidence: 95,
              method: 'title_author_pattern'
            };
          }
        } else if (pattern.seriesName) {
          return {
            belongsToSeries: true,
            seriesName: pattern.seriesName,
            confidence: 85,
            method: 'title_pattern'
          };
        }
      }
    }
    
    return { belongsToSeries: false };
  }
  
  /**
   * Recherche dans la base de données de séries étendue
   */
  static searchInSeriesDatabase(title, author) {
    if (!title) return { belongsToSeries: false };
    
    const titleNormalized = FuzzyMatcher.normalizeString(title);
    const authorNormalized = author ? FuzzyMatcher.normalizeString(author) : '';
    
    // Parcourir toutes les catégories de séries
    for (const [categoryKey, seriesCategory] of Object.entries(EXTENDED_SERIES_DATABASE)) {
      for (const [seriesKey, series] of Object.entries(seriesCategory)) {
        
        // Test correspondance avec le nom de la série
        const seriesNameMatch = FuzzyMatcher.fuzzyMatch(titleNormalized, FuzzyMatcher.normalizeString(series.name));
        
        if (seriesNameMatch >= 70) {
          // Vérifier l'auteur si disponible
          if (author && series.authors && series.authors.length > 0) {
            const authorMatch = series.authors.some(seriesAuthor => {
              const seriesAuthorNormalized = FuzzyMatcher.normalizeString(seriesAuthor);
              return FuzzyMatcher.fuzzyMatch(authorNormalized, seriesAuthorNormalized) >= 60;
            });
            
            if (authorMatch) {
              return {
                belongsToSeries: true,
                seriesName: series.name,
                confidence: Math.min(seriesNameMatch + 10, 100),
                method: 'series_database_title_author'
              };
            }
          } else {
            return {
              belongsToSeries: true,
              seriesName: series.name,
              confidence: seriesNameMatch,
              method: 'series_database_title'
            };
          }
        }
        
        // Test correspondance avec les variations
        if (series.variations) {
          for (const variation of series.variations) {
            const variationMatch = FuzzyMatcher.fuzzyMatch(titleNormalized, FuzzyMatcher.normalizeString(variation));
            
            if (variationMatch >= 70) {
              return {
                belongsToSeries: true,
                seriesName: series.name,
                confidence: variationMatch,
                method: 'series_database_variation'
              };
            }
          }
        }
        
        // Test correspondance avec les mots-clés
        if (series.keywords) {
          for (const keyword of series.keywords) {
            if (titleNormalized.includes(FuzzyMatcher.normalizeString(keyword))) {
              return {
                belongsToSeries: true,
                seriesName: series.name,
                confidence: 80,
                method: 'series_database_keyword'
              };
            }
          }
        }
      }
    }
    
    return { belongsToSeries: false };
  }
  
  /**
   * Filtre une liste de livres en masquant ceux qui appartiennent à des séries
   */
  static filterBooksWithSeriesMasking(books, options = {}) {
    const { logMasking = true, minConfidence = 70 } = options;
    
    const maskedBooks = [];
    const seriesBooks = [];
    
    books.forEach(book => {
      const detection = this.detectBookSeries(book);
      
      if (detection.belongsToSeries && detection.confidence >= minConfidence) {
        seriesBooks.push({
          ...book,
          detectedSeries: detection.seriesName,
          detectionConfidence: detection.confidence,
          detectionMethod: detection.method
        });
        
        if (logMasking) {
          console.log(`🔒 [MASQUAGE INTELLIGENT] Livre "${book.title}" détecté série "${detection.seriesName}" (${detection.confidence}% confiance, méthode: ${detection.method}) - MASQUÉ`);
        }
      } else {
        maskedBooks.push(book);
        
        if (logMasking) {
          console.log(`📖 [MASQUAGE INTELLIGENT] Livre "${book.title}" standalone - AFFICHÉ`);
        }
      }
    });
    
    if (logMasking) {
      console.log(`🔒 [MASQUAGE INTELLIGENT] Résumé: ${seriesBooks.length} livre(s) masqué(s), ${maskedBooks.length} livre(s) affichés`);
    }
    
    return {
      visibleBooks: maskedBooks,
      maskedBooks: seriesBooks,
      stats: {
        total: books.length,
        visible: maskedBooks.length,
        masked: seriesBooks.length
      }
    };
  }
}

export default SeriesDetector;