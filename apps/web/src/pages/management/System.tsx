import React from 'react';
import { AlertTriangle, BarChart3, Boxes, ExternalLink, Gauge } from '@icons';
import { Badge, Button, Collapse, Surface, Switch } from '@ui';
import type { PageHeaderStat } from '@ui/patterns/PageHeader.tsx';
import { apiGet } from '../../shared/api/client';
import {
  PlatformAdminChangelogEntry,
  PlatformAdminFrame,
  PlatformAdminIntegration,
  PlatformAdminQuickLink,
} from './platform-admin/PlatformAdminFrame';

type SystemSignal = {
  id: string;
  label: string;
  status: string;
  ok?: boolean | null;
  hint?: string | null;
  last_heartbeat?: string | null;
  latency_ms?: number | null;
  pending?: number | null;
  leased?: number | null;
  failed?: number | null;
  succeeded?: number | null;
  oldest_pending_seconds?: number | null;
  avg_duration_ms?: number | null;
  failure_rate?: number | null;
  jobs_completed?: number | null;
  jobs_failed?: number | null;
  success_rate?: number | null;
  total_calls?: number | null;
  error_count?: number | null;
  models?: string[];
  enabled?: boolean;
  link?: string | null;
  [key: string]: unknown;
};

type IncidentHistoryItem = {
  action: string;
  created_at?: string | null;
  reason?: string | null;
  payload?: Record<string, unknown> | null;
};

type Incident = {
  id: string;
  title: string;
  status: string;
  severity?: string;
  source?: string;
  first_seen_at?: string | null;
  updated_at?: string | null;
  impacts?: string[];
  history?: IncidentHistoryItem[];
};

type SystemIncidents = {
  active?: Incident[];
  recent?: Incident[];
  integrations?: PlatformAdminIntegration[];
  error?: string;
};

type SystemSummary = {
  collected_at?: string;
  uptime_percent?: number;
  db_latency_ms?: number;
  queue_pending?: number;
  queue_status?: string;
  worker_avg_ms?: number;
  worker_failure_rate?: number;
  llm_success_rate?: number;
  active_incidents?: number;
};

type SystemOverview = {
  collected_at: string;
  recommendations?: {
    auto_refresh_seconds?: number;
  };
  signals?: Record<string, SystemSignal[] | undefined>;
  summary?: SystemSummary;
  incidents?: SystemIncidents;
  links?: Record<string, string | null | undefined>;
  changelog?: PlatformAdminChangelogEntry[];
};

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

const QUICK_LINKS: PlatformAdminQuickLink[] = [
  {
    label: 'Health endpoint',
    href: '/v1/admin/health',
    description: 'Simple ping for load balancers and automation.',
    icon: <ExternalLink className="h-4 w-4" />,
  },
];

const HELP_TEXT = (
  <div className="space-y-2 text-sm leading-relaxed text-gray-600 dark:text-dark-100">
    <p>
      This dashboard highlights the key infrastructure services that keep the platform online: database, cache, job
      queue, workers, and LLM providers. Investigate anything that is not healthy before it turns into an incident.
    </p>
    <p>
      Health data auto-refreshes every 30 seconds by default. Pause auto refresh while triaging to avoid noisy updates.
    </p>
  </div>
);

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
    match: (signal) => signal.id.startsWith('llm:') || /llm/i.test(signal.label),
    metricLabel: 'Success rate',
    metricValue: (signal) => formatPercent(Number(signal.success_rate), 1),
    hint: 'Model registry and providers.',
  },
];

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

function buildSummary(config: Record<string, any> | null): ConfigSummaryItem[] {
  if (!config) return [];
  const entries: ConfigSummaryItem[] = [];
  const push = (key: string, value: unknown) => {
    if (value == null) return;
    const str = String(value);
    if (!str.length) return;
    entries.push({ key, value: str });
  };
  const directKeys = ['env', 'event_group'];
  for (const key of directKeys) {
    if (entries.length >= 6) break;
    if (key in config) push(key, config[key]);
  }
  if ('database_url' in config) {
    const db = String(config.database_url || '');
    if (db) push('database_url', db.replace(/:[^@]+@/, ':***@'));
  }
  if ('redis_url' in config) {
    const redis = String(config.redis_url || '');
    if (redis) push('redis_url', redis.replace(/:[^@]+@/, ':***@'));
  }
  if ('event_topics' in config) {
    const topics = String(config.event_topics || '')
      .split(',')
      .map((topic) => topic.trim())
      .filter(Boolean)
      .slice(0, 4)
      .join(', ');
    if (topics) push('event_topics', topics);
  }
  if (entries.length < 6) {
    for (const [key, value] of Object.entries(config)) {
      if (entries.length >= 6) break;
      if (directKeys.includes(key) || ['database_url', 'redis_url', 'event_topics'].includes(key)) continue;
      if (value && typeof value === 'object') {
        for (const [innerKey, innerValue] of Object.entries(value as Record<string, unknown>)) {
          if (entries.length >= 6) break;
          if (innerValue == null) continue;
          push(`${key}.${innerKey}`, innerValue);
        }
      } else {
        push(key, value);
      }
    }
  }
  return entries;
}

function flattenSignals(signals?: Record<string, SystemSignal[] | undefined>): SystemSignal[] {
  if (!signals) return [];
  const result: SystemSignal[] = [];
  for (const group of Object.values(signals)) {
    if (!group) continue;
    for (const signal of group) {
      if (signal) result.push(signal);
    }
  }
  return result;
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

const EMPTY_STATE_TEXT = 'No data available yet. Check raw JSON below or refresh the page.';

export default function ManagementSystem(): JSX.Element {
  const [config, setConfig] = React.useState<Record<string, any> | null>(null);
  const [overview, setOverview] = React.useState<SystemOverview | null>(null);
  const [pageError, setPageError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [silentRefresh, setSilentRefresh] = React.useState(false);
  const [autoRefresh, setAutoRefresh] = React.useState(true);
  const [showRawConfig, setShowRawConfig] = React.useState(false);
  const [lastUpdated, setLastUpdated] = React.useState<Date | null>(null);
  const refreshTimer = React.useRef<number | null>(null);
  const configSnapshotRef = React.useRef<Record<string, any> | null>(null);

  const load = React.useCallback(async (opts?: { silent?: boolean }) => {
    if (opts?.silent) {
      setSilentRefresh(true);
    } else {
      setLoading(true);
    }
    setPageError(null);
    try {
      const [configRes, overviewRes] = await Promise.allSettled([
        apiGet<Record<string, any>>('/v1/admin/config'),
        apiGet<SystemOverview>('/v1/admin/system/overview'),
      ]);

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
        setPageError(normalizeError(configRes.reason || overviewRes.reason));
      }
      if (configRes.status === 'fulfilled' || overviewRes.status === 'fulfilled') {
        setLastUpdated(new Date());
      }
    } catch (err) {
      setPageError(normalizeError(err));
    } finally {
      if (opts?.silent) setSilentRefresh(false);
      else setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void load();
    return () => {
      if (refreshTimer.current) {
        window.clearInterval(refreshTimer.current);
      }
    };
  }, [load]);

  const autoRefreshIntervalSec = overview?.recommendations?.auto_refresh_seconds ?? 30;

  React.useEffect(() => {
    if (refreshTimer.current) {
      window.clearInterval(refreshTimer.current);
      refreshTimer.current = null;
    }
    if (!autoRefresh) {
      return;
    }
    const intervalMs = Math.max(10, autoRefreshIntervalSec) * 1000;
    const timer = window.setInterval(() => {
      void load({ silent: true });
    }, intervalMs);
    refreshTimer.current = timer;
    return () => {
      window.clearInterval(timer);
    };
  }, [autoRefresh, autoRefreshIntervalSec, load]);

  const configSummary = React.useMemo(() => buildSummary(config), [config]);
  const configJson = React.useMemo(() => JSON.stringify(config || {}, null, 2), [config]);
  const lastUpdatedLabel = React.useMemo(() => {
    if (!lastUpdated) return 'n/a';
    try {
      return `${lastUpdated.toLocaleTimeString()} (${formatRelativeTime(lastUpdated.toISOString())})`;
    } catch {
      return lastUpdated.toISOString();
    }
  }, [lastUpdated]);

  const summaryStats = React.useMemo<PageHeaderStat[]>(() => {
    const stats: PageHeaderStat[] = [];
    const summary = overview?.summary;
    if (!summary) return stats;
    if (summary.queue_pending != null) {
      stats.push({
        label: 'Pending jobs',
        value: formatCount(summary.queue_pending),
        hint: `Queue status: ${summary.queue_status ?? 'n/a'}`,
        icon: <Boxes className="h-5 w-5 text-primary-500" />,
      });
    }
    if (summary.llm_success_rate != null) {
      stats.push({
        label: 'LLM success',
        value: formatPercent(summary.llm_success_rate, 1),
        hint: 'Aggregated across providers',
        icon: <BarChart3 className="h-5 w-5 text-primary-500" />,
      });
    }
    if (summary.db_latency_ms != null) {
      stats.push({
        label: 'DB latency',
        value: formatLatency(summary.db_latency_ms),
        hint: 'Primary database',
        icon: <Gauge className="h-5 w-5 text-primary-500" />,
      });
    }
    return stats;
  }, [overview]);

  const quickLinks = React.useMemo<PlatformAdminQuickLink[]>(() => {
    const links = [...QUICK_LINKS];
    const apiLinks = overview?.links || {};
    if (apiLinks.docs) {
      links.push({
        label: 'Platform monitoring guide',
        href: String(apiLinks.docs),
        description: 'Runbooks, escalation paths, and triage checklists.',
        icon: <ExternalLink className="h-4 w-4" />,
      });
    }
    if (apiLinks.runbooks) {
      links.push({ label: 'Runbook library', href: String(apiLinks.runbooks) });
    }
    if (apiLinks.alerts_channel) {
      links.push({ label: 'Open alerts channel', href: String(apiLinks.alerts_channel) });
    }
    return links;
  }, [overview?.links]);

  const primarySignals = React.useMemo(() => buildPrimarySignals(overview?.signals), [overview?.signals]);
  const incidentIntegrations = overview?.incidents?.integrations ?? [];
  const configEmpty = configSummary.length === 0;

  return (
    <PlatformAdminFrame
      title="System overview"
      description="Heartbeat of databases, queues, workers, and LLM providers for quick triage."
      breadcrumbs={[{ label: 'Platform Admin', to: '/platform/system' }, { label: 'System' }]}
      stats={summaryStats}
      quickLinks={quickLinks}
      helpText={HELP_TEXT}
      integrations={incidentIntegrations}
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
              <Button
                type="button"
                variant="outlined"
                color="neutral"
                onClick={() => void load()}
                disabled={loading || silentRefresh}
              >
                {silentRefresh ? 'Refreshing...' : 'Refresh now'}
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
          <Collapse open={showRawConfig} className="rounded-xl bg-gray-950/90 p-4 text-xs text-emerald-50 shadow-inner dark:bg-dark-900">
            <pre className="max-h-[420px] overflow-auto whitespace-pre-wrap break-all">{configJson}</pre>
          </Collapse>
        </Surface>

        <IncidentsPanel incidents={overview?.incidents} />
      </div>
    </PlatformAdminFrame>
  );
}

function PrimarySignalCard({ card }: { card: PrimarySignalCardModel }) {
  return (
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
}

function IncidentsPanel({ incidents }: { incidents?: SystemIncidents }) {
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
}

function IncidentCard({ incident, compact }: { incident: Incident; compact?: boolean }) {
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
}
