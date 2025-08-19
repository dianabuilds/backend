import { useEffect, useState } from "react";
import { api } from "../api/client";

type AISettings = { provider?: string | null; base_url?: string | null; model?: string | null; has_api_key: boolean };

export default function AISettingsPage() {
  const [aiSettings, setAISettings] = useState<AISettings>({ has_api_key: false });
  const [aiSecret, setAISecret] = useState<string>(""); // пустая строка — не менять

  const loadAISettings = async () => {
    try {
      const res = await api.get<AISettings>("/admin/ai/quests/settings");
      setAISettings(res.data ?? { has_api_key: false });
      setAISecret("");
    } catch (e) {
      console.error(e);
    }
  };

  const saveAI = async () => {
    try {
      await api.put("/admin/ai/quests/settings", {
        provider: aiSettings.provider ?? null,
        base_url: aiSettings.base_url ?? null,
        model: aiSettings.model ?? null,
        api_key: aiSecret === "" ? null : aiSecret, // null — оставить без изменений, "" — очистить, строка — сохранить
      });
      await loadAISettings();
      alert("Настройки сохранены");
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  useEffect(() => { loadAISettings(); }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">AI Settings</h1>
      <div className="rounded border p-4 max-w-2xl space-y-3">
        <div className="flex flex-col gap-1">
          <label className="text-sm text-gray-600">Provider</label>
          <input className="border rounded px-2 py-1" placeholder="openai, anthropic, ..." value={aiSettings.provider ?? ""} onChange={(e) => setAISettings((s) => ({ ...s, provider: e.target.value }))} />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm text-gray-600">Base URL</label>
          <input className="border rounded px-2 py-1" placeholder="https://api..." value={aiSettings.base_url ?? ""} onChange={(e) => setAISettings((s) => ({ ...s, base_url: e.target.value }))} />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm text-gray-600">Model</label>
          <input className="border rounded px-2 py-1" placeholder="gpt-4o-mini, ..." value={aiSettings.model ?? ""} onChange={(e) => setAISettings((s) => ({ ...s, model: e.target.value }))} />
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-sm text-gray-600">API Key</label>
          <input className="border rounded px-2 py-1" type="password" placeholder={aiSettings.has_api_key ? "Секрет сохранён (оставьте пустым — не менять)" : "Введите ключ"} value={aiSecret} onChange={(e) => setAISecret(e.target.value)} />
          <div className="text-xs text-gray-600">{aiSettings.has_api_key ? "Ключ сохранён" : "Ключ не задан"}</div>
        </div>
        <div>
          <button className="px-3 py-1 rounded bg-gray-200 dark:bg-gray-800" onClick={saveAI}>Сохранить</button>
        </div>
      </div>
    </div>
  );
}
