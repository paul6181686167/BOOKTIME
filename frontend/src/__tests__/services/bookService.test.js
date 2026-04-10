import { bookService } from '../../services/bookService';

// Mock axios
jest.mock('axios', () => ({
  create: jest.fn(() => ({
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
  })),
}));

describe('BookService', () => {
  const mockAxios = require('axios').create();

  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.setItem('token', 'test-token');
  });

  test('getBooks returns books data', async () => {
    const mockBooksData = [
      { id: 1, title: 'Book 1', author: 'Author 1' },
      { id: 2, title: 'Book 2', author: 'Author 2' }
    ];

    mockAxios.get.mockResolvedValue({ data: mockBooksData });

    const result = await bookService.getBooks();

    expect(mockAxios.get).toHaveBeenCalledWith('/api/books');
    expect(result).toEqual(mockBooksData);
  });

  test('getBooks with filters', async () => {
    const mockBooksData = [
      { id: 1, title: 'Book 1', author: 'Author 1', category: 'roman' }
    ];

    mockAxios.get.mockResolvedValue({ data: mockBooksData });

    const result = await bookService.getBooks({ category: 'roman', status: 'reading' });

    expect(mockAxios.get).toHaveBeenCalledWith('/api/books', {
      params: { category: 'roman', status: 'reading' }
    });
    expect(result).toEqual(mockBooksData);
  });

  test('addBook creates new book', async () => {
    const newBook = {
      title: 'New Book',
      author: 'New Author',
      category: 'roman'
    };

    const mockResponse = {
      id: 'new-book-id',
      ...newBook,
      date_added: '2024-01-01T00:00:00Z'
    };

    mockAxios.post.mockResolvedValue({ data: mockResponse });

    const result = await bookService.addBook(newBook);

    expect(mockAxios.post).toHaveBeenCalledWith('/api/books', newBook);
    expect(result).toEqual(mockResponse);
  });

  test('updateBook updates existing book', async () => {
    const bookId = 'test-book-id';
    const updateData = {
      status: 'completed',
      rating: 5,
      review: 'Excellent book!'
    };

    const mockResponse = {
      id: bookId,
      title: 'Test Book',
      ...updateData,
      updated_at: '2024-01-01T00:00:00Z'
    };

    mockAxios.put.mockResolvedValue({ data: mockResponse });

    const result = await bookService.updateBook(bookId, updateData);

    expect(mockAxios.put).toHaveBeenCalledWith(`/api/books/${bookId}`, updateData);
    expect(result).toEqual(mockResponse);
  });

  test('deleteBook removes book', async () => {
    const bookId = 'test-book-id';

    mockAxios.delete.mockResolvedValue({ data: { message: 'Book deleted' } });

    const result = await bookService.deleteBook(bookId);

    expect(mockAxios.delete).toHaveBeenCalledWith(`/api/books/${bookId}`);
    expect(result).toEqual({ message: 'Book deleted' });
  });

  test('getStats returns statistics', async () => {
    const mockStats = {
      total_books: 10,
      completed_books: 5,
      reading_books: 3,
      to_read_books: 2,
      categories: {
        roman: 5,
        bd: 3,
        manga: 2
      }
    };

    mockAxios.get.mockResolvedValue({ data: mockStats });

    const result = await bookService.getStats();

    expect(mockAxios.get).toHaveBeenCalledWith('/api/stats');
    expect(result).toEqual(mockStats);
  });

  test('searchBooks returns search results', async () => {
    const searchQuery = 'test query';
    const mockSearchResults = [
      { id: 1, title: 'Test Book 1', author: 'Author 1' },
      { id: 2, title: 'Test Book 2', author: 'Author 2' }
    ];

    mockAxios.get.mockResolvedValue({ data: mockSearchResults });

    const result = await bookService.searchBooks(searchQuery);

    expect(mockAxios.get).toHaveBeenCalledWith('/api/books/search', {
      params: { q: searchQuery }
    });
    expect(result).toEqual(mockSearchResults);
  });

  test('handles API errors gracefully', async () => {
    const errorMessage = 'Network Error';
    mockAxios.get.mockRejectedValue(new Error(errorMessage));

    await expect(bookService.getBooks()).rejects.toThrow(errorMessage);
  });

  test('handles authentication errors', async () => {
    const authError = {
      response: { status: 401, data: { detail: 'Token expired' } }
    };
    mockAxios.get.mockRejectedValue(authError);

    await expect(bookService.getBooks()).rejects.toEqual(authError);
  });
});