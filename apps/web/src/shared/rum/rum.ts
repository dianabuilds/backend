/* Lightweight RUM client: collects NavigationTiming, LCP, CLS, FID
 * and posts to backend POST /v1/metrics/rum.
 */

type RumEvent = {
  event: string;
  ts: number; // epoch millis
  url: string;
  data?: Record<string, any>;
};

type RumOptions = {
  endpoint?: string;
  sampleRate?: number; // 0..1
  debug?: boolean;
};

const now = () => Date.now();

let _enabled = true;
let _debug = false;
let _endpoint = '/v1/metrics/rum';

function log(...args: any[]) {
  if (_debug) console.log('[RUM]', ...args);
}

async function post(e: RumEvent) {
  try {
    // Local import to avoid cyclic deps in SSR
    const { apiPost } = await import('../api/client');
    await apiPost(_endpoint, e, { omitCredentials: true });
  } catch (err) {
    // Swallow errors silently in prod; opt-in debug for dev
    log('post failed', err);
  }
}

export function rumEvent(event: string, data?: Record<string, any>) {
  if (!_enabled) return;
  const payload: RumEvent = {
    event,
    ts: now(),
    url: (typeof location !== 'undefined' ? location.href : '') || '',
    data: data || undefined,
  };
  post(payload);
}

// --- Navigation Timing ---
function captureNavigation() {
  try {
    const navEntries = performance.getEntriesByType('navigation') as any[];
    if (navEntries && navEntries.length) {
      const n: any = navEntries[0];
      const ttfb = Math.max(0, (n.responseStart || 0) - (n.requestStart || 0));
      const dcl = Math.max(0, (n.domContentLoadedEventEnd || 0) - (n.startTime || 0));
      const load = Math.max(0, (n.loadEventEnd || 0) - (n.startTime || 0));
      rumEvent('navigation', { ttfb, domContentLoaded: dcl, loadEvent: load });
      return;
    }
    // Fallback to legacy timing
    const t = (performance as any).timing;
    if (t) {
      const ttfb = Math.max(0, t.responseStart - t.requestStart);
      const dcl = Math.max(0, t.domContentLoadedEventEnd - t.navigationStart);
      const load = Math.max(0, t.loadEventEnd - t.navigationStart);
      rumEvent('navigation', { ttfb, domContentLoaded: dcl, loadEvent: load });
    }
  } catch (e) {
    log('navigation capture failed', e);
  }
}

// --- LCP ---
function captureLCP() {
  try {
    let lcp = 0;
    const po = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const last = entries[entries.length - 1] as any;
      if (last && typeof last.startTime === 'number') {
        lcp = Math.max(lcp, last.startTime);
      }
    });
    po.observe({ type: 'largest-contentful-paint', buffered: true } as any);
    const finalize = () => {
      try { po.disconnect(); } catch {}
      if (lcp > 0) rumEvent('web_vital_lcp', { lcp_ms: Math.round(lcp) });
    };
    addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') finalize();
    });
    addEventListener('pagehide', finalize);
  } catch (e) {
    log('lcp capture failed', e);
  }
}

// --- CLS ---
function captureCLS() {
  try {
    let cls = 0;
    const po = new PerformanceObserver((list) => {
      for (const entry of list.getEntries() as any) {
        // Ignore shifts triggered by user input
        if (!entry.hadRecentInput && entry.value) cls += entry.value;
      }
    });
    po.observe({ type: 'layout-shift', buffered: true } as any);
    const finalize = () => {
      try { po.disconnect(); } catch {}
      if (cls > 0) rumEvent('web_vital_cls', { cls });
    };
    addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'hidden') finalize();
    });
    addEventListener('pagehide', finalize);
  } catch (e) {
    log('cls capture failed', e);
  }
}

// --- FID ---
function captureFID() {
  try {
    const po = new PerformanceObserver((list) => {
      const first = list.getEntries()[0] as any;
      if (!first) return;
      const delay = Math.max(0, (first.processingStart || 0) - (first.startTime || 0));
      if (delay) rumEvent('web_vital_fid', { fid_ms: Math.round(delay) });
    });
    po.observe({ type: 'first-input', buffered: true } as any);
  } catch (e) {
    log('fid capture failed', e);
  }
}

export function startRUM(opts: RumOptions = {}) {
  const env = (import.meta as any)?.env || {};
  const enabledEnv = env.VITE_RUM_ENABLED;
  const srEnv = env.VITE_RUM_SAMPLE_RATE;
  _endpoint = opts.endpoint || '/v1/metrics/rum';
  _debug = !!opts.debug || !!env.VITE_RUM_DEBUG;
  const sampleRate = typeof opts.sampleRate === 'number' ? opts.sampleRate : (srEnv ? parseFloat(srEnv) : 1);
  // simple sampling
  _enabled = Math.random() < (Number.isFinite(sampleRate) ? Math.max(0, Math.min(1, sampleRate)) : 1);
  if (enabledEnv === '0' || enabledEnv === 'false') _enabled = false;

  if (!_enabled) {
    log('RUM disabled by sampling');
    return;
  }

  if (document.readyState === 'complete') {
    captureNavigation();
  } else {
    addEventListener('load', () => captureNavigation());
  }
  captureLCP();
  captureCLS();
  captureFID();
  // UI errors
  try {
    window.addEventListener('error', (ev) => {
      try {
        const e: any = (ev as any).error || {};
        rumEvent('ui_error', {
          message: String((ev as any).message || e.message || 'error'),
          source: String((ev as any).filename || ''),
          lineno: Number((ev as any).lineno || 0),
          colno: Number((ev as any).colno || 0),
          stack: String(e && e.stack ? e.stack : ''),
        });
      } catch {}
    });
    window.addEventListener('unhandledrejection', (ev) => {
      try {
        const r: any = (ev as any).reason || {};
        const msg = typeof r === 'string' ? r : (r && (r.message || r.toString && r.toString())) || 'rejection';
        rumEvent('ui_unhandledrejection', {
          reason: String(msg),
          stack: String(r && r.stack ? r.stack : ''),
        });
      } catch {}
    });
  } catch {}
}
