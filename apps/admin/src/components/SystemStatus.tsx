import { useEffect, useState } from 'react';

import { api } from '../api/client';

const services = [
  { key: 'db', label: 'DB' },
  { key: 'redis', label: 'Redis' },
  { key: 'queue', label: 'Queue' },
  { key: 'ai', label: 'AI' },
  { key: 'payment', label: 'Payments' },
];

type Status = 'ok' | 'fail' | 'unknown';

type OpsStatusResponse = {
  ready: Record<string, string>;
};

function colorClass(status: Status): string {
  switch (status) {
    case 'ok':
      return 'bg-green-500';
    case 'fail':
      return 'bg-red-500';
    default:
      return 'bg-yellow-500';
  }
}

export default function SystemStatus() {
  const [status, setStatus] = useState<Record<string, Status>>({});
  const [error, setError] = useState<string | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const run = async () => {
      setError(null);
      try {
        const res = await api.get<OpsStatusResponse>('/admin/ops/status');
        const ready = (res.data?.ready as Record<string, string> | undefined) || {};
        const map: Record<string, Status> = {};
        for (const { key } of services) {
          const v = ready[key];
          map[key] = v === 'ok' ? 'ok' : v === 'fail' ? 'fail' : 'unknown';
        }
        setStatus(map);
      } catch (e: unknown) {
        setError((e as Error)?.message || 'Failed to load');
        const map: Record<string, Status> = {};
        for (const { key } of services) map[key] = 'fail';
        setStatus(map);
      }
    };
    run();
  }, []);

  return (
    <div>
      <button
        className="flex items-center gap-1"
        onClick={() => setOpen(true)}
        data-testid="system-status-button"
      >
        {services.map(({ key, label }) => (
          <span
            key={key}
            className={`w-3 h-3 rounded-full ${colorClass(status[key] ?? 'unknown')}`}
            title={label}
            data-testid={`status-dot-${key}`}
          />
        ))}
      </button>
      {open && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-900 p-4 rounded shadow max-w-md w-full">
            <h2 className="text-lg font-bold mb-2">System status</h2>
            {error && (
              <div className="mb-2 text-red-600" data-testid="error-text">
                {error}
              </div>
            )}
            <ul className="space-y-1">
              {services.map(({ key, label }) => (
                <li key={key} className="flex items-center gap-2">
                  <span
                    className={`w-3 h-3 rounded-full ${colorClass(status[key] ?? 'unknown')}`}
                  />
                  <span>{label}</span>
                  {status[key] === 'fail' && <span className="text-red-600 text-sm">fail</span>}
                </li>
              ))}
            </ul>
            <div className="mt-3 text-right">
              <button onClick={() => setOpen(false)} className="px-3 py-1 rounded border">
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
