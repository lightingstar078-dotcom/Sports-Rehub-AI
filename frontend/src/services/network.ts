import { checkApi, hasOnlineApi } from './api';

export async function resolveNetwork() {
  if (!navigator.onLine || !hasOnlineApi()) return 'OFFLINE' as const;
  return await checkApi('ONLINE') ? 'ONLINE' as const : 'OFFLINE' as const;
}

/** Whether the local FastAPI runtime required for offline assessments is up. */
export async function localRuntimeAvailable() { return checkApi('OFFLINE'); }
