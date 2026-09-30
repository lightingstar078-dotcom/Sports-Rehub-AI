import { useEffect, useState } from 'react';
import { api, getOnlineApiUrl, saveOnlineApiUrl } from '../services/api';
import { localRuntimeAvailable, resolveNetwork } from '../services/network';
import { useAppStore } from '../store/appStore';

export function Settings() {
  const mode = useAppStore(s => s.network); const setNetwork = useAppStore(s => s.setNetwork);
  const [status, setStatus] = useState<any>(); const [onlineUrl, setOnlineUrl] = useState(getOnlineApiUrl());
  const [localReady, setLocalReady] = useState<boolean>(); const [message, setMessage] = useState('');
  async function refresh() {
    setLocalReady(await localRuntimeAvailable());
    const selected = await resolveNetwork(); setNetwork(selected);
    api<any>('/api/system/status', undefined, selected).then(setStatus).catch(() => setStatus(undefined));
  }
  useEffect(() => { void refresh(); }, []);
  async function saveOnline() {
    try { saveOnlineApiUrl(onlineUrl); await refresh(); setMessage(getOnlineApiUrl() ? 'Online API saved and checked.' : 'Online API removed. The app will use the local runtime.'); }
    catch (error: any) { setMessage(error.message); }
  }
  return <div className="two-col">
    <section className="card form-card"><div className="card-head"><div><h2>Connection Mode</h2><p>Offline uses the FastAPI service running on this computer. Online uses your deployed Render API.</p></div></div>
      <div className="status-list"><div className="status-row"><span>Local offline runtime</span><b>{localReady === undefined ? 'checking…' : localReady ? 'READY on 127.0.0.1:8000' : 'NOT RUNNING'}</b></div><div className="status-row"><span>Current mode</span><b>{mode}</b></div></div>
      <label className="range-label"><span>Online API URL (Render)</span><input value={onlineUrl} onChange={event => setOnlineUrl(event.target.value)} placeholder="https://your-service.onrender.com" /></label>
      <div className="actions"><button className="primary" onClick={saveOnline}>Save & Check Connection</button><button className="secondary" onClick={() => { setOnlineUrl(''); saveOnlineApiUrl(''); void refresh(); }}>Use Local Offline Mode</button></div>
      {message && <p className="profile-strip">{message}</p>}
    </section>
    <section className="card"><div className="card-head"><div><h2>System Status</h2><p>Capability checks for the selected runtime.</p></div></div>{status ? <div className="status-list">{Object.entries(status).map(([key, value]) => <div className="status-row" key={key}><span>{key.replaceAll('_', ' ')}</span><b>{typeof value === 'object' ? JSON.stringify(value) : String(value)}</b></div>)}</div> : <div className="empty">Start the local backend or configure a reachable online API.</div>}</section>
  </div>;
}
