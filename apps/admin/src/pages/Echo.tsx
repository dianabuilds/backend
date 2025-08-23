import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";

interface EchoTrace {
  id: string;
  from_slug: string;
  to_slug: string;
  user_id?: string | null;
  source?: string | null;
  channel?: string | null;
  created_at: string;
}

type Filters = {
  from?: string;
  to?: string;
  user_id?: string;
  source?: string;
  channel?: string;
  date_from?: string;
  date_to?: string;
};

async function fetchEcho(page: number, filters: Filters): Promise<EchoTrace[]> {
  const params = new URLSearchParams();
  params.set("page", String(page));
  if (filters.from) params.set("from", filters.from);
  if (filters.to) params.set("to", filters.to);
  if (filters.user_id) params.set("user_id", filters.user_id);
  if (filters.source) params.set("source", filters.source);
  if (filters.channel) params.set("channel", filters.channel);
  if (filters.date_from) params.set("date_from", filters.date_from);
  if (filters.date_to) params.set("date_to", filters.date_to);
  const qs = params.toString() ? `?${params.toString()}` : "";
  const res = await api.get<EchoTrace[]>(`/admin/echo${qs}`);
  return (res.data || []) as EchoTrace[];
}

async function deleteEcho(id: string) {
  await api.del(`/admin/echo/${id}`);
}

async function anonymizeEcho(id: string) {
  await api.post(`/admin/echo/${id}/anonymize`);
}

async function bulkAnonymizeEcho(ids: string[]) {
  await api.post(`/admin/echo/bulk/anonymize`, { ids });
}

async function bulkDeleteEcho(ids: string[]) {
  await api.post(`/admin/echo/bulk/delete`, { ids });
}

async function recomputePopularity(slugs: string[]) {
  await api.post(`/admin/echo/recompute_popularity`, { node_slugs: slugs.length ? slugs : undefined });
}

export default function Echo() {
  const [page, setPage] = useState(1);
  const [recomputeInput, setRecomputeInput] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [userId, setUserId] = useState("");
  const [source, setSource] = useState("");
  const [channel, setChannel] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [selected, setSelected] = useState<Record<string, boolean>>({});

  const filters = useMemo<Filters>(
    () => ({
      from: from.trim() || undefined,
      to: to.trim() || undefined,
      user_id: userId.trim() || undefined,
      source: source.trim() || undefined,
      channel: channel.trim() || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    }),
    [from, to, userId, source, channel, dateFrom, dateTo]
  );

  const queryClient = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ["echo", page, filters],
    queryFn: () => fetchEcho(page, filters),
  });

  const refresh = () => queryClient.invalidateQueries({ queryKey: ["echo"] });

  const handleDelete = async (id: string) => {
    await deleteEcho(id);
    refresh();
  };

  const handleAnon = async (id: string) => {
    await anonymizeEcho(id);
    refresh();
  };

  const handleRecompute = async () => {
    const slugs = recomputeInput.split(",").map((s) => s.trim()).filter(Boolean);
    await recomputePopularity(slugs);
    setRecomputeInput("");
  };

  const idsSelected = useMemo(() => Object.keys(selected).filter((k) => selected[k]), [selected]);
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
    await bulkAnonymizeEcho(idsSelected);
    clearSelection();
    refresh();
  };

  const handleBulkDelete = async () => {
    if (idsSelected.length === 0) return;
    await bulkDeleteEcho(idsSelected);
    clearSelection();
    refresh();
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Echo Traces</h1>

      <div className="mb-3 grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-2">
        <input value={from} onChange={(e) => setFrom(e.target.value)} placeholder="from slug" className="border rounded px-2 py-1" />
        <input value={to} onChange={(e) => setTo(e.target.value)} placeholder="to slug" className="border rounded px-2 py-1" />
        <input value={userId} onChange={(e) => setUserId(e.target.value)} placeholder="user id (UUID)" className="border rounded px-2 py-1" />
        <input value={source} onChange={(e) => setSource(e.target.value)} placeholder="source" className="border rounded px-2 py-1" />
        <input value={channel} onChange={(e) => setChannel(e.target.value)} placeholder="channel" className="border rounded px-2 py-1" />
        <input value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} type="datetime-local" placeholder="date from" className="border rounded px-2 py-1" />
        <input value={dateTo} onChange={(e) => setDateTo(e.target.value)} type="datetime-local" placeholder="date to" className="border rounded px-2 py-1" />
      </div>

      <div className="mb-4 flex items-center gap-2">
        <input
          type="text"
          placeholder="node slugs (comma separated)"
          value={recomputeInput}
          onChange={(e) => setRecomputeInput(e.target.value)}
          className="border rounded px-2 py-1"
        />
        <button
          onClick={handleRecompute}
          className="px-3 py-1 bg-blue-600 text-white rounded"
        >
          Recompute popularity
        </button>
        <div className="ml-auto flex gap-2">
          <button onClick={handleBulkAnon} className="px-3 py-1 rounded border">Bulk Anon</button>
          <button onClick={handleBulkDelete} className="px-3 py-1 rounded border text-red-600">Bulk Delete</button>
        </div>
      </div>

      {isLoading && <p>Loading...</p>}
      {error && <p className="text-red-500">Error loading traces</p>}
      {!isLoading && !error && (
        <table className="min-w-full text-sm text-left">
          <thead>
            <tr className="border-b">
              <th className="p-2"><input type="checkbox" checked={allChecked} onChange={toggleAll} /></th>
              <th className="p-2">From</th>
              <th className="p-2">To</th>
              <th className="p-2">User</th>
              <th className="p-2">Source</th>
              <th className="p-2">Channel</th>
              <th className="p-2">Created</th>
              <th className="p-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {data?.map((t) => (
              <tr key={t.id} className="border-b hover:bg-gray-50 dark:hover:bg-gray-800">
                <td className="p-2">
                  <input
                    type="checkbox"
                    checked={!!selected[t.id]}
                    onChange={(e) => setSelected((s) => ({ ...s, [t.id]: e.target.checked }))}
                  />
                </td>
                <td className="p-2">{t.from_slug}</td>
                <td className="p-2">{t.to_slug}</td>
                <td className="p-2">{t.user_id ?? "anon"}</td>
                <td className="p-2">{t.source ?? ""}</td>
                <td className="p-2">{t.channel ?? ""}</td>
                <td className="p-2">{new Date(t.created_at).toLocaleString()}</td>
                <td className="p-2 space-x-2">
                  <button onClick={() => handleAnon(t.id)} className="text-blue-600">Anon</button>
                  <button onClick={() => handleDelete(t.id)} className="text-red-600">Del</button>
                </td>
              </tr>
            ))}
            {(data?.length || 0) === 0 && (
              <tr>
                <td colSpan={8} className="p-4 text-center text-gray-500">No echo traces found</td>
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
        <button onClick={clearSelection} className="ml-auto px-3 py-1 border rounded">Clear selection</button>
      </div>
    </div>
  );
}
