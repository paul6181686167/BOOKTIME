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
      // Patterns Dog Man / Super Chien
      {
        regex: /\b(dog\s*man|super\s*chien)\b/i,
        seriesName: 'Dog Man',
        authors: ['dav pilkey', 'pilkey']
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
        // Vérifier les exclusions : si le titre correspond à une exclusion, ignorer cette série
        if (series.exclusions && Array.isArray(series.exclusions)) {
          const titleLower = (title || '').toLowerCase();
          const isExcluded = series.exclusions.some(exc => 
            exc && titleLower.includes(String(exc).toLowerCase())
          );
          if (isExcluded) continue;
        }
        
        // Nom / variation / traduction EN contenus dans le titre
        // (ex. « Harry Potter and the Chamber of Secrets » → Harry Potter)
        const nameCandidates = [
          series.name,
          ...(Array.isArray(series.variations) ? series.variations : []),
          series.translations?.en,
          series.translations?.fr,
        ].filter(Boolean);
        for (const candidate of nameCandidates) {
          const n = FuzzyMatcher.normalizeString(candidate);
          if (n.length < 5) continue;
          if (!titleNormalized.includes(n)) continue;
          const authorOk =
            !authorNormalized ||
            !series.authors?.length ||
            series.authors.some((sa) => {
              const san = FuzzyMatcher.normalizeString(sa);
              return (
                FuzzyMatcher.fuzzyMatch(authorNormalized, san) >= 50 ||
                authorNormalized.includes(san) ||
                san.includes(authorNormalized.split(' ').pop())
              );
            });
          if (authorOk) {
            return {
              belongsToSeries: true,
              seriesName: series.name,
              confidence: 90,
              method: 'series_database_name_in_title',
            };
          }
        }

        // Test correspondance avec le nom de la série
        const seriesNameMatch = FuzzyMatcher.fuzzyMatch(titleNormalized, FuzzyMatcher.normalizeString(series.name));
        
        if (seriesNameMatch >= 70) {
          // Nom exact (ou quasi) de la série → série, même si l'auteur est bruité
          if (seriesNameMatch >= 92) {
            return {
              belongsToSeries: true,
              seriesName: series.name,
              confidence: seriesNameMatch,
              method: 'series_database_exact_title'
            };
          }
          // Vérifier l'auteur si disponible
          if (author && series.authors && series.authors.length > 0) {
            const authorMatch = series.authors.some(seriesAuthor => {
              const seriesAuthorNormalized = FuzzyMatcher.normalizeString(seriesAuthor);
              return (
                FuzzyMatcher.fuzzyMatch(authorNormalized, seriesAuthorNormalized) >= 50 ||
                authorNormalized.includes(seriesAuthorNormalized) ||
                seriesAuthorNormalized.includes(authorNormalized.split(' ').pop())
              );
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
        
        // Test correspondance avec les titres de tomes individuels (méthode la plus précise)
        // Permet de détecter "La Communauté de l'Anneau" → "Le Seigneur des Anneaux"
        // + titres EN vs FR (The Last Olympian ≈ Le Dernier Olympien)
        const volTitleBag = [
          ...Object.values(series.volume_titles || {}),
          ...Object.values(series.volume_titles_en || {}),
        ];
        const authorMatchesSeries =
          !!authorNormalized &&
          Array.isArray(series.authors) &&
          series.authors.some(
            (sa) =>
              FuzzyMatcher.fuzzyMatch(
                authorNormalized,
                FuzzyMatcher.normalizeString(sa)
              ) >= 50
          );

        for (const volTitle of volTitleBag) {
          if (!volTitle) continue;
          const aliases = Array.isArray(volTitle) ? volTitle : [volTitle];
          for (const alias of aliases) {
            const volTitleNorm = FuzzyMatcher.normalizeString(alias);
            if (!volTitleNorm || volTitleNorm.length < 6) continue;

            const isExactMatch = titleNormalized === volTitleNorm;
            const isPartialMatch =
              volTitleNorm.length >= 12 && titleNormalized.includes(volTitleNorm);
            // Chevauchement de mots (FR↔EN) : olympien / olympian
            const wordScore = FuzzyMatcher.partialWordMatch(
              titleNormalized,
              volTitleNorm
            );
            const stemHit = (() => {
              const wa = titleNormalized.split(' ').filter((w) => w.length >= 5);
              const wb = volTitleNorm.split(' ').filter((w) => w.length >= 5);
              if (!wa.length || !wb.length) return false;
              return wa.some((x) =>
                wb.some(
                  (y) =>
                    x === y ||
                    (x.length >= 6 && y.length >= 6 && (x.startsWith(y.slice(0, 6)) || y.startsWith(x.slice(0, 6))))
                )
              );
            })();
            const isLooseMatch =
              authorMatchesSeries && (wordScore >= 50 || stemHit);

            if (isExactMatch || isPartialMatch || isLooseMatch) {
              if (volTitleNorm.length >= 15 || isExactMatch) {
                return {
                  belongsToSeries: true,
                  seriesName: series.name,
                  confidence: isExactMatch ? 98 : isPartialMatch ? 95 : 88,
                  method: 'series_database_volume_title',
                };
              }
              if (authorMatchesSeries) {
                return {
                  belongsToSeries: true,
                  seriesName: series.name,
                  confidence: 93,
                  method: 'series_database_volume_title',
                };
              }
              if (!author) {
                return {
                  belongsToSeries: true,
                  seriesName: series.name,
                  confidence: 80,
                  method: 'series_database_volume_title_no_author',
                };
              }
            }
          }
        }

        // Auteur connu + mot-clé distinctif du titre (ex. Riordan + « olympian »)
        if (authorMatchesSeries && Array.isArray(series.keywords)) {
          const hit = series.keywords.some((kw) => {
            const k = FuzzyMatcher.normalizeString(kw);
            if (!k || k.length < 5) return false;
            if (titleNormalized.includes(k)) return true;
            // stem FR/EN court
            return (
              k.length >= 6 &&
              titleNormalized.split(' ').some(
                (w) =>
                  w.length >= 6 &&
                  (w.startsWith(k.slice(0, 6)) || k.startsWith(w.slice(0, 6)))
              )
            );
          });
          if (hit) {
            return {
              belongsToSeries: true,
              seriesName: series.name,
              confidence: 82,
              method: 'series_database_author_keyword',
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
        
        // Mots-clés : uniquement si le nom de la série ou une variation apparaît aussi dans le titre
        // (évite faux positifs : "hidden" seul ne doit pas masquer "The Hidden Garden")
        if (series.keywords) {
          const seriesNameInTitle = FuzzyMatcher.normalizeString(series.name).length >= 4 && 
            titleNormalized.includes(FuzzyMatcher.normalizeString(series.name).slice(0, 8));
          const variationInTitle = (series.variations || []).some(v => 
            v && v.length >= 6 && titleNormalized.includes(FuzzyMatcher.normalizeString(v))
          );
          if (seriesNameInTitle || variationInTitle) {
            for (const keyword of series.keywords) {
              const kw = FuzzyMatcher.normalizeString(keyword);
              if (kw.length >= 6 && titleNormalized.includes(kw)) {
                return {
                  belongsToSeries: true,
                  seriesName: series.name,
                  confidence: 85,
                  method: 'series_database_keyword'
                };
              }
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
          console.log(` [MASQUAGE INTELLIGENT] Livre "${book.title}" détecté série "${detection.seriesName}" (${detection.confidence}% confiance, méthode: ${detection.method}) - MASQUÉ`);
        }
      } else {
        maskedBooks.push(book);
        
        if (logMasking) {
          console.log(` [MASQUAGE INTELLIGENT] Livre "${book.title}" standalone - AFFICHÉ`);
        }
      }
    });
    
    if (logMasking) {
      console.log(` [MASQUAGE INTELLIGENT] Résumé: ${seriesBooks.length} livre(s) masqué(s), ${maskedBooks.length} livre(s) affichés`);
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