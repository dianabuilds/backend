import { useEffect, useState } from "react";

import EnvChip from "../components/EnvChip";
import {
  DevToolsSettings,
  getDevToolsSettings,
  updateDevToolsSettings,
} from "../api/devtools";
import PageLayout from "./_shared/PageLayout";

function Toggle({
  checked,
  onChange,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <button
      className={`px-2 py-1 rounded text-sm ${
        checked ? "bg-green-600 text-white" : "bg-gray-200 dark:bg-gray-800"
      }`}
      onClick={() => onChange(!checked)}
      aria-pressed={checked}
    >
      {checked ? "On" : "Off"}
    </button>
  );
}

export default function DevToolsPage() {
  const [settings, setSettings] = useState<DevToolsSettings | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getDevToolsSettings();
      setSettings(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setSettings(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const update = async (patch: Partial<DevToolsSettings>) => {
    try {
      const updated = await updateDevToolsSettings(patch);
      setSettings((prev) => ({ ...(prev || {}), ...updated }));
    } catch (e) {
      alert(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <PageLayout title="Dev Tools" subtitle="Environment configuration">
      {loading && (
        <div className="animate-pulse text-sm text-gray-500">Loading...</div>
      )}
      {error && <div className="text-sm text-red-600">{error}</div>}
      {settings && (
        <div className="mt-4 space-y-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600">Environment</span>
            <EnvChip mode={settings.env_mode} />
          </div>

          <div className="flex items-center gap-2">
            <label className="w-60">Preview default</label>
            <select
              value={settings.preview_default || "preview"}
              onChange={(e) => update({ preview_default: e.target.value })}
              className="border rounded px-2 py-1 bg-white dark:bg-gray-900"
            >
              <option value="preview">preview</option>
              <option value="disabled">disabled</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label className="w-60">Allow external calls</label>
            <Toggle
              checked={!!settings.allow_external_calls}
              onChange={(v) => update({ allow_external_calls: v })}
            />
          </div>

          <div className="flex items-center gap-2">
            <label className="w-60">RNG seed strategy</label>
            <select
              value={settings.rng_seed_strategy || "fixed"}
              onChange={(e) => update({ rng_seed_strategy: e.target.value })}
              className="border rounded px-2 py-1 bg-white dark:bg-gray-900"
            >
              <option value="fixed">fixed</option>
              <option value="random">random</option>
            </select>
          </div>

          <section>
            <h2 className="font-semibold mb-1">Providers</h2>
            <pre className="bg-gray-100 dark:bg-gray-800 p-3 rounded text-xs overflow-auto">
              {JSON.stringify(settings.providers ?? {}, null, 2)}
            </pre>
          </section>
        </div>
      )}
    </PageLayout>
  );
}

