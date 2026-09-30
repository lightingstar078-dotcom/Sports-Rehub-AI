import { afterEach, describe, expect, it, vi } from 'vitest';
import { api, getBase, getOnlineApiUrl, saveOnlineApiUrl } from './api';

function mockWindow(protocol = 'http:') {
  const values = new Map<string, string>();
  vi.stubGlobal('window', {
    location: { protocol },
    localStorage: {
      getItem: (key: string) => values.get(key) ?? null,
      setItem: (key: string, value: string) => values.set(key, value),
      removeItem: (key: string) => values.delete(key),
    },
    setTimeout,
    clearTimeout,
  });
}

describe('API URL routing', () => {
  afterEach(() => vi.unstubAllGlobals());

  it('keeps exactly one /api prefix in the request path', async () => {
    mockWindow();
    expect(getBase('OFFLINE')).not.toMatch(/\/api$/);
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ status: 'ok' }), {
      status: 200, headers: { 'Content-Type': 'application/json' },
    }));
    vi.stubGlobal('fetch', fetchMock);

    await api('/api/health', undefined, 'OFFLINE');

    const requestedUrl = String(fetchMock.mock.calls[0][0]);
    expect(requestedUrl).toMatch(/\/api\/health$/);
    expect(requestedUrl).not.toContain('/api/api/');
  });

  it('requires an explicit online API instead of silently routing online requests locally', () => {
    mockWindow();
    expect(() => getBase('ONLINE')).toThrow(/Online API is not configured/);
  });

  it('accepts a service URL ending in /api and stores the service root', () => {
    mockWindow();
    expect(saveOnlineApiUrl('https://rehab-api.example.com/api/')).toBe('https://rehab-api.example.com');
    expect(getOnlineApiUrl()).toBe('https://rehab-api.example.com');
    expect(getBase('ONLINE')).toBe('https://rehab-api.example.com');
  });

  it('rejects insecure remote API URLs from an HTTPS deployment', () => {
    mockWindow('https:');
    expect(() => saveOnlineApiUrl('http://rehab-api.example.com')).toThrow(/requires an HTTPS/);
  });
});
