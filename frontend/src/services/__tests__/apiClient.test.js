import { API_BASE_URL } from '../../config/environment';
import {
  UNAUTHORIZED_EVENT,
  authHeaders,
  apiFetch,
  getToken,
  installUnauthorizedWatcher,
  notifyUnauthorized,
} from '../apiClient';

const baseFetch = jest.fn();
let events;
const onEvent = () => events.push(1);

beforeAll(() => {
  window.fetch = baseFetch;
  installUnauthorizedWatcher();
  // Une seconde installation ne doit pas ré-envelopper fetch
  installUnauthorizedWatcher();
});

beforeEach(() => {
  baseFetch.mockReset();
  localStorage.clear();
  events = [];
  window.addEventListener(UNAUTHORIZED_EVENT, onEvent);
});

afterEach(() => {
  window.removeEventListener(UNAUTHORIZED_EVENT, onEvent);
});

// notifyUnauthorized() ne se déclenche qu'une fois toutes les 5 s : on avance l'horloge
let now = 1_000_000;
beforeEach(() => {
  now += 60_000;
  jest.spyOn(Date, 'now').mockReturnValue(now);
});
afterEach(() => jest.restoreAllMocks());

describe('jeton', () => {
  test('getToken lit le stockage, authHeaders ajoute Bearer seulement si connecté', () => {
    expect(getToken()).toBeNull();
    expect(authHeaders({ A: '1' })).toEqual({ A: '1' });
    localStorage.setItem('token', 'abc');
    expect(getToken()).toBe('abc');
    expect(authHeaders({ A: '1' })).toEqual({ A: '1', Authorization: 'Bearer abc' });
  });
});

describe('apiFetch', () => {
  test('préfixe l’URL du backend et joint le jeton', async () => {
    localStorage.setItem('token', 'abc');
    baseFetch.mockResolvedValue({ status: 200, ok: true });
    await apiFetch('/api/books', { method: 'GET' });
    const [url, init] = baseFetch.mock.calls[0];
    expect(url).toBe(`${API_BASE_URL}/api/books`);
    expect(init.headers.Authorization).toBe('Bearer abc');
  });

  test('auth:false n’envoie pas le jeton, une URL complète reste inchangée', async () => {
    localStorage.setItem('token', 'abc');
    baseFetch.mockResolvedValue({ status: 200, ok: true });
    await apiFetch('https://exemple.test/x', { auth: false });
    const [url, init] = baseFetch.mock.calls[0];
    expect(url).toBe('https://exemple.test/x');
    expect(init.headers.Authorization).toBeUndefined();
  });

  test('abandonne la requête après le délai maximum', async () => {
    jest.useFakeTimers();
    baseFetch.mockImplementation(
      (_url, init) =>
        new Promise((_resolve, reject) => {
          init.signal.addEventListener('abort', () => reject(new Error('aborted')));
        })
    );
    const pending = apiFetch('/api/lent', { timeoutMs: 1000 });
    jest.advanceTimersByTime(1001);
    await expect(pending).rejects.toThrow('aborted');
    jest.useRealTimers();
  });
});

describe('détection de session expirée', () => {
  test('un 401 du backend avec le jeton courant prévient l’application', async () => {
    localStorage.setItem('token', 'abc');
    baseFetch.mockResolvedValue({ status: 401, ok: false });
    await window.fetch(`${API_BASE_URL}/api/books`, { headers: { Authorization: 'Bearer abc' } });
    expect(events).toHaveLength(1);
  });

  test('un 401 sur la connexion (mauvais mot de passe) ne déconnecte pas', async () => {
    localStorage.setItem('token', 'abc');
    baseFetch.mockResolvedValue({ status: 401, ok: false });
    await window.fetch(`${API_BASE_URL}/api/auth/login`, { headers: { Authorization: 'Bearer abc' } });
    expect(events).toHaveLength(0);
  });

  test('un 401 d’un autre site, ou sans jeton, est ignoré', async () => {
    localStorage.setItem('token', 'abc');
    baseFetch.mockResolvedValue({ status: 401, ok: false });
    await window.fetch('https://openlibrary.org/x', { headers: { Authorization: 'Bearer abc' } });
    await window.fetch(`${API_BASE_URL}/api/books`);
    expect(events).toHaveLength(0);
  });

  test('la réponse tardive d’une ancienne session est ignorée', async () => {
    localStorage.setItem('token', 'nouveau');
    baseFetch.mockResolvedValue({ status: 401, ok: false });
    await window.fetch(`${API_BASE_URL}/api/books`, { headers: { Authorization: 'Bearer ancien' } });
    expect(events).toHaveLength(0);
  });

  test('plusieurs 401 en rafale ne produisent qu’une seule alerte', () => {
    notifyUnauthorized();
    notifyUnauthorized();
    notifyUnauthorized();
    expect(events).toHaveLength(1);
  });
});
