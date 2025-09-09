import { useQuery, useQueryClient } from '@tanstack/react-query';
import { memo, useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { useAccount } from '../account/AccountContext';
import { api } from '../api/client';
import { createDraft } from '../api/questEditor';
import CursorPager from '../components/CursorPager';
import { confirmWithEnv } from '../utils/env';

type WorldTemplate = {
  id: string;
  title: string;
  locale?: string | null;
  description?: string | null;
};
type Character = {
  id: string;
  world_id: string;
  name: string;
  role?: string | null;
  description?: string | null;
};
type Job = {
  id: string;
  status: string;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  created_by?: string | null;
  provider?: string | null;
  model?: string | null;
  params?: JobParams | null;
  result_quest_id?: string | null;
  result_version_id?: string | null;
  cost?: number | null;
  token_usage?: unknown;
  reused?: boolean;
  progress?: number;
  logs?: string[] | null;
  error?: string | null;
};
type JobParams = {
  structure?: 'linear' | 'vn_branching' | 'epic';
  length?: 'short' | 'long';
  tone?: 'light' | 'dark' | 'ironic';
  genre?: string;
  locale?: string | null;
  [key: string]: unknown;
};
type AISettings = {
  provider?: string | null;
  base_url?: string | null;
  model?: string | null;
  has_api_key: boolean;
};

export default function AIQuests() {
  const nav = useNavigate();
  const [templates, setTemplates] = useState<WorldTemplate[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reuse, setReuse] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [reusedOnly, setReusedOnly] = useState<boolean>(false);

  // form fields
  const [worldId, setWorldId] = useState<string>('');
  const [structure, setStructure] = useState<'linear' | 'vn_branching' | 'epic'>('vn_branching');
  const [length, setLength] = useState<'short' | 'long'>('short');
  const [tone, setTone] = useState<'light' | 'dark' | 'ironic'>('light');
  const [genre, setGenre] = useState<string>('fantasy');
  const [locale, setLocale] = useState<string>('');
  const [model, setModel] = useState<string>('');
  const [remember, setRemember] = useState<boolean>(false);
  const [allowedModels, setAllowedModels] = useState<string[]>([]);

  // management state
  const [mgmtOpen, setMgmtOpen] = useState<boolean>(false);
  const [worlds, setWorlds] = useState<WorldTemplate[]>([]);
  const [newWorld, setNewWorld] = useState<{
    title: string;
    locale: string;
    description: string;
  }>({ title: '', locale: '', description: '' });
  const [selectedWorld, setSelectedWorld] = useState<string>('');
  const [characters, setCharacters] = useState<Character[]>([]);
  const [newChar, setNewChar] = useState<{
    name: string;
    role: string;
    description: string;
  }>({ name: '', role: '', description: '' });
  const [aiSettings, setAISettings] = useState<AISettings>({
    has_api_key: false,
  });
  const [aiSecret, setAISecret] = useState<string>('');

  const { accountId } = useAccount();

  // Источник истины — React Query
  const queryClient = useQueryClient();

  const {
    data: templatesData,
    isLoading: tLoading,
    isFetching: tFetching,
    error: tError,
  } = useQuery({
    queryKey: ['ai-quests', 'templates'],
    queryFn: async () => {
      const res = await api.get<WorldTemplate[]>('/admin/ai/quests/templates');
      return Array.isArray(res.data) ? res.data : [];
    },
    staleTime: 30_000,
    refetchOnWindowFocus: false,
    placeholderData: (prev) => prev,
  });

  // cursor‑пагинация для jobs
  const [jobsCursor, setJobsCursor] = useState<string | null>(null);
  const [jobsLoading, setJobsLoading] = useState<boolean>(false);
  const isUpdating = tFetching || jobsLoading;

  // Синхронизируем шаблоны через React Query
  useEffect(() => {
    setTemplates(templatesData ?? []);
  }, [templatesData]);

  const loadUserPref = async () => {
    try {
      const res = await api.get<{ model?: string }>('/admin/ai/user-pref');
      if (res.data?.model) setModel(res.data.model);
    } catch {
      /* ignore */
    }
  };

  type ModelRow = { code: string; active?: boolean | null };
  const loadAllowedModels = useCallback(async () => {
    // Global allowed models
    try {
      const res = await api.get<ModelRow[]>(`/admin/ai/system/models`);
      const rows: ModelRow[] = Array.isArray(res.data) ? res.data : [];
      const arr = rows.filter((m) => m?.active).map((m) => String(m.code));
      setAllowedModels(arr);
    } catch {
      /* ignore */
    }
  }, []);

  useEffect(() => {
    loadUserPref().catch(() => void 0);
  }, []);

  useEffect(() => {
    loadAllowedModels().catch(() => void 0);
  }, [accountId, loadAllowedModels]);

  useEffect(() => {
    if (!model && allowedModels.length) setModel(allowedModels[0]);
  }, [model, allowedModels]);

  // загрузка первой страницы jobs
  type JobsCursorResponse = { items?: Job[]; next_cursor?: string | null };
  const loadJobsFirst = useCallback(async () => {
    setJobsLoading(true);
    setError(null);
    try {
      const res = await api.get<JobsCursorResponse>('/admin/ai/quests/jobs_cursor?limit=50');
      const items = Array.isArray(res.data?.items) ? res.data.items! : [];
      setJobs(items);
      setJobsCursor(res.data?.next_cursor || null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Ошибка загрузки задач');
    } finally {
      setJobsLoading(false);
    }
  }, []);

  const loadJobsMore = useCallback(async () => {
    if (!jobsCursor) return;
    setJobsLoading(true);
    setError(null);
    try {
      const res = await api.get<JobsCursorResponse>(
        `/admin/ai/quests/jobs_cursor?limit=50&cursor=${encodeURIComponent(jobsCursor)}`,
      );
      const items = Array.isArray(res.data?.items) ? res.data.items! : [];
      setJobs((prev) => [...prev, ...items]);
      setJobsCursor(res.data?.next_cursor || null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Ошибка загрузки задач');
    } finally {
      setJobsLoading(false);
    }
  }, [jobsCursor]);

  // Показываем "большую" загрузку только на первичном фетче
  useEffect(() => {
    setLoading(Boolean(tLoading || jobsLoading));
  }, [tLoading, jobsLoading]);

  // начальная загрузка jobs
  useEffect(() => {
    loadJobsFirst();
  }, [loadJobsFirst]);

  // автообновление (простое): периодически обновлять первую страницу, если мы в фокусе и нет ручной догрузки
  useEffect(() => {
    const id = setInterval(() => {
      if (document.visibilityState === 'visible') {
        loadJobsFirst().catch(() => void 0);
      }
    }, 5000);
    return () => clearInterval(id);
  }, [loadJobsFirst]);

  // ошибки
  useEffect(() => {
    const msg = tError instanceof Error ? tError.message : null;
    setError(msg);
  }, [tError]);

  // Совместимость: load() теперь просто инвалидирует кэш и триггерит перезагрузку
  const load = useCallback(async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ['ai-quests', 'templates'] }),
      queryClient.invalidateQueries({ queryKey: ['ai-quests', 'jobs'] }),
    ]);
  }, [queryClient]);

  const loadWorlds = async () => {
    try {
      const res = await api.get<WorldTemplate[]>('/admin/ai/quests/worlds');
      setWorlds(Array.isArray(res.data) ? res.data : []);
    } catch (e) {
      console.error(e);
    }
  };

  const loadCharacters = async (wid: string) => {
    if (!wid) {
      setCharacters([]);
      return;
    }
    try {
      const res = await api.get<Character[]>(
        `/admin/ai/quests/worlds/${encodeURIComponent(wid)}/characters`,
      );
      setCharacters(Array.isArray(res.data) ? res.data : []);
    } catch (e) {
      console.error(e);
    }
  };

  const loadAISettings = async () => {
    try {
      const res = await api.get<AISettings>('/admin/ai/quests/settings');
      setAISettings(res.data ?? { has_api_key: false });
      setAISecret('');
    } catch (e) {
      console.error(e);
    }
  };

  // начальная загрузка
  useEffect(() => {
    void load();
  }, [load]);

  // авто‑обновление выполняется через React Query (refetchInterval)

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
      const qs = reuse ? '?reuse=true' : '?reuse=false';
      await api.post(`/admin/ai/quests/generate${qs}`, {
        world_template_id: worldId || null,
        structure,
        length,
        tone,
        genre,
        locale: locale || null,
        extras: {},
        model: model || null,
        remember,
        account_id: accountId || null,
      });
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  const simulate = useCallback(
    async (jobId: string) => {
      try {
        await api.post(`/admin/ai/quests/jobs/${encodeURIComponent(jobId)}/simulate_complete`);
        await load();
      } catch (e) {
        alert(e instanceof Error ? e.message : String(e));
      }
    },
    [load],
  );

  const tick = useCallback(
    async (jobId: string, delta = 10) => {
      try {
        await api.post(`/admin/ai/quests/jobs/${encodeURIComponent(jobId)}/tick`, { delta });
        await load();
      } catch (e) {
        alert(e instanceof Error ? e.message : String(e));
      }
    },
    [load],
  );

  const createNewDraft = useCallback(
    async (questId: string) => {
      try {
        const ver = await createDraft(questId);
        nav(`/quests/${questId}/versions/${ver}`);
      } catch (e) {
        alert(e instanceof Error ? e.message : String(e));
      }
    },
    [nav],
  );

  const createWorld = async () => {
    if (!newWorld.title.trim()) return alert('Введите название мира');
    try {
      await api.post('/admin/ai/quests/worlds', {
        title: newWorld.title,
        locale: newWorld.locale || null,
        description: newWorld.description || null,
        meta: null,
      });
      setNewWorld({ title: '', locale: '', description: '' });
      await Promise.all([loadWorlds(), load()]);
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  const removeWorld = async (id: string) => {
    if (!(await confirmWithEnv('Удалить мир со всеми персонажами?'))) return;
    try {
      await api.request(`/admin/ai/quests/worlds/${encodeURIComponent(id)}`, {
        method: 'DELETE',
      });
      if (id === selectedWorld) {
        setSelectedWorld('');
        setCharacters([]);
      }
      await Promise.all([loadWorlds(), load()]);
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  const addCharacter = async () => {
    if (!selectedWorld) return alert('Выберите мир');
    if (!newChar.name.trim()) return alert('Имя персонажа обязательно');
    try {
      await api.post(`/admin/ai/quests/worlds/${encodeURIComponent(selectedWorld)}/characters`, {
        name: newChar.name,
        role: newChar.role || null,
        description: newChar.description || null,
        traits: null,
      });
      setNewChar({ name: '', role: '', description: '' });
      await loadCharacters(selectedWorld);
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  const removeCharacter = async (id: string) => {
    if (!(await confirmWithEnv('Удалить персонажа?'))) return;
    try {
      await api.request(`/admin/ai/quests/characters/${encodeURIComponent(id)}`, {
        method: 'DELETE',
      });
      await loadCharacters(selectedWorld);
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  const saveAI = async () => {
    try {
      await api.put('/admin/ai/quests/settings', {
        provider: aiSettings.provider ?? null,
        base_url: aiSettings.base_url ?? null,
        model: aiSettings.model ?? null,
        api_key: aiSecret === '' ? null : aiSecret, // null — не менять; строка — сохранить/очистить, если ""
      });
      await loadAISettings();
      alert('Настройки сохранены');
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  const statusBadge = (s: string, reused?: boolean) => {
    const map: Record<string, string> = {
      queued: 'bg-gray-200 text-gray-800',
      running: 'bg-blue-200 text-blue-800',
      completed: 'bg-green-200 text-green-800',
      failed: 'bg-red-200 text-red-800',
      canceled: 'bg-yellow-200 text-yellow-800',
    };
    return (
      <span className="inline-flex items-center gap-2">
        <span className={`px-2 py-0.5 rounded text-xs ${map[s] || 'bg-gray-200'}`}>{s}</span>
        {reused ? (
          <span className="px-2 py-0.5 rounded text-xs bg-purple-200 text-purple-800">cache</span>
        ) : null}
      </span>
    );
  };

  // Оптимизированный список: мемоизированная фильтрация
  const filteredJobs = useMemo(() => {
    const arr = Array.isArray(jobs) ? jobs : [];
    const byStatus = statusFilter === 'all' ? arr : arr.filter((j) => j.status === statusFilter);
    return reusedOnly ? byStatus.filter((j) => j.reused) : byStatus;
  }, [jobs, statusFilter, reusedOnly]);

  // Мемо-компонент строки таблицы, принимает только примитивы и стабильные колбэки
  const JobRow = memo(function JobRow(props: {
    id: string;
    status: string;
    reused?: boolean;
    progress: number;
    created_at: string;
    params?: JobParams | null;
    result_quest_id?: string | null;
    cost?: number | null;
    onTick: (id: string, delta?: number) => void;
    onSimulate: (id: string) => void;
    onCreateDraft: (questId: string) => void;
  }) {
    const {
      id,
      status,
      reused,
      progress,
      created_at,
      params,
      result_quest_id,
      cost,
      onTick,
      onSimulate,
      onCreateDraft,
    } = props;
    const createdText = useMemo(() => new Date(created_at).toLocaleString(), [created_at]);
    const paramsText = useMemo(() => {
      if (!params) return '-';
      const base = `${String(params.structure ?? '')}/${String(params.length ?? '')}/${String(
        params.tone ?? '',
      )}/${String(params.genre ?? '')}`;
      return params.locale ? `${base} · ${params.locale}` : base;
    }, [params]);
    return (
      <tr className="border-b">
        <td className="p-2 font-mono">{id}</td>
        <td className="p-2">{statusBadge(status, reused)}</td>
        <td className="p-2">
          <div className="w-40 bg-gray-200 dark:bg-gray-800 rounded h-3 overflow-hidden">
            <div
              className="bg-blue-600 h-3"
              style={{ width: `${Math.max(0, Math.min(100, progress))}%` }}
              aria-label={`progress ${progress}%`}
            />
          </div>
          <div className="text-xs text-gray-600 mt-1">{progress}%</div>
        </td>
        <td className="p-2">{createdText}</td>
        <td className="p-2">{paramsText}</td>
        <td className="p-2">{result_quest_id ? `quest:${result_quest_id}` : '-'}</td>
        <td className="p-2">{cost != null ? Number(cost).toFixed(4) : '-'}</td>
        <td className="p-2 text-right space-x-2">
          {(status === 'queued' || status === 'running') && (
            <>
              <button className="px-2 py-1 rounded border" onClick={() => onTick(id, 10)}>
                Tick +10%
              </button>
              <button className="px-2 py-1 rounded border" onClick={() => onSimulate(id)}>
                Simulate
              </button>
            </>
          )}
          {result_quest_id && (
            <button
              className="px-2 py-1 rounded border"
              onClick={() => onCreateDraft(result_quest_id!)}
            >
              New draft
            </button>
          )}
        </td>
      </tr>
    );
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">AI Quests</h1>

      <div className="rounded border p-3 mb-6">
        <h2 className="font-semibold mb-2">Создать ИИ‑квест</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          <div className="flex items-center gap-2">
            <label className="w-32 text-sm text-gray-600">Мир</label>
            <select
              className="border rounded px-2 py-1 flex-1"
              value={worldId}
              onChange={(e) => setWorldId(e.target.value)}
            >
              <option value="">— не выбрано —</option>
              {templates.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.title}
                  {t.locale ? ` · ${t.locale}` : ''}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="w-32 text-sm text-gray-600">Структура</label>
            <select
              className="border rounded px-2 py-1 flex-1"
              value={structure}
              onChange={(e) => setStructure(e.target.value as 'linear' | 'vn_branching' | 'epic')}
            >
              <option value="linear">linear</option>
              <option value="vn_branching">vn_branching</option>
              <option value="epic">epic</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="w-32 text-sm text-gray-600">Длина</label>
            <select
              className="border rounded px-2 py-1 flex-1"
              value={length}
              onChange={(e) => setLength(e.target.value as 'short' | 'long')}
            >
              <option value="short">short (10–15)</option>
              <option value="long">long (40–100)</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="w-32 text-sm text-gray-600">Тональность</label>
            <select
              className="border rounded px-2 py-1 flex-1"
              value={tone}
              onChange={(e) => setTone(e.target.value as 'light' | 'dark' | 'ironic')}
            >
              <option value="light">light</option>
              <option value="dark">dark</option>
              <option value="ironic">ironic</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="w-32 text-sm text-gray-600">Жанр</label>
            <input
              className="border rounded px-2 py-1 flex-1"
              placeholder="fantasy, sci-fi…"
              value={genre}
              onChange={(e) => setGenre(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="w-32 text-sm text-gray-600">Локаль</label>
            <input
              className="border rounded px-2 py-1 flex-1"
              placeholder="ru-RU / en-US"
              value={locale}
              onChange={(e) => setLocale(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-2">
            <label className="w-32 text-sm text-gray-600">Model</label>
            <select
              className="border rounded px-2 py-1 flex-1"
              value={model}
              onChange={(e) => setModel(e.target.value)}
            >
              {allowedModels.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
              {!allowedModels.includes(model) && model && <option value={model}>{model}</option>}
            </select>
            <label className="text-sm flex items-center gap-2">
              <input
                type="checkbox"
                checked={remember}
                onChange={(e) => setRemember(e.target.checked)}
              />
              Remember for me
            </label>
          </div>
        </div>
        <div className="mt-3 flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={reuse} onChange={(e) => setReuse(e.target.checked)} />
            Reuse result (cache)
          </label>
          <button className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-800" onClick={submit}>
            Сгенерировать
          </button>
        </div>
      </div>

      <div className="mb-6">
        <button className="px-3 py-1 rounded border" onClick={() => setMgmtOpen((v) => !v)}>
          {mgmtOpen ? 'Скрыть управление' : 'Показать управление (Миры/Персонажи/AI Settings)'}
        </button>
      </div>

      {mgmtOpen && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-8">
          <div className="rounded border p-3">
            <h3 className="font-semibold mb-2">Миры</h3>
            <div className="flex flex-col gap-2 mb-3">
              <input
                className="border rounded px-2 py-1"
                placeholder="Название"
                value={newWorld.title}
                onChange={(e) => setNewWorld((s) => ({ ...s, title: e.target.value }))}
              />
              <input
                className="border rounded px-2 py-1"
                placeholder="Локаль (ru-RU / en-US)"
                value={newWorld.locale}
                onChange={(e) => setNewWorld((s) => ({ ...s, locale: e.target.value }))}
              />
              <textarea
                className="border rounded px-2 py-1"
                placeholder="Описание"
                value={newWorld.description}
                onChange={(e) => setNewWorld((s) => ({ ...s, description: e.target.value }))}
              />
              <button
                className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-800"
                onClick={createWorld}
              >
                Добавить мир
              </button>
            </div>
            <div className="max-h-80 overflow-auto divide-y">
              {worlds.map((w) => (
                <div key={w.id} className="py-2 flex items-center justify-between gap-2">
                  <button
                    className={`text-left flex-1 ${selectedWorld === w.id ? 'font-semibold' : ''}`}
                    onClick={() => setSelectedWorld(w.id)}
                  >
                    {w.title}
                    {w.locale ? ` · ${w.locale}` : ''}
                  </button>
                  <button className="px-2 py-1 rounded border" onClick={() => removeWorld(w.id)}>
                    Удалить
                  </button>
                </div>
              ))}
              {worlds.length === 0 && <div className="text-sm text-gray-500">Пока нет миров</div>}
            </div>
          </div>

          <div className="rounded border p-3">
            <h3 className="font-semibold mb-2">
              Персонажи {selectedWorld ? '' : '(выберите мир)'}
            </h3>
            {selectedWorld && (
              <>
                <div className="flex flex-col gap-2 mb-3">
                  <input
                    className="border rounded px-2 py-1"
                    placeholder="Имя"
                    value={newChar.name}
                    onChange={(e) => setNewChar((s) => ({ ...s, name: e.target.value }))}
                  />
                  <input
                    className="border rounded px-2 py-1"
                    placeholder="Роль"
                    value={newChar.role}
                    onChange={(e) => setNewChar((s) => ({ ...s, role: e.target.value }))}
                  />
                  <textarea
                    className="border rounded px-2 py-1"
                    placeholder="Описание"
                    value={newChar.description}
                    onChange={(e) => setNewChar((s) => ({ ...s, description: e.target.value }))}
                  />
                  <button
                    className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-800"
                    onClick={addCharacter}
                  >
                    Добавить персонажа
                  </button>
                </div>
                <div className="max-h-80 overflow-auto divide-y">
                  {characters.map((c) => (
                    <div key={c.id} className="py-2 flex items-center justify-between gap-2">
                      <div className="flex-1">
                        <div className="font-medium">
                          {c.name}
                          {c.role ? ` · ${c.role}` : ''}
                        </div>
                        {c.description && (
                          <div className="text-xs text-gray-600">{c.description}</div>
                        )}
                      </div>
                      <button
                        className="px-2 py-1 rounded border"
                        onClick={() => removeCharacter(c.id)}
                      >
                        Удалить
                      </button>
                    </div>
                  ))}
                  {characters.length === 0 && (
                    <div className="text-sm text-gray-500">Пока нет персонажей</div>
                  )}
                </div>
              </>
            )}
          </div>

          <div className="rounded border p-3">
            <h3 className="font-semibold mb-2">AI Settings</h3>
            <div className="flex flex-col gap-2">
              <input
                className="border rounded px-2 py-1"
                placeholder="Provider (например: openai, anthropic…)"
                value={aiSettings.provider ?? ''}
                onChange={(e) => setAISettings((s) => ({ ...s, provider: e.target.value }))}
              />
              <input
                className="border rounded px-2 py-1"
                placeholder="Base URL (необязательно)"
                value={aiSettings.base_url ?? ''}
                onChange={(e) => setAISettings((s) => ({ ...s, base_url: e.target.value }))}
              />
              <input
                className="border rounded px-2 py-1"
                placeholder="Model (например: gpt-4o-mini)"
                value={aiSettings.model ?? ''}
                onChange={(e) => setAISettings((s) => ({ ...s, model: e.target.value }))}
              />
              <input
                className="border rounded px-2 py-1"
                placeholder={
                  aiSettings.has_api_key ? 'API Key (оставьте пустым — не менять)' : 'API Key'
                }
                type="password"
                value={aiSecret}
                onChange={(e) => setAISecret(e.target.value)}
              />
              <div className="text-xs text-gray-600">
                {aiSettings.has_api_key ? 'Ключ сохранён' : 'Ключ не задан'}
              </div>
              <button className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-800" onClick={saveAI}>
                Сохранить
              </button>
            </div>

            <CursorPager
              hasMore={Boolean(jobsCursor)}
              loading={jobsLoading}
              onLoadMore={loadJobsMore}
              className="mt-3 flex justify-center"
            />
          </div>
        </div>
      )}

      {loading && <div className="text-sm text-gray-500">Loading…</div>}
      {error && <div className="text-sm text-red-600">{error}</div>}

      {!loading && !error && (
        <>
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <label className="text-sm text-gray-600">Status</label>
            <select
              className="border rounded px-2 py-1"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="all">all</option>
              <option value="queued">queued</option>
              <option value="running">running</option>
              <option value="completed">completed</option>
              <option value="failed">failed</option>
              <option value="canceled">canceled</option>
            </select>
            <label className="text-sm flex items-center gap-2">
              <input
                type="checkbox"
                checked={reusedOnly}
                onChange={(e) => setReusedOnly(e.target.checked)}
              />
              reused only
            </label>
            {isUpdating && (
              <span className="text-xs text-gray-500" aria-live="polite">
                Updating…
              </span>
            )}
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
                {filteredJobs.map((j) => (
                  <JobRow
                    key={j.id}
                    id={j.id}
                    status={j.status}
                    reused={j.reused}
                    progress={j.progress ?? 0}
                    created_at={j.created_at}
                    params={j.params}
                    result_quest_id={j.result_quest_id}
                    cost={j.cost}
                    onTick={tick}
                    onSimulate={simulate}
                    onCreateDraft={createNewDraft}
                  />
                ))}
                {filteredJobs.length === 0 && (
                  <tr>
                    <td colSpan={8} className="p-4 text-center text-gray-500">
                      No jobs
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
