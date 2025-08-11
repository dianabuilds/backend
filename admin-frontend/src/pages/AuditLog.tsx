import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";

interface AuditLogEntry {
  id: string;
  actor_id?: string | null;
  action: string;
  resource_type?: string | null;
  resource_id?: string | null;
  before?: unknown;
  after?: unknown;
  ip?: string | null;
  user_agent?: string | null;
  created_at: string;
}

import { api } from "../api/client";

async function fetchAudit(params: Record<string, string>): Promise<AuditLogEntry[]> {
  const qs = new URLSearchParams(params).toString();
  const res = await api.get<AuditLogEntry[]>(qs ? `/admin/audit?${qs}` : "/admin/audit");
  return (res.data || []) as AuditLogEntry[];
}

export default function AuditLog() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [actor, setActor] = useState(searchParams.get("actor_id") || "");
  const [action, setAction] = useState(searchParams.get("action") || "");
  const [resource, setResource] = useState(searchParams.get("resource") || "");
  const [dateFrom, setDateFrom] = useState(searchParams.get("date_from") || "");
  const [dateTo, setDateTo] = useState(searchParams.get("date_to") || "");
  const page = searchParams.get("page") || "1";
  const params: Record<string, string> = { page };
  if (searchParams.get("actor_id")) params.actor_id = searchParams.get("actor_id")!;
  if (searchParams.get("action")) params.action = searchParams.get("action")!;
  if (searchParams.get("resource")) params.resource = searchParams.get("resource")!;
  if (searchParams.get("date_from")) params.date_from = searchParams.get("date_from")!;
  if (searchParams.get("date_to")) params.date_to = searchParams.get("date_to")!;

  const { data, isLoading, error } = useQuery({
    queryKey: ["audit", params],
    queryFn: () => fetchAudit(params),
  });

  const [selected, setSelected] = useState<AuditLogEntry | null>(null);

  const applyFilters = () => {
    const next: Record<string, string> = { page: "1" };
    if (actor) next.actor_id = actor;
    if (action) next.action = action;
    if (resource) next.resource = resource;
    if (dateFrom) next.date_from = dateFrom;
    if (dateTo) next.date_to = dateTo;
    setSearchParams(next);
  };

  const changePage = (p: number) => {
    const next = new URLSearchParams(searchParams);
    next.set("page", String(p));
    setSearchParams(next);
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Audit log</h1>
      <div className="mb-4 space-x-2">
        <input
          type="text"
          placeholder="Actor ID"
          value={actor}
          onChange={(e) => setActor(e.target.value)}
          className="border rounded px-2 py-1"
        />
        <input
          type="text"
          placeholder="Action"
          value={action}
          onChange={(e) => setAction(e.target.value)}
          className="border rounded px-2 py-1"
        />
        <input
          type="text"
          placeholder="Resource"
          value={resource}
          onChange={(e) => setResource(e.target.value)}
          className="border rounded px-2 py-1"
        />
        <input
          type="date"
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
          className="border rounded px-2 py-1"
        />
        <input
          type="date"
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
          className="border rounded px-2 py-1"
        />
        <button
          onClick={applyFilters}
          className="px-3 py-1 rounded bg-gray-800 text-white hover:bg-black dark:bg-gray-700 dark:hover:bg-gray-600"
        >
          Apply
        </button>
      </div>
      {isLoading && <p>Loading...</p>}
      {error && (
        <p className="text-red-500">{error instanceof Error ? error.message : String(error)}</p>
      )}
      {!isLoading && !error && (
        <>
          <table className="min-w-full text-sm text-left">
            <thead>
              <tr className="border-b">
                <th className="p-2">Actor</th>
                <th className="p-2">Action</th>
                <th className="p-2">Resource</th>
                <th className="p-2">IP/UA</th>
                <th className="p-2">Time</th>
                <th className="p-2">Diff</th>
              </tr>
            </thead>
            <tbody>
              {data?.map((e) => (
                <tr key={e.id} className="border-b hover:bg-gray-50 dark:hover:bg-gray-800">
                  <td className="p-2 font-mono">{e.actor_id}</td>
                  <td className="p-2">{e.action}</td>
                  <td className="p-2">{e.resource_type ? `${e.resource_type}:${e.resource_id}` : e.resource_id}</td>
                  <td className="p-2">{e.ip} / {e.user_agent}</td>
                  <td className="p-2">{new Date(e.created_at).toLocaleString()}</td>
                  <td className="p-2">
                    {(e.before != null || e.after != null) && (
                      <button
                        className="underline text-blue-600"
                        onClick={() => setSelected(e)}
                      >
                        view
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="mt-4 flex gap-2">
            <button
              onClick={() => changePage(Math.max(1, Number(page) - 1))}
              className="px-2 py-1 border rounded"
            >
              Prev
            </button>
            <span>Page {page}</span>
            <button
              onClick={() => changePage(Number(page) + 1)}
              className="px-2 py-1 border rounded"
            >
              Next
            </button>
          </div>
        </>
      )}
      {selected && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center">
          <div className="bg-white dark:bg-gray-900 p-4 rounded shadow max-w-3xl w-full">
            <h2 className="text-lg font-bold mb-2">Diff</h2>
            <div className="grid grid-cols-2 gap-4 max-h-96 overflow-auto text-xs">
              <pre className="bg-gray-100 dark:bg-gray-800 p-2 overflow-auto">{JSON.stringify(selected.before, null, 2)}</pre>
              <pre className="bg-gray-100 dark:bg-gray-800 p-2 overflow-auto">{JSON.stringify(selected.after, null, 2)}</pre>
            </div>
            <div className="text-right mt-2">
              <button
                onClick={() => setSelected(null)}
                className="px-3 py-1 rounded bg-gray-800 text-white hover:bg-black dark:bg-gray-700 dark:hover:bg-gray-600"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
