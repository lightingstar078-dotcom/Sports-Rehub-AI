import { useEffect, useState } from 'react';
import { api, checkApi, getOnlineApiUrl, hasOnlineApi, saveOnlineApiUrl } from '../services/api';
import { localRuntimeAvailable, resolveNetwork, setPreferredMode } from '../services/network';
import { useAppStore } from '../store/appStore';

type RefreshResult = { local: boolean; online: boolean; selected: 'ONLINE' | 'OFFLINE' };

export function Settings() {
  const mode = useAppStore(s => s.network);
  const setNetwork = useAppStore(s => s.setNetwork);
  const [status, setStatus] = useState<any>();
  const [onlineUrl, setOnlineUrl] = useState(getOnlineApiUrl());
  const [localReady, setLocalReady] = useState<boolean>();
  const [onlineReady, setOnlineReady] = useState<boolean>();
  const [message, setMessage] = useState('');
  const [checking, setChecking] = useState(false);

  async function refresh(): Promise<RefreshResult> {
    setChecking(true);
    const [local, online] = await Promise.all([
      localRuntimeAvailable(),
      hasOnlineApi() && navigator.onLine ? checkApi('ONLINE') : Promise.resolve(false),
    ]);
    setLocalReady(local);
    setOnlineReady(online);
    const selected = await resolveNetwork();
    setNetwork(selected);
    try {
      setStatus(await api('/api/system/status', undefined, selected));
    } catch {
      setStatus(undefined);
    } finally {
      setChecking(false);
    }
    return { local, online, selected };
  }

  useEffect(() => { void refresh(); }, []);

  async function connectOnline() {
    try {
      const saved = saveOnlineApiUrl(onlineUrl);
      if (!saved) throw new Error('Enter your deployed FastAPI URL, for example https://your-service.onrender.com.');
      setPreferredMode('ONLINE');
      const result = await refresh();
      setMessage(result.online
        ? 'Online API connected successfully.'
        : result.local
          ? 'API URL saved, but its health check failed. The app is using the local backend; check the Render URL, service status, and CORS settings.'
          : 'API URL saved, but neither backend responded. Check the Render URL/service, or start the local backend.');
    } catch (error: any) {
      setMessage(error.message || 'Could not save the online API URL.');
    }
  }

  async function useOffline() {
    setPreferredMode('OFFLINE');
    const result = await refresh();
    setMessage(result.local
      ? 'Offline mode selected. The local FastAPI backend is ready.'
      : 'Offline mode selected, but the local backend did not respond. Start it at 127.0.0.1:8000.');
  }

  async function useOnline() {
    if (!hasOnlineApi()) {
      setMessage('Add the deployed FastAPI URL first, then select online mode.');
      return;
    }
    setPreferredMode('ONLINE');
    const result = await refresh();
    setMessage(result.online
      ? 'Online mode selected and the API is reachable.'
      : result.local
        ? 'The online API is unavailable. Using the local backend until it responds.'
        : 'Online API is unreachable and no local backend is running. Check the API URL and service status.');
  }

  return <div className="two-col">
    <section className="card form-card">
      <div className="card-head"><div><h2>Connection Mode</h2><p>Offline uses FastAPI on this computer. Online uses your deployed FastAPI service. The saved API URL is preserved when switching modes.</p></div></div>
      <div className="status-list">
        <div className="status-row"><span>Local offline runtime</span><b>{localReady === undefined ? 'CHECKING' : localReady ? 'READY · 127.0.0.1:8000' : 'NOT RUNNING'}</b></div>
        <div className="status-row"><span>Online API</span><b>{!hasOnlineApi() ? 'URL NOT CONFIGURED' : onlineReady === undefined ? 'CHECKING' : onlineReady ? 'REACHABLE' : 'UNREACHABLE'}</b></div>
        <div className="status-row"><span>Active connection</span><b>{mode}</b></div>
      </div>
      <label className="range-label"><span>Online API URL (Render)</span><input value={onlineUrl} onChange={event => setOnlineUrl(event.target.value)} placeholder="https://your-service.onrender.com" autoComplete="url" /></label>
      <div className="actions">
        <button className="primary" onClick={connectOnline} disabled={checking}>{checking ? 'Checking…' : 'Save URL & Connect Online'}</button>
        <button className="secondary" onClick={useOnline} disabled={checking}>Use Online Mode</button>
        <button className="secondary" onClick={useOffline} disabled={checking}>Use Local Offline Mode</button>
      </div>
      {message && <p className="profile-strip" role="status">{message}</p>}
    </section>
    <section className="card">
      <div className="card-head"><div><h2>System Status</h2><p>Capabilities of the currently selected backend.</p></div><button className="ghost" onClick={() => void refresh()} disabled={checking}>{checking ? 'Checking…' : 'Refresh'}</button></div>
      {status ? <div className="status-list">{Object.entries(status).map(([key, value]) => <div className="status-row" key={key}><span>{key.replaceAll('_', ' ')}</span><b>{typeof value === 'object' ? JSON.stringify(value) : String(value)}</b></div>)}</div> : <div className="empty">{checking ? 'Checking backend…' : 'The selected backend did not respond. Check the connection above.'}</div>}
    </section>
  </div>;
}
