import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useToast } from "../components/ToastProvider";
import ConditionEditor, { type Condition } from "./_shared/ConditionEditor";

type AchievementAdmin = {
  id: string;
  code: string;
  title: string;
  description?: string | null;
  icon?: string | null;
  visible: boolean;
  condition: Record<string, any>;
};

function ensureArray<T = any>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === "object") {
    const obj = data as any;
    if (Array.isArray(obj.items)) return obj.items as T[];
    if (Array.isArray(obj.data)) return obj.data as T[];
  }
  return [];
}

// API helpers
async function listAdminAchievements(): Promise<AchievementAdmin[]> {
  const res = await api.get<AchievementAdmin[]>("/admin/achievements");
  return ensureArray<AchievementAdmin>(res.data);
}
async function createAdminAchievement(body: Partial<AchievementAdmin> & { code: string; title: string }): Promise<AchievementAdmin> {
  const res = await api.post<AchievementAdmin>("/admin/achievements", body);
  return res.data as any;
}
async function updateAdminAchievement(id: string, patch: Partial<AchievementAdmin>): Promise<AchievementAdmin> {
  const res = await api.patch<AchievementAdmin>(`/admin/achievements/${encodeURIComponent(id)}`, patch);
  return res.data as any;
}
async function deleteAdminAchievement(id: string): Promise<void> {
  await api.del(`/admin/achievements/${encodeURIComponent(id)}`);
}
async function grantAchievement(id: string, user_id: string) {
  await api.post(`/admin/achievements/${id}/grant`, { user_id });
}
async function revokeAchievement(id: string, user_id: string) {
  await api.post(`/admin/achievements/${id}/revoke`, { user_id });
}

export default function Achievements() {
  const { addToast } = useToast();
  const [items, setItems] = useState<AchievementAdmin[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Create form
  const [cCode, setCCode] = useState("");
  const [cTitle, setCTitle] = useState("");
  const [cDesc, setCDesc] = useState("");
  const [cIcon, setCIcon] = useState("");
  const [cVisible, setCVisible] = useState(true);
  const [cCond, setCCond] = useState<Condition>({ type: "event_count", event: "some_event", count: 1 });

  // Edit state
  const [editId, setEditId] = useState<string | null>(null);
  const [editConditions, setEditConditions] = useState<Record<string, Condition>>({});

  // Grant/Revoke
  const [userId, setUserId] = useState("");

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const rows = await listAdminAchievements();
      setItems(rows);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setItems([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const onCreate = async () => {
    if (!cCode.trim() || !cTitle.trim()) return;
    try {
      const created = await createAdminAchievement({
        code: cCode.trim(),
        title: cTitle.trim(),
        description: cDesc.trim() || undefined,
        icon: cIcon.trim() || undefined,
        visible: cVisible,
        condition: cCond as any,
      });
      setCCode(""); setCTitle(""); setCDesc(""); setCIcon(""); setCVisible(true);
      setCCond({ type: "event_count", event: "some_event", count: 1 });
      setItems((arr) => [created, ...arr]);
      addToast({ title: "Achievement created", variant: "success" });
    } catch (e) {
      addToast({ title: "Create failed", description: e instanceof Error ? e.message : String(e), variant: "error" });
    }
  };

  const onSave = async (row: AchievementAdmin, patch: Partial<AchievementAdmin>) => {
    try {
      const updated = await updateAdminAchievement(row.id, patch);
      setItems((arr) => arr.map((x) => (x.id === row.id ? updated : x)));
      setEditId(null);
      addToast({ title: "Saved", variant: "success" });
    } catch (e) {
      addToast({ title: "Save failed", description: e instanceof Error ? e.message : String(e), variant: "error" });
    }
  };

  const onDelete = async (row: AchievementAdmin) => {
    if (!confirm(`Delete achievement "${row.title}"?`)) return;
    try {
      await deleteAdminAchievement(row.id);
      setItems((arr) => arr.filter((x) => x.id !== row.id));
      addToast({ title: "Deleted", variant: "success" });
    } catch (e) {
      addToast({ title: "Delete failed", description: e instanceof Error ? e.message : String(e), variant: "error" });
    }
  };

  const handleGrant = async (id: string) => {
    if (!userId) return;
    try {
      await grantAchievement(id, userId);
      addToast({ title: "Achievement granted", variant: "success" });
    } catch (e) {
      addToast({ title: "Failed to grant", description: e instanceof Error ? e.message : String(e), variant: "error" });
    }
  };

  const handleRevoke = async (id: string) => {
    if (!userId) return;
    try {
      await revokeAchievement(id, userId);
      addToast({ title: "Achievement revoked", variant: "success" });
    } catch (e) {
      addToast({ title: "Failed to revoke", description: e instanceof Error ? e.message : String(e), variant: "error" });
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Achievements</h1>

      <div className="mb-6 rounded border p-3">
        <h2 className="font-semibold mb-2">Create achievement</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          <input className="border rounded px-2 py-1" placeholder="code" value={cCode} onChange={(e) => setCCode(e.target.value)} />
          <input className="border rounded px-2 py-1" placeholder="title" value={cTitle} onChange={(e) => setCTitle(e.target.value)} />
          <input className="border rounded px-2 py-1 md:col-span-2" placeholder="description (optional)" value={cDesc} onChange={(e) => setCDesc(e.target.value)} />
          <input className="border rounded px-2 py-1" placeholder="icon (optional)" value={cIcon} onChange={(e) => setCIcon(e.target.value)} />
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={cVisible} onChange={(e) => setCVisible(e.target.checked)} />
            Visible
          </label>
          <div className="md:col-span-2">
            <ConditionEditor value={cCond} onChange={setCCond} />
          </div>
        </div>
        <div className="mt-2">
          <button className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-800" onClick={onCreate}>Create</button>
        </div>
      </div>

      <div className="mb-4 flex items-center gap-2">
        <input value={userId} onChange={(e) => setUserId(e.target.value)} placeholder="User ID (UUID) for grant/revoke" className="border rounded px-2 py-1 font-mono w-80" />
      </div>

      {loading && <p>Loading…</p>}
      {error && <p className="text-red-600">{error}</p>}

      {!loading && !error && (
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="p-2 text-left">Code</th>
              <th className="p-2 text-left">Title</th>
              <th className="p-2 text-left">Visible</th>
              <th className="p-2 text-left">Description</th>
              <th className="p-2 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((a) => {
              const isEdit = editId === a.id;
              const [eCode, eTitle, eDesc, eIcon, eVisible] = isEdit
                ? [a.code, a.title, a.description || "", a.icon || "", a.visible, JSON.stringify(a.condition ?? {}, null, 2)]
                : [a.code, a.title, a.description || "", a.icon || "", a.visible, ""];
              return (
                <tr key={a.id} className="border-b align-top">
                  <td className="p-2 font-mono">{isEdit
                    ? <input defaultValue={eCode} onBlur={(ev) => (a.code = ev.currentTarget.value)} className="border rounded px-2 py-1 w-40 font-mono" />
                    : a.code}</td>
                  <td className="p-2">{isEdit
                    ? <input defaultValue={eTitle} onBlur={(ev) => (a.title = ev.currentTarget.value)} className="border rounded px-2 py-1 w-56" />
                    : a.title}</td>
                  <td className="p-2">{isEdit
                    ? <input type="checkbox" defaultChecked={eVisible} onChange={(ev) => (a.visible = ev.currentTarget.checked)} />
                    : String(a.visible)}</td>
                  <td className="p-2">
                    {isEdit ? (
                      <div className="space-y-2">
                        <input defaultValue={eDesc} onBlur={(ev) => (a.description = ev.currentTarget.value)} className="border rounded px-2 py-1 w-full" />
                        <input defaultValue={eIcon} onBlur={(ev) => (a.icon = ev.currentTarget.value)} className="border rounded px-2 py-1 w-full" placeholder="icon" />
                        <ConditionEditor
                          value={editConditions[a.id] ?? (a.condition as any)}
                          onChange={(v) => setEditConditions((m) => ({ ...m, [a.id]: v }))}
                        />
                      </div>
                    ) : (a.description ?? "")}
                  </td>
                  <td className="p-2 space-x-2">
                    {!isEdit ? (
                      <>
                        <button className="px-2 py-1 rounded border" onClick={() => { setEditId(a.id); setEditConditions((m) => ({ ...m, [a.id]: (a.condition as any) || { type: "event_count", event: "some_event", count: 1 } })); }}>Edit</button>
                        <button className="px-2 py-1 rounded border text-red-600 border-red-300" onClick={() => onDelete(a)}>Delete</button>
                        <button className="px-2 py-1 rounded border" disabled={!userId} onClick={() => handleGrant(a.id)}>Grant</button>
                        <button className="px-2 py-1 rounded border" disabled={!userId} onClick={() => handleRevoke(a.id)}>Revoke</button>
                      </>
                    ) : (
                      <>
                        <button className="px-2 py-1 rounded border" onClick={async () => {
                          const patch: Partial<AchievementAdmin> = {
                            code: a.code,
                            title: a.title,
                            description: a.description || undefined,
                            icon: a.icon || undefined,
                            visible: a.visible,
                            condition: (editConditions[a.id] as any) ?? (a.condition || {}),
                          };
                          await onSave(a, patch);
                        }}>Save</button>
                        <button className="px-2 py-1 rounded border" onClick={() => setEditId(null)}>Cancel</button>
                      </>
                    )}
                  </td>
                </tr>
              );
            })}
            {items.length === 0 && (
              <tr>
                <td className="p-2 text-gray-500" colSpan={5}>No achievements</td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}

