import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { render, screen, waitFor } from '@testing-library/react';
import BookDetailModal from '../BookDetailModal';

jest.mock('canvas-confetti', () => () => {});
jest.mock('../../contexts/ThemeContext', () => ({ useTheme: () => ({ isVoid: false }) }));
jest.mock('../common/CommunityReviews', () => () => null);
jest.mock('../common/AddToCollectionMenu', () => () => null);

const OLD = 'Un roman d’Albert Camus publié en 1942 dans la collection Blanche, présenté comme le récit de l’absurde.';
const BACK_COVER =
  'Aujourd’hui, maman est morte. Ou peut-être hier, je ne sais pas. Meursault, employé à Alger, assiste à l’enterrement.';

const makeBook = (id) => ({
  id,
  title: 'L’Étranger',
  author: 'Albert Camus',
  isbn: '9782070360024',
  category: 'roman',
  status: 'to_read',
  total_pages: 186,
  description: OLD,
});

let synopsisCalls;

beforeEach(() => {
  synopsisCalls = 0;
  global.fetch = jest.fn((url) => {
    if (String(url).includes('/synopsis')) {
      synopsisCalls += 1;
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({ description: BACK_COVER, pages: 186, replaced: true, source: 'google_books_isbn' }),
      });
    }
    return Promise.resolve({ ok: false, json: () => Promise.resolve({}) });
  });
});

afterEach(() => {
  delete global.fetch;
});

const renderModal = (book, onUpdate) =>
  render(
    <MemoryRouter>
      <BookDetailModal book={book} onClose={jest.fn()} onUpdate={onUpdate} onDelete={jest.fn()} />
    </MemoryRouter>
  );

describe('résumé = 4ᵉ de couverture', () => {
  test('remplace un ancien résumé par la 4ᵉ de couverture de l’édition', async () => {
    const onUpdate = jest.fn(() => Promise.resolve());
    renderModal(makeBook('verify-1'), onUpdate);
    expect(await screen.findByText(BACK_COVER)).toBeInTheDocument();
    expect(screen.queryByText(OLD)).toBeNull();
    await waitFor(() =>
      expect(onUpdate).toHaveBeenCalledWith('verify-1', { description: BACK_COVER })
    );
  });

  test('ne compare un livre qu’une fois par session', async () => {
    const first = renderModal(makeBook('verify-2'), jest.fn(() => Promise.resolve()));
    await screen.findByText(BACK_COVER);
    first.unmount();
    renderModal({ ...makeBook('verify-2'), description: BACK_COVER }, jest.fn());
    await screen.findByText(BACK_COVER);
    expect(synopsisCalls).toBe(1);
  });
});
