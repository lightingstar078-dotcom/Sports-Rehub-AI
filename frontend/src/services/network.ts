import { checkApi, hasOnlineApi } from './api';
export async function resolveNetwork(){
  if(!navigator.onLine) return 'OFFLINE' as const;
  // Without a deployed API URL, an "ONLINE" check would quietly use the
  // local API and incorrectly label a local-only installation as online.
  if(!hasOnlineApi) return 'OFFLINE' as const;
  const online = await checkApi('ONLINE');
  return online ? 'ONLINE' as const : 'OFFLINE' as const;
}
