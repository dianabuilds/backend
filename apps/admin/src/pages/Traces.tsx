import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { api } from "../api/client";
import PeriodStepSelector from "../components/PeriodStepSelector";

interface TraceItem {
  id: string;
  from_slug?: string;
  to_slug?: string;
  user_id?: string | null;
  source?: string | null;
  channel?: string | null;
  type?: string | null;
  created_at?: string;
  latency_ms?: number | null;
  request_id?: string | null;
}

type Filters = {
  from?: string;
  to?: string;
  user_id?: string;
  source?: string;
  channel?: string;
  type?: string;
  date_from?: string;
  date_to?: string;
};

async function fetchTraces(
  page: number,
  filters: Filters,
): Promise<TraceItem[]> {
  const params = new URLSearchParams();
  params.set("page", String(page));
  if (filters.from) params.set("from", filters.from);
  if (filters.to) params.set("to", filters.to);
  if (filters.user_id) params.set("user_id", filters.user_id);
  if (filters.source) params.set("source", filters.source);
  if (filters.channel) params.set("channel", filters.channel);
  if (filters.type) params.set("type", filters.type);
  if (filters.date_from) params.set("date_from", filters.date_from);
  if (filters.date_to) params.set("date_to", filters.date_to);
  const qs = params.toString() ? `?${params.toString()}` : "";
  const res = await api.get<TraceItem[]>(`/admin/traces${qs}`);
  return (res.data || []) as TraceItem[];
}

async function anonymizeTrace(id: string) {
  await api.post(`/admin/traces/${id}/anonymize`);
}
async function deleteTrace(id: string) {
  await api.del(`/admin/traces/${id}`);
}
async function bulkAnonymize(ids: string[]) {
  await api.post(`/admin/traces/bulk/anonymize`, { ids });
}
async function bulkDelete(ids: string[]) {
  await api.post(`/admin/traces/bulk/delete`, { ids });
}

export default function Traces() {
  const [page, setPage] = useState(1);
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [userId, setUserId] = useState("");
  const [source, setSource] = useState("");
  const [channel, setChannel] = useState("");
  const [type, setType] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [selected, setSelected] = useState<Record<string, boolean>>({});
  const [range, setRange] = useState<"1h" | "24h">("1h");
  const [step, setStep] = useState<60 | 300>(60);

  const filters = useMemo<Filters>(
    () => ({
      from: from.trim() || undefined,
      to: to.trim() || undefined,
      user_id: userId.trim() || undefined,
      source: source.trim() || undefined,
      channel: channel.trim() || undefined,
      type: type.trim() || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    }),
    [from, to, userId, source, channel, type, dateFrom, dateTo],
  );

  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["traces", page, filters],
    queryFn: () => fetchTraces(page, filters),
  });

  const refresh = () => queryClient.invalidateQueries({ queryKey: ["traces"] });

  const idsSelected = useMemo(
    () => Object.keys(selected).filter((k) => selected[k]),
    [selected],
  );
  const allChecked = useMemo(() => {
    const items = data || [];
    return items.length > 0 && items.every((t) => selected[t.id]);
  }, [data, selected]);

  const toggleAll = () => {
    const items = data || [];
    const next: Record<string, boolean> = {};
    const value = !allChecked;
    for (const t of items) next[t.id] = value;
    setSelected(next);
  };
  const clearSelection = () => setSelected({});

  const handleBulkAnon = async () => {
    if (idsSelected.length === 0) return;
    await bulkAnonymize(idsSelected);
    clearSelection();
    refresh();
  };
  const handleBulkDelete = async () => {
    if (idsSelected.length === 0) return;
    await bulkDelete(idsSelected);
    clearSelection();
    refresh();
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Traces</h1>
      <PeriodStepSelector
        range={range}
        step={step}
        onRangeChange={setRange}
        onStepChange={setStep}
        className="mb-2"
      />
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
        Search and inspect transition traces. Use filters to narrow results.
      </p>

      <div className="mb-3 grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-2">
        <input
          value={from}
          onChange={(e) => setFrom(e.target.value)}
          placeholder="from slug"
          className="border rounded px-2 py-1"
        />
        <input
          value={to}
          onChange={(e) => setTo(e.target.value)}
          placeholder="to slug"
          className="border rounded px-2 py-1"
        />
        <input
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          placeholder="user id (UUID)"
          className="border rounded px-2 py-1"
        />
        <input
          value={source}
          onChange={(e) => setSource(e.target.value)}
          placeholder="source"
          className="border rounded px-2 py-1"
        />
        <input
          value={channel}
          onChange={(e) => setChannel(e.target.value)}
          placeholder="channel"
          className="border rounded px-2 py-1"
        />
        <input
          value={type}
          onChange={(e) => setType(e.target.value)}
          placeholder="type"
          className="border rounded px-2 py-1"
        />
        <input
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
          type="datetime-local"
          placeholder="date from"
          className="border rounded px-2 py-1"
        />
        <input
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
          type="datetime-local"
          placeholder="date to"
          className="border rounded px-2 py-1"
        />
      </div>

      <div className="mb-3 flex items-center gap-2">
        <button onClick={handleBulkAnon} className="px-3 py-1 rounded border">
          Bulk Anon
        </button>
        <button
          onClick={handleBulkDelete}
          className="px-3 py-1 rounded border text-red-600"
        >
          Bulk Delete
        </button>
      </div>

      {isLoading && <p>Loading...</p>}
      {error && <p className="text-red-500">Error loading traces</p>}
      {!isLoading && !error && (
        <table className="min-w-full text-sm text-left">
          <thead>
            <tr className="border-b">
              <th className="p-2">
                <input
                  type="checkbox"
                  checked={allChecked}
                  onChange={toggleAll}
                />
              </th>
              <th className="p-2">From</th>
              <th className="p-2">To</th>
              <th className="p-2">User</th>
              <th className="p-2">Type</th>
              <th className="p-2">Source</th>
              <th className="p-2">Channel</th>
              <th className="p-2">Latency</th>
              <th className="p-2">Created</th>
              <th className="p-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {data?.map((t) => (
              <tr
                key={t.id}
                className="border-b hover:bg-gray-50 dark:hover:bg-gray-800"
              >
                <td className="p-2">
                  <input
                    type="checkbox"
                    checked={!!selected[t.id]}
                    onChange={(e) =>
                      setSelected((s) => ({ ...s, [t.id]: e.target.checked }))
                    }
                  />
                </td>
                <td className="p-2">{t.from_slug ?? "-"}</td>
                <td className="p-2">{t.to_slug ?? "-"}</td>
                <td className="p-2">{t.user_id ?? "anon"}</td>
                <td className="p-2">{t.type ?? "-"}</td>
                <td className="p-2">{t.source ?? "-"}</td>
                <td className="p-2">{t.channel ?? "-"}</td>
                <td className="p-2">
                  {t.latency_ms != null ? `${t.latency_ms} ms` : "-"}
                </td>
                <td className="p-2">
                  {t.created_at ? new Date(t.created_at).toLocaleString() : "-"}
                </td>
                <td className="p-2 space-x-2">
                  <button
                    onClick={async () => {
                      await anonymizeTrace(t.id);
                      refresh();
                    }}
                    className="text-blue-600"
                  >
                    Anon
                  </button>
                  <button
                    onClick={async () => {
                      await deleteTrace(t.id);
                      refresh();
                    }}
                    className="text-red-600"
                  >
                    Del
                  </button>
                </td>
              </tr>
            ))}
            {(data?.length || 0) === 0 && (
              <tr>
                <td colSpan={10} className="p-4 text-center text-gray-500">
                  No traces found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}

      <div className="mt-4 flex gap-2 items-center">
        <button
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          className="px-3 py-1 border rounded"
        >
          Prev
        </button>
        <span>Page {page}</span>
        <button
          onClick={() => setPage((p) => p + 1)}
          className="px-3 py-1 border rounded"
        >
          Next
        </button>
        <button
          onClick={clearSelection}
          className="ml-auto px-3 py-1 border rounded"
        >
          Clear selection
        </button>
      </div>
    </div>
  );
}
