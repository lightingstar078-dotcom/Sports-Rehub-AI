const localBase=import.meta.env.VITE_LOCAL_API_URL || 'http://127.0.0.1:8000';
const onlineBase=import.meta.env.VITE_API_URL || '';

/** A deployment only has an online API when its build-time URL was supplied. */
export const hasOnlineApi = Boolean(onlineBase.trim());

export function getBase(mode:'ONLINE'|'OFFLINE'){
  return mode==='ONLINE' && onlineBase ? onlineBase.replace(/\/$/,'') : localBase.replace(/\/$/,'');
}
export async function api<T>(path:string, init?:RequestInit, mode:'ONLINE'|'OFFLINE'='OFFLINE'):Promise<T>{
  let res: Response;
  try { res=await fetch(`${getBase(mode)}${path}`,init); }
  catch { throw new Error('The selected API is unavailable. Start the local backend or configure VITE_API_URL for the deployed API.'); }
  if(!res.ok){let msg=await res.text();try{msg=JSON.parse(msg).detail||msg}catch{};throw new Error(msg||`HTTP ${res.status}`)}
  return res.json();
}
export async function checkApi(mode:'ONLINE'|'OFFLINE'){try{await api('/api/health',undefined,mode); return true}catch{return false}}
