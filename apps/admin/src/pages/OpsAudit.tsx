import { useEffect, useState } from 'react';

import { api } from '../api/client';

interface AuditEntry {
  id: string;
  actor: string;
  action: string;
  created_at?: string;
}

export default function OpsAudit() {
  const [items, setItems] = useState<AuditEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get('/admin/audit')
      .then((res) => setItems((res.data.items as AuditEntry[]) || []))
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Audit Log</h1>
      {error && <p className="text-red-600">{error}</p>}
      <table className="min-w-full text-sm">
        <thead>
          <tr className="border-b">
            <th className="p-2 text-left">Actor</th>
            <th className="p-2 text-left">Action</th>
          </tr>
        </thead>
        <tbody>
          {items.map((it) => (
            <tr key={it.id} className="border-b">
              <td className="p-2">{it.actor}</td>
              <td className="p-2">{it.action}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
