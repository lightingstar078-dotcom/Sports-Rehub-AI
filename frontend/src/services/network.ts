import { checkApi, hasOnlineApi } from './api';

export type ConnectionMode = 'ONLINE' | 'OFFLINE';
type PreferredMode = ConnectionMode | 'AUTO';
const MODE_KEY = 'sports-rehab-ai.connection-mode';

export function getPreferredMode(): PreferredMode {
  if (typeof window === 'undefined') return 'AUTO';
  const saved = window.localStorage.getItem(MODE_KEY);
  return saved === 'ONLINE' || saved === 'OFFLINE' ? saved : 'AUTO';
}

export function setPreferredMode(mode: PreferredMode) {
  if (typeof window === 'undefined') return;
  if (mode === 'AUTO') window.localStorage.removeItem(MODE_KEY);
  else window.localStorage.setItem(MODE_KEY, mode);
}

export async function resolveNetwork() {
  const preferred = getPreferredMode();
  if (preferred === 'OFFLINE') return 'OFFLINE' as const;
  if (typeof navigator !== 'undefined' && navigator.onLine && hasOnlineApi() && await checkApi('ONLINE')) {
    return 'ONLINE' as const;
  }
  // Fall back to the local API when the cloud is unavailable. Settings probes
  // both endpoints separately and makes a missing local runtime visible.
  return 'OFFLINE' as const;
}

/** Whether the local FastAPI runtime required for offline assessments is up. */
export async function localRuntimeAvailable() { return checkApi('OFFLINE'); }
