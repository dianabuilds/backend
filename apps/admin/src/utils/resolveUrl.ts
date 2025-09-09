/**
 * Convert relative URLs (e.g. /static/uploads/...) into absolute ones.
 * Resolves against VITE_API_BASE, maps Vite dev ports (5173–5176) to backend :8000,
 * otherwise falls back to the current window origin.
 */
export function resolveUrl(u?: string): string {
  if (!u) return '';
  try {
    let base = '';
    const envBase = (import.meta as { env?: Record<string, string | undefined> })?.env
      ?.VITE_API_BASE;
    if (envBase) {
      base = envBase;
    } else if (typeof window !== 'undefined' && window.location) {
      const port = window.location.port;
      if (port && ['5173', '5174', '5175', '5176'].includes(port)) {
        // In dev use http backend without TLS to avoid mixed-content issues.
        base = `http://${window.location.hostname}:8000`;
      } else {
        base = `${window.location.protocol}//${window.location.host}`;
      }
    }
    const urlObj = new URL(
      u,
      base || (typeof window !== 'undefined' ? window.location.origin : undefined),
    );
    return urlObj.toString();
  } catch {
    return u;
  }
}
