import React from 'react';
import { Button, Card } from '@ui';
import { apiGet } from '../../shared/api/client';

type EndpointResult = {
  payload: any | null;
  error: string | null;
};

type StatusMeta = {
  ok: boolean;
  text: string;
  hint: string | null;
};

const POSITIVE_MARKERS = ['ok', 'pass', 'ready', 'healthy', 'green', 'up'];

function normalizeError(reason: unknown): string {
  if (!reason) return 'Unexpected error';
  if (reason instanceof Error) return reason.message || 'Unexpected error';
  if (typeof reason === 'string') return reason;
  try {
    return JSON.stringify(reason);
  } catch {
    return 'Unexpected error';
  }
}

function extractDetail(payload: any): string | null {
  if (payload == null) return null;
  if (typeof payload === 'string' || typeof payload === 'number') return String(payload);
  if (typeof payload === 'boolean') return payload ? 'true' : 'false';
  if (typeof payload === 'object') {
    for (const key of ['message', 'detail', 'description', 'reason', 'error']) {
      const value = (payload as any)[key];
      if (typeof value === 'string' && value.length) return value;
    }
    for (const [key, value] of Object.entries(payload as Record<string, unknown>)) {
      if (typeof value === 'string' || typeof value === 'number') {
        return `${key}: ${value}`;
      }
    }
  }
  return null;
}

function evaluatePayload(payload: any): StatusMeta {
  if (payload == null) return { ok: true, text: 'Operational', hint: null };
  if (typeof payload === 'boolean') {
    return { ok: payload, text: payload ? 'Operational' : 'Unavailable', hint: null };
  }
  if (typeof payload === 'string') {
    const lower = payload.toLowerCase();
    return {
      ok: POSITIVE_MARKERS.includes(lower),
      text: payload,
      hint: null,
    };
  }
  if (typeof payload === 'number') {
    const ok = payload === 200 || payload === 0;
    return { ok, text: String(payload), hint: null };
  }
  if (typeof payload === 'object') {
    const cast = payload as Record<string, unknown>;
    let ok: boolean | null = null;
    let label: string | null = null;
    if (typeof cast.ok === 'boolean') ok = cast.ok;
    if (typeof cast.ready === 'boolean') ok = cast.ready;
    if (typeof cast.healthy === 'boolean') ok = cast.healthy;
    if (typeof cast.status === 'string') {
      label = String(cast.status);
      if (ok == null) ok = POSITIVE_MARKERS.includes(cast.status.toLowerCase());
    }
    const hint = extractDetail(cast);
    return {
      ok: ok == null ? true : ok,
      text: label || (ok === false ? 'Attention needed' : 'Operational'),
      hint,
    };
  }
  return { ok: true, text: 'Operational', hint: null };
}

function truncate(value: string | null, max = 160): string | null {
  if (!value) return null;
  if (value.length <= max) return value;
  return `${value.slice(0, max - 3).trim()}...`;
}

function computeStatus(result: EndpointResult): StatusMeta {
  if (result.error) {
    return { ok: false, text: 'Unreachable', hint: truncate(result.error, 160) };
  }
  return evaluatePayload(result.payload);
}

function StatusTile({ label, result }: { label: string; result: EndpointResult }) {
  const meta = computeStatus(result);
  return (
    <div
      className={`rounded-xl border px-4 py-3 transition ${
        meta.ok
          ? 'border-emerald-200/60 bg-emerald-50/80 dark:border-emerald-400/20 dark:bg-emerald-900/20'
          : 'border-rose-200/70 bg-rose-50/80 dark:border-rose-400/30 dark:bg-rose-900/20'
      }`}
    >
      <div className="flex items-center justify-between gap-3">
        <div className="text-sm font-semibold text-gray-900 dark:text-white">{label}</div>
        <span
          className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-wide ${
            meta.ok
              ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-500/10 dark:text-emerald-200'
              : 'bg-rose-100 text-rose-700 dark:bg-rose-500/10 dark:text-rose-200'
          }`}
        >
          <span
            className={`h-2 w-2 rounded-full ${meta.ok ? 'bg-emerald-500 dark:bg-emerald-300' : 'bg-rose-500 dark:bg-rose-300'}`}
          />
          {meta.text}
        </span>
      </div>
      {meta.hint && <div className="mt-2 text-xs text-gray-500 dark:text-dark-200">{meta.hint}</div>}
    </div>
  );
}

function buildSummary(config: Record<string, any> | null): Array<{ key: string; value: string }> {
  if (!config || typeof config !== 'object') return [];
  const entries: Array<{ key: string; value: string }> = [];
  for (const [key, value] of Object.entries(config)) {
    if (value == null) continue;
    if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
      entries.push({ key, value: String(value) });
    } else if (!Array.isArray(value) && typeof value === 'object') {
      for (const [innerKey, innerValue] of Object.entries(value)) {
        if (innerValue == null) continue;
        if (
          typeof innerValue === 'string' ||
          typeof innerValue === 'number' ||
          typeof innerValue === 'boolean'
        ) {
          entries.push({ key: `${key}.${innerKey}`, value: String(innerValue) });
        }
        if (entries.length >= 6) break;
      }
    }
    if (entries.length >= 6) break;
  }
  return entries;
}

export default function ManagementSystem() {
  const [config, setConfig] = React.useState<Record<string, any> | null>(null);
  const [health, setHealth] = React.useState<EndpointResult>({ payload: null, error: null });
  const [readiness, setReadiness] = React.useState<EndpointResult>({ payload: null, error: null });
  const [loading, setLoading] = React.useState(true);
  const [pageError, setPageError] = React.useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = React.useState<Date | null>(null);

  const load = React.useCallback(async () => {
    setLoading(true);
    setPageError(null);
    const [configRes, healthRes, readyRes] = await Promise.allSettled([
      apiGet<Record<string, any>>('/v1/admin/config'),
      apiGet<any>('/v1/admin/health'),
      apiGet<any>('/v1/admin/readyz'),
    ]);

    if (configRes.status === 'fulfilled') {
      setConfig(configRes.value);
    }
    if (configRes.status === 'rejected' && !config) {
      setConfig(null);
    }

    if (healthRes.status === 'fulfilled') {
      setHealth({ payload: healthRes.value, error: null });
    } else {
      setHealth({ payload: null, error: normalizeError(healthRes.reason) });
    }

    if (readyRes.status === 'fulfilled') {
      setReadiness({ payload: readyRes.value, error: null });
    } else {
      setReadiness({ payload: null, error: normalizeError(readyRes.reason) });
    }

    const anySuccess = [configRes, healthRes, readyRes].some((res) => res.status === 'fulfilled');
    if (!anySuccess) {
      setPageError('Failed to fetch system data. Check connectivity or permissions.');
    }
    setLastUpdated(new Date());
    setLoading(false);
  }, [config]);

  React.useEffect(() => {
    load();
  }, [load]);

  const summary = React.useMemo(() => buildSummary(config), [config]);
  const configJson = React.useMemo(() => JSON.stringify(config || {}, null, 2), [config]);
  const lastUpdatedLabel = React.useMemo(() => {
    if (!lastUpdated) return 'N/A';
    try {
      return lastUpdated.toLocaleTimeString();
    } catch {
      return lastUpdated.toISOString();
    }
  }, [lastUpdated]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">System overview</h1>
          <p className="mt-1 max-w-2xl text-sm text-gray-500 dark:text-dark-200">
            Live health signals and environment snapshot for quick release checks or incident triage.
          </p>
        </div>
        <Button variant="outlined" color="primary" size="sm" onClick={load} disabled={loading}>
          {loading ? 'Refreshing...' : 'Refresh data'}
        </Button>
      </div>

      <Card padding="sm" skin="shadow" className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-gray-900 dark:text-white">Service signals</h2>
            <p className="text-xs text-gray-500 dark:text-dark-200">Last update: {lastUpdatedLabel}</p>
          </div>
        </div>
        <div className="grid gap-3 lg:grid-cols-2">
          <StatusTile label="Health endpoint" result={health} />
          <StatusTile label="Readiness endpoint" result={readiness} />
        </div>
        {pageError && <div className="text-xs text-rose-600 dark:text-rose-300">{pageError}</div>}
      </Card>

      <Card padding="sm" className="space-y-4">
        <div className="flex items-baseline justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-gray-900 dark:text-white">Runtime configuration</h2>
            <p className="text-xs text-gray-500 dark:text-dark-200">
              Summary fields are detected automatically; full payload is available below.
            </p>
          </div>
        </div>
        {summary.length > 0 ? (
          <dl className="grid gap-3 sm:grid-cols-2">
            {summary.map((item) => (
              <div key={item.key} className="rounded-lg border border-gray-200/70 bg-white/40 px-3 py-2 dark:border-dark-600 dark:bg-dark-900/30">
                <dt className="text-xs uppercase tracking-wide text-gray-500 dark:text-dark-300">{item.key}</dt>
                <dd className="mt-1 text-sm font-medium text-gray-900 dark:text-white">{item.value}</dd>
              </div>
            ))}
          </dl>
        ) : (
          <div className="rounded-lg border border-dashed border-gray-200 px-4 py-6 text-center text-sm text-gray-500 dark:border-dark-600 dark:text-dark-200">
            No top-level fields detected. Inspect the JSON payload below.
          </div>
        )}
        <div className="rounded-xl bg-gray-900/95 p-4 text-xs text-white shadow-inner dark:bg-dark-900">
          <pre className="max-h-[480px] overflow-auto whitespace-pre-wrap break-all">{configJson}</pre>
        </div>
      </Card>
    </div>
  );
}
