import { bookService } from '../../services/bookService';

// Instance axios mock unique (singleton) : axios.create() doit renvoyer TOUJOURS
// le même objet, sinon les mocks posés dans les tests n'interceptent pas l'instance
// réellement utilisée par bookService.js. Le singleton est construit DANS la factory
// (la factory jest.mock est hoistée avant l'initialisation des variables du module).
jest.mock('axios', () => {
  const api = {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
  };
  const create = jest.fn(() => api);
  return { __esModule: true, default: { create }, create };
});

// eslint-disable-next-line global-require
const mockApi = require('axios').create();

describe('BookService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.setItem('token', 'test-token');
  });

  test('getBooks charge tous les livres via /api/books/all', async () => {
    const mockBooksData = [
      { id: 1, title: 'Book 1', author: 'Author 1' },
      { id: 2, title: 'Book 2', author: 'Author 2' },
    ];
    mockApi.get.mockResolvedValue({ data: mockBooksData });

    const result = await bookService.getBooks();

    expect(mockApi.get).toHaveBeenCalledWith('/api/books/all', { params: { limit: 1000 } });
    expect(result).toEqual(mockBooksData);
  });

  test('getBooks transmet category et status en paramètres', async () => {
    mockApi.get.mockResolvedValue({ data: [] });

    await bookService.getBooks('roman', 'reading');

    expect(mockApi.get).toHaveBeenCalledWith('/api/books/all', {
      params: { category: 'roman', status: 'reading', limit: 1000 },
    });
  });

  test('getBookById récupère un livre', async () => {
    const book = { id: 'abc', title: 'Test' };
    mockApi.get.mockResolvedValue({ data: book });

    const result = await bookService.getBookById('abc');

    expect(mockApi.get).toHaveBeenCalledWith('/api/books/abc');
    expect(result).toEqual(book);
  });

  test('createBook crée un livre', async () => {
    const newBook = { title: 'New Book', author: 'New Author', category: 'roman' };
    const mockResponse = { id: 'new-id', ...newBook };
    mockApi.post.mockResolvedValue({ data: mockResponse });

    const result = await bookService.createBook(newBook);

    expect(mockApi.post).toHaveBeenCalledWith('/api/books', newBook);
    expect(result).toEqual(mockResponse);
  });

  test('updateBook met à jour un livre', async () => {
    const bookId = 'test-book-id';
    const updateData = { status: 'completed', rating: 5 };
    const mockResponse = { id: bookId, ...updateData };
    mockApi.put.mockResolvedValue({ data: mockResponse });

    const result = await bookService.updateBook(bookId, updateData);

    expect(mockApi.put).toHaveBeenCalledWith(`/api/books/${bookId}`, updateData);
    expect(result).toEqual(mockResponse);
  });

  test('deleteBook supprime un livre', async () => {
    const bookId = 'test-book-id';
    mockApi.delete.mockResolvedValue({ data: { message: 'Book deleted' } });

    const result = await bookService.deleteBook(bookId);

    expect(mockApi.delete).toHaveBeenCalledWith(`/api/books/${bookId}`);
    expect(result).toEqual({ message: 'Book deleted' });
  });

  test('getStats récupère les statistiques', async () => {
    const mockStats = { total_books: 10, completed_books: 5 };
    mockApi.get.mockResolvedValue({ data: mockStats });

    const result = await bookService.getStats();

    expect(mockApi.get).toHaveBeenCalledWith('/api/stats');
    expect(result).toEqual(mockStats);
  });

  test('searchBooksGrouped recherche avec query', async () => {
    const mockResults = { total_books: 2, results: [] };
    mockApi.get.mockResolvedValue({ data: mockResults });

    const result = await bookService.searchBooksGrouped('test query');

    expect(mockApi.get).toHaveBeenCalledWith('/api/books/search-grouped', {
      params: { q: 'test query' },
    });
    expect(result).toEqual(mockResults);
  });

  test('propage une erreur métier en cas d’échec API', async () => {
    mockApi.get.mockRejectedValue(new Error('Network Error'));

    await expect(bookService.getBooks()).rejects.toThrow(
      'Erreur lors de la récupération des livres'
    );
  });
});
