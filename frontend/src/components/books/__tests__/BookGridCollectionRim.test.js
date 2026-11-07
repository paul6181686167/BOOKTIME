import React from 'react';
import { render, act } from '@testing-library/react';
import BookGrid from '../BookGrid';
import { createCollection, addItemToCollection } from '../../../utils/collectionsStorage';

jest.mock('../../../services/bookService', () => ({ bookService: {} }));

describe('BookGrid : liseré de collection', () => {
  beforeEach(() => localStorage.clear());

  it('colore le contour des vignettes d\'une collection, en direct', () => {
    const books = [
      { id: 'b1', title: 'Dans la collection', author: 'A', status: 'to_read' },
      { id: 'b2', title: 'Hors collection', author: 'B', status: 'to_read' },
    ];
    const { container } = render(<BookGrid books={books} onBookClick={() => {}} />);
    const frames = () => container.querySelectorAll('.aspect-\\[2\\/3\\].relative');

    expect(frames()[0].style.boxShadow).toBe('');

    act(() => {
      const { collection } = createCollection('Favoris', '#ef4444');
      addItemToCollection(collection.id, { type: 'book', id: 'b1', title: 'Dans la collection' });
    });

    const [first, second] = frames();
    expect(first.style.boxShadow).toContain('#ef4444');
    expect(second.style.boxShadow).toBe('');
  });
});
