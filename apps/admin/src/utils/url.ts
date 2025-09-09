/**
 * Convert a relative URL (e.g. /static/uploads/...) to an absolute backend URL.
 * Honours VITE_API_BASE and maps Vite dev ports (5173–5176) to http://<host>:8000.
 */
export function resolveBackendUrl(u: string | null | undefined): string | null {
  if (!u) return null;
  const url = u;

  // Protocol-relative
  if (url.startsWith('//')) {
    try {
      return (typeof window !== 'undefined' ? window.location.protocol : 'http:') + url;
    } catch {
      return 'http:' + url;
    }
  }
  // Already absolute http/https
  if (/^https?:\/\//i.test(url)) return url;

  // API base
  let base: string | undefined;
  try {
    const envBase = (import.meta as ImportMeta & { env?: Record<string, string | undefined> })?.env
      ?.VITE_API_BASE as string | undefined;
    if (envBase) base = envBase.replace(/\/+$/, '');
  } catch {
    // ignore
  }
  if (!base) {
    try {
      const loc = window.location;
      const isViteDev = /^517[3-6]$/.test(String(loc.port || ''));
      if (isViteDev) base = `${loc.protocol}//${loc.hostname}:8000`;
    } catch {
      // ignore
    }
  }

  if (url.startsWith('/')) return (base || '') + url;
  return (base || '') + '/' + url.replace(/^\.?\//, '');
}

/**
 * Extracts a URL from a typical upload response body or Location header
 * and normalizes it to an absolute backend URL.
 */
export function extractUrlFromUploadResponse(data: unknown, headers?: Headers): string | null {
  // Gather potential URL candidates from common response shapes or Location header
  const candidate: unknown =
    (data &&
      typeof data === 'object' &&
      ((((data as Record<string, unknown>).file as { url?: unknown } | undefined)?.url ??
        (data as Record<string, unknown>).url ??
        (data as Record<string, unknown>).path ??
        (data as Record<string, unknown>).location) as unknown)) ??
    (typeof data === 'string' ? (data as unknown) : null) ??
    (headers ? (headers.get('Location') as unknown) : null);

  if (candidate == null) return null;

  let u = '';
  // Normalize: trim and remove surrounding quotes/escaping when present
  try {
    u = String(candidate).trim();
    // If string looks like "\"/static/...\"" — unescape and strip quotes
    if (/^\\?[\"'].*\\?[\"']$/.test(u)) {
      u = u.replace(/\\\"/g, '"').replace(/\\'/g, "'");
    }
    if ((u.startsWith('"') && u.endsWith('"')) || (u.startsWith("'") && u.endsWith("'"))) {
      u = u.slice(1, -1).trim();
    }
  } catch {
    // noop
  }

  return resolveBackendUrl(u || null);
}

