// Optimiseur de recherche avec algorithme de priorisation et scoring avancé
// OPTIMISATION ALGORITHME RECHERCHE - Priorisation fiches séries et tolérance orthographique universelle

import { EXTENDED_SERIES_DATABASE } from './seriesDatabaseExtended.js';
import { FuzzyMatcher } from './fuzzyMatcher.js';
import { SeriesValidator } from './seriesValidator.js';

export class SearchOptimizer {
  
  // Algorithme de détection avec scoring prioritaire optimisé - NOUVELLE ARCHITECTURE MODULAIRE
  static detectSeriesWithAdvancedScoring(searchQuery) {
    const detectedSeries = [];
    
    // Parcourir toutes les catégories de séries avec nouveaux modules
    for (const [categoryKey, seriesCategory] of Object.entries(EXTENDED_SERIES_DATABASE)) {
      for (const [seriesKey, series] of Object.entries(seriesCategory)) {
        
        // Vérifier les exclusions : si la requête correspond à une exclusion, ignorer cette série
        if (series.exclusions && Array.isArray(series.exclusions)) {
          const queryLower = searchQuery.toLowerCase();
          const isExcluded = series.exclusions.some(exc =>
            exc && queryLower.includes(String(exc).toLowerCase())
          );
          if (isExcluded) continue;
        }

        let bestMatch = null;
        let bestScore = 0;
        
        // 1. CORRESPONDANCE MULTICRITÈRES AVANCÉE avec FuzzyMatcher
        // Tester le nom principal de la série
        const mainNameMatch = FuzzyMatcher.advancedMatch(searchQuery, series.name, {
          exactWeight: 200,
          fuzzyWeight: 180,
          partialWeight: 160,
          phoneticWeight: 140,
          transposeWeight: 170
        });
        
        if (mainNameMatch > bestScore) {
          bestScore = mainNameMatch;
          bestMatch = {
            type: 'main_name',
            target: series.name,
            score: mainNameMatch
          };
        }
        
        // 2. CORRESPONDANCE AVEC VARIATIONS OFFICIELLES
        for (const variation of series.variations || []) {
          const variationMatch = FuzzyMatcher.advancedMatch(searchQuery, variation, {
            exactWeight: 190,
            fuzzyWeight: 170,
            partialWeight: 150,
            phoneticWeight: 130,
            transposeWeight: 160
          });
          
          if (variationMatch > bestScore) {
            bestScore = variationMatch;
            bestMatch = {
              type: 'variation',
              target: variation,
              score: variationMatch
            };
          }
        }
        
        // 🆕 2.1. CORRESPONDANCE PAR AUTEUR - CORRECTION PRINCIPALE
        for (const author of series.authors || []) {
          const authorMatch = FuzzyMatcher.advancedMatch(searchQuery, author, {
            exactWeight: 180,
            fuzzyWeight: 160,
            partialWeight: 140,
            phoneticWeight: 120,
            transposeWeight: 150
          });
          
          if (authorMatch > bestScore && authorMatch >= 50) { // Seuil adapté pour auteurs
            bestScore = authorMatch;
            bestMatch = {
              type: 'author_match',
              target: author,
              score: authorMatch
            };
          }
        }
        
        // 3. CORRESPONDANCE LINGUISTIQUE MULTILINGUE
        const linguisticScore = FuzzyMatcher.checkLinguisticVariations(
          searchQuery, 
          seriesKey, 
          series.variations || []
        );
        
        if (linguisticScore > bestScore) {
          bestScore = linguisticScore;
          bestMatch = {
            type: 'linguistic_variation',
            target: series.name,
            score: linguisticScore
          };
        }
        
        // 4. CORRESPONDANCE PAR MOTS-CLÉS ÉTENDUS
        for (const keyword of series.keywords || []) {
          const keywordMatch = FuzzyMatcher.advancedMatch(searchQuery, keyword, {
            exactWeight: 150,
            fuzzyWeight: 120,
            partialWeight: 100,
            phoneticWeight: 80,
            transposeWeight: 110
          });
          
          if (keywordMatch > bestScore && keywordMatch >= 80) { // Seuil plus élevé pour mots-clés
            bestScore = keywordMatch;
            bestMatch = {
              type: 'keyword_match',
              target: keyword,
              score: keywordMatch
            };
          }
        }
        
        // 5. VALIDATION QUALITÉ DE CORRESPONDANCE
        const matchQuality = FuzzyMatcher.validateMatchQuality(searchQuery, bestMatch?.target || '', 60);
        
        // Si correspondance valide trouvée, ajouter avec score prioritaire
        if (bestMatch && matchQuality.isValid && bestScore >= 50) { // Seuil réduit pour inclure les auteurs
          detectedSeries.push({
            series: series,
            confidence: 100000 + bestScore, // SCORE PRIORITAIRE ABSOLU 100000+
            match_reasons: [bestMatch.type, 'wikipedia_validated', 'advanced_fuzzy'],
            matchType: bestMatch.type,
            originalScore: bestScore,
            matchDetails: `${bestMatch.type} ${bestScore}% avec "${bestMatch.target}"`,
            matchQuality: matchQuality,
            category: categoryKey,
            seriesKey: seriesKey,
            targetMatched: bestMatch.target
          });
        }
      }
    }
    
    // Retourner les séries triées par score de confiance décroissant
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

  // Détection des séries dans la bibliothèque utilisateur - AMÉLIORÉ AVEC AUTEURS
  static detectUserLibrarySeries(query, userBooks) {
    const potentialSeries = {};
    
    userBooks.forEach(book => {
      // 1. DÉTECTION PAR SAGA (existant)
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
      
      // Note : groupement par auteur supprimé — créait de fausses cartes série
      // (ex. chercher "Stephen King" → carte "Livres de Stephen King" au lieu des vrais livres)
    });
    
    return Object.values(potentialSeries)
      .filter(series => series.confidence >= 90000)
      .sort((a, b) => b.confidence - a.confidence);
  }

  // Création d'une carte série avec validation stricte intégrée
  static createSeriesCard(detected, sourceType, userBooks = []) {
    const series = detected.series;
    const isOfficial = sourceType === 'official';
    
    // INTÉGRATION SERIESVALIDATOR - Validation stricte des livres pour cette série
    let validationResults = null;
    if (userBooks.length > 0) {
      validationResults = SeriesValidator.filterBooksForSeries(userBooks, series);
    }
    
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
      description: this.formatSeriesDescription(series, detected, validationResults),
      cover_url: '', // Pas de couverture pour les cartes séries
      
      // Scoring et matching AMÉLIORÉ
      relevanceScore: detected.confidence, // Score 100000+ ou 90000+
      confidence: detected.confidence,
      match_reasons: detected.match_reasons,
      matchType: detected.matchType,
      originalScore: detected.originalScore,
      matchDetails: detected.matchDetails,
      matchQuality: detected.matchQuality || null,
      targetMatched: detected.targetMatched || null,
      
      // Données séries avec validation
      seriesData: series,
      volumes: series.volumes,
      status: series.status,
      first_published: series.first_published,
      validationResults: validationResults,
      
      // Informations de pertinence pour l'affichage ENRICHIES
      relevanceInfo: {
        level: 'prioritaire',
        label: this.getRelevanceLabel(detected),
        color: isOfficial ? 'bg-purple-600' : 'bg-blue-600',
        icon: '📚',
        qualityBadge: this.getQualityBadge(detected),
        validationBadge: validationResults ? this.getValidationBadge(validationResults) : null
      },
      
      // Métadonnées pour navigation
      sourceType: sourceType,
      wikipedia_url: series.wikipedia_url || null,
      translations: series.translations || null
    };
  }

  // Formatage de la description de série avec validation intégrée
  static formatSeriesDescription(series, detected, validationResults = null) {
    const baseDescription = series.description || '';
    const volumeInfo = `${series.volumes} tome(s)`;
    const matchInfo = detected.matchDetails || '';
    const statusInfo = series.status === 'completed' ? '✅ Complète' : '🔄 En cours';
    
    let validationInfo = '';
    if (validationResults) {
      const { validCount, rejectedCount, validationRate } = validationResults;
      validationInfo = ` | 📊 ${validCount} tome(s) validé(s) (${validationRate}%)`;
      if (rejectedCount > 0) {
        validationInfo += ` - ${rejectedCount} exclu(s)`;
      }
    }
    
    return `${baseDescription} | ${volumeInfo} | ${statusInfo} | 🎯 ${matchInfo}${validationInfo}`;
  }

  // Badge de qualité selon la correspondance
  static getQualityBadge(detected) {
    if (!detected.matchQuality) return null;
    
    const confidence = detected.matchQuality.confidence;
    switch (confidence) {
      case 'high':
        return { text: 'Excellente correspondance', color: 'bg-green-500' };
      case 'medium':
        return { text: 'Bonne correspondance', color: 'bg-yellow-500' };
      case 'low':
        return { text: 'Correspondance acceptable', color: 'bg-orange-500' };
      default:
        return { text: 'Correspondance détectée', color: 'bg-gray-500' };
    }
  }

  // Badge de validation stricte
  static getValidationBadge(validationResults) {
    const { validationRate, rejectedCount } = validationResults;
    
    if (validationRate >= 90) {
      return { text: 'Série certifiée', color: 'bg-green-600', icon: '✅' };
    } else if (validationRate >= 70) {
      return { text: 'Majorité validée', color: 'bg-yellow-600', icon: '⚠️' };
    } else if (rejectedCount > validationResults.validCount) {
      return { text: 'Filtrage strict appliqué', color: 'bg-red-600', icon: '🔍' };
    } else {
      return { text: 'Validation partielle', color: 'bg-blue-600', icon: 'ℹ️' };
    }
  }

  // Validation automatisée complète d'une série
  static async validateSeriesComplete(seriesName, books) {
    try {
      const validation = await SeriesValidator.validateWithWikipedia(seriesName, books);
      return validation;
    } catch (error) {
      console.warn(`Validation Wikipedia échouée pour ${seriesName}:`, error);
      return {
        success: false,
        reason: 'validation_error',
        details: error.message
      };
    }
  }



  // Label de pertinence selon le type de correspondance - AMÉLIORÉ AVEC AUTEURS
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
      case 'author_match':
        return 'Série (par auteur)';
      case 'user_library_match':
        return 'Série (votre bibliothèque)';
      case 'user_library_author_match':
        return 'Série (votre auteur)';
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