import { apiGet } from '../client';
import type { ModerationOverview, ModerationOverviewCard, ModerationOverviewChart } from '../../types/moderation';
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
  const source = isObjectRecord(raw) ? raw : {};
  const entries: Record<string, number> = {};
  Object.entries(source).forEach(([key, value]) => {
    const parsed = pickNumber(value);
    if (parsed != null) {
      entries[String(key)] = parsed;
    }
  });
  return entries;
}

function normalizeCard(raw: unknown, index: number): ModerationOverviewCard | null {
  const source = isObjectRecord(raw) ? raw : {};
  const id = pickString(source.id) ?? `card-${index}`;
  const title = pickString(source.title) ?? id;
  const valueSource = source.value ?? source.metric ?? '';
  const value = pickString(valueSource) ?? (pickNumber(valueSource)?.toLocaleString('ru-RU') ?? '');
  if (!title || !value) {
    return null;
  }

  const actions = ensureArray(source.actions, (item) => {
    const actionSource = isObjectRecord(item) ? item : {};
    const label = pickString(actionSource.label);
    if (!label) return null;
    const to = pickString(actionSource.to);
    const href = pickString(actionSource.href);
    const description = pickNullableString(actionSource.description) ?? undefined;
    return {
      label,
      ...(to ? { to } : {}),
      ...(href ? { href } : {}),
      ...(description ? { description } : {}),
    };
  });

  const trendRaw = pickString(source.trend) ?? undefined;
  const trend = trendRaw && TREND_VALUES.has(trendRaw as NonNullable<ModerationOverviewCard['trend']>)
    ? (trendRaw as NonNullable<ModerationOverviewCard['trend']>)
    : undefined;

  const description = pickNullableString(source.description) ?? undefined;
  const delta = pickString(source.delta) ?? undefined;

  return {
    id,
    title,
    value,
    ...(description ? { description } : {}),
    ...(delta ? { delta } : {}),
    ...(trend ? { trend } : {}),
    actions,
  };
}

function normalizeChart(raw: unknown, index: number): ModerationOverviewChart | null {
  const source = isObjectRecord(raw) ? raw : {};
  const id = pickString(source.id) ?? `chart-${index}`;
  const title = pickString(source.title) ?? id;
  if (!title) return null;
  const description = pickNullableString(source.description) ?? undefined;
  const type = pickString(source.type) ?? undefined;
  const options = isObjectRecord(source.options) ? source.options : source.options ?? undefined;
  const series = Array.isArray(source.series) ? source.series : undefined;
  const height = pickNumber(source.height);
  return {
    id,
    title,
    ...(description ? { description } : {}),
    ...(type ? { type } : {}),
    ...(series ? { series } : {}),
    ...(options ? { options } : {}),
    ...(height != null ? { height } : {}),
  };
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

  const complaintsSource = source.complaints_new ?? source.complaints;
  const ticketsSource = source.tickets;
  const queuesSource = source.content_queues ?? source.queues;
  const lastSanctions = ensureArray(source.last_sanctions, (item, index) =>
    normalizeSanction(item, `last-sanction-${index}`),
  );
  const cards = ensureArray(source.cards, normalizeCard).filter(
    (card): card is ModerationOverviewCard => card !== null,
  );
  const charts = ensureArray(source.charts, normalizeChart).filter(
    (chart): chart is ModerationOverviewChart => chart !== null,
  );

  return {
    complaints: normalizeCounters(complaintsSource),
    tickets: normalizeCounters(ticketsSource),
    contentQueues: normalizeCounters(queuesSource),
    lastSanctions,
    cards,
    charts,
  };
}

