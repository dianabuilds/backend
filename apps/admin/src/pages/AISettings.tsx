import { useEffect, useState } from 'react';

import { api, ApiError } from '../api/client';
import LimitBadge, { handleLimit429, refreshLimits } from '../components/LimitBadge';

type CBConfig = {
  fail_rate_threshold?: number;
  min_requests?: number;
  open_seconds?: number;
};

type StageMapEntry = {
  provider?: string;
  base_url?: string;
  model?: string;
};

type AISettings = {
  provider?: string | null;
  base_url?: string | null;
  model?: string | null;
  has_api_key: boolean;
  model_map?: Record<string, StageMapEntry> | null;
  cb?: CBConfig | null;
};

type StageConfig = { stage: string } & StageMapEntry;

export default function AISettingsPage() {
  const [aiSettings, setAISettings] = useState<AISettings>({
    has_api_key: false,
  });
  const [aiSecret, setAISecret] = useState<string>(''); // пустая строка — не менять
  const [stageMap, setStageMap] = useState<StageConfig[]>([]); // карта стадий в удобном формате
  const [cb, setCb] = useState<CBConfig>({});

  const loadAISettings = async () => {
    try {
      const res = await api.get<AISettings>('/admin/ai/quests/settings');
      const data = res.data ?? { has_api_key: false };
      setAISettings(data);
      setAISecret('');
      // Инициализация расширенных полей
      const map: Record<string, StageMapEntry> = data.model_map ?? {};
      setStageMap(
        Object.entries(map).map(([stage, conf]) => ({
          stage,
          provider: conf.provider ?? '',
          base_url: conf.base_url ?? '',
          model: conf.model ?? '',
        })),
      );
      setCb({
        fail_rate_threshold: data.cb?.fail_rate_threshold ?? 0.5,
        min_requests: data.cb?.min_requests ?? 20,
        open_seconds: data.cb?.open_seconds ?? 60,
      });
    } catch (e) {
      console.error(e);
    }
  };

  const saveAI = async () => {
    try {
      const model_map: Record<string, StageMapEntry> = {};
      for (const item of stageMap) {
        if (!item.stage) continue;
        const entry: StageMapEntry = {};
        if (item.provider) entry.provider = item.provider;
        if (item.base_url) entry.base_url = item.base_url;
        if (item.model) entry.model = item.model;
        model_map[item.stage] = entry;
      }
      await api.put('/admin/ai/quests/settings', {
        provider: aiSettings.provider ?? null,
        base_url: aiSettings.base_url ?? null,
        model: aiSettings.model ?? null,
        model_map,
        cb,
        api_key: aiSecret === '' ? null : aiSecret, // null — оставить без изменений, "" — очистить, строка — сохранить
      });
      await loadAISettings();
      await refreshLimits();
      alert('Настройки сохранены');
    } catch (e: any) {
      if (e instanceof ApiError && e.status === 429) {
        const retry = Number(e.headers?.get('Retry-After') || 0);
        await handleLimit429('ai_tokens', retry);
        alert('Rate limit exceeded');
      } else {
        alert(e instanceof Error ? e.message : String(e));
      }
    }
  };

  useEffect(() => {
    loadAISettings();
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">AI Settings</h1>
      <div className="rounded border p-4 max-w-3xl space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex flex-col gap-1">
            <label className="text-sm text-gray-600">Provider (по умолчанию)</label>
            <input
              className="border rounded px-2 py-1"
              placeholder="openai, anthropic, ..."
              value={aiSettings.provider ?? ''}
              onChange={(e) => setAISettings((s) => ({ ...s, provider: e.target.value }))}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-gray-600">Base URL (по умолчанию)</label>
            <input
              className="border rounded px-2 py-1"
              placeholder="https://api..."
              value={aiSettings.base_url ?? ''}
              onChange={(e) => setAISettings((s) => ({ ...s, base_url: e.target.value }))}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-gray-600">Model (по умолчанию)</label>
            <input
              className="border rounded px-2 py-1"
              placeholder="gpt-4o-mini, ..."
              value={aiSettings.model ?? ''}
              onChange={(e) => setAISettings((s) => ({ ...s, model: e.target.value }))}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-sm text-gray-600">API Key</label>
            <input
              className="border rounded px-2 py-1"
              type="password"
              placeholder={
                aiSettings.has_api_key
                  ? 'Секрет сохранён (оставьте пустым — не менять)'
                  : 'Введите ключ'
              }
              value={aiSecret}
              onChange={(e) => setAISecret(e.target.value)}
            />
            <div className="text-xs text-gray-600">
              {aiSettings.has_api_key ? 'Ключ сохранён' : 'Ключ не задан'}
            </div>
          </div>
        </div>

        <div className="space-y-2">
          <div className="text-lg font-semibold">Карта моделей по стадиям</div>
          {stageMap.map((item, idx) => (
            <div key={idx} className="grid grid-cols-1 md:grid-cols-5 gap-2 items-center">
              <input
                className="border rounded px-2 py-1"
                placeholder="Стадия (например: outline)"
                value={item.stage}
                onChange={(e) =>
                  setStageMap((m) => {
                    const copy = [...m];
                    copy[idx] = { ...copy[idx], stage: e.target.value };
                    return copy;
                  })
                }
              />
              <input
                className="border rounded px-2 py-1"
                placeholder="Provider"
                value={item.provider ?? ''}
                onChange={(e) =>
                  setStageMap((m) => {
                    const copy = [...m];
                    copy[idx] = { ...copy[idx], provider: e.target.value };
                    return copy;
                  })
                }
              />
              <input
                className="border rounded px-2 py-1"
                placeholder="Base URL"
                value={item.base_url ?? ''}
                onChange={(e) =>
                  setStageMap((m) => {
                    const copy = [...m];
                    copy[idx] = { ...copy[idx], base_url: e.target.value };
                    return copy;
                  })
                }
              />
              <input
                className="border rounded px-2 py-1"
                placeholder="Model"
                value={item.model ?? ''}
                onChange={(e) =>
                  setStageMap((m) => {
                    const copy = [...m];
                    copy[idx] = { ...copy[idx], model: e.target.value };
                    return copy;
                  })
                }
              />
              <button
                className="px-2 py-1 rounded bg-red-200 dark:bg-red-800"
                onClick={() => setStageMap((m) => m.filter((_, i) => i !== idx))}
              >
                Удалить
              </button>
            </div>
          ))}
          <button
            className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-800"
            onClick={() => setStageMap((m) => [...m, { stage: '' }])}
          >
            Добавить стадию
          </button>
        </div>

        <div className="space-y-2">
          <div className="text-lg font-semibold">Circuit Breaker</div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-sm text-gray-600">fail_rate_threshold (0..1)</label>
              <input
                className="border rounded px-2 py-1"
                type="number"
                step="0.01"
                min={0}
                max={1}
                value={cb.fail_rate_threshold ?? 0.5}
                onChange={(e) =>
                  setCb((c) => ({
                    ...c,
                    fail_rate_threshold: Number(e.target.value),
                  }))
                }
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-gray-600">min_requests</label>
              <input
                className="border rounded px-2 py-1"
                type="number"
                min={1}
                value={cb.min_requests ?? 20}
                onChange={(e) => setCb((c) => ({ ...c, min_requests: Number(e.target.value) }))}
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-sm text-gray-600">open_seconds</label>
              <input
                className="border rounded px-2 py-1"
                type="number"
                min={1}
                value={cb.open_seconds ?? 60}
                onChange={(e) => setCb((c) => ({ ...c, open_seconds: Number(e.target.value) }))}
              />
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-800" onClick={saveAI}>
            Сохранить
          </button>
          <LimitBadge limitKey="ai_tokens" />
        </div>
      </div>
    </div>
  );
}
