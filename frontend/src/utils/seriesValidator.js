// Validateur strict pour filtrage des œuvres officielles dans les fiches séries
// OPTIMISATION FILTRAGE STRICT - Validation basée référentiel Wikipedia

import { FuzzyMatcher } from './fuzzyMatcher.js';
import { EXTENDED_SERIES_DATABASE } from './seriesDatabaseExtended.js';

export class SeriesValidator {
  
  // Exclusions strictes universelles
  static UNIVERSAL_EXCLUSIONS = [
    // Génériques
    'guide', 'artbook', 'making of', 'companion', 'encyclopédie', 'dictionary',
    'behind scenes', 'visual guide', 'ultimate guide', 'complete guide',
    
    // Séries dérivées  
    'spin-off', 'spinoff', 'hors-série', 'side story', 'side quest',
    'adaptation', 'suite', 'continuation', 'legacy', 'next generation',
    'prequel', 'sequel', 'reboot', 'remake', 'reimagining',
    
    // Indicateurs non-officiels
    'fan fiction', 'fanfiction', 'unofficial', 'unauthorized', 'parody', 'parodie',
    'inspired by', 'based on', 'd\'après', 'adaptation de', 'tribute',
    'homage', 'pastiche', 'derivative work',
    
    // Médias dérivés
    'movie', 'film', 'tv series', 'television', 'anime adaptation',
    'game', 'jeu vidéo', 'video game', 'board game', 'card game',
    'soundtrack', 'music', 'theme song', 'opening', 'ending',
    
    // Matériel promotionnel
    'promotional', 'promo', 'preview', 'teaser', 'trailer',
    'poster', 'calendar', 'merchandise', 'collectible',
    
    // Formats dérivés
    'light novel', 'web novel', 'audio book', 'audiobook',
    'radio drama', 'podcast', 'drama cd'
  ];

  // Validation par catégorie avec critères spécifiques
  static validateByCategory(book, seriesData) {
    const category = seriesData.category || book.category;
    
    switch (category) {
      case 'roman':
        return this.validateRoman(book, seriesData);
      case 'bd':
        return this.validateBD(book, seriesData);
      case 'manga':
        return this.validateManga(book, seriesData);
      default:
        return this.validateGeneral(book, seriesData);
    }
  }

  // Validation spécifique Romans
  static validateRoman(book, seriesData) {
    const validation = this.validateGeneral(book, seriesData);
    
    if (!validation.isValid) return validation;
    
    // Critères spécifiques aux romans
    const romanExclusions = [
      'graphic novel', 'comic adaptation', 'manga adaptation',
      'illustrated edition', 'children edition', 'young readers',
      'abridged', 'condensed', 'simplified', 'reader digest'
    ];
    
    // Vérifier exclusions spécifiques romans
    const hasRomanExclusion = this.hasExclusionWords(book, romanExclusions);
    if (hasRomanExclusion.found) {
      return {
        isValid: false,
        reason: 'exclusion_roman',
        details: `Exclusion détectée: ${hasRomanExclusion.word}`,
        confidence: 0
      };
    }
    
    // Validation format roman
    if (book.subjects && Array.isArray(book.subjects)) {
      const subjects = book.subjects.join(' ').toLowerCase();
      if (subjects.includes('comic') || subjects.includes('graphic novel')) {
        return {
          isValid: false,
          reason: 'wrong_format',
          details: 'Format BD/Comic détecté dans les sujets',
          confidence: 0
        };
      }
    }
    
    return validation;
  }

  // Validation spécifique BD
  static validateBD(book, seriesData) {
    const validation = this.validateGeneral(book, seriesData);
    
    if (!validation.isValid) return validation;
    
    // Critères spécifiques aux BD
    const bdExclusions = [
      'novel adaptation', 'text version', 'prose version',
      'manga version', 'anime adaptation', 'light novel'
    ];
    
    // Vérifier exclusions spécifiques BD
    const hasBDExclusion = this.hasExclusionWords(book, bdExclusions);
    if (hasBDExclusion.found) {
      return {
        isValid: false,
        reason: 'exclusion_bd',
        details: `Exclusion BD détectée: ${hasBDExclusion.word}`,
        confidence: 0
      };
    }
    
    return validation;
  }

  // Validation spécifique Manga
  static validateManga(book, seriesData) {
    const validation = this.validateGeneral(book, seriesData);
    
    if (!validation.isValid) return validation;
    
    // Critères spécifiques aux mangas
    const mangaExclusions = [
      'light novel', 'web novel', 'novel version',
      'anime guide', 'character book', 'setting book',
      'data book', 'fan book', 'art book', 'illustration book'
    ];
    
    // Vérifier exclusions spécifiques manga
    const hasMangaExclusion = this.hasExclusionWords(book, mangaExclusions);
    if (hasMangaExclusion.found) {
      return {
        isValid: false,
        reason: 'exclusion_manga',
        details: `Exclusion manga détectée: ${hasMangaExclusion.word}`,
        confidence: 0
      };
    }
    
    // Validation auteur japonais pour authentification
    if (seriesData.authors && book.author) {
      const isJapaneseAuthor = this.validateJapaneseAuthor(book.author, seriesData.authors);
      if (!isJapaneseAuthor.isValid) {
        return {
          isValid: false,
          reason: 'author_mismatch_manga',
          details: 'Auteur non japonais ou non reconnu pour cette série manga',
          confidence: 0
        };
      }
    }
    
    return validation;
  }

  // Validation générale (critères communs)
  static validateGeneral(book, seriesData) {
    // 1. Correspondance exacte du nom de série
    const seriesMatch = this.validateSeriesName(book, seriesData);
    if (!seriesMatch.isValid) return seriesMatch;
    
    // 2. Validation des auteurs originaux
    const authorMatch = this.validateOriginalAuthors(book, seriesData);
    if (!authorMatch.isValid) return authorMatch;
    
    // 3. Vérification des exclusions universelles
    const exclusionCheck = this.hasExclusionWords(book, this.UNIVERSAL_EXCLUSIONS);
    if (exclusionCheck.found) {
      return {
        isValid: false,
        reason: 'universal_exclusion',
        details: `Exclusion universelle détectée: ${exclusionCheck.word}`,
        confidence: 0
      };
    }
    
    // 4. Vérification des exclusions spécifiques à la série
    if (seriesData.exclusions && seriesData.exclusions.length > 0) {
      const seriesExclusion = this.hasExclusionWords(book, seriesData.exclusions);
      if (seriesExclusion.found) {
        return {
          isValid: false,
          reason: 'series_exclusion',
          details: `Exclusion série détectée: ${seriesExclusion.word}`,
          confidence: 0
        };
      }
    }
    
    // 5. Validation du titre contient le nom de la série
    const titleMatch = this.validateTitleContainsSeries(book, seriesData);
    
    // Calcul de la confiance finale
    const confidence = this.calculateConfidence(seriesMatch, authorMatch, titleMatch);
    
    return {
      isValid: true,
      reason: 'validated',
      details: 'Livre validé pour cette série',
      confidence: confidence,
      matches: {
        series: seriesMatch,
        author: authorMatch,
        title: titleMatch
      }
    };
  }

  // Validation du nom de série exact
  static validateSeriesName(book, seriesData) {
    const bookSaga = FuzzyMatcher.normalizeString(book.saga || '');
    const seriesName = FuzzyMatcher.normalizeString(seriesData.name);
    
    // Correspondance exacte préférée
    if (bookSaga === seriesName) {
      return { isValid: true, score: 100, type: 'exact' };
    }
    
    // Correspondance avec variations officielles
    for (const variation of seriesData.variations || []) {
      const normalizedVariation = FuzzyMatcher.normalizeString(variation);
      if (bookSaga === normalizedVariation || bookSaga.includes(normalizedVariation)) {
        return { isValid: true, score: 90, type: 'variation' };
      }
    }
    
    // Correspondance floue tolérante (max 2 erreurs)
    const fuzzyScore = FuzzyMatcher.fuzzyMatch(bookSaga, seriesName, 2);
    if (fuzzyScore >= 85) {
      return { isValid: true, score: fuzzyScore, type: 'fuzzy' };
    }
    
    return { 
      isValid: false, 
      score: fuzzyScore, 
      type: 'no_match',
      details: `Saga "${book.saga}" ne correspond pas à "${seriesData.name}"`
    };
  }

  // Validation des auteurs originaux uniquement
  static validateOriginalAuthors(book, seriesData) {
    if (!book.author || !seriesData.authors || seriesData.authors.length === 0) {
      return { isValid: false, score: 0, type: 'missing_data' };
    }
    
    const bookAuthor = FuzzyMatcher.normalizeString(book.author);
    
    // Vérifier correspondance avec auteurs originaux
    for (const originalAuthor of seriesData.authors) {
      const normalizedOriginal = FuzzyMatcher.normalizeString(originalAuthor);
      
      // Correspondance exacte
      if (bookAuthor === normalizedOriginal) {
        return { isValid: true, score: 100, type: 'exact_author' };
      }
      
      // Correspondance partielle (nom de famille au minimum)
      if (bookAuthor.includes(normalizedOriginal) || normalizedOriginal.includes(bookAuthor)) {
        return { isValid: true, score: 80, type: 'partial_author' };
      }
      
      // Correspondance floue tolérante
      const fuzzyScore = FuzzyMatcher.fuzzyMatch(bookAuthor, normalizedOriginal, 2);
      if (fuzzyScore >= 75) {
        return { isValid: true, score: fuzzyScore, type: 'fuzzy_author' };
      }
    }
    
    return { 
      isValid: false, 
      score: 0, 
      type: 'author_mismatch',
      details: `Auteur "${book.author}" ne correspond à aucun auteur original`
    };
  }

  // Validation que le titre contient le nom de la série
  static validateTitleContainsSeries(book, seriesData) {
    if (!book.title) {
      return { isValid: false, score: 0, type: 'missing_title' };
    }
    
    const bookTitle = FuzzyMatcher.normalizeString(book.title);
    const seriesName = FuzzyMatcher.normalizeString(seriesData.name);
    
    // Titre contient le nom de la série
    if (bookTitle.includes(seriesName)) {
      return { isValid: true, score: 100, type: 'title_contains' };
    }
    
    // Titre contient une variation de la série
    for (const variation of seriesData.variations || []) {
      const normalizedVariation = FuzzyMatcher.normalizeString(variation);
      if (bookTitle.includes(normalizedVariation)) {
        return { isValid: true, score: 90, type: 'title_variation' };
      }
    }
    
    return { 
      isValid: false, 
      score: 0, 
      type: 'title_mismatch',
      details: `Titre "${book.title}" ne contient pas "${seriesData.name}"`
    };
  }

  // Vérification des mots d'exclusion
  static hasExclusionWords(book, exclusions) {
    const searchText = [
      book.title || '',
      book.description || '',
      book.subtitle || '',
      (book.subjects || []).join(' ')
    ].join(' ').toLowerCase();
    
    for (const exclusion of exclusions) {
      if (searchText.includes(exclusion.toLowerCase())) {
        return { found: true, word: exclusion };
      }
    }
    
    return { found: false, word: null };
  }

  // Validation spécifique auteur japonais
  static validateJapaneseAuthor(bookAuthor, seriesAuthors) {
    const japaneseNamePatterns = [
      /^[a-z]+ [a-z]+$/i, // Format occidental: "prénom nom"
      /^[a-z]+$/i,        // Nom unique
      /.*[aeiou]{2,}.*$/i  // Voyelles multiples (caractéristique japonaise romanisée)
    ];
    
    const normalizedBookAuthor = FuzzyMatcher.normalizeString(bookAuthor);
    
    // Vérifier si l'auteur du livre correspond aux auteurs de la série
    for (const seriesAuthor of seriesAuthors) {
      const normalizedSeriesAuthor = FuzzyMatcher.normalizeString(seriesAuthor);
      
      if (normalizedBookAuthor === normalizedSeriesAuthor) {
        return { isValid: true, type: 'exact_match' };
      }
      
      // Correspondance partielle pour gestion des prénoms/noms
      const bookParts = normalizedBookAuthor.split(' ');
      const seriesParts = normalizedSeriesAuthor.split(' ');
      
      // Au moins un nom en commun
      const hasCommonName = bookParts.some(bp => 
        seriesParts.some(sp => bp === sp && bp.length > 2)
      );
      
      if (hasCommonName) {
        return { isValid: true, type: 'partial_match' };
      }
    }
    
    return { 
      isValid: false, 
      type: 'author_mismatch',
      details: `Auteur "${bookAuthor}" ne correspond à aucun auteur reconnu`
    };
  }

  // Calcul de la confiance finale
  static calculateConfidence(seriesMatch, authorMatch, titleMatch) {
    let confidence = 0;
    
    // Pondération des critères
    if (seriesMatch.isValid) {
      confidence += seriesMatch.score * 0.4; // 40% pour la série
    }
    
    if (authorMatch.isValid) {
      confidence += authorMatch.score * 0.4; // 40% pour l'auteur
    }
    
    if (titleMatch.isValid) {
      confidence += titleMatch.score * 0.2; // 20% pour le titre
    }
    
    return Math.round(confidence);
  }

  // Filtrage strict complet pour une série
  static filterBooksForSeries(books, seriesData) {
    const validBooks = [];
    const rejectedBooks = [];
    
    for (const book of books) {
      const validation = this.validateByCategory(book, seriesData);
      
      if (validation.isValid && validation.confidence >= 60) {
        validBooks.push({
          ...book,
          validation: validation
        });
      } else {
        rejectedBooks.push({
          ...book,
          rejection: validation
        });
      }
    }
    
    return {
      validBooks: validBooks.sort((a, b) => 
        (b.validation.confidence || 0) - (a.validation.confidence || 0)
      ),
      rejectedBooks,
      totalBooks: books.length,
      validCount: validBooks.length,
      rejectedCount: rejectedBooks.length,
      validationRate: Math.round((validBooks.length / books.length) * 100)
    };
  }

  // Validation automatisée basée sur Wikipedia
  static async validateWithWikipedia(seriesName, books) {
    // Cette méthode pourrait être étendue pour intégrer l'API Wikipedia
    // Pour l'instant, utilise la base de données locale
    
    const seriesData = this.findSeriesInDatabase(seriesName);
    if (!seriesData) {
      return {
        success: false,
        reason: 'series_not_found',
        details: `Série "${seriesName}" non trouvée dans la base de données`
      };
    }
    
    return {
      success: true,
      validation: this.filterBooksForSeries(books, seriesData),
      seriesData: seriesData
    };
  }

  // Recherche d'une série dans la base de données étendue
  static findSeriesInDatabase(seriesName) {
    const normalizedSearch = FuzzyMatcher.normalizeString(seriesName);
    
    for (const category of Object.values(EXTENDED_SERIES_DATABASE)) {
      for (const series of Object.values(category)) {
        // Correspondance exacte du nom
        if (FuzzyMatcher.normalizeString(series.name) === normalizedSearch) {
          return series;
        }
        
        // Correspondance avec variations
        for (const variation of series.variations || []) {
          if (FuzzyMatcher.normalizeString(variation) === normalizedSearch) {
            return series;
          }
        }
      }
    }
    
    return null;
  }
}

export default SeriesValidator;