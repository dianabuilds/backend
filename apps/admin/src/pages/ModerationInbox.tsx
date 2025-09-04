import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  type CaseListItem,
  createCase,
  listCases,
} from "../api/moderationCases";
import PageLayout from "./_shared/PageLayout";

export default function ModerationInbox() {
  const navigate = useNavigate();
  const [items, setItems] = useState<CaseListItem[]>([]);
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [priority, setPriority] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await listCases({
        q,
        status,
        type: typeFilter,
        priority,
        page: 1,
        size: 50,
      });
      setItems(res.items);
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

  const onCreate = async () => {
    const summary = prompt("Summary of case:");
    if (!summary) return;
    const id = await createCase({ type: "support_request", summary });
    navigate(`/moderation/cases/${id}`);
  };

  const table = useMemo(() => {
    if (loading) return <div className="text-sm text-gray-500">Loading...</div>;
    if (error) return <div className="text-sm text-red-600">{error}</div>;
    return (
      <table className="min-w-full text-sm">
        <thead className="text-left text-gray-500">
          <tr>
            <th className="py-2 pr-4">Summary</th>
            <th className="py-2 pr-4">Type</th>
            <th className="py-2 pr-4">Status</th>
            <th className="py-2 pr-4">Priority</th>
            <th className="py-2 pr-4">Assignee</th>
            <th className="py-2 pr-4">Labels</th>
            <th className="py-2 pr-4">Created</th>
          </tr>
        </thead>
        <tbody>
          {items.map((it) => (
            <tr
              key={it.id}
              className="border-t border-gray-200 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer"
              onClick={() => navigate(`/moderation/cases/${it.id}`)}
            >
              <td className="py-2 pr-4">{it.summary}</td>
              <td className="py-2 pr-4">{it.type}</td>
              <td className="py-2 pr-4">{it.status}</td>
              <td className="py-2 pr-4">{it.priority}</td>
              <td className="py-2 pr-4 font-mono">
                {it.assignee_id?.slice(0, 8) ?? "-"}
              </td>
              <td className="py-2 pr-4">{it.labels.join(", ")}</td>
              <td className="py-2 pr-4">
                {new Date(it.created_at).toLocaleString()}
              </td>
            </tr>
          ))}
          {items.length === 0 && (
            <tr>
              <td className="py-6 text-gray-500" colSpan={7}>
                No cases
              </td>
            </tr>
          )}
        </tbody>
      </table>
    );
  }, [items, loading, error, navigate]);

  return (
    <PageLayout
      title="Moderation — Inbox"
      subtitle="Список обращений и жалоб"
      actions={
        <button
          className="px-3 py-1 rounded bg-blue-600 text-white"
          onClick={onCreate}
        >
          New case
        </button>
      }
    >
      <div className="flex gap-2 mb-3 flex-wrap items-center">
        <input
          className="border rounded px-2 py-1 w-64"
          placeholder="Search..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <select
          className="border rounded px-2 py-1"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option value="">All statuses</option>
          <option value="new">New</option>
          <option value="in_progress">In progress</option>
          <option value="resolved">Resolved</option>
          <option value="rejected">Rejected</option>
        </select>
        <select
          className="border rounded px-2 py-1"
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
        >
          <option value="">All types</option>
          <option value="support_request">Support request</option>
          <option value="complaint_content">Content complaint</option>
          <option value="complaint_user">User complaint</option>
          <option value="appeal">Appeal</option>
        </select>
        <select
          className="border rounded px-2 py-1"
          value={priority}
          onChange={(e) => setPriority(e.target.value)}
        >
          <option value="">Any priority</option>
          <option value="P0">P0</option>
          <option value="P1">P1</option>
          <option value="P2">P2</option>
        </select>
        <button
          className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-800"
          onClick={load}
        >
          Apply
        </button>
      </div>
      {table}
    </PageLayout>
  );
}
