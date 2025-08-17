import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";

type TransitionItem = Record<string, any>;

function ensureArray<T = any>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === "object") {
    const obj = data as any;
    if (Array.isArray(obj.items)) return obj.items as T[];
    if (Array.isArray(obj.data)) return obj.data as T[];
  }
  return [];
}

export default function Transitions() {
  const [items, setItems] = useState<TransitionItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [weights, setWeights] = useState<Record<string, string>>({});

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (from) params.set("from_slug", from);
      if (to) params.set("to_slug", to);
      const qs = params.toString() ? `?${params.toString()}` : "";
      const res = await api.get(`/admin/transitions${qs}`);
      const data = ensureArray<TransitionItem>(res.data);
      setItems(data);
      // заполняем локальные значения весов
      const w: Record<string, string> = {};
      for (const t of data) {
        const id = String(t.id ?? "");
        if (id) w[id] = String(t.weight ?? t.priority ?? "");
      }
      setWeights(w);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const ids = useMemo(() => items.map((it) => String(it.id ?? "")), [items]);

  const setWeightValue = (id: string, v: string) => setWeights((m) => ({ ...m, [id]: v }));

  const patchTransition = async (id: string, body: Record<string, any>) => {
    await api.patch(`/admin/transitions/${id}`, body);
  };

  const toggleDisabled = async (id: string, current: boolean) => {
    await patchTransition(id, { disabled: !current });
    await load();
  };

  const saveWeight = async (id: string) => {
    const v = weights[id];
    const num = Number(v);
    if (isNaN(num)) return;
    // отправим оба поля на случай разных схем
    await patchTransition(id, { weight: num, priority: num });
    await load();
  };

  const deleteTransition = async (id: string) => {
    await api.del(`/admin/transitions/${id}`);
    await load();
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Transitions</h1>
      <div className="mb-4 flex items-center gap-2">
        <input value={from} onChange={(e) => setFrom(e.target.value)} placeholder="from slug" className="border rounded px-2 py-1" />
        <input value={to} onChange={(e) => setTo(e.target.value)} placeholder="to slug" className="border rounded px-2 py-1" />
        <button onClick={load} className="px-3 py-1 rounded border">Search</button>
      </div>
      {loading && <p>Loading...</p>}
      {error && <p className="text-red-600">{error}</p>}
      {!loading && !error && (
        <table className="min-w-full text-sm text-left">
          <thead>
            <tr className="border-b">
              <th className="p-2">ID</th>
              <th className="p-2">From</th>
              <th className="p-2">To</th>
              <th className="p-2">Weight</th>
              <th className="p-2">Disabled</th>
              <th className="p-2">Updated</th>
              <th className="p-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((t, i) => {
              const id = String(t.id ?? i);
              const disabled = Boolean(t.disabled ?? false);
              return (
                <tr key={id} className="border-b hover:bg-gray-50 dark:hover:bg-gray-800">
                  <td className="p-2 font-mono">{t.id ?? "-"}</td>
                  <td className="p-2">{t.from_slug ?? "-"}</td>
                  <td className="p-2">{t.to_slug ?? "-"}</td>
                  <td className="p-2">
                    <div className="flex items-center gap-2">
                      <input
                        className="border rounded px-2 py-1 w-24"
                        value={weights[id] ?? ""}
                        onChange={(e) => setWeightValue(id, e.target.value)}
                      />
                      <button onClick={() => saveWeight(id)} className="px-2 py-1 rounded border">Save</button>
                    </div>
                  </td>
                  <td className="p-2">{String(disabled)}</td>
                  <td className="p-2">{t.updated_at ? new Date(t.updated_at).toLocaleString() : "-"}</td>
                  <td className="p-2 space-x-2">
                    <button onClick={() => toggleDisabled(id, disabled)} className="text-blue-600">{disabled ? "Enable" : "Disable"}</button>
                    <button onClick={() => deleteTransition(id)} className="text-red-600">Del</button>
                  </td>
                </tr>
              );
            })}
            {ids.length === 0 && (
              <tr>
                <td colSpan={7} className="p-4 text-center text-gray-500">No transitions found</td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}
