/**
 * Réveil backend Render (plan gratuit ~15 min d'inactivité) + retries.
 * En local (localhost) : ping rapide, pas de boucle longue.
 */

import { API_BASE_URL, API_ENDPOINTS } from '../config/environment';

const RENDER_HOST_HINTS = ['onrender.com', 'railway.app'];

function isRemoteHostedBackend() {
  try {
    const host = new URL(API_BASE_URL).hostname;
    return RENDER_HOST_HINTS.some((h) => host.includes(h));
  } catch {
    return false;
  }
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * @param {{ onProgress?: (msg: string) => void, maxAttempts?: number }} opts
 * @returns {Promise<{ ok: boolean, data?: object, attempts: number }>}
 */
export async function wakeBackend(opts = {}) {
  const { onProgress, maxAttempts } = opts;
  const remote = isRemoteHostedBackend();
  const attempts = maxAttempts ?? (remote ? 8 : 2);
  const pingUrl = remote ? `${API_BASE_URL}/ping` : API_ENDPOINTS.HEALTH;
  const timeoutMs = remote ? 45000 : 8000;
  const delayMs = remote ? 8000 : 2000;

  for (let i = 1; i <= attempts; i += 1) {
    if (onProgress && i > 1) {
      onProgress(
        remote
          ? `Réveil du serveur… (${i}/${attempts})`
          : `Connexion au backend… (${i}/${attempts})`
      );
    }
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), timeoutMs);
      const res = await fetch(pingUrl, { method: 'GET', signal: controller.signal });
      clearTimeout(timer);
      if (res.ok) {
        const data = await res.json().catch(() => ({}));
        return { ok: true, data, attempts: i };
      }
    } catch {
      /* retry */
    }
    if (i < attempts) await sleep(delayMs);
  }
  return { ok: false, attempts };
}

export function isBackendRemote() {
  return isRemoteHostedBackend();
}
