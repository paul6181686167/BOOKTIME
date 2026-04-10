// Constantes pour les langues supportées
export const LANGUAGES = [
  { code: 'français', name: 'Français', flag: '🇫🇷' },
  { code: 'anglais', name: 'Anglais', flag: '🇬🇧' },
  { code: 'espagnol', name: 'Espagnol', flag: '🇪🇸' },
  { code: 'italien', name: 'Italien', flag: '🇮🇹' },
  { code: 'allemand', name: 'Allemand', flag: '🇩🇪' },
  { code: 'portugais', name: 'Portugais', flag: '🇵🇹' },
  { code: 'russe', name: 'Russe', flag: '🇷🇺' },
  { code: 'japonais', name: 'Japonais', flag: '🇯🇵' },
  { code: 'chinois', name: 'Chinois', flag: '🇨🇳' },
  { code: 'coréen', name: 'Coréen', flag: '🇰🇷' },
  { code: 'arabe', name: 'Arabe', flag: '🇸🇦' },
  { code: 'hindi', name: 'Hindi', flag: '🇮🇳' },
  { code: 'néerlandais', name: 'Néerlandais', flag: '🇳🇱' },
  { code: 'suédois', name: 'Suédois', flag: '🇸🇪' },
  { code: 'norvégien', name: 'Norvégien', flag: '🇳🇴' },
  { code: 'danois', name: 'Danois', flag: '🇩🇰' },
  { code: 'finnois', name: 'Finnois', flag: '🇫🇮' },
  { code: 'polonais', name: 'Polonais', flag: '🇵🇱' },
  { code: 'tchèque', name: 'Tchèque', flag: '🇨🇿' },
  { code: 'hongrois', name: 'Hongrois', flag: '🇭🇺' },
  { code: 'grec', name: 'Grec', flag: '🇬🇷' },
  { code: 'turc', name: 'Turc', flag: '🇹🇷' },
  { code: 'hébreu', name: 'Hébreu', flag: '🇮🇱' },
  { code: 'thaï', name: 'Thaï', flag: '🇹🇭' },
  { code: 'vietnamien', name: 'Vietnamien', flag: '🇻🇳' },
  { code: 'latin', name: 'Latin', flag: '🏛️' },
  { code: 'ancien_grec', name: 'Grec ancien', flag: '🏛️' },
  { code: 'sanskrit', name: 'Sanskrit', flag: '🕉️' }
];

export const getLanguageByCode = (code) => {
  return LANGUAGES.find(lang => lang.code === code) || { code, name: code, flag: '🌍' };
};

export const getLanguageName = (code) => {
  const lang = getLanguageByCode(code);
  return lang.name;
};

export const getLanguageFlag = (code) => {
  const lang = getLanguageByCode(code);
  return lang.flag;
};

// Langues les plus courantes (pour un ordre prioritaire)
export const COMMON_LANGUAGES = [
  'français', 'anglais', 'espagnol', 'italien', 'allemand', 'japonais', 'chinois'
];