import {
  formatAsDays,
  formatDuration,
  formatWords,
  normalizeWpm,
  pagesReadForBook,
  summarizeReadingTime,
} from '../readingTime';

describe('vitesse de lecture choisie dans les paramètres', () => {
  it('n’accepte que les vitesses proposées, sinon la vitesse moyenne', () => {
    expect(normalizeWpm(180)).toBe(180);
    expect(normalizeWpm(300)).toBe(300);
    expect(normalizeWpm(999)).toBe(238);
    expect(normalizeWpm(undefined)).toBe(238);
  });

  it('une lecture plus rapide réduit le temps estimé, romans comme pages illustrées', () => {
    const books = [
      { status: 'completed', category: 'roman', total_pages: 300 },
      { status: 'completed', category: 'bd', total_pages: 100 },
    ];
    const slow = summarizeReadingTime(books, 180);
    const normal = summarizeReadingTime(books);
    const fast = summarizeReadingTime(books, 300);
    expect(slow.totalMinutes).toBeGreaterThan(normal.totalMinutes);
    expect(normal.totalMinutes).toBeGreaterThan(fast.totalMinutes);
    // À la vitesse moyenne, le résultat est inchangé
    expect(normal.byCategory.bd.minutes).toBeCloseTo(80, 5);
  });
});

describe('temps de lecture estimé', () => {
  it('compte toutes les pages d’un livre terminé et la page courante d’un livre en cours', () => {
    expect(pagesReadForBook({ status: 'completed', total_pages: 300 })).toEqual({
      pages: 300,
      guessed: false,
    });
    expect(pagesReadForBook({ status: 'reading', total_pages: 300, current_page: 120 }).pages).toBe(120);
    expect(pagesReadForBook({ status: 'reading', total_pages: 100, current_page: 500 }).pages).toBe(100);
    expect(pagesReadForBook({ status: 'to_read', total_pages: 300 }).pages).toBe(0);
  });

  it('un livre « à relire » a déjà été lu en entier : ses pages comptent', () => {
    expect(pagesReadForBook({ status: 'to_reread', total_pages: 250 }).pages).toBe(250);
    const s = summarizeReadingTime([
      { status: 'completed', category: 'roman', total_pages: 300 },
      { status: 'to_reread', category: 'roman', total_pages: 200 },
      { status: 'reading', category: 'manga', total_pages: 180, current_page: 20 },
    ]);
    expect(s.byCategory.roman.books).toBe(2);
    expect(s.totalPages).toBe(520);
  });

  it('utilise une valeur moyenne quand le nombre de pages est inconnu', () => {
    const r = pagesReadForBook({ status: 'completed', category: 'manga' });
    expect(r.guessed).toBe(true);
    expect(r.pages).toBeGreaterThan(0);
  });

  it('calcule les mots et le temps d’un roman à partir des pages', () => {
    const s = summarizeReadingTime([{ status: 'completed', category: 'roman', total_pages: 238 }]);
    // 238 pages x 280 mots / 238 mots par minute = 280 minutes
    expect(s.byCategory.roman.minutes).toBeCloseTo(280, 5);
    expect(s.byCategory.roman.words).toBe(238 * 280);
    expect(s.totalMinutes).toBe(280);
  });

  it('compte les romans graphiques par temps moyen par page, sans mots', () => {
    const s = summarizeReadingTime([{ status: 'completed', category: 'bd', total_pages: 50 }]);
    expect(s.byCategory.bd.minutes).toBeCloseTo(40, 5);
    expect(s.byCategory.bd.words).toBe(0);
    expect(s.byCategory.bd.books).toBe(1);
  });

  it('ignore les cartes série et les livres à lire', () => {
    const s = summarizeReadingTime([
      { isSeriesCard: true, status: 'completed', total_pages: 999 },
      { status: 'to_read', total_pages: 300 },
    ]);
    expect(s.totalMinutes).toBe(0);
  });

  it('formate durées, jours et mots', () => {
    expect(formatDuration(45)).toBe('45 min');
    expect(formatDuration(150)).toMatch(/^2 h 30$/);
    expect(formatAsDays(60)).toBe('');
    expect(formatAsDays(60 * 48)).toContain('2');
    expect(formatWords(85000)).toMatch(/85\s?000 mots/);
    expect(formatWords(1_200_000)).toContain('million');
  });
});
