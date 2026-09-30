const localBase = import.meta.env.VITE_LOCAL_API_URL || 'http://127.0.0.1:8000';
const buildTimeOnlineBase = import.meta.env.VITE_API_URL || '';
const ONLINE_API_KEY = 'sports-rehab-ai.online-api-url';

function normaliseUrl(value: string) { return value.trim().replace(/\/$/, ''); }

/** Read the deployed API URL from Vite's build config or the Settings page. */
export function getOnlineApiUrl() {
  const saved = typeof window === 'undefined' ? '' : window.localStorage.getItem(ONLINE_API_KEY) || '';
  return normaliseUrl(saved || buildTimeOnlineBase);
}

export function saveOnlineApiUrl(value: string) {
  const url = normaliseUrl(value);
  if (url && !/^https?:\/\/[^\s]+$/i.test(url)) throw new Error('Use a complete URL beginning with http:// or https://.');
  if (url) window.localStorage.setItem(ONLINE_API_KEY, url);
  else window.localStorage.removeItem(ONLINE_API_KEY);
  return url;
}

export function hasOnlineApi() { return Boolean(getOnlineApiUrl()); }

export function getBase(mode: 'ONLINE' | 'OFFLINE') {
  return mode === 'ONLINE' && hasOnlineApi() ? getOnlineApiUrl() : normaliseUrl(localBase);
}

export async function api<T>(path: string, init?: RequestInit, mode: 'ONLINE' | 'OFFLINE' = 'OFFLINE'): Promise<T> {
  let response: Response;
  try { response = await fetch(`${getBase(mode)}${path}`, init); }
  catch { throw new Error('The selected API is unavailable. Start the local backend or configure the deployed API URL in Settings.'); }
  if (!response.ok) {
    let message = await response.text();
    try { message = JSON.parse(message).detail || message; } catch { /* response was not JSON */ }
    throw new Error(message || `HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function checkApi(mode: 'ONLINE' | 'OFFLINE') {
  try { await api('/api/health', undefined, mode); return true; } catch { return false; }
}
