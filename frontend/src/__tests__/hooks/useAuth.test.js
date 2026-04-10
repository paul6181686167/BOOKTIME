import { renderHook, act } from '@testing-library/react';
import { useAuth } from '../../hooks/useAuth';

// Mock du service d'authentification
jest.mock('../../services/authService', () => ({
  login: jest.fn(),
  register: jest.fn(),
  logout: jest.fn(),
  getCurrentUser: jest.fn(),
  isAuthenticated: jest.fn(),
}));

describe('useAuth Hook', () => {
  const mockAuthService = require('../../services/authService');

  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  test('initializes with null user and not loading', () => {
    mockAuthService.getCurrentUser.mockResolvedValue(null);
    
    const { result } = renderHook(() => useAuth());
    
    expect(result.current.user).toBeNull();
    expect(result.current.loading).toBe(true); // Loading initially
  });

  test('loads user on mount', async () => {
    const mockUser = { id: 'test-user', first_name: 'Test', last_name: 'User' };
    mockAuthService.getCurrentUser.mockResolvedValue(mockUser);
    
    const { result, waitForNextUpdate } = renderHook(() => useAuth());
    
    await waitForNextUpdate();
    
    expect(result.current.user).toEqual(mockUser);
    expect(result.current.loading).toBe(false);
  });

  test('handles login successfully', async () => {
    const mockUser = { id: 'test-user', first_name: 'Test', last_name: 'User' };
    const mockToken = 'test-token';
    const loginData = { first_name: 'Test', last_name: 'User' };
    
    mockAuthService.login.mockResolvedValue({
      access_token: mockToken,
      user: mockUser
    });
    
    const { result } = renderHook(() => useAuth());
    
    await act(async () => {
      await result.current.login(loginData);
    });
    
    expect(mockAuthService.login).toHaveBeenCalledWith(loginData);
    expect(result.current.user).toEqual(mockUser);
    expect(localStorage.setItem).toHaveBeenCalledWith('token', mockToken);
  });

  test('handles login failure', async () => {
    const loginData = { first_name: 'Test', last_name: 'User' };
    const errorMessage = 'Invalid credentials';
    
    mockAuthService.login.mockRejectedValue(new Error(errorMessage));
    
    const { result } = renderHook(() => useAuth());
    
    await act(async () => {
      await expect(result.current.login(loginData)).rejects.toThrow(errorMessage);
    });
    
    expect(result.current.user).toBeNull();
  });

  test('handles register successfully', async () => {
    const mockUser = { id: 'test-user', first_name: 'Test', last_name: 'User' };
    const mockToken = 'test-token';
    const registerData = { first_name: 'Test', last_name: 'User' };
    
    mockAuthService.register.mockResolvedValue({
      access_token: mockToken,
      user: mockUser
    });
    
    const { result } = renderHook(() => useAuth());
    
    await act(async () => {
      await result.current.register(registerData);
    });
    
    expect(mockAuthService.register).toHaveBeenCalledWith(registerData);
    expect(result.current.user).toEqual(mockUser);
    expect(localStorage.setItem).toHaveBeenCalledWith('token', mockToken);
  });

  test('handles logout', async () => {
    const mockUser = { id: 'test-user', first_name: 'Test', last_name: 'User' };
    localStorage.setItem('token', 'test-token');
    
    const { result } = renderHook(() => useAuth());
    
    // Set initial user
    act(() => {
      result.current.setUser(mockUser);
    });
    
    await act(async () => {
      await result.current.logout();
    });
    
    expect(mockAuthService.logout).toHaveBeenCalled();
    expect(result.current.user).toBeNull();
    expect(localStorage.removeItem).toHaveBeenCalledWith('token');
  });

  test('handles authentication check', () => {
    mockAuthService.isAuthenticated.mockReturnValue(true);
    localStorage.setItem('token', 'test-token');
    
    const { result } = renderHook(() => useAuth());
    
    expect(result.current.isAuthenticated()).toBe(true);
  });

  test('handles token expiration', async () => {
    const expiredError = {
      response: { status: 401, data: { detail: 'Token expired' } }
    };
    mockAuthService.getCurrentUser.mockRejectedValue(expiredError);
    
    const { result, waitForNextUpdate } = renderHook(() => useAuth());
    
    await waitForNextUpdate();
    
    expect(result.current.user).toBeNull();
    expect(result.current.loading).toBe(false);
  });
});