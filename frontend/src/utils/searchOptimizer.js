// Optimiseur de recherche avec algorithme de priorisation et scoring avancé
// OPTIMISATION ALGORITHME RECHERCHE - Priorisation fiches séries et tolérance orthographique universelle

import { EXTENDED_SERIES_DATABASE } from './seriesDatabaseExtended.js';
import { FuzzyMatcher } from './fuzzyMatcher.js';
import { SeriesValidator } from './seriesValidator.js';

export class SearchOptimizer {
  
  // Algorithme de détection avec scoring prioritaire optimisé
  static detectSeriesWithAdvancedScoring(searchQuery) {
    const query = FuzzyMatcher.normalizeString(searchQuery);
    const detectedSeries = [];
    
    // Parcourir toutes les catégories de séries
    for (const [categoryKey, seriesCategory] of Object.entries(EXTENDED_SERIES_DATABASE)) {
      for (const [seriesKey, series] of Object.entries(seriesCategory)) {
        
        let bestScore = 0;
        let matchType = '';
        let matchDetails = '';
        
        // 1. CORRESPONDANCE EXACTE (Score maximum : 100000 + 200)
        const exactMatch = series.variations.find(variation => 
          FuzzyMatcher.normalizeString(variation) === query
        );
        if (exactMatch) {
          bestScore = 200;
          matchType = 'exact_match';
          matchDetails = `Correspondance exacte avec "${exactMatch}"`;
        }
        
        // 2. CORRESPONDANCE PARTIELLE FORTE (Score : 100000 + 180)
        else {
          for (const variation of series.variations) {
            const normalizedVariation = FuzzyMatcher.normalizeString(variation);
            if (query.includes(normalizedVariation) || normalizedVariation.includes(query)) {
              if (bestScore < 180) {
                bestScore = 180;
                matchType = 'partial_strong_match';
                matchDetails = `Correspondance partielle forte avec "${variation}"`;
              }
            }
          }
        }
        
        // 3. CORRESPONDANCE PAR MOTS-CLÉS (Score : 100000 + 160)
        if (bestScore < 160) {
          for (const keyword of series.keywords) {
            if (query.includes(FuzzyMatcher.normalizeString(keyword))) {
              bestScore = Math.max(bestScore, 160);
              matchType = 'keyword_match';
              matchDetails = `Correspondance par mot-clé "${keyword}"`;
              break;
            }
          }
        }
        
        // 4. CORRESPONDANCE FUZZY AVANCÉE (Score : 100000 + 120-150)
        if (bestScore < 150) {
          let maxFuzzyScore = 0;
          let bestFuzzyVariation = '';
          
          for (const variation of series.variations) {
            const fuzzyScore = FuzzyMatcher.fuzzyMatch(query, variation, 4);
            if (fuzzyScore >= 60 && fuzzyScore > maxFuzzyScore) { // Seuil minimum de 60%
              maxFuzzyScore = fuzzyScore;
              bestFuzzyVariation = variation;
            }
          }
          
          if (maxFuzzyScore > 0) {
            // Score basé sur la qualité de la correspondance floue
            bestScore = Math.max(bestScore, Math.round(120 + (maxFuzzyScore * 0.3)));
            matchType = 'fuzzy_match_advanced';
            matchDetails = `Correspondance floue ${maxFuzzyScore}% avec "${bestFuzzyVariation}"`;
          }
        }
        
        // 5. CORRESPONDANCE PHONÉTIQUE (Score : 100000 + 100-120)
        if (bestScore < 120) {
          for (const variation of series.variations) {
            const phoneticDistance = FuzzyMatcher.phoneticMatch(query, variation);
            if (phoneticDistance <= 2 && variation.length > 3) {
              const phoneticScore = Math.max(0, 120 - (phoneticDistance * 10));
              if (phoneticScore > bestScore) {
                bestScore = phoneticScore;
                matchType = 'phonetic_match';
                matchDetails = `Correspondance phonétique avec "${variation}" (distance: ${phoneticDistance})`;
              }
            }
          }
        }
        
        // Si une correspondance est trouvée, ajouter avec score prioritaire
        if (bestScore >= 100) { // Seuil minimum pour être considéré
          detectedSeries.push({
            series: series,
            confidence: 100000 + bestScore, // SCORE PRIORITAIRE 100000+
            match_reasons: [matchType, 'official_wikipedia_series'],
            matchType: matchType,
            originalScore: bestScore,
            matchDetails: matchDetails,
            category: categoryKey,
            seriesKey: seriesKey
          });
        }
      }
    }
    
    // Retourner les séries triées par score de confiance
    return detectedSeries.sort((a, b) => b.confidence - a.confidence);
  }

  // Génération des cartes séries avec scoring prioritaire optimisé
  static generateSeriesCardsForSearch(query, userBooks = []) {
    console.log('🔍 Génération cartes séries pour:', query);
    
    // 1. DÉTECTION SÉRIES OFFICIELLES (Score 100000+)
    const officialSeries = this.detectSeriesWithAdvancedScoring(query);
    
    // 2. DÉTECTION SÉRIES BIBLIOTHÈQUE UTILISATEUR (Score 90000+)
    const userSeries = this.detectUserLibrarySeries(query, userBooks);
    
    // 3. CONVERSION EN CARTES SÉRIES
    const seriesCards = [];
    
    // Ajouter séries officielles
    officialSeries.forEach(detected => {
      seriesCards.push(this.createSeriesCard(detected, 'official'));
    });
    
    // Ajouter séries utilisateur (si pas déjà détectées comme officielles)
    userSeries.forEach(detected => {
      const alreadyDetected = seriesCards.some(card => 
        FuzzyMatcher.normalizeString(card.name) === FuzzyMatcher.normalizeString(detected.series.name)
      );
      
      if (!alreadyDetected) {
        seriesCards.push(this.createSeriesCard(detected, 'user_library'));
      }
    });
    
    console.log(`✅ ${seriesCards.length} carte(s) série générée(s) avec scores prioritaires`);
    return seriesCards.slice(0, 5); // Limiter à 5 séries maximum
  }

  // Détection des séries dans la bibliothèque utilisateur
  static detectUserLibrarySeries(query, userBooks) {
    const potentialSeries = {};
    
    userBooks.forEach(book => {
      if (book.saga && book.saga.trim()) {
        const sagaKey = FuzzyMatcher.normalizeString(book.saga);
        const queryNormalized = FuzzyMatcher.normalizeString(query);
        
        // Vérifier si la requête correspond à cette saga
        const sagaMatch = FuzzyMatcher.fuzzyMatch(queryNormalized, sagaKey);
        
        if (sagaMatch >= 50) { // Seuil minimum pour considérer une correspondance
          if (!potentialSeries[sagaKey]) {
            potentialSeries[sagaKey] = {
              series: {
                name: book.saga,
                authors: [book.author],
                category: book.category,
                volumes: 1,
                description: `Série de votre bibliothèque incluant "${book.title}"`,
                first_published: book.publication_year || 'Inconnue',
                status: 'user_library',
                keywords: [book.saga.toLowerCase()],
                variations: [book.saga.toLowerCase()],
                exclusions: []
              },
              confidence: 90000 + sagaMatch, // Score 90000+ pour bibliothèque utilisateur
              match_reasons: ['user_library_saga'],
              matchType: 'user_library_match',
              originalScore: sagaMatch,
              matchDetails: `Série de votre bibliothèque (${sagaMatch}% de correspondance)`
            };
          } else {
            // Améliorer les données de la série existante
            potentialSeries[sagaKey].confidence += 10;
            potentialSeries[sagaKey].series.volumes += 1;
            
            if (!potentialSeries[sagaKey].series.authors.includes(book.author)) {
              potentialSeries[sagaKey].series.authors.push(book.author);
            }
          }
        }
      }
    });
    
    return Object.values(potentialSeries)
      .filter(series => series.confidence >= 90000)
      .sort((a, b) => b.confidence - a.confidence);
  }

  // Création d'une carte série
  static createSeriesCard(detected, sourceType) {
    const series = detected.series;
    const isOfficial = sourceType === 'official';
    
    return {
      // Identifiants
      id: `series_${FuzzyMatcher.normalizeString(series.name).replace(/\s+/g, '_')}`,
      isSeriesCard: true, // MARQUEUR ESSENTIEL pour le tri prioritaire
      isFromOpenLibrary: false,
      
      // Données de base
      name: series.name,
      title: `📚 ${isOfficial ? 'SÉRIE' : 'MA SÉRIE'} : ${series.name}`,
      author: series.authors.join(', '),
      category: series.category,
      description: this.formatSeriesDescription(series, detected),
      cover_url: '', // Pas de couverture pour les cartes séries
      
      // Scoring et matching
      relevanceScore: detected.confidence, // Score 100000+ ou 90000+
      confidence: detected.confidence,
      match_reasons: detected.match_reasons,
      matchType: detected.matchType,
      originalScore: detected.originalScore,
      matchDetails: detected.matchDetails,
      
      // Données séries
      seriesData: series,
      volumes: series.volumes,
      status: series.status,
      first_published: series.first_published,
      
      // Informations de pertinence pour l'affichage
      relevanceInfo: {
        level: 'prioritaire',
        label: this.getRelevanceLabel(detected),
        color: isOfficial ? 'bg-purple-600' : 'bg-blue-600',
        icon: '📚'
      },
      
      // Métadonnées pour navigation
      sourceType: sourceType,
      wikipedia_url: series.wikipedia_url || null
    };
  }

  // Formatage de la description de série
  static formatSeriesDescription(series, detected) {
    const baseDescription = series.description || '';
    const volumeInfo = `${series.volumes} tome(s)`;
    const matchInfo = detected.matchDetails || '';
    const statusInfo = series.status === 'completed' ? '✅ Complète' : '🔄 En cours';
    
    return `${baseDescription} | ${volumeInfo} | ${statusInfo} | 🎯 ${matchInfo}`;
  }

  // Label de pertinence selon le type de correspondance
  static getRelevanceLabel(detected) {
    switch (detected.matchType) {
      case 'exact_match':
        return 'Série (correspondance exacte)';
      case 'partial_strong_match':
        return 'Série (correspondance forte)';
      case 'keyword_match':
        return 'Série (mot-clé)';
      case 'fuzzy_match_advanced':
        return 'Série (correspondance approximative)';
      case 'phonetic_match':
        return 'Série (correspondance phonétique)';
      case 'user_library_match':
        return 'Série (votre bibliothèque)';
      default:
        return 'Série détectée';
    }
  }

  // Tri final avec garantie de priorité absolue des séries
  static applySuperiorSeriesPrioritySort(allResults) {
    return allResults.sort((a, b) => {
      // 1. Les séries ont TOUJOURS la priorité absolue
      if (a.isSeriesCard && !b.isSeriesCard) return -1;
      if (!a.isSeriesCard && b.isSeriesCard) return 1;
      
      // 2. Si les deux sont des séries, trier par score de confiance
      if (a.isSeriesCard && b.isSeriesCard) {
        return (b.relevanceScore || b.confidence || 0) - (a.relevanceScore || a.confidence || 0);
      }
      
      // 3. Si les deux sont des livres, maintenir ordre original ou par pertinence
      const scoreA = a.relevanceScore || a.search_score || 0;
      const scoreB = b.relevanceScore || b.search_score || 0;
      return scoreB - scoreA;
    });
  }

  // Validation stricte pour filtrage dans les fiches séries
  static validateBookForSeries(book, seriesData) {
    return SeriesValidator.validateByCategory(book, seriesData);
  }

  // Métriques de performance pour le monitoring
  static getSearchMetrics(query, results, detectionTime) {
    const seriesCount = results.filter(r => r.isSeriesCard).length;
    const booksCount = results.length - seriesCount;
    
    return {
      query: query,
      total_results: results.length,
      series_detected: seriesCount,
      books_found: booksCount,
      detection_time_ms: detectionTime,
      has_priority_series: seriesCount > 0,
      top_result_is_series: results.length > 0 && results[0].isSeriesCard,
      average_series_score: seriesCount > 0 ? 
        results.filter(r => r.isSeriesCard).reduce((sum, r) => sum + (r.confidence || 0), 0) / seriesCount : 0
    };
  }
}

export default SearchOptimizer;