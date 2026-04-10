/**
 * 🚀 EXTENDED SERIES DATABASE - BOOKTIME
 * Base de données étendue des séries populaires
 * 
 * Dernière mise à jour: 2025-07-12 00:57:13
 * Nombre de séries: 3
 * 
 * Généré automatiquement par: update_series_detection.py
 * Source: Open Library + base manuelle
 */

// Export pour modules ES6
export const EXTENDED_SERIES_DATABASE = [
  {
    name: "Harry Potter",
    authors: ["J.K. Rowling"],
    category: "roman",
    volumes: 7,
    keywords: ["harry", "potter", "wizard", "hogwarts", "magic"],
    variations: ["Harry Potter", "HP", "Potter"],
    first_published: 1997,
    status: "completed",
    description: "Série de romans fantastiques",
    subjects: ["fantasy", "wizards", "magic", "children"],
    languages: ["en", "fr"],
    translations: {"en": "Harry Potter", "fr": "Harry Potter"},
    source: "manual",
  },
  {
    name: "Astérix",
    authors: ["René Goscinny", "Albert Uderzo"],
    category: "bd",
    volumes: 39,
    keywords: ["asterix", "obelix", "gaulois", "roman", "comic"],
    variations: ["Astérix", "Asterix", "Astérix le Gaulois"],
    first_published: 1959,
    status: "ongoing",
    description: "Série de bande dessinée française",
    subjects: ["comic", "french", "historical", "humor"],
    languages: ["fr", "en"],
    translations: {"en": "Asterix", "fr": "Astérix"},
    source: "manual",
  },
  {
    name: "One Piece",
    authors: ["Eiichiro Oda"],
    category: "manga",
    volumes: 105,
    keywords: ["one", "piece", "luffy", "pirates", "treasure"],
    variations: ["One Piece", "OP", "Wan Pīsu"],
    first_published: 1997,
    status: "ongoing",
    description: "Manga d'aventure et de pirates",
    subjects: ["manga", "pirates", "adventure", "shonen"],
    languages: ["ja", "fr", "en"],
    translations: {"en": "One Piece", "fr": "One Piece", "ja": "ワンピース"},
    source: "manual",
  }
];

// Statistiques base de données
export const SERIES_STATS = {
  total_series: 3,
  by_category: {
    roman: 1,
    bd: 1,
    manga: 1
  },
  total_volumes: 151,
  avg_volumes_per_series: 50.3,
  last_updated: "2025-07-12 00:57:13"
};

// Fonctions utilitaires
export const getSeriesByCategory = (category) => {
  return EXTENDED_SERIES_DATABASE.filter(series => series.category === category);
};

export const getSeriesByAuthor = (author) => {
  return EXTENDED_SERIES_DATABASE.filter(series => 
    series.authors.some(a => a.toLowerCase().includes(author.toLowerCase()))
  );
};

export const searchSeries = (query) => {
  const queryLower = query.toLowerCase();
  return EXTENDED_SERIES_DATABASE.filter(series => 
    series.name.toLowerCase().includes(queryLower) ||
    series.authors.some(a => a.toLowerCase().includes(queryLower)) ||
    series.keywords.some(k => k.toLowerCase().includes(queryLower))
  );
};

// Export par défaut
export default EXTENDED_SERIES_DATABASE;
