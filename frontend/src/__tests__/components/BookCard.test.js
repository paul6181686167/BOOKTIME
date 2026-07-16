import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import BookCard from '../../components/BookCard';

// LanguageIndicator dépend d'un contexte de langue ; on l'isole pour tester
// uniquement le rendu propre de BookCard.
jest.mock('../../components/LanguageIndicator', () => () => null);

const mockBook = {
  id: 'test-book-1',
  title: 'Test Book',
  author: 'Test Author',
  category: 'roman',
  status: 'reading',
  current_page: 150,
  total_pages: 300,
  rating: 4,
  cover_url: 'https://example.com/cover.jpg',
  saga: 'Test Saga',
  volume_number: 1,
};

describe('BookCard Component', () => {
  const mockOnBookClick = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('affiche titre et auteur', () => {
    render(<BookCard book={mockBook} onBookClick={mockOnBookClick} />);
    expect(screen.getByText('Test Book')).toBeInTheDocument();
    expect(screen.getByText('Test Author')).toBeInTheDocument();
  });

  test('affiche la couverture avec le titre en alt', () => {
    render(<BookCard book={mockBook} onBookClick={mockOnBookClick} />);
    const cover = screen.getByAltText('Test Book');
    expect(cover).toBeInTheDocument();
    expect(cover).toHaveAttribute('src', mockBook.cover_url);
  });

  test('affiche le statut "En cours" pour un livre en lecture', () => {
    render(<BookCard book={mockBook} onBookClick={mockOnBookClick} />);
    expect(screen.getByText('En cours')).toBeInTheDocument();
  });

  test('affiche la progression pages pour un livre en cours', () => {
    render(<BookCard book={mockBook} onBookClick={mockOnBookClick} />);
    expect(screen.getByText('150 / 300')).toBeInTheDocument();
    expect(screen.getByText('300 pages')).toBeInTheDocument();
  });

  test('affiche la saga', () => {
    render(<BookCard book={mockBook} onBookClick={mockOnBookClick} />);
    expect(screen.getByText('📖 Test Saga')).toBeInTheDocument();
  });

  test('affiche les étoiles de notation (rating > 0)', () => {
    const { container } = render(<BookCard book={mockBook} onBookClick={mockOnBookClick} />);
    // 5 emplacements d'étoiles (remplies + vides) sont rendus quand rating > 0.
    const starSlots = container.querySelectorAll('.w-3.h-3 svg');
    expect(starSlots.length).toBe(5);
  });

  test('déclenche onBookClick au clic', async () => {
    render(<BookCard book={mockBook} onBookClick={mockOnBookClick} />);
    await userEvent.click(screen.getByText('Test Book'));
    expect(mockOnBookClick).toHaveBeenCalledWith(mockBook);
  });

  test('affiche un livre terminé correctement', () => {
    const completedBook = { ...mockBook, status: 'completed', current_page: 300, rating: 5 };
    render(<BookCard book={completedBook} onBookClick={mockOnBookClick} />);
    expect(screen.getByText('Terminé')).toBeInTheDocument();
  });

  test('affiche un livre à lire correctement', () => {
    const toReadBook = { ...mockBook, status: 'to_read', current_page: 0, rating: 0 };
    const { container } = render(<BookCard book={toReadBook} onBookClick={mockOnBookClick} />);
    expect(screen.getByText('À lire')).toBeInTheDocument();
    // rating = 0 -> pas de bloc d'étoiles.
    expect(container.querySelectorAll('.w-3.h-3 svg').length).toBe(0);
  });

  test('affiche le placeholder quand pas de couverture', () => {
    const bookWithoutCover = { ...mockBook, cover_url: '' };
    render(<BookCard book={bookWithoutCover} onBookClick={mockOnBookClick} />);
    expect(screen.getByText('Pas de couverture')).toBeInTheDocument();
    expect(screen.getByText('📚')).toBeInTheDocument();
  });
});
