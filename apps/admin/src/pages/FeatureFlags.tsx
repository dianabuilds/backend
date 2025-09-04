import { useEffect, useState } from 'react';

import { ApiError } from '../api/client';
import { type FeatureFlag, listFlags, updateFlag } from '../api/flags';
import PageLayout from './_shared/PageLayout';

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      className={`inline-flex items-center px-2 py-1 rounded ${checked ? 'bg-green-600 text-white' : 'bg-gray-200 dark:bg-gray-800'}`}
      onClick={() => onChange(!checked)}
      aria-pressed={checked}
    >
      {checked ? 'On' : 'Off'}
    </button>
  );
}

export default function FeatureFlagsPage() {
  const [flags, setFlags] = useState<FeatureFlag[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const items = await listFlags();
      setFlags(items);
    } catch (e) {
      if (e instanceof ApiError) {
        const msg = typeof e.detail === 'string' ? e.detail : e.message;
        setError(msg);
      } else {
        setError(e instanceof Error ? e.message : String(e));
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const onToggle = async (f: FeatureFlag, v: boolean) => {
    try {
      const updated = await updateFlag(f.key, { value: v });
      setFlags((arr) => arr.map((x) => (x.key === f.key ? updated : x)));
    } catch (e) {
      const msg =
        e instanceof ApiError
          ? typeof e.detail === 'string'
            ? e.detail
            : e.message
          : e instanceof Error
            ? e.message
            : String(e);
      alert(msg);
    }
  };

  const onDescBlur = async (f: FeatureFlag, v: string) => {
    if (v === (f.description || '')) return;
    try {
      const updated = await updateFlag(f.key, { description: v });
      setFlags((arr) => arr.map((x) => (x.key === f.key ? updated : x)));
    } catch (e) {
      const msg =
        e instanceof ApiError
          ? typeof e.detail === 'string'
            ? e.detail
            : e.message
          : e instanceof Error
            ? e.message
            : String(e);
      alert(msg);
    }
  };

  return (
    <PageLayout title="Feature Flags" subtitle="Включение/выключение функционала админки">
      {loading && <div className="animate-pulse text-sm text-gray-500">Loading...</div>}
      {error && <div className="text-sm text-red-600">{error}</div>}
      <div className="mt-4 overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="text-left text-gray-500">
            <tr>
              <th className="py-2 pr-4">Key</th>
              <th className="py-2 pr-4">Description</th>
              <th className="py-2 pr-4">Enabled</th>
              <th className="py-2 pr-4">Updated</th>
            </tr>
          </thead>
          <tbody>
            {flags.map((f) => (
              <tr key={f.key} className="border-t border-gray-200 dark:border-gray-800">
                <td className="py-2 pr-4 font-mono">{f.key}</td>
                <td className="py-2 pr-4">
                  <input
                    type="text"
                    defaultValue={f.description || ''}
                    onBlur={(e) => onDescBlur(f, e.currentTarget.value)}
                    className="w-full px-2 py-1 rounded border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900"
                  />
                </td>
                <td className="py-2 pr-4">
                  <Toggle checked={!!f.value} onChange={(v) => onToggle(f, v)} />
                </td>
                <td className="py-2 pr-4 text-gray-500">
                  {f.updated_at ? new Date(f.updated_at).toLocaleString() : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </PageLayout>
  );
}
