import { api } from "./client";

export interface AlertItem {
  id?: string;
  startsAt?: string;
  description: string;
  url?: string | null;
}

export async function getAlerts(): Promise<AlertItem[]> {
  const res = await api.get<any>("/admin/ops/alerts");
  const list: any[] = Array.isArray(res.data)
    ? res.data
    : res.data?.alerts || res.data?.data || [];
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
  }));
}
