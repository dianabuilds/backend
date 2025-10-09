const CSRF_COOKIE = 'XSRF-TOKEN';
const CSRF_STORAGE_KEY = 'auth.csrf_token';

let csrfTokenCache: string | null = null;

function rememberCsrfToken(token: string | null | undefined): string | null {
  const normalized = typeof token === 'string' && token.trim() ? token.trim() : null;
  csrfTokenCache = normalized;
  try {
    if (typeof sessionStorage !== 'undefined') {
      if (normalized) sessionStorage.setItem(CSRF_STORAGE_KEY, normalized);
      else sessionStorage.removeItem(CSRF_STORAGE_KEY);
    }
  } catch {
    // ignore
  }
  try {
    if (typeof localStorage !== 'undefined') {
      if (normalized) localStorage.setItem(CSRF_STORAGE_KEY, normalized);
      else localStorage.removeItem(CSRF_STORAGE_KEY);
    }
  } catch {
    // ignore
  }
  return csrfTokenCache;
}

function loadStoredCsrfToken(): string | null {
  try {
    if (typeof sessionStorage !== 'undefined') {
      const value = sessionStorage.getItem(CSRF_STORAGE_KEY);
      if (value && value.length) return value;
    }
  } catch {
    // ignore
  }
  try {
    if (typeof localStorage !== 'undefined') {
      const value = localStorage.getItem(CSRF_STORAGE_KEY);
      if (value && value.length) return value;
    }
  } catch {
    // ignore
  }
  return null;
}

csrfTokenCache = loadStoredCsrfToken();

function parseCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const raw = document.cookie || '';
  if (!raw) return null;
  const parts = raw.split(';');
  for (const part of parts) {
    const trimmed = part.trim();
    if (!trimmed) continue;
    const eq = trimmed.indexOf('=');
    if (eq === -1) continue;
    const key = trimmed.slice(0, eq).trim();
    if (key === name) {
      const value = trimmed.slice(eq + 1);
      try {
        return decodeURIComponent(value);
      } catch {
        return value;
      }
    }
  }
  return null;
}

export function getCookie(nameContains: string): string | null {
  try {
    if (typeof document === 'undefined') return null;
    const normalized = nameContains.trim();
    if (!normalized) return null;
    const exact = parseCookie(normalized);
    if (exact !== null) return exact;
    const cookies = document.cookie.split(';');
    for (const entry of cookies) {
      const trimmed = entry.trim();
      if (!trimmed) continue;
      const eq = trimmed.indexOf('=');
      const key = eq === -1 ? trimmed : trimmed.slice(0, eq);
      if (key.toLowerCase().includes(normalized.toLowerCase())) {
        const value = eq >= 0 ? trimmed.slice(eq + 1) : '';
        try {
          return decodeURIComponent(value);
        } catch {
          return value;
        }
      }
    }
    return null;
  } catch {
    return null;
  }
}

export function csrfHeaders(): Record<string, string> {
  const headers: Record<string, string> = {};
  const token = csrfTokenCache || parseCookie(CSRF_COOKIE);
  if (token) headers['X-CSRF-Token'] = token;
  return headers;
}

export function syncCsrfFromResponse(res: Response): void {
  const headerToken =
    res.headers.get('X-CSRF-Token') ||
    res.headers.get('x-csrf-token') ||
    res.headers.get('x-xsrf-token');
  if (headerToken) rememberCsrfToken(headerToken);
  if (typeof document !== 'undefined') {
    try {
      const domToken = parseCookie(CSRF_COOKIE);
      if (domToken && domToken !== csrfTokenCache) rememberCsrfToken(domToken);
    } catch {
      // ignore
    }
  }
}

export function setCsrfToken(token?: string | null): void {
  rememberCsrfToken(token ?? null);
}

export function clearCsrfToken(): void {
  rememberCsrfToken(null);
}

export function primeCsrfFromCookies(): void {
  const token = parseCookie(CSRF_COOKIE);
  if (token) rememberCsrfToken(token);
}

export function getCsrfToken(): string | null {
  return csrfTokenCache;
}