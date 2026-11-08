import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import ConfirmHost from '../ConfirmHost';
import { confirmAction } from '../../../utils/confirmDialog';

test('sans fenêtre montée, retombe sur window.confirm', async () => {
  const spy = jest.spyOn(window, 'confirm').mockReturnValue(true);
  await expect(confirmAction('Sûr ?')).resolves.toBe(true);
  expect(spy).toHaveBeenCalledWith('Sûr ?');
  spy.mockRestore();
});

test('affiche la question et renvoie true au clic sur Confirmer', async () => {
  render(<ConfirmHost />);
  let result;
  await act(async () => {
    result = confirmAction('Supprimer cette série ?', { confirmLabel: 'Supprimer' });
  });
  expect(screen.getByText('Supprimer cette série ?')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Supprimer' }));
  await expect(result).resolves.toBe(true);
  expect(screen.queryByTestId('confirm-dialog')).toBeNull();
});

test('renvoie false avec Annuler ou la touche Échap', async () => {
  render(<ConfirmHost />);
  let result;
  await act(async () => {
    result = confirmAction('Continuer ?');
  });
  fireEvent.click(screen.getByRole('button', { name: 'Annuler' }));
  await expect(result).resolves.toBe(false);

  await act(async () => {
    result = confirmAction('Encore ?');
  });
  fireEvent.keyDown(document, { key: 'Escape' });
  await expect(result).resolves.toBe(false);
});
