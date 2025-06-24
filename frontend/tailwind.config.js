/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'booktime': {
          50: '#fef7ff',
          100: '#fdeeff',
          200: '#fdd5ff',
          300: '#fcb3ff',
          400: '#f881ff',
          500: '#f04fff',
          600: '#e81cff',
          700: '#d300e8',
          800: '#a800b8',
          900: '#8a0095',
        },
        'book': {
          'roman': '#3b82f6',      // Blue
          'bd': '#10b981',         // Green  
          'manga': '#f59e0b',      // Yellow/Orange
        }
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}