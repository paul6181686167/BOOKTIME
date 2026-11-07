import React from 'react';
import { render, fireEvent, screen } from '@testing-library/react';
import ModalOverlay from '../ModalOverlay';

describe('ModalOverlay', () => {
  it('est rendue dans document.body avec la sémantique de dialogue', () => {
    const { container } = render(
      <div style={{ transform: 'translate3d(0,0,0)' }}>
        <ModalOverlay onClose={() => {}} ariaLabel="Test">
          <button>ok</button>
        </ModalOverlay>
      </div>
    );
    const dialog = screen.getByRole('dialog', { name: 'Test' });
    expect(dialog.parentElement).toBe(document.body);
    expect(container.contains(dialog)).toBe(false);
    expect(dialog.getAttribute('aria-modal')).toBe('true');
  });

  it('ferme au clic sur le fond, pas sur le contenu', () => {
    const onClose = jest.fn();
    render(
      <ModalOverlay onClose={onClose} ariaLabel="Fond">
        <button>contenu</button>
      </ModalOverlay>
    );
    fireEvent.click(screen.getByText('contenu'));
    expect(onClose).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole('dialog'));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('ne ferme pas sur le fond quand closeOnBackdrop est faux', () => {
    const onClose = jest.fn();
    render(
      <ModalOverlay onClose={onClose} closeOnBackdrop={false} ariaLabel="Formulaire">
        <p>x</p>
      </ModalOverlay>
    );
    fireEvent.click(screen.getByRole('dialog'));
    expect(onClose).not.toHaveBeenCalled();
  });

  it('Échap ne ferme que la fenêtre du dessus', () => {
    const bottom = jest.fn();
    const top = jest.fn();
    render(
      <>
        <ModalOverlay onClose={bottom} ariaLabel="Dessous"><p>a</p></ModalOverlay>
        <ModalOverlay onClose={top} ariaLabel="Dessus"><p>b</p></ModalOverlay>
      </>
    );
    fireEvent.keyDown(document, { key: 'Escape' });
    expect(top).toHaveBeenCalledTimes(1);
    expect(bottom).not.toHaveBeenCalled();
  });

  it('place le focus dans la fenêtre à l’ouverture', () => {
    render(
      <ModalOverlay onClose={() => {}} ariaLabel="Focus">
        <button>un</button>
      </ModalOverlay>
    );
    expect(screen.getByRole('dialog')).toHaveFocus();
  });

  it('garde Tab et Maj+Tab dans la fenêtre', () => {
    render(
      <ModalOverlay onClose={() => {}} ariaLabel="Piège">
        <button>premier</button>
        <button>dernier</button>
      </ModalOverlay>
    );
    const first = screen.getByText('premier');
    const last = screen.getByText('dernier');

    last.focus();
    fireEvent.keyDown(document, { key: 'Tab' });
    expect(first).toHaveFocus();

    first.focus();
    fireEvent.keyDown(document, { key: 'Tab', shiftKey: true });
    expect(last).toHaveFocus();
  });
});
