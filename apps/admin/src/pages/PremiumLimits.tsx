import { useState } from 'react';

import { api } from '../api/client';

type LimitStatus = {
  plan: string;
  limits: {
    stories?: { month: any };
    [k: string]: any;
  };
};

export default function PremiumLimits() {
  const [userId, setUserId] = useState('');
  const [data, setData] = useState<LimitStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const load = async () => {
    setErr(null);
    setLoading(true);
    try {
      const res = await api.get<LimitStatus>(`/premium/users/${encodeURIComponent(userId)}/limits`);
      setData(res.data!);
    } catch (e: any) {
      setErr(e?.message || 'Ошибка');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-lg font-semibold">Premium — Limits</h1>
      <div className="rounded border p-3">
        <div className="text-sm text-gray-500 mb-2">Проверка лимитов пользователя</div>
        <div className="flex items-center gap-2">
          <input
            className="rounded border px-2 py-1 w-[420px]"
            placeholder="User ID (UUID)"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
          />
          <button
            onClick={load}
            disabled={!userId || loading}
            className="text-sm px-3 py-1.5 rounded bg-gray-100 hover:bg-gray-200 disabled:opacity-50"
          >
            Проверить
          </button>
        </div>
        {err ? <div className="text-sm text-red-600 mt-2">{err}</div> : null}
        {loading ? <div className="text-sm text-gray-500 mt-2">Загрузка…</div> : null}
        {data ? (
          <div className="mt-3 text-sm">
            <div>
              План: <b>{data.plan}</b>
            </div>
            <pre className="mt-2 bg-gray-50 rounded p-2 text-xs whitespace-pre-wrap">
              {JSON.stringify(data.limits, null, 2)}
            </pre>
          </div>
        ) : null}
      </div>
    </div>
  );
}
