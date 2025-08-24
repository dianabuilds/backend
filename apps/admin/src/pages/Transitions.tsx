import { useEffect, useMemo, useState } from "react";

import {
  createTransition,
  deleteTransition as apiDeleteTransition,
  listTransitions,
  type Transition,
  updateTransition,
} from "../api/transitions";

function ensureArray<T = any>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === "object") {
    const obj = data as any;
    if (Array.isArray(obj.items)) return obj.items as T[];
    if (Array.isArray(obj.data)) return obj.data as T[];
  }
  return [];
}

type StatusFilter = "any" | "enabled" | "disabled";

export default function Transitions() {
  const [items, setItems] = useState<Transition[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // filters
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [status, setStatus] = useState<StatusFilter>("any");

  // pagination
  const [limit, setLimit] = useState<number>(50);
  const [offset, setOffset] = useState<number>(0);

  // inline weight editor values
  const [weights, setWeights] = useState<Record<string, string>>({});

  // creation form
  const [cFrom, setCFrom] = useState("");
  const [cTo, setCTo] = useState("");
  const [cLabel, setCLabel] = useState("");
  const [cWeight, setCWeight] = useState<string>("");

  // selection for bulk actions
  const [selected, setSelected] = useState<Record<string, boolean>>({});

  const ids = useMemo(() => items.map((it) => String(it.id)), [items]);
  const selectedIds = useMemo(
    () => ids.filter((id) => selected[id]),
    [ids, selected],
  );
  const allSelected = ids.length > 0 && selectedIds.length === ids.length;

  const setWeightValue = (id: string, v: string) =>
    setWeights((m) => ({ ...m, [id]: v }));
  const toggleSelectAll = () => {
    if (allSelected) {
      setSelected({});
    } else {
      const m: Record<string, boolean> = {};
      for (const id of ids) m[id] = true;
      setSelected(m);
    }
  };
  const toggleOne = (id: string) =>
    setSelected((m) => ({ ...m, [id]: !m[id] }));

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const rows = await listTransitions({
        from_slug: from || undefined,
        to_slug: to || undefined,
        limit,
        offset,
        status,
      });
      const data = ensureArray<Transition>(rows);
      setItems(data);
      // заполним локальные веса
      const w: Record<string, string> = {};
      for (const t of data) {
        const id = String(t.id);
        w[id] = String(t.weight ?? t.priority ?? "");
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
  }, [limit, offset, status]);

  const handleSearch = async () => {
    setOffset(0);
    await load();
  };

  const toggleDisabled = async (id: string, current: boolean) => {
    await updateTransition(id, { disabled: !current });
    await load();
  };

  const saveWeight = async (id: string) => {
    const v = weights[id];
    const num = Number(v);
    if (isNaN(num)) return;
    await updateTransition(id, { weight: num, priority: num });
    await load();
  };

  const doDelete = async (id: string) => {
    const ok = window.confirm("Delete this transition? This cannot be undone.");
    if (!ok) return;
    await apiDeleteTransition(id);
    await load();
  };

  const hasPrev = offset > 0;
  const hasNext = items.length >= limit;

  const bulkEnable = async () => {
    if (selectedIds.length === 0) return;
    for (const id of selectedIds)
      await updateTransition(id, { disabled: false });
    await load();
  };

  const bulkDisable = async () => {
    if (selectedIds.length === 0) return;
    for (const id of selectedIds)
      await updateTransition(id, { disabled: true });
    await load();
  };

  const bulkDelete = async () => {
    if (selectedIds.length === 0) return;
    const ok = window.confirm(`Delete ${selectedIds.length} transition(s)?`);
    if (!ok) return;
    for (const id of selectedIds) await apiDeleteTransition(id);
    await load();
  };

  const create = async () => {
    const body = {
      from_slug: cFrom.trim(),
      to_slug: cTo.trim(),
      label: cLabel.trim() || undefined,
      weight: cWeight.trim() ? Number(cWeight.trim()) : undefined,
      priority: cWeight.trim() ? Number(cWeight.trim()) : undefined,
      disabled: false,
    };
    if (!body.from_slug || !body.to_slug) return;
    await createTransition(body);
    setCFrom("");
    setCTo("");
    setCLabel("");
    setCWeight("");
    setOffset(0);
    await load();
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Transitions</h1>

      <div className="mb-4 flex flex-wrap items-center gap-2">
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
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value as StatusFilter)}
          className="border rounded px-2 py-1"
        >
          <option value="any">any</option>
          <option value="enabled">enabled</option>
          <option value="disabled">disabled</option>
        </select>
        <button onClick={handleSearch} className="px-3 py-1 rounded border">
          Search
        </button>

        <div className="ml-auto flex items-center gap-2">
          <label className="text-sm text-gray-600">Page size</label>
          <input
            type="number"
            min={1}
            max={1000}
            value={limit}
            onChange={(e) =>
              setLimit(Math.max(1, Math.min(1000, Number(e.target.value) || 1)))
            }
            className="w-20 border rounded px-2 py-1"
          />
          <button
            className="px-2 py-1 rounded border"
            disabled={!hasPrev}
            onClick={() => setOffset(Math.max(0, offset - limit))}
            title="Previous page"
          >
            ‹ Prev
          </button>
          <button
            className="px-2 py-1 rounded border"
            disabled={!hasNext}
            onClick={() => setOffset(offset + limit)}
            title="Next page"
          >
            Next ›
          </button>
        </div>
      </div>

      <div className="mb-6 rounded border p-3">
        <h2 className="font-semibold mb-2">Create transition</h2>
        <div className="flex flex-wrap items-center gap-2">
          <input
            className="border rounded px-2 py-1"
            placeholder="from slug"
            value={cFrom}
            onChange={(e) => setCFrom(e.target.value)}
          />
          <input
            className="border rounded px-2 py-1"
            placeholder="to slug"
            value={cTo}
            onChange={(e) => setCTo(e.target.value)}
          />
          <input
            className="border rounded px-2 py-1 w-48"
            placeholder="label (optional)"
            value={cLabel}
            onChange={(e) => setCLabel(e.target.value)}
          />
          <input
            className="border rounded px-2 py-1 w-24"
            placeholder="weight"
            value={cWeight}
            onChange={(e) => setCWeight(e.target.value)}
          />
          <button
            className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-800"
            onClick={create}
          >
            Create
          </button>
        </div>
      </div>

      {loading && <p>Loading...</p>}
      {error && <p className="text-red-600">{error}</p>}

      {!loading && !error && (
        <>
          <div className="mb-2 flex items-center gap-2">
            <input
              type="checkbox"
              checked={allSelected}
              onChange={toggleSelectAll}
            />
            <span className="text-sm text-gray-600">Select all</span>
            <div className="ml-auto flex items-center gap-2">
              <button
                className="px-2 py-1 rounded border"
                disabled={selectedIds.length === 0}
                onClick={bulkEnable}
              >
                Enable
              </button>
              <button
                className="px-2 py-1 rounded border"
                disabled={selectedIds.length === 0}
                onClick={bulkDisable}
              >
                Disable
              </button>
              <button
                className="px-2 py-1 rounded border text-red-600 border-red-300"
                disabled={selectedIds.length === 0}
                onClick={bulkDelete}
              >
                Delete
              </button>
            </div>
          </div>

          <table className="min-w-full text-sm text-left">
            <thead>
              <tr className="border-b">
                <th className="p-2" />
                <th className="p-2">ID</th>
                <th className="p-2">From</th>
                <th className="p-2">To</th>
                <th className="p-2">Label</th>
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
                  <tr
                    key={id}
                    className="border-b hover:bg-gray-50 dark:hover:bg-gray-800"
                  >
                    <td className="p-2 align-middle">
                      <input
                        type="checkbox"
                        checked={!!selected[id]}
                        onChange={() => toggleOne(id)}
                      />
                    </td>
                    <td className="p-2 font-mono">{t.id ?? "-"}</td>
                    <td className="p-2">{t.from_slug ?? "-"}</td>
                    <td className="p-2">{t.to_slug ?? "-"}</td>
                    <td className="p-2">{t.label ?? "—"}</td>
                    <td className="p-2">
                      <div className="flex items-center gap-2">
                        <input
                          className="border rounded px-2 py-1 w-24"
                          value={weights[id] ?? ""}
                          onChange={(e) => setWeightValue(id, e.target.value)}
                        />
                        <button
                          onClick={() => saveWeight(id)}
                          className="px-2 py-1 rounded border"
                        >
                          Save
                        </button>
                      </div>
                    </td>
                    <td className="p-2">{String(disabled)}</td>
                    <td className="p-2">
                      {t.updated_at
                        ? new Date(t.updated_at).toLocaleString()
                        : "-"}
                    </td>
                    <td className="p-2 space-x-2">
                      <button
                        onClick={() => toggleDisabled(id, disabled)}
                        className="text-blue-600"
                      >
                        {disabled ? "Enable" : "Disable"}
                      </button>
                      <button
                        onClick={() => doDelete(id)}
                        className="text-red-600"
                      >
                        Del
                      </button>
                    </td>
                  </tr>
                );
              })}
              {ids.length === 0 && (
                <tr>
                  <td colSpan={9} className="p-4 text-center text-gray-500">
                    No transitions found
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </>
      )}
    </div>
  );
}
