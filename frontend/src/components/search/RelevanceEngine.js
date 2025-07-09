/**
 * RelevanceEngine - Moteur de calcul de pertinence pour la recherche BOOKTIME
 * Extrait de App.js pour améliorer la modularité
 * 
 * Fonctionnalités :
 * - Détection intelligente des séries populaires
 * - Calcul de score de pertinence basé sur la popularité
 * - Correspondances exactes et approximatives
 * - Bonus pour livres locaux et métadonnées de qualité
 */

// Mapping complet des séries populaires avec leurs variations et auteurs
const SERIES_MAPPING = {
  // === ROMANS FANTASY/SF ===
  'harry potter': {
    score: 18000,
    category: 'roman',
    keywords: ['harry', 'potter', 'hogwarts', 'sorcier', 'wizard', 'poudlard', 'voldemort', 'hermione', 'ron', 'dumbledore'],
    authors: ['j.k. rowling', 'jk rowling', 'rowling'],
    variations: ['harry potter', 'école des sorciers', 'chambre des secrets', 'prisonnier d\'azkaban', 'coupe de feu', 'ordre du phénix', 'prince de sang-mêlé', 'reliques de la mort'],
    volumes: 7,
    language: ['fr', 'en']
  },
  'seigneur des anneaux': {
    score: 18000,
    category: 'roman',
    keywords: ['anneau', 'communauté', 'deux tours', 'retour du roi', 'terre du milieu', 'middle earth', 'hobbit', 'frodo', 'gandalf', 'aragorn', 'legolas', 'gimli'],
    authors: ['j.r.r. tolkien', 'jrr tolkien', 'tolkien'],
    variations: ['seigneur des anneaux', 'lord of the rings', 'communauté de l\'anneau', 'fellowship', 'deux tours', 'two towers', 'retour du roi', 'return of the king', 'hobbit'],
    volumes: 3,
    language: ['fr', 'en']
  },
  'game of thrones': {
    score: 16000,
    category: 'roman',
    keywords: ['game of thrones', 'trône de fer', 'westeros', 'jon snow', 'daenerys', 'tyrion', 'stark', 'lannister', 'targaryen'],
    authors: ['george r.r. martin', 'george martin', 'martin'],
    variations: ['game of thrones', 'trône de fer', 'song of ice and fire', 'chanson de glace et de feu'],
    volumes: 5,
    language: ['fr', 'en']
  },
  'witcher': {
    score: 15000,
    category: 'roman',
    keywords: ['witcher', 'sorceleur', 'geralt', 'rivia', 'ciri', 'yennefer', 'triss'],
    authors: ['andrzej sapkowski', 'sapkowski'],
    variations: ['witcher', 'sorceleur', 'geralt de rivia'],
    volumes: 8,
    language: ['fr', 'en', 'pl']
  },
  'dune': {
    score: 16000,
    category: 'roman',
    keywords: ['dune', 'arrakis', 'paul atreides', 'fremen', 'spice', 'épice', 'muad\'dib'],
    authors: ['frank herbert', 'herbert'],
    variations: ['dune', 'cycle de dune'],
    volumes: 6,
    language: ['fr', 'en']
  },

  // === MANGAS ===
  'one piece': {
    score: 18000,
    category: 'manga',
    keywords: ['one piece', 'luffy', 'zoro', 'sanji', 'pirates', 'chapeau de paille', 'grand line', 'nami', 'usopp', 'chopper'],
    authors: ['eiichiro oda', 'oda'],
    variations: ['one piece'],
    volumes: 100,
    language: ['fr', 'en', 'jp']
  },
  'naruto': {
    score: 17000,
    category: 'manga',
    keywords: ['naruto', 'sasuke', 'sakura', 'kakashi', 'ninja', 'konoha', 'sharingan', 'hokage', 'boruto'],
    authors: ['masashi kishimoto', 'kishimoto'],
    variations: ['naruto', 'boruto'],
    volumes: 72,
    language: ['fr', 'en', 'jp']
  },
  'dragon ball': {
    score: 17000,
    category: 'manga',
    keywords: ['dragon ball', 'goku', 'vegeta', 'kamehameha', 'saiyan', 'piccolo', 'gohan', 'frieza', 'cell'],
    authors: ['akira toriyama', 'toriyama'],
    variations: ['dragon ball', 'dragonball', 'dragon ball z', 'dragon ball super'],
    volumes: 42,
    language: ['fr', 'en', 'jp']
  },
  'attack on titan': {
    score: 16000,
    category: 'manga',
    keywords: ['attack on titan', 'attaque des titans', 'eren', 'mikasa', 'armin', 'titans', 'murs', 'shingeki no kyojin'],
    authors: ['hajime isayama', 'isayama'],
    variations: ['attack on titan', 'attaque des titans', 'shingeki no kyojin'],
    volumes: 34,
    language: ['fr', 'en', 'jp']
  },
  'death note': {
    score: 15000,
    category: 'manga',
    keywords: ['death note', 'light', 'l', 'kira', 'ryuk', 'shinigami', 'yagami'],
    authors: ['tsugumi ohba', 'takeshi obata', 'ohba', 'obata'],
    variations: ['death note'],
    volumes: 12,
    language: ['fr', 'en', 'jp']
  },
  'bleach': {
    score: 15000,
    category: 'manga',
    keywords: ['bleach', 'ichigo', 'rukia', 'shinigami', 'hollow', 'soul society', 'zanpakuto'],
    authors: ['tite kubo', 'kubo'],
    variations: ['bleach'],
    volumes: 74,
    language: ['fr', 'en', 'jp']
  },
  'fullmetal alchemist': {
    score: 15000,
    category: 'manga',
    keywords: ['fullmetal alchemist', 'edward elric', 'alphonse', 'alchemy', 'alchimie', 'philosopher stone'],
    authors: ['hiromu arakawa', 'arakawa'],
    variations: ['fullmetal alchemist', 'full metal alchemist'],
    volumes: 27,
    language: ['fr', 'en', 'jp']
  },
  'demon slayer': {
    score: 16000,
    category: 'manga',
    keywords: ['demon slayer', 'kimetsu no yaiba', 'tanjiro', 'nezuko', 'demons', 'hashira'],
    authors: ['koyoharu gotouge', 'gotouge'],
    variations: ['demon slayer', 'kimetsu no yaiba'],
    volumes: 23,
    language: ['fr', 'en', 'jp']
  },
  'my hero academia': {
    score: 15000,
    category: 'manga',
    keywords: ['my hero academia', 'boku no hero', 'midoriya', 'deku', 'quirk', 'all might', 'bakugo'],
    authors: ['kohei horikoshi', 'horikoshi'],
    variations: ['my hero academia', 'boku no hero academia'],
    volumes: 35,
    language: ['fr', 'en', 'jp']
  },

  // === BANDES DESSINÉES ===
  'astérix': {
    score: 18000,
    category: 'bd',
    keywords: ['astérix', 'asterix', 'obélix', 'obelix', 'gaulois', 'potion magique', 'panoramix', 'idéfix'],
    authors: ['rené goscinny', 'albert uderzo', 'goscinny', 'uderzo'],
    variations: ['astérix', 'asterix'],
    volumes: 39,
    language: ['fr', 'en']
  },
  'tintin': {
    score: 18000,
    category: 'bd',
    keywords: ['tintin', 'milou', 'capitaine haddock', 'tournesol', 'dupont', 'dupond', 'mille sabords'],
    authors: ['hergé', 'herge'],
    variations: ['tintin', 'aventures de tintin'],
    volumes: 24,
    language: ['fr', 'en']
  },
  'gaston lagaffe': {
    score: 15000,
    category: 'bd',
    keywords: ['gaston', 'lagaffe', 'spirou', 'fantasio', 'prunelle', 'longtarin'],
    authors: ['andré franquin', 'franquin'],
    variations: ['gaston lagaffe', 'gaston'],
    volumes: 19,
    language: ['fr']
  },
  'lucky luke': {
    score: 15000,
    category: 'bd',
    keywords: ['lucky luke', 'dalton', 'jolly jumper', 'rantanplan', 'cowboy', 'western'],
    authors: ['morris', 'rené goscinny', 'goscinny'],
    variations: ['lucky luke'],
    volumes: 70,
    language: ['fr', 'en']
  },
  'spirou': {
    score: 15000,
    category: 'bd',
    keywords: ['spirou', 'fantasio', 'marsupilami', 'spip', 'zorglub', 'champignac'],
    authors: ['andré franquin', 'franquin', 'rob-vel'],
    variations: ['spirou et fantasio', 'spirou'],
    volumes: 55,
    language: ['fr']
  },
  'thorgal': {
    score: 14000,
    category: 'bd',
    keywords: ['thorgal', 'aaricia', 'jolan', 'louve', 'viking', 'nordique'],
    authors: ['jean van hamme', 'grzegorz rosinski', 'van hamme', 'rosinski'],
    variations: ['thorgal'],
    volumes: 38,
    language: ['fr']
  },
  'xiii': {
    score: 14000,
    category: 'bd',
    keywords: ['xiii', 'treize', 'jason fly', 'conspiracy', 'conspiration'],
    authors: ['jean van hamme', 'william vance', 'van hamme', 'vance'],
    variations: ['xiii', 'treize'],
    volumes: 27,
    language: ['fr', 'en']
  },
  'blake et mortimer': {
    score: 14000,
    category: 'bd',
    keywords: ['blake', 'mortimer', 'francis blake', 'philip mortimer', 'jacobs'],
    authors: ['edgar p. jacobs', 'jacobs'],
    variations: ['blake et mortimer', 'blake mortimer'],
    volumes: 27,
    language: ['fr', 'en']
  },

  // === COMICS AMÉRICAINS ===
  'batman': {
    score: 16000,
    category: 'bd',
    keywords: ['batman', 'bruce wayne', 'gotham', 'joker', 'robin', 'alfred', 'dark knight'],
    authors: ['dc comics', 'bob kane', 'bill finger'],
    variations: ['batman', 'dark knight', 'chevalier noir'],
    volumes: 1000,
    language: ['fr', 'en']
  },
  'superman': {
    score: 16000,
    category: 'bd',
    keywords: ['superman', 'clark kent', 'metropolis', 'lois lane', 'lex luthor', 'kryptonite'],
    authors: ['dc comics', 'jerry siegel', 'joe shuster'],
    variations: ['superman', 'man of steel'],
    volumes: 1000,
    language: ['fr', 'en']
  },
  'spider-man': {
    score: 16000,
    category: 'bd',
    keywords: ['spider-man', 'spiderman', 'peter parker', 'new york', 'web', 'toile'],
    authors: ['marvel comics', 'stan lee', 'steve ditko'],
    variations: ['spider-man', 'spiderman', 'amazing spider-man'],
    volumes: 1000,
    language: ['fr', 'en']
  },
  'x-men': {
    score: 15000,
    category: 'bd',
    keywords: ['x-men', 'wolverine', 'cyclops', 'storm', 'xavier', 'magneto', 'mutants'],
    authors: ['marvel comics', 'stan lee', 'jack kirby'],
    variations: ['x-men', 'uncanny x-men'],
    volumes: 1000,
    language: ['fr', 'en']
  },
  'walking dead': {
    score: 15000,
    category: 'bd',
    keywords: ['walking dead', 'rick grimes', 'zombies', 'walkers', 'apocalypse'],
    authors: ['robert kirkman', 'kirkman'],
    variations: ['walking dead'],
    volumes: 193,
    language: ['fr', 'en']
  },

  // === ROMANS POLICIERS ===
  'sherlock holmes': {
    score: 16000,
    category: 'roman',
    keywords: ['sherlock holmes', 'watson', 'baker street', 'moriarty', 'london', 'detective'],
    authors: ['arthur conan doyle', 'conan doyle', 'doyle'],
    variations: ['sherlock holmes', 'adventures of sherlock holmes'],
    volumes: 60,
    language: ['fr', 'en']
  },
  'hercule poirot': {
    score: 15000,
    category: 'roman',
    keywords: ['hercule poirot', 'agatha christie', 'orient express', 'nil', 'belgian', 'detective'],
    authors: ['agatha christie', 'christie'],
    variations: ['hercule poirot', 'poirot'],
    volumes: 39,
    language: ['fr', 'en']
  },
  'san antonio': {
    score: 14000,
    category: 'roman',
    keywords: ['san antonio', 'bérurier', 'pinaud', 'police', 'commissaire'],
    authors: ['frédéric dard', 'dard'],
    variations: ['san antonio', 'san-antonio'],
    volumes: 175,
    language: ['fr']
  }
};

// Mots-clés génériquement populaires (fallback)
const GENERAL_POPULAR_KEYWORDS = [
  // Comics/BD supplémentaires
  'wolverine', 'deadpool', 'iron man', 'captain america', 'hulk', 'thor', 'avengers',
  'wonder woman', 'flash', 'green lantern', 'aquaman', 'justice league',
  'sandman', 'watchmen', 'v for vendetta', 'hellboy', 'spawn',
  
  // Mangas supplémentaires
  'one punch man', 'tokyo ghoul', 'fairy tail', 'black clover', 'jujutsu kaisen',
  'chainsaw man', 'mob psycho', 'hunter x hunter', 'yu yu hakusho',
  'cowboy bebop', 'akira', 'ghost in the shell', 'evangelion',
  
  // Romans supplémentaires
  'percy jackson', 'twilight', 'hunger games', 'divergent', 'maze runner',
  'outlander', 'fifty shades', 'dark tower', 'foundation', 'hyperion',
  'mistborn', 'wheel of time', 'chronicles of narnia', 'his dark materials',
  
  // BD franco-belges supplémentaires
  'largo winch', 'blacksad', 'corto maltese', 'lanfeust', 'trolls de troy',
  'donjon', 'dungeon', 'bone', 'fables', 'saga', 'invincible',
  
  // Classiques
  'james bond', 'indiana jones', 'conan', 'tarzan', 'flash gordon',
  'buck rogers', 'phantom', 'prince valiant', 'dick tracy'
];

/**
 * Détecte si un livre appartient à une série populaire
 * @param {string} searchQuery - Terme de recherche
 * @returns {Object|null} - Informations sur la série détectée ou null
 */
function detectSeries(searchQuery) {
  const query = searchQuery.toLowerCase();
  
  for (const [seriesName, seriesData] of Object.entries(SERIES_MAPPING)) {
    // Vérification directe du nom de série dans la requête
    if (query.includes(seriesName)) {
      return { series: seriesName, data: seriesData, confidence: 'high' };
    }
    
    // Vérification des variations
    for (const variation of seriesData.variations) {
      if (query.includes(variation)) {
        return { series: seriesName, data: seriesData, confidence: 'high' };
      }
    }
  }
  
  return null;
}

/**
 * Vérifie si un livre correspond à une série spécifique
 * @param {Object} book - Livre à vérifier
 * @param {string} seriesName - Nom de la série
 * @param {Object} seriesData - Données de la série
 * @returns {number} - Score de confiance de correspondance
 */
function isBookInSeries(book, seriesName, seriesData) {
  const bookTitle = (book.title || '').toLowerCase();
  const bookAuthor = (book.author || '').toLowerCase();
  const bookSaga = (book.saga || '').toLowerCase();
  const bookCategory = (book.category || '').toLowerCase();
  
  let confidence = 0;
  
  // Vérification par saga (le plus fiable)
  if (bookSaga.includes(seriesName) || seriesData.variations.some(v => bookSaga.includes(v))) {
    confidence += 100;
  }
  
  // Vérification par auteur (très fiable pour les séries uniques)
  if (seriesData.authors.some(author => bookAuthor.includes(author))) {
    confidence += 90;
  }
  
  // Bonus pour correspondance de catégorie
  if (seriesData.category && bookCategory === seriesData.category) {
    confidence += 20;
  }
  
  // Vérification par mots-clés dans le titre
  let keywordMatches = 0;
  seriesData.keywords.forEach(keyword => {
    if (bookTitle.includes(keyword)) {
      keywordMatches++;
    }
  });
  
  if (keywordMatches > 0) {
    confidence += keywordMatches * 25; // Réduction du score pour éviter les faux positifs
  }
  
  // Vérification par variations dans le titre (très importante)
  seriesData.variations.forEach(variation => {
    if (bookTitle.includes(variation)) {
      confidence += 70;
    }
  });
  
  // Bonus pour titre exact ou quasi-exact
  if (seriesData.variations.some(variation => bookTitle === variation || bookTitle.startsWith(variation))) {
    confidence += 50;
  }
  
  // Vérification des langues supportées
  if (seriesData.language && book.language) {
    if (seriesData.language.includes(book.language)) {
      confidence += 10;
    }
  }
  
  return confidence;
}

/**
 * Calcule le score de pertinence d'un livre par rapport à un terme de recherche
 * @param {Object} book - Livre à évaluer
 * @param {string} searchTerm - Terme de recherche
 * @returns {number} - Score de pertinence (0 à 100000+)
 */
export function calculateRelevanceScore(book, searchTerm) {
  if (!searchTerm || !searchTerm.trim()) return 0;
  
  const term = searchTerm.toLowerCase().trim();
  const termWords = term.split(/\s+/).filter(word => word.length > 1);
  
  // Normalisation des champs de recherche
  const title = (book.title || '').toLowerCase();
  const author = (book.author || '').toLowerCase();
  const saga = (book.saga || '').toLowerCase();
  
  let score = 0;
  
  // === DÉTECTION INTELLIGENTE DES SÉRIES POPULAIRES ===
  
  // Détecter si la recherche concerne une série populaire
  const detectedSeries = detectSeries(term);
  
  let matchScore = 0;
  let popularityBonus = 0;
  
  if (detectedSeries) {
    const { series, data } = detectedSeries;
    
    // Vérifier si ce livre appartient à la série recherchée
    const seriesConfidence = isBookInSeries(book, series, data);
    
    if (seriesConfidence >= 100) {
      // Livre confirmé de la série (par saga ou auteur + mots-clés)
      popularityBonus = data.score;
      matchScore = 40000; // Score très élevé pour les vrais livres de la série
    } else if (seriesConfidence >= 80) {
      // Livre probable de la série
      popularityBonus = data.score * 0.8;
      matchScore = 30000;
    } else if (seriesConfidence >= 50) {
      // Livre possible de la série
      popularityBonus = data.score * 0.5;
      matchScore = 20000;
    }
  }
  
  // === CORRESPONDANCES EXACTES CLASSIQUES ===
  
  // Si pas de série détectée ou score faible, utiliser la correspondance classique
  if (matchScore < 20000) {
    // Correspondance exacte complète
    if (title === term) {
      matchScore = Math.max(matchScore, 35000);
    }
    // Correspondance de séquence complète
    else if (title.includes(term)) {
      if (title.startsWith(term)) {
        matchScore = Math.max(matchScore, 25000);
      } else {
        matchScore = Math.max(matchScore, 18000);
      }
    }
    // Multi-mots : tous les mots présents
    else if (termWords.length > 1) {
      let wordsFound = 0;
      termWords.forEach(word => {
        if (title.includes(word)) wordsFound++;
      });
      
      const completeness = wordsFound / termWords.length;
      if (completeness === 1) {
        matchScore = Math.max(matchScore, 15000); // Tous les mots trouvés
      } else if (completeness >= 0.8) {
        matchScore = Math.max(matchScore, 12000); // 80%+ des mots
      } else if (completeness >= 0.6) {
        matchScore = Math.max(matchScore, 8000);  // 60%+ des mots
      } else if (completeness >= 0.4) {
        matchScore = Math.max(matchScore, 5000);  // 40%+ des mots
      }
    }
    // Mot simple
    else {
      if (title.startsWith(term)) {
        matchScore = Math.max(matchScore, 8000);
      } else if (title.includes(` ${term} `) || title.includes(`${term} `) || title.includes(` ${term}`)) {
        matchScore = Math.max(matchScore, 6000); // Mot entier
      } else if (title.includes(term)) {
        matchScore = Math.max(matchScore, 4000); // Contient le mot
      }
    }
  }
  
  // Correspondances dans l'auteur
  if (author.includes(term)) {
    if (author === term) {
      matchScore += 10000;
    } else if (author.startsWith(term)) {
      matchScore += 6000;
    } else {
      matchScore += 3000;
    }
  }
  
  // Correspondances dans la saga
  if (saga && saga.includes(term)) {
    if (saga === term) {
      matchScore += 8000;
    } else if (saga.startsWith(term)) {
      matchScore += 5000;
    } else {
      matchScore += 2000;
    }
  }
  
  // === BONUS GÉNÉRAUX ===
  
  // Séries génériquement populaires (fallback)
  if (!detectedSeries) {
    const titleAndSaga = `${title} ${saga} ${author}`.toLowerCase();
    for (const keyword of GENERAL_POPULAR_KEYWORDS) {
      if (titleAndSaga.includes(keyword) || term.includes(keyword)) {
        popularityBonus += 8000;
        break;
      }
    }
  }
  
  // Bonus pour livres récents
  if (book.first_publish_year) {
    const year = book.first_publish_year;
    if (year >= 2020) popularityBonus += 1000;
    else if (year >= 2015) popularityBonus += 800;
    else if (year >= 2010) popularityBonus += 600;
    else if (year >= 2000) popularityBonus += 400;
    else if (year >= 1990) popularityBonus += 200;
  }
  
  // Bonus pour métadonnées de qualité
  if (book.cover_url) popularityBonus += 500;
  if (book.number_of_pages && book.number_of_pages >= 100 && book.number_of_pages <= 800) {
    popularityBonus += 300;
  }
  
  // === BONUS POUR LIVRES LOCAUX ===
  
  let localBonus = 0;
  if (!book.isFromOpenLibrary) {
    localBonus = 3000; // Bonus pour livres possédés
  } else if (book.isFromOpenLibrary && book.isOwned) {
    localBonus = 1500;
  }
  
  // === CALCUL FINAL ===
  
  score = matchScore + popularityBonus + localBonus;
  
  // Malus pour livres sans métadonnées importantes
  if (!book.author || book.author.trim() === '') score -= 2000;
  if (!book.title || book.title.trim() === '') score -= 3000;
  
  return Math.max(0, Math.round(score));
}

/**
 * Détermine le niveau de pertinence d'un livre basé sur son score
 * @param {number} score - Score de pertinence
 * @returns {Object} - Niveau de pertinence avec métadonnées visuelles
 */
export function getRelevanceLevel(score) {
  if (score >= 800) return { level: 'excellent', label: 'Très pertinent', color: 'bg-green-500', icon: '🎯' };
  if (score >= 400) return { level: 'good', label: 'Pertinent', color: 'bg-blue-500', icon: '✨' };
  if (score >= 100) return { level: 'moderate', label: 'Moyennement pertinent', color: 'bg-yellow-500', icon: '👁️' };
  if (score >= 50) return { level: 'low', label: 'Peu pertinent', color: 'bg-orange-500', icon: '🔍' };
  return { level: 'minimal', label: 'Faiblement pertinent', color: 'bg-gray-500', icon: '📄' };
}

export default {
  calculateRelevanceScore,
  getRelevanceLevel
};