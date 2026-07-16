import React from 'react';
import { renderHook, act } from '@testing-library/react';
import { useAuth, AuthProvider } from '../../hooks/useAuth';

// authService est une CLASSE (default export) : on mocke le constructeur pour
// renvoyer une instance dont les méthodes sont des jest.fn() pilotables.
const mockLogin = jest.fn();
const mockRegister = jest.fn();
const mockLogout = jest.fn();
const mockGetCurrentUser = jest.fn();

jest.mock('../../services/authService', () => ({
  __esModule: true,
  default: class MockAuthService {
    login(...args) {
      return mockLogin(...args);
    }
    register(...args) {
      return mockRegister(...args);
    }
    logout(...args) {
      return mockLogout(...args);
    }
    getCurrentUser(...args) {
      return mockGetCurrentUser(...args);
    }
  },
}));

const wrapper = ({ children }) => <AuthProvider>{children}</AuthProvider>;

describe('useAuth Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    mockGetCurrentUser.mockReturnValue(null);
  });

  test('lève une erreur hors AuthProvider', () => {
    const spy = jest.spyOn(console, 'error').mockImplementation(() => {});
    expect(() => renderHook(() => useAuth())).toThrow(
      'useAuth must be used within an AuthProvider'
    );
    spy.mockRestore();
  });

  test('initialise avec user null et loading false après montage', () => {
    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.user).toBeNull();
    expect(result.current.loading).toBe(false);
  });

  test('charge l’utilisateur courant au montage', () => {
    const mockUser = { id: 'test-user', email: 'test@example.com' };
    mockGetCurrentUser.mockReturnValue(mockUser);

    const { result } = renderHook(() => useAuth(), { wrapper });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.loading).toBe(false);
  });

  test('connexion réussie : met à jour user', async () => {
    const mockUser = { id: 'test-user', email: 'test@example.com' };
    mockLogin.mockResolvedValue({ success: true, user: mockUser });

    const { result } = renderHook(() => useAuth(), { wrapper });

    let returned;
    await act(async () => {
      returned = await result.current.login('test@example.com', 'pwd123');
    });

    expect(mockLogin).toHaveBeenCalledWith('test@example.com', 'pwd123');
    expect(result.current.user).toEqual(mockUser);
    expect(returned).toEqual({ success: true, user: mockUser });
  });

  test('connexion échouée : user reste null', async () => {
    mockLogin.mockResolvedValue({ success: false, error: 'Invalid credentials' });

    const { result } = renderHook(() => useAuth(), { wrapper });

    let returned;
    await act(async () => {
      returned = await result.current.login('bad@example.com', 'wrong');
    });

    expect(result.current.user).toBeNull();
    expect(returned).toEqual({ success: false, error: 'Invalid credentials' });
  });

  test('inscription réussie : met à jour user', async () => {
    const mockUser = { id: 'new-user', email: 'new@example.com' };
    mockRegister.mockResolvedValue({ success: true, user: mockUser });

    const { result } = renderHook(() => useAuth(), { wrapper });

    await act(async () => {
      await result.current.register('new@example.com', 'pwd123');
    });

    expect(mockRegister).toHaveBeenCalledWith('new@example.com', 'pwd123');
    expect(result.current.user).toEqual(mockUser);
  });

  test('déconnexion : réinitialise user et appelle le service', async () => {
    const mockUser = { id: 'test-user', email: 'test@example.com' };
    mockGetCurrentUser.mockReturnValue(mockUser);

    const { result } = renderHook(() => useAuth(), { wrapper });
    expect(result.current.user).toEqual(mockUser);

    act(() => {
      result.current.logout();
    });

    expect(mockLogout).toHaveBeenCalled();
    expect(result.current.user).toBeNull();
  });
});
