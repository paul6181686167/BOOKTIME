import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import IsbnScannerModal, { buildImportPayload } from '../IsbnScannerModal';

jest.mock('react-hot-toast', () => {
  const toast = () => {};
  toast.success = () => {};
  toast.error = () => {};
  return { __esModule: true, default: toast };
});
jest.mock('html5-qrcode', () => ({
  Html5Qrcode: class {},
  Html5QrcodeSupportedFormats: {},
}));

const VALID = '9782070360024';
const BOOK = {
  title: 'Le Petit Prince',
  author: 'Antoine de Saint-Exupéry',
  isbn: VALID,
  cover_url: '',
  category: 'roman',
  number_of_pages: 96,
};

function mockFetch(handlers) {
  global.fetch = jest.fn((url, options) => {
    const key = Object.keys(handlers).find((k) => String(url).includes(k));
    const { status = 200, body = {} } = handlers[key]({ url, options });
    return Promise.resolve({ ok: status >= 200 && status < 300, status, json: () => Promise.resolve(body) });
  });
}

async function openWithBook(props = {}) {
  mockFetch({
    'search-isbn': () => ({ body: { book: BOOK } }),
    '/import': () => ({ body: { book: { id: 'b1', title: BOOK.title } } }),
  });
  const utils = render(<IsbnScannerModal isOpen onClose={() => {}} {...props} />);
  fireEvent.change(screen.getByLabelText('Saisir l’ISBN'), { target: { value: VALID } });
  fireEvent.click(screen.getByRole('button', { name: 'OK' }));
  await screen.findByText('Ajouter à ma bibliothèque');
  return utils;
}

describe('buildImportPayload', () => {
  test('ne garde que des champs propres', () => {
    const payload = buildImportPayload({
      ...BOOK,
      id: 'isbn_1',
      isFromOpenLibrary: true,
      author: 'Auteur inconnu',
      category: 'poesie',
      first_publish_year: '1943',
      publisher: ['Gallimard'],
    });
    expect(payload).toEqual({
      ol_key: '',
      title: 'Le Petit Prince',
      author: '',
      category: 'roman',
      cover_url: '',
      isbn: VALID,
      description: '',
      publisher: '',
      total_pages: 96,
      first_publish_year: 1943,
    });
    expect(payload.id).toBeUndefined();
  });
});

describe('IsbnScannerModal', () => {
  test('est rendue dans <body>, au-dessus de la barre de navigation', () => {
    mockFetch({});
    const { container } = render(<IsbnScannerModal isOpen onClose={() => {}} />);
    const dialog = screen.getByRole('dialog');
    expect(container.contains(dialog)).toBe(false);
    expect(document.body.contains(dialog)).toBe(true);
    expect(dialog.style.zIndex).toBe('1300');
  });

  test("la saisie manuelle est présente et modifiable", () => {
    mockFetch({});
    render(<IsbnScannerModal isOpen onClose={() => {}} />);
    const input = screen.getByLabelText('Saisir l’ISBN');
    fireEvent.change(input, { target: { value: VALID } });
    expect(input.value).toBe(VALID);
  });

  test("sans couverture, une vignette de repli affiche le titre", async () => {
    await openWithBook();
    expect(screen.getByTestId('cover-placeholder')).toHaveTextContent('Le Petit Prince');
  });

  test("une couverture réduite à un pixel est remplacée par la vignette de repli", async () => {
    mockFetch({
      'search-isbn': () => ({ body: { book: { ...BOOK, cover_url: 'https://x.test/blank.gif' } } }),
    });
    const { container } = render(<IsbnScannerModal isOpen onClose={() => {}} />);
    fireEvent.change(screen.getByLabelText('Saisir l’ISBN'), { target: { value: VALID } });
    fireEvent.click(screen.getByRole('button', { name: 'OK' }));
    await screen.findByText('Ajouter à ma bibliothèque');
    const img = document.body.querySelector('img');
    Object.defineProperty(img, 'naturalWidth', { value: 1 });
    fireEvent.load(img);
    expect(await screen.findByTestId('cover-placeholder')).toBeInTheDocument();
    expect(container).toBeTruthy();
  });

  test("ajouter envoie l'import au serveur puis rafraîchit et ferme", async () => {
    const onAdded = jest.fn();
    const onClose = jest.fn();
    await openWithBook({ onAdded, onClose });
    fireEvent.click(screen.getByText('Ajouter à ma bibliothèque'));
    await waitFor(() => expect(onClose).toHaveBeenCalled());
    const call = global.fetch.mock.calls.find(([url]) => String(url).includes('/api/openlibrary/import'));
    expect(call[1].method).toBe('POST');
    expect(JSON.parse(call[1].body)).toMatchObject({ title: 'Le Petit Prince', isbn: VALID, category: 'roman' });
    expect(onAdded).toHaveBeenCalledTimes(1);
  });

  test("un livre déjà possédé est signalé sans erreur", async () => {
    const onClose = jest.fn();
    mockFetch({
      'search-isbn': () => ({ body: { book: BOOK } }),
      '/import': () => ({ status: 409, body: { detail: 'Ce livre est déjà dans votre collection' } }),
    });
    render(<IsbnScannerModal isOpen onClose={onClose} />);
    fireEvent.change(screen.getByLabelText('Saisir l’ISBN'), { target: { value: VALID } });
    fireEvent.click(screen.getByRole('button', { name: 'OK' }));
    fireEvent.click(await screen.findByText('Ajouter à ma bibliothèque'));
    await waitFor(() => expect(onClose).toHaveBeenCalled());
  });

  test("un échec serveur laisse la fenêtre ouverte pour réessayer", async () => {
    const onClose = jest.fn();
    mockFetch({
      'search-isbn': () => ({ body: { book: BOOK } }),
      '/import': () => ({ status: 500, body: { detail: 'Erreur serveur' } }),
    });
    render(<IsbnScannerModal isOpen onClose={onClose} />);
    fireEvent.change(screen.getByLabelText('Saisir l’ISBN'), { target: { value: VALID } });
    fireEvent.click(screen.getByRole('button', { name: 'OK' }));
    fireEvent.click(await screen.findByText('Ajouter à ma bibliothèque'));
    await waitFor(() => expect(screen.getByText('Ajouter à ma bibliothèque')).toBeEnabled());
    expect(onClose).not.toHaveBeenCalled();
  });
});
