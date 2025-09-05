import { api } from "./client";

export interface AlertItem {
  id?: string;
  startsAt?: string;
  description: string;
  url?: string | null;
  type?: string;
  severity?: string;
  status?: "active" | "resolved";
}

export interface ResolveAlertResponse {
  status: string;
}

export async function getAlerts(): Promise<AlertItem[]> {
  const res = await api.get<any>("/admin/ops/alerts");
  const raw = res.data;
  const list: any[] = Array.isArray(raw)
    ? raw
    : raw?.alerts || raw?.data || [];
  return list.map((a, i) => ({
    id: a.id || a.fingerprint || a.labels?.alertname || String(i),
    startsAt: a.startsAt || a.starts_at || a.activeAt || a.active_at,
    description:
      a.description ||
      a.message ||
      a.annotations?.description ||
      a.annotations?.summary ||
      "",
    url:
      a.url ||
      a.annotations?.dashboard ||
      a.annotations?.runbook ||
      a.annotations?.link ||
      a.generatorURL ||
      null,
    type: a.type || a.labels?.type || a.labels?.alertname,
    severity: a.severity || a.labels?.severity || a.labels?.level,
    status:
      a.status ||
      (a.endsAt || a.ends_at ? "resolved" : "active"),
  }));
}

export async function resolveAlert(id: string): Promise<ResolveAlertResponse> {
  const res = await api.post(`/admin/ops/alerts/${id}/resolve`, {});
  return res.data as ResolveAlertResponse;
}
