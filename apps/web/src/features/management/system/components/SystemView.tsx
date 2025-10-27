import React from 'react';
import { AlertTriangle } from '@icons';
import { Badge, Button, Collapse, Surface, Switch } from '@ui';
import { fetchSystemConfig, fetchSystemOverview } from '@shared/api/management';
import { extractErrorMessage } from '@shared/utils/errors';
import { PlatformAdminFrame } from '@shared/layouts/management';
import type {
  SystemIncident,
  SystemIncidents,
  SystemOverview,
  SystemSignal,
} from '@shared/types/management';

type ConfigSummaryItem = {
  key: string;
  value: string;
};

type PrimarySignalCardModel = {
  id: string;
  label: string;
  statusLabel: string;
  statusColor: 'success' | 'warning' | 'error' | 'neutral' | 'info';
  metricLabel: string;
  metricValue: string;
  hint?: string;
  heartbeat?: string | null;
};

const STATUS_BADGE_MAP: Record<string, { label: string; color: 'success' | 'warning' | 'error' | 'neutral' | 'info' }> = {
  healthy: { label: 'Healthy', color: 'success' },
  warning: { label: 'Warning', color: 'warning' },
  degraded: { label: 'Degraded', color: 'warning' },
  critical: { label: 'Critical', color: 'error' },
  unknown: { label: 'Unknown', color: 'neutral' },
};

const PRIMARY_SIGNAL_DEFS: Array<{
  id: string;
  label: string;
  match: (signal: SystemSignal) => boolean;
  metricLabel: string;
  metricValue: (signal: SystemSignal) => string;
  hint: string;
}> = [
  {
    id: 'database',
    label: 'Database',
    match: (signal) => /database/.test(signal.id) || /database/i.test(signal.label),
    metricLabel: 'Latency',
    metricValue: (signal) => formatLatency(Number(signal.latency_ms)),
    hint: 'Primary Postgres connection.',
  },
  {
    id: 'redis',
    label: 'Redis',
    match: (signal) => /redis/.test(signal.id) || /redis/i.test(signal.label),
    metricLabel: 'Latency',
    metricValue: (signal) => formatLatency(Number(signal.latency_ms)),
    hint: 'Cache and rate-limiting store.',
  },
  {
    id: 'queue',
    label: 'Queue',
    match: (signal) => /queue/.test(signal.id) || /queue/i.test(signal.label),
    metricLabel: 'Pending jobs',
    metricValue: (signal) => formatCount(Number(signal.pending)),
    hint: 'Worker job backlog.',
  },
  {
    id: 'workers',
    label: 'Workers',
    match: (signal) => /worker/.test(signal.id) || /worker/i.test(signal.label),
    metricLabel: 'Failure rate',
    metricValue: (signal) => formatPercent(Number(signal.failure_rate), 1),
    hint: 'Async workers delivering jobs.',
  },
  {
    id: 'llm',
    label: 'LLM providers',
    match: (signal) => /llm/.test(signal.id) || /llm/i.test(signal.label) || /model/.test(signal.id),
    metricLabel: 'Success rate',
    metricValue: (signal) => formatPercent(Number(signal.success_rate), 1),
    hint: 'Primary LLM call success ratio.',
  },
];

const EMPTY_STATE_TEXT = 'No data available yet. Check raw JSON below or refresh the page.';

export default function ManagementSystem(): React.ReactElement {
  const [config, setConfig] = React.useState<Record<string, unknown> | null>(null);
  const [overview, setOverview] = React.useState<SystemOverview | null>(null);
  const [pageError, setPageError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [refreshing, setRefreshing] = React.useState(false);
  const [autoRefresh, setAutoRefresh] = React.useState(true);
  const [showRawConfig, setShowRawConfig] = React.useState(false);
  const [lastUpdated, setLastUpdated] = React.useState<Date | null>(null);

  const refreshTimerRef = React.useRef<number | null>(null);
  const abortRef = React.useRef<AbortController | null>(null);
  const configSnapshotRef = React.useRef<Record<string, unknown> | null>(null);

  const load = React.useCallback(
    async (opts?: { silent?: boolean }) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      if (opts?.silent) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setPageError(null);

      try {
        const [configRes, overviewRes] = await Promise.allSettled([
          fetchSystemConfig({ signal: controller.signal }),
          fetchSystemOverview({ signal: controller.signal }),
        ]);

        if (controller.signal.aborted) {
          return;
        }

        if (configRes.status === 'fulfilled') {
          configSnapshotRef.current = configRes.value;
          setConfig(configRes.value);
        } else if (!configSnapshotRef.current) {
          setConfig(null);
        }

        if (overviewRes.status === 'fulfilled') {
          setOverview(overviewRes.value);
        } else if (!opts?.silent) {
          setOverview(null);
        }

        if (configRes.status === 'rejected' && overviewRes.status === 'rejected') {
          const reason = (configRes as PromiseRejectedResult).reason ?? (overviewRes as PromiseRejectedResult).reason;
          setPageError(extractErrorMessage(reason, 'Не удалось загрузить системный обзор.'));
        }

        if (configRes.status === 'fulfilled' || overviewRes.status === 'fulfilled') {
          setLastUpdated(new Date());
        }
      } catch (err) {
        if ((err as Error)?.name === 'AbortError') {
          return;
        }
        setPageError(extractErrorMessage(err, 'Не удалось загрузить системный обзор.'));
      } finally {
        const aborted = controller.signal.aborted;
        abortRef.current = null;
        if (!aborted) {
          if (opts?.silent) {
            setRefreshing(false);
          } else {
            setLoading(false);
          }
        }
      }
    },
    [],
  );

  React.useEffect(() => {
    void load();
    return () => {
      abortRef.current?.abort();
      if (refreshTimerRef.current) {
        window.clearInterval(refreshTimerRef.current);
      }
    };
  }, [load]);

  const autoRefreshIntervalSec = overview?.recommendations?.auto_refresh_seconds ?? 30;

  React.useEffect(() => {
    if (refreshTimerRef.current) {
      window.clearInterval(refreshTimerRef.current);
      refreshTimerRef.current = null;
    }
    if (!autoRefresh) {
      return undefined;
    }
    const intervalMs = Math.max(10, autoRefreshIntervalSec) * 1000;
    const timer = window.setInterval(() => {
      void load({ silent: true });
    }, intervalMs);
    refreshTimerRef.current = timer;
    return () => {
      window.clearInterval(timer);
    };
  }, [autoRefresh, autoRefreshIntervalSec, load]);

  const configSummary = React.useMemo(() => buildSummary(config), [config]);
  const configJson = React.useMemo(() => JSON.stringify(config ?? {}, null, 2), [config]);

  const lastUpdatedLabel = React.useMemo(() => {
    if (!lastUpdated) return 'n/a';
    try {
      return `${lastUpdated.toLocaleTimeString()} (${formatRelativeTime(lastUpdated.toISOString())})`;
    } catch {
      return lastUpdated.toISOString();
    }
  }, [lastUpdated]);

  const primarySignals = React.useMemo(() => buildPrimarySignals(overview?.signals), [overview?.signals]);
  const configEmpty = configSummary.length === 0;

  return (
    <PlatformAdminFrame
      title="System overview"
      description="Heartbeat of databases, queues, workers, and LLM providers for quick triage."
      breadcrumbs={[{ label: 'Platform Admin', to: '/platform/system' }, { label: 'System' }]}
      changelog={overview?.changelog ?? []}
    >
      <div className="space-y-6">
        <Surface variant="soft" className="space-y-4 px-5 py-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="text-sm font-semibold text-gray-900 dark:text-white">Health snapshot</div>
              <p className="text-xs text-gray-500 dark:text-dark-200">Last fetch: {lastUpdatedLabel}</p>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 text-sm text-gray-700 dark:text-dark-100">
                <Switch checked={autoRefresh} onChange={(event) => setAutoRefresh(event.currentTarget.checked)} />
                Auto refresh
              </div>
              <Button type="button" variant="outlined" color="neutral" onClick={() => void load()} disabled={loading || refreshing}>
                {refreshing ? 'Refreshing…' : 'Refresh now'}
              </Button>
            </div>
          </div>
          {pageError ? (
            <div className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-600 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-200">
              {pageError}
            </div>
          ) : null}
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
            {primarySignals.map((card) => (
              <PrimarySignalCard key={card.id} card={card} />
            ))}
          </div>
        </Surface>

        <Surface variant="soft" className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-semibold text-gray-900 dark:text-white">Runtime configuration snapshot</h2>
              <p className="text-xs text-gray-500 dark:text-dark-200">Key environment parameters. Toggle the raw payload for full context.</p>
            </div>
            <Button type="button" variant="ghost" onClick={() => setShowRawConfig((prev) => !prev)}>
              {showRawConfig ? 'Hide JSON' : 'Show JSON'}
            </Button>
          </div>
          {configEmpty ? (
            <div className="rounded-lg border border-dashed border-gray-200 px-4 py-6 text-center text-sm text-gray-500 dark:border-dark-600 dark:text-dark-200">
              {EMPTY_STATE_TEXT}
            </div>
          ) : (
            <dl className="grid gap-3 sm:grid-cols-2">
              {configSummary.map((item) => (
                <div key={item.key} className="rounded-lg border border-gray-200/70 bg-white px-3 py-2 text-sm shadow-sm dark:border-dark-600 dark:bg-dark-800">
                  <dt className="text-xs uppercase tracking-wide text-gray-500 dark:text-dark-300">{item.key}</dt>
                  <dd className="mt-1 font-medium text-gray-900 dark:text-white">{item.value}</dd>
                </div>
              ))}
            </dl>
          )}
          <Collapse
            open={showRawConfig}
            className="rounded-xl border border-emerald-200 bg-emerald-50/80 p-4 text-xs text-emerald-700 shadow-inner dark:border-emerald-500/40 dark:bg-emerald-900/40 dark:text-emerald-200"
          >
            <pre className="max-h-[420px] overflow-auto whitespace-pre-wrap break-all">{configJson}</pre>
          </Collapse>
        </Surface>

        <IncidentsPanel incidents={overview?.incidents} />
      </div>
    </PlatformAdminFrame>
  );
}

const PrimarySignalCard = ({ card }: { card: PrimarySignalCardModel }) => (
  <div className="flex h-full flex-col justify-between rounded-2xl border border-gray-200/70 bg-white/80 p-4 shadow-sm dark:border-dark-700 dark:bg-dark-800/70">
    <div className="flex items-start justify-between gap-3">
      <div className="text-sm font-semibold text-gray-900 dark:text-white">{card.label}</div>
      <Badge color={card.statusColor} variant="soft">
        {card.statusLabel}
      </Badge>
    </div>
    <div className="mt-6 space-y-1">
      <div className="text-xs uppercase tracking-wide text-gray-500 dark:text-dark-200">{card.metricLabel}</div>
      <div className="text-2xl font-semibold text-gray-900 dark:text-white">{card.metricValue}</div>
      {card.hint ? <p className="text-xs text-gray-500 dark:text-dark-200">{card.hint}</p> : null}
    </div>
    <div className="mt-4 text-[11px] text-gray-500 dark:text-dark-300">Heartbeat: {formatRelativeTime(card.heartbeat)}</div>
  </div>
);

const IncidentsPanel = ({ incidents }: { incidents?: SystemIncidents }) => {
  if (!incidents) return null;
  const active = incidents.active || [];
  const recent = incidents.recent || [];
  return (
    <Surface variant="soft" className="space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-amber-500" />
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white">Active incidents and latest alerts</h3>
        </div>
        {incidents.error ? (
          <Badge color="error" variant="outline" className="text-[10px] uppercase">
            {incidents.error}
          </Badge>
        ) : null}
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-3">
          <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">Active</h4>
          {active.length === 0 ? (
            <div className="rounded-lg border border-dashed border-gray-200 px-3 py-4 text-xs text-gray-500 dark:border-dark-600 dark:text-dark-200">
              No active incidents.
            </div>
          ) : (
            active.map((incident) => <IncidentCard key={incident.id} incident={incident} />)
          )}
        </div>
        <div className="space-y-3">
          <h4 className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-dark-300">Recent alerts</h4>
          {recent.length === 0 ? (
            <div className="rounded-lg border border-dashed border-gray-200 px-3 py-4 text-xs text-gray-500 dark:border-dark-600 dark:text-dark-200">
              Alert log is clean. New events will show up here first.
            </div>
          ) : (
            recent.slice(0, 3).map((incident) => <IncidentCard key={incident.id} incident={incident} compact />)
          )}
        </div>
      </div>
    </Surface>
  );
};

const IncidentCard = ({ incident, compact }: { incident: SystemIncident; compact?: boolean }) => {
  const severity = (incident.severity || 'info').toLowerCase();
  const severityColor: 'success' | 'warning' | 'error' | 'neutral' | 'info' =
    severity === 'critical' || severity === 'major'
      ? 'error'
      : severity === 'warning' || severity === 'minor'
      ? 'warning'
      : 'info';
  const status = incident.status ? incident.status.replace(/_/g, ' ') : 'pending';
  return (
    <div className="rounded-xl border border-gray-200/70 px-3 py-3 text-xs leading-relaxed shadow-sm dark:border-dark-600 dark:bg-dark-800/40">
      <div className="flex items-center justify-between gap-2">
        <span className="font-medium text-gray-900 dark:text-white">{incident.title || incident.id}</span>
        <Badge color={severityColor} variant="soft">
          {incident.severity || 'info'}
        </Badge>
      </div>
      <div className="mt-1 text-[11px] uppercase tracking-wide text-gray-500 dark:text-dark-300">{status}</div>
      <div className="mt-1 text-[11px] text-gray-500 dark:text-dark-200">
        Updated {formatRelativeTime(incident.updated_at || incident.first_seen_at)}
      </div>
      {!compact && incident.impacts?.length ? (
        <div className="mt-2 flex flex-wrap gap-1">
          {incident.impacts.map((impact) => (
            <Badge key={impact} color="neutral" variant="soft" className="text-[10px]">
              {impact}
            </Badge>
          ))}
        </div>
      ) : null}
      {!compact && incident.history?.length ? (
        <ul className="mt-2 space-y-1 text-[11px] text-gray-500 dark:text-dark-200">
          {incident.history.slice(0, 3).map((entry, index) => (
            <li key={index}>
              {entry.action} - {formatRelativeTime(entry.created_at)}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
};

function flattenSignals(signals?: Record<string, SystemSignal[] | undefined>): SystemSignal[] {
  if (!signals) return [];
  return Object.values(signals)
    .filter(Boolean)
    .flatMap((group) => group || [])
    .filter((item): item is SystemSignal => Boolean(item));
}

function buildPrimarySignals(signals?: Record<string, SystemSignal[] | undefined>): PrimarySignalCardModel[] {
  const flat = flattenSignals(signals);
  return PRIMARY_SIGNAL_DEFS.map((def) => {
    const signal = flat.find((item) => def.match(item));
    if (!signal) {
      return {
        id: def.id,
        label: def.label,
        statusLabel: 'No data',
        statusColor: 'neutral',
        metricLabel: def.metricLabel,
        metricValue: 'n/a',
        hint: def.hint,
        heartbeat: null,
      };
    }
    const statusKey = signal.status?.toLowerCase?.() || 'unknown';
    const badgeMeta = STATUS_BADGE_MAP[statusKey] || { label: signal.status || 'Unknown', color: 'neutral' };
    let metricValue: string;
    try {
      metricValue = def.metricValue(signal);
    } catch {
      metricValue = 'n/a';
    }
    return {
      id: def.id,
      label: def.label,
      statusLabel: badgeMeta.label,
      statusColor: badgeMeta.color,
      metricLabel: def.metricLabel,
      metricValue,
      hint: signal.hint || def.hint,
      heartbeat: signal.last_heartbeat || null,
    };
  });
}

function buildSummary(config: Record<string, unknown> | null): ConfigSummaryItem[] {
  if (!config) return [];
  const entries: ConfigSummaryItem[] = [];
  const push = (key: string, value: unknown) => {
    if (value == null) return;
    const str = String(value);
    if (!str.length) return;
    entries.push({ key, value: str });
  };

  const service = config.service as Record<string, unknown> | undefined;
  if (service) {
    push('Environment', service.env);
    push('Region', service.region);
    push('Release channel', service.channel);
    push('Version', service.version);
  }

  const workers = config.workers as Record<string, unknown> | undefined;
  if (workers) {
    push('Workers concurrency', workers.concurrency);
    push('Workers autoscale', workers.autoscale);
  }

  const llm = config.llm as Record<string, unknown> | undefined;
  if (llm) {
    push('Default LLM provider', llm.primary);
    push('Fallback provider', llm.fallback);
  }

  const billing = config.billing as Record<string, unknown> | undefined;
  if (billing) {
    push('Billing provider', billing.gateway);
    push('Crypto enabled', billing.crypto_enabled);
  }

  return entries;
}

function formatLatency(ms?: number | null): string {
  if (ms == null || Number.isNaN(ms)) return 'n/a';
  if (ms >= 1000) return `${(ms / 1000).toFixed(2)} s`;
  if (ms >= 100) return `${ms.toFixed(0)} ms`;
  return `${ms.toFixed(1)} ms`;
}

function formatPercent(value?: number | null, digits = 1): string {
  if (value == null || Number.isNaN(value)) return 'n/a';
  const normalized = value > 1 ? value : value * 100;
  return `${normalized.toFixed(digits)}%`;
}

function formatCount(value?: number | null): string {
  if (value == null || Number.isNaN(value)) return 'n/a';
  if (Math.abs(value) >= 1000) return `${(value / 1000).toFixed(1)}k`;
  return value.toLocaleString();
}

function formatRelativeTime(iso?: string | null): string {
  if (!iso) return 'n/a';
  const parsed = new Date(iso);
  if (Number.isNaN(parsed.getTime())) return iso;
  const diffMs = Date.now() - parsed.getTime();
  if (diffMs < 0) return parsed.toLocaleTimeString();
  const diffSec = Math.round(diffMs / 1000);
  if (diffSec < 60) return `${diffSec}s ago`;
  if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
  if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
  return parsed.toLocaleDateString();
}
