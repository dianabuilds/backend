import React from 'react';
import { Button, Card, Checkbox, Input, LineChart, MetricCard, Spinner, useToast } from '@ui';
import { extractErrorMessage } from '../../../../shared/utils/errors';
import { apiGetRaw } from '../../../../shared/api/client';
import { fetchAdminNodeAnalytics } from '../api';
import type { AdminNodeAnalytics } from '../types';
type AnalyticsPanelProps = {
  nodeId: string;
};
type AnalyticsFilters = {
  start: string;
  end: string;
  limit: string;
  views: boolean;
  reactions: boolean;
  comments: boolean;
};
const initialFilters: AnalyticsFilters = {
  start: '',
  end: '',
  limit: '30',
  views: true,
  reactions: true,
  comments: true,
};
function safeNumber(value: unknown, fallback = 0): number {
  if (typeof value === 'number' && !Number.isNaN(value)) return value;
  return fallback;
}
function formatNumber(value: number | null | undefined): string {
  if (typeof value !== 'number' || Number.isNaN(value)) return '0';
  return value.toLocaleString();
}
export function AnalyticsPanel({ nodeId }: AnalyticsPanelProps) {
  const { pushToast } = useToast();
  const [filters, setFilters] = React.useState<AnalyticsFilters>(initialFilters);
  const [data, setData] = React.useState<AdminNodeAnalytics | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [exporting, setExporting] = React.useState(false);
  const buildQuery = React.useCallback(() => {
    const query: Record<string, string> = {};
    if (filters.start) query.start = `${filters.start}T00:00:00Z`;
    if (filters.end) query.end = `${filters.end}T23:59:59Z`;
    const limit = Number.parseInt(filters.limit, 10);
    if (!Number.isNaN(limit) && limit > 0) query.limit = String(limit);
    return query;
  }, [filters.end, filters.limit, filters.start]);
  const loadAnalytics = React.useCallback(async () => {
    if (!nodeId) return;
    setLoading(true);
    try {
      const payload = await fetchAdminNodeAnalytics(nodeId, {
        start: filters.start ? `${filters.start}T00:00:00Z` : undefined,
        end: filters.end ? `${filters.end}T23:59:59Z` : undefined,
        limit: Number.parseInt(filters.limit, 10) || undefined,
      });
      setData(payload);
      setError(null);
    } catch (err) {
      setError(extractErrorMessage(err));
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [filters.end, filters.limit, filters.start, nodeId]);
  React.useEffect(() => {
    loadAnalytics();
  }, [loadAnalytics]);
  const categories = React.useMemo(() => {
    if (!data?.views?.buckets) return [];
    return data.views.buckets.map((bucket) => bucket.bucket_date ?? '');
  }, [data?.views?.buckets]);
  const chartSeries = React.useMemo(() => {
    if (!data) return [];
    const series: Array<{ name: string; data: number[] }> = [];
    if (filters.views) {
      series.push({
        name: 'Views',
        data: (data.views?.buckets ?? []).map((bucket) => safeNumber(bucket.views)),
      });
    }
    if (filters.reactions) {
      const likeCount = safeNumber(data.reactions?.totals?.like);
      series.push({
        name: 'Likes (cumulative)',
        data: (data.views?.buckets ?? []).map(() => likeCount),
      });
    }
    if (filters.comments) {
      const byStatus = data.comments?.by_status ?? {};
      const totalComments = safeNumber(data.comments?.total);
      series.push({
        name: 'Comments total',
        data: (data.views?.buckets ?? []).map(() => totalComments),
      });
      const hidden = safeNumber(byStatus.hidden);
      if (hidden) {
        series.push({
          name: 'Hidden comments',
          data: (data.views?.buckets ?? []).map(() => hidden),
        });
      }
    }
    return series;
  }, [data, filters.comments, filters.reactions, filters.views]);
  const delayHint = React.useMemo(() => {
    if (!data?.delay) return null;
    const seconds = safeNumber(data.delay.seconds);
    if (!seconds) return null;
    return `Analytics delayed by ${seconds} seconds (latest ${data.delay.latest_at ?? ''})`;
  }, [data?.delay]);
  const handleFieldChange = React.useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = event.target;
    setFilters((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  }, []);
  const handleReset = React.useCallback(() => {
    setFilters(initialFilters);
  }, []);
  const handleExport = React.useCallback(async () => {
    if (!nodeId) return;
    setExporting(true);
    try {
      const query = buildQuery();
      const params = new URLSearchParams(query);
      params.set('format', 'csv');
      const url = `/v1/admin/nodes/${encodeURIComponent(nodeId)}/analytics?${params.toString()}`;
      const response = await apiGetRaw(url, { headers: { Accept: 'text/csv' } });
      const blob = await response.blob();
      const downloadUrl = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = `node-${nodeId}-analytics.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(downloadUrl);
      pushToast({ intent: 'success', description: 'Analytics CSV export started.' });
    } catch (err) {
      pushToast({ intent: 'error', description: extractErrorMessage(err) });
    } finally {
      setExporting(false);
    }
  }, [buildQuery, nodeId, pushToast]);
  const metrics = React.useMemo(() => {
    if (!data) return [];
    const totalViews = safeNumber(data.views?.total);
    const totalLikes = safeNumber(data.reactions?.totals?.like);
    const totalComments = safeNumber(data.comments?.total);
    const pending = safeNumber(data.comments?.by_status?.pending);
    const hidden = safeNumber(data.comments?.by_status?.hidden);
    return [
      { label: 'Total views', value: formatNumber(totalViews) },
      { label: 'Total likes', value: formatNumber(totalLikes) },
      { label: 'Comments', value: formatNumber(totalComments) },
      { label: 'Pending', value: formatNumber(pending) },
      { label: 'Hidden', value: formatNumber(hidden) },
    ];
  }, [data]);
  return (
    <Card className="space-y-6 p-6" data-testid="analytics-panel" data-analytics="admin.comments.analytics">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <h3 className="text-base font-semibold text-neutral-900 dark:text-neutral-100">Engagement analytics</h3>
          <p className="text-sm text-neutral-600 dark:text-neutral-300">
            Visualize daily views, reactions, and comment statuses with exportable datasets.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outlined"
            color="neutral"
            size="sm"
            onClick={loadAnalytics}
            disabled={loading}
            data-testid="analytics-refresh"
            data-analytics="admin.analytics.refresh"
          >
            {loading ? 'Refreshing...' : 'Refresh'}
          </Button>
          <Button
            variant="outlined"
            color="neutral"
            size="sm"
            onClick={handleReset}
            disabled={loading}
            data-testid="analytics-reset"
          >
            Reset
          </Button>
          <Button
            size="sm"
            variant="outlined"
            onClick={handleExport}
            disabled={exporting || loading}
            data-testid="analytics-export"
            data-analytics="admin.analytics.export.csv"
          >
            {exporting ? 'Exporting...' : 'Export CSV'}
          </Button>
        </div>
      </div>
      <div className="grid gap-4 md:grid-cols-3" data-testid="analytics-filters">
        <div className="space-y-1">
          <label htmlFor="analytics-start" className="text-sm font-medium text-neutral-800 dark:text-neutral-200">
            Start date
          </label>
          <Input
            id="analytics-start"
            type="date"
            name="start"
            value={filters.start}
            onChange={handleFieldChange}
            data-testid="analytics-start-input"
          />
        </div>
        <div className="space-y-1">
          <label htmlFor="analytics-end" className="text-sm font-medium text-neutral-800 dark:text-neutral-200">
            End date
          </label>
          <Input
            id="analytics-end"
            type="date"
            name="end"
            value={filters.end}
            onChange={handleFieldChange}
            data-testid="analytics-end-input"
          />
        </div>
        <div className="space-y-1">
          <label htmlFor="analytics-limit" className="text-sm font-medium text-neutral-800 dark:text-neutral-200">
            Buckets limit
          </label>
          <Input
            id="analytics-limit"
            type="number"
            min={1}
            max={365}
            name="limit"
            value={filters.limit}
            onChange={handleFieldChange}
            data-testid="analytics-limit-input"
          />
        </div>
        <div className="col-span-full flex flex-wrap items-center gap-4" data-testid="analytics-segments">
          <label className="flex items-center gap-2 text-sm text-neutral-700 dark:text-neutral-200">
            <Checkbox name="views" checked={filters.views} onChange={handleFieldChange} />
            Views
          </label>
          <label className="flex items-center gap-2 text-sm text-neutral-700 dark:text-neutral-200">
            <Checkbox name="reactions" checked={filters.reactions} onChange={handleFieldChange} />
            Likes
          </label>
          <label className="flex items-center gap-2 text-sm text-neutral-700 dark:text-neutral-200">
            <Checkbox name="comments" checked={filters.comments} onChange={handleFieldChange} />
            Comments
          </label>
        </div>
      </div>
      {delayHint && (
        <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-2 text-xs text-amber-700 dark:border-amber-500/60 dark:bg-amber-900/20 dark:text-amber-200" data-testid="analytics-delay">
          {delayHint}
        </div>
      )}
      {error ? (
        <Card className="border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-500/60 dark:bg-rose-900/30 dark:text-rose-200">
          {error}
        </Card>
      ) : loading && !data ? (
        <div className="flex flex-col items-center gap-2 py-16 text-sm text-neutral-500 dark:text-neutral-300">
          <Spinner />
          <span>Loading analytics...</span>
        </div>
      ) : data ? (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" data-testid="analytics-metrics">
            {metrics.map((metric) => (
              <MetricCard key={metric.label} label={metric.label} value={metric.value} tone="neutral" />
            ))}
          </div>
          <div className="rounded-lg border border-neutral-200 p-4 dark:border-dark-600" data-testid="analytics-chart">
            {chartSeries.length ? (
              <LineChart
                series={chartSeries}
                height={320}
                options={{
                  xaxis: { categories },
                  yaxis: { labels: { formatter: (value: number) => formatNumber(value) } },
                  stroke: { width: 2 },
                }}
              />
            ) : (
              <div className="py-16 text-center text-sm text-neutral-500 dark:text-neutral-300">Select at least one segment to visualize.</div>
            )}
          </div>
        </>
      ) : (
        <Card className="border border-dashed border-neutral-300 bg-neutral-50 p-6 text-center text-sm text-neutral-500 dark:border-dark-500 dark:bg-dark-700/40 dark:text-dark-100">
          Analytics data is unavailable for this node.
        </Card>
      )}
    </Card>
  );
}
export default AnalyticsPanel;
