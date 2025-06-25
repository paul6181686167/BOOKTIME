class OpenLibraryService {
  constructor() {
    this.backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
  }

  getAuthHeaders() {
    const token = localStorage.getItem('token');
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };
  }

  async searchUniversal(query, options = {}) {
    const params = new URLSearchParams();
    params.append('q', query);
    
    if (options.limit) params.append('limit', options.limit);
    if (options.category) params.append('category', options.category);

    const response = await fetch(`${this.backendUrl}/api/openlibrary/search-universal?${params}`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('Failed to search OpenLibrary');
    }

    return response.json();
  }

  async getBookDetails(workKey) {
    const response = await fetch(`${this.backendUrl}/api/openlibrary/book/${workKey}`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('Failed to fetch OpenLibrary book details');
    }

    return response.json();
  }

  async getAuthorDetails(authorName) {
    const encodedAuthorName = encodeURIComponent(authorName);
    const response = await fetch(`${this.backendUrl}/api/openlibrary/author/${encodedAuthorName}`, {
      headers: this.getAuthHeaders()
    });

    if (!response.ok) {
      throw new Error('Failed to fetch OpenLibrary author details');
    }

    return response.json();
  }

  async addBookToLibrary(bookData) {
    const response = await fetch(`${this.backendUrl}/api/books`, {
      method: 'POST',
      headers: this.getAuthHeaders(),
      body: JSON.stringify(bookData)
    });

    if (!response.ok) {
      throw new Error('Failed to add book to library');
    }

    return response.json();
  }
}

const openLibraryService = new OpenLibraryService();
export default openLibraryService;