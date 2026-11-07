import React from 'react';
import { render, screen } from '@testing-library/react';
import AuthorModal from '../AuthorModal';

jest.mock('../../contexts/ThemeContext', () => ({
  useTheme: () => ({ isVoid: false }),
}));
jest.mock('../../services/authorPrefetch', () => ({
  readAuthorProfile: jest.fn(() => Promise.resolve(null)),
}));

describe('AuthorModal', () => {
  beforeEach(() => {
    global.fetch = jest.fn(() =>
      Promise.resolve({ ok: false, status: 404, json: () => Promise.resolve({}) })
    );
  });

  it('est rendue dans document.body, hors du conteneur (carrousel mobile)', () => {
    const { container } = render(
      <div data-testid="slide" style={{ transform: 'translate3d(0,0,0)' }}>
        <AuthorModal author="Albert Camus" isOpen onClose={() => {}} />
      </div>
    );
    const overlay = document.body.querySelector('.modal-overlay');
    expect(overlay).not.toBeNull();
    expect(container.contains(overlay)).toBe(false);
    expect(overlay.parentElement).toBe(document.body);
    const sheet = overlay.querySelector('.modal-content-wide');
    expect(sheet.style.overflowY).toBe('auto');
    expect(screen.getAllByText('Albert Camus').length).toBeGreaterThan(0);
  });
});
