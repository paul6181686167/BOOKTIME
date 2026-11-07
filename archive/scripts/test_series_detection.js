/**
 * Test de détection des séries pour diagnostiquer le problème
 */

import { EXTENDED_SERIES_DATABASE } from '/app/frontend/src/utils/seriesDatabaseExtended.js';
import SeriesDetector from '/app/frontend/src/utils/seriesDetector.js';

// Livres de test
const testBooks = [
  {
    title: "Harry Potter à l'école des sorciers",
    author: "J.K. Rowling",
    category: "roman"
  },
  {
    title: "Harry Potter et la chambre des secrets",
    author: "J.K. Rowling",
    category: "roman"
  },
  {
    title: "One Piece tome 1",
    author: "Eiichiro Oda",
    category: "manga"
  },
  {
    title: "Astérix le Gaulois",
    author: "René Goscinny",
    category: "bd"
  },
  {
    title: "Le Petit Prince",
    author: "Antoine de Saint-Exupéry",
    category: "roman"
  }
];

console.log('=== TEST DÉTECTION SÉRIES ===');

// Test 1 : Vérifier la base de données
console.log('\n1. Vérification base de données des séries :');
console.log('Harry Potter présent :', !!EXTENDED_SERIES_DATABASE.romans?.harry_potter);
console.log('One Piece présent :', !!EXTENDED_SERIES_DATABASE.manga?.one_piece);
console.log('Astérix présent :', !!EXTENDED_SERIES_DATABASE.bd?.asterix);

// Test 2 : Tester la détection pour chaque livre
console.log('\n2. Test détection pour chaque livre :');
testBooks.forEach(book => {
  const detection = SeriesDetector.detectBookSeries(book);
  console.log(`\n📖 Livre: "${book.title}" par ${book.author}`);
  console.log(`   Série détectée: ${detection.belongsToSeries ? 'OUI' : 'NON'}`);
  if (detection.belongsToSeries) {
    console.log(`   Nom série: ${detection.seriesName}`);
    console.log(`   Confiance: ${detection.confidence}%`);
    console.log(`   Méthode: ${detection.method}`);
  }
});

// Test 3 : Vérifier masquage
console.log('\n3. Test masquage intelligent :');
const maskingResult = SeriesDetector.filterBooksWithSeriesMasking(testBooks, { logMasking: true });
console.log(`\nRésumé masquage:`);
console.log(`- Total livres: ${maskingResult.stats.total}`);
console.log(`- Livres visibles: ${maskingResult.stats.visible}`);
console.log(`- Livres masqués: ${maskingResult.stats.masked}`);