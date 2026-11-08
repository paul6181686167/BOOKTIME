import { API_BASE_URL } from '../../config/environment';
import {
  SLOW_BACKEND_EVENT,
  SLOW_BACKEND_MS,
  beginBackendRequest,
  __resetSlowBackendNotice,
} from '../slowBackendNotice';

describe('slowBackendNotice', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    __resetSlowBackendNotice();
  });

  afterEach(() => {
    __resetSlowBackendNotice();
    jest.useRealTimers();
  });

  test('signale un backend lent après le délai, puis se tait à la fin', () => {
    const seen = [];
    const onChange = (e) => seen.push(e.detail.slow);
    window.addEventListener(SLOW_BACKEND_EVENT, onChange);

    const end = beginBackendRequest(`${API_BASE_URL}/api/books`);
    jest.advanceTimersByTime(SLOW_BACKEND_MS - 50);
    expect(seen).toEqual([]);
    jest.advanceTimersByTime(100);
    expect(seen).toEqual([true]);
    end();
    expect(seen).toEqual([true, false]);

    window.removeEventListener(SLOW_BACKEND_EVENT, onChange);
  });

  test('ignore Open Library et n’émet rien si la requête est rapide', () => {
    const seen = [];
    window.addEventListener(SLOW_BACKEND_EVENT, (e) => seen.push(e.detail.slow));
    const end = beginBackendRequest('https://openlibrary.org/search.json');
    jest.advanceTimersByTime(SLOW_BACKEND_MS + 500);
    end();
    expect(seen).toEqual([]);
  });
});
