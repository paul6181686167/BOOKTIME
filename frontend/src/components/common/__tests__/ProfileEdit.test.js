import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import ProfileEditForm, {
  buildProfilePatch,
  normalizeHandleInput,
  validateHandle,
} from '../ProfileEditForm';
import ProfileIdentityCard from '../ProfileIdentityCard';
import AuthService from '../../../services/authService';

const mockUpdateUser = jest.fn();
let mockUser;
const mockToast = {};

jest.mock('../../../hooks/useAuth', () => ({
  useAuth: () => ({ user: mockUser, updateUser: mockUpdateUser }),
}));
jest.mock('react-hot-toast', () => {
  const toast = () => {};
  toast.loading = (...a) => mockToast.loading?.(...a);
  toast.success = (...a) => mockToast.success?.(...a);
  toast.error = (...a) => mockToast.error?.(...a);
  return { __esModule: true, default: toast };
});

afterEach(() => {
  jest.restoreAllMocks();
});

beforeEach(() => {
  mockUser = { email: 'a@b.fr', display_name: 'Alice', bio: 'Lectrice', avatar_url: '' };
  mockUpdateUser.mockReset();
  mockToast.loading = jest.fn(() => 't1');
  mockToast.success = jest.fn();
  mockToast.error = jest.fn();
});

describe('buildProfilePatch', () => {
  test('ne contient que ce qui a changé', () => {
    expect(buildProfilePatch(mockUser, { name: ' Alice ', bio: 'Lectrice', avatar: undefined })).toEqual({});
    expect(buildProfilePatch(mockUser, { name: 'Alicia', bio: 'Lectrice', avatar: '' })).toEqual({
      display_name: 'Alicia',
      avatar_url: '',
    });
  });
});

describe('pseudo', () => {
  test('normalise et valide le pseudo saisi', () => {
    expect(normalizeHandleInput('  @Alice.SF ')).toBe('alice.sf');
    expect(validateHandle('')).toBe('');
    expect(validateHandle('ab')).toMatch(/Entre 3 et 20/);
    expect(validateHandle('éric')).toMatch(/sans accent/);
    expect(validateHandle('alice_sf')).toBe('');
  });

  test('entre dans le patch seulement s’il change', () => {
    const base = { name: 'Alice', bio: 'Lectrice', avatar: undefined };
    expect(buildProfilePatch({ ...mockUser, username: 'alice' }, { ...base, username: '@Alice' })).toEqual({});
    expect(buildProfilePatch(mockUser, { ...base, username: '@Alice' })).toEqual({ username: 'alice' });
    expect(buildProfilePatch({ ...mockUser, username: 'alice' }, { ...base, username: '' })).toEqual({
      username: '',
    });
  });

  test('un pseudo invalide bloque l’enregistrement', () => {
    const update = jest.spyOn(AuthService.prototype, 'updateProfile');
    render(<ProfileEditForm onDone={jest.fn()} />);
    fireEvent.change(screen.getByLabelText('Pseudo'), { target: { value: 'ab' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer' }));
    expect(update).not.toHaveBeenCalled();
    expect(mockToast.error).toHaveBeenCalled();
  });
});

describe('carte de profil', () => {
  test("n'a plus de bouton de modification (réservé aux paramètres)", () => {
    jest.spyOn(AuthService.prototype, 'fetchProfile').mockResolvedValue({ success: false });
    render(<ProfileIdentityCard />);
    expect(screen.getByText('Alice')).toBeInTheDocument();
    expect(screen.getByText(/Aucun pseudo/)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Modifier/ })).toBeNull();
  });

  test('affiche le @pseudo quand il existe', () => {
    mockUser = { ...mockUser, username: 'alice' };
    jest.spyOn(AuthService.prototype, 'fetchProfile').mockResolvedValue({ success: false });
    render(<ProfileIdentityCard />);
    expect(screen.getByText('@alice')).toBeInTheDocument();
  });

  test('« Choisir un pseudo » ouvre l’éditeur si on le demande', () => {
    jest.spyOn(AuthService.prototype, 'fetchProfile').mockResolvedValue({ success: false });
    const onEdit = jest.fn();
    render(<ProfileIdentityCard onEditProfile={onEdit} />);
    fireEvent.click(screen.getByRole('button', { name: 'Choisir un pseudo' }));
    expect(onEdit).toHaveBeenCalled();
  });
});

describe('enregistrement du profil', () => {
  test('est optimiste : le profil change et le formulaire se ferme avant la réponse du serveur', async () => {
    let resolveSave;
    jest.spyOn(AuthService.prototype, 'updateProfile').mockImplementation(
      () => new Promise((resolve) => (resolveSave = resolve))
    );
    const onDone = jest.fn();
    render(<ProfileEditForm onDone={onDone} />);

    fireEvent.change(screen.getByLabelText('Nom affiché'), { target: { value: 'Alicia' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer' }));

    expect(mockUpdateUser).toHaveBeenCalledWith({ display_name: 'Alicia' });
    expect(onDone).toHaveBeenCalledTimes(1);

    await act(async () => resolveSave({ success: true, profile: { display_name: 'Alicia', bio: 'Lectrice', avatar_url: '' } }));
    await waitFor(() => expect(mockToast.success).toHaveBeenCalled());
  });

  test('rétablit le profil précédent et prévient si le serveur refuse', async () => {
    jest.spyOn(AuthService.prototype, 'updateProfile').mockResolvedValue({ success: false, error: 'Photo trop volumineuse.' });
    render(<ProfileEditForm onDone={() => {}} />);
    fireEvent.change(screen.getByLabelText('Biographie'), { target: { value: 'Nouvelle bio' } });
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer' }));

    await waitFor(() => expect(mockToast.error).toHaveBeenCalled());
    expect(mockToast.error.mock.calls[0][0]).toContain('Photo trop volumineuse.');
    expect(mockUpdateUser).toHaveBeenLastCalledWith({ display_name: 'Alice', bio: 'Lectrice', avatar_url: '' });
  });

  test('sans modification, ferme sans appeler le serveur', () => {
    const spy = jest.spyOn(AuthService.prototype, 'updateProfile');
    const onDone = jest.fn();
    render(<ProfileEditForm onDone={onDone} />);
    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer' }));
    expect(onDone).toHaveBeenCalled();
    expect(spy).not.toHaveBeenCalled();
  });
});

describe('AuthService.updateProfile', () => {
  const service = () => new AuthService();
  const opts = { attempts: 3, timeoutMs: 50, retryDelayMs: 1 };

  test('relance après une panne réseau puis réussit', async () => {
    global.fetch = jest
      .fn()
      .mockRejectedValueOnce(new Error('Failed to fetch'))
      .mockResolvedValueOnce({ ok: true, status: 200, json: () => Promise.resolve({ profile: { bio: 'x' } }) });
    const res = await service().updateProfile({ bio: 'x' }, opts);
    expect(res).toEqual({ success: true, profile: { bio: 'x' } });
    expect(global.fetch).toHaveBeenCalledTimes(2);
  });

  test('ne relance pas une erreur de validation (4xx)', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: () => Promise.resolve({ detail: 'Photo trop volumineuse.' }),
    });
    const res = await service().updateProfile({ avatar_url: 'x' }, opts);
    expect(res).toEqual({ success: false, error: 'Photo trop volumineuse.' });
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  test('relance les erreurs serveur puis abandonne avec un message', async () => {
    global.fetch = jest.fn().mockResolvedValue({ ok: false, status: 503, json: () => Promise.resolve({}) });
    const res = await service().updateProfile({ bio: 'x' }, opts);
    expect(res.success).toBe(false);
    expect(global.fetch).toHaveBeenCalledTimes(3);
  });
});
