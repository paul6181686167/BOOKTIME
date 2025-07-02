// Algorithme de correspondance floue avec tolérance orthographique avancée
// OPTIMISATION RECHERCHE TOLÉRANTE - Extension universelle toutes séries populaires

export class FuzzyMatcher {
  
  // Normalisation de chaîne avec suppression accents et caractères spéciaux
  static normalizeString(str) {
    if (!str) return '';
    return str
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '') // Supprimer accents
      .replace(/[^\w\s]/g, ' ') // Remplacer ponctuation par espaces
      .replace(/\s+/g, ' ') // Normaliser espaces multiples
      .trim();
  }

  // Distance de Levenshtein optimisée
  static levenshteinDistance(str1, str2) {
    const matrix = Array(str2.length + 1).fill(null)
      .map(() => Array(str1.length + 1).fill(null));

    for (let i = 0; i <= str1.length; i++) matrix[0][i] = i;
    for (let j = 0; j <= str2.length; j++) matrix[j][0] = j;

    for (let j = 1; j <= str2.length; j++) {
      for (let i = 1; i <= str1.length; i++) {
        const indicator = str1[i - 1] === str2[j - 1] ? 0 : 1;
        matrix[j][i] = Math.min(
          matrix[j][i - 1] + 1,     // insertion
          matrix[j - 1][i] + 1,     // deletion
          matrix[j - 1][i - 1] + indicator // substitution
        );
      }
    }

    return matrix[str2.length][str1.length];
  }

  // Correspondance floue avec pourcentage de similarité
  static fuzzyMatch(str1, str2, maxErrors = 4) {
    const normalized1 = this.normalizeString(str1);
    const normalized2 = this.normalizeString(str2);
    
    if (normalized1 === normalized2) return 100;
    if (!normalized1 || !normalized2) return 0;
    
    const distance = this.levenshteinDistance(normalized1, normalized2);
    const maxLength = Math.max(normalized1.length, normalized2.length);
    
    if (distance > maxErrors) return 0;
    
    const similarity = ((maxLength - distance) / maxLength) * 100;
    return Math.round(similarity);
  }

  // Correspondance phonétique simplifiée (Soundex-like)
  static phoneticMatch(str1, str2) {
    const phonetic1 = this.getPhoneticCode(str1);
    const phonetic2 = this.getPhoneticCode(str2);
    
    return this.levenshteinDistance(phonetic1, phonetic2);
  }

  // Code phonétique simplifié
  static getPhoneticCode(str) {
    const normalized = this.normalizeString(str);
    return normalized
      .replace(/[aeiouy]/g, '') // Supprimer voyelles
      .replace(/[bp]/g, '1')
      .replace(/[fv]/g, '2')
      .replace(/[cgjkqsxz]/g, '3')
      .replace(/[dt]/g, '4')
      .replace(/[lr]/g, '5')
      .replace(/[mn]/g, '6')
      .replace(/h/g, '')
      .replace(/(.)\1+/g, '$1') // Supprimer doublons
      .substring(0, 4)
      .padEnd(4, '0');
  }

  // Correspondance partielle avec mots
  static partialWordMatch(query, target) {
    const queryWords = this.normalizeString(query).split(' ').filter(w => w.length > 1);
    const targetNormalized = this.normalizeString(target);
    
    if (queryWords.length === 0) return 0;
    
    let matchedWords = 0;
    for (const word of queryWords) {
      if (targetNormalized.includes(word)) {
        matchedWords++;
      }
    }
    
    return Math.round((matchedWords / queryWords.length) * 100);
  }

  // Correspondance par inversion de caractères
  static transposeMatch(str1, str2) {
    const normalized1 = this.normalizeString(str1);
    const normalized2 = this.normalizeString(str2);
    
    if (Math.abs(normalized1.length - normalized2.length) > 2) return 0;
    
    // Générer des variations avec transpositions simples
    const variations = this.generateTranspositions(normalized1);
    
    for (const variation of variations) {
      if (variation === normalized2) return 95;
      if (this.levenshteinDistance(variation, normalized2) <= 1) return 85;
    }
    
    return 0;
  }

  // Générer variations avec transpositions de caractères adjacents
  static generateTranspositions(str) {
    const variations = [];
    
    for (let i = 0; i < str.length - 1; i++) {
      const chars = str.split('');
      [chars[i], chars[i + 1]] = [chars[i + 1], chars[i]];
      variations.push(chars.join(''));
    }
    
    return variations;
  }

  // Correspondance multi-critères avancée
  static advancedMatch(query, target, options = {}) {
    const {
      exactWeight = 100,
      fuzzyWeight = 80,
      partialWeight = 60,
      phoneticWeight = 40,
      transposeWeight = 75
    } = options;

    const scores = [];

    // 1. Correspondance exacte
    if (this.normalizeString(query) === this.normalizeString(target)) {
      scores.push(exactWeight);
    }

    // 2. Correspondance floue
    const fuzzyScore = this.fuzzyMatch(query, target, 3);
    if (fuzzyScore >= 70) {
      scores.push(Math.round((fuzzyScore / 100) * fuzzyWeight));
    }

    // 3. Correspondance partielle par mots
    const partialScore = this.partialWordMatch(query, target);
    if (partialScore >= 50) {
      scores.push(Math.round((partialScore / 100) * partialWeight));
    }

    // 4. Correspondance phonétique
    const phoneticDistance = this.phoneticMatch(query, target);
    if (phoneticDistance <= 2) {
      const phoneticScore = Math.max(0, phoneticWeight - (phoneticDistance * 10));
      scores.push(phoneticScore);
    }

    // 5. Correspondance avec transpositions
    const transposeScore = this.transposeMatch(query, target);
    if (transposeScore > 0) {
      scores.push(Math.round((transposeScore / 100) * transposeWeight));
    }

    // Retourner le meilleur score
    return scores.length > 0 ? Math.max(...scores) : 0;
  }

  // Test de correspondance avec seuils configurables
  static testMatch(query, target, thresholds = {}) {
    const {
      excellent = 90,
      good = 75,
      acceptable = 60,
      minimal = 40
    } = thresholds;

    const score = this.advancedMatch(query, target);

    return {
      score,
      match: score >= minimal,
      quality: score >= excellent ? 'excellent' :
               score >= good ? 'good' :
               score >= acceptable ? 'acceptable' :
               score >= minimal ? 'minimal' : 'none'
    };
  }

  // Correspondances linguistiques par langue
  static checkLinguisticVariations(query, seriesKey, variations) {
    const normalized = this.normalizeString(query);
    
    // Variations françaises courantes
    const frenchVariations = {
      'seigneur_anneaux': ['seigneur des anneaux', 'seigneurs des anneaux', 'seigneur anneau', 'sda'],
      'game_of_thrones': ['game of throne', 'games of thrones', 'trône de fer', 'trone de fer', 'got'],
      'attack_on_titan': ['attaque titans', 'attaque des titan', 'attaque des titans', 'shingeki no kyojin'],
      'harry_potter': ['herry potter', 'harry poter', 'harrypotter', 'potter', 'hp'],
      'one_piece': ['one pece', 'onepiece', 'wan pisu'],
      'dragon_ball': ['dragonball', 'dragon bal', 'doragon boru'],
      'asterix': ['asterix', 'astérics', 'asterics', 'astérik'],
      'tintin': ['tin tin', 'tentin', 'ten ten'],
      'naruto': ['narutoo', 'narotto', 'narouto']
    };

    // Vérifier variations spécifiques à cette série
    const seriesVariations = frenchVariations[seriesKey] || [];
    const allVariations = [...variations, ...seriesVariations];

    let bestScore = 0;
    for (const variation of allVariations) {
      const score = this.advancedMatch(normalized, variation);
      bestScore = Math.max(bestScore, score);
    }

    return bestScore;
  }

  // Validation de qualité de correspondance
  static validateMatchQuality(query, target, minScore = 60) {
    const result = this.testMatch(query, target);
    
    return {
      isValid: result.score >= minScore,
      score: result.score,
      quality: result.quality,
      confidence: result.score >= 90 ? 'high' :
                  result.score >= 75 ? 'medium' :
                  result.score >= 60 ? 'low' : 'very_low'
    };
  }
}