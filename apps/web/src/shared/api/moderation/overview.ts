import { apiGet } from '../client';
import type {
  ModerationOverview,
  ModerationOverviewCard,
  ModerationOverviewChart,
} from '../../types/moderation';
import {
  ensureArray,
  isObjectRecord,
  normalizeSanction,
  pickNumber,
  pickNullableString,
  pickString,
} from './utils';

export type FetchModerationOverviewParams = {
  range?: string;
  signal?: AbortSignal;
};

const TREND_VALUES = new Set<NonNullable<ModerationOverviewCard['trend']>>(['up', 'down', 'steady']);

function normalizeCounters(raw: unknown): Record<string, number> {
  if (!isObjectRecord(raw)) {
    return {};
  }
  const entries: Record<string, number> = {};
  Object.entries(raw).forEach(([key, value]) => {
    const numeric = pickNumber(value);
    if (numeric != null) {
      entries[String(key)] = numeric;
    }
  });
  return entries;
}

function normalizeComplaintsBlock(raw: unknown): Record<string, number> {
  if (!isObjectRecord(raw)) {
    return {};
  }
  const counters: Record<string, number> = {};
  const total = pickNumber(raw.count);
  if (total != null) {
    counters.total = total;
  }
  if (isObjectRecord(raw.by_category)) {
    Object.entries(normalizeCounters(raw.by_category)).forEach(([key, value]) => {
      counters[key] = value;
    });
  } else {
    Object.entries(normalizeCounters(raw)).forEach(([key, value]) => {
      if (key !== 'count') {
        counters[key] = value;
      }
    });
  }
  return counters;
}

function normalizeCards(raw: unknown): ModerationOverviewCard[] {
  return ensureArray(raw, (item, index) => {
    if (!isObjectRecord(item)) {
      return null;
    }
    const id = pickString(item.id) ?? `card-${index}`;
    const title = pickString(item.title) ?? id;
    const valueSource = pickString((item as Record<string, unknown>).value);
    const meta = isObjectRecord(item.meta) ? item.meta : undefined;
    const computedValue =
      valueSource ??
      pickString(meta?.value) ??
      pickString(meta?.count) ??
      pickString(item.subtitle) ??
      undefined;
    const trendRaw = pickString(item.trend)?.toLowerCase();
    const trend = trendRaw && TREND_VALUES.has(trendRaw as NonNullable<ModerationOverviewCard['trend']>)
      ? (trendRaw as NonNullable<ModerationOverviewCard['trend']>)
      : undefined;
    const actions = ensureArray(item.actions, (action) => {
      if (!isObjectRecord(action)) {
        return null;
      }
      const label = pickString(action.label);
      if (!label) {
        return null;
      }
      const to = pickString(action.to);
      const href = pickString(action.href);
      const kind = pickString(action.kind) as ModerationOverviewCard['actions'][number]['kind'];
      return {
        label,
        ...(to ? { to } : {}),
        ...(href ? { href } : {}),
        ...(kind ? { kind } : {}),
      };
    });
    const roleVisibility = ensureArray(item.roleVisibility, pickString);

    return {
      id,
      title,
      value: computedValue,
      subtitle: pickNullableString(item.subtitle) ?? undefined,
      description: pickNullableString(item.description) ?? undefined,
      delta: pickNullableString(item.delta) ?? undefined,
      trend,
      status: pickNullableString(item.status) ?? undefined,
      meta: meta ?? {},
      actions,
      roleVisibility: roleVisibility.length ? roleVisibility : undefined,
    };
  });
}

function normalizeCharts(raw: unknown): ModerationOverviewChart[] {
  if (!isObjectRecord(raw)) {
    return [];
  }
  const charts: ModerationOverviewChart[] = [];
  const sources = ensureArray(raw.complaint_sources, (entry) => {
    if (!isObjectRecord(entry)) {
      return null;
    }
    const label = pickString(entry.label);
    const value = pickNumber(entry.value);
    if (!label || value == null) {
      return null;
    }
    return { label, value };
  });
  if (sources.length) {
    charts.push({
      id: 'complaint-sources',
      title: 'Complaint sources',
      type: 'pie',
      series: sources.map((entry) => entry.value),
      options: {
        labels: sources.map((entry) => entry.label),
      },
    });
  }

  const avgResponse = pickNumber(raw.avg_response_time_hours);
  if (avgResponse != null) {
    charts.push({
      id: 'avg-response-time',
      title: 'Average response time (hours)',
      type: 'bar',
      series: [
        {
          name: 'Hours',
          data: [avgResponse],
        },
      ],
      options: {
        xaxis: { categories: ['24h window'] },
        dataLabels: { enabled: true },
      },
    });
  }

  const aiShare = pickNumber(raw.ai_autodecisions_share);
  if (aiShare != null) {
    const boundedShare = Math.max(0, Math.min(1, aiShare));
    charts.push({
      id: 'ai-decisions-share',
      title: 'AI auto-decisions share',
      type: 'pie',
      series: [boundedShare, Number.parseFloat((1 - boundedShare).toFixed(4))],
      options: {
        labels: ['AI decisions', 'Human decisions'],
      },
    });
  }

  return charts;
}

export async function fetchModerationOverview(
  params: FetchModerationOverviewParams = {},
): Promise<ModerationOverview> {
  const { range, signal } = params;
  const query = new URLSearchParams();
  if (range && range.trim()) {
    query.set('range', range.trim());
  }
  const path = query.size ? `/api/moderation/overview?${query.toString()}` : '/api/moderation/overview';
  const payload = await apiGet<unknown>(path, { signal });
  const source = isObjectRecord(payload) ? payload : {};

  const complaints = normalizeComplaintsBlock(source.complaints_new ?? source.complaints);
  const tickets = normalizeCounters(source.tickets);
  const contentQueues = normalizeCounters(source.content_queues ?? source.queues);
  const lastSanctions = ensureArray(source.last_sanctions, (item, index) => normalizeSanction(item, `sanction-${index}`));
  const cards = normalizeCards(source.cards);
  const charts = normalizeCharts(source.charts);

  return {
    complaints,
    tickets,
    contentQueues,
    lastSanctions,
    cards,
    charts,
  };
}
