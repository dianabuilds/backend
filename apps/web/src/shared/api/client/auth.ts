type AuthLostHandler = () => void;

let authLostHandler: AuthLostHandler | null = null;

export function setAuthLostHandler(handler?: AuthLostHandler): void {
  authLostHandler = handler || null;
}

export function notifyAuthLost(): void {
  if (!authLostHandler) return;
  try {
    authLostHandler();
  } catch {
    // ignore handler errors
  }
}

const ADMIN_KEY_STORAGE_KEYS = ['admin.api.key', 'admin.apiKey'];

function readRuntimeAdminKey(): string | null {
  if (typeof window === 'undefined') return null;

  const candidates: Array<unknown> = [
    (window as any).__ADMIN_API_KEY,
    (window as any).__ADMIN_KEY__,
  ];
  for (const candidate of candidates) {
    if (typeof candidate === 'string' && candidate.trim()) return candidate.trim();
  }

  for (const storageName of ['sessionStorage', 'localStorage']) {
    try {
      const storage = (window as any)[storageName] as Storage | undefined;
      if (!storage) continue;
      for (const key of ADMIN_KEY_STORAGE_KEYS) {
        const value = storage.getItem(key);
        if (typeof value === 'string' && value.trim()) return value.trim();
      }
    } catch {
      // ignore storage errors
    }
  }

  return null;
}

function isAdminEndpoint(path: string): boolean {
  return (
    path.includes('/admin') ||
    path.startsWith('/v1/flags') ||
    path.startsWith('/v1/audit') ||
    path.startsWith('/v1/notifications/send')
  );
}

export function applyAdminKey(headers: Record<string, string>, path: string): Record<string, string> {
  try {
    if (!isAdminEndpoint(path)) return headers;
    const adminKey = readRuntimeAdminKey();
    if (adminKey) headers['X-Admin-Key'] = adminKey;
    return headers;
  } catch {
    return headers;
  }
}

function decodeBase64UrlSegment(segment: string): string {
  const normalized = segment.replace(/-/g, '+').replace(/_/g, '/');
  const padLength = (4 - (normalized.length % 4 || 4)) % 4;
  const padded = normalized.padEnd(normalized.length + padLength, '=');
  const binary = atob(padded);

  if (typeof TextDecoder !== 'undefined') {
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) {
      bytes[i] = binary.charCodeAt(i);
    }
    return new TextDecoder().decode(bytes);
  }

  let percentEncoded = '';
  for (let i = 0; i < binary.length; i += 1) {
    const hex = binary.charCodeAt(i).toString(16).padStart(2, '0');
    percentEncoded += `%${hex}`;
  }
  try {
    return decodeURIComponent(percentEncoded);
  } catch {
    return binary;
  }
}

export function decodeJwt<T = unknown>(token: string | undefined | null): T | null {
  try {
    if (!token) return null;
    const parts = token.split('.');
    if (parts.length < 2) return null;
    const json = decodeBase64UrlSegment(parts[1]);
    return JSON.parse(json) as T;
  } catch {
    return null;
  }
}