import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import BookCard from '../../components/BookCard';

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
  volume_number: 1
};

describe('BookCard Component', () => {
  const mockOnClick = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders book information correctly', () => {
    render(<BookCard book={mockBook} onClick={mockOnClick} />);
    
    expect(screen.getByText('Test Book')).toBeInTheDocument();
    expect(screen.getByText('Test Author')).toBeInTheDocument();
    expect(screen.getByText('Test Saga - Tome 1')).toBeInTheDocument();
  });

  test('renders book cover image', () => {
    render(<BookCard book={mockBook} onClick={mockOnClick} />);
    
    const coverImage = screen.getByAltText('Test Book cover');
    expect(coverImage).toBeInTheDocument();
    expect(coverImage).toHaveAttribute('src', mockBook.cover_url);
  });

  test('renders progress bar for reading books', () => {
    render(<BookCard book={mockBook} onClick={mockOnClick} />);
    
    // Should show progress (150/300 = 50%)
    expect(screen.getByText('150 / 300 pages')).toBeInTheDocument();
  });

  test('renders status badge', () => {
    render(<BookCard book={mockBook} onClick={mockOnClick} />);
    
    // Should show "En cours" status
    expect(screen.getByText('En cours')).toBeInTheDocument();
  });

  test('renders category badge', () => {
    render(<BookCard book={mockBook} onClick={mockOnClick} />);
    
    // Should show category badge
    expect(screen.getByText('Roman')).toBeInTheDocument();
  });

  test('renders rating stars', () => {
    render(<BookCard book={mockBook} onClick={mockOnClick} />);
    
    // Should show 4 stars
    const stars = screen.getAllByText('★');
    expect(stars).toHaveLength(4);
  });

  test('handles click events', async () => {
    render(<BookCard book={mockBook} onClick={mockOnClick} />);
    
    const card = screen.getByText('Test Book').closest('div');
    await userEvent.click(card);
    
    expect(mockOnClick).toHaveBeenCalledWith(mockBook);
  });

  test('renders completed book correctly', () => {
    const completedBook = {
      ...mockBook,
      status: 'completed',
      current_page: 300,
      rating: 5
    };

    render(<BookCard book={completedBook} onClick={mockOnClick} />);
    
    expect(screen.getByText('Terminé')).toBeInTheDocument();
    expect(screen.getByText('300 / 300 pages')).toBeInTheDocument();
    
    // Should show 5 stars
    const stars = screen.getAllByText('★');
    expect(stars).toHaveLength(5);
  });

  test('renders to-read book correctly', () => {
    const toReadBook = {
      ...mockBook,
      status: 'to_read',
      current_page: 0,
      rating: 0
    };

    render(<BookCard book={toReadBook} onClick={mockOnClick} />);
    
    expect(screen.getByText('À lire')).toBeInTheDocument();
    expect(screen.getByText('0 / 300 pages')).toBeInTheDocument();
    
    // Should show no stars
    const stars = screen.queryAllByText('★');
    expect(stars).toHaveLength(0);
  });

  test('renders book without saga', () => {
    const bookWithoutSaga = {
      ...mockBook,
      saga: '',
      volume_number: null
    };

    render(<BookCard book={bookWithoutSaga} onClick={mockOnClick} />);
    
    expect(screen.getByText('Test Book')).toBeInTheDocument();
    expect(screen.getByText('Test Author')).toBeInTheDocument();
    expect(screen.queryByText('Test Saga')).not.toBeInTheDocument();
  });

  test('renders placeholder when no cover image', () => {
    const bookWithoutCover = {
      ...mockBook,
      cover_url: ''
    };

    render(<BookCard book={bookWithoutCover} onClick={mockOnClick} />);
    
    // Should show placeholder div
    const placeholder = screen.getByText('📖');
    expect(placeholder).toBeInTheDocument();
  });
});