import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import UpdateBanner from '../UpdateBanner';
import { UPDATE_READY_EVENT } from '../../utils/registerServiceWorker';

test('invisible tant qu’aucune mise à jour n’est prête', () => {
  render(<UpdateBanner />);
  expect(screen.queryByTestId('update-banner')).toBeNull();
});

test('apparaît quand une nouvelle version est prête, et peut être repoussée', () => {
  render(<UpdateBanner />);
  act(() => {
    window.dispatchEvent(new Event(UPDATE_READY_EVENT));
  });
  expect(screen.getByTestId('update-banner')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Mettre à jour' })).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Plus tard' }));
  expect(screen.queryByTestId('update-banner')).toBeNull();
});
