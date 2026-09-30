import { afterEach, describe, expect, it, vi } from 'vitest';
import { saveOnlineApiUrl } from './api';
import { getPreferredMode, resolveNetwork, setPreferredMode } from './network';

function mockBrowser(online = true) {
  const values = new Map<string, string>();
  vi.stubGlobal('window', {
    location: { protocol: 'https:' },
    localStorage: {
      getItem: (key: string) => values.get(key) ?? null,
      setItem: (key: string, value: string) => values.set(key, value),
      removeItem: (key: string) => values.delete(key),
    },
    setTimeout,
    clearTimeout,
  });
  vi.stubGlobal('navigator', { onLine: online });
}

describe('connection mode selection', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('preserves an explicit offline choice and does not probe the cloud', async () => {
    mockBrowser();
    saveOnlineApiUrl('https://rehab-api.example.com');
    setPreferredMode('OFFLINE');
    const fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);

    expect(getPreferredMode()).toBe('OFFLINE');
    expect(await resolveNetwork()).toBe('OFFLINE');
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('selects the configured online service when its health probe succeeds', async () => {
    mockBrowser();
    saveOnlineApiUrl('https://rehab-api.example.com');
    setPreferredMode('ONLINE');
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: 'ok' }), {
      status: 200, headers: { 'Content-Type': 'application/json' },
    })));

    expect(await resolveNetwork()).toBe('ONLINE');
  });
});
