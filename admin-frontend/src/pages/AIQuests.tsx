import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useNavigate } from "react-router-dom";
import { createDraft } from "../api/questEditor";

type WorldTemplate = { id: string; title: string; locale?: string | null; description?: string | null };
type Character = { id: string; world_id: string; name: string; role?: string | null; description?: string | null };
type Job = {
  id: string;
  status: string;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  created_by?: string | null;
  provider?: string | null;
  model?: string | null;
  params: any;
  result_quest_id?: string | null;
  result_version_id?: string | null;
  cost?: number | null;
  token_usage?: any;
  reused?: boolean;
  progress?: number;
  logs?: string[] | null;
  error?: string | null;
};
type AISettings = { provider?: string | null; base_url?: string | null; model?: string | null; has_api_key: boolean };

export default function AIQuests() {
  const nav = useNavigate();
  const [templates, setTemplates] = useState<WorldTemplate[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reuse, setReuse] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [reusedOnly, setReusedOnly] = useState<boolean>(false);

  // form fields
  const [worldId, setWorldId] = useState<string>("");
  const [structure, setStructure] = useState<"linear"|"vn_branching"|"epic">("vn_branching");
  const [length, setLength] = useState<"short"|"long">("short");
  const [tone, setTone] = useState<"light"|"dark"|"ironic">("light");
  const [genre, setGenre] = useState<string>("fantasy");
  const [locale, setLocale] = useState<string>("");

  // management state
  const [mgmtOpen, setMgmtOpen] = useState<boolean>(false);
  const [worlds, setWorlds] = useState<WorldTemplate[]>([]);
  const [newWorld, setNewWorld] = useState<{ title: string; locale: string; description: string }>({ title: "", locale: "", description: "" });
  const [selectedWorld, setSelectedWorld] = useState<string>("");
  const [characters, setCharacters] = useState<Character[]>([]);
  const [newChar, setNewChar] = useState<{ name: string; role: string; description: string }>({ name: "", role: "", description: "" });
  const [aiSettings, setAISettings] = useState<AISettings>({ has_api_key: false });
  const [aiSecret, setAISecret] = useState<string>("");

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [t, j] = await Promise.all([
        api.get<WorldTemplate[]>("/admin/ai/quests/templates"),
        api.get<Job[]>("/admin/ai/quests/jobs"),
      ]);
      setTemplates(Array.isArray(t.data) ? (t.data as any) : []);
      setJobs(Array.isArray(j.data) ? (j.data as any) : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setTemplates([]); setJobs([]);
    } finally {
      setLoading(false);
    }
  };

  const loadWorlds = async () => {
    try {
      const res = await api.get<WorldTemplate[]>("/admin/ai/quests/worlds");
      setWorlds(Array.isArray(res.data) ? res.data : []);
    } catch (e) {
      console.error(e);
    }
  };

  const loadCharacters = async (wid: string) => {
    if (!wid) { setCharacters([]); return; }
    try {
      const res = await api.get<Character[]>(`/admin/ai/quests/worlds/${encodeURIComponent(wid)}/characters`);
      setCharacters(Array.isArray(res.data) ? res.data : []);
    } catch (e) {
      console.error(e);
    }
  };

  const loadAISettings = async () => {
    try {
      const res = await api.get<AISettings>("/admin/ai/quests/settings");
      setAISettings(res.data ?? { has_api_key: false });
      setAISecret("");
    } catch (e) {
      console.error(e);
    }
  };

  // начальная загрузка
  useEffect(() => { load(); }, []);

  // авто‑обновление каждые 5 секунд
  useEffect(() => {
    const id = setInterval(() => { load().catch(() => void 0); }, 5000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    if (mgmtOpen) {
      loadWorlds().catch(() => void 0);
      loadAISettings().catch(() => void 0);
    }
  }, [mgmtOpen]);

  useEffect(() => {
    loadCharacters(selectedWorld).catch(() => void 0);
  }, [selectedWorld]);

  const submit = async () => {
    try {
      const qs = reuse ? "?reuse=true" : "?reuse=false";
      await api.post(`/admin/ai/quests/generate${qs}`, {
        world_template_id: worldId || null,
        structure,
        length,
        tone,
        genre,
        locale: locale || null,
        extras: {},
      });
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  const simulate = async (jobId: string) => {
    try {
      await api.post(`/admin/ai/quests/jobs/${encodeURIComponent(jobId)}/simulate_complete`);
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  const tick = async (jobId: string, delta = 10) => {
    try {
      await api.post(`/admin/ai/quests/jobs/${encodeURIComponent(jobId)}/tick`, { delta });
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  const createWorld = async () => {
    if (!newWorld.title.trim()) return alert("Введите название мира");
    try {
      await api.post("/admin/ai/quests/worlds", {
        title: newWorld.title,
        locale: newWorld.locale || null,
        description: newWorld.description || null,
        meta: null,
      });
      setNewWorld({ title: "", locale: "", description: "" });
      await Promise.all([loadWorlds(), load()]);
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  const removeWorld = async (id: string) => {
    if (!confirm("Удалить мир со всеми персонажами?")) return;
    try {
      await api.request(`/admin/ai/quests/worlds/${encodeURIComponent(id)}`, { method: "DELETE" });
      if (id === selectedWorld) { setSelectedWorld(""); setCharacters([]); }
      await Promise.all([loadWorlds(), load()]);
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  const addCharacter = async () => {
    if (!selectedWorld) return alert("Выберите мир");
    if (!newChar.name.trim()) return alert("Имя персонажа обязательно");
    try {
      await api.post(`/admin/ai/quests/worlds/${encodeURIComponent(selectedWorld)}/characters`, {
        name: newChar.name,
        role: newChar.role || null,
        description: newChar.description || null,
        traits: null,
      });
      setNewChar({ name: "", role: "", description: "" });
      await loadCharacters(selectedWorld);
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  const removeCharacter = async (id: string) => {
    if (!confirm("Удалить персонажа?")) return;
    try {
      await api.request(`/admin/ai/quests/characters/${encodeURIComponent(id)}`, { method: "DELETE" });
      await loadCharacters(selectedWorld);
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  const saveAI = async () => {
    try {
      await api.put("/admin/ai/quests/settings", {
        provider: aiSettings.provider ?? null,
        base_url: aiSettings.base_url ?? null,
        model: aiSettings.model ?? null,
        api_key: aiSecret === "" ? null : aiSecret, // null — не менять; строка — сохранить/очистить, если ""
      });
      await loadAISettings();
      alert("Настройки сохранены");
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  const statusBadge = (s: string, reused?: boolean) => {
    const map: Record<string, string> = {
      queued: "bg-gray-200 text-gray-800",
      running: "bg-blue-200 text-blue-800",
      completed: "bg-green-200 text-green-800",
      failed: "bg-red-200 text-red-800",
      canceled: "bg-yellow-200 text-yellow-800",
    };
    return (
      <span className="inline-flex items-center gap-2">
        <span className={`px-2 py-0.5 rounded text-xs ${map[s] || "bg-gray-200"}`}>{s}</span>
        {reused ? <span className="px-2 py-0.5 rounded text-xs bg-purple-200 text-purple-800">cache</span> : null}
      </span>
    );
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">AI Quests</h1>

      <div className="rounded border p-3 mb-6">
        <h2 className="font-semibold mb-2">Создать ИИ‑квест</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          <div className="flex items-center gap-2">
            <label className="w-32 text-sm text-gray-600">Мир</label>
            <select className="border rounded px-2 py-1 flex-1" value={worldId} onChange={(e) => setWorldId(e.target.value)}>
              <option value="">— не выбрано —</option>
              {templates.map((t: any) => (<option key={t.id} value={t.id}>{t.title}{t.locale ? ` · ${t.locale}` : ""}</option>))}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="w-32 text-sm text-gray-600">Структура</label>
            <select className="border rounded px-2 py-1 flex-1" value={structure} onChange={(e) => setStructure(e.target.value as any)}>
              <option value="linear">linear</option>
              <option value="vn_branching">vn_branching</option>
              <option value="epic">epic</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="w-32 text-sm text-gray-600">Длина</label>
            <select className="border rounded px-2 py-1 flex-1" value={length} onChange={(e) => setLength(e.target.value as any)}>
              <option value="short">short (10–15)</option>
              <option value="long">long (40–100)</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="w-32 text-sm text-gray-600">Тональность</label>
            <select className="border rounded px-2 py-1 flex-1" value={tone} onChange={(e) => setTone(e.target.value as any)}>
              <option value="light">light</option>
              <option value="dark">dark</option>
              <option value="ironic">ironic</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="w-32 text-sm text-gray-600">Жанр</label>
            <input className="border rounded px-2 py-1 flex-1" placeholder="fantasy, sci-fi…" value={genre} onChange={(e) => setGenre(e.target.value)} />
          </div>
          <div className="flex items-center gap-2">
            <label className="w-32 text-sm text-gray-600">Локаль</label>
            <input className="border rounded px-2 py-1 flex-1" placeholder="ru-RU / en-US" value={locale} onChange={(e) => setLocale(e.target.value)} />
          </div>
        </div>
        <div className="mt-3 flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={reuse} onChange={(e) => setReuse(e.target.checked)} />
            Reuse result (cache)
          </label>
          <button className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-800" onClick={submit}>Сгенерировать</button>
        </div>
      </div>

      <div className="mb-6">
        <button className="px-3 py-1 rounded border" onClick={() => setMgmtOpen((v) => !v)}>
          {mgmtOpen ? "Скрыть управление" : "Показать управление (Миры/Персонажи/AI Settings)"}
        </button>
      </div>

      {mgmtOpen && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-8">
          <div className="rounded border p-3">
            <h3 className="font-semibold mb-2">Миры</h3>
            <div className="flex flex-col gap-2 mb-3">
              <input className="border rounded px-2 py-1" placeholder="Название" value={newWorld.title} onChange={(e) => setNewWorld((s) => ({ ...s, title: e.target.value }))} />
              <input className="border rounded px-2 py-1" placeholder="Локаль (ru-RU / en-US)" value={newWorld.locale} onChange={(e) => setNewWorld((s) => ({ ...s, locale: e.target.value }))} />
              <textarea className="border rounded px-2 py-1" placeholder="Описание" value={newWorld.description} onChange={(e) => setNewWorld((s) => ({ ...s, description: e.target.value }))} />
              <button className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-800" onClick={createWorld}>Добавить мир</button>
            </div>
            <div className="max-h-80 overflow-auto divide-y">
              {worlds.map((w) => (
                <div key={w.id} className="py-2 flex items-center justify-between gap-2">
                  <button className={`text-left flex-1 ${selectedWorld === w.id ? "font-semibold" : ""}`} onClick={() => setSelectedWorld(w.id)}>
                    {w.title}{w.locale ? ` · ${w.locale}` : ""}
                  </button>
                  <button className="px-2 py-1 rounded border" onClick={() => removeWorld(w.id)}>Удалить</button>
                </div>
              ))}
              {worlds.length === 0 && <div className="text-sm text-gray-500">Пока нет миров</div>}
            </div>
          </div>

          <div className="rounded border p-3">
            <h3 className="font-semibold mb-2">Персонажи {selectedWorld ? "" : "(выберите мир)"}</h3>
            {selectedWorld && (
              <>
                <div className="flex flex-col gap-2 mb-3">
                  <input className="border rounded px-2 py-1" placeholder="Имя" value={newChar.name} onChange={(e) => setNewChar((s) => ({ ...s, name: e.target.value }))} />
                  <input className="border rounded px-2 py-1" placeholder="Роль" value={newChar.role} onChange={(e) => setNewChar((s) => ({ ...s, role: e.target.value }))} />
                  <textarea className="border rounded px-2 py-1" placeholder="Описание" value={newChar.description} onChange={(e) => setNewChar((s) => ({ ...s, description: e.target.value }))} />
                  <button className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-800" onClick={addCharacter}>Добавить персонажа</button>
                </div>
                <div className="max-h-80 overflow-auto divide-y">
                  {characters.map((c) => (
                    <div key={c.id} className="py-2 flex items-center justify-between gap-2">
                      <div className="flex-1">
                        <div className="font-medium">{c.name}{c.role ? ` · ${c.role}` : ""}</div>
                        {c.description && <div className="text-xs text-gray-600">{c.description}</div>}
                      </div>
                      <button className="px-2 py-1 rounded border" onClick={() => removeCharacter(c.id)}>Удалить</button>
                    </div>
                  ))}
                  {characters.length === 0 && <div className="text-sm text-gray-500">Пока нет персонажей</div>}
                </div>
              </>
            )}
          </div>

          <div className="rounded border p-3">
            <h3 className="font-semibold mb-2">AI Settings</h3>
            <div className="flex flex-col gap-2">
              <input className="border rounded px-2 py-1" placeholder="Provider (например: openai, anthropic…)" value={aiSettings.provider ?? ""} onChange={(e) => setAISettings((s) => ({ ...s, provider: e.target.value }))} />
              <input className="border rounded px-2 py-1" placeholder="Base URL (необязательно)" value={aiSettings.base_url ?? ""} onChange={(e) => setAISettings((s) => ({ ...s, base_url: e.target.value }))} />
              <input className="border rounded px-2 py-1" placeholder="Model (например: gpt-4o-mini)" value={aiSettings.model ?? ""} onChange={(e) => setAISettings((s) => ({ ...s, model: e.target.value }))} />
              <input className="border rounded px-2 py-1" placeholder={aiSettings.has_api_key ? "API Key (оставьте пустым — не менять)" : "API Key"} type="password" value={aiSecret} onChange={(e) => setAISecret(e.target.value)} />
              <div className="text-xs text-gray-600">{aiSettings.has_api_key ? "Ключ сохранён" : "Ключ не задан"}</div>
              <button className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-800" onClick={saveAI}>Сохранить</button>
            </div>
          </div>
        </div>
      )}

      {loading && <div className="text-sm text-gray-500">Loading…</div>}
      {error && <div className="text-sm text-red-600">{error}</div>}

      {!loading && !error && (
        <>
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <label className="text-sm text-gray-600">Status</label>
            <select className="border rounded px-2 py-1" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
              <option value="all">all</option>
              <option value="queued">queued</option>
              <option value="running">running</option>
              <option value="completed">completed</option>
              <option value="failed">failed</option>
              <option value="canceled">canceled</option>
            </select>
            <label className="text-sm flex items-center gap-2">
              <input type="checkbox" checked={reusedOnly} onChange={(e) => setReusedOnly(e.target.checked)} />
              reused only
            </label>
          </div>
          <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="p-2 text-left">ID</th>
                <th className="p-2 text-left">Status</th>
                <th className="p-2 text-left">Progress</th>
                <th className="p-2 text-left">Created</th>
                <th className="p-2 text-left">Params</th>
                <th className="p-2 text-left">Result</th>
                <th className="p-2 text-left">Cost</th>
                <th className="p-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {jobs
                .filter((j: any) => statusFilter === "all" ? true : j.status === statusFilter)
                .filter((j: any) => !reusedOnly || j.reused)
                .map((j) => (
                <tr key={j.id} className="border-b">
                  <td className="p-2 font-mono">{j.id}</td>
                  <td className="p-2">{statusBadge(j.status, (j as any).reused)}</td>
                  <td className="p-2">
                    <div className="w-40 bg-gray-200 dark:bg-gray-800 rounded h-3 overflow-hidden">
                      <div
                        className="bg-blue-600 h-3"
                        style={{ width: `${Math.max(0, Math.min(100, j.progress ?? 0))}%` }}
                        aria-label={`progress ${j.progress ?? 0}%`}
                      />
                    </div>
                    <div className="text-xs text-gray-600 mt-1">{j.progress ?? 0}%</div>
                  </td>
                  <td className="p-2">{new Date(j.created_at).toLocaleString()}</td>
                  <td className="p-2">{j.params ? `${j.params.structure}/${j.params.length}/${j.params.tone}/${j.params.genre}${j.params.locale ? " · " + j.params.locale : ""}` : "-"}</td>
                  <td className="p-2">{j.result_quest_id ? `quest:${j.result_quest_id}` : "-"}</td>
                  <td className="p-2">{j.cost != null ? j.cost.toFixed(4) : "-"}</td>
                  <td className="p-2 text-right space-x-2">
                    {(j.status === "queued" || j.status === "running") && (
                      <>
                        <button className="px-2 py-1 rounded border" onClick={() => tick(j.id, 10)}>Tick +10%</button>
                        <button className="px-2 py-1 rounded border" onClick={() => simulate(j.id)}>Simulate</button>
                      </>
                    )}
                    {j.result_quest_id && (
                      <button
                        className="px-2 py-1 rounded border"
                        onClick={async () => {
                          try {
                            const ver = await createDraft(j.result_quest_id as string);
                            nav(`/quests/version/${ver}`);
                          } catch (e) {
                            alert(e instanceof Error ? e.message : String(e));
                          }
                        }}
                      >
                        New draft
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {jobs.length === 0 && (
                <tr><td colSpan={7} className="p-4 text-center text-gray-500">No jobs</td></tr>
              )}
            </tbody>
          </table>
        </div>
        </>
      )}
    </div>
  );
}
