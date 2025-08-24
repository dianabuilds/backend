import { useEffect, useState } from "react";

import { api } from "../api/client";
import ErrorBanner from "../components/ErrorBanner";

type Limits = {
  providers: Record<string, number>;
  models: Record<string, number>;
};

type Stats = {
  jobs: Record<string, number>;
  job_avg_ms: number;
  cost_usd_total: number;
  tokens: { prompt: number; completion: number };
  stages: Record<string, { count: number; avg_ms: number }>;
};

export default function AIRateLimits() {
  const [limits, setLimits] = useState<Limits>({ providers: {}, models: {} });
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [err, setErr] = useState<string | null>(null);

  const load = async () => {
    setErr(null);
    setLoading(true);
    try {
      const lr = await api.get<Limits>("/admin/ai/quests/rate_limits");
      setLimits(lr.data || { providers: {}, models: {} });
      const sr = await api.get<Stats>("/admin/ai/quests/stats");
      setStats(sr.data || null);
    } catch (e: any) {
      setErr(e?.message || "Ошибка загрузки");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const setProv = (k: string, v: string) => {
    setLimits((prev) => ({
      ...prev,
      providers: { ...(prev.providers || {}), [k]: Number(v || 0) },
    }));
  };
  const rmProv = (k: string) => {
    setLimits((prev) => {
      const p = { ...(prev.providers || {}) };
      delete p[k];
      return { ...prev, providers: p };
    });
  };
  const setModel = (k: string, v: string) => {
    setLimits((prev) => ({
      ...prev,
      models: { ...(prev.models || {}), [k]: Number(v || 0) },
    }));
  };
  const rmModel = (k: string) => {
    setLimits((prev) => {
      const m = { ...(prev.models || {}) };
      delete m[k];
      return { ...prev, models: m };
    });
  };

  const save = async () => {
    setErr(null);
    setLoading(true);
    try {
      await api.post("/admin/ai/quests/rate_limits", limits);
      alert("Лимиты сохранены (оверрайды применены)");
    } catch (e: any) {
      setErr(e?.message || "Ошибка сохранения");
    } finally {
      setLoading(false);
    }
  };

  const addProv = () => setProv("", "60");
  const addModel = () => setModel("", "60");

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-lg font-semibold">AI — Rate limits</h1>
      {err ? <ErrorBanner message={err} onClose={() => setErr(null)} /> : null}
      <div className="rounded border p-3 space-y-2">
        <div className="text-sm text-gray-500">Провайдеры (RPM)</div>
        <div className="space-y-2">
          {Object.entries(limits.providers || {}).map(([k, v]) => (
            <div key={k} className="flex items-center gap-2">
              <input
                className="rounded border px-2 py-1 w-64"
                placeholder="provider (например, openai)"
                value={k}
                onChange={(e) => {
                  const nk = e.target.value;
                  setLimits((prev) => {
                    const p = { ...(prev.providers || {}) };
                    const val = p[k];
                    delete p[k];
                    p[nk] = val;
                    return { ...prev, providers: p };
                  });
                }}
              />
              <input
                className="rounded border px-2 py-1 w-32"
                type="number"
                min={1}
                value={v as any}
                onChange={(e) => setProv(k, e.target.value)}
              />
              <button
                className="text-red-600 hover:underline text-sm"
                onClick={() => rmProv(k)}
              >
                удалить
              </button>
            </div>
          ))}
        </div>
        <button
          onClick={addProv}
          className="text-sm px-3 py-1.5 rounded bg-gray-100 hover:bg-gray-200"
        >
          + провайдер
        </button>
      </div>

      <div className="rounded border p-3 space-y-2">
        <div className="text-sm text-gray-500">Модели (RPM)</div>
        <div className="space-y-2">
          {Object.entries(limits.models || {}).map(([k, v]) => (
            <div key={k} className="flex items-center gap-2">
              <input
                className="rounded border px-2 py-1 w-64"
                placeholder="model (например, gpt-4o-mini)"
                value={k}
                onChange={(e) => {
                  const nk = e.target.value;
                  setLimits((prev) => {
                    const m = { ...(prev.models || {}) };
                    const val = m[k];
                    delete m[k];
                    m[nk] = val;
                    return { ...prev, models: m };
                  });
                }}
              />
              <input
                className="rounded border px-2 py-1 w-32"
                type="number"
                min={1}
                value={v as any}
                onChange={(e) => setModel(k, e.target.value)}
              />
              <button
                className="text-red-600 hover:underline text-sm"
                onClick={() => rmModel(k)}
              >
                удалить
              </button>
            </div>
          ))}
        </div>
        <button
          onClick={addModel}
          className="text-sm px-3 py-1.5 rounded bg-gray-100 hover:bg-gray-200"
        >
          + модель
        </button>
      </div>

      <div className="flex gap-2">
        <button
          onClick={save}
          disabled={loading}
          className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Сохранение…" : "Сохранить лимиты"}
        </button>
        <button
          onClick={load}
          disabled={loading}
          className="px-4 py-2 rounded bg-gray-100 hover:bg-gray-200 disabled:opacity-50"
        >
          Обновить
        </button>
      </div>

      <div className="rounded border p-3">
        <div className="text-sm text-gray-500">Статистика стадий</div>
        {stats ? (
          <div className="text-sm">
            <div className="mb-2">
              Jobs: started={stats.jobs?.started || 0}, completed=
              {stats.jobs?.completed || 0}, failed={stats.jobs?.failed || 0}
            </div>
            <div className="mb-2">
              Avg job duration: {stats.job_avg_ms.toFixed(0)} ms; cost: $
              {stats.cost_usd_total.toFixed(4)}; tokens: prompt=
              {stats.tokens.prompt}, completion={stats.tokens.completion}
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="text-left text-gray-500">
                    <th className="px-2 py-1">Stage</th>
                    <th className="px-2 py-1">Count</th>
                    <th className="px-2 py-1">Avg duration, ms</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(stats.stages || {}).map(([name, s]) => (
                    <tr key={name} className="border-t">
                      <td className="px-2 py-1">{name}</td>
                      <td className="px-2 py-1">{(s as any).count}</td>
                      <td className="px-2 py-1">
                        {((s as any).avg_ms || 0).toFixed(0)}
                      </td>
                    </tr>
                  ))}
                  {Object.keys(stats.stages || {}).length === 0 ? (
                    <tr>
                      <td className="px-2 py-3 text-gray-500" colSpan={3}>
                        нет данных
                      </td>
                    </tr>
                  ) : null}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="text-sm text-gray-500">Нет данных</div>
        )}
      </div>
    </div>
  );
}
