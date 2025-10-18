const DEFAULT_CSRF_COOKIE = 'XSRF-TOKEN';
const DEFAULT_CSRF_HEADER = 'X-CSRF-Token';
const DEFAULT_CSRF_STORAGE_KEY = 'auth.csrf_token';

type CsrfState = {
  token: string;
  expiresAt: number | null;
};

type PersistedCsrfState = {
  token: string;
  expiresAt?: number | null;
  header?: string;
  cookie?: string;
};

type RememberOptions = {
  ttlMs?: number | null;
  ttlSeconds?: number | null;
  headerName?: string;
  cookieName?: string;
  issuedAt?: number;
};

type CsrfConfig = {
  cookieName: string;
  headerName: string;
  storageKey: string;
  ttlMs: number | null;
};

function readEnv(keys: string[]): string | undefined {
  const sources: Array<Record<string, any> | undefined> = [];
  if (typeof import.meta !== 'undefined' && (import.meta as any)?.env) {
    sources.push((import.meta as any).env as Record<string, any>);
  }
  if (typeof process !== 'undefined' && process && typeof process === 'object') {
    sources.push((process as any).env as Record<string, any>);
  }
  for (const source of sources) {
    if (!source) continue;
    for (const key of keys) {
      const value = source[key];
      if (typeof value === 'string' && value.trim().length > 0) {
        return value.trim();
      }
    }
  }
  return undefined;
}

function parseTtlSeconds(value: string | undefined): number | null {
  if (!value) return null;
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return null;
  return numeric > 0 ? numeric : null;
}

const initialCookieName =
  readEnv(['VITE_CSRF_COOKIE_NAME', 'VITE_AUTH_CSRF_COOKIE_NAME', 'APP_AUTH_CSRF_COOKIE_NAME']) ??
  DEFAULT_CSRF_COOKIE;
const initialHeaderName =
  readEnv(['VITE_CSRF_HEADER_NAME', 'VITE_AUTH_CSRF_HEADER_NAME', 'APP_AUTH_CSRF_HEADER_NAME']) ??
  DEFAULT_CSRF_HEADER;
const initialStorageKey = readEnv(['VITE_CSRF_STORAGE_KEY', 'VITE_AUTH_CSRF_STORAGE_KEY']) ?? DEFAULT_CSRF_STORAGE_KEY;
const initialTtlSeconds = parseTtlSeconds(
  readEnv(['VITE_CSRF_TTL_SECONDS', 'VITE_AUTH_CSRF_TTL_SECONDS', 'APP_AUTH_CSRF_TTL_SECONDS']),
);

const csrfConfig: CsrfConfig = {
  cookieName: initialCookieName,
  headerName: initialHeaderName,
  storageKey: initialStorageKey,
  ttlMs: initialTtlSeconds != null ? initialTtlSeconds * 1000 : null,
};

let csrfTokenCache: CsrfState | null = null;

function persistState(state: PersistedCsrfState | null): void {
  const payload = state && state.token ? JSON.stringify(state) : null;
  try {
    if (typeof sessionStorage !== 'undefined') {
      if (payload) sessionStorage.setItem(csrfConfig.storageKey, payload);
      else sessionStorage.removeItem(csrfConfig.storageKey);
    }
  } catch {
    // ignore storage errors
  }
  try {
    if (typeof localStorage !== 'undefined') {
      if (payload) localStorage.setItem(csrfConfig.storageKey, payload);
      else localStorage.removeItem(csrfConfig.storageKey);
    }
  } catch {
    // ignore storage errors
  }
}

function parsePersisted(value: string | null): PersistedCsrfState | null {
  if (!value) return null;
  try {
    const parsed = JSON.parse(value) as PersistedCsrfState | null;
    if (!parsed || typeof parsed !== 'object') return null;
    const token = typeof parsed.token === 'string' && parsed.token.trim() ? parsed.token.trim() : null;
    if (!token) return null;
    const expiresAt =
      parsed.expiresAt != null && Number.isFinite(Number(parsed.expiresAt))
        ? Number(parsed.expiresAt)
        : null;
    const header = typeof parsed.header === 'string' && parsed.header.trim() ? parsed.header.trim() : undefined;
    const cookie = typeof parsed.cookie === 'string' && parsed.cookie.trim() ? parsed.cookie.trim() : undefined;
    return { token, expiresAt, header, cookie };
  } catch {
    return null;
  }
}

function readFromStorage(): PersistedCsrfState | null {
  try {
    if (typeof sessionStorage !== 'undefined') {
      const value = sessionStorage.getItem(csrfConfig.storageKey);
      const parsed = parsePersisted(value);
      if (parsed) return parsed;
    }
  } catch {
    // ignore session storage access errors
  }
  try {
    if (typeof localStorage !== 'undefined') {
      const value = localStorage.getItem(csrfConfig.storageKey);
      const parsed = parsePersisted(value);
      if (parsed) return parsed;
    }
  } catch {
    // ignore local storage access errors
  }
  return null;
}

function isExpired(expiresAt: number | null | undefined): boolean {
  if (expiresAt == null) return false;
  return Number.isFinite(expiresAt) && expiresAt <= Date.now();
}

function applyPersistedState(): CsrfState | null {
  const persisted = readFromStorage();
  if (!persisted) {
    return null;
  }
  if (persisted.header) {
    csrfConfig.headerName = persisted.header;
  }
  if (persisted.cookie) {
    csrfConfig.cookieName = persisted.cookie;
  }
  if (isExpired(persisted.expiresAt)) {
    persistState(null);
    return null;
  }
  return {
    token: persisted.token,
    expiresAt: persisted.expiresAt ?? null,
  };
}

csrfTokenCache = applyPersistedState();

function detectCookieToken(): { name: string; value: string } | null {
  if (typeof document === 'undefined') return null;
  const raw = document.cookie || '';
  if (!raw) return null;
  const parts = raw.split(';');
  let fallback: { name: string; value: string } | null = null;
  for (const part of parts) {
    const trimmed = part.trim();
    if (!trimmed) continue;
    const eq = trimmed.indexOf('=');
    const name = eq === -1 ? trimmed : trimmed.slice(0, eq);
    const lower = name.toLowerCase();
    const valueRaw = eq >= 0 ? trimmed.slice(eq + 1) : '';
    let value = valueRaw;
    try {
      value = decodeURIComponent(valueRaw);
    } catch {
      value = valueRaw;
    }
    if (name === csrfConfig.cookieName) {
      return { name, value };
    }
    if (!fallback && (lower.includes('csrf') || lower.includes('xsrf'))) {
      fallback = { name, value };
    }
  }
  return fallback;
}

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

function detectHeaderToken(res: Response): { name: string; value: string } | null {
  const preferred = csrfConfig.headerName;
  const preferredValue = res.headers.get(preferred) ?? res.headers.get(preferred.toLowerCase());
  if (preferredValue) {
    return { name: preferred, value: preferredValue };
  }
  const candidates: Array<{ name: string; value: string }> = [];
  res.headers.forEach((value, key) => {
    if (!value) return;
    if (key === preferred || key.toLowerCase() === preferred.toLowerCase()) {
      candidates.push({ name: key, value });
      return;
    }
    const lower = key.toLowerCase();
    if (lower.includes('csrf') || lower.includes('xsrf')) {
      candidates.push({ name: key, value });
    }
  });
  return candidates.length ? candidates[0] : null;
}

function detectTtlFromHeaders(res: Response): number | null {
  const candidates = ['x-csrf-ttl', 'x-csrf-ttl-seconds', 'x-csrf-expires-in', 'x-csrf-expires'];
  for (const name of candidates) {
    const value = res.headers.get(name) ?? res.headers.get(name.toUpperCase());
    if (!value) continue;
    const numeric = Number(value);
    if (Number.isFinite(numeric) && numeric > 0) {
      return numeric * 1000;
    }
  }
  return null;
}

function resolveRememberTtl(options?: RememberOptions): number | null {
  if (!options) {
    return csrfConfig.ttlMs;
  }
  if (options.ttlMs === null || options.ttlSeconds === null) {
    csrfConfig.ttlMs = null;
    return null;
  }
  const ttlMsCandidate =
    options.ttlMs != null
      ? Number(options.ttlMs)
      : options.ttlSeconds != null
      ? Number(options.ttlSeconds) * 1000
      : undefined;
  if (ttlMsCandidate === undefined || Number.isNaN(ttlMsCandidate)) {
    return csrfConfig.ttlMs;
  }
  if (!Number.isFinite(ttlMsCandidate) || ttlMsCandidate <= 0) {
    csrfConfig.ttlMs = null;
    return null;
  }
  csrfConfig.ttlMs = ttlMsCandidate;
  return ttlMsCandidate;
}

function rememberCsrfToken(token: string | null | undefined, options?: RememberOptions): string | null {
  const normalized = typeof token === 'string' && token.trim() ? token.trim() : null;
  if (options?.headerName && options.headerName.trim()) {
    csrfConfig.headerName = options.headerName.trim();
  }
  if (options?.cookieName && options.cookieName.trim()) {
    csrfConfig.cookieName = options.cookieName.trim();
  }
  if (!normalized) {
    csrfTokenCache = null;
    persistState(null);
    return null;
  }
  const ttlMs = resolveRememberTtl(options);
  const issuedAt =
    options && typeof options.issuedAt === 'number' && Number.isFinite(options.issuedAt) ? options.issuedAt : Date.now();
  const expiresAt = ttlMs != null ? issuedAt + ttlMs : null;
  csrfTokenCache = { token: normalized, expiresAt };
  persistState({
    token: normalized,
    expiresAt,
    header: csrfConfig.headerName,
    cookie: csrfConfig.cookieName,
  });
  return normalized;
}

function ensureTokenFresh(): string | null {
  if (csrfTokenCache && isExpired(csrfTokenCache.expiresAt)) {
    rememberCsrfToken(null);
  }
  if (!csrfTokenCache) {
    const cookie = detectCookieToken();
    if (cookie) {
      rememberCsrfToken(cookie.value, { cookieName: cookie.name });
    }
  }
  return csrfTokenCache?.token ?? null;
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
  const token = ensureTokenFresh();
  if (token) headers[getCsrfHeaderName()] = token;
  return headers;
}

export function syncCsrfFromResponse(res: Response): void {
  const headerEntry = detectHeaderToken(res);
  const ttlMs = detectTtlFromHeaders(res);
  if (headerEntry) {
    rememberCsrfToken(headerEntry.value, { headerName: headerEntry.name, ttlMs });
  } else if (ttlMs != null) {
    resolveRememberTtl({ ttlMs });
  }
  if (typeof document !== 'undefined') {
    try {
      const cookie = detectCookieToken();
      if (cookie && cookie.value && cookie.value !== csrfTokenCache?.token) {
        rememberCsrfToken(cookie.value, { cookieName: cookie.name, ttlMs });
      }
    } catch {
      // ignore
    }
  }
}

export function setCsrfToken(token?: string | null, options?: RememberOptions): void {
  rememberCsrfToken(token ?? null, options);
}

export function clearCsrfToken(): void {
  rememberCsrfToken(null);
}

export function primeCsrfFromCookies(): void {
  const token = ensureTokenFresh();
  if (!token) {
    const cookie = detectCookieToken();
    if (cookie) rememberCsrfToken(cookie.value, { cookieName: cookie.name });
  }
}

export function getCsrfToken(): string | null {
  return ensureTokenFresh();
}

export function getCsrfCookieName(): string {
  return csrfConfig.cookieName;
}

export function getCsrfHeaderName(): string {
  return csrfConfig.headerName;
}

export function getCsrfTtlMs(): number | null {
  return csrfConfig.ttlMs;
}
