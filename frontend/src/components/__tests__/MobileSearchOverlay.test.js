import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import MobileSearchOverlay from '../MobileSearchOverlay';

jest.mock('../../contexts/ThemeContext', () => ({ useTheme: () => ({ isVoid: false }) }));

function setup(searchTerm = 'dune') {
  const onSearch = jest.fn();
  const onClose = jest.fn();
  render(
    <MobileSearchOverlay
      isOpen
      onClose={onClose}
      searchTerm={searchTerm}
      onSearchChange={() => {}}
      onSearch={onSearch}
    />
  );
  return { onSearch, onClose };
}

test('valider le clavier lance la recherche puis ferme la fenêtre pour montrer les résultats', () => {
  const { onSearch, onClose } = setup('  dune ');
  fireEvent.submit(screen.getByPlaceholderText(/Titre, auteur/).closest('form'));
  expect(onSearch).toHaveBeenCalledWith('dune');
  expect(onClose).toHaveBeenCalledTimes(1);
});

test('le bouton Rechercher fait de même', () => {
  const { onSearch, onClose } = setup('one piece');
  fireEvent.click(screen.getByRole('button', { name: /Rechercher/ }));
  expect(onSearch).toHaveBeenCalledWith('one piece');
  expect(onClose).toHaveBeenCalledTimes(1);
});

test('une saisie vide ne lance rien et ne ferme pas', () => {
  const { onSearch, onClose } = setup('   ');
  fireEvent.submit(screen.getByPlaceholderText(/Titre, auteur/).closest('form'));
  expect(onSearch).not.toHaveBeenCalled();
  expect(onClose).not.toHaveBeenCalled();
});
