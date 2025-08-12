import { useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import { useToast } from "../components/ToastProvider";
import { Link } from "react-router-dom";

interface QuestItem {
  id: string;
  title: string;
  subtitle?: string | null;
  description?: string | null;
  cover_image?: string | null;
  tags?: string[] | null;
  price?: number | null;
  is_premium_only?: boolean;
  allow_comments?: boolean;
  is_draft?: boolean;
  is_deleted?: boolean;
  author_id: string;
  created_at: string;
  published_at?: string | null;
}

function ensureArray<T = any>(data: unknown): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === "object") {
    const obj = data as any;
    if (Array.isArray(obj.items)) return obj.items as T[];
    if (Array.isArray(obj.data)) return obj.data as T[];
  }
  return [];
}

async function fetchQuests(params: Record<string, string>): Promise<QuestItem[]> {
  const qs = new URLSearchParams(params).toString();
  // админский эндпоинт с фильтрами по роли автора/черновикам
  const res = await api.get(`/admin/quests?${qs}`);
  return ensureArray<QuestItem>(res.data);
}

async function createQuest(payload: any): Promise<QuestItem> {
  const res = await api.post("/quests", payload);
  return res.data as QuestItem;
}

async function publishQuest(id: string): Promise<QuestItem> {
  const res = await api.post(`/quests/${id}/publish`, {});
  return res.data as QuestItem;
}

export default function Quests() {
  const { addToast } = useToast();
  const qc = useQueryClient();
  const [q, setQ] = useState("");
  const [authorRole, setAuthorRole] = useState<string>(""); // any|admin|moderator|user
  const [draftOnly, setDraftOnly] = useState<boolean>(true);

  const queryParams = useMemo(() => {
    const p: Record<string, string> = {};
    if (q) p.q = q;
    if (authorRole) p.author_role = authorRole;
    if (draftOnly) p.draft = "true";
    return p;
  }, [q, authorRole, draftOnly]);

  const { data, isLoading, error } = useQuery({
    queryKey: ["quests-admin", queryParams],
    queryFn: () => fetchQuests(queryParams),
  });

  // Модалка создания
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [subtitle, setSubtitle] = useState("");
  const [description, setDescription] = useState("");
  const [tags, setTags] = useState("");
  const [price, setPrice] = useState<string>("");
  const [premiumOnly, setPremiumOnly] = useState(false);
  const [allowComments, setAllowComments] = useState(true);
  const [entryNode, setEntryNode] = useState("");
  const [nodes, setNodes] = useState("");
  const [customTransitions, setCustomTransitions] = useState("");

  const resetForm = () => {
    setTitle(""); setSubtitle(""); setDescription(""); setTags(""); setPrice("");
    setPremiumOnly(false); setAllowComments(true); setEntryNode(""); setNodes(""); setCustomTransitions("");
  };

  const handleCreate = async () => {
    try {
      const payload: any = {
        title,
        subtitle: subtitle || null,
        description: description || null,
        tags: tags ? tags.split(",").map(s => s.trim()).filter(Boolean) : [],
        price: price ? Number(price) : null,
        is_premium_only: premiumOnly,
        allow_comments: allowComments,
        entry_node_id: entryNode || null,
        nodes: nodes ? nodes.split(",").map(s => s.trim()) : [],
      };
      if (customTransitions) {
        try {
          payload.custom_transitions = JSON.parse(customTransitions);
        } catch {
          addToast({ title: "Invalid custom_transitions JSON", variant: "error" });
          return;
        }
      }
      const quest = await createQuest(payload);
      addToast({ title: "Quest created", description: quest.title, variant: "success" });
      setOpen(false);
      resetForm();
      qc.invalidateQueries({ queryKey: ["quests-admin"] });
    } catch (e) {
      addToast({ title: "Failed to create quest", description: e instanceof Error ? e.message : String(e), variant: "error" });
    }
  };

  const handlePublish = async (id: string) => {
    try {
      const q = await publishQuest(id);
      addToast({ title: "Quest published", description: q.title, variant: "success" });
      qc.invalidateQueries({ queryKey: ["quests-admin"] });
    } catch (e) {
      addToast({ title: "Failed to publish quest", description: e instanceof Error ? e.message : String(e), variant: "error" });
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Quests</h1>

      <div className="mb-4 flex items-end gap-2">
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search..." className="border rounded px-2 py-1" />
        <label className="flex items-center gap-2 text-sm">
          <span>Author role</span>
          <select value={authorRole} onChange={(e) => setAuthorRole(e.target.value)} className="border rounded px-2 py-1">
            <option value="">any</option>
            <option value="admin">admin</option>
            <option value="moderator">moderator</option>
            <option value="user">user</option>
          </select>
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={draftOnly} onChange={(e) => setDraftOnly(e.target.checked)} />
          <span>Drafts only</span>
        </label>
        <button className="px-3 py-1 rounded bg-blue-600 text-white" onClick={() => setOpen(true)}>Create quest</button>
        <Link className="px-3 py-1 rounded border" to="/quests/editor">Open visual editor</Link>
      </div>

      {isLoading && <p>Loading…</p>}
      {error && <p className="text-red-600">{(error as Error).message}</p>}
      {!isLoading && !error && (
        <table className="min-w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="p-2 text-left">Title</th>
              <th className="p-2 text-left">Author</th>
              <th className="p-2 text-left">Price</th>
              <th className="p-2 text-left">Premium</th>
              <th className="p-2 text-left">Draft</th>
              <th className="p-2 text-left">Created</th>
              <th className="p-2 text-left">Published</th>
              <th className="p-2 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            {(data || []).map((q) => (
              <tr key={q.id} className="border-b">
                <td className="p-2">{q.title}</td>
                <td className="p-2 font-mono">{q.author_id}</td>
                <td className="p-2">{q.price ?? 0}</td>
                <td className="p-2">{q.is_premium_only ? "yes" : "no"}</td>
                <td className="p-2">{q.is_draft ? "yes" : "no"}</td>
                <td className="p-2">{new Date(q.created_at).toLocaleString()}</td>
                <td className="p-2">{q.published_at ? new Date(q.published_at).toLocaleString() : "-"}</td>
                <td className="p-2 space-x-2">
                  {q.is_draft && <button className="px-2 py-1 rounded border" onClick={() => handlePublish(q.id)}>Publish</button>}
                </td>
              </tr>
            ))}
            {(!data || data.length === 0) && <tr><td className="p-2 text-gray-500" colSpan={8}>No quests</td></tr>}
          </tbody>
        </table>
      )}

      {open && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-900 p-4 rounded shadow max-w-2xl w-full">
            <h2 className="text-lg font-bold mb-2">Create quest</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div className="flex flex-col">
                <label className="text-sm text-gray-600">Title</label>
                <input className="border rounded px-2 py-1" value={title} onChange={(e) => setTitle(e.target.value)} />
              </div>
              <div className="flex flex-col">
                <label className="text-sm text-gray-600">Subtitle</label>
                <input className="border rounded px-2 py-1" value={subtitle} onChange={(e) => setSubtitle(e.target.value)} />
              </div>
              <div className="md:col-span-2 flex flex-col">
                <label className="text-sm text-gray-600">Description</label>
                <textarea className="border rounded px-2 py-1" rows={3} value={description} onChange={(e) => setDescription(e.target.value)} />
              </div>
              <div className="flex flex-col">
                <label className="text-sm text-gray-600">Tags (comma)</label>
                <input className="border rounded px-2 py-1" value={tags} onChange={(e) => setTags(e.target.value)} />
              </div>
              <div className="flex flex-col">
                <label className="text-sm text-gray-600">Price</label>
                <input className="border rounded px-2 py-1" value={price} onChange={(e) => setPrice(e.target.value)} placeholder="0, empty for free" />
              </div>
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={premiumOnly} onChange={(e) => setPremiumOnly(e.target.checked)} />
                <span>Premium only</span>
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" checked={allowComments} onChange={(e) => setAllowComments(e.target.checked)} />
                <span>Allow comments</span>
              </label>
              <div className="flex flex-col">
                <label className="text-sm text-gray-600">Entry node id</label>
                <input className="border rounded px-2 py-1" value={entryNode} onChange={(e) => setEntryNode(e.target.value)} placeholder="UUID or empty" />
              </div>
              <div className="md:col-span-2 flex flex-col">
                <label className="text-sm text-gray-600">Nodes (comma of UUIDs)</label>
                <input className="border rounded px-2 py-1" value={nodes} onChange={(e) => setNodes(e.target.value)} placeholder="id1,id2,..." />
              </div>
              <div className="md:col-span-2 flex flex-col">
                <label className="text-sm text-gray-600">Custom transitions (JSON)</label>
                <textarea className="border rounded px-2 py-1 font-mono text-xs" rows={4} value={customTransitions} onChange={(e) => setCustomTransitions(e.target.value)} placeholder='{"from_node_id":{"to_node_id":{...}}}' />
              </div>
            </div>
            <div className="mt-3 flex justify-end gap-2">
              <button className="px-3 py-1 rounded border" onClick={() => setOpen(false)}>Cancel</button>
              <button className="px-3 py-1 rounded bg-blue-600 text-white" onClick={handleCreate}>Create</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
