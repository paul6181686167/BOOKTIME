import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from '../App';

// Mock des services
jest.mock('../services/authService', () => ({
  getCurrentUser: jest.fn(),
  isAuthenticated: jest.fn(),
}));

jest.mock('../services/bookService', () => ({
  getBooks: jest.fn(),
  getStats: jest.fn(),
}));

describe('App Component', () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  test('renders login page when not authenticated', () => {
    // Mock user not authenticated
    const { getCurrentUser } = require('../services/authService');
    getCurrentUser.mockResolvedValue(null);

    render(<App />);
    
    expect(screen.getByText(/connexion/i)).toBeInTheDocument();
  });

  test('renders BOOKTIME logo', async () => {
    // Mock authenticated user
    const { getCurrentUser } = require('../services/authService');
    getCurrentUser.mockResolvedValue({
      id: 'test-user',
      first_name: 'Test',
      last_name: 'User'
    });

    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('BOOKTIME')).toBeInTheDocument();
    });
  });

  test('renders category tabs', async () => {
    // Mock authenticated user
    const { getCurrentUser } = require('../services/authService');
    getCurrentUser.mockResolvedValue({
      id: 'test-user',
      first_name: 'Test',
      last_name: 'User'
    });

    // Mock books service
    const { getBooks, getStats } = require('../services/bookService');
    getBooks.mockResolvedValue([]);
    getStats.mockResolvedValue({
      total_books: 0,
      completed_books: 0,
      reading_books: 0,
      to_read_books: 0
    });

    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('Roman')).toBeInTheDocument();
      expect(screen.getByText('BD')).toBeInTheDocument();
      expect(screen.getByText('Manga')).toBeInTheDocument();
    });
  });

  test('switches between categories', async () => {
    // Mock authenticated user
    const { getCurrentUser } = require('../services/authService');
    getCurrentUser.mockResolvedValue({
      id: 'test-user',
      first_name: 'Test',
      last_name: 'User'
    });

    // Mock books service
    const { getBooks, getStats } = require('../services/bookService');
    getBooks.mockResolvedValue([]);
    getStats.mockResolvedValue({
      total_books: 0,
      completed_books: 0,
      reading_books: 0,
      to_read_books: 0
    });

    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('Roman')).toBeInTheDocument();
    });

    // Click on BD tab
    const bdTab = screen.getByText('BD');
    await userEvent.click(bdTab);
    
    // BD tab should be active
    expect(bdTab).toHaveClass('bg-green-600');
  });

  test('renders search bar', async () => {
    // Mock authenticated user
    const { getCurrentUser } = require('../services/authService');
    getCurrentUser.mockResolvedValue({
      id: 'test-user',
      first_name: 'Test',
      last_name: 'User'
    });

    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByPlaceholderText(/rechercher/i)).toBeInTheDocument();
    });
  });

  test('renders statistics cards', async () => {
    // Mock authenticated user
    const { getCurrentUser } = require('../services/authService');
    getCurrentUser.mockResolvedValue({
      id: 'test-user',
      first_name: 'Test',
      last_name: 'User'
    });

    // Mock books service with stats
    const { getBooks, getStats } = require('../services/bookService');
    getBooks.mockResolvedValue([]);
    getStats.mockResolvedValue({
      total_books: 10,
      completed_books: 5,
      reading_books: 3,
      to_read_books: 2
    });

    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('Total livres')).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument();
      expect(screen.getByText('Terminés')).toBeInTheDocument();
      expect(screen.getByText('5')).toBeInTheDocument();
    });
  });

  test('opens profile modal', async () => {
    // Mock authenticated user
    const { getCurrentUser } = require('../services/authService');
    getCurrentUser.mockResolvedValue({
      id: 'test-user',
      first_name: 'Test',
      last_name: 'User'
    });

    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('TU')).toBeInTheDocument();
    });

    // Click on profile button
    const profileButton = screen.getByText('TU');
    await userEvent.click(profileButton);
    
    // Profile modal should be visible
    await waitFor(() => {
      expect(screen.getByText(/profil/i)).toBeInTheDocument();
    });
  });
});