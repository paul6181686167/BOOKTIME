/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Accent unique de l'application, aligné sur le vert de la barre de
        // chargement (booktime-600 === #16a34a). Les 19 `ring-booktime-500` et
        // les 18 `ring-green-500` du code deviennent ainsi la même couleur.
        'booktime': {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
          // Fond de page : vert doux mais bien présent
          mist: '#bce8cb',
          mistSoft: '#d0f0dc',
        },
        // Mode sombre en nuances de vert (plus de gris bleuté).
        // 900 = page, 800 = carte, 700 = relief / bordures.
        // Les teintes claires (50–500) restent celles de Tailwind.
        // 900 = fond page, 800 = vignettes (un cran plus clair pour contraster moins fort)
        'gray': {
          700: '#1e3a2c',
          800: '#163528',
          900: '#234f37',
        },
        'book': {
          'roman': '#3b82f6',
          'bd': '#10b981',
          'manga': '#f59e0b',
        }
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif'],
        // Serif système pour les titres d'œuvres : donne du caractère à une
        // application de lecture sans télécharger une police de plus.
        'display': ['"Iowan Old Style"', '"Palatino Linotype"', 'Palatino', 'Georgia', 'serif'],
      },
      fontSize: {
        // Échelle des très petits corps, en remplacement des text-[9px] et
        // autres valeurs arbitraires semées dans les composants.
        'micro': ['0.5625rem', { lineHeight: '0.75rem' }],
        'mini': ['0.625rem', { lineHeight: '0.875rem' }],
        'tiny': ['0.6875rem', { lineHeight: '0.9375rem' }],
      },
      boxShadow: {
        // Ombres larges et peu contrastées, à la place des shadow-sm/lg secs
        'card': '0 1px 2px rgba(15, 23, 42, 0.04), 0 4px 12px -2px rgba(15, 23, 42, 0.08)',
        'card-hover': '0 2px 4px rgba(15, 23, 42, 0.06), 0 14px 30px -8px rgba(15, 23, 42, 0.20)',
      },
    },
  },
  plugins: [],
  // Pas de liste corePlugins ici : en Tailwind 3 le moteur JIT ne produit que
  // les classes réellement présentes dans le code, donc désactiver des plugins
  // ne fait pas maigrir le CSS. La liste qui existait auparavant neutralisait
  // silencieusement 92 classes déjà écrites dans les composants, dont tous les
  // anneaux de focus (accessibilité) et le flou d'arrière-plan.
}
