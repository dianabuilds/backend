import { api } from './client';

export interface AlertItem {
  id?: string;
  startsAt?: string;
  description: string;
  url?: string | null;
  type?: string;
  severity?: string;
  status?: 'active' | 'resolved';
}

export interface ResolveAlertResponse {
  status: string;
}

type AlertLike = {
  id?: string;
  fingerprint?: string;
  labels?: Record<string, string>;
  startsAt?: string;
  starts_at?: string;
  activeAt?: string;
  active_at?: string;
  description?: string;
  message?: string;
  annotations?: Record<string, string>;
  url?: string;
  generatorURL?: string;
  severity?: string;
  level?: string;
  type?: string;
  status?: string;
  endsAt?: string;
  ends_at?: string;
};

export async function getAlerts(): Promise<AlertItem[]> {
  const res = await api.get<unknown>('/admin/ops/alerts');
  const raw = res.data as unknown;
  let list: unknown[] = [];
  if (Array.isArray(raw)) list = raw as unknown[];
  else if (raw && typeof raw === 'object') {
    const obj = raw as Record<string, unknown> & { alerts?: unknown[]; data?: unknown[] };
    list = (Array.isArray(obj.alerts) ? obj.alerts : Array.isArray(obj.data) ? obj.data : []) as unknown[];
  }
  return (list as AlertLike[]).map((a, i) => ({
    id: a.id || a.fingerprint || a.labels?.alertname || String(i),
    startsAt: a.startsAt || a.starts_at || a.activeAt || a.active_at,
    description:
      a.description || a.message || a.annotations?.description || a.annotations?.summary || '',
    url:
      a.url ||
      a.annotations?.dashboard ||
      a.annotations?.runbook ||
      a.annotations?.link ||
      a.generatorURL ||
      null,
    type: a.type || a.labels?.type || a.labels?.alertname,
    severity: a.severity || a.labels?.severity || a.labels?.level,
    status: (a.status === 'resolved' ? 'resolved' : (a.endsAt || a.ends_at ? 'resolved' : 'active')) as
      | 'active'
      | 'resolved',
  }));
}

export async function resolveAlert(id: string): Promise<ResolveAlertResponse> {
  const res = await api.post(`/admin/ops/alerts/${id}/resolve`, {});
  return res.data as ResolveAlertResponse;
}
