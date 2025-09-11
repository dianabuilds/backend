/* istanbul ignore file */
// Minimal client for telemetry endpoints used by RumTab.
// Implemented via the app's generic API helper to avoid regenerating OpenAPI services.

import { api } from '../../api/client';

async function rumSummaryAdminTelemetryRumSummaryGet(
  params: {
    window?: number;
  } = {},
): Promise<unknown> {
  const qs = new URLSearchParams();
  if (typeof params.window === 'number') qs.set('window', String(params.window));
  const url = '/admin/telemetry/rum/summary' + (qs.toString() ? `?${qs.toString()}` : '');
  const res = await api.get(url);
  return res.data as unknown;
}

async function listRumEventsAdminTelemetryRumGet(
  event?: string,
  url?: string,
  offset?: number,
  limit?: number,
): Promise<unknown[]> {
  const qs = new URLSearchParams();
  if (event) qs.set('event', event);
  if (url) qs.set('url', url);
  if (typeof offset === 'number') qs.set('offset', String(offset));
  if (typeof limit === 'number') qs.set('limit', String(limit));
  const path = '/admin/telemetry/rum' + (qs.toString() ? `?${qs.toString()}` : '');
  const res = await api.get(path);
  return (res.data as unknown[]) ?? [];
}

export const AdminTelemetryService = {
  rumSummaryAdminTelemetryRumSummaryGet,
  listRumEventsAdminTelemetryRumGet,
};
