const FALLBACK_ORIGIN = 'https://caves.world';

function sanitizeOrigin(value: string | null | undefined): string {
  if (!value) return '';
  const trimmed = value.trim();
  if (!trimmed) return '';
  try {
    const url = new URL(trimmed);
    return url.origin.replace(/\/+$/, '');
  } catch {
    if (!/^https?:\/\//i.test(trimmed)) {
      return '';
    }
    return trimmed.replace(/\/+$/, '');
  }
}

let cachedEnvOrigin: string | undefined;

function readEnvOrigin(): string {
  if (cachedEnvOrigin !== undefined) {
    return cachedEnvOrigin;
  }
  let origin = '';
  const metaEnv = typeof import.meta !== 'undefined' ? (import.meta as ImportMeta).env : undefined;
  if (metaEnv && typeof metaEnv.VITE_PUBLIC_SITE_ORIGIN === 'string') {
    origin = metaEnv.VITE_PUBLIC_SITE_ORIGIN;
  }
  if (!origin && typeof process !== 'undefined' && typeof process.env?.PUBLIC_SITE_ORIGIN === 'string') {
    origin = process.env.PUBLIC_SITE_ORIGIN;
  }
  cachedEnvOrigin = sanitizeOrigin(origin);
  return cachedEnvOrigin;
}

type MaybeRecord = Record<string, unknown> | null | undefined;

function readMetaOrigin(meta?: MaybeRecord): string {
  if (!meta) return '';
  const candidates: Array<unknown> = [
    meta.origin,
    meta.siteUrl,
    meta.site_url,
    meta.baseUrl,
    meta.base_url,
    meta.canonicalOrigin,
    meta.canonical_origin,
  ];
  for (const candidate of candidates) {
    if (typeof candidate === 'string') {
      const resolved = sanitizeOrigin(candidate);
      if (resolved) {
        return resolved;
      }
    }
  }
  return '';
}

export function resolveSiteOrigin(meta?: MaybeRecord): string {
  const fromMeta = readMetaOrigin(meta);
  if (fromMeta) {
    return fromMeta;
  }
  const envOrigin = readEnvOrigin();
  if (envOrigin) {
    return envOrigin;
  }
  if (typeof window !== 'undefined' && typeof window.location?.origin === 'string') {
    const normalized = sanitizeOrigin(window.location.origin);
    if (normalized) {
      return normalized;
    }
  }
  return FALLBACK_ORIGIN;
}

export function isAbsoluteUrl(url: string): boolean {
  return /^https?:\/\//i.test(url);
}

function normalizePath(path: string): string {
  if (!path) return '';
  if (path.startsWith('/')) {
    return path;
  }
  return '/' + path;
}

export function buildCanonicalUrl(pathOrUrl: string, origin?: string): string {
  const raw = (pathOrUrl ?? '').trim();
  if (!raw) {
    return resolveSiteOrigin();
  }
  if (isAbsoluteUrl(raw)) {
    try {
      const url = new URL(raw);
      url.hash = '';
      return url.toString();
    } catch {
      return raw;
    }
  }
  const baseOrigin = sanitizeOrigin(origin ?? '') || resolveSiteOrigin();
  const normalizedOrigin = baseOrigin.replace(/\/+$/, '');
  const normalizedPath = normalizePath(raw);
  return normalizedOrigin + normalizedPath;
}

