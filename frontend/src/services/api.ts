// API callers pass complete `/api/...` paths. The Vite proxy therefore needs
// an empty base (not `/api`, which would accidentally request `/api/api/...`).
const buildTimeLocalBase = serviceBase(import.meta.env.VITE_LOCAL_API_URL || (import.meta.env.DEV ? '' : 'http://127.0.0.1:8000'));
const buildTimeOnlineBase = import.meta.env.VITE_API_URL || '';
const ONLINE_API_KEY = 'sports-rehab-ai.online-api-url';

function normaliseUrl(value: string) { return value.trim().replace(/\/+$/, ''); }
function serviceBase(value: string) { return normaliseUrl(value).replace(/\/api$/i, ''); }

/** Read the deployed API URL from Vite's build config or the Settings page. */
export function getOnlineApiUrl() {
  const saved = typeof window === 'undefined' ? '' : window.localStorage.getItem(ONLINE_API_KEY) || '';
  return serviceBase(saved || buildTimeOnlineBase);
}

export function saveOnlineApiUrl(value: string) {
  let url = normaliseUrl(value);
  if (url) {
    let parsed: URL;
    try { parsed = new URL(url); } catch { throw new Error('Enter a complete API URL such as https://your-service.onrender.com.'); }
    if (!['http:', 'https:'].includes(parsed.protocol) || parsed.username || parsed.password || parsed.search || parsed.hash) {
      throw new Error('Use an http:// or https:// API URL without credentials, query parameters, or a fragment.');
    }
    if (window.location.protocol === 'https:' && parsed.protocol !== 'https:' && !['localhost', '127.0.0.1', '[::1]'].includes(parsed.hostname)) {
      throw new Error('A deployed HTTPS app requires an HTTPS online API URL.');
    }
    // Accept either a service root or a URL ending in /api; callers append
    // their own /api/... paths.
    url = serviceBase(`${parsed.origin}${parsed.pathname}`);
  }
  if (url) window.localStorage.setItem(ONLINE_API_KEY, url);
  else window.localStorage.removeItem(ONLINE_API_KEY);
  return url;
}

export function hasOnlineApi() { return Boolean(getOnlineApiUrl()); }

export function getBase(mode: 'ONLINE' | 'OFFLINE') {
  if (mode === 'ONLINE') {
    const online = getOnlineApiUrl();
    if (!online) throw new Error('Online API is not configured. Add your deployed HTTPS API URL in Settings or set VITE_API_URL before building for Vercel.');
    return online;
  }
  return normaliseUrl(buildTimeLocalBase);
}

export async function api<T>(path: string, init?: RequestInit, mode: 'ONLINE' | 'OFFLINE' = 'OFFLINE'): Promise<T> {
  const base = getBase(mode);
  const url = `${base}${path.startsWith('/') ? path : `/${path}`}`;
  const controller = new AbortController();
  const callerSignal = init?.signal;
  const timeoutMs = path.includes('/assessment') ? 240_000 : path.includes('/detect-human') ? 20_000 : 15_000;
  const timeout = window.setTimeout(() => controller.abort(new DOMException('Request timed out', 'TimeoutError')), timeoutMs);
  const abortFromCaller = () => controller.abort(callerSignal?.reason);
  callerSignal?.addEventListener('abort', abortFromCaller, { once: true });
  let response: Response;
  try { response = await fetch(url, { ...init, signal: controller.signal }); }
  catch (error: any) {
    if (error?.name === 'AbortError' || error?.name === 'TimeoutError') {
      throw new Error(`Request to ${url} timed out after ${Math.round(timeoutMs / 1000)} seconds. Check that the selected backend is running and reachable.`);
    }
    const mixedContent = window.location.protocol === 'https:' && /^http:\/\//i.test(base) && !/^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?\b/i.test(base);
    throw new Error(mixedContent
      ? `Cannot reach ${base}: an HTTPS site cannot call an insecure API. Configure the HTTPS deployed API URL in Settings.`
      : `Cannot reach ${url}. Start the local backend at 127.0.0.1:8000, or configure/check the deployed API URL in Settings.`);
  } finally {
    window.clearTimeout(timeout);
    callerSignal?.removeEventListener('abort', abortFromCaller);
  }
  if (!response.ok) {
    let message = await response.text();
    try { message = JSON.parse(message).detail || message; } catch { /* response was not JSON */ }
    throw new Error(message || `HTTP ${response.status}`);
  }
  try { return await response.json() as T; }
  catch {
    throw new Error(`The server at ${url} returned a non-JSON response. Check that this URL points to the FastAPI backend (not the Vercel frontend).`);
  }
}

export async function checkApi(mode: 'ONLINE' | 'OFFLINE') {
  try {
    const health = await api<{ status?: string }>('/api/health', undefined, mode);
    return health?.status === 'ok';
  } catch { return false; }
}
