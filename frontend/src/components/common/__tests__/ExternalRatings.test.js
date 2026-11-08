import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import ExternalRatings from '../ExternalRatings';
import { fetchExternalRatings } from '../../../services/externalRatingsService';

jest.mock('../../../services/externalRatingsService', () => ({ fetchExternalRatings: jest.fn() }));

const LINKS = [{ label: 'Babelio', url: 'https://babelio.test' }];

beforeEach(() => fetchExternalRatings.mockReset());

test('affiche chaque note sur 5 avec sa source et le nombre d’avis', async () => {
  fetchExternalRatings.mockResolvedValue({
    ratings: [
      { source: 'openlibrary', label: 'Open Library', score: 4.23, count: 1234, url: 'https://ol.test', scope: 'book' },
      { source: 'anilist', label: 'AniList', score: 4.4, count: null, url: null, scope: 'series' },
    ],
    links: LINKS,
  });
  render(<ExternalRatings title="One Piece" category="manga" />);
  expect(await screen.findByText('4,2/5')).toBeInTheDocument();
  expect(screen.getByText(/1\s?234 avis/)).toBeInTheDocument();
  // une note de série affichée dans une fiche livre est signalée comme telle
  expect(screen.getByText('AniList (série)')).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /Open Library/ })).toHaveAttribute('href', 'https://ol.test');
  expect(screen.getByRole('link', { name: /Babelio/ })).toBeInTheDocument();
});

test('indique l’absence de note mais garde les liens de recherche', async () => {
  fetchExternalRatings.mockResolvedValue({ ratings: [], links: LINKS });
  render(<ExternalRatings title="Livre rare" />);
  expect(await screen.findByText(/Aucune note trouvée/)).toBeInTheDocument();
  expect(screen.getByRole('link', { name: /Babelio/ })).toBeInTheDocument();
});

test('ne montre rien si le serveur est injoignable', async () => {
  fetchExternalRatings.mockRejectedValue(new Error('offline'));
  const { container } = render(<ExternalRatings title="X Y Z" />);
  await waitFor(() => expect(fetchExternalRatings).toHaveBeenCalled());
  await act(async () => {
    await new Promise((r) => setTimeout(r, 0));
  });
  expect(container).toBeEmptyDOMElement();
});
