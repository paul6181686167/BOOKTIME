import { API_BASE_URL } from '../config/environment';
import { getToken } from './apiClient';

export class AdminError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function request(method, path, body) {
  const token = getToken();
  const res = await fetch(`${API_BASE_URL}/api/admin${path}`, {
    method,
    headers: {
      ...(body ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const detail =
      typeof data.detail === 'string' ? data.detail : data.detail?.[0]?.msg || 'Action impossible';
    throw new AdminError(detail, res.status);
  }
  return data;
}

const adminService = {
  getStats: () => request('GET', '/stats'),
  listUsers: ({ q = '', status = 'all', skip = 0, limit = 20 } = {}) => {
    const params = new URLSearchParams({ status, skip: String(skip), limit: String(limit) });
    if (q.trim()) params.set('q', q.trim());
    return request('GET', `/users?${params.toString()}`);
  },
  banUser: (userId, reason) => request('POST', `/users/${userId}/ban`, { reason: reason || '' }),
  unbanUser: (userId) => request('POST', `/users/${userId}/unban`),
};

export default adminService;
