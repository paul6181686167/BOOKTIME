import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import BookDetailModal from '../BookDetailModal';

jest.mock('../../contexts/ThemeContext', () => ({
  useTheme: () => ({ isVoid: false }),
}));
jest.mock('../../services/authorPrefetch', () => ({
  prefetchAuthor: jest.fn(),
  readAuthorProfile: jest.fn(() => Promise.resolve(null)),
}));

describe('BookDetailModal fermeture', () => {
  beforeEach(() => {
    global.fetch = jest.fn(() =>
      Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) })
    );
  });

  it('est rendue dans document.body et se ferme avec la croix et le fond', () => {
    const onClose = jest.fn();
    const book = {
      id: 'b1',
      title: 'L\'Étranger',
      author: 'Albert Camus',
      status: 'to_read',
      description: '',
      total_pages: 200,
      isFromOpenLibrary: true,
    };
    const { container } = render(
      <MemoryRouter>
        <div style={{ transform: 'translate3d(0,0,0)' }}>
          <BookDetailModal book={book} onClose={onClose} onUpdate={jest.fn()} onDelete={jest.fn()} />
        </div>
      </MemoryRouter>
    );
    const overlay = document.body.querySelector('.modal-overlay');
    expect(overlay).not.toBeNull();
    expect(overlay.parentElement).toBe(document.body);
    expect(container.contains(overlay)).toBe(false);

    const closeBtn = overlay.querySelector('.sticky button');
    fireEvent.click(closeBtn);
    expect(onClose).toHaveBeenCalledTimes(1);

    fireEvent.click(overlay);
    expect(onClose).toHaveBeenCalledTimes(2);
  });
});
