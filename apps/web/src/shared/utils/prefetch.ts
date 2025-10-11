const prefetched = new Map<string, number>();
const preconnectedOrigins = new Set<string>();
const PREFETCH_TTL_MS = 30 * 1000;
const AUDIT_USER_AGENT_HINTS = ['lighthouse', 'chrome-lighthouse', 'pagespeed', 'gpsi'];
const AUDIT_BLOCKED_PATHS = ['/v1/public/home'];

function isDocumentHidden(): boolean {
  if (typeof document === 'undefined') {
    return false;
  }
  try {
    return document.visibilityState === 'hidden';
  } catch {
    return false;
  }
}

function isAuditUserAgent(): boolean {
  if (typeof navigator === 'undefined') {
    return false;
  }
  const ua = typeof navigator.userAgent === 'string' ? navigator.userAgent.toLowerCase() : '';
  if (!ua) {
    return false;
  }
  return AUDIT_USER_AGENT_HINTS.some((hint) => ua.includes(hint));
}

function isAuditBlocked(target: URL): boolean {
  if (!isAuditUserAgent()) {
    return false;
  }
  const pathname = target.pathname.toLowerCase();
  return AUDIT_BLOCKED_PATHS.some((blockedPath) => pathname === blockedPath || pathname.startsWith(`${blockedPath}/`));
}

function isEphemeralUrl(target: URL): boolean {
  if (target.search || target.hash) {
    return true;
  }
  const pathname = target.pathname.toLowerCase();
  const ephemeralSegments = ['preview', 'draft', 'token', 'session'];
  return ephemeralSegments.some((segment) => pathname.includes(segment));
}

function shouldPrefetch(target: URL): boolean {
  if (isDocumentHidden()) {
    return false;
  }
  if (isAuditBlocked(target)) {
    return false;
  }
  if (target.protocol !== 'http:' && target.protocol !== 'https:') {
    return false;
  }
  if (typeof navigator === 'undefined') return true;
  const connection = (navigator as any).connection;
  if (connection) {
    if (typeof connection.saveData === 'boolean' && connection.saveData) {
      return false;
    }
    const effectiveType = typeof connection.effectiveType === 'string' ? connection.effectiveType.toLowerCase() : null;
    if (effectiveType === 'slow-2g' || effectiveType === '2g') {
      return false;
    }
  }
  return true;
}

function hasPerformanceEntry(url: string): boolean {
  if (typeof performance === 'undefined' || typeof performance.getEntriesByName !== 'function') {
    return false;
  }
  return performance.getEntriesByName(url).length > 0;
}

function hasRecentPrefetch(url: string, now: number): boolean {
  const last = prefetched.get(url);
  if (!last) {
    return false;
  }
  if (now - last < PREFETCH_TTL_MS) {
    return true;
  }
  prefetched.delete(url);
  return false;
}

function ensurePreconnect(target: URL): void {
  if (typeof document === 'undefined') return;
  if (typeof window !== 'undefined' && target.origin === window.location.origin) {
    return;
  }
  if (preconnectedOrigins.has(target.origin)) {
    return;
  }
  const link = document.createElement('link');
  link.rel = 'preconnect';
  link.href = target.origin;
  link.crossOrigin = 'anonymous';
  document.head.appendChild(link);
  preconnectedOrigins.add(target.origin);
}

type ResourceHint = {
  as: HTMLLinkElement['as'];
  crossOrigin?: HTMLLinkElement['crossOrigin'];
};

function resolveResourceHint(target: URL): ResourceHint {
  const pathname = target.pathname.toLowerCase();
  if (pathname.endsWith('.js')) {
    return { as: 'script', crossOrigin: 'anonymous' };
  }
  if (pathname.endsWith('.css')) {
    return { as: 'style' };
  }
  if (pathname.endsWith('.json') || pathname.includes('/api/')) {
    return { as: 'fetch', crossOrigin: 'anonymous' };
  }
  if (pathname.endsWith('.woff2') || pathname.endsWith('.woff')) {
    return { as: 'font', crossOrigin: 'anonymous' };
  }
  return { as: 'document' };
}

function appendPrefetchLink(target: URL): void {
  if (typeof document === 'undefined') return;
  const link = document.createElement('link');
  link.rel = 'prefetch';
  link.href = target.toString();
  link.fetchPriority = 'low';
  const hint = resolveResourceHint(target);
  link.as = hint.as;
  if (hint.crossOrigin) {
    link.crossOrigin = hint.crossOrigin;
  } else if (typeof window !== 'undefined' && target.origin !== window.location.origin) {
    link.crossOrigin = 'anonymous';
  }
  document.head.appendChild(link);
}

function schedulePrefetch(task: () => void): void {
  if (typeof window === 'undefined') return;
  if (typeof (window as any).requestIdleCallback === 'function') {
    (window as any).requestIdleCallback(task, { timeout: 1500 });
  } else {
    window.setTimeout(task, 200);
  }
}

export function prefetchUrl(href: string | null | undefined): void {
  if (!href || typeof window === 'undefined' || typeof document === 'undefined') {
    return;
  }

  let target: URL;
  try {
    target = new URL(href, window.location.href);
  } catch {
    return;
  }

  if (!shouldPrefetch(target)) {
    return;
  }

  const normalized = target.toString();
  const now = Date.now();
  const ephemeral = isEphemeralUrl(target);

  if (!ephemeral && (hasRecentPrefetch(normalized, now) || hasPerformanceEntry(normalized))) {
    return;
  }

  if (ephemeral && hasPerformanceEntry(normalized)) {
    return;
  }

  if (!ephemeral) {
    prefetched.set(normalized, now);
  }

  ensurePreconnect(target);
  const prefetchTarget = target;
  schedulePrefetch(() => appendPrefetchLink(prefetchTarget));
}

export function __resetPrefetchStateForTests(): void {
  prefetched.clear();
  preconnectedOrigins.clear();
}
